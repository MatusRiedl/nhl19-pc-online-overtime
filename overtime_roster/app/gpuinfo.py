"""The graphics card, for the Boost card's Picture options (0.99.0, Overtime Native v3): which of DLSS, DLSS 5 and DLSS
frame generation it can run.

Windows: the display adapters' DriverDesc in the registry (the names Device Manager shows), no driver call. Other
systems: unknown (Native v3 is a Windows build). An NVIDIA RTX card's generation is the number after "RTX" cut to its
first digit times ten (RTX 2060 -> 20, RTX 4090 -> 40, RTX 5080 -> 50; "RTX A4000" and other workstation names: 20, the
oldest that runs DLSS). Standard library only.
"""
import re
import sys

CLASS_KEY = r'SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}'
_RTX = re.compile(r'\bRTX\s*(\d{4})\b', re.I)
# what each Picture option needs (owner 2026-11-21): DLSS from RTX 20, DLSS 5 from RTX 20 (RTX 20/30/40 with the
# compat file), DLSS frame generation from RTX 40
DLSS_FROM, DLSS5_FROM, FG_FROM = 20, 20, 40
DLSS5_NATIVE_FROM = 50      # RTX 50 runs NVIDIA's own DLSS 5 file; RTX 20/30/40 need the compat build
DESKTOPVERTRES = 117        # GetDeviceCaps: the screen's height in real pixels, whatever the Windows scaling


def rtx_generation(name):
    """20, 30, 40, 50... for an NVIDIA RTX card's name, 0 for any other."""
    if not name or 'nvidia' not in name.lower() and 'geforce' not in name.lower() and 'rtx' not in name.lower():
        return 0
    m = _RTX.search(name)
    if m:
        return int(m.group(1)[0]) * 10
    return DLSS_FROM if re.search(r'\bRTX\b', name, re.I) else 0


def adapter_names(winreg=None):
    """The display adapters' names on Windows ([] elsewhere, or when the registry does not read)."""
    if sys.platform != 'win32' and winreg is None:
        return []
    if winreg is None:
        import winreg
    names = []
    try:
        root = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, CLASS_KEY)
    except OSError:
        return []
    with root:
        for i in range(64):
            try:
                sub = winreg.EnumKey(root, i)
            except OSError:
                break
            if not sub.isdigit():
                continue
            try:
                with winreg.OpenKey(root, sub) as key:
                    name, _kind = winreg.QueryValueEx(key, 'DriverDesc')
            except OSError:
                continue
            if isinstance(name, str) and name.strip() and name.strip() not in names:
                names.append(name.strip())
    return names


def screen_height():
    """The primary screen's height in pixels on Windows (GetDeviceCaps DESKTOPVERTRES: real pixels, also at 125 % or
    150 % scaling), for the DLSS quality choice; None on other systems or when it does not read."""
    if sys.platform != 'win32':
        return None
    try:
        import ctypes
        user32, gdi32 = ctypes.WinDLL('user32'), ctypes.WinDLL('gdi32')     # own handles: no global prototypes
        user32.GetDC.restype, user32.GetDC.argtypes = ctypes.c_void_p, (ctypes.c_void_p,)
        user32.ReleaseDC.argtypes = (ctypes.c_void_p, ctypes.c_void_p)
        gdi32.GetDeviceCaps.argtypes = (ctypes.c_void_p, ctypes.c_int)
        hdc = user32.GetDC(None)
        if not hdc:
            return None
        try:
            height = gdi32.GetDeviceCaps(hdc, DESKTOPVERTRES)
        finally:
            user32.ReleaseDC(None, hdc)
    except (OSError, AttributeError, ValueError):
        return None
    return height if isinstance(height, int) and height > 0 else None


def info(names=None):
    """{'name': the card the options are for ('' when unknown), 'rtx': its RTX generation (0: none), 'dlss', 'dlss5',
    'dlss5_compat' (needs the RTX 20/30/40 compat file), 'framegen': bool}. Of several cards, the newest RTX one."""
    names = adapter_names() if names is None else names
    best = max(names, key=rtx_generation, default='')
    rtx = rtx_generation(best)
    return {'name': best, 'rtx': rtx, 'dlss': rtx >= DLSS_FROM, 'dlss5': rtx >= DLSS5_FROM,
            'dlss5_compat': DLSS5_FROM <= rtx < DLSS5_NATIVE_FROM, 'framegen': rtx >= FG_FROM}
