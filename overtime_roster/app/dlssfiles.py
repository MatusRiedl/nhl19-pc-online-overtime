"""The DLSS files for Overtime Native v3's Picture options (0.99.0). The Overtime server hosts both (owner 2026-11-22,
which reverses 2026-11-21's "never hosted by us"): the app downloads one the first time it is turned on (fetch, through
packdownload: the published sha256 and size). They are not in the exe or the packs, so taking them off the server is
all it takes to stop; a player can always add their own copy on the Boost card instead (add).

- DLSS ('dlss', nvngx_dlss.dll): NVIDIA's Super Resolution model, found in many PC games' folders. NGX looks for it
  beside the program, so it is kept in the app's folder (app_dir('dlss')) and copied beside Overtime Native v3's
  shadPS4 (place_beside) at each start; a pack update that rewrites the exe leaves it.
- DLSS 5 ('dlss5', nvngx_dlssnr.dll): NVIDIA's Neural Rendering model; on RTX 20/30/40 the player's compat build of
  it. Kept in app_dir('dlss'); the game's config names it (GPU.dlss_nr_dll), so the pack never touches it.

A file is taken when its name is the one NGX asks for, it is a Windows DLL (MZ) and is bigger than MIN_BYTES.

- Frame generation (v1.00.0, FG_PACK): NVIDIA Streamline's DLLs and the DLSS frame generation model, one zip on the
  Overtime server, downloaded the first time frame generation is picked (fg_fetch) and unpacked into fg_dir(). They
  only work as one set, so there is no add-your-own. Streamline loads them from beside the program: fg_place_beside
  copies them there at each start, with NVIDIA's licence texts (licenses/NVIDIA beside it).

Standard library only.
"""
import filecmp
import os
import shutil

from overtime_core import durable

from . import paths

FILES = {'dlss': {'name': 'nvngx_dlss.dll', 'label': 'DLSS'},
         'dlss5': {'name': 'nvngx_dlssnr.dll', 'label': 'DLSS 5'}}
MIN_BYTES = 1 << 20     # the smallest real one is tens of MB
KINDS = {'dlss': 'DLSS (nvngx_dlss.dll)', 'dlss5': 'DLSS 5 (nvngx_dlssnr.dll)'}
# frame generation (v1.00.0): the pack, the DLLs at its top (the fork's FrameGen::RequiredDlls), its licence folder
FG_PACK = 'dlss_fg.zip'
FG_DLLS = ('sl.interposer.dll', 'sl.common.dll', 'sl.dlss_g.dll', 'sl.reflex.dll', 'sl.pcl.dll', 'nvngx_dlssg.dll')
FG_LICENSES = 'licenses'
FG_LICENSES_BESIDE = os.path.join('licenses', 'NVIDIA')
FG_LABEL = 'frame generation files'
FG_MAX_BYTES = 256 << 20    # a member bigger than this is no Streamline file (nvngx_dlssg.dll is about 8 MB)


class DlssFileError(RuntimeError):
    pass


def path(kind):
    """Where the app keeps the player's file of `kind` ('dlss', 'dlss5')."""
    return os.path.join(paths.app_dir('dlss'), FILES[kind]['name'])


def here(kind):
    """The kept file of `kind` when it is there, else ''."""
    p = path(kind)
    return p if os.path.isfile(p) else ''


def check(kind, source):
    """Why `source` is not a file of `kind`, or ''."""
    want = FILES[kind]['name']
    if os.path.basename(source).lower() != want:
        return f'Choose the file named {want}.'
    return content(want, source)


def content(want, source):
    """Why the file at `source` is not a DLSS file `want` (a Windows DLL of MIN_BYTES or more), or ''."""
    try:
        size = os.path.getsize(source)
        with open(source, 'rb') as f:
            head = f.read(2)
    except OSError as err:
        return f'{want} does not read: {err.strerror or err}'
    if head != b'MZ' or size < MIN_BYTES:
        return f'That {want} is not a DLSS file (too small, or not a Windows DLL).'
    return ''


