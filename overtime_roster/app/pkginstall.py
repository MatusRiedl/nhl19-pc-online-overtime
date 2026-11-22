"""NHL 19 from its PKG files, for a player with no extracted game (Setup, Find game picks a .pkg; owner 2026-11-10:
"they point to a game iso and the app will do the rest"). docs/notes/pkg-extractors.md.

The tool is shadPS4Plus's pkg_extractor 1.1 (GPL-2.0), downloaded from its GitHub release and checked by sha256, never
re-hosted by Overtime, and run as a program of its own. The base game goes into a new folder next to the PKG
(`<pkg folder>\\CUSA11126`); the update goes into a new folder beside the game, named after it (`<game>-patch`), the
layout shadPS4 mounts over the base and Overtime reads (gamefiles.roots). Nothing in an existing folder is changed:
each PKG is extracted into a fresh scratch folder on the target drive, then moved to its place in one rename.
Standard library only.

Linux (0.97.0): the same release's AppImage, run with APPIMAGE_EXTRACT_AND_RUN (no FUSE needed). macOS: that release
has no build for it, so a PKG is refused there in words until Overtime builds the tool from its source
(docs/notes/macos-support.md); an extracted game folder works as everywhere.

The update installs by itself (owner 2026-11-21): after the game PKG, add_update looks in the same folder for the update
Overtime needs (find_update reads each PKG's own param.sfo, no tool) and installs it with install()'s checks.
docs/notes/pkg-auto-update.md.
"""
import hashlib
import http.client
import os
import re
import shutil
import struct
import subprocess
import sys
import threading
import time
import urllib.error
import zipfile

from overtime_core import gamefiles, overlay, sfo

from . import gamesetup, packdownload, paths, selfupdate

_RELEASE = 'https://github.com/AzaharPlus/shadPS4Plus/releases/download/PKG_EXTRACTOR_1_1/'
# the release's file per system: (file, sha256, size, the program's name in the app's folder). sha256 and size are
# GitHub's own for each asset (its API's "digest", read 2026-11-18; the Windows one is the value pinned since 0.90)
TOOLS = {
    'win32': ('ShadPs4Plus-PkgExtractor-1.1-windows.zip',
              'a6a6dee84c1283949245c868e580ff8d0049d0e73df9de3096460ee26c6f04d7', 1026861, 'pkg_extractor.exe'),
    'linux': ('ShadPs4Plus-PkgExtractor-1.1-linux.AppImage',
              'b360bc691aa3d89071aa707224155f6eade348d314cf7798ac550e31c11a7bcc', 2415096, 'pkg_extractor.AppImage'),
}
NO_TOOL = ('Overtime cannot unpack a PKG on this system yet. Extract the game on a Windows or Linux PC (or with '
           "shadPS4Plus's PKG extractor), copy the folder here, then pick that folder.")


def tool_for(system=None):
    """(download URL, sha256, size, program name) of the PKG tool for this system, or None (macOS: no build)."""
    system = system or sys.platform
    found = TOOLS.get(system if system in ('win32', 'darwin') else 'linux')
    return (_RELEASE + found[0], *found[1:]) if found else None


TOOL_URL, TOOL_SHA256, TOOL_SIZE, TOOL_EXE = tool_for() or (None, None, 0, 'pkg_extractor')
SOURCE = 'https://github.com/AzaharPlus/shadPS4Plus/tree/PKG_EXTRACTOR_1_1/extractor'     # GPL-2.0, its source
BASE, UPDATE, DLC = 101, 102, 103      # pkg_extractor --check-type's exit codes; 0 = not a PKG it reads
_WHAT = {BASE: 'the game', UPDATE: 'an update', DLC: 'DLC'}
MAGIC = b'\x7fCNT'                     # a PS4 PKG's first four bytes; the content id is at 0x40 (36 bytes)
SPARE = 1.05                           # free space wanted: the PKG's size and 5 %
SCRATCH = '.overtime-pkg-'
KINDS = 'NHL 19 PKG (*.pkg)'
_FILE_LINE = re.compile(r'Extracting file (\d+) of (\d+)')
# a PKG's entry table (big-endian): the count at 0x10, the table's offset at 0x18, 32 bytes per entry (id, name offset,
# flags 1, flags 2, offset, size, 8 spare). sce_sys/param.sfo is entry 0x1000 and is not encrypted (read 2026-11-21 from
# NHL 19's game and 1.60 update PKGs: CATEGORY gd / APP_VER 01.00, and gp / 01.60)
SFO_ENTRY = 0x1000
PATCH = 'gp'                           # param.sfo CATEGORY of an update; the game itself is 'gd'
_MAX_ENTRIES, _MAX_SFO = 4096, 1 << 16


