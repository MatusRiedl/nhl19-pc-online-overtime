"""My edits: the Roster tab's player edits, kept in edits.json (the app folder) when Save writes them and put back
after every Update (Go and Apply), as Legacy's edits.json. docs/ui/update.md "My edits".

A kept edit is one player's: `id` is who he was before his first kept edit (first, last, real birth date: the person
key the update's matcher knows him by), `label` his name now. It holds the latest value of everything that was
changed: `card` {key: value} in the card's units (roster_card.values; ratings as 'ratings': {field: value}), `face`
{'style': type, 'parts': {part: value}}, `gear` {choice: value}. A renamed player is still found (every mix of his old
and new name and birth date), and the update's plan matches him to NHL.com under his old name (`aliases`).

A team's hand-set lines are kept too (`lines`, key "league:abbr"): the places the Lines tab applied and Save wrote
(slot -> the player's id as above) and the letters (player -> 0, C 1, A 2). They go back after the update's lines,
real or by rating: the player's line always wins. A player who has left the team is skipped with his reason.

It is put back through the Roster tab's own checks and writers (roster_card.check / write, faces, equipment), one
change per part: a part the roster refuses changes nothing and is skipped with its reason (a card value that is
refused, such as a number another player has now, is skipped alone; the rest of the card goes in).

A player the user made (New player, v1.00.0: overtime_core.newplayer) keeps a `new` part too: {'pos', 'team':
{'index', 'league', 'abbr', 'name'} or {'fa': True}}, with his card's values as he was made. NHL.com does not list
him: the update's plan leaves him alone (made_ids), and after the update he is made again when the roster does not have
him (a new roster, the game's own) or moved back to his club when a club league's rebuild or a release moved him,
before his other parts go back.

A league the user made (League maker, v1.00.0: overtime_core.leaguemaker) is kept whole under `leagues`, by its slot
({'name', 'slot', 'clubs'}, as a league file holds it): after the update it is written again over the slot's places
first, so the clubs' kept lines (keyed by the league's abbreviations) find their teams. A slot set back to the game's own
and saved is no longer kept.
"""
import json

from overtime_core import durable, equipment as EQ, faces as F, leaguemaker as LM, lines as LN, newplayer as NP, \
    rosterupdate as U, trades as X
from overtime_core.roster import ALTERNATE, CAPTAIN

from . import labels as L, paths, roster_card as RC
from .session import TEAMS, EditError

VERSION = 1
FILE = 'edits.json'
PARTS = ('card', 'face', 'gear')
NEW = 'new'         # a player the user made: kept with or without other parts
PART_WORDS = {'card': 'card', 'face': 'face & type', 'gear': 'equipment', 'lines': 'lines', NEW: 'new player'}
MADE_CARD = ('first', 'last', 'num', 'pos', 'shoots', 'born', 'country', 'height', 'weight')
LINES = 'lines|'     # the prefix of a team's kept lines among the rows of My edits
LEAGUES = 'leagues'
LEAGUE = 'league|'   # the prefix of a kept league among the rows of My edits
NAME_KEYS = ('first', 'last', 'born')


# --- the file ------------------------------------------------------------------------------------------------------
def where():
    return paths.app_dir(FILE)


def empty():
    return {'version': VERSION, 'players': {}, 'lines': {}, LEAGUES: {}}


def load(path=None):
    """edits.json, or an empty one (no file, or one this version cannot read)."""
    try:
        with open(path or where(), encoding='utf-8') as f:
            data = json.load(f)
    except (OSError, ValueError):
        return empty()
    if not isinstance(data, dict) or data.get('version') != VERSION or not isinstance(data.get('players'), dict):
        return empty()
    data['players'] = {k: e for k, e in data['players'].items()
                       if isinstance(e, dict) and isinstance(e.get('id'), dict)}
    kept = data.get('lines')
    data['lines'] = {k: e for k, e in (kept.items() if isinstance(kept, dict) else ())
                     if isinstance(e, dict) and isinstance(e.get('slots'), dict) and isinstance(e.get('letters'), list)}
    kept = data.get(LEAGUES)
    data[LEAGUES] = {}
    for k, e in (kept.items() if isinstance(kept, dict) else ()):
        try:
            league = LM.normalise(e)
        except LM.LeagueError:
            continue
        if league['slot'] == k and k in LM.SLOTS and league['name'] and league['clubs']:
            data[LEAGUES][k] = league
    return data


