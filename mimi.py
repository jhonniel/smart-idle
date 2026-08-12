import time
import pyautogui
from ctypes import Structure, windll, c_uint, sizeof, byref


class LASTINPUTINFO(Structure):
    _fields_ = [
        ("cbSize", c_uint),
        ("dwTime", c_uint),
    ]


def get_idle_time():
    last_input = LASTINPUTINFO()
    last_input.cbSize = sizeof(LASTINPUTINFO)

    windll.user32.GetLastInputInfo(byref(last_input))

    millis = windll.kernel32.GetTickCount() - last_input.dwTime
    return millis / 1000


IDLE_LIMIT = 120       # 2 minutes before starting
PRESS_INTERVAL = 30    # Press Ctrl every 30 seconds while idle

print("Keyboard activity monitor is running...")
print("Automatic Ctrl press starts after 2 minutes of inactivity.")


while True:

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
        time.sleep(1)
        current = get_idle_time()

        # Idle time dropped => user pressed a key or moved the mouse
        if current < baseline:
            print("User activity detected -> automatic Ctrl press stopped")
            break

        baseline = current