class PkgError(RuntimeError):
    pass


def title_of(pkg):
    """The title id in a PKG's header (CUSA11126 from UP0006-CUSA11126_00-...), or PkgError."""
    try:
        with open(pkg, 'rb') as f:
            head = f.read(0x64)
    except OSError as err:
        raise PkgError(f'The PKG does not open: {err.strerror or err}') from err
    if len(head) < 0x64 or head[:4] != MAGIC:
        raise PkgError(f'{os.path.basename(pkg)} is not a PS4 PKG.')
    content = head[0x40:0x64].split(b'\0', 1)[0].decode('ascii', 'replace')
    m = re.fullmatch(r'[A-Z]{2}\d{4}-([A-Z]{4}\d{5})_\d\d-.*', content)
    if not m:
        raise PkgError(f'{os.path.basename(pkg)} names no game ({content or "no content id"}).')
    return m.group(1)


def sfo_of(pkg):
    """The param.sfo values a PKG carries ({'TITLE_ID', 'APP_VER', 'CATEGORY', ...}), read from its entry table without
    the tool; PkgError when there is none Overtime reads (not a PS4 PKG, cut short, the entry encrypted)."""
    name = os.path.basename(pkg)
    try:
        with open(pkg, 'rb') as f:
            head = f.read(0x20)
            if len(head) < 0x20 or head[:4] != MAGIC:
                raise PkgError(f'{name} is not a PS4 PKG.')
            count, table = struct.unpack_from('>I', head, 0x10)[0], struct.unpack_from('>I', head, 0x18)[0]
            if not 0 < count <= _MAX_ENTRIES:
                raise PkgError(f'{name} has no entry table Overtime reads.')
            whole = os.fstat(f.fileno()).st_size
            f.seek(table)
            raw = f.read(count * 32)
            if len(raw) < count * 32:
                raise PkgError(f'{name} is cut short.')
            for i in range(count):
                entry, _name, _flags1, _flags2, offset, size = struct.unpack_from('>6I', raw, i * 32)
                if entry != SFO_ENTRY:
                    continue
                if not 0 < size <= _MAX_SFO or offset + size > whole:
                    raise PkgError(f'{name} is cut short.')
                f.seek(offset)
                return sfo.values(f.read(size))
    except OSError as err:
        raise PkgError(f'The PKG does not open: {err.strerror or err}') from err
    except (struct.error, ValueError, IndexError, KeyError) as err:       # sfo.SfoError is a ValueError
        raise PkgError(f'{name} has no param.sfo Overtime reads ({err}).') from err
    raise PkgError(f'{name} has no param.sfo.')


def find_update(pkg, title):
    """The update PKG Overtime needs for game `title` (APP_VER gamesetup.APP_VER, CATEGORY gp, that title id) in the
    folder of the game PKG `pkg`, top level only. Returns (its path or None, [(file name, version)] of the updates for
    that game at another version seen there). Only headers are read; a file that is no PKG Overtime reads is passed
    over."""
    pkg = os.path.abspath(pkg)
    folder = os.path.dirname(pkg)
    try:
        names = sorted(os.listdir(folder), key=str.lower)
    except OSError:
        return None, []
    found, others = None, []
    for name in names:
        path = os.path.join(folder, name)
        if (not name.lower().endswith('.pkg') or os.path.normcase(path) == os.path.normcase(pkg)
                or not os.path.isfile(path)):
            continue
        try:
            values = sfo_of(path)
        except PkgError:
            continue
        if values.get('TITLE_ID') != title or values.get('CATEGORY') != PATCH:
            continue
        if values.get('APP_VER') != gamesetup.APP_VER:
            others.append((name, values.get('APP_VER') or '?'))
        elif found is None:
            found = path
    return found, others