def count(data):
    """How many things edits.json keeps: players, teams' lines and leagues."""
    return len(data['players']) + len(data.get('lines') or {}) + len(data.get(LEAGUES) or {})


def save(data, path=None):
    """Write edits.json whole or not at all (a temporary file, then a rename)."""
    path = path or where()
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    durable.replace(tmp, path)


# --- who a player is -----------------------------------------------------------------------------------------------
def plain_name(first, last):
    return ' '.join(RC.plain(f'{first or ""} {last or ""}').split())


def person_key(first, last, born):
    return f"{plain_name(first, last)}|{born or ''}"


def identity(s, clock, pi):
    """{'first', 'last', 'born'} of player pi now (born: his real birth date, as on the card)."""
    _, b = s.bio(pi)
    return {'first': b['firstname'], 'last': b['lastname'], 'born': clock.born(b)}


def keys_of(e):
    """The person keys he may have now, newest first: his new name and birth date, either one alone, his old ones (an
    update puts NHL.com's birth date back but leaves a name alone)."""
    i, card = e['id'], e.get('card') or {}
    names = [(card.get('first', i['first']), card.get('last', i['last'])), (i['first'], i['last'])]
    borns = [card.get('born', i['born']), i['born']]
    out = []
    for first, last in names:
        for born in borns:
            k = person_key(first, last, born)
            if k not in out:
                out.append(k)
    return out


def index(s, clock):
    """({person key: playerindex}, {plain name: [playerindex]}) of every player of the roster (his main card:
    rosterupdate.State.main_pi)."""
    state = U.State(s.db)
    keys, names = {}, {}
    for gid in s.bio_row:
        pi = state.main_pi(gid)
        if pi is None:
            continue
        _, b = s.bio(pi)
        if b is not None:
            keys.setdefault(person_key(b['firstname'], b['lastname'], clock.born(b)), pi)
            names.setdefault(plain_name(b['firstname'], b['lastname']), []).append(pi)
    return keys, names


def locate(e, found, shift=0):
    """The playerindex of the player of kept edit `e` in the roster (`found`: index()), or None: one of his person
    keys (`shift`: the roster's clock shift; his birth date that many years on too, as a bio the update did not place
    keeps its stored year), else his name alone when one player of the roster has it (a birth date read on another
    clock)."""
    keys, names = found
    mine = keys_of(e)
    if shift:
        mine += [k for k in (_shifted(k, shift) for k in list(mine)) if k and k not in mine]
    pi = next((keys[k] for k in mine if k in keys), None)
    if pi is None:
        for k in mine:
            hits = names.get(k.split('|')[0], ())
            if len(hits) == 1:
                return hits[0]
    return pi


def _shifted(key, shift):
    name, _, born = key.partition('|')
    try:
        return f"{name}|{int(born[:4]) + shift:04d}{born[4:]}" if len(born) == 10 else None
    except ValueError:
        return None


def made_ids(data, s, clock):
    """Game ids of the kept players the user made who are in the roster: the update's plan leaves them alone
    (rosterupdate.plan `keep`)."""
    if not any(e.get(NEW) for e in data['players'].values()):
        return set()
    found = index(s, clock)
    out = set()
    for e in data['players'].values():
        if e.get(NEW):
            pi = locate(e, found, clock.shift)
            if pi is not None:
                out.add(s.bio(pi)[1]['game_id'])
    return out


def team_of(s, pi):
    """His `new` part's team: {'index', 'league', 'abbr', 'name'} of his club, or {'fa': True}."""
    _, e = s.entry(pi)
    if e is None:
        return {'fa': True}
    team = e['team']
    i = s.team_row.get(team)
    league = s.rows[TEAMS][i]['league'] if i is not None else None
    return {'index': team, 'league': league, 'abbr': s.team_abbr(team), 'name': s.team_name(team)}


