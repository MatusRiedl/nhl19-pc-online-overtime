"""update.gather's stops say why: a season NHL.com has no games for yet, NHL.com down with its reason (a tester's
2027-28, 2026-11-21: every stop read "NHL.com did not answer")."""
import ssl
import urllib.error

import pytest

from overtime_core import calendar, nhlcom, ratings as R, rosterupdate as U
from overtime_roster.app import calendar_ctl, update


@pytest.fixture
def no_pack(monkeypatch):
    """No NHL 27 pack, no data pack; rosters past gather_rosters pass through as they are."""
    monkeypatch.setattr(update.sources, 'nhl27_pack', lambda d: (None, ''))

    def load_pack(*a, **kw):
        raise R.PackError('no data pack (no connection and no cached copy)')
    monkeypatch.setattr(R, 'load_pack', load_pack)
    monkeypatch.setattr(U, 'with_absent', lambda real, *a: (real, [], {}))
    for name in ('listed', 'farm_clubs', 'merged'):
        monkeypatch.setattr(update.clubdata, name, lambda *a: {})


def down(reason):
    def fetch(url, timeout=20):
        raise urllib.error.URLError(reason)
    return nhlcom.Client(fetch=fetch, min_interval=0)


def test_a_season_without_games_yet_says_so(no_pack, monkeypatch, tmp_path):
    monkeypatch.setattr(U, 'gather_rosters', lambda client, season, log=None: [{'team': 'ANA'}])
    monkeypatch.setattr(calendar, 'season_games', lambda client, season, log=None: [])
    with pytest.raises(update.NoGames) as err:
        update.gather(nhlcom.Client(min_interval=0), 2027, str(tmp_path))
    text = str(err.value)
    assert text.startswith('No 2027-28 calendar yet: NHL.com lists no games for it') and 'Pick 2026-27' in text
    assert 'did not answer' not in text and not err.value.offline_helps


def test_nhl_com_down_gives_its_reason(no_pack, tmp_path):
    with pytest.raises(update.UpdateError) as err:
        update.gather(down(TimeoutError('timed out')), 2026, str(tmp_path))
    assert str(err.value).startswith('No rosters: NHL.com did not answer (no answer in time) and there is no data pack.')
    assert err.value.offline_helps


def test_a_certificate_failure_is_named():
    err = nhlcom.NhlComError('NHL.com: /standings/now: ...')
    err.__cause__ = urllib.error.URLError(ssl.SSLCertVerificationError('CERTIFICATE_VERIFY_FAILED'))
    assert update.why(err) == 'this PC could not check its certificate'


def test_calendar_tab_says_a_season_is_not_out_yet(monkeypatch, tmp_path):
    monkeypatch.setattr(calendar, 'season_games', lambda client, season, log=None: [])
    monkeypatch.setattr(calendar_ctl.paths, 'app_dir', lambda *a: str(tmp_path))
    monkeypatch.setattr(R, 'load_pack', lambda *a, **kw: None)
    with pytest.raises(calendar_ctl.SyncError, match='No 2027-28 calendar yet'):
        calendar_ctl.real_season(2027)
