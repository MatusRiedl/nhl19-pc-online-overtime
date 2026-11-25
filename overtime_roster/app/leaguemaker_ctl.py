"""League maker on the Roster tab (v1.00.0; docs/notes/league-maker.md): a league of the user's own clubs (a KHL, say)
in one of NHL 19's club league slots, as modders share it in a league file.

The window (the Players card's New league... button) shows a slot's name and clubs, one club a line ("name | city |
nickname | ABBR"); the user names the league, types or pastes the clubs, or imports a league file. Make it:
overtime_core.leaguemaker writes the clubs place by place as one change, one Undo; the places keep their players and
the slot's calendar. Save keeps the league, its name with it, in My edits (myedits `leagues`): every roster update puts
its clubs back over the ones the update dealt, and Patch puts its name on the slot's texts (the names layer,
overtime_core.overlay.league_strings; a roster save has no league names). Export writes the slot as a league file.
"""
import copy
import os

from overtime_core import leaguemaker as LM

from . import myedits, sources
from .registry import Part

FILE_KINDS = ('League file (*.json)',)
TEXT_MAX = 20000        # the clubs box: 32 clubs of four fields with room to spare


def clubs_text(clubs):
    """The clubs box's text: one club a line, "name | city | nickname | ABBR"."""
    return '\n'.join(' | '.join(c[f] for f in LM.CLUB_FIELDS) for c in clubs)