def team_in(s, spec):
    """The club (team index) or FA of a `new` part's team in this roster, or None: its league and abbreviation, else its
    index when that slot is still in its league."""
    if spec.get('fa'):
        return X.FA
    clubs = X.club_teams(s.db)
    hit = [t for t, lg in clubs.items() if lg == spec.get('league') and s.team_abbr(t) == spec.get('abbr')]
    if hit:
        return hit[0]
    return spec.get('index') if clubs.get(spec.get('index')) == spec.get('league') else None


def aliases(data, s, clock):
    """{game_id: (first, last, real birth date or None)} of the kept players whose name or birth date the user
    changed: the update's plan matches them to NHL.com as they were (rosterupdate.plan `aliases`), so a renamed player
    is not released. The birth date only when it was changed (else the roster's own stored one matches)."""
    found = index(s, clock)
    out = {}
    for e in data['players'].values():
        if e.get(NEW):
            continue    # NHL.com does not list him (made_ids)
        i, card = e['id'], e.get('card') or {}
        renamed = (plain_name(card.get('first', i['first']), card.get('last', i['last']))
                   != plain_name(i['first'], i['last']))
        reborn = card.get('born', i['born']) != i['born']
        if not (renamed or reborn):
            continue
        pi = locate(e, found)
        if pi is None:
            continue
        _, b = s.bio(pi)
        out[b['game_id']] = (i['first'], i['last'], i['born'] if reborn and i['born'] else None)
    return out


def find(data, ident):
    """The key of the kept edit of the player who is `ident` now, or None."""
    k = person_key(ident['first'], ident['last'], ident['born'])
    return next((key for key, e in data['players'].items() if k in keys_of(e)), None)


# --- keeping them --------------------------------------------------------------------------------------------------
def record(data, s, clock, items):
    """Keep the edits `items` ([{pi, what, kept, ident}]: roster_card.Edits items Save just wrote; ident: who he was
    before that edit) with the values he has now. Returns how many players' edits changed."""
    touched = set()
    for it in items:
        pi = it['pi']
        _, b = s.bio(pi)
        if b is None or it['what'] not in PARTS + (NEW,):
            continue
        ident = it.get('ident') or identity(s, clock, pi)
        key = find(data, ident) or find(data, identity(s, clock, pi))
        if key is None:
            key = person_key(ident['first'], ident['last'], ident['born'])
            data['players'][key] = {'id': dict(ident)}
        e = data['players'][key]
        if it['what'] == NEW:
            now = RC.values(s, clock, pi)
            e[NEW] = {'pos': now['pos'], 'team': team_of(s, pi)}
            e.setdefault('card', {}).update({k: now[k] for k in MADE_CARD})
        else:
            _keep(e, s, clock, pi, b, it['what'], it.get('kept', it['keys']))
        e['label'] = s.name(b)
        team = RC.rail_team(s, pi)
        e['team'] = s.team_abbr(team) or str(team)
        touched.add(key)
    return len(touched)


def follow_made(data, s, clock):
    """The made players' clubs as the roster has them now (a Move / trade since): Save keeps where he plays. Returns how
    many changed."""
    if not any(e.get(NEW) for e in data['players'].values()):
        return 0
    found = index(s, clock)
    n = 0
    for e in data['players'].values():
        if not e.get(NEW):
            continue
        pi = locate(e, found, clock.shift)
        if pi is None:
            continue
        team = team_of(s, pi)
        if e[NEW].get('team') != team:
            e[NEW]['team'] = team
            e['team'] = 'FA' if team.get('fa') else team['abbr'] or str(team['index'])
            n += 1
    return n


def team_key(s, team):
    """(key of a team's kept lines, its league, its abbreviation): the abbreviation is only known inside a league."""
    t = s.rows[TEAMS][s.team_row[team]]
    abbr = s.team_abbr(team)
    return f"{t['league']}:{abbr}", t['league'], abbr


