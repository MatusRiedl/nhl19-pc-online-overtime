"""The Roster tab's Move / trade window, Bring in game moves and the next-step note (app/trade_ctl.py), through the
Controller on the game's own default roster."""
import pytest

from overtime_core import rosterupdate as U, trades as X
from overtime_roster.app import controller as C, jobs, sources, trade_ctl

pytestmark = pytest.mark.game


class Host:
    def __init__(self):
        self.snaps, self.lines = {}, []

    def register(self, name, fn):
        self.snaps[name] = fn

    def changed(self, *names):
        pass

    def log(self, msg):
        self.lines.append(msg)


@pytest.fixture
def ctl(game_dir, tmp_path, monkeypatch):
    monkeypatch.setenv('OVERTIME_ROSTER_HOME', str(tmp_path / 'home'))
    monkeypatch.setattr(jobs, 'run', lambda work, done=None, failed=None, expected=(): done and done(work()))
    c = C.Controller(Host(), game_dir=game_dir, save_dir=str(tmp_path / 'saves'))
    c.load_source(sources.GAME_ID)
    c.shell.tab('roster')
    return c


def club_forwards(s, team):
    """playerindexes of a club's forwards, most line places first."""
    t = s.db[U.ROSTER]
    out = []
    for i, on in enumerate(t.column('team')):
        if on == team:
            pi = t.get(i, 'playerindex')
            if s.bio(pi)[1]['position'] < 3:
                out.append((-sum(1 for f in X.lines.SLOTS if t.get(i, f)), pi))
    return [pi for _n, pi in sorted(out)]


def gid(s, pi):
    return s.bio(pi)[1]['game_id']


def test_a_swap_made_in_the_window_then_the_note_says_save(ctl):
    c, s, tr = ctl, ctl.session, ctl.parts['trade']
    a, b = club_forwards(s, 0)[0], club_forwards(s, 1)[0]
    c.calls['trade_open'](a)
    w = tr.view()['window']
    assert [r['gid'] for r in w['rows']] == [gid(s, a)] and w['rows'][0]['to'] is None and not w['can_apply']
    assert w['leagues'][0]['label'] == 'NHL' and w['leagues'][-1]['value'] == X.FA
    c.calls['trade_find'](s.bio(b)[1]['lastname'].strip())
    hit = next(f for f in tr.view()['window']['found'] if f['id'] == b)
    c.calls['trade_add'](hit['id'])
    w = tr.view()['window']
    assert [(r['gid'], r['to']) for r in w['rows']] == [(gid(s, a), 1), (gid(s, b), 0)]     # a swap by itself
    assert w['can_apply'] and w['button'] == 'Make the trade' and all('places' in r['line'] for r in w['rows'])
    before = s.db.to_bytes()
    assert c.calls['trade_apply']() == {'ok': True}
    ch = s.history[-1]
    assert ch.moved == (gid(s, a), gid(s, b)) and ch.tab == 'Roster' and len(c.parts['save'].pending()) == 1
    assert U.State(s.db).entry[a] == (U.ROSTER, 1)
    v = tr.view()
    assert v['window'] is None and v['note']['unsaved'] and v['note']['title'] == 'Next: press Save'
    assert any('Ctrl+S' in step for step in v['note']['steps'])
    assert any('Active Rosters' in step for step in v['note']['steps'])
    assert 'Roster update' in v['note']['caution']                   # Patch's Roster update is on by default
    c.parts['patchall'].update_on = False
    assert tr.view()['note']['caution'] == ''
    s.undo()
    assert s.db.to_bytes() == before and tr.view()['note'] is None


def test_the_window_lists_why_a_move_is_refused_and_changes_nothing(ctl):
    c, s, tr = ctl, ctl.session, ctl.parts['trade']
    t = s.db[U.ROSTER]
    goalie = next(t.get(i, 'playerindex') for i, on in enumerate(t.column('team'))
                  if on == 2 and s.bio(t.get(i, 'playerindex'))[1]['position'] == U.GOALIE)
    c.calls['trade_open'](goalie)
    c.calls['trade_to'](gid(s, goalie), 'league:1')        # a league picked, not its club yet
    w = tr.view()['window']
    assert w['rows'][0]['league'] == 1 and w['rows'][0]['to'] is None and not w['can_apply']
    c.calls['trade_to'](gid(s, goalie), X.FA)
    w = tr.view()['window']
    assert not w['can_apply'] and 'goalie' in w['problems'][0]
    before = s.db.to_bytes()
    assert c.calls['trade_apply']().get('error')
    assert s.db.to_bytes() == before and tr.view()['window'] is not None
    c.calls['trade_close']()
    assert tr.view()['window'] is None


def test_game_moves_come_over_and_the_apps_own_trade_stays(ctl, monkeypatch, tmp_path):
    c, s, tr = ctl, ctl.session, ctl.parts['trade']
    mine = club_forwards(s, 3)[0]
    c.calls['trade_open'](mine)
    c.calls['trade_to'](gid(s, mine), 5)
    assert c.calls['trade_apply']() == {'ok': True}
    # the game's save: the same player went to 4 there, and a free agent signed with 7
    theirs = c.game.default_db()
    state = U.State(theirs)
    free = next(state.bio(pi)['game_id'] for pi in sorted(state.free) if state.bio(pi)['position'] < 3
                and not any(p in state.entry for p in state.pis_of[state.bio(pi)['game_id']]))
    X.move_players(theirs, [(gid(s, mine), 4), (free, 7)])
    folder = tmp_path / 'saves' / 'RosterCustom3'
    folder.mkdir(parents=True)
    (folder / 'DATA').write_bytes(b'')
    src = sources.Source('save:RosterCustom3', 'save', 'Changed in NHL 19', str(folder),
                         info={'folder': 'RosterCustom3'})
    monkeypatch.setattr(c.parts['rosters'], 'refresh_sources', lambda quiet=False: None)
    c.sources = [src]
    monkeypatch.setattr(trade_ctl.sources, 'load', lambda source, game: (theirs, source.name))
    c.calls['trade_import_open']()
    m = tr.view()['importing']
    assert m['folder'] == 'RosterCustom3' and m['saves'][0]['label'].startswith('Changed in NHL 19 (Custom Roster 4')
    rows = {x['gid']: x for x in m['moves']}
    assert set(rows) == {gid(s, mine), free} and not m['different']
    assert rows[gid(s, mine)]['mine'] and not rows[gid(s, mine)]['on']     # the app's trade stays unless ticked
    assert rows[free]['on'] and m['can_apply']
    assert c.calls['trade_import_apply']() == {'ok': True}
    where = X.where(s.db)
    assert where[gid(s, mine)] == 5 and where[free] == 7
    assert s.history[-1].label == 'Game moves from Custom Roster 4: 1 player' and tr.view()['importing'] is None
    assert tr.view()['note']['unsaved']
    s.undo()
    assert X.where(s.db)[free] == X.FA


def test_no_roster_save_says_what_to_do(ctl, monkeypatch):
    c = ctl
    monkeypatch.setattr(c.parts['rosters'], 'refresh_sources', lambda quiet=False: None)
    c.sources = [s for s in c.sources if s.kind != 'save']
    assert 'Save Roster' in c.calls['trade_import_open']()['error']
    assert c.parts['trade'].view()['importing'] is None