class LeagueMakerCtl(Part):
    SLICES = {'leaguemaker': 'view'}
    CALLS = {'leaguemaker_open': 'open', 'leaguemaker_set': 'set', 'leaguemaker_make': 'make',
             'leaguemaker_close': 'close', 'leaguemaker_import': 'import_file', 'leaguemaker_import_path': 'import_path',
             'leaguemaker_export': 'export', 'leaguemaker_reset': 'reset'}

    def __init__(self, ctl):
        super().__init__(ctl)
        # {'key', 'values': {slot, name, clubs (text)}, 'problems': [text], 'notes': [text]}
        self.window = None
        self.opened = 0
        self.made = []          # [(change, league)] the session made: Save keeps the live ones (keep)
        self.base = None        # My edits' leagues before the session made one: a slot whose leagues were taken back
        self._stock = None

    def roster_changed(self):
        self.window = None
        self.made = []
        self.base = None

    def drafts(self):
        """Save's "apply your changes first?": the window holds a name or clubs not made yet."""
        c = self.ctl
        with c.lock:
            w, s = self.window, c.session
            if not w or s is None:
                return ''
            v = w['values']
            here = self._fill(s, v['slot'])
            try:
                same = v['name'].strip() == here['name'] and \
                    LM.parse_clubs(v['clubs']) == LM.parse_clubs(here['clubs'])
            except LM.LeagueError:      # a line it cannot read: typed, not made
                same = False
        return '' if same else 'the League maker window (not made yet)'

    def _say(self, text, tone='caution'):
        self.ctl.say(text, tone)
        self.ctl.changed('leaguemaker')
        return {'error': text} if tone == 'caution' else None

    def stock(self):
        """The game's own database (club names a league must not keep the abbreviations of)."""
        if self._stock is None:
            self._stock = self.ctl.game.default_db()
        return self._stock

    def stock_teams(self):
        db = self.stock()
        return {r['index']: r for r in db['exhibitionteams'].rows()}

    def _live(self):
        s = self.ctl.session
        return {id(ch) for ch in s.history} if s is not None else set()

    def name_of(self, key):
        """The name slot `key` goes by: the newest league the session made there (not taken back), else the one My
        edits keeps, else '' (the game's own)."""
        live = self._live()
        for ch, lg in reversed(self.made):
            if lg['slot'] == key and id(ch) in live:
                return '' if lg.get('reset') else lg['name']
        kept = (self.ctl.parts['roster'].kept().get(myedits.LEAGUES) or {}).get(key)
        return kept['name'] if kept else ''

    def _fill(self, s, key):
        """The window's values for slot `key`: its name (name_of) and the clubs the open roster has there."""
        return {'slot': key, 'name': self.name_of(key), 'clubs': clubs_text(LM.from_db(s.db, key)['clubs'])}

    # --- the window --------------------------------------------------------------------------------------------------
    def open(self, slot=None):
        c = self.ctl
        with c.lock:
            s = c.session
            if s is None:
                return self._say('Open a roster in Setup first.')
            have = [x['key'] for x in LM.slots(s.db)]
            if not have:
                return self._say('This roster has no club league a league can take.')
            key = slot if slot in have else have[-1]
            self.opened += 1
            self.window = {'key': self.opened, 'values': self._fill(s, key), 'problems': [], 'notes': []}
        c.changed('leaguemaker')
        return None

    def close(self):
        self.window = None
        self.ctl.changed('leaguemaker')

    def set(self, key, value):
        """leaguemaker_set(key, value): 'slot' shows that slot's name and clubs; 'name' and 'clubs' are typed."""
        c = self.ctl
        with c.lock:
            s, w = c.session, self.window
            if s is None or w is None:
                return None
            v = w['values']
            if key == 'slot' and value in LM.SLOTS:
                w['values'] = self._fill(s, value)
            elif key == 'name':
                v['name'] = str(value if value is not None else '')[:60]
            elif key == 'clubs':
                v['clubs'] = str(value if value is not None else '')[:TEXT_MAX]
            else:
                return None
            w['problems'], w['notes'] = [], []
        c.changed('leaguemaker')
        return None

    def _league(self, v):
        """The window's values as a league definition; raises LM.LeagueError."""
        return LM.normalise({'name': v['name'], 'slot': v['slot'], 'clubs': LM.parse_clubs(v['clubs'])})

    def make(self, typed=None):
        """Make the league: one change. `typed`: the text boxes as typed (the last one may not have reached
        leaguemaker_set yet). {ok} or {error}."""
        c = self.ctl
        if isinstance(typed, dict):
            for key in ('name', 'clubs'):
                if key in typed:
                    self.set(key, typed[key])
        with c.lock:
            s, w = c.session, self.window
            if s is None or w is None:
                return None
            if c.busy:
                return self._say('Wait a moment: something else is still running.')
            stock = self.stock_teams()
            try:
                league = self._league(w['values'])
                problems, notes = LM.check(s.db, league, stock)
            except LM.LeagueError as err:
                problems, notes = err.problems, []
            w['problems'], w['notes'] = problems, notes
            if problems:
                return self._say(problems[0])
            slot = LM.SLOTS[league['slot']][1]

            def work(db):
                done = LM.make(db, league, stock)
                return [(f"{league['name']}: {new}", old, f'{slot} place {index}')
                        for index, old, new in done['clubs'] if old != new] or \
                    [(league['name'], self.name_of(league['slot']) or slot, 'league name')], done
            if self.base is None:
                self.base = copy.deepcopy(c.parts['roster'].kept().get(myedits.LEAGUES) or {})
            try:
                ch, _done = s.bulk(f"League {league['name']} ({slot})", work)
            except LM.LeagueError as err:
                w['problems'] = err.problems
                return self._say(err.problems[0])
            ch.tab = 'Roster'
            self.made.append((ch, league))
            self.window = None
            c.issues = None
        c.host.log(f"League maker: {league['name']} in the {slot} slot ({len(league['clubs'])} clubs)")
        c.say(f"{league['name']} takes the {slot} slot: {len(league['clubs'])} clubs. Not saved yet: press Save (My "
              f"edits keeps the league for every update), then Patch in Setup so NHL 19 shows the name {league['name']}.",
              'good')
        c.changed('leaguemaker', 'roster', 'roster_card', 'editor', 'lines', 'save', 'rail', 'office', 'trade')
        return {'ok': True}

    def reset(self):
        """Back to the game's own: the window's slot gets the clubs its places had in the game's own roster (the
        players stay) and, once saved and patched, its own name. One change."""
        c = self.ctl
        with c.lock:
            s, w = c.session, self.window
            if s is None or w is None:
                return None
            key = w['values']['slot']
            have = LM.places(s.db, key)
            stock = self.stock_teams()
            clubs = [{'name': r['teamname'], 'city': r['cityname'], 'nickname': r['nickname'], 'abbr': r['abbrname']}
                     for r in (stock.get(p['index']) for p in have) if r]
            slot = LM.SLOTS[key][1]
            league = {'slot': key, 'name': slot, 'clubs': clubs}

            def work(db):
                done = LM.make(db, league)
                return [(f'{slot}: {new}', old, f'place {index}') for index, old, new in done['clubs'] if old != new] \
                    or [(slot, self.name_of(key), 'league name')], done
            if self.base is None:
                self.base = copy.deepcopy(c.parts['roster'].kept().get(myedits.LEAGUES) or {})
            try:
                ch, _done = s.bulk(f'League {slot}: back to the game\'s own', work)
            except LM.LeagueError as err:
                return self._say(err.problems[0])
            ch.tab = 'Roster'
            self.made.append((ch, {'slot': key, 'reset': True}))
            w['values'] = self._fill(s, key)
            w['problems'], w['notes'] = [], []
        c.say(f"The {slot} slot has the game's own clubs again. Not saved yet: press Save, then Patch in Setup for "
              'its own name.', 'good')
        c.changed('leaguemaker', 'roster', 'roster_card', 'editor', 'lines', 'save', 'rail', 'office', 'trade')
        return {'ok': True}

    # --- league files ------------------------------------------------------------------------------------------------
    def import_file(self):
        """Import...: Windows' picker for a league file, then import_path. {type: true} in browser mode."""
        pick = getattr(self.ctl.host, 'pick', None)
        path = pick(False, '', FILE_KINDS) if pick else None
        if path is None:
            return {'type': True}
        if not path:
            return {'cancelled': True}
        return self.import_path(path)

    def import_path(self, path):
        """A league file into the window (nothing changes in the roster until Make league)."""
        c = self.ctl
        try:
            with open(path, encoding='utf-8-sig') as f:
                league = LM.loads(f.read(TEXT_MAX * 4))
        except OSError as err:
            return self._say(f'The league file could not be read: {err.strerror or err}.')
        except LM.LeagueError as err:
            return self._say(err.problems[0])
        with c.lock:
            s = c.session
            if s is None:
                return self._say('Open a roster in Setup first.')
            if self.window is None:
                self.opened += 1
                self.window = {'key': self.opened, 'values': {}, 'problems': [], 'notes': []}
            w = self.window
            slot = league['slot'] if league['slot'] in LM.SLOTS else w['values'].get('slot') or 'echl'
            w['values'] = {'slot': slot, 'name': league['name'], 'clubs': clubs_text(league['clubs'])}
            try:
                w['problems'], w['notes'] = LM.check(s.db, dict(league, slot=slot), self.stock_teams())
            except LM.LeagueError as err:
                w['problems'], w['notes'] = err.problems, []
        c.say(f"{league['name'] or 'The league'}: {len(league['clubs'])} clubs read from {os.path.basename(path)}. "
              'Check them, then Make league.', 'good')
        c.changed('leaguemaker')
        return {'ok': True}

    def export(self, folder=None):
        """Export...: the window's slot as the open roster has it, written as a league file into a folder the user
        picks (`folder`: typed in browser mode). {path} or {error}; {type: true} in browser mode."""
        c = self.ctl
        with c.lock:
            s, w = c.session, self.window
            if s is None or w is None:
                return None
            key = w['values']['slot']
            league = LM.from_db(s.db, key, w['values']['name'].strip() or self.name_of(key) or LM.SLOTS[key][1])
        if folder is None:
            pick = getattr(c.host, 'pick', None)
            folder = pick(True, '', ()) if pick else None
        if folder is None:
            return {'type': True}
        if not folder:
            return {'cancelled': True}
        stem = ''.join(ch if ch.isalnum() or ch in ' -_' else '_' for ch in league['name']).strip() or league['slot']
        path = os.path.join(folder, f'{stem}.league.json')
        try:
            with open(path, 'w', encoding='utf-8', newline='\n') as f:
                f.write(LM.dumps(league))
        except OSError as err:
            return self._say(f'The league file could not be written: {err.strerror or err}.')
        c.say(f'{league["name"]} written to {path}.', 'good')
        return {'path': path}

    # --- Save: what My edits keeps ----------------------------------------------------------------------------------
    def keep(self, data, ids):
        """Save (RosterCtl.to_keep): My edits' leagues in `data` (edits.json to be) for the changes `ids` the save
        writes. Each slot the session made a league in keeps its newest one in `ids` (a reset takes the slot's kept
        league away); a slot whose leagues were all taken back keeps what My edits had before the first of them."""
        live = self._live()
        newest = {}
        for ch, lg in self.made:
            if id(ch) in ids and id(ch) in live:
                newest[lg['slot']] = lg
            else:
                newest.setdefault(lg['slot'], None)
        for key, lg in newest.items():
            if lg is not None:
                myedits.record_league(data, lg)
                continue
            before = (self.base or {}).get(key)
            leagues = data.setdefault(myedits.LEAGUES, {})
            if before:
                leagues[key] = copy.deepcopy(before)
            else:
                leagues.pop(key, None)

    # --- the slice ---------------------------------------------------------------------------------------------------
    def view(self):
        c = self.ctl
        with c.lock:
            s, w = c.session, self.window
            if s is None or w is None:
                return {'window': None, 'busy': bool(c.busy)}
            slots = [{'key': x['key'], 'label': f"{x['game_name']} ({x['places']} places)",
                      'places': x['places'], 'game_name': x['game_name'], 'name': self.name_of(x['key'])}
                     for x in LM.slots(s.db)]
            v = w['values']
            lines = [ln for ln in v['clubs'].splitlines() if ln.strip()]
            here = next((x for x in slots if x['key'] == v['slot']), None)
            kept = (c.parts['roster'].kept().get(myedits.LEAGUES) or {}).get(v['slot'])
            return {'busy': bool(c.busy), 'window': {
                'key': w['key'], 'values': dict(v), 'slots': slots, 'problems': list(w['problems']),
                'notes': list(w['notes']), 'clubs': len(lines), 'places': here['places'] if here else 0,
                'kept': bool(kept), 'can_make': not c.busy and bool(v['name'].strip()) and bool(lines),
                # the Game roster (2018-19) open: a Season crashes with its saves active (lab c32f, c32g)
                'game_roster': c.parts['rosters'].open_id == sources.GAME_ID}}
