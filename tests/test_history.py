"""Match history rules (overtime_core.history): claims, confirmation, standings, a player's detail."""
from overtime_core import history as H


def claim(team, sf, sa, opp=None):
    return {'team': team, 'opp_team': opp, 'for': sf, 'against': sa, 'source': 'app'}


def match(mid, a, b, ca=None, cb=None, started=1000.0):
    claims = {}
    if ca:
        claims[a[0]] = ca
    if cb:
        claims[b[0]] = cb
    return {'id': mid, 'started': started, 'code': None, 'rules': None,
            'players': [{'pid': a[0], 'name': a[1]}, {'pid': b[0], 'name': b[1]}], 'claims': claims}


ANN, BO, CY = ('a1', 'Ann'), ('b2', 'Bo'), ('c3', 'Cy')


def test_pid_is_salted_and_stable():
    assert H.pid(5, 's') == H.pid('5', 's') != H.pid(5, 't') != H.pid(6, 's')
    assert len(H.pid(5, 's')) == 10 and '5' != H.pid(5, 's')


def test_team_and_score_checks():
    assert H.team_code(' pit ') == 'PIT' and H.team_code('NHLX9') is None and H.team_code('A') is None
    assert H.team_code(None) is None and H.team_code(7) is None
    assert H.score('3') == 3 and H.score(0) == 0 and H.score(100) is None and H.score(-1) is None
    assert H.score(True) is None and H.score(2.5) is None and H.score('x') is None


def test_no_claim_is_open():
    r = H.resolve(match(1, ANN, BO))
    assert r['status'] == H.OPEN and r['winner'] is None and r['scores'] == {'a1': None, 'b2': None}


def test_one_claim_is_waiting_for_the_other_and_shows_the_provisional_score():
    r = H.resolve(match(1, ANN, BO, ca=claim('PIT', 3, 2, 'BOS')))
    assert (r['status'], r['waiting_for'], r['winner']) == (H.WAITING, 'b2', None)
    assert r['scores'] == {'a1': 3, 'b2': 2} and r['teams'] == {'a1': 'PIT', 'b2': 'BOS'}


def test_mirroring_claims_confirm_and_name_the_winner():
    r = H.resolve(match(1, ANN, BO, ca=claim('PIT', 3, 2), cb=claim('BOS', 2, 3)))
    assert (r['status'], r['winner']) == (H.CONFIRMED, 'a1')
    assert r['scores'] == {'a1': 3, 'b2': 2} and r['teams'] == {'a1': 'PIT', 'b2': 'BOS'}
    r = H.resolve(match(2, ANN, BO, ca=claim('PIT', 1, 4), cb=claim('BOS', 4, 1)))
    assert r['winner'] == 'b2'


def test_claims_that_differ_are_disputed_and_nobody_wins():
    r = H.resolve(match(1, ANN, BO, ca=claim('PIT', 3, 2), cb=claim('BOS', 3, 2)))
    assert r['status'] == H.DISPUTED and r['winner'] is None
    assert H.resolve(match(1, ANN, BO, ca=claim('PIT', 3, 2), cb=claim('BOS', 2, 4)))['status'] == H.DISPUTED


def test_two_game_reports_off_by_one_goal_still_confirm_with_each_sides_own_score():
    """Match 75 (2026-11-10): the game said 8-5 to one side and 4-8 to the other; the winner and own scores agree."""
    def game(team, sf, sa):
        return {**claim(team, sf, sa), 'source': 'game'}
    m = match(75, ANN, BO, ca=game('TB', 8, 5), cb=game('PIT', 4, 8))
    r = H.resolve(m)
    assert (r['status'], r['winner']) == (H.CONFIRMED, 'a1') and r['scores'] == {'a1': 8, 'b2': 4} and H.full(m)
    # two goals apart, a different winner, or a typed entry among them: still a dispute
    assert H.resolve(match(1, ANN, BO, ca=game('TB', 8, 6), cb=game('PIT', 4, 8)))['status'] == H.DISPUTED
    assert H.resolve(match(1, ANN, BO, ca=game('TB', 5, 4), cb=game('PIT', 5, 4)))['status'] == H.DISPUTED
    assert H.resolve(match(1, ANN, BO, ca=game('TB', 8, 5), cb=claim('PIT', 4, 8)))['status'] == H.DISPUTED
    assert not H.full(match(1, ANN, BO, ca=game('TB', 8, 6), cb=game('PIT', 4, 8)))


