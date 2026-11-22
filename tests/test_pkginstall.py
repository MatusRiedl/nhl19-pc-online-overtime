"""pkginstall: NHL 19 from its PKG files with shadPS4Plus's pkg_extractor, here a fake one (no real PKG in the tests)."""
import hashlib
import io
import os
import pathlib
import zipfile
from collections import namedtuple

import pytest

from overtime_core import sfo
from overtime_roster.app import pkginstall

Usage = namedtuple('Usage', 'total used free')


def _sfo(title_id='CUSA11126', app_ver='01.60'):
    return sfo.build([sfo.Entry('APP_VER', sfo.FMT_UTF8, app_ver, 8), sfo.Entry('TITLE_ID', sfo.FMT_UTF8, title_id, 12)])


def _pkg(path, title='CUSA11126', size=4096):
    content = f'UP0006-{title}_00-NHL19GAME0000000'.encode().ljust(36, b'0')[:36]
    path.write_bytes(pkginstall.MAGIC + b'\0' * 0x3c + content + b'\0' * (size - 0x64))
    return path


def _game_files(folder, app_ver):
    (folder / 'sce_sys').mkdir(parents=True)
    (folder / 'sce_sys' / 'param.sfo').write_bytes(_sfo(app_ver=app_ver))
    (folder / 'eboot.bin').write_bytes(b'\x7fELF fake eboot')
    if app_ver == '01.00':
        (folder / 'databigs').mkdir()
        (folder / 'databigs' / 'inxp_10.big').write_bytes(b'x' * 100)


def _full_pkg(path, title='CUSA11126', category='gp', app_ver='01.60'):
    """A PKG with an entry table and its param.sfo (entry 0x1000), laid out as the real NHL 19 ones are; no game data."""
    content = f'UP0006-{title}_00-NHLICEHOCKEY2019'.encode().ljust(36, b'\0')[:36]
    data = sfo.build([sfo.Entry('APP_VER', sfo.FMT_UTF8, app_ver, 8), sfo.Entry('CATEGORY', sfo.FMT_UTF8, category, 4),
                      sfo.Entry('TITLE_ID', sfo.FMT_UTF8, title, 12)])
    head = bytearray(0x200)
    head[:4] = pkginstall.MAGIC
    head[0x10:0x14] = (2).to_bytes(4, 'big')            # two entries
    head[0x18:0x1c] = (0x100).to_bytes(4, 'big')        # the table at 0x100
    head[0x40:0x64] = content
    entries = [(0x0001, 0x400, 4), (pkginstall.SFO_ENTRY, 0x200, len(data))]
    for i, (entry, offset, size) in enumerate(entries):
        at = 0x100 + i * 32
        for n, value in enumerate((entry, 0, 0, 0, offset, size)):
            head[at + n * 4:at + n * 4 + 4] = value.to_bytes(4, 'big')
    path.write_bytes(bytes(head) + data.ljust(0x200, b'\0') + b'body')
    return path


def _kind_from_sfo(pkg):
    """What the real tool says, from the synthetic PKG's CATEGORY: gp an update, anything else the game."""
    try:
        return pkginstall.UPDATE if pkginstall.sfo_of(pkg).get('CATEGORY') == 'gp' else pkginstall.BASE
    except pkginstall.PkgError:
        return pkginstall.BASE


