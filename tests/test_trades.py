"""trades: several players change clubs in one go, and two rosters compared (a save changed in NHL 19). Runs on the
game's own default roster."""
import pytest

from overtime_core import careerstats, lines, nhl27 as N, rosterupdate as U, trades as X
from overtime_core.roster import Roster
from overtime_roster.app import sources

pytestmark = pytest.mark.game


@pytest.fixture(scope='module')
def game(game_dir):
    return sources.GameData(game_dir)


@pytest.fixture
def db(game):
    return game.default_db()


def players(db, team, kind=None):
    """[(game_id, playerindex, slots held, jersey)] of a club, most places first."""
    state, t = U.State(db), db[U.ROSTER]
    out = []
    for i, on in enumerate(t.column('team')):
        if on != team:
            continue
        pi = t.get(i, 'playerindex')
        b = state.bio(pi)
        if kind and X.kind_of(b['position']) != kind:
            continue
        out.append((b['game_id'], pi, frozenset(s for s in lines.SLOTS if t.get(i, s)), t.get(i, 'jersey')))
    return sorted(out, key=lambda p: (-len(p[2]), p[0]))


def row_of(db, pi):
    return db[U.ROSTER].column('playerindex').index(pi)


def strict(db):
    return {(i.rule, i.team, i.player) for i in Roster.from_database(db).verify(strict=True)}


def free_skater(db):
    state = U.State(db)
    for pi in sorted(state.free):
        b = state.bio(pi)
        if b and b['position'] <= 3 and b['team'] == -1 and not any(p in state.entry for p in state.pis_of[b['game_id']]):
            return b
    raise AssertionError('no free skater in the default roster')


def test_two_clubs_swap_their_top_forwards(db, game):
    a, b = players(db, 0, 'F')[0], players(db, 1, 'F')[0]
    problems, rules = U.check(db, game.schema()), strict(db)
    plan = X.move_players(db, [(a[0], 1), (b[0], 0)])
    assert [(m.game_id, m.frm, m.to) for m in plan.moves] == [(a[0], 0, 1), (b[0], 1, 0)]
    state, t = U.State(db), db[U.ROSTER]
    assert state.entry[a[1]] == (U.ROSTER, 1) and state.entry[b[1]] == (U.ROSTER, 0)
    # each takes the other's places, so neither club's lines were dealt again
    assert frozenset(s for s in lines.SLOTS if t.get(row_of(db, a[1]), s)) == b[2]
    assert frozenset(s for s in lines.SLOTS if t.get(row_of(db, b[1]), s)) == a[2]
    assert plan.dealt == []
    for team, (gid, pi) in ((1, a[:2]), (0, b[:2])):
        bio = state.bio(pi)
        assert (bio['team'], bio['proteam'], bio['contractstatus']) == (team, team, 0)
        assert bio['jersey'] == t.get(row_of(db, pi), 'jersey')
        jerseys = [p[3] for p in players(db, team)]
        assert len(set(jerseys)) == len(jerseys)
        keys = sorted(t.get(i, 'key') for i, on in enumerate(t.column('team')) if on == team)
        assert keys == [U.KEYS_PER_TEAM * team + n for n in range(len(keys))]
    assert U.check(db, game.schema()) == problems and strict(db) <= rules
    again = type(db).parse(db.to_bytes(), game.schema())
    assert U.State(again).entry[a[1]] == (U.ROSTER, 1)


def test_a_goalie_trade_keeps_both_teams_dressed_and_careers_whole(db, game):
    a, b = players(db, 2, 'G')[0], players(db, 3, 'G')[0]
    problems, missing = U.check(db, game.schema()), careerstats.missing(db)    # the stock roster lacks one already
    X.move_players(db, [(a[0], 3), (b[0], 2)])
    assert len(players(db, 2, 'G')) == len(players(db, 3, 'G')) == 2
    for team in (2, 3):
        assert lines.check_lineup(db, team) == []
    assert careerstats.missing(db) == missing and U.check(db, game.schema()) == problems


def test_a_free_agent_goalie_at_an_nhl_club_gets_a_career_row(db, game):
    state, season = U.State(db), db[careerstats.SEASON]
    have = set(season.column('game_id'))
    g = next((state.bio(pi) for pi in sorted(state.free) if state.bio(pi) and state.bio(pi)['position'] == U.GOALIE
              and state.bio(pi)['game_id'] not in have
              and not any(p in state.entry for p in state.pis_of[state.bio(pi)['game_id']])), None)
    if g is None:
        pytest.skip('every free agent goalie has a career row here')
    X.move_players(db, [(g['game_id'], 8)])
    assert careerstats.missing(db) == [] and careerstats.check(db) == []    # fill gives the stock one's too


