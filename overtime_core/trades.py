"""Trades and moves: players change clubs, go to the free agents or come from them, several in one go (the game's own
Edit Rosters moves one at a time), and the clubs two rosters disagree on (a save the player changed in NHL 19 against
the app's open roster). docs/notes/trades.md.

A move writes only the patterns the update and the Front office's signing already write (rosterupdate):
- the player's club record moves: its row leaves the old club's rows of exhibitionrostertable and joins the end of the
  new club's (keys in the stock layout, rosterupdate._rebuild_roster); he arrives without a captain's letter;
- number: his own when the new club has it free, else the first free one from 2 (as sign_player);
- bio, the three stock patterns of a club player (rosterupdate._sign_free_agents, _unsign):
  an NHL club: team and proteam the club, contractstatus 0; his NHL deal stays, one who had none gets the lowest
  one-season deal (nhl27.estimate); a club of another league: team the club, an NHL deal or NHL rights stay with
  their proteam (a farm or loaned player), anyone else keeps contractstatus -1; the free agents: no team, no deal;
- lines: a newcomer sits out (a spare, as a signing). The places of a player who left go to one player of his kind
  (goalie, defenceman, forward): a newcomer of that kind first, else the team's best spare of that kind who holds no
  place (the Lines tab's rule: a scratch who comes in takes every place of the one he replaces). A team still left
  with a place nobody holds gets its lines dealt again by ratings (lines.build);
- an NHL goalie without a career row gets one (careerstats.fill: Play Now crashes without it).
Refused, nothing changed: Seattle and Coachella Valley (custom teams with a Play Now copy, a follow-up), the All-Star,
national, Pro-Am and other copy teams, a club with no room (40 rows), a club left short of 2 goalies or 18 skaters
(the game hangs on a team it cannot dress: rosterupdate.short_teams), and a result the verify rules (roster.py) or
the update's checks find a new problem in.
"""
from dataclasses import dataclass, field

from . import careerstats, lines, nhl27 as N, rosterupdate as U, teams as T
from .roster import Roster, _clean

FA = -1                     # the free agents, as a team (labels.FREE_AGENTS)
SEATTLE_TEAMS = (T.SEATTLE, T.SEATTLE_AHL, T.SEATTLE_PLAY_NOW)
DRESS = {'G': 2, 'S': 18}   # a club dresses 2 goalies and 18 skaters (lines.deal)
NUMBERS = range(2, 99)      # the first free number from 2 (sign_player)
SEATTLE_LATER = 'Seattle and Coachella Valley are custom teams with a Play Now copy: their trades come later.'
DIFFERENT_SHARE = 0.9       # fewer players in common than this: two different rosters, not one changed in the game
DIFFERENT_MOVES = 300


class TradeError(ValueError):
    """A move the roster refuses; nothing was changed. `problems`: every sentence."""

    def __init__(self, problems):
        self.problems = list(problems)
        super().__init__(' '.join(self.problems))


@dataclass
class Moved:
    """One player of a trade, as planned (preview) or done (move_players)."""
    game_id: int
    pi: int                 # his club record (exhibitionplayers index), or his free agent record
    name: str
    kind: str               # 'G', 'D' or 'F'
    frm: int                # team index or FA
    to: int
    number: int = None      # on the new club (None: a free agent)
    old_number: int = None
    deal: bool = False      # gets the lowest deal (he had no NHL deal)
    takes: str = ''         # the name of the player whose places he takes ('' : he sits out)


@dataclass
class Plan:
    moves: list = field(default_factory=list)       # [Moved]
    problems: list = field(default_factory=list)    # sentences: the trade cannot go through
    fills: dict = field(default_factory=dict)       # {team: [(pi in, pi out, slots, dressed)]}
    dealt: list = field(default_factory=list)       # teams whose lines were dealt again (move_players)


def kind_of(position):
    return 'G' if position == U.GOALIE else 'D' if position == 3 else 'F'