class FakeTool:
    """popen for pkg_extractor: --check-type exits `kind` (a number, or kind(pkg) per file); an extract writes what a
    real one writes (or nothing)."""

    def __init__(self, kind=pkginstall.BASE, writes=True):
        self.kind, self.writes, self.calls = kind, writes, []

    def kind_of(self, pkg):
        return self.kind(pkg) if callable(self.kind) else self.kind

    def __call__(self, args, **kw):
        self.calls.append(args)
        tool = self

        class Proc:
            returncode = None

            def __init__(self):
                kind = tool.kind_of(args[1])
                if args[-1] == '--check-type':
                    self.returncode, self.stdout = kind, io.StringIO('pkg is a base game\n')
                    return
                title = pkginstall.title_of(args[1])
                if tool.writes:
                    out = os.path.join(args[2], title + ('-patch' if kind == pkginstall.UPDATE else ''))
                    _game_files(pathlib.Path(out), '01.60' if kind == pkginstall.UPDATE else '01.00')
                    self.stdout = io.StringIO(f'Extracting file 1 of 1 to {out}\n\nTHE END {args[1]}\n')
                else:
                    self.stdout = io.StringIO('Cannot extract PKG file : Failed to decrypt\n\nTHE END x\n')
                self.returncode = 0

            def communicate(self):
                return self.stdout.read(), None

            def wait(self):
                return self.returncode
        return Proc()


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setenv('OVERTIME_ROSTER_HOME', str(tmp_path / 'apphome'))
    monkeypatch.setattr(pkginstall.overlay, 'launcher_running', lambda: False)
    monkeypatch.setattr(pkginstall, 'ensure_tool', lambda progress=None, opener=None: str(tmp_path / 'pkg_extractor.exe'))
    return tmp_path


def _install(pkg, game_dir=None, tool=None):
    return pkginstall.install(str(pkg), game_dir and str(game_dir), running=lambda: False, popen=tool or FakeTool())


def test_title_comes_from_the_pkg_header(tmp_path):
    assert pkginstall.title_of(str(_pkg(tmp_path / 'a.pkg'))) == 'CUSA11126'
    (tmp_path / 'b.pkg').write_bytes(b'not a pkg' * 20)
    with pytest.raises(pkginstall.PkgError, match='not a PS4 PKG'):
        pkginstall.title_of(str(tmp_path / 'b.pkg'))


def test_base_goes_into_a_new_folder_beside_the_pkg(home):
    (home / 'dl').mkdir()
    pkg = _pkg(home / 'dl' / 'game.pkg')
    use, kind, game = _install(pkg)
    assert use == str(home / 'dl' / 'CUSA11126') and kind == pkginstall.BASE
    assert game['title_id'] == 'CUSA11126' and game['app_ver'] == '01.00' and not game['ok']
    assert sorted(os.listdir(home / 'dl')) == ['CUSA11126', 'game.pkg']      # the scratch folder is gone
    # a folder of that name already there is never written into
    use2, _kind, _game = _install(pkg)
    assert use2 == str(home / 'dl' / 'CUSA11126-2')


def test_update_goes_beside_the_game_as_shadps4_mounts_it(home):
    games = home / 'games'
    _game_files(games / 'NHL 19', '01.00')
    (games / 'NHL 19-patch').mkdir()                    # an older update folder: kept, not deleted
    (games / 'NHL 19-patch' / 'old.txt').write_text('keep')
    pkg = _pkg(home / 'update.pkg')
    use, kind, game = _install(pkg, games / 'NHL 19', FakeTool(pkginstall.UPDATE))
    assert use == str(games / 'NHL 19') and kind == pkginstall.UPDATE
    assert game['ok'] and game['app_ver'] == '01.60' and game['update'] == str(games / 'NHL 19-patch')
    assert (games / 'NHL 19-patch.old' / 'old.txt').read_text() == 'keep'
    assert sorted(os.listdir(games)) == ['NHL 19', 'NHL 19-patch', 'NHL 19-patch.old']


def test_update_needs_the_game_first(home):
    with pytest.raises(pkginstall.PkgError, match='game PKG first'):
        _install(_pkg(home / 'update.pkg'), None, FakeTool(pkginstall.UPDATE))


def test_update_refused_where_an_update_folder_shadps4_prefers_is(home):
    _game_files(home / 'CUSA11126', '01.00')
    (home / 'CUSA11126-UPDATE').mkdir()
    with pytest.raises(pkginstall.PkgError, match='-UPDATE'):
        _install(_pkg(home / 'u.pkg'), home / 'CUSA11126', FakeTool(pkginstall.UPDATE))