def test_threes_game_reports_are_decided_by_each_sides_own_score():
    """Match 79 (2026-11-10, lost 14-2): the winner's game said 14-1, the loser's 2-10. Each own score is right."""
    def game(team, sf, sa):
        return {**claim(team, sf, sa), 'source': 'game'}

    def threes(ca, cb):
        return {**match(79, ANN, BO, ca=ca, cb=cb), 'mode': 'threes'}
    m = threes(game('MTL', 14, 1), game('PIT', 2, 10))
    r = H.resolve(m)
    assert (r['status'], r['winner']) == (H.CONFIRMED, 'a1') and r['scores'] == {'a1': 14, 'b2': 2} and H.full(m)
    assert H.resolve(threes(game('MTL', 8, 3), game('PIT', 2, 6)))['scores'] == {'a1': 8, 'b2': 2}     # match 78
    # both claim the win, both the loss, equal own scores, or a typed entry: still a dispute
    for ca, cb in ((game('MTL', 5, 1), game('PIT', 6, 2)), (game('MTL', 1, 5), game('PIT', 2, 6)),
                   (game('MTL', 3, 1), game('PIT', 3, 2)), (game('MTL', 14, 1), claim('PIT', 2, 10))):
        assert H.resolve(threes(ca, cb))['status'] == H.DISPUTED
    # outside Threes the one-goal rule stands
    assert H.resolve(match(79, ANN, BO, ca=game('MTL', 14, 1), cb=game('PIT', 2, 10)))['status'] == H.DISPUTED


def test_a_missing_team_is_taken_from_the_other_claim():
    r = H.resolve(match(1, ANN, BO, ca=claim(None, 3, 2, 'BOS'), cb=claim('BOS', 2, 3)))
    assert r['teams'] == {'a1': None, 'b2': 'BOS'}
    r = H.resolve(match(1, ANN, BO, ca=claim('PIT', 3, 2), cb=claim(None, 2, 3)))
    assert r['teams']['b2'] is None


def games():
    """Newest first: Ann beat Bo (PIT vs BOS) twice, lost to Cy once, one match still unplayed, one disputed."""
    return [
        match(5, ANN, BO, started=5000.0),
        match(4, ANN, CY, ca=claim('PIT', 1, 2), cb=claim('TOR', 2, 1), started=4000.0),
        match(3, ANN, BO, ca=claim('PIT', 4, 0), cb=claim('BOS', 0, 4), started=3000.0),
        match(2, BO, CY, ca=claim('BOS', 3, 4), cb=claim('TOR', 3, 4), started=2000.0),
        match(1, ANN, BO, ca=claim('PIT', 5, 3), cb=claim('BOS', 3, 5), started=1000.0),
    ]


def test_standings_count_only_confirmed_matches_best_first():
    rows = H.standings(games())
    assert [(r['name'], r['w'], r['l'], r['played']) for r in rows] == [('Ann', 2, 1, 3), ('Cy', 1, 0, 1), ('Bo', 0, 2, 2)]
    ann = rows[0]
    assert (ann['gf'], ann['ga'], ann['last']) == (10, 5, 4000.0)


def test_standings_skip_players_without_a_confirmed_match():
    assert H.standings([match(1, ANN, BO)]) == []


def test_player_detail_lists_opponents_teams_and_recent_matches():
    d = H.player_detail(games(), 'a1')
    assert (d['name'], d['w'], d['l'], d['played']) == ('Ann', 2, 1, 3)
    assert [(o['name'], o['w'], o['l']) for o in d['opponents']] == [('Bo', 2, 0), ('Cy', 0, 1)]
    assert [(t['team'], t['w'], t['l']) for t in d['teams']] == [('PIT', 2, 1)]
    assert [(t['team'], t['w'], t['l']) for t in d['against']] == [('BOS', 2, 0), ('TOR', 0, 1)]
    assert [m['id'] for m in d['recent']] == [5, 4, 3, 1]
    assert [m['result'] for m in d['recent']] == [None, 'L', 'W', 'W']
    last = d['recent'][1]
    assert (last['opponent']['name'], last['team'], last['opp_team'], last['for'], last['against']) == ('Cy', 'PIT', 'TOR', 1, 2)


def test_player_detail_unknown_player_and_limit():
    assert H.player_detail(games(), 'zz') is None
    assert len(H.player_detail(games(), 'a1', limit=2)['recent']) == 2


def test_a_forfeit_is_a_1_0_loss_for_the_player_who_quit_whatever_a_lone_claim_says():
    m = match(1, ANN, BO, cb=claim('BOS', 0, 4))                 # Bo's own (unfinished) score
    m['forfeit'] = ANN[0]
    r = H.resolve(m)
    assert (r['status'], r['winner'], r['left'], r['forfeit']) == (H.CONFIRMED, BO[0], ANN[0], True)
    assert r['scores'] == {ANN[0]: 0, BO[0]: 1} and r['waiting_for'] is None
    assert H.resolve(match(2, ANN, BO))['forfeit'] is False