def club_teams(db):
    """{team index: league} of the clubs players can move between: the NHL's 31 and every club league
    (rosterupdate.CLUB_LEAGUES), without the All-Star teams and Seattle's Play Now copy."""
    return {r['index']: r['league'] for r in db[T.TEAMS].rows()
            if r['league'] in U.CLUB_LEAGUES and r['index'] not in U.SHADOW_TEAMS}


def _custom_of(db, state):
    """{game_id: custom team} of Seattle's and Coachella Valley's players (customrostertable)."""
    out = {}
    if U.CUSTOM_ROSTER in db:
        t, players = db[U.CUSTOM_ROSTER], db[U.PLAYERS]
        gid = {players.get(i, 'index'): players.get(i, 'playerid') for i in range(players.count)
               if players.get(i, 'table') == 0}
        for pi, team in zip(t.column('playerindex'), t.column('team')):
            if team in SEATTLE_TEAMS and pi in gid:
                out[gid[pi]] = team
    return out


def _record(state, clubs, gid):
    """(pi, team) of a bio's club record, else (pi, FA) of his free agent record, else (None, None)."""
    pis = state.pis_of.get(gid, [])
    club = sorted(p for p in pis if p in state.entry and state.entry[p][0] == U.ROSTER and state.entry[p][1] in clubs)
    if club:
        return club[0], state.entry[club[0]][1]
    free = sorted(p for p in pis if p in state.free)
    return (free[0], FA) if free else (None, None)


def where(db):
    """{game_id: club index, FA, or teams.SEATTLE / SEATTLE_AHL} of every player with a club record, a free agent
    record or a place on Seattle's or Coachella Valley's custom roster; players only on copy teams are left out."""
    state, clubs = U.State(db), club_teams(db)
    custom = _custom_of(db, state)
    out = {}
    for gid in state.pis_of:
        if gid in custom:
            out[gid] = T.SEATTLE if custom[gid] in (T.SEATTLE, T.SEATTLE_PLAY_NOW) else T.SEATTLE_AHL
            continue
        _pi, team = _record(state, clubs, gid)
        if team is not None:
            out[gid] = team
    return out


def _name(b):
    return _clean(f"{b['firstname']} {b['lastname']}") or f"player {b['game_id']}"


def _team_names(db):
    """{team index: name} as the app's team list shows them (session.team_name: the nickname, no (R))."""
    return {r['index']: (_clean(r.get('nickname') or r.get('teamname') or '').rstrip('®™ ')
                         or f"team {r['index']}") for r in db[T.TEAMS].rows()}


def team_name(names, team):
    return 'the free agents' if team == FA else names.get(team, f'team {team}')


def preview(db, moves):
    """The Plan of `moves` [(game_id, to: team index or FA)] without changing anything: who goes where, his number, whose
    places he takes, and every reason the trade cannot go through (plan.problems)."""
    return _plan(db, U.State(db), list(moves))