def record_lines(data, s, clock, team, slots, letters):
    """Keep the lines a team's Lines tab applied: `slots` {slot: playerindex of its new holder}, `letters`
    {playerindex: 0, C or A}. A later one over an earlier one, place by place and player by player."""
    key, league, abbr = team_key(s, team)
    e = data.setdefault('lines', {}).setdefault(key, {'abbr': abbr, 'league': league, 'slots': {}, 'letters': []})
    e['label'] = s.team_name(team)
    for slot, pi in slots.items():
        if pi is not None and s.bio(pi)[1] is not None:
            e['slots'][slot] = identity(s, clock, pi)
    for pi, value in letters.items():
        if s.bio(pi)[1] is None:
            continue
        ident = identity(s, clock, pi)
        k = person_key(ident['first'], ident['last'], ident['born'])
        e['letters'] = [x for x in e['letters'] if person_key(**x['id']) != k] + [{'id': ident, 'value': value}]


def _keep(e, s, clock, pi, b, what, keys):
    if what == 'card':
        now = RC.values(s, clock, pi)
        card = e.setdefault('card', {})
        for k in keys:
            if k.startswith('ratings.'):
                f = k[len('ratings.'):]
                if f in now['ratings']:
                    card.setdefault('ratings', {})[f] = now['ratings'][f]
            elif k in now:
                card[k] = now[k]
    elif what == 'face':
        face = e.setdefault('face', {})
        _t, _r, ai = s.ai(b)
        if 'style' in keys and ai:
            face['style'] = ai.get(F.STYLE)
        parts = {k: v for k, v in F.read(b).items() if k in keys}
        if parts:
            face.setdefault('parts', {}).update(parts)
    elif what == 'gear':
        kind = EQ.kind_of(b['position'])
        row = EQ.row_of(s.db, b['game_id'], kind)
        if row is not None:
            now = EQ.read(s.db, row, kind)
            e.setdefault('gear', {}).update({k: now[k] for k in keys if k in now})


def forget(data, s, clock, items):
    """Drop what the taken-back edits `items` kept (saved earlier, then taken back and saved again), unless a later
    edit still keeps it. Returns how many players' edits changed."""
    touched = set()
    for it in items:
        key = find(data, it.get('ident') or {}) if it.get('ident') else None
        if key is None and s.bio(it['pi'])[1] is not None:
            key = find(data, identity(s, clock, it['pi']))
        e = data['players'].get(key) if key else None
        if e is None:
            continue
        if it['what'] == NEW:       # his making taken back: nothing of him is kept
            del data['players'][key]
            touched.add(key)
            continue
        part = e.get(it['what'])
        if not isinstance(part, dict):
            continue
        for k in it.get('kept', it['keys']):
            if it['what'] == 'card' and k.startswith('ratings.'):
                (part.get('ratings') or {}).pop(k[len('ratings.'):], None)
                if part.get('ratings') == {}:
                    part.pop('ratings')
            elif it['what'] == 'face' and k != 'style':
                (part.get('parts') or {}).pop(k, None)
                if part.get('parts') == {}:
                    part.pop('parts')
            else:
                part.pop(k, None)
        if not part:
            e.pop(it['what'])
        if not any(p in e for p in PARTS + (NEW,)):
            del data['players'][key]
        touched.add(key)
    return len(touched)


def record_league(data, league):
    """Keep a league the League maker made (its slot's latest), or forget the slot's ({'slot', 'reset': True})."""
    kept = data.setdefault(LEAGUES, {})
    if league.get('reset'):
        kept.pop(league['slot'], None)
    else:
        kept[league['slot']] = LM.normalise(league)


def remove(data, key):
    if key.startswith(LEAGUE):
        return (data.get(LEAGUES) or {}).pop(key[len(LEAGUE):], None) is not None
    if key.startswith(LINES):
        return (data.get('lines') or {}).pop(key[len(LINES):], None) is not None
    return data['players'].pop(key, None) is not None


def words(e):
    """['number #94', 'cap hit $1.5M', '3 ratings', 'face & type', 'equipment'] of one kept edit."""
    out = []
    card = e.get('card') or {}
    made = e.get(NEW)
    if made:
        team = made.get('team') or {}
        club = 'free agent' if team.get('fa') else team.get('name') or team.get('abbr') or 'a club'
        out.append(f'new player, {club}')
    for k in RC.ORDER:
        if k in card and not (made and k in MADE_CARD):
            out.append(f'{RC.WORDS[k]} {RC.shown(k, card[k])}')
    n = len(card.get('ratings') or {})
    if n:
        out.append('1 rating' if n == 1 else f'{n} ratings')
    face = e.get('face') or {}
    if 'style' in face:
        out.append('player type')
    if face.get('parts'):
        out.append('face')
    if e.get('gear'):
        out.append('equipment')
    return out