def test_two_mirroring_reports_stand_over_a_forfeit_a_dispute_does_not():
    m = match(1, ANN, BO, ca=claim('PIT', 3, 2), cb=claim('BOS', 2, 3))
    m['forfeit'] = ANN[0]
    r = H.resolve(m)
    assert (r['status'], r['winner'], r['forfeit']) == (H.CONFIRMED, ANN[0], False)
    m['claims'][BO[0]] = claim('BOS', 5, 3)                       # the two differ: the quit decides
    r = H.resolve(m)
    assert (r['status'], r['winner'], r['forfeit']) == (H.CONFIRMED, BO[0], True)
    rows = H.standings([m])
    assert [(x['name'], x['w'], x['l'], x['gf'], x['ga']) for x in rows] == [('Bo', 1, 0, 1, 0), ('Ann', 0, 1, 0, 1)]


def test_game_stats_keep_penalty_minutes_and_drop_the_numbers_the_game_leaves_at_0():
    # live match 1 of 2026-11-07: pims 480 with four minors (the opponent had 4 power plays); shotsa / fol 0 on both sides
    raw = {'shots': 26, 'shotsa': 0, 'pims': 480, 'ppo': 3, 'fow': 8, 'fol': 0, 'toa': 230}
    assert H.clean_stats(raw) == {'shots': 26, 'pims': 8, 'ppo': 3, 'fow': 8, 'toa': 230}
    assert H.clean_stats({'shotsa': 0, 'fol': 0}) is None and H.clean_stats({'pims': 300})['pims'] == 5


def test_the_opponents_report_gives_shots_against_and_faceoffs_lost():
    mine = {'shots': 26, 'fow': 8}
    assert H.with_opponent(mine, {'shots': 34, 'fow': 24}) == {'shots': 26, 'fow': 8, 'shotsa': 34, 'fol': 24}
    assert H.with_opponent(mine, None) == mine and H.with_opponent(mine, {}) is not mine
    s = H.stat_summary([{'stats': {'fow': 8}, 'for': 2, 'against': 4}])
    assert s['rates']['faceoffs'] is None and s['rates']['saving'] is None   # no opponent numbers: no rate


# --- World of Chel player lines (v1.00.0): each player's own skater or goalie line, goalie metrics apart ---------------

GOALIE_LINE = {'pos': 0, 'glgp': 1, 'glshots': 20, 'glsaves': 18, 'glga': 2, 'glso': 0, 'toiseconds': 3600}
SKATER_LINE = {'pos': 4, 'skgp': 1, 'skgoals': 1, 'skassists': 2, 'skplusmin': -1, 'skshots': 4, 'skhits': 3}


def woc_match(mid, home, away, lines, score=(3, 2), mode='chel_dropin'):
    """A two-side WoC match where every player reported (`home`/`away` pids, `lines` {pid: his stats})."""
    players = [{'pid': p, 'name': p, 'side': s} for s, pids in enumerate((home, away)) for p in pids]
    claims = {p['pid']: {'team': None, 'opp_team': None, 'for': score[p['side']], 'against': score[1 - p['side']],
                         'source': 'game', 'at': 1.0, 'side': p['side'], 'stats': lines.get(p['pid'])} for p in players}
    return {'id': mid, 'started': 1000.0 + mid, 'code': None, 'rules': None, 'mode': mode, 'sides': 2,
            'players': players, 'claims': claims}


def test_clean_woc_stats_keeps_whole_skater_and_goalie_numbers_and_the_position():
    raw = {**GOALIE_LINE, 'glsavepct': 0.9, 'glgaa': 2.0, 'playername': 'x', 'ratingDefense': 70.5, 'skplusmin': -3,
           'skgoals': True, 'skshots': -1, 'skhits': H.STAT_MAX + 1, 'toi': 60}
    assert H.clean_woc_stats(raw) == {**GOALIE_LINE, 'skplusmin': -3}
    assert H.clean_woc_stats(None) is None and H.clean_woc_stats({'pos': 0}) is None
    assert H.clean_woc_stats({'glsavepct': 0.9, 'skgoals': 1.0}) is None
    assert H.clean_woc_stats({'skgoals': 1, 'pos': 12}) == {'skgoals': 1}
    assert H.clean_woc_stats({'skplusmin': -H.STAT_MAX - 1}) is None