# --- the tool ---------------------------------------------------------------------------------------------------------
def tool_dir():
    return paths.app_dir('pkgtool')


def tool_exe():
    return os.path.join(paths.app_home(), 'pkgtool', TOOL_EXE)


def _stamp():
    return os.path.join(paths.app_home(), 'pkgtool', 'sha256.txt')


def _download(part, progress=None, opener=None):
    sha, got = hashlib.sha256(), 0
    try:
        r = (opener or packdownload._open)(TOOL_URL)
    except (OSError, ValueError, http.client.HTTPException) as err:
        gone = isinstance(err, urllib.error.HTTPError) and err.code == 404
        raise PkgError('The PKG tool is not on GitHub any more.' if gone else packdownload.NETWORK) from err
    with r, open(part, 'wb') as out:
        while True:
            try:
                block = r.read(packdownload.CHUNK)
            except (OSError, http.client.HTTPException) as err:
                raise PkgError(packdownload.NETWORK) from err
            if not block:
                break
            got += len(block)
            if got > TOOL_SIZE:
                raise PkgError('The PKG tool downloaded is not the one Overtime knows, so it was not used.')
            out.write(block)
            sha.update(block)
            if progress:
                progress(got, TOOL_SIZE)
    if got != TOOL_SIZE or sha.hexdigest() != TOOL_SHA256:
        raise PkgError('The PKG tool downloaded is not the one Overtime knows, so it was not used.')


class _NoZip:
    """ensure_tool's stand-in for the zip when the download is the program itself: nothing to unpack."""
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    @staticmethod
    def infolist():
        return ()


def ensure_tool(progress=None, opener=None):
    """The PKG tool in the app's folder, downloaded (the first time) from the shadPS4Plus release and checked: a zip
    holding pkg_extractor.exe on Windows, one AppImage on Linux. PkgError where the release has no build (macOS)."""
    if not TOOL_URL:
        raise PkgError(NO_TOOL)
    exe, stamp = tool_exe(), _stamp()
    try:
        with open(stamp, encoding='ascii') as f:
            if f.read().strip() == TOOL_SHA256 and os.path.isfile(exe):
                return exe
    except OSError:
        pass
    folder = tool_dir()
    part = os.path.join(folder, 'tool.zip.part')
    try:
        _download(part, progress, opener)
        if not TOOL_URL.lower().endswith('.zip'):       # one program file (Linux: the AppImage), not a zip
            os.chmod(part, 0o755)
            os.replace(part, exe)
        with zipfile.ZipFile(part) if os.path.exists(part) else _NoZip() as z:
            for info in z.infolist():
                name = os.path.basename(info.filename.replace('\\', '/'))
                if info.is_dir() or not name or name in ('.', '..'):
                    continue
                with z.open(info) as src, open(os.path.join(folder, name), 'wb') as out:
                    shutil.copyfileobj(src, out, 1 << 20)
        if not os.path.isfile(exe):
            raise PkgError(f'The PKG tool has no {TOOL_EXE}.')
        with open(stamp, 'w', encoding='ascii') as f:
            f.write(TOOL_SHA256 + '\n')
    except zipfile.BadZipFile as err:
        raise PkgError(f'The PKG tool does not unpack: {err}') from err
    except OSError as err:
        raise PkgError(f'The PKG tool could not be saved: {err}') from err
    finally:
        if os.path.exists(part):
            os.remove(part)
    return exe


