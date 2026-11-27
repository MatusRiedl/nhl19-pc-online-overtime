"""New player (v1.00.0; overtime_core/newplayer.py, app/newplayer_ctl.py, myedits `new`): a player made by hand into
any club or the free agents, on the game's own default roster. He is one change, the roster rules and the online
roster check still pass, and My edits keeps him through every update (one copy, his club, his birth date), makes him
again in a roster that does not have him and forgets him when his making is taken back and saved."""
import json
import os

import pytest

from overtime_core import newplayer as NP, rosterupdate as U, trades as X
from overtime_core.roster import Roster
from overtime_roster.app import controller as C, jobs, myedits, roster_card as RC, sources, update

from test_update_go import DATA, Host, _template_save, view

pytestmark = pytest.mark.game

EDM = 11        # Edmonton
BORN = '2004-05-06'


def issues(db):
    return {(i.rule, i.message) for i in Roster.from_database(db).verify()}


def club_of(db, pi):
    e = U.State(db).entry.get(pi)
    return e[1] if e else X.FA


def test_a_new_player_signs_with_any_club_or_stays_a_free_agent(game_dir):
    from overtime_roster.app import hostroster
    rosters = pytest.importorskip('overtime_server.rosters')     # not in the public tree
    db, schema, _initial = rosters.load(game_dir)
    before = issues(db)
    shl = next(t for t, lg in X.club_teams(db).items() if lg == 2)
    made = [NP.create(db, 'Ann', 'Skater', 'LW', 'L', BORN, EDM),
            NP.create(db, 'Bo', 'Keeper', 'G', 'L', '1999-12-31', X.FA),
            NP.create(db, 'Cy', 'Swede', 'D', 'R', '2001-02-03', shl)]
    state, bios = U.State(db), db[U.BIOS]
    for (pi, gid, _plan), (team, goalie) in zip(made, ((EDM, False), (X.FA, True), (shl, False))):
        b = state.bio(pi)
        assert b['game_id'] == gid and gid < U.SPECIAL_IDS and b['artid'] in U.NEW_ARTIDS
        assert (b['position'] == U.GOALIE) == goalie and b['headid'] >= 60000     # a generic face
        assert club_of(db, pi) == team and (pi in state.free) == (team == X.FA)
        assert any(r == gid for r in db[U.AI[goalie]].column('game_id'))
        assert any(r == gid for r in db[U.EQUIPMENT[goalie]].column('game_id'))
    a = state.bio(made[0][0])
    assert (a['firstname'], a['lastname'], a['handedness'], a['team'], a['proteam']) == ('Ann', 'Skater', 0, EDM, EDM)
    assert a['year'] + U.YEAR_BASE == 2004 and (a['month'], a['day']) == (4, 5)
    assert state.bio(made[1][0])['team'] == -1 and len({gid for _pi, gid, _p in made}) == 3
    assert issues(db) - before == set()
    blob, crc, came = hostroster.host_roster(game_dir, schema, db)     # a host roster carries him online
    assert came == 'open' and rosters.check_bytes(blob) == crc
    assert len(bios.rows()) == len({r['game_id'] for r in bios.rows()})


def test_a_position_or_club_the_roster_has_not_is_refused(game_dir):
    rosters = pytest.importorskip('overtime_server.rosters')     # not in the public tree
    db, _schema, _initial = rosters.load(game_dir)
    raw = db.to_bytes()
    with pytest.raises(U.UpdateError):
        NP.create(db, 'A', 'B', 'X', 'L', BORN, EDM)
    with pytest.raises(X.TradeError):
        NP.create(db, 'A', 'B', 'C', 'L', BORN, 31)     # an All-Star team is not a club
    with pytest.raises(X.TradeError):
        NP.create(db, 'A', 'B', 'C', 'L', BORN, U.T.SEATTLE)    # nor a custom team (v1.00.0 limit)
    assert db.to_bytes() == raw


def test_the_plan_leaves_a_kept_made_player_alone(game_dir):
    rosters = pytest.importorskip('overtime_server.rosters')     # not in the public tree
    db, _schema, _initial = rosters.load(game_dir)
    pi, gid, _plan = NP.create(db, 'Connor', 'McDavid', 'C', 'L', '1997-01-13', EDM)     # a namesake
    real = [{'id': 1, 'first': 'Connor', 'last': 'McDavid', 'birth': '1997-01-13', 'team': 'EDM',
             'position': 'C'}]
    plain = U.plan(db, real)
    kept = U.plan(db, real, keep={gid})
    assert pi not in {p for _r, p, _t, _l in kept.placed} and pi not in {p for p, _n, _t in kept.releases}
    assert pi in {p for _r, p, _t, _l in plain.placed} or pi in {p for p, _n, _t in plain.releases}


