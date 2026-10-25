# Version 2.0 validation

Verified on 25 October 2026 using Python 3.12.14, pygame-ce 2.5.8 and SDL 2.32.10 in Linux. The environment has no physical display/audio device, so rendered game and event-flow checks used SDL dummy drivers.

## Executed checks

| Check | Observed result |
|---|---|
| `python -m pytest -q` | **75 passed** |
| Pure simulation timing | Matching tracking timing/positions at 30, 60, 120, 144 and 240 update rates; chunked spawning matches the same elapsed single update |
| Rules | Left-button/arena bounds, hit/miss/expiry, life exhaustion, practice exemption, precision size/points, combo reset/cap, seeded placement, daily settings and achievements |
| Tracking | Held vs on-target time, no-shot behavior, score, off-target accuracy and duration completion |
| Persistence | Profile isolation, valid settings, restart roundtrip, bounded history, grouped bests, CSV formula protection, atomic-write failures and damaged-file recovery |
| UI/state | Pause freezes time/combo/target age/effects; focus loss pauses; resized clicks use event positions; countdown, results/restart/quit, keyboard input and profile creation |
| Display | Logical coordinate mapping, letterbox rejection, fullscreen/windowed switching under dummy SDL and button bounds |
| Audio | Startup survives a forced audio failure; generated sound bank initializes under SDL dummy audio |
| `python tools/smoke_check.py` | Passed; real posted SDL menu events, five modes, tracking, pause/resume, restart, profiles, daily, statistics, achievements, resized coordinates and queued-quit public run loop |
| Rendered screens | Training, settings, profiles, statistics, achievements, help, all five modes, pause and results rendered; main layouts visually reviewed |
| Launch interface | `python aim_trainer.py --help` succeeded |
| Packaging | A version 2.0.0 wheel built successfully; source ZIP excludes environments, caches, player saves and temporary test artifacts |
| Preservation | Five original Python modules and three original coursework documents retained byte for byte |

The smoke script stores test data in a temporary directory and does not change the normal player data directory. The screenshots in documentation show test sessions; the distributed game starts without that test history.

## Scoped renderer measurement

The smoke script measured **300 frames after 60 warm-up frames**, including Session update, drawing, scaling and the SDL display call. The window was 1000 × 800, rendering a 1440 × 900 logical canvas in Practice. This run observed:

- Median CPU update/render duration: **2.309 ms**.
- p95 CPU update/render duration: **3.698 ms**.

These are headless SDL dummy-backend measurements, not physical-display FPS, input-to-photon latency, GPU performance or a speed comparison with v1.0. Actual desktop results vary. Frame-cap sleeping is excluded from the measured interval. The script can reproduce the method and record a new report; it need not reproduce identical numbers.

## Reproduce

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
python tools/smoke_check.py --screenshots ./qa-screens --report ./qa-result.json
```

The GitHub workflow is configured for Linux/Windows and Python 3.11–3.13. It has not been observed running in the user's GitHub repository.

## Practical verification limits

Native Windows/macOS play, actual speakers, high-DPI desktop scaling, physical mouse latency and a physical fullscreen monitor transition were not tested in this environment. The batch/shell startup scripts are provided; the Windows batch script was not executed on Windows here. Test those on the demonstration machine before presenting.

The game has no online accounts, multiplayer, anti-cheat, cloud backup or packaged Windows executable. It is not a clinical measurement system or a proven intervention for another game's performance. Profiles are local and editable. Run one application instance per data directory to avoid competing writes.

Original v1.0 is archived for comparison, not certified as bug-free or revalidated in full. Its Word/PDF reports retain their original content and scope.
