"""`OvertimeNHL19.exe --mcp`: the MCP server an AI client starts (overtime_roster/mcp, docs/notes/mcp.md). The protocol
part needs no game; the tools are driven through the server the way a client calls them, on the game's own roster."""
import io
import json
import os
import sys

import pytest

from overtime_roster import mcp as M
from overtime_roster.app import jobs, save_ctl
from overtime_roster.mcp import protocol as P, tools as T


def toy_server(log=None):
    def hello(name, times=1):
        return {'text': ' '.join([f'Ahoj {name}'] * times)}

    def refuse():
        raise P.ToolError('No roster is open.')

    def crash():
        raise ValueError('boom')
    tools = [P.Tool('hello', 'Hello', 'Greets.', T._obj({'name': {'type': 'string'}, 'times': {'type': 'integer'}},
                                                        ['name']), hello, read_only=True),
             P.Tool('refuse', 'Refuse', 'Refuses.', T._obj({}), refuse),
             P.Tool('crash', 'Crash', 'Crashes.', T._obj({}), crash)]
    return P.Server('toy', 'Toy', '1.0', tools, 'Say hello.', log or (lambda _t: None))


def call(server, tool, ident=1, /, **args):
    return server.handle({'jsonrpc': '2.0', 'id': ident, 'method': 'tools/call',
                          'params': {'name': tool, 'arguments': args}})


def lines(raw):
    return [json.loads(x) for x in raw.decode('utf-8').splitlines()]


def test_initialize_echoes_a_known_version_and_offers_the_newest_otherwise():
    s = toy_server()
    for asked, got in (('2025-06-18', '2025-06-18'), ('2024-11-05', '2024-11-05'), ('2099-01-01', P.VERSIONS[0])):
        r = s.handle({'jsonrpc': '2.0', 'id': 7, 'method': 'initialize',
                      'params': {'protocolVersion': asked, 'capabilities': {}, 'clientInfo': {'name': 'test'}}})
        assert r['id'] == 7 and r['result']['protocolVersion'] == got
        assert r['result']['capabilities'] == {'tools': {'listChanged': False}}
        assert r['result']['serverInfo'] == {'name': 'toy', 'title': 'Toy', 'version': '1.0'}
        assert r['result']['instructions'] == 'Say hello.'
    assert s.handle({'jsonrpc': '2.0', 'id': 'p', 'method': 'ping'}) == {'jsonrpc': '2.0', 'id': 'p', 'result': {}}
    assert s.handle({'jsonrpc': '2.0', 'method': 'notifications/initialized'}) is None
    assert s.handle({'jsonrpc': '2.0', 'id': 3, 'result': {}}) is None          # a reply from the client
    # a 2026-07-28 client probes server/discover and falls back to initialize on an error
    assert s.handle({'jsonrpc': '2.0', 'id': 4, 'method': 'server/discover'})['error']['code'] == P.NO_METHOD


def test_tools_list_and_the_results_of_a_call():
    logged = []
    s = toy_server(logged.append)
    listed = s.handle({'jsonrpc': '2.0', 'id': 1, 'method': 'tools/list'})['result']['tools']
    assert [t['name'] for t in listed] == ['hello', 'refuse', 'crash']
    assert listed[0]['inputSchema']['required'] == ['name'] and listed[0]['annotations']['readOnlyHint'] is True
    r = call(s, 'hello', name='Juraj', times=2)['result']
    assert r['structuredContent'] == {'text': 'Ahoj Juraj Ahoj Juraj'} and 'isError' not in r
    assert json.loads(r['content'][0]['text']) == r['structuredContent']
    r = call(s, 'refuse')['result']
    assert r['isError'] is True and r['content'][0]['text'] == 'No roster is open.'
    r = call(s, 'crash')['result']
    assert r['isError'] is True and 'boom' in r['content'][0]['text'] and 'ValueError' in logged[0]
    # the arguments against the schema: a wrong one is the tool's error, not a crash
    for args, words in (({}, 'name missing'), ({'name': 'x', 'colour': 'red'}, 'takes no colour'),
                        ({'name': 5}, 'name must be a string'), ({'name': 'x', 'times': True}, 'an integer'),
                        ({'name': 'x', 'times': '2'}, 'an integer')):
        r = call(s, 'hello', **args)['result']
        assert r['isError'] is True and words in r['content'][0]['text'], (args, r)
    assert call(s, 'nope')['error']['code'] == P.BAD_PARAMS
    bad = s.handle({'jsonrpc': '2.0', 'id': 2, 'method': 'tools/call', 'params': {'name': 'hello', 'arguments': [1]}})
    assert bad['error']['code'] == P.BAD_PARAMS


