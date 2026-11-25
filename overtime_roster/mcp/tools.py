"""The tools an AI gets over MCP (`OvertimeNHL19.exe --mcp`, owner 2026-11-25: "a way for others to use AI to connect
to their local Overtime copy ... and edit rosters, add leagues"). Each tool drives the same Controller and parts the
window drives (the Roster card's checks, New player, Trade, League maker, Verify, Save), in one call: a refusal comes
back as the card's sentences. Nothing reaches NHL 19 until save_roster_as_new, and that always writes a new roster:
no tool overwrites, deletes, patches, updates, plays online or takes a path."""
import collections
import sys

from .protocol import Tool, ToolError

LIMIT = 200         # rows a list gives at most
FA = -1             # labels.FREE_AGENTS: the free agents' team and league

INSTRUCTIONS = (
    'Overtime edits NHL 19 rosters (PS4 NHL 19 on the shadPS4 emulator) on this PC. Start with overtime_status, '
    "then open_roster ('default' is the 2026-27 Overtime default). find_players and get_player read; edit_player, "
    'create_player, move_players and make_league change the open roster in memory, each as one edit (list_edits, '
    'undo_last_edit). Run verify_roster, then save_roster_as_new: it always writes a new roster and never overwrites '
    "one. The player then loads it in NHL 19; a new league's name shows after Patch in Overtime's Setup tab. Ids are "
    'the ones these tools give: player ids from find_players, team and league ids from list_teams.')

KEYS = ('first, last, num (1-99), pos (C, LW, RW, D; G stays G), shoots (L or R), captain (0 none, 1 C, 2 A), '
        "born (YYYY-MM-DD as get_player shows it), country (a country name such as Slovakia, or get_player's id), "
        'height (cm), '
        'weight (kg), salary (cap hit in $M), years (contract years left), twoway (0 or 1), ratings {field: value}')


class Host:
    """The Controller's host without a window: slices kept, pushes dropped, the log on stderr, no file pickers."""

    def __init__(self, log):
        self.snaps, self.lines, self._log = {}, collections.deque(maxlen=400), log

    def register(self, name, fn):
        self.snaps[name] = fn

    def changed(self, *names):
        pass

    def log(self, *lines):
        for line in lines:
            self.lines.append(str(line))
            self._log(str(line))

    def send(self, event, payload=None):
        pass

    def open_path(self, path):
        pass

    def pick(self, folder, start='', kinds=()):
        return None


def inline_jobs():
    """jobs.run without its thread: a tool's result waits for the roster to open or the save to end."""
    from ..app import jobs
    if getattr(jobs.run, 'inline', False):
        return

    def run(work, done=None, failed=None, expected=()):
        try:
            result = work()
        except expected as err:
            jobs.log_block(err)
            if failed:
                failed(str(err))
            return None
        except Exception as err:    # noqa: BLE001 (as jobs.run: logged, then told)
            message = jobs.log_unexpected(err)
            if failed:
                failed(message)
            return None
        if done:
            done(result)
        return None
    run.inline = True
    jobs.run = run


def _int(value, what):
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ToolError(f'{what}: a whole number, please.') from None


def _keys(item, keys, what):
    """A list item's keys (the protocol checks only the top-level arguments): a misspelt one would be passed over."""
    unknown = [k for k in item if k not in keys]
    if unknown:
        raise ToolError(f"{what}: no key {', '.join(map(repr, unknown))}. Keys: {', '.join(keys)}.")


def _obj(props, required=()):
    return {'type': 'object', 'properties': props, 'required': list(required), 'additionalProperties': False}