def test_refusals_before_anything_is_written(home):
    with pytest.raises(pkginstall.PkgError, match='CUSA00001, not NHL 19'):
        _install(_pkg(home / 'other.pkg', title='CUSA00001'))
    with pytest.raises(pkginstall.PkgError, match='DLC'):
        _install(_pkg(home / 'dlc.pkg'), None, FakeTool(pkginstall.DLC))
    with pytest.raises(pkginstall.PkgError, match='cannot read'):
        _install(_pkg(home / 'bad.pkg'), None, FakeTool(0))
    with pytest.raises(Exception, match='running'):
        pkginstall.install(str(_pkg(home / 'g.pkg')), running=lambda: True, popen=FakeTool())
    assert not [n for n in os.listdir(home) if n.startswith(pkginstall.SCRATCH) or n == 'CUSA11126']


def test_no_room_says_how_much(home, monkeypatch):
    monkeypatch.setattr(pkginstall.shutil, 'disk_usage', lambda p: Usage(10**12, 10**12, 1000))
    with pytest.raises(pkginstall.PkgError, match='free, the game needs about'):
        _install(_pkg(home / 'g.pkg'))


def test_a_failed_extract_leaves_nothing_and_says_the_tools_reason(home):
    with pytest.raises(pkginstall.PkgError, match='Failed to decrypt'):
        _install(_pkg(home / 'g.pkg'), None, FakeTool(writes=False))
    assert sorted(os.listdir(home)) == ['g.pkg']


# --- the update installs by itself after the game PKG (owner 2026-11-21) ---------------------------------------------
def test_param_sfo_comes_from_the_pkgs_entry_table(tmp_path):
    values = pkginstall.sfo_of(str(_full_pkg(tmp_path / 'u.pkg')))
    assert (values['TITLE_ID'], values['APP_VER'], values['CATEGORY']) == ('CUSA11126', '01.60', 'gp')
    (tmp_path / 'junk.pkg').write_bytes(b'not a pkg' * 20)
    (tmp_path / 'ps3.pkg').write_bytes(b'\x7fPKG' + b'\0' * 200)
    whole = (tmp_path / 'u.pkg').read_bytes()
    (tmp_path / 'cut.pkg').write_bytes(whole[:0x220])                   # the sfo cut short
    (tmp_path / 'nosfo.pkg').write_bytes(_pkg(tmp_path / 'h.pkg').read_bytes())     # a header with no table
    for name in ('junk.pkg', 'ps3.pkg', 'cut.pkg', 'nosfo.pkg'):
        with pytest.raises(pkginstall.PkgError):
            pkginstall.sfo_of(str(tmp_path / name))


def test_find_update_takes_the_one_overtime_needs_beside_the_game_pkg(tmp_path):
    dl = tmp_path / 'dl'
    dl.mkdir()
    game = _full_pkg(dl / 'NHL.19.PS4.pkg', category='gd', app_ver='01.00')
    _full_pkg(dl / 'a-old.pkg', app_ver='01.05')                         # an older update: named, not used
    _full_pkg(dl / 'b-other.pkg', title='CUSA00001')                     # another game's update
    _full_pkg(dl / 'c-us.pkg', title='CUSA11116')                        # the other region's update
    (dl / 'd-junk.pkg').write_bytes(b'junk')
    (dl / 'e-folder.pkg').mkdir()
    _full_pkg(dl / 'NHL.19.Update.v1.60.PS4.PKG')                        # upper-case extension too
    _full_pkg(tmp_path / 'elsewhere.pkg')                                # another folder: not looked at
    found, others = pkginstall.find_update(str(game), 'CUSA11126')
    assert found == str(dl / 'NHL.19.Update.v1.60.PS4.PKG') and others == [('a-old.pkg', '01.05')]
    assert pkginstall.find_update(str(game), 'CUSA11116')[0] == str(dl / 'c-us.pkg')
    assert pkginstall.find_update(str(tmp_path / 'elsewhere.pkg'), 'CUSA11126') == (None, [])