# --- in the app --------------------------------------------------------------------------------------------------------
@pytest.fixture
def app(game_dir, tmp_path, monkeypatch):
    monkeypatch.setenv('OVERTIME_ROSTER_HOME', str(tmp_path / 'home'))

    def inline(work, done=None, failed=None, expected=()):
        try:
            out = work()
        except expected as err:
            return failed and failed(str(err))
        return done and done(out)
    monkeypatch.setattr(jobs, 'run', inline)
    with open(os.path.join(DATA, 'nhl_rosters_20262027.json'), encoding='utf-8') as f:
        real = json.load(f)
    with open(os.path.join(DATA, 'nhl_schedule_20262027.json'), encoding='utf-8') as f:
        games = [tuple(g) for g in json.load(f)]

    def gather(client, season, pack_dir, fetch=None, offline=False, step=None, log=None, schedule=True):
        for k in update.GATHER_STEPS:
            step(k, 'ok', 'fixture')
        return update.Gathered(season, real, games, [], [], {'rosters': 'NHL.com', 'calendar': 'NHL.com'})
    monkeypatch.setattr(update, 'gather', gather)
    saves = str(tmp_path / 'saves')
    _template_save(saves)
    host = Host()
    c = C.Controller(host, game_dir=game_dir, save_dir=saves)
    host.ctl = c
    c.load_source(sources.GAME_ID)
    c.calls['tab']('roster')
    c.calls['rail_team'](EDM)
    return c


def window(c):
    return c.host.snap('newplayer')['window']


def make(c, first, last, pos='C', shoots='L', born=BORN, team=None):
    assert c.calls['newplayer_open']() is None
    if team is not None:
        c.calls['newplayer_set']('team', team)
    for k, v in (('pos', pos), ('shoots', shoots)):
        c.calls['newplayer_set'](k, v)
    return c.calls['newplayer_make']({'first': first, 'last': last, 'born': born})


def found(c, first, last):
    s = c.session
    return myedits.index(s, c.parts['roster'].clock(s))[1].get(myedits.plain_name(first, last), [])


def test_the_window_makes_him_on_the_rail_club_and_opens_his_card(app):
    c = app
    s = c.session
    assert c.calls['newplayer_open']() is None
    w = window(c)
    assert w['values']['team'] == EDM and w['values']['league'] == 0 and not w['can_make']
    assert w['leagues'][0]['label'] == 'NHL' and w['leagues'][-1]['value'] == X.FA
    c.calls['newplayer_set']('league', X.FA)
    assert window(c)['values']['team'] == X.FA
    c.calls['newplayer_set']('team', EDM)
    mcdavid = next(p for p in s.players_of(EDM) if s.bio(p)[1]['lastname'] == 'McDavid')
    his = c.parts['roster'].clock(s).born(s.bio(mcdavid)[1])
    for bad, key in (({'first': 'A', 'last': '', 'born': BORN}, 'last'),
                     ({'first': 'A', 'last': 'B', 'born': '2004-13-01'}, 'born'),
                     ({'first': 'A', 'last': 'B', 'born': '2019-01-01'}, 'born'),
                     ({'first': 'Connor', 'last': 'McDavid', 'born': his}, 'last')):
        before = len(s.history)
        assert 'error' in c.calls['newplayer_make'](bad), bad
        assert window(c)['problems'][0]['key'] == key and len(s.history) == before
    raw = s.db.to_bytes()
    assert c.calls['newplayer_make']({'first': 'Matus', 'last': 'Newman', 'born': BORN}) == {'ok': True}
    assert window(c) is None and c.team == EDM
    pi = c.player
    v = c.host.snap('roster_card')['values']
    assert (v['first'], v['last'], v['born'], v['pos']) == ('Matus', 'Newman', BORN, 'C')
    assert RC.rail_team(s, pi) == EDM and pi in s.players_of(EDM)
    ch = s.history[-1]
    assert ch.label == f'New player Matus Newman ({s.team_name(EDM)})'
    assert len(c.parts['save'].pending()) == 1
    assert any(it['what'] == myedits.NEW for it in c.parts['roster'].edits.items)
    s.undo()
    assert s.db.to_bytes() == raw and found(c, 'Matus', 'Newman') == []


def test_a_signing_refused_after_he_is_made_changes_nothing(app, monkeypatch):
    c = app
    s = c.session

    def refuse(db, moves, deal_years=1):
        raise X.TradeError(['Edmonton would have 51 players.'])
    monkeypatch.setattr(NP.X, 'move_players', refuse)       # newplayer.create made his bio rows already
    raw, before = s.db.to_bytes(), len(s.history)
    out = make(c, 'Matus', 'Newman', team=EDM)
    assert out == {'error': 'Edmonton would have 51 players.'}
    assert window(c)['problems'] == [{'key': 'team', 'text': 'Edmonton would have 51 players.'}]
    assert s.db.to_bytes() == raw and len(s.history) == before and found(c, 'Matus', 'Newman') == []
    assert c.parts['save'].pending() == []


