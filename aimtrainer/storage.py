"""Atomic local JSON persistence, bounded records, recovery and safe CSV export."""
import csv
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import tempfile
import uuid
from .model import Settings, board_key, achievement_ids


def data_directory():
    if os.environ.get("AIMTRAINER_DATA"):
        return Path(os.environ["AIMTRAINER_DATA"]).expanduser()
    if os.name == "nt":
        return Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "UltimateAimTrainer"
    return Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local/share"))) / "ultimate-aim-trainer"


def blank():
    return {"schema": 2, "active": "Player", "profiles": {"Player": {"settings": {}, "sessions": []}}}


class Store:
    def __init__(self, directory=None):
        self.directory = Path(directory) if directory is not None else data_directory()
        self.path = self.directory / "progress.json"
        self.notice = ""
        self.data = blank()
        self.load()

    def load(self):
        if not self.path.exists():
            return
        try:
            if self.path.stat().st_size > 10_000_000:
                raise ValueError("Save too large")
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict) or raw.get("schema") != 2 or not isinstance(raw.get("profiles"), dict):
                raise ValueError("Unknown save format")
            profiles = {}
            for name, profile in list(raw["profiles"].items())[:20]:
                if not isinstance(name, str) or not 1 <= len(name.strip()) <= 24 or not isinstance(profile, dict):
                    continue
                sessions = profile.get("sessions", [])
                if not isinstance(sessions, list):
                    sessions = []
                valid = []
                for row in sessions[-1000:]:
                    if not isinstance(row, dict) or row.get("mode") not in {"classic", "precision", "tracking", "survival", "practice"}:
                        continue
                    if row.get("difficulty") not in ("Easy", "Medium", "Hard"):
                        continue
                    if not all(isinstance(row.get(k, 0), (int, float)) and not isinstance(row.get(k), bool) and math.isfinite(row.get(k, 0)) and 0 <= row.get(k, 0) <= 10**12 for k in ("score", "elapsed", "accuracy", "hits", "shots", "misses", "expired", "best_combo", "targets_per_second", "tracked_seconds", "held_seconds")):
                        continue
                    if row.get("accuracy", 0) > 100 or not isinstance(row.get("date"), str):
                        continue
                    if any(k not in row for k in ("score", "elapsed", "accuracy")):
                        continue
                    if row.get("duration") not in (None, 30, 60, 90, 120) or type(row.get("daily", False)) is not bool:
                        continue
                    if not isinstance(row.get("reason", ""), str):
                        continue
                    if row.get("average_hit_ms") is not None and (not isinstance(row["average_hit_ms"], (int, float)) or not math.isfinite(row["average_hit_ms"]) or row["average_hit_ms"] < 0):
                        continue
                    try:
                        datetime.fromisoformat(row["date"])
                    except ValueError:
                        continue
                    valid.append(row)
                profiles[name] = {"settings": vars(Settings.from_dict(profile.get("settings"))), "sessions": valid}
            if not profiles:
                raise ValueError("No readable profiles")
            self.data = {"schema": 2, "profiles": profiles, "active": raw.get("active") if raw.get("active") in profiles else next(iter(profiles))}
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            # Keep the damaged bytes for inspection; never silently destroy them.
            try:
                backup = self.directory / f"progress-recovery-{uuid.uuid4().hex[:8]}.json"
                backup.write_bytes(self.path.read_bytes())
                self.notice = "Unreadable save preserved as a recovery file. A fresh profile is ready."
            except OSError:
                self.notice = "Could not read saved progress. Using a temporary profile."

    @property
    def active(self):
        return self.data["active"]

    @property
    def profile(self):
        return self.data["profiles"][self.active]

    @property
    def settings(self):
        return Settings.from_dict(self.profile["settings"])

    @property
    def sessions(self):
        return self.profile["sessions"]

    def save(self):
        filename = None
        try:
            self.directory.mkdir(parents=True, exist_ok=True)
            fd, filename = tempfile.mkstemp(prefix="progress-", suffix=".tmp", dir=self.directory)
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2, allow_nan=False)
                f.flush()
                os.fsync(f.fileno())
            os.replace(filename, self.path)
            return True
        except (OSError, ValueError):
            self.notice = "Progress is kept for this visit; the save folder is not writable."
            return False
        finally:
            if filename:
                try:
                    Path(filename).unlink(missing_ok=True)
                except OSError:
                    pass

    def set_settings(self, settings):
        self.profile["settings"] = vars(Settings.from_dict(vars(settings)))
        return self.save()

    def select(self, name):
        if name not in self.data["profiles"]:
            raise ValueError("Unknown profile")
        self.data["active"] = name
        return self.save()

    def create(self, name):
        name = " ".join(name.split())
        if not 1 <= len(name) <= 24 or any(ord(c) < 32 for c in name):
            raise ValueError("Use a name of 1 to 24 readable characters.")
        if any(n.casefold() == name.casefold() for n in self.data["profiles"]):
            raise ValueError("That profile name already exists.")
        if len(self.data["profiles"]) >= 20:
            raise ValueError("The local profile limit is 20.")
        self.data["profiles"][name] = {"settings": {}, "sessions": []}
        self.data["active"] = name
        return self.save()

    def add(self, row):
        row = {**row, "id": uuid.uuid4().hex, "date": datetime.now(timezone.utc).isoformat()}
        previous = [r for r in self.sessions if board_key(r) == board_key(row) and r.get("reason") != "Ended early" and r["score"] > 0]
        self.sessions.append(row)
        self.profile["sessions"] = self.sessions[-1000:]
        saved = self.save()
        eligible = row["mode"] != "practice" and row["reason"] != "Ended early" and row["score"] > 0
        return row, eligible and (not previous or row["score"] > max(r["score"] for r in previous)), saved

    def bests(self):
        best = {}
        for row in self.sessions:
            if row["mode"] == "practice" or row.get("reason") == "Ended early" or row["score"] <= 0:
                continue
            key = board_key(row)
            if key not in best or row["score"] > best[key]["score"]:
                best[key] = row
        return sorted(best.values(), key=lambda r: (r["mode"], r["difficulty"], r.get("duration") or 0))

    def export(self):
        self.directory.mkdir(parents=True, exist_ok=True)
        path = self.directory / "exports" / f"training-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:4]}.csv"
        path.parent.mkdir(exist_ok=True)
        fields = ["date", "mode", "difficulty", "duration", "elapsed", "score", "accuracy", "hits", "shots", "misses", "expired", "best_combo", "average_hit_ms", "targets_per_second", "tracked_seconds", "held_seconds", "daily", "challenge_date", "seed", "reason", "version"]
        with path.open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fields, extrasaction="ignore")
            writer.writeheader()
            for row in self.sessions:
                writer.writerow({k: ("'" + str(row.get(k, "")) if str(row.get(k, "")).lstrip().startswith(("=", "+", "-", "@")) else row.get(k, "")) for k in fields})
        return path
