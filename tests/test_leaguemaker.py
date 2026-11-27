"""League maker (v1.00.0; overtime_core/leaguemaker.py, app/leaguemaker_ctl.py, myedits `leagues`, the names layer's
league texts): a league of the user's own clubs (a KHL) in one of NHL 19's club league slots. Its clubs go into the
roster as one change (the places keep their players), the name is not roster data: My edits keeps the league with its
name, every update puts its clubs back, and Patch serves the name on the slot's texts (test_overlay)."""
import json
import os

import pytest

from overtime_core import leaguemaker as LM, overlay
from overtime_core.tdb import Database
from overtime_roster.app import myedits, patch_ctl, sources

from test_newplayer import app  # noqa: F401 - the Roster tab on the game's own roster, Update offline
from test_update_go import view

KHL = [{'name': 'CSKA Moscow', 'city': 'Moscow', 'nickname': 'CSKA', 'abbr': 'CSKA'},
       {'name': 'SKA Saint Petersburg', 'city': 'Saint Petersburg', 'nickname': 'SKA', 'abbr': 'SKA'},
       {'name': 'Dynamo Moscow', 'city': 'Moscow', 'nickname': 'Dynamo', 'abbr': 'DYN'}]
TEXT = 'CSKA Moscow | Moscow | CSKA | CSKA\nSKA Saint Petersburg | Saint Petersburg | SKA | SKA\nDynamo Moscow | DYN\n'


def tables(db, but=()):
    return {t.name: t.rows() for t in db.tables if t.name not in but}


# --- overtime_core.leaguemaker ----------------------------------------------------------------------------------------
@pytest.mark.game
def test_a_league_takes_its_slots_places_and_nothing_else(game_db):
    raw, schema = game_db
    db, stock = Database.parse(raw, schema), Database.parse(raw, schema)
    before = LM.places(db, 'del')
    assert len(before) == 14 and [s['key'] for s in LM.slots(db)] == list(LM.SLOTS)
    done = LM.make(db, {'name': 'KHL', 'slot': 'del', 'clubs': KHL}, {r['index']: r for r in stock['exhibitionteams'].rows()})
    assert done['slot'] == 'del' and done['name'] == 'KHL'
    assert [(i, new) for i, _old, new in done['clubs']] == [(s['index'], c['name']) for s, c in zip(before, KHL)]
    after = LM.places(db, 'del')
    assert [(s['name'], s['city'], s['nickname'], s['abbr']) for s in after[:3]] == \
        [(c['name'], c['city'], c['nickname'], c['abbr']) for c in KHL]
    assert after[3:] == before[3:]                          # a place the league gives no club keeps its own
    assert tables(db, ('exhibitionteams',)) == tables(stock, ('exhibitionteams',))   # players, calendars: untouched
    assert LM.from_db(db, 'del', 'KHL')['clubs'][:3] == LM.normalise({'clubs': KHL})['clubs']
    assert LM.from_db(db, 'del')['name'] == ''          # the name is not roster data


@pytest.mark.game
def test_a_league_the_roster_cannot_take_changes_nothing(game_db):
    raw, schema = game_db
    db = Database.parse(raw, schema)
    stock = {r['index']: r for r in db['exhibitionteams'].rows()}
    berlin = LM.places(db, 'del')[0]
    cases = [({'name': '', 'slot': 'del', 'clubs': KHL}, 'Give the league a name.'),
             ({'name': 'K' * 25, 'slot': 'del', 'clubs': KHL}, 'the game holds 24'),
             ({'name': 'KHL', 'slot': 'nhl', 'clubs': KHL}, 'There is no league slot nhl'),
             ({'name': 'KHL', 'slot': 'del', 'clubs': []}, 'Add at least one club.'),
             ({'name': 'KHL', 'slot': 'del', 'clubs': KHL * 5}, 'DEL has 14 places and the league 15 clubs'),
             ({'name': 'KHL', 'slot': 'del', 'clubs': [dict(KHL[0], abbr='CSKAX')]}, 'must be 1-4 letters'),
             ({'name': 'KHL', 'slot': 'del', 'clubs': [dict(KHL[0], abbr='C-K')]}, 'must be 1-4 letters'),
             ({'name': 'KHL', 'slot': 'del', 'clubs': [KHL[0], dict(KHL[1], abbr='CSKA')]}, 'share the abbreviation'),
             ({'name': 'KHL', 'slot': 'del', 'clubs': [dict(KHL[0], abbr='')]}, 'has no abbreviation'),
             ({'name': 'KHL', 'slot': 'del', 'clubs': [dict(KHL[0], name='X' * 40)]}, 'longer than the game'),
             ({'name': 'KHL', 'slot': 'del', 'clubs': [dict(KHL[0], abbr=berlin['abbr'])]},
              f"was {berlin['name']}'s abbreviation")]
    raw_before = db.to_bytes()
    for league, why in cases:
        with pytest.raises(LM.LeagueError) as err:
            LM.make(db, league, stock)
        assert any(why in p for p in err.value.problems), (why, err.value.problems)
    assert db.to_bytes() == raw_before
    problems, notes = LM.check(db, {'name': 'KHL', 'slot': 'del', 'clubs': KHL}, stock)
    assert problems == [] and any('11 keep their clubs' in n for n in notes)


