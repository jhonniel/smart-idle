# mimi

Hidden cross-platform idle monitor for **Windows, macOS, and Linux**. After **2 minutes** of no keyboard/mouse activity, it taps a **safe key** every **30 seconds** until you use the computer again. No mouse movement.

Safe keys are non-typing only (`F15`, `F16`, `Ctrl`, `Shift`) so the focused app does not receive letters or numbers.

Runs quietly in the background and can start automatically at login.

---

## Requirements

| Requirement | Details |
|-------------|---------|
| **Operating system** | Windows 10/11, macOS, or Linux (X11). See the per-OS notes below. |
| **Python** | Python 3.8+ with `pip` (tested on 3.14). On Windows, `pythonw.exe` is also used for hidden mode. |
| **Python package** | `pyautogui` (>= 0.9.54) — listed in `requirements.txt` |
| **Internet** | Needed once, only to install the package |

Idle detection is built in per platform:

- **Windows** — Win32 `GetLastInputInfo` (standard library `ctypes`)
- **macOS** — the built-in `ioreg` command (`HIDIdleTime`)
- **Linux** — tries X11 XScreenSaver, then GNOME Mutter IdleMonitor (Wayland), then `xprintidle`

Key injection per platform:

- **Windows / macOS** — `pyautogui`
- **Linux** — a virtual keyboard via `/dev/uinput` (the `evdev` package), which works on **both X11 and Wayland**. If `evdev` or `/dev/uinput` is unavailable, it falls back to `pyautogui` (X11 only).

### Per-OS system notes

- **macOS:** You must grant **Accessibility** permission to the app that runs mimi (Terminal, or Python). Go to **System Settings → Privacy & Security → Accessibility** and enable it, or key presses will be ignored.
- **Linux (Ubuntu):** Ubuntu defaults to **Wayland**, which blocks `pyautogui`. mimi handles this by injecting keys through `/dev/uinput` instead — but that needs a one-time permission setup (see the Linux part of Step 3). This is why the ghost key may not have worked before.

---

## Step 1 — Install Python

