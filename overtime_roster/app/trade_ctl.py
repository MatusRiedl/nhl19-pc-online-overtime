"""Trades and moves on the Roster tab (docs/notes/trades.md): the Move / trade window, Bring in game moves, and the
next-step note that says which button gets a move into NHL 19.

- Move / trade (the player card's button): players change clubs, go to the free agents or come from them, several in
  one go (overtime_core.trades.move_players: numbers, places in the lines, contracts and the free agent list follow the
  game's own patterns). The window previews each player's number and whose places he takes, and every reason the
  roster refuses. One change of the roster: one Undo takes the whole trade back.
- Bring in game moves (the Players card's button): a roster save NHL 19 wrote (moves made in the game's Edit Rosters)
  is read, never written, and compared with the open roster by player (trades.compare). The window lists who plays
  elsewhere there; the ticked moves come over as one change. Players this app moved since the roster was opened keep
  the app's club unless ticked. Only clubs come over: ratings, names, lines and numbers of the others stay the app's.
- The next-step note (the Players card, after a trade or game moves): Save writes the roster, NHL 19 plays the roster
  picked in Rosters > Active Rosters. Patch is not needed for moves; with Roster update on it puts traded players back.
"""
import os

from overtime_core import trades as X

from . import labels as L, roster_card as RC, savegame, sources
from .registry import Part

FOUND = 8                   # players the trade window's search lists
SKIPPED_NAMES = 6           # names Bring in game moves shows of each kind of move it leaves out
NOTE_TAB = 'Roster'