def test_league_files_and_typed_clubs():
    lg = LM.loads(LM.dumps({'name': ' KHL ', 'slot': 'DEL', 'clubs': [dict(KHL[0], abbr='cska')]}))
    assert lg == {'format': LM.FORMAT, 'version': LM.VERSION, 'name': 'KHL', 'slot': 'del', 'clubs': [KHL[0]]}
    clubs = LM.parse_clubs(TEXT)
    assert clubs[:2] == KHL[:2] and (clubs[2]['name'], clubs[2]['abbr'], clubs[2]['city']) == ('Dynamo Moscow', 'DYN', '')
    assert LM.normalise({'clubs': clubs})['clubs'][2]['nickname'] == 'Dynamo Moscow'    # no nickname: the name
    assert [c['abbr'] for c in LM.parse_clubs('A;B;C;AA\nX\tY\tZ\tXY\nP, PP')] == ['AA', 'XY', 'PP']
    for bad, why in (('{', 'not a league file'), ('{"format": "overtime-roster"}', 'not a league file'),
                     ('{"format": "overtime-league", "version": 9, "clubs": []}', 'version 9'),
                     ('[1]', 'holds one league'), ('{"clubs": "x"}', 'no list of clubs'),
                     ('{"clubs": [1]}', 'Club 1 is not a club')):
        with pytest.raises(LM.LeagueError) as err:
            LM.loads(bad)
        assert why in err.value.problems[0], (bad, err.value.problems)


# --- the app: the window, Save into My edits, Update, Patch ---------------------------------------------------------
def window(c):
    return c.host.snap('leaguemaker')['window']


def make_khl(c, slot='del', name='KHL', text=TEXT):
    assert c.calls['leaguemaker_open'](slot) is None
    return c.calls['leaguemaker_make']({'name': name, 'clubs': text})


def del_names(c, n=3):
    return [p['name'] for p in LM.places(c.session.db, 'del')[:n]]


def save(c):
    c.calls['save_name']('Mine')
    assert c.calls['save'](None) is None and c.parts['save'].unsaved() == 0


@pytest.mark.game
def test_the_window_makes_a_league_as_one_change(app):  # noqa: F811
    c = app
    s = c.session
    assert c.calls['leaguemaker_open']() is None
    w = window(c)
    assert w['values']['slot'] == 'echl' and w['values']['name'] == '' and not w['can_make']
    assert [x['key'] for x in w['slots']] == list(LM.SLOTS) and w['places'] == len(LM.places(s.db, 'echl'))
    rosters = c.parts['rosters']
    for ident, warn in ((sources.GAME_ID, True), ('save:RosterCustom0', False)):   # the Game roster warning
        rosters.open_id = ident
        assert window(c)['game_roster'] is warn
    c.calls['leaguemaker_set']('slot', 'del')
    stock = del_names(c, 14)
    assert window(c)['values']['clubs'].splitlines()[0].startswith(stock[0] + ' | ')
    before, raw = len(s.history), s.db.to_bytes()
    bad = c.calls['leaguemaker_make']({'name': 'KHL', 'clubs': 'CSKA Moscow | CSKAXX'})
    assert 'error' in bad and window(c)['problems'] and len(s.history) == before
    assert make_khl(c) == {'ok': True}
    assert window(c) is None and len(s.history) == before + 1
    assert del_names(c) == [k['name'] for k in KHL] and del_names(c, 14)[3:] == stock[3:]
    ch = s.history[-1]
    assert ch.label == 'League KHL (DEL)' and ch.tab == 'Roster'
    assert c.parts['leaguemaker'].name_of('del') == 'KHL'
    assert c.calls['leaguemaker_open']('del') is None and window(c)['values']['name'] == 'KHL'
    assert next(x for x in window(c)['slots'] if x['key'] == 'del')['name'] == 'KHL'
    c.calls['leaguemaker_close']()
    s.undo()
    assert s.db.to_bytes() == raw and c.parts['leaguemaker'].name_of('del') == ''
    # a name alone (the clubs as they are) is still a change: Save keeps the name for Patch
    assert c.calls['leaguemaker_open']('del') is None
    assert c.calls['leaguemaker_make']({'name': 'DEL Pro'}) == {'ok': True}
    assert s.db.to_bytes() == raw and s.history[-1].label == 'League DEL Pro (DEL)'