def _environment(exe):
    """The tool's environment: the one from before this program; an AppImage is told to unpack itself for the run,
    so it starts with or without FUSE (a Steam Deck's Game Mode has none)."""
    env = selfupdate.clean_environment()
    if exe.lower().endswith('.appimage'):
        env['APPIMAGE_EXTRACT_AND_RUN'] = '1'
    return env


def _popen(args, popen=subprocess.Popen):
    try:
        return popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                     cwd=os.path.dirname(args[0]), text=True, encoding='utf-8', errors='replace',
                     creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0), env=_environment(args[0]))
    except OSError as err:
        raise PkgError(f'The PKG tool did not start ({err.strerror or err}). Your antivirus may have stopped it.') \
            from err


def kind(exe, pkg, popen=subprocess.Popen):
    """BASE, UPDATE or DLC (the tool's --check-type), or PkgError."""
    proc = _popen([exe, pkg, '--check-type'], popen)
    out = proc.communicate()[0] or ''
    if proc.returncode in (BASE, UPDATE, DLC):
        return proc.returncode
    said = _why(out.splitlines()) or 'it may be cut short or damaged: download it again'     # the tool crashes on those
    raise PkgError(f'The PKG tool cannot read {os.path.basename(pkg)}{f" ({said})" if said else ""}.')


# --- installing --------------------------------------------------------------------------------------------------------
def _gigabytes(n):
    return f'{n / 1e9:.1f} GB'


def _room(folder, need):
    free = shutil.disk_usage(folder).free
    if free < need:
        drive = os.path.splitdrive(os.path.abspath(folder))[0] or folder
        raise PkgError(f'{drive} has {_gigabytes(free)} free, the game needs about {_gigabytes(need)}. Free some space, '
                       'or move the PKG to a drive with room, then try again.')


def _size(folder):
    total = 0
    for top, _dirs, names in os.walk(folder):
        for name in names:
            try:
                total += os.path.getsize(os.path.join(top, name))
            except OSError:
                pass
    return total


def _free_name(path):
    """`path`, or `path-2`, `path-3`... the first that does not exist (an existing folder is never written into)."""
    if not os.path.exists(path):
        return path
    n = 2
    while os.path.exists(f'{path}-{n}'):
        n += 1
    return f'{path}-{n}'


def extract(exe, pkg, scratch, progress=None, popen=subprocess.Popen, poll=1.0):
    """Run the tool into `scratch`; its output lines. progress(done bytes, total bytes) from the folder's size against
    the PKG's (the tool only says which file it is on)."""
    total = os.path.getsize(pkg)
    proc = _popen([exe, pkg, scratch], popen)
    stop = threading.Event()

    def watch():
        while not stop.wait(poll):
            if progress:
                progress(min(_size(scratch), total), total)
    watcher = threading.Thread(target=watch, daemon=True, name='pkg-extract')
    watcher.start()
    lines = []
    try:
        for raw in proc.stdout:
            lines.append(raw.rstrip())
        proc.wait()
    finally:
        stop.set()
        watcher.join(5)
    return lines


def _why(lines):
    """The tool's reason from its output, without the file's path: 'Cannot open PKG file : <why>', 'Could not read
    SFO.', '"<path>" doesn't appear to be a valid PKG file'."""
    for x in reversed(lines):
        x = x.strip()
        if x.startswith('Cannot ') and ':' in x:
            return x.split(':', 1)[1].strip()
        if x.startswith('Could not'):
            return x.rstrip('.')
        if "doesn't appear" in x:
            return re.sub(r'^"[^"]*"\s*', '', x).replace("doesn't appear", 'does not appear', 1).rstrip('.')
    return ''


