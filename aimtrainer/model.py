"""Game rules and simulation. No display, audio, filesystem, or Pygame dependency."""
from dataclasses import dataclass, field, asdict
from datetime import date
import hashlib
import math
import random

MODES = {
    "classic": ("Classic", "The original challenge, refined.", "60-second score attack"),
    "precision": ("Precision", "Small targets. Deliberate shots.", "Accuracy before speed"),
    "tracking": ("Tracking", "Stay with a moving target.", "Hold left click to track"),
    "survival": ("Survival", "Keep your streak. Protect your lives.", "Progressive endurance"),
    "practice": ("Practice", "Your pace. Your training ground.", "Unlimited, configurable"),
}
DIFFICULTIES = ("Easy", "Medium", "Hard")
ARENA = (34.0, 130.0, 1372.0, 666.0)
STEP = 1 / 120


@dataclass
class Settings:
    difficulty: str = "Medium"
    duration: int = 60
    crosshair: str = "Cross"
    crosshair_size: int = 14
    crosshair_color: str = "Mint"
    volume: int = 50
    particles: bool = True
    screen_shake: bool = True
    reduced_motion: bool = False
    target_radius: int = 28
    spawn_interval: float = 0.65
    fps: int = 120

    @classmethod
    def from_dict(cls, data):
        """Validate persisted preferences rather than trusting arbitrary JSON types."""
        defaults = cls()
        if not isinstance(data, dict):
            return defaults
        options = {"difficulty": DIFFICULTIES, "duration": (30, 60, 90, 120),
                   "crosshair": ("Cross", "Dot", "Circle", "Cross + dot"),
                   "crosshair_size": (8, 14, 20, 26), "crosshair_color": ("Mint", "White", "Coral", "Gold"),
                   "volume": (0, 25, 50, 75, 100), "target_radius": (18, 28, 40, 54),
                   "spawn_interval": (0.4, 0.65, 0.9, 1.2), "fps": (60, 120, 144)}
        for key, choices in options.items():
            value = data.get(key)
            if type(value) is type(choices[0]) and value in choices:
                setattr(defaults, key, value)
        for key in ("particles", "screen_shake", "reduced_motion"):
            if type(data.get(key)) is bool:
                setattr(defaults, key, data[key])
        return defaults


def daily_seed(day=None):
    return int.from_bytes(hashlib.sha256((day or date.today()).isoformat().encode()).digest()[:8], "big")


@dataclass
class Target:
    x: float
    y: float
    radius: float
    lifetime: float
    born: float
    age: float = 0

    @property
    def visible_radius(self):
        # Grow/shrink is based on active simulation time, never on rendered frames.
        t = self.age / self.lifetime
        return self.radius * min(1.0, 0.5 + t * 5, max(0.0, (1 - t) * 4))

    def contains(self, pos):
        return pos is not None and math.dist((self.x, self.y), pos) <= self.visible_radius