def test_a_free_agent_signs_with_an_nhl_club_on_the_lowest_deal(db):
    b = free_skater(db)
    plan = X.move_players(db, [(b['game_id'], 4)], deal_years=2)
    state = U.State(db)
    pi = plan.moves[0].pi
    assert plan.moves[0].deal and plan.moves[0].frm == X.FA
    assert state.entry[pi] == (U.ROSTER, 4) and not any(p in state.free for p in state.pis_of[b['game_id']])
    now = state.bio(pi)
    assert (now['team'], now['proteam'], now['contractstatus']) == (4, 4, 0)
    assert now['contractdollars'] == N.estimate(99)['contractdollars'] and now['contractlength'] == 2
    t = db[U.ROSTER]
    assert all(not t.get(row_of(db, pi), s) for s in lines.SLOTS) and not t.get(row_of(db, pi), lines.DRESSED)


def test_a_released_player_goes_to_the_free_agents_and_a_spare_takes_his_places(db, game):
    out = players(db, 5, 'F')[0]
    spares = [p for p in players(db, 5, 'F') if not p[2]]
    plan = X.move_players(db, [(out[0], X.FA)])
    state, t = U.State(db), db[U.ROSTER]
    assert out[1] in state.free and out[1] not in state.entry
    bio = state.bio(out[1])
    assert bio['team'] == -1 and {f: bio[f] for f in N.NO_CONTRACT} == N.NO_CONTRACT
    assert lines.check_lineup(db, 5) == []
    if spares:      # the best spare forward holds the places he left, and nobody else moved
        took = [p for p in players(db, 5, 'F') if p[2] == out[2]]
        assert took and plan.dealt == []
    assert U.key_problems(db) == []


def test_leavers_nobody_replaces_get_the_lines_dealt_again(db, game):
    for team in U.NHL:      # a club with fewer spare forwards than the forwards it lets go, and skaters to spare
        forwards = players(db, team, 'F')
        k = sum(1 for p in forwards if not p[2]) + 1
        if len(players(db, team)) - len(players(db, team, 'G')) - k >= X.DRESS['S']:
            break
    else:
        pytest.skip('no club with skaters to spare')
    held = X._held(db, team)
    plan = X.move_players(db, [(p[0], X.FA) for p in forwards[:k]])
    assert plan.dealt == [team] and lines.check_lineup(db, team) == [] and X._held(db, team) == held


def test_a_farm_player_moving_between_minor_clubs_keeps_his_nhl_deal(db):
    clubs = X.club_teams(db)
    state = U.State(db)
    pick = None
    for team in sorted(t for t, league in clubs.items() if league == 1):
        for gid, pi, _slots, _j in players(db, team):
            b = state.bio(pi)
            if b['contractstatus'] == 0 and b['contractdollars'] > 0 and b['proteam'] in U.NHL:
                pick = (gid, pi, team, b['proteam'], b['contractdollars'])
                break
        if pick:
            break
    assert pick, 'no AHL player on an NHL deal in the default roster'
    to = next(t for t, league in sorted(clubs.items()) if league == 1 and t != pick[2])
    X.move_players(db, [(pick[0], to)])
    b = U.State(db).bio(pick[1])
    assert (b['team'], b['proteam'], b['contractstatus'], b['contractdollars']) == (to, pick[3], 0, pick[4])


@pytest.mark.parametrize('case', ['unknown', 'twice', 'same club', 'copy team', 'seattle', 'short of goalies',
                                  'no room'])
def test_refused_trades_change_nothing(db, case):
    f0, g2 = players(db, 0, 'F')[0][0], players(db, 2, 'G')[0][0]
    moves = {
        'unknown': [(99_999_999, 1)],
        'twice': [(f0, 1), (f0, 2)],
        'same club': [(f0, 0)],
        'copy team': [(f0, 31)],
        'seattle': [(f0, U.MIRROR)],
        'short of goalies': [(g2, X.FA)],
        'no room': [(gid, 0) for gid, *_ in players(db, 1)[:41 - len(players(db, 0))]],
    }[case]
    before = db.to_bytes()
    assert X.preview(db, moves).problems
    with pytest.raises(X.TradeError) as err:
        X.move_players(db, moves)
    assert err.value.problems and db.to_bytes() == before


def test_compare_finds_the_moves_made_in_the_game(db, game):
    theirs = game.default_db()
    a, b = players(theirs, 0, 'F')[0][0], free_skater(theirs)['game_id']
    X.move_players(theirs, [(a, 1), (b, 7)])
    out = X.compare(db, theirs)
    assert {m[0]: (m[3], m[4]) for m in out.moves} == {a: (0, 1), b: (X.FA, 7)}
    assert not out.different and not out.skipped and out.common > 6000
    assert X.compare(db, db).moves == []
    # taking them back brings the open roster to the same clubs
    X.move_players(db, [(m[0], m[4]) for m in out.moves])
    assert X.compare(db, theirs).moves == []