def install(pkg, game_dir=None, progress=None, running=None, popen=subprocess.Popen, opener=None, want=None):
    """Install one NHL 19 PKG. The base: a new folder next to the PKG. The update: a new `<game>-patch` folder beside
    `game_dir` (the base must be there). Returns (folder of the game to use, BASE | UPDATE, read_game's dict).
    progress(stage 'tool' | 'extract', done, total). `want` (BASE or UPDATE): any other kind the tool reads is refused
    before anything is extracted. PkgError in words for everything that stops it."""
    pkg = os.path.abspath(pkg)
    title = title_of(pkg)
    if title not in gamesetup.TITLE_IDS:
        raise PkgError(f'This PKG is {title}, not NHL 19 ({" or ".join(gamesetup.TITLE_IDS)}).')
    gamesetup._refuse_while_running(running)
    if overlay.launcher_running():
        raise PkgError('Close the shadPS4 launcher first.')
    exe = ensure_tool((lambda d, t: progress('tool', d, t)) if progress else None, opener)
    k = kind(exe, pkg, popen)
    if want is not None and k != want:
        raise PkgError(f'The PKG tool reads {os.path.basename(pkg)} as {_WHAT[k]}, not as {_WHAT[want]}.')
    if k == DLC:
        raise PkgError('This PKG is DLC. NHL 19 needs only the game and its update 1.60.')
    if k == UPDATE:
        game = gamesetup.read_game(game_dir) if game_dir else None
        base = gamefiles.roots(game_dir)[0] if game_dir else None
        if not game or game.get('title_id') not in gamesetup.TITLE_IDS or not base:
            raise PkgError('Install the game PKG first, then its update.')
        parent, target = os.path.dirname(base), base + '-patch'
        if os.path.isdir(base + '-UPDATE'):
            raise PkgError(f'An update is already in {base}-UPDATE, and shadPS4 uses that one first. Move it out of '
                           'that folder, then install the update again.')
    else:
        parent = os.path.dirname(pkg)
        target = _free_name(os.path.join(parent, title))
    _room(parent, int(os.path.getsize(pkg) * SPARE))
    scratch = os.path.join(parent, SCRATCH + str(os.getpid()) + '-' + str(int(time.time())))
    os.makedirs(scratch)
    try:
        lines = extract(exe, pkg, scratch, (lambda d, t: progress('extract', d, t)) if progress else None, popen)
        made = os.path.join(scratch, title + ('-patch' if k == UPDATE else ''))
        if not os.path.isfile(os.path.join(made, 'sce_sys', 'param.sfo')):
            why = _why(lines)
            raise PkgError(f'The PKG did not extract{f": {why}" if why else ""}.')
        if k == UPDATE and os.path.isdir(target):
            os.replace(target, _free_name(target + '.old'))     # an earlier update is kept, not deleted
        os.replace(made, target)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    use = base if k == UPDATE else target
    return use, k, gamesetup.read_game(use)


def add_update(pkg, use, game, progress=None, running=None, popen=subprocess.Popen, opener=None):
    """Right after the game PKG `pkg` went into `use` (read_game's `game`): the update Overtime needs, found beside
    `pkg` (find_update) and installed with install()'s checks; the tool must read it as an update. progress(stage
    'tool' | 'update', done, total). Never raises: a failed update leaves the game as it is.
    Returns (folder of the game, read_game's dict, what happened): {'file': the update's file name or None, 'others':
    [(file name, version)] updates of another version seen there, 'installed': bool, 'error': why not, or None}."""
    try:
        title = game.get('title_id') or title_of(pkg)
    except PkgError:
        return use, game, {'file': None, 'others': [], 'installed': False, 'error': None}
    found, others = find_update(pkg, title)
    auto = {'file': found and os.path.basename(found), 'others': others, 'installed': False, 'error': None}
    if not found:
        return use, game, auto
    step = (lambda stage, d, t: progress('update' if stage == 'extract' else stage, d, t)) if progress else None
    try:
        use, _kind, game = install(found, use, step, running, popen, opener, want=UPDATE)
    except (PkgError, gamesetup.SetupError, OSError) as err:
        auto['error'] = str(err)
        return use, game, auto
    auto['installed'] = True
    return use, game, auto