def _plan(db, state, moves):
    clubs = club_teams(db)
    custom = _custom_of(db, state)
    names = _team_names(db)
    roster = db[U.ROSTER]
    plan = Plan()
    bad = plan.problems
    seen = set()
    for gid, to in moves:
        brow = state.bio_row.get(gid)
        if brow is None:
            bad.append(f'Player {gid} is not in this roster.')
            continue
        b = db[U.BIOS].row(brow)
        who = _name(b)
        if gid in seen:
            bad.append(f'{who} is in the trade twice.')
            continue
        seen.add(gid)
        if gid in custom:
            bad.append(f'{who} plays for {"Coachella Valley" if custom[gid] == T.SEATTLE_AHL else "Seattle"}. '
                       + SEATTLE_LATER)
            continue
        pi, frm = _record(state, clubs, gid)
        if pi is None:
            bad.append(f'{who} plays for no club and is not a free agent: only his copies (All-Stars, national team) '
                       'are in this roster.')
            continue
        if to in SEATTLE_TEAMS:
            bad.append(SEATTLE_LATER)
            continue
        if to != FA and to not in clubs:
            bad.append(f'{team_name(names, to)} is not a club players move to (the All-Star, national and other copy '
                       'teams keep their own cards).')
            continue
        if to == frm:
            bad.append(f'{who} already plays for {team_name(names, to)}.')
            continue
        old = roster.get(_row_of(roster, pi), 'jersey') if frm != FA else b['jersey']
        plan.moves.append(Moved(gid, pi, who, kind_of(b['position']), frm, to, old_number=old))
    if bad:
        return plan

    rows_of = {}    # team -> [row] of exhibitionrostertable now
    for i, team in enumerate(roster.column('team')):
        rows_of.setdefault(team, []).append(i)
    leaving = {m.pi for m in plan.moves if m.frm != FA}
    teams = {m.frm for m in plan.moves} | {m.to for m in plan.moves}
    teams.discard(FA)
    pi_col = roster.column('playerindex')
    for team in sorted(teams):
        stay = [i for i in rows_of.get(team, []) if pi_col[i] not in leaving]
        come = [m for m in plan.moves if m.to == team]
        n = len(stay) + len(come)
        if n > U.KEYS_PER_TEAM:
            bad.append(f'{team_name(names, team)} would have {n} players: the game holds {U.KEYS_PER_TEAM} a team.')
        count = lambda rows, extra: {  # noqa: E731
            'G': sum(_kind_at(db, state, pi_col[i]) == 'G' for i in rows) + sum(m.kind == 'G' for m in extra),
            'S': sum(_kind_at(db, state, pi_col[i]) in ('D', 'F') for i in rows) + sum(m.kind != 'G' for m in extra)}
        now, after = count(rows_of.get(team, []), []), count(stay, come)
        short = [k for k in DRESS if after[k] < DRESS[k] and after[k] < now[k]]
        if short:
            goalies = f"{after['G']} goalie{'s' if after['G'] != 1 else ''}"
            bad.append(f"{team_name(names, team)} would have {goalies} and {after['S']} skaters: a team needs "
                       f"{DRESS['G']} goalies and {DRESS['S']} skaters to play. Add "
                       f"{'a goalie' if 'G' in short else 'a skater'} to the trade.")
        used = {roster.get(i, 'jersey') for i in stay}
        for m in come:
            want = m.old_number
            m.number = want if want in range(1, 100) and want not in used else next((k for k in NUMBERS if k not in used),
                                                                                   None)
            if m.number is None:
                bad.append(f'{team_name(names, team)} has every number taken.')
            used.add(m.number)
        _fill_plan(db, state, plan, team, rows_of.get(team, []), stay, come)
    net = sum(1 for m in plan.moves if m.frm == FA) - sum(1 for m in plan.moves if m.to == FA)
    if roster.count + net > roster.max_records:
        bad.append(f'The roster table is full ({roster.max_records} rows).')
    for m in plan.moves:
        if m.to in U.NHL:
            b = state.bio(m.pi)
            m.deal = not (b['contractstatus'] == 0 and b['contractdollars'] > 0)
    return plan


def _row_of(roster, pi):
    return roster.column('playerindex').index(pi)


def _kind_at(db, state, pi):
    b = state.bio(pi)
    return kind_of(b['position']) if b is not None else None


