import random
import time
import traceback
from ctypes import Structure, windll, c_uint, sizeof, byref
from pathlib import Path

import pyautogui

user32 = windll.user32
kernel32 = windll.kernel32

LOG_FILE = Path(__file__).with_name("mimi.log")

IDLE_LIMIT = 120          # 2 minutes before starting keep-awake presses
PRESS_INTERVAL = 30       # Seconds between presses while idle
RESTART_DELAY = 5         # Seconds to wait before restart after a crash

# Safe keys only: no letters/numbers/symbols, so nothing is typed into the active app.
# F15/F16 are usually unbound; modifiers are tap-only (no text).
SAFE_KEYS = ("f15", "f16", "ctrl", "shift")


def log(message):
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{stamp}] {message}\n"
    with LOG_FILE.open("a", encoding="utf-8") as handle:
        handle.write(line)


class LASTINPUTINFO(Structure):
    _fields_ = [
        ("cbSize", c_uint),
        ("dwTime", c_uint),
    ]


def get_idle_time():
    last_input = LASTINPUTINFO()
    last_input.cbSize = sizeof(LASTINPUTINFO)
    user32.GetLastInputInfo(byref(last_input))
    millis = kernel32.GetTickCount() - last_input.dwTime
    return millis / 1000


def press_safe_key():
    key = random.choice(SAFE_KEYS)
    pyautogui.press(key)
    return key


def run():
    log("mimi started")
    print("mimi is running...")
    print("Safe-key keep-awake starts after 2 minutes of inactivity.")
    print(f"Safe keys (random each press): {', '.join(SAFE_KEYS)}")
    print(f"Log file: {LOG_FILE}")

    while True:
        idle_time = get_idle_time()

        if idle_time < IDLE_LIMIT:
            time.sleep(1)
            continue

        key = press_safe_key()
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