class OvertimeTools:
    def __init__(self, game_dir=None, save_dir=None, log=None):
        self.game_dir, self.save_dir = game_dir, save_dir
        self.log = log or (lambda text: print(text, file=sys.stderr, flush=True))
        self.c = None

    # --- the app, made on the first tool call (the client's start-up waits for none of it) ------------------------
    def ctl(self):
        if self.c is None:
            inline_jobs()
            from ..app.controller import Controller

            class Quiet(Controller):
                def remember(self, **_kw):      # the window's settings (its roster, its first run) stay the window's
                    pass
            self.c = Quiet(Host(self.log), game_dir=self.game_dir, save_dir=self.save_dir, reopen=False)
        return self.c

    def session(self):
        c = self.ctl()
        if c.session is None:
            raise ToolError("No roster is open: call open_roster first ('default' is the Overtime default).")
        return c, c.session

    @staticmethod
    def said(c):
        return (c.status or {}).get('text', '')

    @staticmethod
    def settle(c):
        """A question the window would show (NHL 19 running, ...): dropped, its words are the tool's error."""
        q = c.shell.asking
        if q:
            c.shell.asking = None
            raise ToolError(' '.join([q.get('title', '')] + list(q.get('lines') or [])).strip())

    @staticmethod
    def player(s, player_id):
        pi = _int(player_id, 'player_id')
        if s.bio(pi)[1] is None:
            raise ToolError(f'No player {pi}: find_players gives the ids.')
        return pi

    @staticmethod
    def row(c, s, pi):
        """His summary with the age the Roster tab shows: on the game's 2018-19 clock (the session's own age counts
        to today, so a roster with moved birth dates would say Celebrini is 28)."""
        row = s.summary(pi)
        _, b = s.bio(pi)
        if b is not None:
            row['age'] = c.parts['roster'].clock(s).age(b)
        return row

    # --- reading ---------------------------------------------------------------------------------------------------
    def status(self):
        from .. import VERSION
        from ..app import rosters_ctl
        c = self.ctl()
        c.refresh_sources(quiet=True)
        rosters = [{'id': key, 'name': name, 'about': about} for key, name, about, _game in rosters_ctl.STARTS]
        rosters += [{'id': s.info.get('folder'), 'name': s.name, 'about': s.meta} for s in c.sources
                    if s.kind == 'save' and s.usable][:LIMIT]
        return {'overtime': VERSION, 'game_folder': c.game_dir, 'game_found': bool(c.game.ok),
                'save_folder': c.save_dir, 'open_roster': c.parts['rosters'].open_roster(),
                'unsaved_edits': c.parts['save'].unsaved() if c.session else 0, 'rosters': rosters}

    def list_teams(self, league=None):
        c, s = self.session()
        if league is None:
            return {'leagues': [{'id': lg, 'name': label, 'teams': n} for lg, label, n in s.leagues()],
                    'next': 'list_teams with a league id lists its teams (NHL is 0, the free agents -1).'}
        lg = _int(league, 'league')
        if lg == FA:
            return {'league': FA, 'teams': [{'id': FA, 'code': 'FA', 'name': 'Free agents',
                                             'players': len(s.free_agents)}]}
        return {'league': lg, 'teams': [{'id': t['id'], 'code': t['code'], 'name': t['name'], 'players': t['count']}
                                        for t in c.rail.listed(s, lg)]}

    def find_players(self, name=None, team=None, limit=50):
        c, s = self.session()
        rc = c.parts['roster']
        if name and str(name).strip():
            pis = rc.found(s, str(name))
        elif team is not None:
            pis = rc.team_rows(s, _int(team, 'team'))
        else:
            raise ToolError('Give a name (part of it is enough) or a team id.')
        n = max(1, min(_int(limit, 'limit'), LIMIT))
        return {'found': len(pis), 'players': [self.row(c, s, pi) for pi in pis[:n]]}

    def get_player(self, player_id):
        from ..app import labels as L, roster_card as RC
        c, s = self.session()
        pi = self.player(s, player_id)
        _, b = s.bio(pi)
        v = RC.values(s, c.parts['roster'].clock(s), pi)
        labels = {f: label for g in RC.rating_groups(s, b) for f, label in g['items']}
        row = self.row(c, s, pi)
        return {'id': pi, 'name': row['name'], 'team': row['team'], 'team_id': RC.rail_team(s, pi),
                'overall': row['ovr'], 'age': row['age'],
                'values': {k: x for k, x in v.items() if k != 'ratings'}, 'country_name': L.country(v['country']),
                'ratings': {f: {'label': labels.get(f, f), 'value': n} for f, n in v['ratings'].items()},
                'edit_player_takes': KEYS}

    def list_league_slots(self):
        from overtime_core import leaguemaker as LM
        c, s = self.session()
        lm = c.parts['leaguemaker']
        return {'slots': [{'slot': x['key'], 'game_league': x['game_name'], 'places': x['places'],
                           'name_now': lm.name_of(x['key'])} for x in LM.slots(s.db)],
                'next': "make_league takes one slot: its clubs take the slot's places, the league its name."}

    def list_edits(self):
        c, s = self.session()
        with c.lock:
            pending = c.parts['save'].pending()
        return {'unsaved': len(pending), 'edits': [{'edit': ch.label, 'tab': ch.tab, 'taken_back': undone}
                                                   for ch, undone in pending][:LIMIT]}

    def verify_roster(self):
        c, s = self.session()
        c.parts['save'].run_verify()
        issues = list(c.issues or [])
        errors = [i for i in issues if i.level == 'error']
        rest = [i for i in issues if i.level != 'error']
        return {'errors': len(errors), 'warnings': len(rest),
                'issues': [{'level': i.level, 'rule': i.rule, 'text': i.message, 'team': i.team, 'player': i.player}
                           for i in (errors + rest)[:LIMIT]]}

    # --- changing the open roster ----------------------------------------------------------------------------------
    def open_roster(self, roster, discard_unsaved_edits=False):
        from ..app import rosters_ctl
        c = self.ctl()
        rp = c.parts['rosters']
        c.refresh_sources(quiet=True)
        key = str(roster or '').strip()
        n = c.parts['save'].unsaved() if c.session is not None else 0
        if n and not discard_unsaved_edits:
            raise ToolError(f'The open roster has {n} unsaved edit(s). Save them with save_roster_as_new first, or call '
                            'open_roster again with discard_unsaved_edits true.')
        before = c.session
        if key.lower() in (rosters_ctl.DEFAULT, 'overtime default'):
            rp.load_default()
        else:
            src = rp.source(key) or next((x for x in c.sources if x.name.lower() == key.lower()), None)
            if src is None or not src.usable:
                raise ToolError(f'No roster {key!r}: overtime_status lists them.')
            rp.load_source(src.id)
        self.settle(c)
        if c.session is None or c.session is before:
            raise ToolError(self.said(c) or 'The roster did not open.')
        return {'ok': True, 'open_roster': rp.open_roster(), 'note': self.said(c)}

    def edit_player(self, player_id, changes):
        c, s = self.session()
        pi = self.player(s, player_id)
        if not isinstance(changes, dict) or not changes:
            raise ToolError(f'changes: an object with any of {KEYS}.')
        from ..app import roster_card as RC
        unknown = [k for k in changes if k not in RC.ORDER + ('ratings',)]
        if unknown:     # the card would pass over them and say nothing changed
            raise ToolError(f"Not changed: no key {', '.join(map(repr, unknown))}. Keys: {KEYS}.")
        changes = dict(changes)
        if isinstance(changes.get('country'), str) and not changes['country'].strip().isdigit():
            from ..app import labels as L
            want = changes['country'].strip().lower()
            cid = next((k for k, v in L.COUNTRIES.items() if v.lower() == want), None)
            if cid is None:
                raise ToolError(f"Not changed: no country {changes['country']!r}. Countries: "
                                + ', '.join(sorted(L.COUNTRIES.values())) + '.')
            changes['country'] = cid
        rc = c.parts['roster']
        rc.pick_player(pi)
        reply = rc.apply(changes) or {}
        if not reply.get('ok'):
            with c.lock:        # the card does not keep what the AI typed
                rc.typed.pop(pi, None)
                rc.problems.pop(pi, None)
            problems = [p['text'] for p in reply.get('problems') or []]
            raise ToolError('Not changed: ' + ('; '.join(problems) or reply.get('error') or self.said(c)))
        return {'ok': True, 'changed': reply.get('changes', 0), 'note': self.said(c), 'player': self.row(c, s, pi)}

    def create_player(self, first, last, born, team, position='C', shoots='L'):
        from ..app import labels as L
        c, s = self.session()
        if position not in L.POSITIONS:
            raise ToolError(f"position: one of {', '.join(L.POSITIONS)}.")
        if shoots not in L.HANDS:
            raise ToolError('shoots: L or R.')
        team = _int(team, 'team')
        np = c.parts['newplayer']
        np.open()
        if np.window is None:
            raise ToolError(self.said(c))
        np.set('pos', position)
        np.set('shoots', shoots)
        np.set('team', team)
        if np.window['values']['team'] != team:
            np.close()
            raise ToolError(f'Team {team} takes no new players: give a club id from list_teams, or -1 for the free '
                            'agents.')
        reply = np.make({'first': str(first or ''), 'last': str(last or ''), 'born': str(born or '')})
        if not reply or not reply.get('ok'):
            problems = [p['text'] for p in (np.window or {}).get('problems') or []]
            np.close()
            raise ToolError('Not made: ' + ('; '.join(problems) or self.said(c)))
        return {'ok': True, 'player': self.row(c, s, c.player), 'note': self.said(c)}

    def move_players(self, moves):
        c, s = self.session()
        if not isinstance(moves, list) or not moves:
            raise ToolError('moves: a list of {player_id, team} (team -1 = the free agents).')
        tp = c.parts['trade']
        rows = []
        for m in moves:
            if not isinstance(m, dict):
                raise ToolError('Each move is an object {player_id, team}.')
            _keys(m, ('player_id', 'team'), 'Not moved')
            pi = self.player(s, m.get('player_id'))
            gid = tp._gid(s, pi)
            if gid is None:
                raise ToolError(f'Player {pi} cannot be moved (no game id).')
            rows.append([gid, _int(m.get('team'), 'team'), None])
        with c.lock:
            tp.window = {'moves': rows, 'query': '', 'problems': []}
        reply = tp.apply()
        if not reply or not reply.get('ok'):
            problems = list((tp.window or {}).get('problems') or [])
            tp.close()
            raise ToolError('Not moved: ' + ('; '.join(problems) or self.said(c)))
        moved = [tp._pi_of(s, gid) for gid, _to, _lg in rows]
        return {'ok': True, 'note': self.said(c), 'players': [self.row(c, s, pi) for pi in moved if pi is not None]}

    def make_league(self, slot, name, clubs):
        c, s = self.session()
        if not isinstance(clubs, list) or not clubs:
            raise ToolError('clubs: a list of {name, city, nickname, abbr}.')
        lines = []
        for club in clubs:
            if not isinstance(club, dict):
                raise ToolError('Each club is an object {name, city, nickname, abbr}.')
            _keys(club, ('name', 'city', 'nickname', 'abbr'), 'Not made')
            parts = [str(club.get(k) or '').replace('|', '/').strip() for k in ('name', 'city', 'nickname', 'abbr')]
            lines.append(' | '.join(parts))
        lm = c.parts['leaguemaker']
        lm.open(str(slot))
        if lm.window is None:
            raise ToolError(self.said(c))
        if lm.window['values'].get('slot') != slot:
            lm.close()
            raise ToolError(f'No slot {slot!r}: list_league_slots gives them.')
        reply = lm.make({'name': str(name or ''), 'clubs': '\n'.join(lines)})
        if not reply or not reply.get('ok'):
            problems = list((lm.window or {}).get('problems') or [])
            lm.close()
            raise ToolError('Not made: ' + ('; '.join(problems) or self.said(c)))
        return {'ok': True, 'note': self.said(c)}

    def undo_last_edit(self):
        c, s = self.session()
        if not s.history:
            raise ToolError('Nothing to take back.')
        label = s.history[-1].label
        c.calls['undo']()
        self.settle(c)
        return {'ok': True, 'taken_back': label, 'note': self.said(c)}

    def save_roster_as_new(self, name, target='save'):
        from ..app import install
        c, s = self.session()
        name = ' '.join(str(name or '').split())[:64]
        if not name:
            raise ToolError('name: the new roster needs a name.')
        where = {'save': install.TARGET_SAVE, 'export': install.TARGET_EXPORT}.get(target)
        if where is None:
            raise ToolError("target: 'save' (a new custom roster NHL 19 loads) or 'export' (a file in Overtime's "
                            'exports folder).')
        with c.lock:
            if c.busy:
                raise ToolError(f'Wait a moment: {c.busy}')
            c.target, c.slot = where, None      # slot None: a new folder, never an overwrite
            c.result = None
        c.parts['save'].save_start(name=name)
        self.settle(c)
        r = c.result
        if not r or not r.get('ok'):
            raise ToolError(' '.join([(r or {}).get('title') or 'Not saved'] + list((r or {}).get('lines') or [])[:3])
                            or self.said(c))
        return {'ok': True, 'saved': r['title'], 'folder': r.get('folder', ''), 'lines': list(r.get('lines') or [])[:8],
                'not_done': list(r.get('after') or []), 'note': self.said(c)}

    # --- the list the client sees ----------------------------------------------------------------------------------
    def tools(self):
        pid = {'type': 'integer', 'description': 'A player id from find_players.'}
        return [
            Tool('overtime_status', 'Overtime status',
                 'The game and save folders, the open roster, unsaved edits, and the rosters open_roster can open.',
                 _obj({}), self.status, read_only=True),
            Tool('open_roster', 'Open a roster',
                 "Open a roster to edit: 'default' (the 2026-27 Overtime default), 'game' (the roster NHL 19 came with) "
                 'or a saved roster (its id from overtime_status). Refuses while the open roster has unsaved edits '
                 'unless discard_unsaved_edits is true.',
                 _obj({'roster': {'type': 'string'}, 'discard_unsaved_edits': {'type': 'boolean'}}, ['roster']),
                 self.open_roster),
            Tool('list_teams', 'List leagues and teams',
                 'No league: the leagues (id, name, teams). With a league id: its teams (id, code, name, players).',
                 _obj({'league': {'type': 'integer'}}), self.list_teams, read_only=True),
            Tool('find_players', 'Find players',
                 'Players by name (part of it, every league) or by team id: id, position, number, name, age, overall, '
                 'shoots, nationality, letter, team.',
                 _obj({'name': {'type': 'string'}, 'team': {'type': 'integer'},
                       'limit': {'type': 'integer', 'minimum': 1, 'maximum': LIMIT}}),
                 self.find_players, read_only=True),
            Tool('get_player', 'Get a player', 'His card: name, number, position, birth, size, contract, letter and '
                 'every rating with its label, in the units edit_player takes.',
                 _obj({'player_id': pid}, ['player_id']), self.get_player, read_only=True),
            Tool('edit_player', 'Edit a player',
                 f'Change values of his card as one edit, checked like the Roster card: {KEYS}. Only the keys given '
                 'change. Refused values change nothing and say why.',
                 _obj({'player_id': pid, 'changes': {'type': 'object'}}, ['player_id', 'changes']), self.edit_player),
            Tool('create_player', 'Create a player',
                 'A new player on a club (team id from list_teams) or the free agents (-1): first and last name, born '
                 'YYYY-MM-DD, position C/LW/RW/D/G, shoots L/R. Give him ratings next with edit_player.',
                 _obj({'first': {'type': 'string'}, 'last': {'type': 'string'}, 'born': {'type': 'string'},
                       'team': {'type': 'integer'}, 'position': {'type': 'string', 'enum': ['C', 'LW', 'RW', 'D', 'G']},
                       'shoots': {'type': 'string', 'enum': ['L', 'R']}}, ['first', 'last', 'born', 'team']),
                 self.create_player),
            Tool('move_players', 'Move players',
                 'Trades and signings as one edit: each player to a team id (-1 = the free agents). Numbers, lines '
                 'and contracts follow as in the Trade window.',
                 _obj({'moves': {'type': 'array', 'minItems': 1, 'items': _obj(
                     {'player_id': {'type': 'integer'}, 'team': {'type': 'integer'}}, ['player_id', 'team'])}},
                     ['moves']), self.move_players),
            Tool('list_league_slots', 'List league slots',
                 'The club leagues a league of yours can take (slot, the game\'s league, places, its name now).',
                 _obj({}), self.list_league_slots, read_only=True),
            Tool('make_league', 'Make a league',
                 "Put a league in a slot (list_league_slots): its name (24 letters at most) and its clubs (name, city, "
                 "nickname, abbr of 3-4 letters), up to the slot's places. One edit; NHL 19 shows the name after Patch.",
                 _obj({'slot': {'type': 'string'}, 'name': {'type': 'string'},
                       'clubs': {'type': 'array', 'minItems': 1, 'items': _obj(
                           {'name': {'type': 'string'}, 'city': {'type': 'string'}, 'nickname': {'type': 'string'},
                            'abbr': {'type': 'string'}}, ['name', 'abbr'])}}, ['slot', 'name', 'clubs']),
                 self.make_league),
            Tool('verify_roster', 'Verify the roster',
                 'The roster rules NHL 19 needs (errors) and the ones worth a look (warnings).',
                 _obj({}), self.verify_roster, read_only=True),
            Tool('list_edits', 'List unsaved edits', 'The edits made since the roster was opened or saved.',
                 _obj({}), self.list_edits, read_only=True),
            Tool('undo_last_edit', 'Undo the last edit', 'Takes back the newest edit of the open roster.',
                 _obj({}), self.undo_last_edit),
            Tool('save_roster_as_new', 'Save as a new roster',
                 "Write the open roster with its edits as a new roster: target 'save' (default: a new custom roster "
                 "NHL 19 loads) or 'export' (a file in Overtime's exports folder). Never overwrites a roster.",
                 _obj({'name': {'type': 'string'}, 'target': {'type': 'string', 'enum': ['save', 'export']}},
                      ['name']), self.save_roster_as_new),
        ]
