"""The DLSS files a player adds for Overtime Native v3's Picture options (0.99.0). Overtime never hosts or ships them
(NVIDIA's licence, owner 2026-11-21): each player picks their own copy on the Boost card.

- DLSS ('dlss', nvngx_dlss.dll): NVIDIA's Super Resolution model, found in many PC games' folders. NGX looks for it
  beside the program, so it is kept in the app's folder (app_dir('dlss')) and copied beside Overtime Native v3's
  shadPS4 (place_beside) at each start; a pack update that rewrites the exe leaves it.
- DLSS 5 ('dlss5', nvngx_dlssnr.dll): NVIDIA's Neural Rendering model; on RTX 20/30/40 the player's compat build of
  it. Kept in app_dir('dlss'); the game's config names it (GPU.dlss_nr_dll), so the pack never touches it.

A file is taken when its name is the one NGX asks for, it is a Windows DLL (MZ) and is bigger than MIN_BYTES. Standard
library only.
"""
import os
import shutil

from overtime_core import durable

from . import paths

FILES = {'dlss': {'name': 'nvngx_dlss.dll', 'label': 'DLSS'},
         'dlss5': {'name': 'nvngx_dlssnr.dll', 'label': 'DLSS 5'}}
MIN_BYTES = 1 << 20     # the smallest real one is tens of MB
KINDS = {'dlss': 'DLSS (nvngx_dlss.dll)', 'dlss5': 'DLSS 5 (nvngx_dlssnr.dll)'}


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


def remove(kind, beside=()):
    """Take the kept file of `kind` away, and its copies beside the programs in `beside` (their exe paths)."""
    for p in (path(kind), *(os.path.join(os.path.dirname(exe), FILES[kind]['name']) for exe in beside if exe)):
        try:
            if os.path.isfile(p):
                os.remove(p)
        except OSError as err:
            raise DlssFileError(f"{FILES[kind]['name']} is in use: close NHL 19 first ({err.strerror or err})") from err


def ready_for(run):
    """Before a start of `run`: the DLSS file beside it when it is one of the app's builds with the Picture options
    (the player's own shadPS4 folder is never written to)."""
    from . import boost
    build = boost.build_of(run) if run else None
    if build and boost.BUILDS[build].get('picture'):
        place_beside(run)


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
