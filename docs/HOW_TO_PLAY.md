# Play and presentation guide

1. Install `requirements.txt` in a Python 3.11+ virtual environment and run `python aim_trainer.py`.
2. Open Profiles if you want a separate name/settings/history. The initial Player profile is ready immediately.
3. In Settings, choose difficulty, Precision/Tracking duration, crosshair and comfort preferences. Classic always lasts 60 seconds.
4. Return to Training, select a mode and press Start. The game counts down from three.
5. Click targets in the arena. In Tracking, hold left click and follow the moving target.
6. Press Escape to pause. Resume freezes no extra active time; End session saves an early result; Restart starts a new attempt.
7. Review results. R restarts the same mode. Choose another mode returns to Training.
8. Open Statistics to filter history, view accuracy trends, grouped personal bests and achievements. Export history to CSV if needed.
9. Play Daily for the date-seeded Precision/Medium/60-second challenge.

## Suggested final-project demonstration

- Explain the original v1 problems using the README comparison and `legacy/v1.0` source.
- Show the new menu, a customized crosshair and an isolated profile.
- Start Classic; hit targets, miss deliberately and explain the independent missed/expired counts.
- Pause for several seconds and show that active time/targets remain frozen.
- Demonstrate Tracking and explain accuracy vs total on-target time.
- End Practice explicitly, show that it saves without life penalties, then inspect Statistics and CSV export.
- Show the pure model tests and the save/recovery design. Avoid calling the result a clinical reaction-time score or guaranteed improvement in another game.

The original submission reports are archived under `docs/original_v1.0`. They have not been rewritten to claim features that were absent from the original coursework. Current behavior, scoring and limitations are documented in the root README and architecture guide.
