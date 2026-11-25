"""A player made by hand: the Roster tab's New player (v1.00.0; docs/notes/new-player.md), into any club or the free
agents, as NHL Legacy's editor let you add yourself to a roster.

He is made the way the roster update makes a player NHL 19 does not have (rosterupdate._Maker): a donor with a generic
face lends his AI, equipment and the bio fields nobody types (his own game id, playerindex and portrait art id; no
draft, no pro history, no NHL games), then he is a free agent (add_unsigned's steps) and signs with the club through
the Move / trade code (trades.move_players: number, contract, places in the lines, the free agent list). The rest of
his card (number, country, size, ratings, face, equipment) is the Roster tab's own card and windows.
"""
from . import nhl27 as N, rosterupdate as U, trades as X

FA = X.FA
CODES = {'C': 'C', 'LW': 'L', 'RW': 'R', 'D': 'D', 'G': 'G'}   # the card's positions -> NHL.com's (_Maker reads those)


def create(db, first, last, pos, shoots, born, team, shift=0, deal_years=1):
    """Make one player in `db`: `pos` a card position (C LW RW D G), `shoots` 'L' or 'R', `born` 'YYYY-MM-DD' (his
    real birth date; `shift`: years the roster's dates sit behind, roster_card.roster_shift), `team` a club index
    (trades.club_teams) or FA. Returns (playerindex, game_id, trades.Plan or None). Raises U.UpdateError or
    X.TradeError; `db` may be half written then (the caller keeps it to put back: session.bulk)."""
    if pos not in CODES:
        raise U.UpdateError(f'there is no position {pos}')
    if team != FA and team not in X.club_teams(db):
        raise X.TradeError(['Pick a club or the free agents.'])
    real = {'first': first, 'last': last, 'position': CODES[pos], 'shoots': shoots, 'birth': born}
    pi, gid, _style, _donor = U._Maker(db).make(real, -1, -1, U.UNSIGNED_NUMBER, None, shift)
    bios = db[U.BIOS]
    for f, v in dict(N.NO_CONTRACT, contractstatus=-1).items():   # a free agent's, as add_unsigned's
        bios.set(bios.count - 1, f, v)
    U.sort_players(db)
    U._rebuild_free(db, remove=(), add=[pi])
    plan = X.move_players(db, [(gid, team)], deal_years) if team != FA else None
    return pi, gid, plan