def add(kind, source):
    """Copy the player's `source` in as the kept file of `kind`; returns its path. DlssFileError when it is not one."""
    why = check(kind, source)
    if why:
        raise DlssFileError(why)
    target = path(kind)
    if os.path.normcase(os.path.abspath(source)) == os.path.normcase(os.path.abspath(target)):
        return target
    tmp = target + '.part'
    try:
        shutil.copyfile(source, tmp)
        durable.replace(tmp, target)
    except OSError as err:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise DlssFileError(f"{FILES[kind]['name']} was not copied: {err.strerror or err}") from err
    return target


def fetch(kind, progress=None, release=None):
    """Download the file of `kind` from the Overtime server straight into the app's folder (packdownload: the
    published sha256 and size, TRIES, then content()); returns its path. `release`: packdownload.download's (the
    published table, or None: the release host). DlssFileError with the reason for players otherwise (NOT_OFFERED:
    the server has none)."""
    from . import packdownload      # here: packdownload checks the files with content()
    name = FILES[kind]['name']
    (_name, ok, message), = packdownload.download([name], paths.app_dir('dlss'), progress=progress, release=release)
    if ok and here(kind):
        return path(kind)
    if message == packdownload.NOT_OFFERED:
        message = f'The Overtime server does not offer {name} now. Add your own copy on the Boost card.'
    raise DlssFileError(message if not ok else f'{name} did not arrive.')


def downloaded(kind):
    """True when the kept file of `kind` is the one fetch() put there (not a copy the player added since)."""
    from . import packdownload
    return packdownload.recorded(FILES[kind]['name'], paths.app_dir('dlss'))


def remove(kind, beside=()):
    """Take the kept file of `kind` away, and its copies beside the programs in `beside` (their exe paths)."""
    for p in (path(kind), *(os.path.join(os.path.dirname(exe), FILES[kind]['name']) for exe in beside if exe)):
        try:
            if os.path.isfile(p):
                os.remove(p)
        except OSError as err:
            raise DlssFileError(f"{FILES[kind]['name']} is in use: close NHL 19 first ({err.strerror or err})") from err


def ready_for(run):
    """Before a start of `run`: the DLSS file and the frame generation files beside it when it is one of the app's
    builds with the Picture options (the player's own shadPS4 folder is never written to)."""
    from . import boost
    build = boost.build_of(run) if run else None
    if build and boost.BUILDS[build].get('picture'):
        place_beside(run)
        fg_place_beside(run)


def place_beside(exe):
    """Put the kept DLSS file beside `exe` (where NGX looks for it) when it is not there already; the copy beside it
    goes when the kept one is gone. Never raises: DLSS then falls back to FSR 1 in the game."""
    name = FILES['dlss']['name']
    if not exe:
        return
    kept, there = here('dlss'), os.path.join(os.path.dirname(exe), name)
    try:
        if not kept:
            if os.path.isfile(there):
                os.remove(there)
            return
        if os.path.isfile(there) and os.path.getsize(there) == os.path.getsize(kept):
            return
        shutil.copyfile(kept, there)
    except OSError:
        pass


# --- frame generation (v1.00.0) -------------------------------------------------------------------------------------
def fg_dir():
    """Where the app keeps the unpacked frame generation files."""
    return os.path.join(paths.app_dir('dlss'), 'fg')


def fg_here():
    """True when every frame generation DLL is in fg_dir()."""
    return all(os.path.isfile(os.path.join(fg_dir(), name)) for name in FG_DLLS)


def _fg_members(names):
    """{target path relative to fg_dir: member} of a frame generation zip's names: the DLLs at its top (any case) and
    the files under licenses/ (no folder climbing). Nothing else is taken."""
    out = {}
    for member in names:
        parts = member.replace('\\', '/').split('/')
        if member.endswith('/') or ':' in member or any(p in ('', '.', '..') for p in parts):
            continue
        if len(parts) == 1 and parts[0].lower() in FG_DLLS:
            out[parts[0].lower()] = member
        elif len(parts) > 1 and parts[0].lower() == FG_LICENSES:
            out[os.path.join(FG_LICENSES, *parts[1:])] = member
    return out


