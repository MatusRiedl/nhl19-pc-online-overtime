"""1.00.0 (owner 2026-11-26: "make in patch all toggles toggled, so people get the full thing"): every Patch switch on
once, for a new install and an older one (controller.full_migrate, Controller.full_once), the Roster update group and
its options too (not the starter profile); a switch turned off after that stays off. The question "Patch NHL 19
again?" waits for the first-look downloads, so one Patch puts them in (patch_ctl._waits,
SetupController.assets_pending)."""
import threading
import time
import types

from overtime_core import overlay
from overtime_roster.app import controller as C, patch_ctl, settings
from overtime_roster.app import setup_controller as SC

ALL = (*patch_ctl.KEYS, *patch_ctl.EXTRA_KEYS)


def test_full_migrate_turns_every_switch_on_and_each_can_be():
    want = C.full_migrate(dict.fromkeys(ALL, False))
    assert all(want[k] for k in ALL)
    assert not any(patch_ctl.why(want, k, (), missing_ok=True) for k in ALL)     # what each needs is on too
    assert C.full_migrate({'menus': True, 'extra': 'kept'})['extra'] == 'kept'


def _older_prefs():
    return {'packs_default': C.PACKS_DEFAULT, 'chel_default': C.CHEL_DEFAULT,
            'patch': {'names': True, 'roster': True, 'league': True, 'text': True, 'menus': True, 'chel': False,
                      'art': True, 'kits': False, 'photos': False},
            'patch_tab': {'update': False, 'starter': False},
            'update': {'season': 2027, 'lines': False, 'nhl27': True, 'calendar': True, 'retire': False,
                       'myedits': True}}


def test_an_older_install_gets_every_switch_on_once_and_keeps_what_it_turns_off_after(game_dir, tmp_path,
                                                                                      monkeypatch):
    from tests.test_editors_app import Host
    monkeypatch.setenv('OVERTIME_ROSTER_HOME', str(tmp_path / 'home'))
    assert settings.save(_older_prefs())
    host = Host()
    c = C.Controller(host, game_dir=game_dir, save_dir=str(tmp_path / 'saves'))
    assert c.full_once and all(c.patch_want[k] for k in ALL)
    assert c.prefs['full_default'] == C.FULL_DEFAULT and c.prefs['first_assets'] is True
    assert c.prefs['patch'] == c.patch_want
    assert c.parts['patchall'].update_on is True and c.prefs['patch_tab'] == {'update': True, 'starter': False}
    assert all(c.parts['update'].opts.values()) and c.prefs['update']['season'] == 2027
    line = next(m for m in host.lines if m.startswith('Patch switches: every one is on now'))
    assert 'chel' in line and 'kits' in line and 'alts_hometown' in line and 'names' not in line
    # the player turns some off afterwards: they stay off, nothing is turned on again
    c.remember(patch={**c.patch_want, 'alts_hometown': False}, patch_tab={'update': False, 'starter': False},
               update={**c.prefs['update'], 'retire': False})
    host2 = Host()
    again = C.Controller(host2, game_dir=game_dir, save_dir=str(tmp_path / 'saves'))
    assert not again.full_once and again.patch_want['alts_hometown'] is False
    assert again.parts['patchall'].update_on is False and again.parts['update'].opts['retire'] is False
    assert not any(m.startswith('Patch switches:') for m in host2.lines)


def test_the_starter_profile_is_not_turned_on(game_dir, tmp_path, monkeypatch):
    from tests.test_editors_app import Host
    monkeypatch.setenv('OVERTIME_ROSTER_HOME', str(tmp_path / 'home'))
    assert settings.save(_older_prefs())
    c = C.Controller(Host(), game_dir=game_dir, save_dir=str(tmp_path / 'saves'))
    assert c.parts['patchall'].starter_on is False      # never booted on a fresh save folder (starter-profile.md)


def _setup(**kw):
    s = types.SimpleNamespace(first_assets=True, packs=[], dl=None, known_emulator=lambda: 'shadPS4.exe',
                              _extras_wanted=lambda: [])
    s.__dict__.update(kw)
    return s


def test_assets_pending_only_while_a_pack_is_coming():
    pending = SC.SetupController.assets_pending
    rows = [{'name': 'kitlayers_clubs.zip', 'state': 'missing'}, {'name': 'rink.zip', 'state': 'offline'}]
    assert pending(_setup(packs=rows, _extras_wanted=lambda: ['kitlayers_clubs.zip'])) is True
    assert pending(_setup(packs=rows, _extras_wanted=lambda: ['rink.zip'])) is False          # offline: none coming
    assert pending(_setup(packs=rows, dl={'names': ['rink.zip']})) is True                    # a download runs
    assert pending(_setup(packs=rows, first_assets=False, _extras_wanted=lambda: ['kitlayers_clubs.zip'])) is False
    assert pending(_setup(packs=None, _extras_wanted=lambda: ['kitlayers_clubs.zip'])) is False  # list not read yet
    assert pending(_setup(packs=rows, known_emulator=lambda: '', _extras_wanted=lambda: ['kitlayers_clubs.zip'])) \
        is False


def test_the_patch_again_question_waits_for_the_downloads_and_asks_once(monkeypatch):
    """The packs come one after the other with a moment between them that is not busy: the question waits for the
    last one, then asks once."""
    from overtime_roster.app import matchsetup
    monkeypatch.setattr(matchsetup, 'active', lambda: False)
    monkeypatch.setattr(patch_ctl, 'REPATCH_POLL', 0.01)
    monkeypatch.setattr(overlay, 'emulator_running', lambda: False)
    old = {'applied': True, 'layers': {'database': {}}, 'outdated': ['database']}
    monkeypatch.setattr(overlay, 'status', lambda game_dir: old)
    asked, left = [], {'n': 2}

    class Shell:
        def question(self):
            return None

        def ask(self, title, lines, buttons, answers=None, tone=''):
            asked.append(title)

    ctl = types.SimpleNamespace(prefs={}, lock=threading.RLock(), busy=None, shell=Shell(), game_dir='G',
                                setup=types.SimpleNamespace(setup_patch=lambda: None,
                                                            assets_pending=lambda: left['n'] > 0),
                                host=types.SimpleNamespace(log=lambda m: None, send=lambda e, p=None: None))
    ctl.remember = lambda **kv: ctl.prefs.update(kv)
    assert patch_ctl.offer_repatch(ctl, old) is False and asked == []      # two packs to come: it waits
    time.sleep(0.05)
    left['n'] = 1                                                          # between packs, not busy: still waits
    time.sleep(0.05)
    assert asked == []
    left['n'] = 0
    end = time.monotonic() + 3
    while time.monotonic() < end and (not asked or ctl.repatch_waiting):
        time.sleep(0.01)
    assert asked == ['Patch NHL 19 again?'] and not ctl.repatch_waiting
    assert patch_ctl.offer_repatch(ctl, old) is False and len(asked) == 1  # once per version
