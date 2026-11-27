"""League maker (v1.00.0; docs/notes/league-maker.md): a league of the user's own clubs (a KHL, say) in one of NHL 19's
club league slots, as a modder shares it in a league file.

NHL 19 numbers its leagues in the eboot (ids 0-31, the team lists take 0-15), so a new league takes over a slot: its
clubs, one per place (exhibitionteams of the league in `index` order: name, city, nickname and abbreviation), are
written into the roster; the places keep their players and the slot's calendar (it is by place); players come and go
through Move / trade and New player. A place the file gives no club keeps its own.

The league's name is not roster data: a roster file (a save) has no `stockleagues`, and the game's league pickers look
`stockleagues.name` up as a loc id (a plain name shows blank; lab c32d, docs/notes/league-maker.md). The name travels
with the league (the league file, My edits) and the names layer writes it on the slot's own loc ids
(overtime_core.overlay.league_strings).

The league file (JSON):

    {"format": "overtime-league", "version": 1, "name": "KHL", "slot": "echl",
     "clubs": [{"name": "SKA Saint Petersburg", "city": "Saint Petersburg", "nickname": "SKA", "abbr": "SKA"}, ...]}
"""
import json
import re

from . import teams as T

FORMAT, VERSION = 'overtime-league', 1
# the club league slots a league can take: key -> (exhibitionteams.league, the slot as the game names it). Not the NHL
# and AHL (Franchise's own), national teams, prospects or event teams.
SLOTS = {'shl': (2, 'SHL'), 'liiga': (3, 'Liiga'), 'del': (4, 'DEL'), 'extraliga': (5, 'Extraliga'),
         'nl': (6, 'National League'), 'icehl': (7, 'ICE Hockey League'), 'allsvenskan': (8, 'HockeyAllsvenskan'),
         'ohl': (11, 'OHL'), 'qmjhl': (12, 'QMJHL'), 'whl': (13, 'WHL'), 'echl': (15, 'ECHL')}
NAME_MAX = 24           # the pickers' width (stockleagues.name holds 24 bytes)
ABBR_MAX = 4            # the menus' abbreviation texts (NHLTEAMNAME_ABBR3) hold 3-4 letters
CLUB_FIELDS = ('name', 'city', 'nickname', 'abbr')


class LeagueError(ValueError):
    """A league file or league the roster cannot take: `problems` says why, nothing was changed."""

    def __init__(self, problems):
        self.problems = list(problems)
        super().__init__('; '.join(self.problems))


def _width(table, field):
    return table.by_name[field].depth // 8 - 1


def _fits(table, field, text):
    return len((text or '').encode('utf-8')) <= _width(table, field)


def places(db, key):
    """The rows of slot `key` in place order ({'index', 'name', 'city', 'nickname', 'abbr'})."""
    league = SLOTS[key][0]
    rows = sorted((r for r in db[T.TEAMS].rows() if r['league'] == league), key=lambda r: r['index'])
    return [{'index': r['index'], 'name': r['teamname'], 'city': r['cityname'], 'nickname': r['nickname'],
             'abbr': r['abbrname']} for r in rows]


def slots(db):
    """Every slot a league can take: [{'key', 'league', 'game_name', 'places', 'clubs'}]."""
    out = []
    for key, (league, game_name) in SLOTS.items():
        clubs = places(db, key)
        if clubs:
            out.append({'key': key, 'league': league, 'game_name': game_name, 'places': len(clubs), 'clubs': clubs})
    return out


def _clean(text):
    return re.sub(r'\s+', ' ', str(text or '')).strip()


def normalise(league):
    """A league definition with its texts trimmed, the abbreviations upper case and missing fields filled (a club's
    nickname is its name, its city empty). Raises LeagueError for a shape no league has."""
    if not isinstance(league, dict):
        raise LeagueError(['A league file holds one league: {"name", "slot", "clubs"}.'])
    clubs = league.get('clubs')
    if not isinstance(clubs, list):
        raise LeagueError(['The league has no list of clubs.'])
    out = []
    for n, c in enumerate(clubs, 1):
        if not isinstance(c, dict):
            raise LeagueError([f'Club {n} is not a club ({{"name", "city", "nickname", "abbr"}}).'])
        club = {f: _clean(c.get(f)) for f in CLUB_FIELDS}
        club['abbr'] = club['abbr'].upper()
        club['nickname'] = club['nickname'] or club['name']
        out.append(club)
    return {'format': FORMAT, 'version': VERSION, 'name': _clean(league.get('name')),
            'slot': _clean(league.get('slot')).lower(), 'clubs': out}