class Session:
    def __init__(self, mode="classic", settings=None, seed=None, daily=False):
        if mode not in MODES:
            raise ValueError("Unknown game mode")
        self.settings = Settings.from_dict(asdict(settings or Settings()))
        self.daily = bool(daily)
        self.challenge_date = date.today().isoformat() if daily else None
        # The daily challenge is identical across profiles and settings for that date.
        if daily:
            mode = "precision"
            self.settings = Settings(difficulty="Medium", duration=60)
            seed = daily_seed() if seed is None else seed
        self.mode = mode
        self.seed = seed if seed is not None else random.SystemRandom().randrange(2**63)
        self.rng = random.Random(self.seed)
        self.elapsed = 0.0
        self.accumulator = 0.0
        self.hits = self.shots = self.misses = self.expired = self.score = 0
        self.combo = self.best_combo = 0
        self.last_hit = -100.0
        self.lives = 10
        self.targets = []
        self.hit_times = []
        self.tracked = self.held = 0.0
        self.finished = False
        self.reason = ""
        self.next_spawn = 0.0
        self.events = []
        self.track_point = (720.0, 450.0)
        self.track_start = (self.rng.uniform(100, 900), self.rng.uniform(80, 420))

    @property
    def multiplier(self):
        return min(8, 1 + max(0, self.combo - 1) // 3)

    @property
    def accuracy(self):
        if self.mode == "tracking":
            return 100 * self.tracked / self.held if self.held else 0.0
        return 100 * self.hits / self.shots if self.shots else 0.0

    @property
    def duration(self):
        return None if self.mode in ("practice", "survival") else (60 if self.mode == "classic" else self.settings.duration)

    def interval(self):
        base = {"Easy": 0.85, "Medium": 0.65, "Hard": 0.48}[self.settings.difficulty]
        if self.mode == "practice":
            return self.settings.spawn_interval
        if self.mode == "survival":
            return max(0.22, base / (1 + self.elapsed / 45))
        return base

    def spawn(self):
        radius = {"Easy": 38, "Medium": 30, "Hard": 23}[self.settings.difficulty]
        if self.mode == "precision":
            radius *= 0.62
        if self.mode == "practice":
            radius = self.settings.target_radius
        lifetime = {"Easy": 3.2, "Medium": 2.5, "Hard": 1.9}[self.settings.difficulty]
        if self.mode == "survival":
            lifetime = max(0.75, lifetime / (1 + self.elapsed / 70))
        x, y, width, height = ARENA
        # Reject overlapping placements; bounded attempts prevent a busy loop.
        for _ in range(40):
            px = self.rng.uniform(x + radius + 8, x + width - radius - 8)
            py = self.rng.uniform(y + radius + 8, y + height - radius - 8)
            if all(math.dist((px, py), (t.x, t.y)) > radius + t.radius + 14 for t in self.targets):
                self.targets.append(Target(px, py, radius, lifetime, self.elapsed))
                return

    def update(self, dt, pointer=None, holding=False):
        if self.finished or not math.isfinite(dt) or dt <= 0:
            return
        self.accumulator += dt
        # Fixed simulation steps produce consistent lifetimes and motion at 60/120/144 FPS.
        while self.accumulator + 1e-10 >= STEP and not self.finished:
            self.accumulator -= STEP
            self._step(pointer, holding)

    def _step(self, pointer, holding):
        self.elapsed += STEP
        if self.elapsed - self.last_hit > 0.65:
            self.combo = 0
        if self.mode == "tracking":
            speed = {"Easy": 145, "Medium": 210, "Hard": 285}[self.settings.difficulty]
            def bounce(value, span):
                return span - abs(value % (2 * span) - span)
            x, y, w, h = ARENA
            self.track_point = (x + 40 + bounce(self.track_start[0] + self.elapsed * speed, w - 80),
                                y + 40 + bounce(self.track_start[1] + self.elapsed * speed * 0.64, h - 80))
            if holding:
                self.held += STEP
                radius = {"Easy": 42, "Medium": 32, "Hard": 24}[self.settings.difficulty]
                if pointer is not None and math.dist(pointer, self.track_point) <= radius:
                    self.tracked += STEP
            self.score = round(self.tracked * 100)
        else:
            if self.elapsed + 1e-9 >= self.next_spawn:
                self.spawn()
                self.next_spawn = self.elapsed + self.interval()
            for target in self.targets[:]:
                target.age = self.elapsed - target.born
                if target.age >= target.lifetime:
                    self.targets.remove(target)
                    self.expired += 1
                    self.combo = 0
                    self.events.append(("expired", (target.x, target.y)))
                    if self.mode != "practice":
                        self.lives = max(0, self.lives - 1)
        if self.lives <= 0:
            self.finish("Out of lives")
        elif self.duration is not None and self.elapsed + 1e-9 >= self.duration:
            self.elapsed = float(self.duration)
            self.finish("Session complete")

    def shoot(self, pos, button=1):
        if self.finished or self.mode == "tracking" or button != 1 or pos is None:
            return None
        x, y, w, h = ARENA
        if not (x <= pos[0] <= x + w and y <= pos[1] <= y + h):
            return None
        self.shots += 1
        for target in reversed(self.targets):
            if target.contains(pos):
                self.targets.remove(target)
                self.hits += 1
                self.combo = self.combo + 1 if self.elapsed - self.last_hit <= 0.65 else 1
                self.best_combo = max(self.best_combo, self.combo)
                self.last_hit = self.elapsed
                self.hit_times.append(max(0.0, self.elapsed - target.born) * 1000)
                self.score += (150 if self.mode == "precision" else 100) * self.multiplier
                self.events.append(("hit", (target.x, target.y)))
                return "hit"
        self.misses += 1
        self.combo = 0
        if self.mode != "practice":
            self.lives = max(0, self.lives - 1)
            if self.lives == 0:
                self.finish("Out of lives")
        self.events.append(("miss", pos))
        return "miss"

    def finish(self, reason="Practice ended"):
        self.finished = True
        self.reason = reason

    def summary(self):
        return {"mode": self.mode, "difficulty": self.settings.difficulty, "duration": self.duration,
                "elapsed": round(self.elapsed, 3), "score": self.score, "hits": self.hits,
                "shots": self.shots, "misses": self.misses, "expired": self.expired,
                "accuracy": round(self.accuracy, 2), "best_combo": self.best_combo,
                "average_hit_ms": round(sum(self.hit_times) / len(self.hit_times), 1) if self.hit_times else None,
                "targets_per_second": round(self.hits / self.elapsed, 3) if self.elapsed else 0,
                "tracked_seconds": round(self.tracked, 3), "held_seconds": round(self.held, 3),
                "daily": self.daily, "seed": self.seed, "reason": self.reason,
                "challenge_date": self.challenge_date,
                "radius": self.settings.target_radius if self.mode == "practice" else None,
                "interval": self.settings.spawn_interval if self.mode == "practice" else None,
                "version": "2.0.0"}


def board_key(row):
    """Only compare runs with the same mode, difficulty and duration."""
    daily = f"daily:{row.get('challenge_date') or row.get('date', '')[:10]}" if row.get("daily") else row["mode"]
    return f"{daily}:{row['difficulty']}:{row.get('duration')}"


def achievement_ids(rows):
    earned = set()
    for row in rows:
        if row.get("hits", 0) >= 1:
            earned.add("first_hit")
        if row.get("shots", 0) >= 20 and row.get("accuracy", 0) >= 90 and row.get("mode") != "tracking":
            earned.add("sharp_eye")
        if row.get("best_combo", 0) >= 10:
            earned.add("in_flow")
        if row.get("mode") == "survival" and row.get("elapsed", 0) >= 60:
            earned.add("survivor")
        if row.get("mode") == "tracking" and row.get("tracked_seconds", 0) >= 15:
            earned.add("steady_hand")
        if row.get("daily") and row.get("reason") == "Session complete":
            earned.add("daily_done")
    if len(rows) >= 10:
        earned.add("consistent")
    return earned


ACHIEVEMENTS = {"first_hit": ("First contact", "Land your first hit."),
                "sharp_eye": ("Sharp eye", "90% accuracy with at least 20 shots."),
                "in_flow": ("In the flow", "Build a 10-hit combo."),
                "survivor": ("Survivor", "Reach 60 seconds in Survival."),
                "steady_hand": ("Steady hand", "Track on target for 15 seconds."),
                "daily_done": ("Daily discipline", "Finish a daily challenge."),
                "consistent": ("Keep showing up", "Save 10 training sessions.")}
