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


# --- the Overtime server's copies (owner 2026-11-22): downloaded the first time a choice needs one --------------------
def serve(root, files):
    """A release folder whose latest.json lists `files` ({name: bytes}) as packs; its URL."""
    import hashlib
    import pathlib
    (root / 'packs').mkdir(parents=True, exist_ok=True)
    packs, sums = {}, ''
    for name, data in files.items():
        (root / 'packs' / name).write_bytes(data)
        sha = hashlib.sha256(data).hexdigest()
        packs[name] = {'file': f'packs/{name}', 'sha256': sha, 'size': len(data)}
        sums += f'{sha}  packs/{name}\n'
    (root / 'latest.json').write_text(json.dumps({'version': '0.99.0', 'packs': packs}))
    (root / 'SHA256SUMS.txt').write_text(sums)
    return pathlib.Path(root / 'latest.json').as_uri()


def test_fetch_downloads_the_served_file_into_the_apps_folder(home):
    from overtime_roster.app import packdownload
    assert set(packdownload.PICTURE_PACKS) == {'nvngx_dlss.dll', 'nvngx_dlssnr.dll'}
    assert not set(packdownload.PICTURE_PACKS) & (set(packdownload.TOOL_PACKS) | set(packdownload.PACKS))
    url = serve(home / 'release', {'nvngx_dlssnr.dll': DLL})
    seen = []
    got = dlssfiles.fetch('dlss5', lambda name, done, total: seen.append((name, done, total)), url)
    assert got == dlssfiles.path('dlss5') == dlssfiles.here('dlss5') and open(got, 'rb').read() == DLL
    assert seen[-1] == ('nvngx_dlssnr.dll', len(DLL), len(DLL)) and dlssfiles.downloaded('dlss5')
    assert sorted(os.listdir(os.path.dirname(got))) == ['nvngx_dlssnr.dll', packdownload.RECORD]   # one copy
    dlssfiles.add('dlss5', dll(home / 'mine', 'nvngx_dlssnr.dll', DLL + b'own'))
    assert not dlssfiles.downloaded('dlss5')            # the player's own copy since
    with pytest.raises(dlssfiles.DlssFileError, match='does not offer nvngx_dlss.dll'):
        dlssfiles.fetch('dlss', release=url)            # taken off the server (or never put there)
    bad = serve(home / 'bad', {'nvngx_dlss.dll': b'PK' + DLL[2:]})
    with pytest.raises(dlssfiles.DlssFileError, match='not a DLSS file'):
        dlssfiles.fetch('dlss', release=bad)
    assert not dlssfiles.here('dlss') and not os.path.exists(dlssfiles.path('dlss') + '.part')


def test_a_download_keeps_the_players_own_file_beside_it(home):
    """The player's own nvngx_dlss.dll (not in the folder's record) stays when DLSS 5's file is downloaded into the
    same folder, and still counts as their own."""
    from overtime_roster.app import packdownload
    mine = DLL + b'mine'
    dlssfiles.add('dlss', dll(home / 'mine', 'nvngx_dlss.dll', mine))
    url = serve(home / 'release', {'nvngx_dlss.dll': DLL, 'nvngx_dlssnr.dll': DLL + b'5'})
    assert dlssfiles.fetch('dlss5', release=url) == dlssfiles.path('dlss5')
    assert open(dlssfiles.path('dlss'), 'rb').read() == mine and not dlssfiles.downloaded('dlss')
    assert dlssfiles.downloaded('dlss5')
    folder = os.path.dirname(dlssfiles.path('dlss'))
    assert sorted(os.listdir(folder)) == sorted(['nvngx_dlss.dll', 'nvngx_dlssnr.dll', packdownload.RECORD])


RTX30 = {'name': 'NVIDIA GeForce RTX 3080', 'rtx': 30, 'dlss': True, 'dlss5': True, 'dlss5_compat': True,
         'framegen': False}


def test_turning_dlss_on_downloads_the_servers_file_first(sc, monkeypatch, tmp_path):
    from overtime_roster.app import packdownload
    monkeypatch.setattr(sc, '_gpu', dict(RTX30))
    sc.setup_refresh()
    sc.setup_build(boost.NATIVE3)
    sc.boost_table = packdownload.published(serve(tmp_path / 'release', {'nvngx_dlss.dll': DLL,
                                                                         'nvngx_dlssnr.dll': DLL + b'5'}), max_age=0)
    pic = sc._boost_card(str(sc.world['emu']))['picture']
    assert pic['offered'] == {'dlss': True, 'dlss5': True} and pic['getting'] == '' and pic['progress'] is None
    assert sc.setup_upscaler('dlss') == {'ok': True, 'downloading': 'dlss'}
    assert dlssfiles.here('dlss') and config(sc)['upscaler'] == 'dlss' and sc.ctl.busy is None
    assert any(t.startswith('Downloading the DLSS file... ') for t, _tone in sc.ctl.said)
    assert sc.ctl.said[-1] == ('Upscaler: DLSS. NHL 19 uses it from its next start.', 'good')
    assert sc.setup_dlss5(True) == {'ok': True, 'downloading': 'dlss5'}
    gpu = config(sc)
    assert gpu['dlss_nr'] is True and gpu['dlss_nr_dll'] == dlssfiles.path('dlss5')
    pic = sc._boost_card(str(sc.world['emu']))['picture']
    assert pic['files'] == {'dlss': True, 'dlss5': True} and pic['notes'] == []    # the server's file: no compat note
    assert sc.setup_upscaler('dlss') == {'ok': True}           # here now: no second download