class TradeCtl(Part):
    SLICES = {'trade': 'view'}
    CALLS = {'trade_open': 'open', 'trade_add': 'add', 'trade_drop': 'drop', 'trade_to': 'set_to',
             'trade_find': 'find', 'trade_apply': 'apply', 'trade_close': 'close',
             'trade_import_open': 'import_open', 'trade_import_pick': 'import_pick',
             'trade_import_tick': 'import_tick', 'trade_import_apply': 'import_apply',
             'trade_import_close': 'import_close', 'trade_note_close': 'note_close'}

    def __init__(self, ctl):
        super().__init__(ctl)
        self.window = None      # {'moves': [[game_id, to or None, league picked]], 'query': str, 'problems': [str]}
        self.importing = None   # {'folder', 'cmp': trades.Comparison | None, 'error', 'on': {game_id: bool}, 'problems'}
        self.note = None        # {'session', 'change'}: the next-step note of the last trade or game moves

    def roster_changed(self):
        self.window = self.importing = None
        if self.note is not None and self.note['session'] is not self.ctl.session:
            self.note = None

    def drafts(self):
        return 'the Move / trade window (not made yet)' if self.window and self.window['moves'] else ''

    # --- helpers -----------------------------------------------------------------------------------------------------
    def _say(self, text, tone='caution'):
        self.ctl.say(text, tone)
        self.ctl.changed('trade')
        return {'error': text} if tone == 'caution' else None

    @staticmethod
    def _team_name(s, team):
        return 'Free agents' if team == X.FA else s.team_name(team)

    @staticmethod
    def _gid(s, pi):
        _, b = s.bio(pi)
        return b['game_id'] if b else None

    def _pi_of(self, s, gid):
        """The playerindex the app lists him under (his club record, else a free agent record)."""
        pis = [pi for pi in self._pis(s, gid) if s.bio(pi)[1]]
        clubs = self._clubs(s)
        club = [pi for pi in pis if s.entry(pi)[1] is not None and RC.rail_team(s, pi) in clubs]
        free = [pi for pi in pis if pi in set(s.free_agents)]
        return (club or free or pis or [None])[0]

    @staticmethod
    def _pis(s, gid):
        players = s.db[X.U.PLAYERS]
        return [players.get(i, 'index') for i, g in enumerate(players.column('playerid'))
                if g == gid and players.get(i, 'table') == 0]

    @staticmethod
    def _clubs(s):
        return X.club_teams(s.db)

    def _deal_years(self, s):
        return 1 + (1 if RC.expansion(s) else 0)    # the extra season every NHL deal carries here (office's signing)

    def _lines_waiting(self, s, teams):
        c = self.ctl
        held = [t for t in teams if t != X.FA and (c.parts['lines'].touched(t) or c.parts['strategy'].touched(t))]
        if not held:
            return ''
        names = ', '.join(self._team_name(s, t) for t in held)
        return f'Apply or take back your Lines and Strategy changes of {names} first: the move changes their lines.'

    # --- the Move / trade window ---------------------------------------------------------------------------------------
    def open(self, pi=None):
        c = self.ctl
        with c.lock:
            s = c.session
            if s is None:
                return self._say('Open a roster in Setup first.')
            pi = c.player if pi is None else pi
            gid = self._gid(s, pi) if pi is not None else None
            self.window = {'moves': [[gid, None, None]] if gid is not None else [], 'query': '', 'problems': []}
        c.changed('trade')
        return None

    def close(self):
        self.window = None
        self.ctl.changed('trade')

    def find(self, text):
        if self.window is not None:
            self.window['query'] = str(text or '')[:60]
            self.ctl.changed('trade')

    def add(self, pi):
        c = self.ctl
        with c.lock:
            s, w = c.session, self.window
            if s is None or w is None:
                return None
            gid = self._gid(s, pi)
            if gid is None or any(m[0] == gid for m in w['moves']):
                return None
            mine = self._pi_of(s, gid)
            frm = RC.rail_team(s, mine) if mine is not None else None
            first = w['moves'][0] if w['moves'] else None
            back = None
            if first is not None:       # a swap: he goes where the first player came from
                fpi = self._pi_of(s, first[0])
                back = RC.rail_team(s, fpi) if fpi is not None else None
            to = back if back is not None and back != frm and (back == X.FA or back in self._clubs(s)) else None
            if first is not None and first[1] is None and frm in self._clubs(s) and frm != back:
                first[1] = frm          # and the first goes to his club
            w['moves'].append([gid, to, None])
            w['query'], w['problems'] = '', []
        c.changed('trade')
        return None

    def drop(self, gid):
        if self.window is not None:
            self.window['moves'] = [m for m in self.window['moves'] if m[0] != gid]
            self.window['problems'] = []
            self.ctl.changed('trade')

    def set_to(self, gid, team):
        """His new club (a team index or trades.FA); 'league:N' picks a league whose club he still has to pick."""
        w = self.window
        if w is None:
            return
        league = None
        if isinstance(team, str) and team.startswith('league:'):
            league, team = team[7:], None
        try:
            team = int(team)
        except (TypeError, ValueError):
            team = None
        try:
            league = int(league) if league is not None else None
        except ValueError:
            league = None
        for m in w['moves']:
            if m[0] == gid:
                m[1], m[2] = team, league
        w['problems'] = []
        self.ctl.changed('trade')

    def apply(self):
        c = self.ctl
        with c.lock:
            s, w = c.session, self.window
            if s is None or w is None:
                return None
            if c.busy:
                return self._say('Wait a moment: something else is still running.')
            moves = [(gid, to) for gid, to, _lg in w['moves'] if to is not None]
            if not moves or len(moves) < len(w['moves']):
                return self._say('Pick a club for every player first.' if w['moves'] else 'Add a player first.')
            teams = {m.frm for m in X.preview(s.db, moves).moves} | {to for _g, to in moves}
            waiting = self._lines_waiting(s, teams)
            if waiting:
                w['problems'] = [waiting]
                return self._say(waiting)
            label = self._label(s, moves)

            def work(db):
                plan = X.move_players(db, moves, self._deal_years(s))
                return self._details(s, plan), plan
            try:
                ch, plan = s.bulk(label, work)
            except X.TradeError as err:
                w['problems'] = err.problems
                return self._say(err.problems[0])
            ch.tab, ch.team, ch.moved = NOTE_TAB, plan.moves[0].to if plan.moves[0].to != X.FA else plan.moves[0].frm, \
                tuple(m.game_id for m in plan.moves)
            self.window = None
            self.note = {'session': s, 'change': ch}
        c.host.log(f'Trade: {label}')
        c.say(f'{label}. Not saved yet: the note on the Players card says what is next.', 'good')
        c.changed('trade', 'editor', 'lines', 'strategy', 'save', 'office')
        return {'ok': True}

    def _label(self, s, moves):
        if len(moves) == 1:
            gid, to = moves[0]
            pi = self._pi_of(s, gid)
            who = s.name(s.bio(pi)[1]) if pi is not None else f'player {gid}'
            return f'{who} to the free agents' if to == X.FA else f'{who} moves to {s.team_name(to)}'
        clubs = sorted({to for _g, to in moves if to != X.FA})
        names = ' and '.join(s.team_abbr(t) or s.team_name(t) for t in clubs[:3])
        return f'Trade: {len(moves)} players ({names})' if names else f'{len(moves)} players to the free agents'

    def _details(self, s, plan):
        out = []
        for m in plan.moves:
            new = self._team_name(s, m.to) + (f' #{m.number}' if m.number is not None else '')
            out.append((m.name, self._team_name(s, m.frm), new))
        for team in plan.dealt:
            out.append((f'{self._team_name(s, team)} lines', 'as they were', 'dealt again by ratings'))
        return out

    def _line(self, s, m):
        """What happens to one player of the window, as a short line."""
        if m.to == X.FA:
            return 'Free agent: his contract ends, any club can sign him later.'
        bits = [f'#{m.number}' + (f' (his #{m.old_number} is taken there)' if m.old_number and m.number != m.old_number
                                  else '')]
        bits.append(f"takes {m.takes}'s places in the lines" if m.takes else
                    'sits out as a spare: put him in on the Lines tab')
        if m.deal:
            bits.append('gets the lowest one-season NHL deal (change it on the Front office tab)')
        return ', '.join(bits) + '.'

    def _trade_view(self, s):
        w = self.window
        moves = [(gid, to) for gid, to, _lg in w['moves']]
        leagues = {gid: lg for gid, _to, lg in w['moves']}
        picked = [(gid, to) for gid, to in moves if to is not None]
        plan = X.preview(s.db, picked) if picked else X.Plan()
        by_gid = {m.game_id: m for m in plan.moves}
        clubs = self._clubs(s)
        rows = []
        for gid, to in moves:
            pi = self._pi_of(s, gid)
            b = s.bio(pi)[1] if pi is not None else None
            frm = RC.rail_team(s, pi) if pi is not None else None
            sm = s.summary(pi) if pi is not None else {}
            m = by_gid.get(gid)
            rows.append({'gid': gid, 'name': s.name(b) if b else f'player {gid}', 'pos': sm.get('pos', ''),
                         'ovr': sm.get('ovr', ''), 'from': self._team_name(s, frm) if frm is not None else '',
                         'from_team': self.ctl.rail.chip(frm) if frm not in (None, X.FA) else None,
                         'to': to, 'league': X.FA if to == X.FA else clubs.get(to) if to is not None else leagues[gid],
                         'line': self._line(s, m) if m and not plan.problems else
                         ('' if to is not None else 'Pick his new club.')})
        found = []
        query = w['query'].strip()
        if query:
            have = {gid for gid, _to in moves}
            rc = self.ctl.parts['roster']
            for pi in rc.found(s, query):
                gid = self._gid(s, pi)
                if gid in have or self._pi_of(s, gid) != pi:
                    continue        # one line a player: his club record (not his All-Star or national copies)
                sm = s.summary(pi)
                team = RC.rail_team(s, pi)
                found.append({'id': pi, 'name': sm['name'], 'pos': sm['pos'], 'ovr': sm['ovr'],
                              'team': self._team_name(s, team)})
                have.add(gid)
                if len(found) >= FOUND:
                    break
        problems = list(w['problems']) or list(plan.problems)
        ready = bool(picked) and len(picked) == len(moves) and not plan.problems
        return {'open': True, 'rows': rows, 'query': w['query'], 'found': found, 'problems': problems,
                'can_apply': ready and not w['problems'], 'button': 'Make the trade' if len(moves) > 1 else 'Move him',
                'leagues': self._league_options(s, clubs)}

    def _league_options(self, s, clubs):
        by_league = {}
        for team, lg in clubs.items():
            if team in s.team_entries:
                by_league.setdefault(lg, []).append({'value': team, 'label': s.team_name(team)})
        out = [{'value': lg, 'label': L.LEAGUES.get(lg, f'League {lg}'),
                'teams': sorted(teams, key=lambda t: t['label'])} for lg, teams in sorted(by_league.items())]
        out.append({'value': X.FA, 'label': 'Free agents', 'teams': [{'value': X.FA, 'label': 'Free agents'}]})
        return out

    # --- Bring in game moves -----------------------------------------------------------------------------------------
    def _saves(self):
        """[(folder name, Source)] of the custom and downloaded roster saves, the one written last first (not the
        online roster: the app writes it for Multiplayer, the game does not change it)."""
        c = self.ctl
        out = []
        for src in c.sources:
            folder = src.info.get('folder') or os.path.basename(src.path)
            if src.kind != 'save' or not src.usable or folder.startswith('RosterOnline'):
                continue
            try:
                when = os.path.getmtime(os.path.join(src.path, 'DATA'))
            except OSError:
                when = 0
            out.append((when, folder, src))
        return [(folder, src) for _w, folder, src in sorted(out, key=lambda x: -x[0])]

    def import_open(self):
        c = self.ctl
        if c.session is None:
            return self._say('Open a roster in Setup first.')
        c.parts['rosters'].refresh_sources(quiet=True)
        saves = self._saves()
        if not saves:
            return self._say('No roster save found: in NHL 19, save the roster you changed first (Rosters > Save '
                             'Roster).')
        return self.import_pick(saves[0][0])

    def import_pick(self, folder):
        c = self.ctl
        src = next((src for f, src in self._saves() if f == folder), None)
        state = {'folder': folder, 'cmp': None, 'error': '', 'on': {}, 'problems': []}
        if src is None:
            state['error'] = 'That save is gone. Pick another one.'
        else:
            try:
                theirs, _label = sources.load(src, c.game)
            except Exception as err:    # noqa: BLE001 - a save the game wrote halfway or another title's
                state['error'] = f'Cannot read {folder}: {err}'
                theirs = None
            if theirs is not None:
                with c.lock:
                    s = c.session
                    if s is None:
                        return None
                    cmp = X.compare(s.db, theirs)
                    mine = self._app_moved(s)
                state['cmp'] = cmp
                state['on'] = {m[0]: m[0] not in mine for m in cmp.moves}
        self.importing = state
        c.changed('trade')
        return None

    @staticmethod
    def _app_moved(s):
        return {gid for ch in s.history for gid in getattr(ch, 'moved', ())}

    def import_tick(self, gid, on):
        if self.importing and gid in self.importing['on']:
            self.importing['on'][gid] = bool(on)
            self.importing['problems'] = []
            self.ctl.changed('trade')

    def import_close(self):
        self.importing = None
        self.ctl.changed('trade')

    def import_apply(self):
        c = self.ctl
        imp = self.importing
        with c.lock:
            s = c.session
            if s is None or not imp or imp['cmp'] is None:
                return None
            if c.busy:
                return self._say('Wait a moment: something else is still running.')
            if imp['cmp'].different:
                return self._say('That save is a different roster: open it in Setup instead.')
            moves = [(m[0], m[4]) for m in imp['cmp'].moves if imp['on'].get(m[0])]
            if not moves:
                return self._say('Tick the moves to bring in first.')
            waiting = self._lines_waiting(s, {m[3] for m in imp['cmp'].moves} | {to for _g, to in moves})
            if waiting:
                imp['problems'] = [waiting]
                return self._say(waiting)
            label = f"Game moves from {savegame.roster_label(imp['folder'])}: {len(moves)} " \
                    f"player{'s' if len(moves) != 1 else ''}"

            def work(db):
                plan = X.move_players(db, moves, self._deal_years(s))
                return self._details(s, plan), plan
            try:
                ch, _plan = s.bulk(label, work)
            except X.TradeError as err:
                imp['problems'] = err.problems
                return self._say(err.problems[0])
            ch.tab, ch.team = NOTE_TAB, None
            self.importing = None
            self.note = {'session': s, 'change': ch}
        c.host.log(f'Trade: {label}')
        c.say(f'{label}. Not saved yet: the note on the Players card says what is next.', 'good')
        c.changed('trade', 'editor', 'lines', 'strategy', 'save', 'office')
        return {'ok': True}

    def _import_view(self, s):
        imp = self.importing
        saves = self._saves()
        open_folder = (self.ctl.parts['rosters'].open_roster() or {}).get('id')
        active = savegame.active_roster(self.ctl.save_dir) if self.ctl.save_dir else None
        options = []
        for folder, src in saves:
            tags = [savegame.roster_label(folder)] + (['open here'] if folder == open_folder else []) + \
                   (['active in NHL 19'] if folder == active else [])
            options.append({'value': folder, 'label': f"{src.name} ({', '.join(tags)})"})
        out = {'open': True, 'saves': options, 'folder': imp['folder'], 'error': imp['error'], 'moves': [],
               'skipped': [], 'unknown': 0, 'different': False, 'problems': list(imp['problems']), 'can_apply': False}
        cmp = imp['cmp']
        if cmp is None:
            return out
        mine = self._app_moved(s)
        out['moves'] = [{'gid': gid, 'name': name, 'pos': kind, 'from': self._team_name(s, frm),
                         'to': self._team_name(s, to), 'on': bool(imp['on'].get(gid)),
                         'mine': 'You moved him in the app: your move stays unless you tick this.' if gid in mine
                         else ''} for gid, name, kind, frm, to in cmp.moves]
        by_why = {}
        for _g, name, _k, _f, _t, why in cmp.skipped:
            by_why.setdefault(why, []).append(name)
        out['skipped'] = [{'why': why, 'names': names[:SKIPPED_NAMES], 'more': max(0, len(names) - SKIPPED_NAMES)}
                          for why, names in by_why.items()]
        out['unknown'] = len(cmp.unknown)
        out['different'] = cmp.different
        picked = [(m[0], m[4]) for m in cmp.moves if imp['on'].get(m[0])]
        if picked and not cmp.different and not imp['problems']:
            out['problems'] = X.preview(s.db, picked).problems
            if out['problems']:     # the game's save has players this roster lacks (made there), or a move left out
                out['problems'].append('Untick the moves of those clubs to bring in the rest.')
        out['can_apply'] = bool(picked) and not cmp.different and not out['problems']
        return out

    # --- the next-step note ------------------------------------------------------------------------------------------
    def note_close(self):
        self.note = None
        self.ctl.changed('trade')

    def _note_view(self, s):
        n = self.note
        if n is None or n['session'] is not s or not any(ch is n['change'] for ch in s.history):
            return None
        c = self.ctl
        save = c.parts['save']
        roster = c.parts['rosters'].open_roster() or {}
        unsaved = any(ch is n['change'] for ch, _undone in save.pending())
        folder = roster.get('id') if roster.get('kind') == 'save' else None
        slot = savegame.roster_label(folder) if folder else 'the new custom roster'
        active = savegame.active_roster(c.save_dir) if c.save_dir else None
        playing = bool(folder) and folder == active
        steps = []
        if unsaved:
            where = f'over {roster.get("name") or folder} ({slot})' if save.update_mode(roster) else \
                'as a new custom roster'
            steps.append(f'Press Save (the bar at the bottom, or Ctrl+S). It writes the roster {where}.')
            if not save.update_mode(roster):
                slot = 'the new custom roster'
                playing = False
        title = 'Next: press Save' if unsaved else 'Saved. Next: play it in NHL 19'
        if playing:
            steps.append(f'NHL 19 plays {slot} already (it is the active roster): start the game, or restart it if '
                         'it is running.')
        else:
            steps.append(f'In NHL 19: Rosters > Active Rosters, pick "{slot}".')
        steps.append('No Patch needed: moves live in the roster save.')
        caution = ''
        if c.parts['patchall'].update_on:
            caution = ('Careful with Patch: its Roster update re-does the teams from NHL.com and puts traded players '
                       'back. Turn Roster update off on the Patch tab to keep your moves.')
        return {'title': title, 'steps': steps, 'caution': caution, 'unsaved': unsaved}

    # --- the slice ---------------------------------------------------------------------------------------------------
    def view(self):
        c = self.ctl
        with c.lock:
            s = c.session
            if s is None:
                return {'window': None, 'importing': None, 'note': None, 'busy': bool(c.busy)}
            return {'window': self._trade_view(s) if self.window is not None else None,
                    'importing': self._import_view(s) if self.importing is not None else None,
                    'note': self._note_view(s), 'busy': bool(c.busy)}