def line_words(e):
    """['3 places', '1 letter'] of one team's kept lines."""
    out = []
    n = len(e['slots'])
    if n:
        out.append(f"{n} place{'s' if n != 1 else ''}")
    n = len(e['letters'])
    if n:
        out.append(f"{n} letter{'s' if n != 1 else ''}")
    return out


def rows(data):
    """The list of kept edits, by last name: [{key, label, team, words}]."""
    def last(k):
        e = data['players'][k]
        return RC.plain((e.get('card') or {}).get('last', e['id']['last']))
    out = [{'key': k, 'label': e.get('label') or f"{e['id']['first']} {e['id']['last']}", 'team': e.get('team', ''),
            'words': words(e)} for k, e in data['players'].items()]
    out = sorted(out, key=lambda r: (last(r['key']), RC.plain(r['label']), r['key']))
    teams = [{'key': LINES + k, 'label': f"{e.get('label') or e['abbr']} lines", 'team': e['abbr'],
              'words': line_words(e)} for k, e in (data.get('lines') or {}).items()]
    leagues = [{'key': LEAGUE + k, 'label': f"{e['name']} league", 'team': LM.SLOTS[k][1],
                'words': [f"{len(e['clubs'])} club{'s' if len(e['clubs']) != 1 else ''}", f"in the {LM.SLOTS[k][1]} slot"]}
               for k, e in (data.get(LEAGUES) or {}).items()]
    return sorted(leagues, key=lambda r: RC.plain(r['label'])) + out + sorted(teams, key=lambda r: RC.plain(r['label']))


# --- putting them back ---------------------------------------------------------------------------------------------
def replay(s, clock, data, model_of=lambda table: None, fold=lambda ch: None):
    """Put every kept edit back in the open roster (after an update). Each part of a player is one change (s.edit),
    handed to `fold` (the update folds them into its own change, so one Undo takes both back). Returns {'applied': n
    parts, 'skipped': [{'who', 'part', 'why'}]}."""
    out = replay_leagues(s, data, fold)     # first: the made players' clubs and the kept lines go by its clubs
    found = index(s, clock)
    kept = sorted(data['players'].values(), key=lambda e: RC.plain(e.get('label') or e['id']['last']))
    failed, moved = set(), False
    for e in kept:          # the made players first: made again or moved back, then their parts go back as anyone's
        if not e.get(NEW):
            continue
        who = e.get('label') or f"{e['id']['first']} {e['id']['last']}"
        try:
            went = _put_new(s, clock, e, locate(e, found, clock.shift), who, fold)
        except EditError as err:
            failed.add(id(e))
            out['skipped'].append({'who': who, 'part': PART_WORDS[NEW], 'why': str(err)})
            continue
        out['applied'] += 1
        moved = moved or went
    if moved:
        found = index(s, clock)
    for e in kept:
        if id(e) in failed:
            continue
        who = e.get('label') or f"{e['id']['first']} {e['id']['last']}"
        pi = locate(e, found, clock.shift if e.get(NEW) else 0)
        if pi is None:
            out['skipped'].append({'who': who, 'part': 'player', 'why': 'He is not in this roster.'})
            continue
        for part in PARTS:
            if not e.get(part):
                continue
            try:
                went, refused = _put(s, clock, pi, part, e[part], model_of, fold)
            except EditError as err:
                went, refused = False, [str(err)]
            out['applied'] += went
            out['skipped'] += [{'who': who, 'part': PART_WORDS[part], 'why': why} for why in refused]
    back = replay_lines(s, clock, data, fold)
    out['applied'] += back['applied']
    out['skipped'] += back['skipped']
    return out