def test_the_role_and_the_line_tell_a_goalie_from_a_skater():
    assert H.woc_role(GOALIE_LINE) == H.GOALIE and H.woc_role(SKATER_LINE) == H.SKATER
    assert H.woc_role({'glgp': 1}) == H.GOALIE and H.woc_role({'glgp': 1, 'skgp': 1}) == H.SKATER
    assert H.woc_line(GOALIE_LINE) == {'role': 'goalie', 'pos': 'G', 'shots': 20, 'saves': 18, 'ga': 2, 'svpct': 0.9}
    assert H.woc_line(SKATER_LINE) == {'role': 'skater', 'pos': 'C', 'g': 1, 'a': 2, 'pts': 3, 'plusmin': -1,
                                       'shots': 4, 'hits': 3}
    assert H.woc_line({'pos': 0, 'glshots': 10, 'glga': 3})['saves'] == 7   # no saves in the report: shots - goals
    assert H.woc_line({'pos': 0})['svpct'] is None


def test_woc_summary_counts_each_game_for_its_own_role_only():
    shutout = {**GOALIE_LINE, 'glga': 0, 'glsaves': 20, 'glso': 1, 'glbrkshots': 2, 'glbrksaves': 1}
    s = H.woc_summary([{'stats': GOALIE_LINE, 'won': True}, {'stats': shutout, 'won': True},
                       {'stats': SKATER_LINE, 'won': False}])
    gl, sk = s['goalie'], s['skater']
    assert (gl['gp'], gl['w'], gl['l'], gl['shots'], gl['saves'], gl['ga'], gl['so'], gl['toi']) == (2, 2, 0, 40, 38, 2, 1, 7200)
    assert (gl['svpct'], gl['gaa'], gl['brk_shots'], gl['brk_saves'], gl['brk_svpct'], gl['pen_svpct']) == (0.95, 1.0, 2, 1, 0.5, None)
    assert (sk['gp'], sk['w'], sk['l'], sk['g'], sk['a'], sk['pts'], sk['plusmin'], sk['shots'], sk['hits']) == (
        1, 0, 1, 1, 2, 3, -1, 4, 3)
    one = H.woc_summary([{'stats': GOALIE_LINE, 'won': False}])
    assert one['skater'] is None and (one['goalie']['svpct'], one['goalie']['gaa'], one['goalie']['l']) == (0.9, 2.0, 1)
    assert H.woc_summary([{'stats': SKATER_LINE, 'won': True}])['goalie'] is None and H.woc_summary([]) is None
    # GAA only over the goalie games that say their time on ice
    untimed = {'pos': 0, 'glshots': 10, 'glga': 5}
    assert H.woc_summary([{'stats': GOALIE_LINE, 'won': True}, {'stats': untimed, 'won': False}])['goalie']['gaa'] == 2.0


def test_player_detail_gives_world_of_chel_lines_and_keeps_them_out_of_the_versus_totals():
    m1 = woc_match(1, ['g1', 's1'], ['s2'], {'g1': GOALIE_LINE, 's1': SKATER_LINE}, score=(3, 2))
    m2 = woc_match(2, ['s2'], ['g1'], {'g1': SKATER_LINE}, score=(4, 1))        # g1 skates this one and loses
    m3 = woc_match(3, ['g1'], ['s2'], {'g1': GOALIE_LINE}, mode='chel_gm3on3')
    d = H.player_detail([m3, m2, m1], 'g1')
    assert (d['woc']['goalie']['gp'], d['woc']['goalie']['w'], d['woc']['skater']['gp'], d['woc']['skater']['l']) == (2, 2, 1, 1)
    assert d['stats'] is None and d['shootout'] is None                       # no Versus totals from WoC lines
    assert [r['line']['role'] for r in d['recent']] == ['goalie', 'skater', 'goalie']
    assert all(r['box'] == [] for r in d['recent'])
    assert H.player_detail([m1], 's2')['woc'] is None and 'line' not in H.player_detail([m1], 's2')['recent'][0]
    assert len(H.woc_games([m3, m2, m1], 'g1')) == 3
    assert len(H.woc_games([m3, m2, m1], 'g1', ('chel_dropin',))) == 2
    assert H.woc_games([woc_match(4, ['g1'], ['s2'], {'g1': GOALIE_LINE}, mode=H.ONES)], 'g1') == []
    waiting = woc_match(5, ['g1'], ['s2'], {'g1': GOALIE_LINE})
    del waiting['claims']['s2']
    assert H.woc_games([waiting], 'g1') == []                                 # only confirmed games count