def _fill_plan(db, state, plan, team, rows, stay, come):
    """Who takes the places of each player leaving `team`: a newcomer of his kind, else the best spare of his kind who
    holds no place. A leaver nobody replaces is left to the check after the move (lines dealt again)."""
    roster = db[U.ROSTER]
    stay_set = set(stay)
    newcomers = list(come)
    fills = []
    quality = {p.index: p.q for p in lines.players_of(db, team)}

    def places(i):
        r = roster.row(i)
        return frozenset(s for s in lines.SLOTS if r.get(s)), bool(r.get(lines.DRESSED))

    taken = set()
    leavers = [i for i in rows if i not in stay_set]
    leavers.sort(key=lambda i: -len(places(i)[0]))
    for i in leavers:
        slots, dressed = places(i)
        if not slots:
            continue
        out_pi = roster.get(i, 'playerindex')
        kind = _kind_at(db, state, out_pi)
        m = next((m for m in newcomers if m.kind == kind and m.pi not in taken), None)
        if m is not None:
            taken.add(m.pi)
            m.takes = next((x.name for x in plan.moves if x.pi == out_pi), '')
            fills.append((m.pi, out_pi, slots, dressed))
            continue
        spares = []
        for j in stay:
            pi = roster.get(j, 'playerindex')
            held, on = places(j)
            if pi in taken or held or on or _kind_at(db, state, pi) != kind:
                continue
            spares.append((-quality.get(pi, 0), pi))
        if spares:
            pi = min(spares)[1]
            taken.add(pi)
            fills.append((pi, out_pi, slots, dressed))
    if fills:
        plan.fills[team] = fills


def _issues(db, teams):
    """What the verify rules (strict) and the update's checks find on these teams and in the whole roster's keys,
    goalie careers and free agent list, as comparable keys."""
    out = set()
    for i in Roster.from_database(db).verify(strict=True):
        if i.team is None or i.team in teams or i.rule in ('duplicate_player', 'dangling_player', 'capacity'):
            out.add((i.rule, i.team, i.player, i.message if i.rule in ('capacity',) else ''))
    out |= {('keys', p) for p in U.key_problems(db)}
    for team in teams:
        out |= {('lineup', team, p) for p in lines.check_lineup(db, team)}
    if careerstats.SEASON in db:
        out |= {('career', p) for p in careerstats.check(db)}
    return out


def move_players(db, moves, deal_years=1):
    """Do the trade `moves` [(game_id, to: team index or FA)] in `db` as one piece. `deal_years`: the stored length of
    the lowest deal a player without an NHL deal gets at an NHL club (+1 on a roster that carries the expansion
    season, as the Front office's signing). Returns the Plan (moves, whose places each took, teams whose lines were
    dealt again); raises TradeError and changes nothing when the roster refuses it."""
    state = U.State(db)
    plan = _plan(db, state, list(moves))
    if plan.problems:
        raise TradeError(plan.problems)
    if not plan.moves:
        raise TradeError(['Pick a player to move first.'])
    teams = {m.frm for m in plan.moves} | {m.to for m in plan.moves}
    teams.discard(FA)
    kept = db.keep()
    before = _issues(db, teams)
    careers_before = set(careerstats.missing(db)) if careerstats.SEASON in db else set()
    lineup_before = {team: (set(lines.check_lineup(db, team)), _held(db, team)) for team in teams}
    try:
        _write(db, state, plan, deal_years)
        names = _team_names(db)
        for team in sorted(teams):
            problems, held = lineup_before[team]
            if set(lines.check_lineup(db, team)) - problems or held - _held(db, team):
                try:
                    lines.build(db, team)
                except lines.NotEnoughPlayers as err:
                    raise TradeError([f'{team_name(names, team)} cannot dress a lineup: {err}.']) from None
                plan.dealt.append(team)
        if careerstats.SEASON in db and set(careerstats.missing(db)) - careers_before:
            careerstats.fill(db)    # a goalie new to an NHL club (fill also gives the ones the roster lacked a row)
        new = _issues(db, teams) - before
        if new:
            raise TradeError([f'The roster would break a rule: {_said(k)}' for k in sorted(new, key=str)[:5]])
    except (TradeError, U.UpdateError, ValueError) as err:
        db.put_back(kept)
        if isinstance(err, TradeError):
            raise
        raise TradeError([str(err)]) from None
    return plan


def _held(db, team):
    """The line places (of the 87) someone on `team` holds."""
    roster = db[U.ROSTER]
    return {s for i, on in enumerate(roster.column('team')) if on == team for s in lines.SLOTS if roster.get(i, s)}


def _said(key):
    return ' '.join(str(x) for x in key if x not in (None, ''))


