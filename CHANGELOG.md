# Changelog

## 2.0.0 — 25 October 2026

- Rebuilt gameplay around one event loop and explicit screen states.
- Fixed pause timing, Options/Back/Quit flow, expired-target life penalties, stale multipliers and click-position handling.
- Added fixed-step simulation with time-based target motion and lifetimes.
- Added Classic, Precision, Tracking, Survival and configurable unlimited Practice.
- Added a date-seeded daily Precision challenge, three-second countdown and focus-loss pause.
- Replaced the UI with a dark training dashboard, mode cards, clearer HUD, pause overlay and richer results.
- Added resizable/fullscreen display with letterbox-aware mouse coordinates.
- Added crosshair customization, generated sounds, volume controls, particles and reduced motion.
- Added local profiles, isolated preferences/history, grouped personal bests, accuracy charts, achievements and CSV export.
- Added validated atomic saves, damaged-file recovery and graceful write/audio failure handling.
- Added automated rules/storage/UI regression tests and a real SDL smoke check with a scoped renderer measurement.
- Added installation scripts, packaging metadata, CI configuration, architecture/play documentation and a complete v1/v2 README.
- Preserved the five original source files and three original coursework documents byte for byte, excluding the old virtual environment.

## 1.0 — original submitted coursework

- Five Python source modules using Pygame.
- Growing/shrinking circular targets, three difficulties, 60-second sessions, lives, combos, particles and a basic menu/results flow.
- Original Word/PDF submission and PDF how-to-play guide supplied with the source.
- Known source-level timing, navigation, expiry/multiplier and audio-startup issues are documented in the README version comparison.