@pytest.mark.game
def test_save_keeps_the_league_and_update_and_patch_follow_it(app):  # noqa: F811
    c = app
    assert make_khl(c) == {'ok': True}
    save(c)
    kept = myedits.load()['leagues']
    assert list(kept) == ['del'] and kept['del']['name'] == 'KHL'
    assert kept['del']['clubs'] == LM.normalise({'clubs': LM.parse_clubs(TEXT)})['clubs']
    rows = c.host.snap('save')['kept']
    assert rows[0]['key'] == myedits.LEAGUE + 'del' and rows[0]['label'] == 'KHL league'
    # Patch serves the kept leagues; the card tells a league kept since the patch
    assert patch_ctl.kept_leagues(c) == [kept['del']]
    digest = overlay.leagues_digest([kept['del']])
    assert not patch_ctl.leagues_changed(c, {'layers': {'names': {'leagues_sha256': digest}}})
    assert patch_ctl.leagues_changed(c, {'layers': {'names': {'strings': 30}}})
    assert not patch_ctl.leagues_changed(c, {'layers': {}})            # no names layer: no league texts at all
    # Update twice over it: the clubs stay; the game's own roster again: the update puts them back
    for _ in range(2):
        assert c.calls['update_go']() is None
        assert view(c.host)['result']['kind'] == 'good', c.host.lines[-30:]
        assert del_names(c) == [k['name'] for k in KHL]
    c.load_source(sources.GAME_ID)
    assert del_names(c) != [k['name'] for k in KHL]
    assert c.calls['update_go']() is None
    assert view(c.host)['result']['kind'] == 'good', c.host.lines[-30:]
    assert del_names(c) == [k['name'] for k in KHL]
    assert c.parts['leaguemaker'].name_of('del') == 'KHL'               # the window names it from My edits
    # My edits' Remove: the slot is the update's again, the roster keeps its clubs
    assert c.calls['myedits_remove'](myedits.LEAGUE + 'del') == {'ok': True}
    assert myedits.load()['leagues'] == {} and patch_ctl.kept_leagues(c) == []
    assert del_names(c) == [k['name'] for k in KHL]


@pytest.mark.game
def test_a_league_taken_back_and_saved_leaves_my_edits_as_before(app):  # noqa: F811
    c = app
    s = c.session
    assert make_khl(c) == {'ok': True}
    save(c)
    assert make_khl(c, name='MHL', text='Red Army | RA\n') == {'ok': True}
    save(c)
    assert myedits.load()['leagues']['del']['name'] == 'MHL'
    s.undo()                    # MHL taken back: KHL is the roster's again, and My edits'
    save(c)
    assert myedits.load()['leagues']['del']['name'] == 'KHL'
    s.undo()                    # KHL too: My edits as it was before the session made a league
    save(c)
    assert myedits.load()['leagues'] == {}


@pytest.mark.game
def test_back_to_the_game_own_clubs_takes_the_kept_league_away(app):  # noqa: F811
    c = app
    stock = del_names(c, 14)
    assert make_khl(c) == {'ok': True}
    save(c)
    assert c.calls['leaguemaker_open']('del') is None
    assert c.calls['leaguemaker_reset']() == {'ok': True}
    assert del_names(c, 14) == stock and window(c)['values']['name'] == ''
    assert c.parts['leaguemaker'].drafts() == ''        # the window shows the slot as it is: nothing to make
    save(c)
    c.calls['leaguemaker_set']('name', 'VHL')
    assert c.parts['leaguemaker'].drafts()               # typed and not made: Save asks first
    assert myedits.load()['leagues'] == {}


@pytest.mark.game
def test_import_and_export_a_league_file(app, tmp_path):  # noqa: F811
    c = app
    path = tmp_path / 'khl.league.json'
    path.write_text(LM.dumps({'name': 'KHL', 'slot': 'del', 'clubs': KHL}), encoding='utf-8')
    assert c.calls['leaguemaker_import_path'](str(path)) == {'ok': True}
    w = window(c)
    assert w['values']['slot'] == 'del' and w['values']['name'] == 'KHL' and w['problems'] == []
    assert LM.parse_clubs(w['values']['clubs']) == KHL
    assert c.calls['leaguemaker_make']() == {'ok': True}
    bad = tmp_path / 'bad.json'
    bad.write_text('{"format": "something"}', encoding='utf-8')
    assert 'error' in c.calls['leaguemaker_import_path'](str(bad))
    out = tmp_path / 'out'
    out.mkdir()
    c.host.pick = lambda folder, start, kinds: str(out)
    assert c.calls['leaguemaker_open']('del') is None
    got = c.calls['leaguemaker_export']()
    assert got['path'] == os.path.join(str(out), 'KHL.league.json')
    with open(got['path'], encoding='utf-8') as f:
        lg = json.load(f)
    assert lg['name'] == 'KHL' and lg['slot'] == 'del' and lg['clubs'][:3] == KHL and len(lg['clubs']) == 14


def test_the_patch_card_asks_for_a_patch_when_the_kept_leagues_changed():
    f = {'busy': None, 'checked': True, 'running': False, 'match_setup': False, 'error': None, 'patched': True,
         'problems': [], 'online': True, 'changed': False, 'leagues_changed': True}
    line = patch_ctl.state_line(f)
    assert line['tone'] == 'caution' and 'leagues changed' in line['text'] and 'Patch again' in line['text']
    assert patch_ctl.state_line(dict(f, changed=True))['text'].startswith('Patched. You changed the switches')
