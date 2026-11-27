"""New player on the Roster tab (v1.00.0; docs/notes/new-player.md): a player made by hand into any club or the free
agents, as NHL Legacy's editor let you add yourself to a roster.

The window (the Players card's New player... button) asks what the roster cannot make up: his name, position, shoots,
birth date and club (the clubs the Move / trade window offers, or the free agents; the rail's team first). Make him:
overtime_core.newplayer makes him (a generic face, a donor's AI and equipment, his own ids) and signs him with the club
(number, contract, places in the lines) as one change, one Undo. His card opens: number, country, size and ratings are
the card's, his face and equipment its windows'. Save keeps him in My edits (myedits `new`): every roster update leaves
him alone and puts him back if it moved him, or makes him again in a roster that does not have him.
"""
import datetime

from overtime_core import newplayer as NP, rosterupdate as U, trades as X

from . import labels as L, myedits, roster_card as RC
from .registry import Part
from .session import BIOS, clean

PICK = ''
OLDEST = 50     # a birth year further back is a typo (the card's own floor is the field's range)


class NewPlayerCtl(Part):
    SLICES = {'newplayer': 'view'}
    CALLS = {'newplayer_open': 'open', 'newplayer_set': 'set', 'newplayer_make': 'make',
             'newplayer_close': 'close'}

    def __init__(self, ctl):
        super().__init__(ctl)
        # {'key': opened, 'values': {first, last, pos, shoots, born, league, team}, 'problems': [{key, text}]}
        self.window = None
        self.opened = 0

    def roster_changed(self):
        self.window = None

    def drafts(self):
        return 'the New player window (not made yet)' if self.window else ''

    def _say(self, text, tone='caution'):
        self.ctl.say(text, tone)
        self.ctl.changed('newplayer')
        return {'error': text} if tone == 'caution' else None

    # --- the window --------------------------------------------------------------------------------------------------
    def open(self):
        c = self.ctl
        with c.lock:
            s = c.session
            if s is None:
                return self._say('Open a roster in Setup first.')
            clubs = X.club_teams(s.db)
            team = c.team if c.team in clubs or c.team == X.FA else None
            league = X.FA if team == X.FA else clubs.get(team)
            self.opened += 1
            values = {'first': '', 'last': '', 'pos': 'C', 'shoots': 'L', 'born': '', 'league': league, 'team': team}
            self.window = {'key': self.opened, 'values': values, 'problems': []}
        c.changed('newplayer')
        return None

    def close(self):
        self.window = None
        self.ctl.changed('newplayer')

    def set(self, key, value):
        """newplayer_set(key, value): a typed or picked value. 'league' picks a league (its only club, or none yet);
        'team' a club of it."""
        c = self.ctl
        with c.lock:
            s, w = c.session, self.window
            if s is None or w is None:
                return None
            v = w['values']
            if key in ('first', 'last', 'born'):
                v[key] = str(value if value is not None else '')[:60]
            elif key == 'pos' and value in L.POSITIONS:
                v['pos'] = value
            elif key == 'shoots' and value in L.HANDS:
                v['shoots'] = value
            elif key in ('league', 'team'):
                try:
                    n = int(value)
                except (TypeError, ValueError):
                    n = None
                clubs = X.club_teams(s.db)
                if key == 'league':
                    teams = [t for t, lg in clubs.items() if lg == n and t in s.team_entries]
                    v['league'] = n if n == X.FA or teams else None
                    v['team'] = X.FA if n == X.FA else (teams[0] if len(teams) == 1 else None)
                elif n == X.FA or n in clubs:
                    v['team'], v['league'] = n, X.FA if n == X.FA else clubs[n]
            else:
                return None
            w['problems'] = [p for p in w['problems'] if p['key'] not in (key, '')]
        c.changed('newplayer')
        return None

    def _check(self, s, clock, v):
        """[{key, text}] of every wrong value, in the window's order (the card's rules)."""
        out = []
        for key, field in (('first', 'firstname'), ('last', 'lastname')):
            text = clean(v[key])
            limit = RC._text_limit(s, BIOS, field)
            if key == 'last' and not text:
                out.append({'key': key, 'text': 'Give him a last name.'})
            elif len(text.encode('utf-8')) > limit:
                out.append({'key': key, 'text': f'The {RC.WORDS[key]} is too long: {limit} letters at most.'})
        text = v['born'].strip()
        try:
            real = datetime.date.fromisoformat(text) if RC.DATE.match(text) else None
        except ValueError:
            real = None
        if real is None:
            out.append({'key': 'born', 'text': 'Write his birth date as YYYY-MM-DD, like 2001-03-14.'})
        else:
            stored, day = clock.stored(real), clock.day
            if stored.year < L.YEAR_BASE or stored.year - L.YEAR_BASE > 255 or not \
                    RC.MIN_AGE <= RC.age_on(stored, day) <= OLDEST:
                out.append({'key': 'born', 'text': f'He has to be {RC.MIN_AGE} to {OLDEST} years old.'})
        if v['team'] is None:
            out.append({'key': 'team', 'text': 'Pick his club, or the free agents.'})
        if not out:
            first, last = clean(v['first']), clean(v['last'])
            keys, _names = myedits.index(s, clock)
            if myedits.person_key(first, last, real.isoformat()) in keys:
                out.append({'key': 'last', 'text': 'A player with this name and birth date is in the roster already.'})
        return out

    def make(self, typed=None):
        """Make him: one change, then his card opens. `typed`: the window's text fields as typed (the last one may not
        have reached newplayer_set yet). {ok} or {error}."""
        c = self.ctl
        if isinstance(typed, dict):
            for key in ('first', 'last', 'born'):
                if key in typed:
                    self.set(key, typed[key])
        with c.lock:
            s, w = c.session, self.window
            if s is None or w is None:
                return None
            if c.busy:
                return self._say('Wait a moment: something else is still running.')
            rc = c.parts['roster']
            clock = rc.clock(s)
            v = w['values']
            w['problems'] = self._check(s, clock, v)
            if w['problems']:
                return self._say(w['problems'][0]['text'])
            team = v['team']
            waiting = c.parts['trade']._lines_waiting(s, [team]) if team != X.FA else ''
            if waiting:
                w['problems'] = [{'key': 'team', 'text': waiting}]
                return self._say(waiting)
            first, last = clean(v['first']), clean(v['last'])
            name = ' '.join(f'{first} {last}'.split())
            where = 'Free agents' if team == X.FA else s.team_name(team)
            deal_years = c.parts['trade']._deal_years(s)

            def work(db):
                pi, _gid, _plan = NP.create(db, first, last, v['pos'], v['shoots'], v['born'].strip(), team,
                                            clock.shift, deal_years)
                return [(f'{name}: new player', '-', where)], pi
            try:
                ch, pi = s.bulk(f'New player {name} ({where})', work)
            except X.TradeError as err:
                w['problems'] = [{'key': 'team', 'text': p} for p in err.problems[:3]] or \
                    [{'key': '', 'text': str(err)}]
                return self._say(w['problems'][0]['text'])
            except (U.UpdateError, ValueError) as err:
                w['problems'] = [{'key': '', 'text': str(err)}]
                return self._say(str(err))
            rc.note(ch, pi, myedits.NEW, ['new player'], [])
            self.window = None
            c.issues = None
        c.host.log(f'New player: {name} ({where})')
        c.parts['rail'].pick_team(RC.rail_team(s, pi))
        with c.lock:
            if c.session is s:
                c.player, c.query = pi, ''
        c.say(f'{name} is on {where}. Not saved yet: give him his number, ratings and face on his card, then press '
              'Save (My edits keeps him for every update).', 'good')
        c.changed('newplayer', 'roster', 'roster_card', 'editor', 'lines', 'strategy', 'save', 'rail', 'office',
                  'trade')
        return {'ok': True}

    # --- the slice ---------------------------------------------------------------------------------------------------
    def view(self):
        c = self.ctl
        with c.lock:
            s, w = c.session, self.window
            if s is None or w is None:
                return {'window': None, 'busy': bool(c.busy)}
            v = w['values']
            clubs = X.club_teams(s.db)
            leagues = c.parts['trade']._league_options(s, clubs)
            return {'busy': bool(c.busy), 'window': {
                'key': w['key'], 'values': dict(v, league=PICK if v['league'] is None else v['league'],
                               team=PICK if v['team'] is None else v['team']),
                'problems': list(w['problems']), 'leagues': leagues,
                'positions': list(L.POSITIONS), 'hands': list(L.HANDS),
                'can_make': not c.busy and v['team'] is not None and bool(v['last'].strip())
                and bool(v['born'].strip())}}