def test_the_game_pkg_brings_its_update_from_the_same_folder(home, monkeypatch):
    dl = home / 'dl'
    dl.mkdir()
    game_pkg = _full_pkg(dl / 'NHL.19.PS4.pkg', category='gd', app_ver='01.00')
    _full_pkg(dl / 'NHL.19.Update.v1.60.PS4.pkg')
    tool, stages = FakeTool(_kind_from_sfo), []
    use, kind, game = _install(game_pkg, None, tool)
    assert kind == pkginstall.BASE and not game['ok']
    real = pkginstall.extract

    def extract(exe, pkg, scratch, progress=None, popen=None):     # one progress call (the watcher's poll is 1 s)
        if progress:
            progress(1, 2)
        return real(exe, pkg, scratch, None, popen)
    monkeypatch.setattr(pkginstall, 'extract', extract)
    use2, game2, auto = pkginstall.add_update(str(game_pkg), use, game, lambda s, d, t: stages.append(s),
                                              running=lambda: False, popen=tool)
    assert use2 == use == str(dl / 'CUSA11126') and game2['ok'] and game2['app_ver'] == '01.60'
    assert auto == {'file': 'NHL.19.Update.v1.60.PS4.pkg', 'others': [], 'installed': True, 'error': None}
    assert sorted(os.listdir(dl)) == ['CUSA11126', 'CUSA11126-patch', 'NHL.19.PS4.pkg', 'NHL.19.Update.v1.60.PS4.pkg']
    assert stages == ['update']
    assert [c[1] for c in tool.calls if c[-1] == '--check-type'] == [str(game_pkg), str(dl / 'NHL.19.Update.v1.60.PS4.pkg')]


def test_no_update_or_another_version_installs_nothing_more(home):
    dl = home / 'dl'
    dl.mkdir()
    game_pkg = _full_pkg(dl / 'game.pkg', category='gd', app_ver='01.00')
    tool = FakeTool(_kind_from_sfo)
    use, _kind, game = _install(game_pkg, None, tool)
    assert pkginstall.add_update(str(game_pkg), use, game, popen=tool)[2] == \
        {'file': None, 'others': [], 'installed': False, 'error': None}
    _full_pkg(dl / 'update-105.pkg', app_ver='01.05')
    calls = len(tool.calls)
    use2, game2, auto = pkginstall.add_update(str(game_pkg), use, game, popen=tool)
    assert use2 == use and game2 is game and auto['file'] is None and auto['others'] == [('update-105.pkg', '01.05')]
    assert len(tool.calls) == calls and sorted(os.listdir(dl)) == ['CUSA11126', 'game.pkg', 'update-105.pkg']


def test_a_failed_update_keeps_the_game(home):
    """The tool reads the file beside the game as a game, not an update: refused before anything is extracted (no
    second game folder), and the game stays as installed."""
    dl = home / 'dl'
    dl.mkdir()
    game_pkg = _full_pkg(dl / 'game.pkg', category='gd', app_ver='01.00')
    _full_pkg(dl / 'update.pkg')
    tool = FakeTool(pkginstall.BASE)
    use, _kind, game = _install(game_pkg, None, tool)
    use2, game2, auto = pkginstall.add_update(str(game_pkg), use, game, running=lambda: False, popen=tool)
    assert use2 == use and game2 is game and not auto['installed'] and auto['file'] == 'update.pkg'
    assert 'reads update.pkg as the game, not as an update' in auto['error']
    assert sorted(os.listdir(dl)) == ['CUSA11126', 'game.pkg', 'update.pkg']
    # a refusal from install() itself (here: an -UPDATE folder shadPS4 prefers) is said too
    (dl / 'CUSA11126-UPDATE').mkdir()
    auto = pkginstall.add_update(str(game_pkg), use, game, running=lambda: False, popen=FakeTool(_kind_from_sfo))[2]
    assert '-UPDATE' in auto['error'] and not auto['installed']


