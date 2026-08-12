import random
import time
from ctypes import Structure, windll, c_uint, sizeof, byref, WINFUNCTYPE
from ctypes.wintypes import HWND, LPARAM, BOOL

import pyautogui

user32 = windll.user32
kernel32 = windll.kernel32

# Windows display affinity — capture apps see black / no content
WDA_MONITOR = 0x00000001
WDA_EXCLUDEFROMCAPTURE = 0x00000011  # Win10 2004+

IDLE_LIMIT = 120          # 2 minutes before starting keep-awake presses
PRESS_INTERVAL = 30       # Seconds between presses while idle
PROTECT_INTERVAL = 2      # Re-apply screenshot block every N seconds

# Safe keys only: no letters/numbers/symbols, so nothing is typed into the active app.
# F15/F16 are usually unbound; modifiers are tap-only (no text).
SAFE_KEYS = ("f15", "f16", "ctrl", "shift")


class LASTINPUTINFO(Structure):
    _fields_ = [
        ("cbSize", c_uint),
        ("dwTime", c_uint),
    ]


EnumWindowsProc = WINFUNCTYPE(BOOL, HWND, LPARAM)


def get_idle_time():
    last_input = LASTINPUTINFO()
    last_input.cbSize = sizeof(LASTINPUTINFO)
    user32.GetLastInputInfo(byref(last_input))
    millis = kernel32.GetTickCount() - last_input.dwTime
    return millis / 1000


def _protect_window(hwnd, _lparam):
    if user32.IsWindowVisible(hwnd):
        if not user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE):
            user32.SetWindowDisplayAffinity(hwnd, WDA_MONITOR)
    return True


_enum_callback = EnumWindowsProc(_protect_window)


def block_screenshots():
    """Mark visible windows so capture apps get black / blank content."""
    user32.EnumWindows(_enum_callback, 0)


def press_safe_key():
    key = random.choice(SAFE_KEYS)
    pyautogui.press(key)
    return key


print("mimi is running...")
print("Screenshot block is ON (capture apps get black screen).")
print("Safe-key keep-awake starts after 2 minutes of inactivity.")
print(f"Safe keys (random each press): {', '.join(SAFE_KEYS)}")

last_protect = 0.0

while True:
    now = time.time()

    if now - last_protect >= PROTECT_INTERVAL:
        block_screenshots()
        last_protect = now

    idle_time = get_idle_time()

    if idle_time < IDLE_LIMIT:
        time.sleep(1)
        continue

    key = press_safe_key()
    print(f"Idle for 2 minutes -> safe key pressed ({key})")

    time.sleep(0.5)
    baseline = get_idle_time()

    for _ in range(PRESS_INTERVAL):
        now = time.time()
        if now - last_protect >= PROTECT_INTERVAL:
            block_screenshots()
            last_protect = now

        time.sleep(1)
        current = get_idle_time()

        if current < baseline:
            print("User activity detected -> automatic keep-awake stopped")
            break

        baseline = current