def _write(db, state, plan, deal_years):
    bios, roster = db[U.BIOS], db[U.ROSTER]
    adds = []
    for m in plan.moves:
        b = state.bio(m.pi)
        brow = state.bio_row[b['game_id']]
        if m.to == FA:
            U._unsign(bios, brow, b)
            continue
        if m.to in U.NHL:
            values = {'team': m.to, 'proteam': m.to, 'jersey': m.number, 'contractstatus': 0}
            if m.deal:
                values.update(N.estimate(99), contractlength=deal_years)
        else:
            values = {'team': m.to, 'jersey': m.number}
            tied = b['proteam'] in U.NHL and b['contractstatus'] == 0
            if not tied:
                values.update(proteam=-1, contractstatus=-1)
        for f, v in values.items():
            if b[f] != v:
                bios.set(brow, f, v)
        adds.append((m.to, {'team': m.to, 'playerindex': m.pi, 'jersey': m.number,
                            'playerstyle': U._ai_value(db, b, 'playerstyle', 0)}))
    leaving = {m.pi for m in plan.moves if m.frm != FA}
    at = U._rebuild_roster(roster, leaving, adds)
    for fills in plan.fills.values():
        for pi_in, _pi_out, slots, dressed in fills:
            row = at[pi_in]
            for s in slots:
                if roster.get(row, s) != 1:
                    roster.set(row, s, 1)
            if roster.get(row, lines.DRESSED) != int(dressed):
                roster.set(row, lines.DRESSED, int(dressed))
    signed = {p for m in plan.moves if m.to != FA for p in state.pis_of.get(m.game_id, ()) if p in state.free}
    released = {m.pi for m in plan.moves if m.to == FA
                and not any(p in state.free for p in state.pis_of.get(m.game_id, ()))}
    if signed or released:
        U._rebuild_free(db, remove=signed, add=released)


# --- two rosters compared ----------------------------------------------------------------------------------------------
@dataclass
class Comparison:
    """The clubs a save (`theirs`, e.g. one the player changed in NHL 19) has its players on where the open roster
    (`mine`) has them elsewhere."""
    moves: list = field(default_factory=list)     # [(game_id, name, kind, from in mine, to in theirs)]
    skipped: list = field(default_factory=list)   # [(game_id, name, kind, from, to, why)]
    unknown: list = field(default_factory=list)   # names only in theirs (made in the game): not brought over
    common: int = 0                               # players both know
    different: bool = False                       # too little in common: not one roster changed in the game


def compare(mine, theirs):
    """Comparison of two databases by bio game_id: each player's club (or the free agents) in both. A move to or from
    Seattle or Coachella Valley, or to a club `mine` does not have, is listed as skipped with its reason."""
    a, b = where(mine), where(theirs)
    clubs = club_teams(mine)
    state = U.State(mine)
    out = Comparison()
    out.common = len(set(a) & set(b))
    bios_theirs = theirs[U.BIOS]
    gid_rows = {g: i for i, g in enumerate(bios_theirs.column('game_id'))}
    for gid in sorted(set(b) - set(a)):
        if gid not in state.bio_row and gid in gid_rows and b[gid] != FA:
            out.unknown.append(_name(bios_theirs.row(gid_rows[gid])))
    for gid in sorted(set(a) & set(b)):
        frm, to = a[gid], b[gid]
        if frm == to:
            continue
        bio = mine[U.BIOS].row(state.bio_row[gid])
        item = (gid, _name(bio), kind_of(bio['position']), frm, to)
        if frm in SEATTLE_TEAMS or to in SEATTLE_TEAMS:
            out.skipped.append(item + (SEATTLE_LATER,))
        elif to != FA and to not in clubs:
            out.skipped.append(item + ('That club is not in the open roster.',))
        else:
            out.moves.append(item)
    out.different = (out.common < DIFFERENT_SHARE * max(1, min(len(a), len(b)))
                     or len(out.moves) > DIFFERENT_MOVES)
    return out
