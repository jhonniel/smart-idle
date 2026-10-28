import platform
import random
import re
import subprocess
import time
import traceback
from pathlib import Path

LOG_FILE = Path(__file__).with_name("mimi.log")

IDLE_LIMIT = 120          # Seconds of inactivity before keep-awake starts
PRESS_INTERVAL = 30       # Seconds between presses while idle
RESTART_DELAY = 5         # Seconds to wait before restart after a crash

# Safe keys only: no letters/numbers/symbols, so nothing is typed into the active app.
# F15/F16 are usually unbound; modifiers are tap-only (no text).
SAFE_KEYS = ("f15", "f16", "ctrl", "shift")

SYSTEM = platform.system()  # 'Windows', 'Darwin' (macOS), or 'Linux'


def log(message):
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{stamp}] {message}\n"
    with LOG_FILE.open("a", encoding="utf-8") as handle:
        handle.write(line)


# ---------------------------------------------------------------------------
# Idle detection (per OS)
# ---------------------------------------------------------------------------

def _build_windows_idle():
    """Idle seconds via the Win32 GetLastInputInfo API."""
    from ctypes import Structure, windll, c_uint, sizeof, byref

    class LASTINPUTINFO(Structure):
        _fields_ = [
            ("cbSize", c_uint),
            ("dwTime", c_uint),
        ]

    user32 = windll.user32
    kernel32 = windll.kernel32

    def _idle():
        info = LASTINPUTINFO()
        info.cbSize = sizeof(LASTINPUTINFO)
        user32.GetLastInputInfo(byref(info))
        return (kernel32.GetTickCount() - info.dwTime) / 1000.0

    return _idle


def _build_macos_idle():
    """Idle seconds via ioreg HIDIdleTime (no extra packages needed)."""

    def _idle():
        out = subprocess.check_output(["ioreg", "-c", "IOHIDSystem"], text=True)
        for line in out.splitlines():
            if "HIDIdleTime" in line:
                nanoseconds = int(line.rsplit("=", 1)[1].strip())
                return nanoseconds / 1_000_000_000
        return 0.0

    return _idle


def _try_build_x11_idle():
    """XScreenSaver idle (X11 sessions). Returns a callable or None."""
    import ctypes

    try:
        libX11 = ctypes.CDLL("libX11.so.6")
        libXss = ctypes.CDLL("libXss.so.1")
    except OSError:
        return None

    class XScreenSaverInfo(ctypes.Structure):
        _fields_ = [
            ("window", ctypes.c_ulong),
            ("state", ctypes.c_int),
            ("kind", ctypes.c_int),
            ("since", ctypes.c_ulong),
            ("idle", ctypes.c_ulong),
            ("event_mask", ctypes.c_ulong),
        ]

    libX11.XOpenDisplay.restype = ctypes.c_void_p
    libX11.XOpenDisplay.argtypes = [ctypes.c_char_p]
    libX11.XDefaultRootWindow.restype = ctypes.c_ulong
    libX11.XDefaultRootWindow.argtypes = [ctypes.c_void_p]
    libXss.XScreenSaverAllocInfo.restype = ctypes.POINTER(XScreenSaverInfo)
    libXss.XScreenSaverQueryInfo.argtypes = [
        ctypes.c_void_p,
        ctypes.c_ulong,
        ctypes.POINTER(XScreenSaverInfo),
    ]

    display = libX11.XOpenDisplay(None)
    if not display:
        return None

    root = libX11.XDefaultRootWindow(display)
    info = libXss.XScreenSaverAllocInfo()

    def _idle():
        libXss.XScreenSaverQueryInfo(display, root, info)
        return info.contents.idle / 1000.0

    return _idle


def _idle_gnome_mutter():
    """Idle seconds via the GNOME Mutter IdleMonitor (works on Wayland)."""
    out = subprocess.check_output(
        [
            "gdbus", "call", "--session",
            "--dest", "org.gnome.Mutter.IdleMonitor",
            "--object-path", "/org/gnome/Mutter/IdleMonitor/Core",
            "--method", "org.gnome.Mutter.IdleMonitor.GetIdletime",
        ],
        text=True,
    )
    # Output looks like: "(uint64 12345,)"  -> milliseconds.
    # Match the number after the uint64 token (not the "64" inside "uint64").
    match = re.search(r"uint64\s+(\d+)", out) or re.search(r"(\d+)", out)
    return int(match.group(1)) / 1000.0 if match else 0.0


