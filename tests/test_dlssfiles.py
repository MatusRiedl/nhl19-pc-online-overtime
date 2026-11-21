"""The player's own DLSS files (0.99.0, Overtime Native v3's Picture options): checked, kept in the app's folder, the
DLSS one beside the v3 build before a start (never beside the player's own shadPS4), the Boost card's Picture block."""
import json
import os
import zipfile

import pytest

from overtime_roster.app import boost, dlssfiles, emufile, emusettings, gamesetup

from test_setup_controller import sc, world  # noqa: F401  (fixtures)

DLL = b'MZ' + b'\0' * (dlssfiles.MIN_BYTES + 10)


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setenv('OVERTIME_ROSTER_HOME', str(tmp_path / 'apphome'))
    return tmp_path


def dll(folder, name, data=DLL):
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, name)
    with open(path, 'wb') as f:
        f.write(data)
    return path


def test_a_file_is_taken_only_by_its_name_header_and_size(home):
    src = home / 'game'
    assert 'nvngx_dlss.dll' in dlssfiles.check('dlss', dll(src, 'other.dll'))
    assert 'not a DLSS file' in dlssfiles.check('dlss', dll(src / 'a', 'nvngx_dlss.dll', b'PK' + DLL[2:]))
    assert 'not a DLSS file' in dlssfiles.check('dlss5', dll(src / 'b', 'nvngx_dlssnr.dll', b'MZ' + b'\0' * 100))
    assert 'does not read' in dlssfiles.check('dlss', str(src / 'gone' / 'nvngx_dlss.dll'))
    assert dlssfiles.check('dlss', dll(src / 'c', 'NVNGX_DLSS.DLL')) == ''
    with pytest.raises(dlssfiles.DlssFileError):
        dlssfiles.add('dlss5', dll(src, 'nvngx_dlss.dll'))
    assert dlssfiles.here('dlss5') == ''


def test_added_kept_beside_the_v3_build_and_removed(home):
    kept = dlssfiles.add('dlss', dll(home / 'game', 'nvngx_dlss.dll'))
    assert kept == dlssfiles.path('dlss') and dlssfiles.here('dlss') == kept
    assert open(kept, 'rb').read() == DLL and not os.path.exists(kept + '.part')
    v3 = boost.exe_path(boost.NATIVE3)
    os.makedirs(os.path.dirname(v3), exist_ok=True)
    open(v3, 'wb').write(b'MZ v3')
    own = dll(home / 'PS4 Emulator', 'shadPS4.exe', b'MZ own')
    dlssfiles.ready_for(own)        # the player's own shadPS4's folder is never written to
    assert not os.path.exists(os.path.join(os.path.dirname(own), 'nvngx_dlss.dll'))
    dlssfiles.ready_for(v3)
    beside = os.path.join(os.path.dirname(v3), 'nvngx_dlss.dll')
    assert open(beside, 'rb').read() == DLL
    dlssfiles.remove('dlss', (v3,))
    assert not dlssfiles.here('dlss') and not os.path.exists(beside)
    open(beside, 'wb').write(DLL)       # an old copy beside it goes at the next start once the kept one is gone
    dlssfiles.ready_for(v3)
    assert not os.path.exists(beside)


def test_a_windows_pack_carries_the_dlss5_forwarder_beside_the_program(home):
    pack = home / 'shadps4_native3.zip'
    with zipfile.ZipFile(pack, 'w') as z:
        z.writestr('build/shadPS4.exe', b'MZ v3')
        z.writestr('build/nvngx.dll_dlssnr.dll', b'MZ forwarder')
        z.writestr('build/README.txt', b'not taken')
        z.writestr('build/sub/nvngx.dll_dlssnr.dll', b'not taken either')
    target = home / 'out' / 'shadPS4.exe'
    os.makedirs(target.parent)
    emufile.unpack(str(pack), str(target), system='win32')
    assert sorted(os.listdir(target.parent)) == ['nvngx.dll_dlssnr.dll', 'shadPS4.exe']
    assert (target.parent / 'nvngx.dll_dlssnr.dll').read_bytes() == b'MZ forwarder'


def config(sc):
    user = gamesetup.emu_user_dir(str(sc.world['emu']))
    with open(gamesetup.custom_config_path(user), encoding='utf-8') as f:
        return json.load(f)['GPU']


def test_the_picture_block_on_the_boost_card(sc, monkeypatch, tmp_path):
    monkeypatch.setattr(sc, '_gpu', {'name': 'NVIDIA GeForce RTX 3080', 'rtx': 30, 'dlss': True, 'dlss5': True,
                                     'dlss5_compat': True, 'framegen': False})
    sc.setup_refresh()
    sc.setup_build(boost.NATIVE3)
    card = sc._boost_card(str(sc.world['emu']))
    pic = card['picture']
    assert pic['upscaler'] == 'off' and not pic['dlss5'] and pic['files'] == {'dlss': False, 'dlss5': False}
    assert pic['can_dlss'] and pic['dlss5_compat'] and pic['notes'] == []
    assert sc.setup_upscaler('dlss') == {'ok': True}
    gpu = config(sc)
    assert gpu['upscaler'] == 'dlss' and gpu['fsr_enabled'] is False
    pic = sc._boost_card(str(sc.world['emu']))['picture']
    assert pic['upscaler'] == 'dlss' and any('nvngx_dlss.dll' in n for n in pic['notes'])
    assert 'error' in sc.setup_dlss5(True)      # no DLSS 5 file yet
    assert sc.setup_dlss_file_set('dlss5', dll(tmp_path / 'mine', 'nvngx_dlssnr.dll')) == {'ok': True}
    assert sc.setup_dlss5(True) == {'ok': True}
    gpu = config(sc)
    assert gpu['dlss_nr'] is True and gpu['dlss_nr_dll'] == dlssfiles.path('dlss5')
    pic = sc._boost_card(str(sc.world['emu']))['picture']
    assert pic['dlss5'] and any('compat' in n for n in pic['notes'])
    assert sc.setup_dlss_file_remove('dlss5') == {'ok': True}
    gpu = config(sc)
    assert gpu['dlss_nr'] is False and gpu['dlss_nr_dll'] == '' and not dlssfiles.here('dlss5')
    assert sc.setup_upscaler('fsr1') == {'ok': True} and config(sc)['fsr_enabled'] is True
    assert 'error' in sc.setup_upscaler('xess')
    sc.setup_build(boost.NATIVE2)       # v2 has no Picture options: no block
    assert sc._boost_card(str(sc.world['emu']))['picture'] is None
    assert emusettings.value(gamesetup.emu_user_dir(str(sc.world['emu'])), 'GPU.upscaler') == 'fsr1'


def test_a_player_on_v2_moves_to_v3_once(sc, monkeypatch):
    from test_setup_controller import FakeCtl
    from overtime_roster.app import setup_controller as SC
    ctl = FakeCtl(str(sc.world['game']))
    ctl.prefs['setup'] = {'build': boost.NATIVE2, 'rebuild': SC.REBUILD, SC.V2_MOVE: True}
    moved = SC.SetupController(ctl)
    assert moved.build == (boost.NATIVE3 if boost.DEFAULT == boost.NATIVE3 else boost.NATIVE2)
    ctl.prefs['setup'] = {'build': boost.NATIVE2, 'rebuild': SC.REBUILD, SC.V2_MOVE: True, SC.V3_MOVE: True}
    assert SC.SetupController(ctl).build == boost.NATIVE2      # chosen again after the move: it stays