def test_the_stdio_loop_writes_one_json_line_per_reply():
    s = toy_server()
    msgs = [{'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {'protocolVersion': '2025-11-25'}},
            {'jsonrpc': '2.0', 'method': 'notifications/initialized'},
            {'jsonrpc': '2.0', 'id': 2, 'method': 'tools/call', 'params': {'name': 'hello',
                                                                         'arguments': {'name': 'Šťastný\nZdeno'}}}]
    raw = b''.join((json.dumps(m, ensure_ascii=False) + '\r\n').encode('utf-8') for m in msgs)
    raw += b'\n{not json\n[{"jsonrpc": "2.0", "id": 9, "method": "ping"}]\n"text"\n'
    out = io.BytesIO()
    assert s.run(io.BytesIO(raw), out) == 0
    text = out.getvalue().decode('utf-8')
    assert 'Šťastný' in text                            # UTF-8, not \u escapes
    got = lines(out.getvalue())
    assert len(got) == 5 and all(m['jsonrpc'] == '2.0' for m in got)
    assert got[0]['id'] == 1 and got[1]['result']['structuredContent']['text'] == 'Ahoj Šťastný\nZdeno'
    assert [m['error']['code'] for m in got[2:]] == [P.PARSE, P.INVALID, P.INVALID]
    assert got[2]['id'] is None


def test_main_serves_over_stdio_and_prints_nothing_else_there(monkeypatch):
    msgs = [{'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {'protocolVersion': '2025-11-25'}},
            {'jsonrpc': '2.0', 'method': 'notifications/initialized'},
            {'jsonrpc': '2.0', 'id': 2, 'method': 'tools/list'}]
    out, err = io.BytesIO(), io.StringIO()

    class Stream:
        def __init__(self, buffer):
            self.buffer = buffer

        def write(self, text):          # what a stray print would reach
            self.buffer.write(text.encode('utf-8'))
    monkeypatch.setattr(sys, 'stdin', Stream(io.BytesIO(b''.join(json.dumps(m).encode() + b'\n' for m in msgs))))
    monkeypatch.setattr(sys, 'stdout', Stream(out))
    monkeypatch.setattr(sys, 'stderr', err)
    assert M.main(['--mcp']) == 0
    got = lines(out.getvalue())
    assert [m['id'] for m in got] == [1, 2]
    assert got[0]['result']['serverInfo']['name'] == 'overtime-nhl19'
    names = [t['name'] for t in got[1]['result']['tools']]
    assert names[0] == 'overtime_status' and 'save_roster_as_new' in names and len(names) == 14
    assert 'waiting for a client' in err.getvalue()
    monkeypatch.setattr(sys, 'stdin', None)
    assert M.main(['--mcp']) == 2                       # a double click: no client


def test_the_exe_entry_hands_mcp_to_the_server(monkeypatch):
    from overtime_roster import mcp
    from overtime_roster.window import main as W
    seen = []
    monkeypatch.setattr(mcp, 'main', lambda argv: seen.append(argv) or 0)
    assert W.entry(['--mcp', '--game-dir', 'X']) == 0 and seen == [['--mcp', '--game-dir', 'X']]


def test_the_client_settings_for_this_pc():
    exe = r'C:\Games\Overtime NHL 19\OvertimeNHL19.exe'
    c = M.config(frozen=True, executable=exe, env={})
    assert c['command'] == [exe, '--mcp']
    assert json.loads(c['desktop']) == {'mcpServers': {'overtime': {'command': exe, 'args': ['--mcp']}}}
    assert c['code'] == f'claude mcp add --transport stdio overtime -- "{exe}" --mcp'
    assert M.command(frozen=True, executable='/tmp/.mount_x/AppRun', env={'APPIMAGE': '/home/deck/Overtime.AppImage'}) \
        == ['/home/deck/Overtime.AppImage', '--mcp']
    src = json.loads(M.config(frozen=False, executable='python', env={})['desktop'])['mcpServers']['overtime']
    assert src['args'] == ['-m', 'overtime_roster.mcp']
    assert os.path.isdir(os.path.join(src['env']['PYTHONPATH'], 'overtime_roster', 'mcp'))
    assert 'PYTHONPATH=' in M.config(frozen=False, executable='python', env={})['code']


# --- the tools on the game's roster ------------------------------------------------------------------------------------
@pytest.fixture
def mcp(game_dir, tmp_path, monkeypatch):
    monkeypatch.setenv('OVERTIME_ROSTER_HOME', str(tmp_path / 'home'))
    monkeypatch.setattr(jobs, 'run', jobs.run)         # the tools make it inline: put back after the test
    saves = tmp_path / 'saves'
    saves.mkdir()
    logged = []
    tools = T.OvertimeTools(game_dir, str(saves), logged.append)
    server = P.Server(M.NAME, M.TITLE, 'test', tools.tools(), T.INSTRUCTIONS, logged.append)
    ident = iter(range(1, 10000))

    def use(tool, /, **args):
        r = call(server, tool, next(ident), **args)
        assert 'result' in r, r
        r = r['result']
        return r.get('structuredContent') or r['content'][0]['text'], bool(r.get('isError'))
    return use, tools, saves, tmp_path / 'home'


def opened(use, roster='game'):
    r, bad = use('open_roster', roster=roster)
    assert not bad, r
    return r


@pytest.mark.game
def test_read_edit_refuse_and_undo(mcp):
    use, tools, _saves, _home = mcp
    r, bad = use('find_players', name='McDavid')
    assert bad and 'open_roster' in r
    r, bad = use('overtime_status')
    assert not bad and r['game_found'] and r['open_roster'] is None
    assert [x['id'] for x in r['rosters'][:2]] == ['game', 'default']
    assert opened(use)['open_roster']['id'] == 'game'
    r, _ = use('find_players', name='mcdavid')
    pid = r['players'][0]['id']
    assert r['players'][0]['name'] == 'Connor McDavid'
    p, bad = use('get_player', player_id=pid)
    assert not bad and p['values']['last'] == 'McDavid' and p['values']['pos'] == 'C'
    field, rating = next(iter(p['ratings'].items()))
    assert rating['label'] and isinstance(rating['value'], int)
    new = rating['value'] - 1
    r, bad = use('edit_player', player_id=pid, changes={'ratings': {field: new}, 'num': 98})
    assert not bad and r['ok'] and r['changed'] == 2, r
    assert use('get_player', player_id=pid)[0]['ratings'][field]['value'] == new
    assert use('get_player', player_id=pid)[0]['values']['num'] == 98
    # a refused value changes nothing, and the card keeps nothing of it
    r, bad = use('edit_player', player_id=pid, changes={'num': 150})
    assert bad and r.startswith('Not changed:'), r
    assert tools.c.parts['roster'].typed == {} and tools.c.parts['roster'].problems == {}
    r, bad = use('edit_player', player_id=pid, changes={'country': 'Atlantis'})
    assert bad and 'Slovakia' in r
    assert use('get_player', player_id=999999)[1]
    e, _ = use('list_edits')
    assert e['unsaved'] == 1 and e['edits'][0]['edit'].startswith('Connor McDavid: number #97 to #98')
    r, bad = use('undo_last_edit')
    assert not bad and r['taken_back'] == e['edits'][0]['edit']
    assert use('list_edits')[0]['unsaved'] == 0
    assert use('get_player', player_id=pid)[0]['ratings'][field]['value'] == rating['value']
    assert use('undo_last_edit')[1]


@pytest.mark.game
def test_new_player_moves_league_and_saves_as_new_rosters(mcp, monkeypatch):
    use, tools, saves, home = mcp
    opened(use)
    lg, _ = use('list_teams')
    assert lg['leagues'][0] == {'id': 0, 'name': lg['leagues'][0]['name'], 'teams': lg['leagues'][0]['teams']}
    nhl = use('list_teams', league=0)[0]['teams']
    club = nhl[0]['id']
    r, bad = use('create_player', first='Matúš', last='Overtimer', born='2004-02-29', team=-1, position='D',
                 shoots='R')
    assert not bad and r['player']['name'] == 'Matúš Overtimer' and r['player']['team'] == 'FA', r
    pid = r['player']['id']
    assert use('create_player', first='A', last='B', born='2004-01-01', team=987654)[1]
    r, bad = use('create_player', first='A', last='B', born='yesterday', team=-1)
    assert bad and 'YYYY-MM-DD' in r
    r, bad = use('edit_player', player_id=pid, changes={'country': 'slovakia', 'num': 44})
    assert not bad, r
    assert use('get_player', player_id=pid)[0]['country_name'] == 'Slovakia'
    r, bad = use('move_players', moves=[{'player_id': pid, 'team': club}])
    assert not bad and r['players'][0]['team'] == nhl[0]['code'], r
    slots, _ = use('list_league_slots')
    slot = slots['slots'][0]
    r, bad = use('make_league', slot=slot['slot'], name='Overtime Liga',
                 clubs=[{'name': 'Bratislava Lions', 'city': 'Bratislava', 'nickname': 'Lions', 'abbr': 'BRL'}])
    assert not bad, r
    assert use('list_league_slots')[0]['slots'][0]['name_now'] == 'Overtime Liga'
    r, bad = use('make_league', slot='nowhere', name='X', clubs=[{'name': 'A', 'abbr': 'AAA'}])
    assert bad and 'list_league_slots' in r
    r, bad = use('make_league', slot=slot['slot'], name='X' * 30, clubs=[{'name': 'A', 'abbr': 'AAA'}])
    assert bad and r.startswith('Not made:')
    v, _ = use('verify_roster')
    assert set(v) == {'errors', 'warnings', 'issues'}
    assert use('list_edits')[0]['unsaved'] == 4
    # the open roster is not left for another while it has edits
    r, bad = use('open_roster', roster='game')
    assert bad and 'unsaved' in r
    # saved as new rosters: never over one
    r, bad = use('save_roster_as_new', name='AI roster', target='export')
    assert not bad and r['ok'], r
    assert os.listdir(home / 'exports')
    before = set(os.listdir(saves))
    r, bad = use('save_roster_as_new', name='AI roster')
    assert not bad, r
    r, bad = use('save_roster_as_new', name='AI roster 2')
    assert not bad, r
    made = set(os.listdir(saves)) - before
    assert len(made) == 2, made
    assert use('save_roster_as_new', name='x', target='folder')[1]
    assert use('list_edits')[0]['unsaved'] == 0
    status, _ = use('overtime_status')
    assert {x['id'] for x in status['rosters']} >= made
    monkeypatch.setattr(save_ctl.overlay, 'emulator_running', lambda: True)
    r, bad = use('save_roster_as_new', name='AI roster 3')
    assert bad and 'Close shadPS4 first' in r and tools.c.shell.asking is None
    assert opened(use, sorted(made)[0])['open_roster']['kind'] == 'save'


@pytest.mark.game
def test_the_overtime_default_opens(mcp, default_roster):
    use, _tools, _saves, _home = mcp
    assert opened(use, 'default')['open_roster'] == {'id': 'default', 'name': 'Overtime default', 'kind': 'start'}
    r, _ = use('find_players', name='Celebrini')
    assert r['found'] >= 1