def test_a_file_the_server_does_not_offer_keeps_the_add_your_own_flow(sc, monkeypatch, tmp_path):
    from overtime_roster.app import packdownload
    monkeypatch.setattr(sc, '_gpu', dict(RTX30))
    sc.setup_refresh()
    sc.setup_build(boost.NATIVE3)
    url = serve(tmp_path / 'release', {'nvngx_dlss.dll': DLL})
    sc.boost_table = packdownload.published(url, max_age=0)
    assert 'error' in sc.setup_dlss5(True)                  # no DLSS 5 file served: add your own
    (tmp_path / 'release' / 'packs' / 'nvngx_dlss.dll').unlink()      # taken off after the last look
    assert sc.setup_upscaler('dlss') == {'ok': True, 'downloading': 'dlss'}
    assert config(sc)['upscaler'] == 'dlss' and not dlssfiles.here('dlss')     # the choice stays: FSR 1 until then
    text, tone = sc.ctl.said[-1]
    assert tone == 'caution' and text.startswith('DLSS file not downloaded: ')
    pic = sc._boost_card(str(sc.world['emu']))['picture']
    assert any('press Download beside it, or add your own' in n for n in pic['notes'])
    assert sc.setup_dlss_file_get('dlss5')['error'].startswith('The Overtime server does not offer nvngx_dlssnr.dll')
    (tmp_path / 'release' / 'packs' / 'nvngx_dlss.dll').write_bytes(DLL)     # back on the server: Download
    assert sc.setup_dlss_file_get('dlss') == {'ok': True, 'downloading': 'dlss'} and dlssfiles.here('dlss')
    assert sc.ctl.said[-1] == ('DLSS file downloaded. NHL 19 uses it from its next start.', 'good')
    assert sc.setup_dlss_file_remove('dlss') == {'ok': True}
    sc.boost_table = {}
    pic = sc._boost_card(str(sc.world['emu']))['picture']
    assert any('add your own, or the game uses FSR 1' in n for n in pic['notes'])
    sc.ctl.busy = 'Patching...'                             # a job runs (a download may write the same file)
    assert 'error' in sc.setup_dlss_file_set('dlss', dll(tmp_path / 'mine', 'nvngx_dlss.dll'))
    assert 'error' in sc.setup_dlss_file_remove('dlss') and not dlssfiles.here('dlss')


# --- DLSS quality (owner 2026-11-22): the render resolutions named by the DLSS mode ------------------------------------
def test_dlss_quality_names_each_resolution_that_fits_the_screen_by_its_mode():
    from overtime_roster.app import setup_controller as SC

    def modes(screen):
        return [(r['value'], r['label']) for r in SC.dlss_quality(screen)]
    assert modes(1080) == [(720, 'Quality'), (1080, 'DLAA')]
    assert modes(1440) == [(720, 'Performance'), (1080, 'Quality'), (1440, 'DLAA')]
    assert modes(2160) == [(720, 'Ultra Performance'), (1080, 'Performance'), (1440, 'Quality')]
    assert modes(1200) == [(720, 'Balanced'), (1080, 'Quality')]
    assert modes(1600) == [(720, 'Performance'), (1080, 'Quality 1080p'), (1440, 'Quality 1440p')]   # two Quality
    assert modes(None) == [(720, '720p'), (1080, '1080p'), (1440, '1440p')]      # no screen size: plain
    assert SC.dlss_quality(1440)[0]['title'].startswith('Renders at 1280x720')


def test_the_dlss_quality_row_shows_with_dlss_and_sets_the_resolution(sc, monkeypatch):
    from overtime_roster.app import gpuinfo
    monkeypatch.setattr(sc, '_gpu', dict(RTX30))
    monkeypatch.setattr(gpuinfo, 'screen_height', lambda: 1440)
    sc.setup_refresh()
    sc.setup_build(boost.NATIVE3)
    assert sc._boost_card(str(sc.world['emu']))['picture']['quality'] == []      # not with DLSS off
    sc.setup_upscaler('dlss')
    pic = sc._boost_card(str(sc.world['emu']))['picture']
    assert [r['label'] for r in pic['quality']] == ['Performance', 'Quality', 'DLAA'] and pic['screen'] == 1440
    assert pic['resolution'] == sc.resolution == 1080
    assert sc.setup_resolution(1440) == {'ok': True}
    assert sc._boost_card(str(sc.world['emu']))['picture']['resolution'] == 1440


def test_screen_height_is_a_number_on_windows_and_none_elsewhere(monkeypatch):
    import sys
    from overtime_roster.app import gpuinfo
    h = gpuinfo.screen_height()
    assert h is None or (isinstance(h, int) and h > 0)
    monkeypatch.setattr(sys, 'platform', 'linux')
    assert gpuinfo.screen_height() is None
