# Start here

This is **Ultimate Aim Trainer 2.0**, a Python/Pygame desktop game.

## Windows

1. Install Python 3.11 or newer.
2. Extract the ZIP completely.
3. Open the extracted `UltimateAimTrainer-2.0` folder.
4. Double-click `start_windows.bat`.
5. Choose a mode and click Start. A three-second countdown begins.

If the launcher needs help, open a terminal in that folder and run:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe aim_trainer.py
```

## Linux / macOS

```bash
sh start_unix.sh
```

The initial package installation needs internet; the installed game works offline. The game is not a website and does not require Flask, a browser or a GPU.

ESC pauses. F11 toggles fullscreen. In Tracking, hold left click; in other modes, click targets. End Practice through the pause menu to save it. Results and settings save outside the source folder; see How to play inside the game for the exact path.

Read `README.md` for modes, scoring, settings, the full v1/v2 comparison, architecture and troubleshooting. Original source is in `legacy/v1.0`; original submission reports are in `docs/original_v1.0`. The new game does not import the archived modules.