def fg_pack_problem(source):
    """Why the zip at `source` is not the frame generation pack (each of FG_DLLS at its top as a Windows DLL, NVIDIA's
    licence texts under licenses/), or ''."""
    import zipfile
    try:
        with zipfile.ZipFile(source) as z:
            members = _fg_members(z.namelist())
            for name in FG_DLLS:
                if name not in members:
                    return f'{name} is not in the frame generation pack.'
                info = z.getinfo(members[name])
                with z.open(info) as f:
                    if f.read(2) != b'MZ' or info.file_size > FG_MAX_BYTES:
                        return f'{name} in the frame generation pack is not a Windows DLL.'
            if not any(k.startswith(FG_LICENSES + os.sep) for k in members):
                return "NVIDIA's licence texts are not in the frame generation pack."
    except (zipfile.BadZipFile, KeyError, ValueError, OSError) as err:
        return f'The frame generation pack does not read: {err}'
    return ''


def fg_unpack(source):
    """Unpack the frame generation zip at `source` into fg_dir() (in place of what was there); returns fg_dir().
    DlssFileError when it is not the pack or does not unpack."""
    import zipfile
    why = fg_pack_problem(source)
    if why:
        raise DlssFileError(why)
    target = fg_dir()
    part = target + '.part'
    try:
        shutil.rmtree(part, ignore_errors=True)
        with zipfile.ZipFile(source) as z:
            for rel, member in _fg_members(z.namelist()).items():
                out = os.path.join(part, rel)
                os.makedirs(os.path.dirname(out), exist_ok=True)
                with z.open(member) as src, open(out, 'wb') as dst:
                    shutil.copyfileobj(src, dst)
        if os.path.isdir(target):
            shutil.rmtree(target)
        os.replace(part, target)
    except (OSError, zipfile.BadZipFile) as err:
        shutil.rmtree(part, ignore_errors=True)
        raise DlssFileError(f'The {FG_LABEL} were not unpacked: {getattr(err, "strerror", None) or err}') from err
    return target


def fg_fetch(progress=None, release=None):
    """Download the frame generation pack from the Overtime server into the app's folder (packdownload: the published
    sha256 and size, then fg_pack_problem) and unpack it; returns fg_dir(). DlssFileError with the reason for players
    otherwise."""
    from . import packdownload
    folder = paths.app_dir('dlss')
    (_name, ok, message), = packdownload.download([FG_PACK], folder, progress=progress, release=release)
    if not ok:
        if message == packdownload.NOT_OFFERED:
            message = f'The Overtime server does not offer the {FG_LABEL} now. Try again later.'
        raise DlssFileError(message)
    return fg_unpack(os.path.join(folder, FG_PACK))


def _fg_clear(folder):
    """The frame generation DLLs and NVIDIA's licence folder out of `folder` (a program's)."""
    for name in FG_DLLS:
        p = os.path.join(folder, name)
        if os.path.isfile(p):
            os.remove(p)
    shutil.rmtree(os.path.join(folder, FG_LICENSES_BESIDE), ignore_errors=True)


def fg_remove(beside=()):
    """Take the frame generation files away: the app's copy, its pack, and the copies beside the programs in `beside`
    (their exe paths)."""
    try:
        for exe in beside:
            if exe:
                _fg_clear(os.path.dirname(exe))
        if os.path.isdir(fg_dir()):
            shutil.rmtree(fg_dir())
        pack = os.path.join(paths.app_dir('dlss'), FG_PACK)
        if os.path.isfile(pack):
            os.remove(pack)
    except OSError as err:
        raise DlssFileError(f'The {FG_LABEL} are in use: close NHL 19 first ({err.strerror or err})') from err


def fg_place_beside(exe):
    """Put the kept frame generation DLLs beside `exe` (where Streamline loads them from), with NVIDIA's licence texts
    in licenses/NVIDIA; the copies beside it go when the kept ones are gone. Never raises: the game then plays without
    frame generation (one log line)."""
    if not exe:
        return
    folder, kept = os.path.dirname(exe), fg_dir()
    try:
        if not fg_here():
            _fg_clear(folder)
            return
        for name in FG_DLLS:
            src, there = os.path.join(kept, name), os.path.join(folder, name)
            if not (os.path.isfile(there) and filecmp.cmp(src, there, shallow=False)):
                shutil.copyfile(src, there)
        licences = os.path.join(kept, FG_LICENSES)
        if os.path.isdir(licences):
            shutil.copytree(licences, os.path.join(folder, FG_LICENSES_BESIDE), dirs_exist_ok=True)
    except OSError:
        pass