def _idle_xprintidle():
    """Idle seconds via the xprintidle command (X11)."""
    out = subprocess.check_output(["xprintidle"], text=True)
    return int(out.strip()) / 1000.0


def _build_linux_idle():
    """Pick the first Linux idle method that actually works on this session."""
    candidates = []

    x11 = _try_build_x11_idle()
    if x11:
        candidates.append(("XScreenSaver", x11))
    candidates.append(("GNOME Mutter", _idle_gnome_mutter))
    candidates.append(("xprintidle", _idle_xprintidle))

    for name, fn in candidates:
        try:
            fn()
            log(f"Linux idle method: {name}")
            return fn
        except Exception:
            continue

    log("WARNING: no idle method available; pressing on a fixed interval instead")

    def _always_idle():
        return float(IDLE_LIMIT)

    return _always_idle


def build_idle_getter():
    if SYSTEM == "Windows":
        return _build_windows_idle()
    if SYSTEM == "Darwin":
        return _build_macos_idle()
    if SYSTEM == "Linux":
        return _build_linux_idle()
    raise RuntimeError(f"Unsupported operating system: {SYSTEM}")


# ---------------------------------------------------------------------------
# Key press (per OS)
# ---------------------------------------------------------------------------

def _build_linux_presser():
    """Inject keys via /dev/uinput (kernel level) so it works on X11 AND Wayland."""
    try:
        from evdev import UInput, ecodes
    except Exception:
        return None

    key_map = {
        "f15": ecodes.KEY_F15,
        "f16": ecodes.KEY_F16,
        "ctrl": ecodes.KEY_LEFTCTRL,
        "shift": ecodes.KEY_LEFTSHIFT,
    }

    try:
        ui = UInput({ecodes.EV_KEY: list(key_map.values())}, name="mimi-virtual-kbd")
    except Exception:
        # Usually a permission problem on /dev/uinput
        return None

    def _press(key):
        code = key_map.get(key)
        if code is None:
            return
        ui.write(ecodes.EV_KEY, code, 1)
        ui.syn()
        time.sleep(0.02)
        ui.write(ecodes.EV_KEY, code, 0)
        ui.syn()

    log("Linux key method: uinput (evdev)")
    return _press


def build_key_presser():
    if SYSTEM == "Linux":
        presser = _build_linux_presser()
        if presser:
            return presser
        log("Linux key method: pyautogui (X11 only; will not work on Wayland)")

    import pyautogui

    def _press(key):
        pyautogui.press(key)

    return _press


def run():
    get_idle_time = build_idle_getter()
    press_key = build_key_presser()

    log(f"mimi started on {SYSTEM}")
    print(f"mimi is running on {SYSTEM}...")
    print("Safe-key keep-awake starts after 2 minutes of inactivity.")
    print(f"Safe keys (random each press): {', '.join(SAFE_KEYS)}")
    print(f"Log file: {LOG_FILE}")

    while True:
        idle_time = get_idle_time()

        if idle_time < IDLE_LIMIT:
            time.sleep(1)
            continue

        key = random.choice(SAFE_KEYS)
        press_key(key)
        log(f"Idle keep-awake -> safe key pressed ({key})")
        print(f"Idle for 2 minutes -> safe key pressed ({key})")

        time.sleep(0.5)
        baseline = get_idle_time()

        for _ in range(PRESS_INTERVAL):
            time.sleep(1)
            current = get_idle_time()

            if current < baseline:
                log("User activity detected -> keep-awake paused")
                print("User activity detected -> automatic keep-awake stopped")
                break

            baseline = current


if __name__ == "__main__":
    while True:
        try:
            run()
        except KeyboardInterrupt:
            log("mimi stopped by user")
            break
        except Exception:
            log("mimi crashed:\n" + traceback.format_exc())
            log(f"Restarting in {RESTART_DELAY} seconds...")
            time.sleep(RESTART_DELAY)
