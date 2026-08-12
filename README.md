# mimi

Hidden Windows idle monitor. After **2 minutes** of no keyboard/mouse activity, it taps a **safe key** every **30 seconds** until you use the PC again. No mouse movement.

Safe keys are non-typing only (`F15`, `F16`, `Ctrl`, `Shift`) so the focused app does not receive letters or numbers.

Also blocks screenshots for **capture apps** (for example Hubstaff-style screen samples): your screen looks normal to you, but those apps should get a **black / blank** image instead of your real desktop.

Runs in the background with no console window, and can start automatically at login.

---

## Requirements

- Windows
- Python 3 (with `pip`)
- Internet (only for the one-time package install)

---

## Step 1 — Install Python

1. Install Python from [python.org](https://www.python.org/downloads/) or Scoop.
2. During install, enable **Add Python to PATH** if using the official installer.
3. Open PowerShell and confirm:

```powershell
python --version
pythonw --version
```

Both should print a version number.

---

## Step 2 — Get the project files

Put these files in one folder, for example:

`C:\Users\<YourName>\Documents\Projects\mimi\`

| File | Purpose |
|------|---------|
| `mimi.py` | Main script (safe-key keep-awake + screenshot block) |
| `mimi.vbs` | Hidden launcher (no console window) |
| `requirements.txt` | Python dependencies |

---

## Step 3 — Install dependencies

Open PowerShell in the project folder:

```powershell
cd C:\Users\<YourName>\Documents\Projects\mimi
python -m pip install -r requirements.txt
```

This installs `pyautogui` (and its helpers).

Confirm:

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
Screenshot block is ON (capture apps get black screen).
Safe-key keep-awake starts after 2 minutes of inactivity.
Safe keys: f15, f16, ctrl, shift
```

Leave the PC idle for 2 minutes — it should print when a safe key is pressed. Press `Ctrl+C` to stop.

To test screenshot blocking: with mimi running, take a screenshot from another app (or Snipping Tool / Win+Shift+S). Captured windows should appear black. Your live screen should still look normal.

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
5. Every **2 seconds**, marks visible windows with Windows `SetWindowDisplayAffinity` (`WDA_EXCLUDEFROMCAPTURE`, fallback `WDA_MONITOR`) so screenshot / monitoring apps (like Hubstaff samples) should get black / blank content. You still see the screen normally.

### Screenshot block limits

- Aimed at apps that take periodic desktop screenshots (Hubstaff and similar).
- Uses the built-in Windows capture-exclusion API — your display stays normal.
- May not stop every capture method (some elevated tools, custom drivers, or a phone camera).
- New windows are covered on the next protect pass (every 2 seconds).
- After updating `mimi.py`, restart mimi so the new protection is active.

---

## Settings

Edit `mimi.py`:

```python
IDLE_LIMIT = 120          # seconds before first keep-awake press
PRESS_INTERVAL = 30       # seconds between presses while idle
PROTECT_INTERVAL = 2      # seconds between screenshot-block refreshes
SAFE_KEYS = ("f15", "f16", "ctrl", "shift")  # non-typing keys only
```

After changing settings, restart mimi (stop the old process, then run `mimi.vbs` again).

---

## Stop mimi

1. Open **Task Manager** (`Ctrl + Shift + Esc`)
2. Find **pythonw.exe**
3. End the task

To disable auto-start: delete `mimi.lnk` from the Startup folder (`shell:startup`).

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `python` not found | Reinstall Python and enable PATH, or restart the terminal |
| `No module named pyautogui` | Run `python -m pip install -r requirements.txt` |
| VBS does nothing | Confirm `pythonw.exe` works; run `python mimi.py` to see errors |
| Does not start at login | Check Startup has `mimi.lnk` pointing to the correct `mimi.vbs` path |
| Shortcut broken after moving folder | Update or recreate the Startup shortcut |
| Screenshots not black | Restart mimi; some tools ignore this Windows flag |
| Some windows still capture fine | Elevated / protected apps may ignore affinity |

---

## Finish checklist

- [ ] Python installed (`python` / `pythonw` work)
- [ ] `pip install -r requirements.txt` succeeded
- [ ] `python mimi.py` works when tested
- [ ] `mimi.vbs` runs hidden
- [ ] Startup shortcut `mimi.lnk` created
- [ ] (Optional) Sign out/in once to confirm auto-start