def replay_leagues(s, data, fold=lambda ch: None):
    """Put every kept league back over its slot (after an update): one change a league that differs. Returns
    {'applied': leagues changed, 'skipped': [{'who', 'part', 'why'}]}."""
    out = {'applied': 0, 'skipped': []}
    for key, league in sorted((data.get(LEAGUES) or {}).items()):
        who = f"{league['name']} league"
        if LM.from_db(s.db, key, league['name'])['clubs'][:len(league['clubs'])] == LM.normalise(league)['clubs']:
            continue        # its clubs are there (its name is the names layer's: Patch)

        def work(db, lg=league, who=who):
            done = LM.make(db, lg)
            return [(f"My edits: {lg['name']}: {new}", old, f'place {index}') for index, old, new in done['clubs']
                    if old != new], None
        try:
            ch, _ = s.bulk(f'My edits: {who}', work)
        except LM.LeagueError as err:
            out['skipped'].append({'who': who, 'part': 'league', 'why': err.problems[0]})
            continue
        fold(ch)
        out['applied'] += 1
    return out


def _put_new(s, clock, e, pi, who, fold):
    """A made player back in the roster: made again when it does not have him (`pi` None), moved back to his club when
    he is elsewhere. Returns whether the roster changed; raises EditError with the reason it refuses."""
    spec = e[NEW]
    team = team_in(s, spec.get('team') or {'fa': True})
    if team is None:
        name = (spec.get('team') or {}).get('name') or 'His club'
        raise EditError(f'{name} is not in this roster.')
    deal_years = 1 + (1 if RC.expansion(s) else 0)     # as the Move / trade window's
    if pi is None:
        card, i = e.get('card') or {}, e['id']
        args = (card.get('first', i['first']), card.get('last', i['last']), card.get('pos') or spec.get('pos'),
                card.get('shoots') or 'L', card.get('born') or i['born'], team, clock.shift, deal_years)

        def make(db):
            NP.create(db, *args)
            return [(f'My edits: {who}', '', 'new player')], None
        _bulk(s, f'My edits: {who}: new player', make, fold)
        return True
    _, now = s.entry(pi)
    where = now['team'] if now is not None else X.FA
    if where == team and (team != X.FA or pi in set(s.free_agents)):
        return False
    if where == team:       # a free agent the update retired (off the list): on the list again

        def relist(db):
            U._rebuild_free(db, remove=(), add=[pi])
            return [(f'My edits: {who}', '', 'free agent again')], None
        _bulk(s, f'My edits: {who}: free agent', relist, fold)
        return True
    gid = s.bio(pi)[1]['game_id']

    def move(db):
        X.move_players(db, [(gid, team)], deal_years)
        return [(f'My edits: {who}', '', 'back to his club' if team != X.FA else 'free agent again')], None
    _bulk(s, f'My edits: {who}: his club', move, fold)
    return True


def _bulk(s, label, work, fold):
    try:
        ch, _ = s.bulk(label, work)
    except X.TradeError as err:
        raise EditError(err.problems[0] if err.problems else str(err)) from None
    except (U.UpdateError, ValueError) as err:
        raise EditError(str(err)) from None
    fold(ch)


def replay_lines(s, clock, data, fold=lambda ch: None):
    """Put every team's kept lines back over what the update dealt (the player's line wins). One change a team that
    differs. Returns {'applied': teams changed, 'skipped': [{'who', 'part', 'why'}]}."""
    out = {'applied': 0, 'skipped': []}
    kept = data.get('lines') or {}
    if not kept:
        return out
    found = index(s, clock)
    teams = {(t['league'], s.team_abbr(t['index'])): t['index'] for t in s.rows[TEAMS] if t['index'] in s.team_entries}
    for e in sorted(kept.values(), key=lambda e: RC.plain(e.get('label') or e['abbr'])):
        who = e.get('label') or e['abbr']
        team = teams.get((e['league'], e['abbr']))
        if team is None:
            out['skipped'].append({'who': who, 'part': 'lines', 'why': 'The team is not in this roster.'})
            continue
        try:
            ch, refused = _put_lines(s, found, team, e, who)
        except EditError as err:
            ch, refused = None, [str(err)]
        if ch is not None and ch.snaps:
            fold(ch)
            out['applied'] += 1
        out['skipped'] += [{'who': who, 'part': 'lines', 'why': why} for why in refused]
    return out


