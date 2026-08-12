import time
import ctypes
from ctypes import Structure, windll, c_uint, sizeof, byref, WINFUNCTYPE
from ctypes.wintypes import HWND, LPARAM, BOOL

import pyautogui

user32 = windll.user32
kernel32 = windll.kernel32

# Windows display affinity — capture apps (Hubstaff-style screenshots) see black / no content
WDA_MONITOR = 0x00000001
WDA_EXCLUDEFROMCAPTURE = 0x00000011  # stronger; Win10 2004+

IDLE_LIMIT = 120          # 2 minutes before starting Ctrl presses
PRESS_INTERVAL = 30       # Press Ctrl every 30 seconds while idle
PROTECT_INTERVAL = 2      # Re-apply screenshot block every N seconds


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
    # Visible top-level windows only — you still see the screen normally.
    # Apps that take screenshots (e.g. Hubstaff) should get black / blank content.
    if user32.IsWindowVisible(hwnd):
        if not user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE):
            user32.SetWindowDisplayAffinity(hwnd, WDA_MONITOR)
    return True


_enum_callback = EnumWindowsProc(_protect_window)


def block_screenshots():
    """
    Mark visible windows so screenshot/monitoring apps get black (or no) content.
    Your live screen stays normal; only capturing apps are affected.
    """
    user32.EnumWindows(_enum_callback, 0)


print("mimi is running...")
print("Screenshot block is ON (capture apps get black screen).")
print("Automatic Ctrl press starts after 2 minutes of inactivity.")

last_protect = 0.0

while True:
    now = time.time()

    # Keep re-applying so new windows are also protected
    if now - last_protect >= PROTECT_INTERVAL:
        block_screenshots()
        last_protect = now

    idle_time = get_idle_time()

    # User is active
    if idle_time < IDLE_LIMIT:
        time.sleep(1)
        continue

    # User has been idle for 2 minutes — press Ctrl only (no mouse)
    pyautogui.press("ctrl")
    print("Idle for 2 minutes -> Ctrl pressed")

    # Our keypress resets idle time; wait briefly then watch for real user input
    time.sleep(0.5)
    baseline = get_idle_time()

    for _ in range(PRESS_INTERVAL):
        now = time.time()
        if now - last_protect >= PROTECT_INTERVAL:
            block_screenshots()
            last_protect = now

        time.sleep(1)
        current = get_idle_time()

        # Idle time dropped => user pressed a key or moved the mouse
        if current < baseline:
            print("User activity detected -> automatic Ctrl press stopped")
            break

        baseline = current