def check(db, league, stock=None):
    """The league `league` (normalise) on this roster: (problems, notes). Problems stop make(); notes say what the
    league leaves as it is. `stock` {index: exhibitionteams row} of the game's own roster: a club that keeps the
    abbreviation of the club its place had is refused (the menus would keep that club's name)."""
    lg = normalise(league)
    problems, notes = [], []
    if lg['slot'] not in SLOTS:
        return [f"There is no league slot {lg['slot'] or '(none)'}: pick one of {', '.join(SLOTS)}."], notes
    key, slot_name = lg['slot'], SLOTS[lg['slot']][1]
    if not lg['name']:
        problems.append('Give the league a name.')
    elif len(lg['name'].encode('utf-8')) > NAME_MAX:
        problems.append(f"The league name is {len(lg['name'])} letters: the game holds {NAME_MAX}.")
    spots = places(db, key)
    clubs = lg['clubs']
    if not clubs:
        problems.append('Add at least one club.')
    if len(clubs) > len(spots):
        roomy = [f'{SLOTS[k][1]} {len(places(db, k))}' for k in SLOTS if len(places(db, k)) >= len(clubs)]
        problems.append(f'{slot_name} has {len(spots)} places and the league {len(clubs)} clubs. '
                        + (f"Slots with room: {', '.join(roomy)}." if roomy else 'No slot holds that many.'))
    teams = db[T.TEAMS]
    widths = {'name': 'teamname', 'city': 'cityname', 'nickname': 'nickname', 'abbr': 'abbrname'}
    seen = {}
    others = {r['abbrname'].upper() for r in teams.rows() if r['league'] != SLOTS[key][0] and r['abbrname']}
    for n, (club, spot) in enumerate(zip(clubs, spots), 1):
        label = club['name'] or f'Club {n}'
        if not club['name']:
            problems.append(f'Club {n} has no name.')
        if not club['abbr']:
            problems.append(f'{label} has no abbreviation.')
        elif len(club['abbr']) > ABBR_MAX or not re.fullmatch(r'[A-Z0-9]+', club['abbr']):
            problems.append(f"{label}: the abbreviation {club['abbr']} must be 1-{ABBR_MAX} letters or digits.")
        elif club['abbr'] in seen:
            problems.append(f"{label} and {seen[club['abbr']]} share the abbreviation {club['abbr']}.")
        elif club['abbr'] in others:
            notes.append(f"{label}: another league's club is {club['abbr']} too.")
        seen.setdefault(club['abbr'], label)
        for f, field in widths.items():
            if not _fits(teams, field, club[f]):
                problems.append(f"{label}: the {f} is longer than the game's {_width(teams, field)} bytes.")
        old = (stock or {}).get(spot['index'])
        if old and club['abbr'] == (old['abbrname'] or '').upper() and _clean(club['name']) != _clean(old['teamname']):
            problems.append(f"{label}: {club['abbr']} was {old['teamname']}'s abbreviation; give the club another "
                            f"(the game's menus would keep {old['teamname']}'s name).")
    if len(clubs) < len(spots):
        kept = ', '.join(s['name'] for s in spots[len(clubs):])
        notes.append(f"{slot_name} has {len(spots)} places: {len(spots) - len(clubs)} keep their clubs ({kept}).")
    notes.append(f"The clubs keep the players and calendar of the {slot_name} places they take.")
    return problems, notes


def make(db, league, stock=None):
    """Write `league`'s clubs into `db` place by place (its name is not roster data: see the module). Raises
    LeagueError (nothing written) when check() finds a problem. Returns {'slot', 'name', 'clubs': [(index, old name, new
    name)]}."""
    problems, _notes = check(db, league, stock)
    if problems:
        raise LeagueError(problems)
    lg = normalise(league)
    key = lg['slot']
    teams, done = db[T.TEAMS], []
    row_of = {teams.get(i, 'index'): i for i in range(teams.count)}
    for club, spot in zip(lg['clubs'], places(db, key)):
        row = row_of[spot['index']]
        for field, value in (('teamname', club['name']), ('nickname', club['nickname']), ('cityname', club['city']),
                             ('abbrname', club['abbr'])):
            teams.set(row, field, value)
        done.append((spot['index'], spot['name'], club['name']))
    return {'slot': key, 'name': lg['name'], 'clubs': done}


def from_db(db, key, name=''):
    """Slot `key` as a league definition named `name` (the clubs the roster has there now)."""
    return normalise({'name': name, 'slot': key, 'clubs': [{f: s[f] for f in CLUB_FIELDS} for s in places(db, key)]})


def loads(text):
    """A league file's text as a league definition. Raises LeagueError."""
    try:
        data = json.loads(text)
    except ValueError as err:
        raise LeagueError([f'This is not a league file (JSON): {err}.']) from err
    if isinstance(data, dict) and data.get('format') not in (None, FORMAT):
        raise LeagueError([f"This file is a {data.get('format')}, not a league file."])
    if isinstance(data, dict) and isinstance(data.get('version'), int) and data['version'] > VERSION:
        raise LeagueError([f"This league file is version {data['version']}: this app reads version {VERSION}."])
    return normalise(data)


def dumps(league):
    return json.dumps(normalise(league), ensure_ascii=False, indent=1) + '\n'


def parse_clubs(text):
    """Clubs typed one per line: "name | city | nickname | ABBR" (also with ; , or tab between; city and nickname may
    be left out: "name | ABBR"). Returns [club]; raises LeagueError for a line it cannot read."""
    clubs, problems = [], []
    for n, line in enumerate((text or '').splitlines(), 1):
        if not line.strip():
            continue
        sep = next((s for s in ('|', '\t', ';', ',') if s in line), None)
        parts = [p.strip() for p in line.split(sep)] if sep else [line.strip()]
        if len(parts) == 4:
            name, city, nick, abbr = parts
        elif len(parts) == 3:
            name, city, abbr = parts
            nick = ''
        elif len(parts) == 2:
            name, abbr = parts
            city = nick = ''
        else:
            problems.append(f'Line {n}: give "name | city | nickname | ABBR" (or "name | ABBR").')
            continue
        clubs.append({'name': name, 'city': city, 'nickname': nick, 'abbr': abbr})
    if problems:
        raise LeagueError(problems)
    return normalise({'clubs': clubs})['clubs']