def _put_lines(s, found, team, e, who):
    """One team's kept lines over the open roster: (the change, [why] of each place or letter refused)."""
    refused = []
    mine = set(s.players_of(team))

    def here(ident):
        pi = locate({'id': ident}, found)
        if pi is None or pi not in mine:
            refused.append(' '.join(f"{ident['first']} {ident['last']} is not on {who} now.".split()))
            return None
        return pi

    def work(setter):
        for slot in LN.SLOTS:        # even strength first: a scratched player dresses before special teams
            ident = e['slots'].get(slot)
            pi = here(ident) if ident else None
            if pi is None:
                continue
            try:
                LN.place(s.db, team, slot, pi, setter)
            except (LN.NotDressed, ValueError) as err:
                refused.append(str(err))
        for item in e['letters']:
            pi = here(item['id'])
            value = item['value']
            if pi is None or value not in (0, CAPTAIN, ALTERNATE):
                continue
            if value == CAPTAIN:
                for q in mine:
                    i = s.entry_row.get(q)
                    if q != pi and i is not None and s.rows[LN.ROSTER][i]['captain'] == CAPTAIN:
                        setter(LN.ROSTER, i, 'captain', 0)
            setter(LN.ROSTER, s.entry_row[pi], 'captain', value)
    ch, _ = s.edit(f'My edits: {who} lines', work)
    if ch.snaps:
        ch.tab, ch.team = 'Lines', team
        ch.details.append((f'My edits: {who}', '', 'lines'))
    return ch, refused


def _put(s, clock, pi, part, value, model_of, fold):
    """Put one part back: (it went in, or was already so; [why] of each value refused)."""
    _, b = s.bio(pi)
    who = s.name(b)
    if part == 'card':
        typed = dict(value)
        changes, problems = RC.check(s, clock, pi, typed)
        refused = [p['text'] for p in problems]
        if problems:   # the card's other values still go in
            for p in problems:
                if p['key'].startswith('ratings.'):
                    typed['ratings'] = {f: v for f, v in typed.get('ratings', {}).items()
                                        if f'ratings.{f}' != p['key']}
                else:
                    typed.pop(p['key'], None)
            changes, _again = RC.check(s, clock, pi, typed)
        if changes:
            table, _r, _ai = s.ai(b)
            rated = any(k.startswith('ratings.') for k, _o, _n in changes)
            model = model_of(table) if rated and table else None
            ch, _lost = s.edit(f'My edits: {who}', lambda setter: RC.write(s, clock, pi, changes, setter, model))
            for k, old, new in changes:
                if k.startswith('ratings.'):
                    ch.details.append((f'My edits: {who}: {L.rating_label(k[len("ratings."):]).lower()}', old, new))
                else:
                    ch.details.append((f'My edits: {who}: {RC.WORDS[k]}', RC.shown(k, old), RC.shown(k, new)))
            fold(ch)
        return bool(changes) or not problems, refused
    if part == 'face':
        style, parts = value.get('style'), dict(value.get('parts') or {})

        def work(setter):
            if style is not None:
                F.set_type(s.db, pi, int(style), setter, model_of(s.ai(b)[0]))
                for t, row in RC.style_rows(s, pi):
                    if F.STYLE in s.db[t].by_name:
                        setter(t, row, F.STYLE, int(style))
            if parts:
                F.write(s.db, s.bio(pi)[0], parts, setter)
        ch, _ = s.edit(f'My edits: {who}: face & type', work)
        ch.details.append((f'My edits: {who}', '', 'face & type'))
        fold(ch)
        return True, []
    if part == 'gear':
        kind = EQ.kind_of(b['position'])
        row = EQ.row_of(s.db, b['game_id'], kind)
        if row is None:
            return False, ['He has no equipment record.']
        ok, problems = EQ.clean(s.db, value, kind)
        if problems:
            return False, problems
        ch, _ = s.edit(f'My edits: {who}: equipment', lambda setter: EQ.write(s.db, row, ok, kind, setter))
        ch.details.append((f'My edits: {who}', '', 'equipment'))
        fold(ch)
        return True, []
    return False, [f'unknown part {part}']
