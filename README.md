# mimi

Hidden Windows idle monitor. After **2 minutes** of no keyboard/mouse activity, it taps a **safe key** every **30 seconds** until you use the PC again. No mouse movement.

Safe keys are non-typing only (`F15`, `F16`, `Ctrl`, `Shift`) so the focused app does not receive letters or numbers.

Runs in the background with no console window, and can start automatically at login.

---

## Requirements

| Requirement | Details |
|-------------|---------|
| **Operating system** | Windows 10 or 11 (uses Windows-only APIs via `ctypes`; it will not run on macOS or Linux) |
| **Python** | Python 3.8+ with `pip` (tested on Python 3.14). The `pythonw.exe` that ships with Python is also required for hidden mode. |
| **Python package** | `pyautogui` (>= 0.9.54) — listed in `requirements.txt` |
| **Internet** | Needed once, only to install the package |

Everything else mimi uses (`ctypes`, `random`, `time`, `pathlib`) is part of the Python standard library, so there is nothing else to install.

---

## Step 1 — Install Python

1. Install Python 3.8 or newer from [python.org](https://www.python.org/downloads/) (or via Scoop: `scoop install python`).
2. If using the official installer, enable **Add Python to PATH** on the first screen.
3. Open PowerShell and confirm both commands print a version:

```powershell
python --version
pythonw --version
```

If `python` is not recognized, close and reopen PowerShell, or reinstall with PATH enabled.

---

## Step 2 — Get the project files

Put these files together in one folder, for example `C:\Users\<YourName>\Documents\Projects\mimi\`:

| File | Purpose | Required? |
|------|---------|-----------|
| `mimi.py` | Main script (safe-key keep-awake) | Yes |
| `mimi.vbs` | Hidden launcher + watchdog (no console window) | Yes, for hidden/auto-start use |
| `requirements.txt` | Python dependency list | Yes, for install |
| `stop_mimi.ps1` | Stops mimi cleanly | Optional |
| `README.md` | This guide | Optional |
| `mimi.log` | Created automatically at runtime | Auto-generated |

---

## Step 3 — Install the requirements

Open PowerShell in the project folder and install from `requirements.txt`:

```powershell
cd C:\Users\<YourName>\Documents\Projects\mimi
python -m pip install -r requirements.txt
```

This installs `pyautogui` and its helper packages.

Confirm it imports and prints a version:

```powershell
python -c "import pyautogui; print(pyautogui.__version__)"
```

---

## Step 4 — Test the script (visible)

Run with a console so you can see messages:

```powershell
python mimi.py
```

You should see:

```text
mimi is running...
Safe-key keep-awake starts after 2 minutes of inactivity.
Safe keys: f15, f16, ctrl, shift
```

Leave the PC idle for 2 minutes — it should print when a safe key is pressed. Press `Ctrl+C` to stop.

---

## Step 5 — Run hidden

Double-click `mimi.vbs`, or from PowerShell:

```powershell
wscript mimi.vbs
```

No window appears. The script runs via `pythonw.exe` in the background.

---

## Step 6 — Auto-start on login (boot / sign-in)

1. Press `Win + R`
2. Type `shell:startup` and press Enter
3. Create a shortcut to `mimi.vbs` in that Startup folder:
   - Right-click inside the Startup folder → **New** → **Shortcut**
   - Browse to your `mimi.vbs`
   - Name the shortcut **mimi**
   - Finish

Or create the shortcut with PowerShell:

```powershell
$startup = [Environment]::GetFolderPath('Startup')
$target = 'C:\Users\<YourName>\Documents\Projects\mimi\mimi.vbs'
$shortcutPath = Join-Path $startup 'mimi.lnk'
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $target
$shortcut.WorkingDirectory = 'C:\Users\<YourName>\Documents\Projects\mimi'
$shortcut.Save()
```

After this, mimi starts automatically every time you sign in to Windows.

---

## How it works

1. Watches Windows idle time (`GetLastInputInfo`).
2. If idle for **120 seconds**, presses one **random safe key** from `F15`, `F16`, `Ctrl`, `Shift`.
3. While still idle, presses another random safe key every **30 seconds**.
4. If you move the mouse or type, automatic presses stop until idle again.

---

## Settings

Edit `mimi.py`:

```python
IDLE_LIMIT = 120          # seconds before first keep-awake press
PRESS_INTERVAL = 30       # seconds between presses while idle
SAFE_KEYS = ("f15", "f16", "ctrl", "shift")  # non-typing keys only
```

After changing settings, restart mimi (use `stop_mimi.ps1` or Task Manager, then run `mimi.vbs` again).

---

## Auto-restart on crash

`mimi.vbs` runs as a hidden watchdog:

1. Starts `mimi.py` with `pythonw.exe`
2. If it crashes or exits, waits **5 seconds** and starts it again
3. `mimi.py` also restarts itself on internal errors

Crash details are written to **`mimi.log`**.

---

## Stop mimi

**Option A — stop script (recommended):**

```powershell
.\stop_mimi.ps1
```

This creates `mimi.stop` and the watchdog exits cleanly.

**Option B — Task Manager:**

1. End **wscript.exe** (the watchdog — stops auto-restart)
2. End **pythonw.exe** if it is still running

To disable auto-start at login: delete `mimi.lnk` from the Startup folder (`shell:startup`).

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `python` not found | Reinstall Python and enable PATH, or restart the terminal |
| `No module named pyautogui` | Run `python -m pip install -r requirements.txt` |
| VBS does nothing | Confirm `pythonw.exe` works; run `python mimi.py` to see errors |
| Does not start at login | Check Startup has `mimi.lnk` pointing to the correct `mimi.vbs` path |
| Shortcut broken after moving folder | Update or recreate the Startup shortcut |
| mimi keeps coming back after kill | End **wscript.exe** (watchdog), or run `stop_mimi.ps1` |
| Crashes repeat | Check `mimi.log` for the error at the bottom |

---

## Finish checklist

- [ ] Python installed (`python` / `pythonw` work)
- [ ] `pip install -r requirements.txt` succeeded
- [ ] `python mimi.py` works when tested
- [ ] `mimi.vbs` runs hidden
- [ ] Startup shortcut `mimi.lnk` created
- [ ] (Optional) Sign out/in once to confirm auto-start