**Windows:**
1. Install from [python.org](https://www.python.org/downloads/) (or `scoop install python`).
2. Enable **Add Python to PATH** during install.
3. Confirm in PowerShell:
   ```powershell
   python --version
   pythonw --version
   ```

**macOS:**
```bash
brew install python
python3 --version
```

**Ubuntu / Debian Linux:**
```bash
sudo apt update
sudo apt install python3 python3-pip
python3 --version
```

---

## Step 2 — Get the project files

Put these files together in one folder.

| File | Purpose | Platform |
|------|---------|----------|
| `mimi.py` | Main script (safe-key keep-awake) | All |
| `requirements.txt` | Python dependency list | All |
| `mimi.vbs` | Hidden launcher + watchdog | Windows |
| `stop_mimi.ps1` | Stops mimi | Windows |
| `run_mimi.sh` | Starts mimi in the background | macOS / Linux |
| `stop_mimi.sh` | Stops mimi | macOS / Linux |
| `README.md` | This guide | All |
| `mimi.log` | Created automatically at runtime | All |

---

## Step 3 — Install the requirements

From the project folder:

**Windows (PowerShell):**
```powershell
cd C:\Users\<YourName>\Documents\Projects\mimi
python -m pip install -r requirements.txt
```

**macOS / Linux (terminal):**
```bash
cd /path/to/mimi
python3 -m pip install -r requirements.txt
```

**Linux also needs these system packages**:
```bash
sudo apt install python3-tk python3-dev scrot xprintidle
```

**Linux — allow the ghost key (one-time `/dev/uinput` setup).** This is what makes keys work on Wayland:
```bash
# Load the uinput kernel module (and make it load at boot)
sudo modprobe uinput
echo uinput | sudo tee /etc/modules-load.d/uinput.conf

# Let your user access /dev/uinput via a udev rule
echo 'KERNEL=="uinput", GROUP="input", MODE="0660"' | sudo tee /etc/udev/rules.d/99-uinput.rules
sudo udevadm control --reload-rules && sudo udevadm trigger

# Add yourself to the input group, then LOG OUT and back in
sudo usermod -aG input "$USER"
```
After logging back in, `evdev` (installed by `requirements.txt`) can create the virtual keyboard without root.

Confirm the package imports:
```bash
python3 -c "import pyautogui; print(pyautogui.__version__)"
```
(Use `python` instead of `python3` on Windows.)

---

## Step 4 — Test the script (visible)

Run it in a terminal so you can see the messages:

```bash
python3 mimi.py        # Windows: python mimi.py
```

You should see something like:

```text
mimi is running on Linux...
Safe-key keep-awake starts after 2 minutes of inactivity.
Safe keys (random each press): f15, f16, ctrl, shift
```

Leave the computer idle for 2 minutes — it should print when a safe key is pressed. Press `Ctrl+C` to stop.

---

## Step 5 — Run it in the background (hidden)

### Windows
Double-click `mimi.vbs`, or from PowerShell:
```powershell
wscript mimi.vbs
```
No window appears; it runs via `pythonw.exe`. `mimi.vbs` also acts as a watchdog and relaunches the script if it exits.

### macOS / Linux
Make the scripts executable once, then run:
```bash
chmod +x run_mimi.sh stop_mimi.sh
./run_mimi.sh
```
This launches mimi with `nohup` so it keeps running after you close the terminal. `mimi.py` restarts itself on crashes.

---

## Step 6 — Auto-start at login

### Windows
1. Press `Win + R`, type `shell:startup`, press Enter.
2. Create a shortcut to `mimi.vbs` in that folder (or run this in PowerShell):
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

### macOS (LaunchAgent)
Create `~/Library/LaunchAgents/com.mimi.keepawake.plist` with this content (edit the path to `mimi.py`):
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key><string>com.mimi.keepawake</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/&lt;YourName&gt;/mimi/mimi.py</string>
    </array>
    <key>RunAtLoad</key><true/>
    <key>KeepAlive</key><true/>
</dict>
</plist>
```
Then load it:
```bash
launchctl load ~/Library/LaunchAgents/com.mimi.keepawake.plist
```

### Ubuntu / Linux (systemd user service)
Create `~/.config/systemd/user/mimi.service` (edit the path to `mimi.py`):
```ini
[Unit]
Description=mimi keep-awake

[Service]
ExecStart=/usr/bin/python3 /home/<YourName>/mimi/mimi.py
Restart=always

[Install]
WantedBy=default.target
```
Then enable and start it:
```bash
systemctl --user daemon-reload
systemctl --user enable --now mimi.service
```

---

## How it works

1. Detects idle time with the right API for your OS (see Requirements).
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

Restart mimi after changing settings.

---

## Auto-restart on crash

- `mimi.py` catches errors and restarts itself after **5 seconds**.
- On Windows, `mimi.vbs` also relaunches the script if the process exits.
- On macOS/Linux, the LaunchAgent (`KeepAlive`) or systemd service (`Restart=always`) relaunches it at the OS level.

Crash details are written to **`mimi.log`**.

---

## Stop mimi

**Windows:**
```powershell
.\stop_mimi.ps1
```
Or in Task Manager, end **wscript.exe** (the watchdog) first, then **pythonw.exe**.

**macOS / Linux:**
```bash
./stop_mimi.sh
```
If you set up auto-start, also disable it:
```bash
# macOS
launchctl unload ~/Library/LaunchAgents/com.mimi.keepawake.plist
# Linux
systemctl --user disable --now mimi.service
```

To disable auto-start on Windows: delete `mimi.lnk` from `shell:startup`.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `python` / `python3` not found | Reinstall Python (enable PATH on Windows), reopen the terminal |
| `No module named pyautogui` | Run the Step 3 install command |
| Keys do nothing on **macOS** | Grant Accessibility permission to Terminal/Python |
| Ghost key does nothing on **Linux** (esp. Wayland) | Do the `/dev/uinput` setup in Step 3, then log out and back in; check `mimi.log` says `Linux key method: uinput (evdev)` |
| `PermissionError` on `/dev/uinput` | You are not in the `input` group yet, or need to re-login after `usermod -aG input` |
| `xprintidle: command not found` (Linux) | `sudo apt install xprintidle`, or install `libxss1` for the built-in method |
| Windows VBS does nothing | Confirm `pythonw.exe` works; run `python mimi.py` to see errors |
| Crashes repeat | Check `mimi.log` for the error at the bottom |

---

## Finish checklist

- [ ] Python installed and on PATH
- [ ] `pip install -r requirements.txt` succeeded (plus system packages on Linux)
- [ ] macOS: Accessibility permission granted / Linux: on an X11 session
- [ ] `python mimi.py` works when tested
- [ ] Background launcher works (`mimi.vbs` or `run_mimi.sh`)
- [ ] (Optional) Auto-start configured for your OS