def test_made_players_come_back_after_two_updates_and_in_a_new_roster(app):
    c = app
    s = c.session
    shl = next(t for t, lg in X.club_teams(s.db).items() if lg == 2)
    assert make(c, 'Matus', 'Newman', 'C', 'L', BORN, EDM) == {'ok': True}
    me = c.player
    va = c.host.snap('roster_card')['values']
    rating = next(iter(va['ratings']))
    used = {x['num'] for x in c.host.snap('roster')['rows']}
    num = next(n for n in range(2, 99) if n not in used)
    assert c.calls['roster_apply']({**va, 'num': num, 'ratings': {**va['ratings'], rating: 91}})['ok']
    assert make(c, 'Erik', 'Klubb', 'D', 'R', '2001-02-03', shl) == {'ok': True}
    assert make(c, 'Old', 'Freeman', 'G', 'L', '1985-03-04', X.FA) == {'ok': True}     # old enough to retire
    c.calls['save_name']('Mine')
    assert c.calls['save'](None) is None and c.parts['save'].unsaved() == 0
    kept = myedits.load()
    assert len(kept['players']) == 3
    mine = next(e for e in kept['players'].values() if e['id']['last'] == 'Newman')
    assert mine['new'] == {'pos': 'C', 'team': {'index': EDM, 'league': 0, 'abbr': 'EDM',
                                                 'name': s.team_name(EDM)}}
    assert mine['card']['num'] == num and mine['card']['ratings'] == {rating: 91} and mine['card']['born'] == BORN
    assert myedits.words(mine)[0] == f'new player, {s.team_name(EDM)}'
    assert c.host.snap('save')['kept_count'] == 3
    assert {r['label'] for r in c.host.snap('save')['kept']} >= {'Matus Newman', 'Erik Klubb', 'Old Freeman'}
    assert me in s.players_of(EDM)

    def check(c):
        s = c.session
        clock = c.parts['roster'].clock(s)
        for first, last, team in (('Matus', 'Newman', EDM), ('Erik', 'Klubb', shl), ('Old', 'Freeman', X.FA)):
            pis = found(c, first, last)
            assert len(pis) == 1, (first, last, pis, c.host.lines[-20:])
            assert RC.rail_team(s, pis[0]) == team, (first, last)
        pi = found(c, 'Matus', 'Newman')[0]
        v = RC.values(s, clock, pi)
        assert v['born'] == BORN and v['num'] == num and v['ratings'][rating] == 91
        assert not [i for i in s.verify() if 'Newman' in str(i)]

    for _ in range(2):          # Update twice: one copy each, his club, his birth date, his card
        assert c.calls['update_go']() is None
        r = view(c.host)['result']
        assert r['kind'] == 'good', (r, c.host.lines[-30:])
        check(c)
        made = myedits.made_ids(myedits.load(), c.session, c.parts['roster'].clock(c.session))
        assert len(made) == 3

    # the game's own roster again (a new roster): the update makes them again
    c.load_source(sources.GAME_ID)
    assert found(c, 'Matus', 'Newman') == []
    assert c.calls['update_go']() is None
    assert view(c.host)['result']['kind'] == 'good', c.host.lines[-30:]
    check(c)
    assert any(line.startswith('My edits: ') and ', 0 skipped' in line for line in c.host.lines)


def test_his_making_taken_back_and_saved_forgets_him(app):
    c = app
    s = c.session
    assert make(c, 'Gone', 'Soon') == {'ok': True}
    c.calls['save_name']('Mine')
    assert c.calls['save'](None) is None
    assert [e['id']['last'] for e in myedits.load()['players'].values()] == ['Soon']
    s.undo()
    assert found(c, 'Gone', 'Soon') == []
    assert c.calls['save'](None) is None
    assert myedits.load()['players'] == {}


def test_a_move_after_saving_is_kept_as_his_club(app):
    c = app
    s = c.session
    assert make(c, 'Moving', 'Man') == {'ok': True}
    pi = c.player
    c.calls['save_name']('Mine')
    assert c.calls['save'](None) is None
    c.calls['trade_open'](pi)
    c.calls['trade_to'](s.bio(pi)[1]['game_id'], 1)
    assert c.calls['trade_apply']() == {'ok': True}
    assert c.calls['save'](None) is None
    e = next(iter(myedits.load()['players'].values()))
    assert e['new']['team']['index'] == 1 and e['team'] == s.team_abbr(1)


def test_replay_puts_a_retired_or_moved_made_player_back(app):
    c = app
    s = c.session
    assert make(c, 'Free', 'Agent', 'G', 'L', '1985-03-04', X.FA) == {'ok': True}
    fa = c.player
    assert make(c, 'Club', 'Man', team=EDM) == {'ok': True}
    club = c.player
    c.calls['save_name']('Mine')
    assert c.calls['save'](None) is None
    s.bulk('retired and released', lambda db: (U._retire(db, [(fa, 'Free Agent', 41)]) or [],
                                                 X.move_players(db, [(s.bio(club)[1]['game_id'], X.FA)])))
    assert fa not in s.free_agents and RC.rail_team(s, club) == X.FA
    clock = c.parts['roster'].clock(s)
    out = myedits.replay(s, clock, myedits.load())
    assert out['skipped'] == [] and out['applied'] >= 2
    assert fa in s.free_agents and RC.rail_team(s, club) == EDM
    assert myedits.replay(s, clock, myedits.load())['skipped'] == []      # again: nothing to do, nothing refused