@pytest.mark.windows_only
def test_the_tool_is_downloaded_once_and_checked(tmp_path, monkeypatch):
    monkeypatch.setenv('OVERTIME_ROSTER_HOME', str(tmp_path / 'apphome'))
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as z:
        for name in ('pkg_extractor.exe', 'libc++.dll', 'zlib1.dll', 'readme_windows.txt'):
            z.writestr(name, b'MZ ' + name.encode())
    data = buf.getvalue()
    monkeypatch.setattr(pkginstall, 'TOOL_SHA256', hashlib.sha256(data).hexdigest())
    monkeypatch.setattr(pkginstall, 'TOOL_SIZE', len(data))
    opened = []

    def opener(url):
        opened.append(url)
        return io.BytesIO(data)
    exe = pkginstall.ensure_tool(opener=opener)
    folder = os.path.dirname(exe)
    assert exe.endswith('pkg_extractor.exe') and os.path.isfile(os.path.join(folder, 'zlib1.dll'))
    assert pkginstall.ensure_tool(opener=opener) == exe and len(opened) == 1      # not again
    assert opened == [pkginstall.TOOL_URL] and not os.path.exists(os.path.join(folder, 'tool.zip.part'))


def test_another_tool_file_is_not_used(tmp_path, monkeypatch):
    monkeypatch.setenv('OVERTIME_ROSTER_HOME', str(tmp_path / 'apphome'))
    monkeypatch.setattr(pkginstall, 'TOOL_URL', 'https://example.test/pkg_extractor')   # macOS has no tool in the release
    monkeypatch.setattr(pkginstall, 'TOOL_SIZE', 10)
    with pytest.raises(pkginstall.PkgError, match='not the one Overtime knows'):
        pkginstall.ensure_tool(opener=lambda url: io.BytesIO(b'0123456789'))
    assert not os.path.exists(pkginstall.tool_exe())


def test_the_tool_per_system():
    """Windows: the zip pinned since 0.90. Linux: the same release's AppImage. macOS: the release has none."""
    win, linux = pkginstall.tool_for('win32'), pkginstall.tool_for('linux')
    assert win[0].endswith('-windows.zip') and win[1].startswith('a6a6dee8') and win[2:] == (1026861, 'pkg_extractor.exe')
    assert linux[0].endswith('-linux.AppImage') and len(linux[1]) == 64 and linux[3] == 'pkg_extractor.AppImage'
    assert pkginstall.tool_for('darwin') is None and pkginstall.tool_for('freebsd14') == linux


def test_on_linux_the_tool_is_one_program_file(tmp_path, monkeypatch):
    monkeypatch.setenv('OVERTIME_ROSTER_HOME', str(tmp_path / 'apphome'))
    data = bytes([0x7F]) + b'ELF the AppImage'
    url, _sha, _size, name = pkginstall.tool_for('linux')
    monkeypatch.setattr(pkginstall, 'TOOL_URL', url)
    monkeypatch.setattr(pkginstall, 'TOOL_EXE', name)
    monkeypatch.setattr(pkginstall, 'TOOL_SHA256', hashlib.sha256(data).hexdigest())
    monkeypatch.setattr(pkginstall, 'TOOL_SIZE', len(data))
    opened = []

    def opener(u):
        opened.append(u)
        return io.BytesIO(data)
    exe = pkginstall.ensure_tool(opener=opener)
    with open(exe, 'rb') as f:
        assert f.read() == data and exe.endswith('pkg_extractor.AppImage')
    assert sorted(os.listdir(os.path.dirname(exe))) == ['pkg_extractor.AppImage', 'sha256.txt']
    assert pkginstall.ensure_tool(opener=opener) == exe and opened == [url]
    env = pkginstall._environment(exe)
    assert env['APPIMAGE_EXTRACT_AND_RUN'] == '1' and 'APPIMAGE_EXTRACT_AND_RUN' not in pkginstall._environment('x.exe')


def test_macos_refuses_a_pkg_in_words(monkeypatch):
    monkeypatch.setattr(pkginstall, 'TOOL_URL', None)
    with pytest.raises(pkginstall.PkgError, match='cannot unpack a PKG on this system yet'):
        pkginstall.ensure_tool(opener=lambda url: io.BytesIO(b''))
