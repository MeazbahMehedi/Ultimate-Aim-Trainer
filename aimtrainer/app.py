"""One event loop, explicit screens, logical coordinates and non-blocking overlays."""
import argparse
from collections import deque
from dataclasses import asdict
from datetime import date
import math
from pathlib import Path
import random
import time
import pygame
from . import __version__
from .audio import Audio
from .model import Session, Settings, MODES, ARENA, ACHIEVEMENTS, achievement_ids, board_key
from .storage import Store
from .ui import Painter, WIDTH, HEIGHT, BG, SIDE, PANEL, RAISED, LINE, TEXT, MUTED, ACCENT, CYAN, CORAL, GOLD


class Game:
    def __init__(self, directory=None, size=(1280, 800), silent=False):
        pygame.display.init()
        pygame.font.init()
        pygame.display.set_caption("Ultimate Aim Trainer 2.0")
        self.window = pygame.display.set_mode(size, pygame.RESIZABLE)
        self.windowed_size = size
        self.fullscreen = False
        self.ui = Painter()
        icon = pygame.Surface((64, 64));icon.fill(BG)
        pygame.draw.circle(icon, ACCENT, (32, 32), 25, 5)
        pygame.draw.circle(icon, ACCENT, (32, 32), 9)
        pygame.display.set_icon(icon)
        self.store = Store(directory)
        self.settings = self.store.settings
        self.audio = Audio() if not silent else None
        self.screen = "training"
        self.running = True
        self.mode = "classic"
        self.session = None
        self.last_result = None
        self.result_saved = False
        self.personal_best = False
        self.new_achievements = set()
        self.focus = -1
        self.pointer = (0.0, 0.0)
        self.holding = False
        self.countdown = 0.0
        self.history_page = 0
        self.history_mode = "all"
        self.statistics_tab = "History"
        self.profile_input = ""
        self.profile_editing = False
        self.message = self.store.notice
        self.message_until = 8.0 if self.message else 0.0
        self.uptime = 0.0
        self.effects = []
        self.flash = 0.0
        self.frame_times = deque(maxlen=600)
        self.effect_rng = random.Random(17)
        self.viewport = (0, 0, WIDTH, HEIGHT)
        self.render()

    def notify(self, text, seconds=5):
        self.message, self.message_until = text, self.uptime + seconds

    def sound(self, name):
        if self.audio:
            self.audio.play(name, self.settings.volume)

    def map_point(self, point):
        x, y, w, h = self.viewport
        if not (x <= point[0] < x + w and y <= point[1] < y + h):
            return None
        return ((point[0] - x) * WIDTH / w, (point[1] - y) * HEIGHT / h)

    def show(self, screen):
        self.screen = screen
        self.focus = -1
        self.holding = False
        self.profile_editing = False

    def start(self, daily=False):
        self.session = Session(self.mode, self.settings, daily=daily)
        self.effects.clear()
        self.flash = 0
        self.countdown = 3.0
        self.result_saved = False
        self.new_achievements = set()
        self.show("countdown")

    def finish(self):
        if self.result_saved:
            return
        before = achievement_ids(self.store.sessions)
        self.last_result, self.personal_best, saved = self.store.add(self.session.summary())
        self.new_achievements = achievement_ids(self.store.sessions) - before
        self.result_saved = True
        self.show("results")
        self.sound("finish")
        if not saved:
            self.notify(self.store.notice, 12)

    def toggle_fullscreen(self):
        try:
            if not self.fullscreen:
                self.windowed_size = self.window.get_size()
                self.window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            else:
                self.window = pygame.display.set_mode(self.windowed_size, pygame.RESIZABLE)
            self.fullscreen = not self.fullscreen
        except pygame.error:
            self.notify("Fullscreen is unavailable on this display. Windowed mode remains ready.")

    def action(self, action):
        self.sound("click")
        if isinstance(action, tuple):
            key, value = action
            if key == "mode":
                self.mode = value
            elif key == "setting":
                name, choices = value
                current = getattr(self.settings, name)
                setattr(self.settings, name, choices[(choices.index(current) + 1) % len(choices)])
                if not self.store.set_settings(self.settings):
                    self.notify(self.store.notice)
            elif key == "select_profile":
                self.store.select(value);self.settings = self.store.settings
                self.notify(f"Switched to {value}.")
            elif key == "page":
                self.history_page = max(0, self.history_page + value)
            elif key == "stats_tab":
                self.statistics_tab = value;self.history_page = 0
            return
        if action in ("training", "statistics", "profiles", "settings", "help"):
            self.show(action)
        elif action == "start":
            self.start()
        elif action == "daily":
            self.start(daily=True)
        elif action == "quit":
            self.running = False
        elif action == "pause":
            self.show("paused")
        elif action == "resume":
            self.show("playing")
        elif action == "restart":
            self.start(self.session.daily)
        elif action == "end":
            self.session.finish("Practice ended" if self.session.mode == "practice" else "Ended early")
            self.finish()
        elif action == "create_profile":
            try:
                saved = self.store.create(self.profile_input)
                self.settings = self.store.settings
                self.profile_input = ""
                self.profile_editing = False
                self.notify("Profile created." if saved else self.store.notice)
            except ValueError as exc:
                self.notify(str(exc))
        elif action == "edit_profile":
            self.profile_editing = True
            pygame.key.start_text_input()
        elif action == "export":
            try:
                self.store.export()
                self.notify("CSV saved in your data folder / exports. Open Help for the folder path.", 9)
            except OSError:
                self.notify("Could not export: check the data-folder write permission.")
        elif action == "filter":
            choices = ["all", *MODES]
            self.history_mode = choices[(choices.index(self.history_mode) + 1) % len(choices)]
            self.history_page = 0

    def handle(self, event):
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.VIDEORESIZE and not self.fullscreen:
            self.window = pygame.display.set_mode((max(640, event.w), max(400, event.h)), pygame.RESIZABLE)
            self.windowed_size = self.window.get_size()
            self.render()  # Coordinate mapping matches any following click in the event queue.
        elif event.type == pygame.WINDOWFOCUSLOST:
            self.holding = False
            if self.screen in ("playing", "countdown"):
                self.show("paused" if self.screen == "playing" else "ready")
        elif event.type == pygame.MOUSEMOTION:
            self.pointer = self.map_point(event.pos)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.holding = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.pointer = self.map_point(event.pos)
            self.holding = True
            if self.screen == "playing":
                if self.pointer and pygame.Rect(1275, 28, 125, 48).collidepoint(self.pointer):
                    self.show("paused")
                else:
                    self.session.shoot(self.pointer, event.button)
            elif self.screen == "profiles" and self.pointer and pygame.Rect(274, 258, 680, 58).collidepoint(self.pointer):
                self.action("edit_profile")
            else:
                for button in self.ui.buttons:
                    if self.pointer and button.rect.collidepoint(self.pointer):
                        self.action(button.action)
                        break
        elif event.type == pygame.TEXTINPUT and self.profile_editing:
            self.profile_input = (self.profile_input + "".join(c for c in event.text if c.isprintable()))[:24]
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F11:
                self.toggle_fullscreen()
            elif self.profile_editing:
                if event.key == pygame.K_BACKSPACE:
                    self.profile_input = self.profile_input[:-1]
                elif event.key == pygame.K_RETURN:
                    self.action("create_profile")
                elif event.key == pygame.K_ESCAPE:
                    self.profile_editing = False
            elif event.key == pygame.K_ESCAPE:
                if self.screen == "playing":
                    self.show("paused")
                elif self.screen == "paused":
                    self.show("playing")
                elif self.screen in ("countdown", "ready"):
                    self.show("training")
                elif self.screen != "training":
                    self.show("training")
            elif event.key == pygame.K_TAB:
                if self.ui.buttons:
                    self.focus = (self.focus + (-1 if event.mod & pygame.KMOD_SHIFT else 1)) % len(self.ui.buttons)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                if self.screen == "ready":
                    self.countdown = 3;self.show("countdown")
                elif self.focus >= 0 and self.focus < len(self.ui.buttons):
                    self.action(self.ui.buttons[self.focus].action)
            elif event.key == pygame.K_r and self.screen == "results":
                self.action("restart")

    def update(self, dt):
        self.uptime += dt
        self.ui.dt = dt
        if self.screen == "countdown":
            self.countdown -= dt
            if self.countdown <= 0:
                self.holding = False
                self.show("playing")
        elif self.screen == "playing":
            self.session.update(dt, self.pointer, self.holding)
            for kind, pos in self.session.events:
                if kind == "hit":
                    self.sound("hit")
                    if self.settings.particles and not self.settings.reduced_motion:
                        for _ in range(min(12, 120 - len(self.effects))):
                            angle = self.effect_rng.random() * math.tau
                            speed = self.effect_rng.uniform(65, 190)
                            self.effects.append([pos[0], pos[1], math.cos(angle) * speed, math.sin(angle) * speed, .45])
                elif kind == "miss":
                    self.sound("miss")
                    self.flash = .1 if self.settings.screen_shake and not self.settings.reduced_motion else 0
            self.session.events.clear()
            if self.session.finished:
                self.finish()
        if self.screen == "playing":
            for p in self.effects:
                p[0] += p[2] * dt;p[1] += p[3] * dt;p[4] -= dt
            self.effects = [p for p in self.effects if p[4] > 0]
            self.flash = max(0, self.flash - dt)

    def sidebar(self, title, subtitle):
        u = self.ui
        pygame.draw.rect(u.surface, SIDE, (0, 0, 226, HEIGHT))
        pygame.draw.line(u.surface, LINE, (226, 0), (226, HEIGHT))
        u.target((42, 47), 16)
        u.text("ULTIMATE", (72, 28), 17, TEXT, True)
        u.text("AIM TRAINER", (72, 49), 13, MUTED, True)
        u.text("TRAIN WITH INTENTION", (25, 115), 11, MUTED, True)
        for i, (key, label) in enumerate([("training", "Training"), ("statistics", "Statistics"), ("profiles", "Profiles"), ("settings", "Settings"), ("help", "How to play")]):
            y = 151 + i * 62
            if self.screen == key:
                u.panel((16, y, 194, 48), (36, 53, 46), False, 12)
                pygame.draw.rect(u.surface, ACCENT, (16, y + 12, 3, 24), border_radius=2)
            u.button((25, y + 3, 175, 42), label, key, small=True)
        u.panel((18, 686, 188, 108), PANEL)
        u.text("YOUR LOCAL PROFILE", (32, 702), 10, MUTED, True)
        u.fit(self.store.active, (32, 726), 160, 19, TEXT, True)
        u.text(f"{len(self.store.sessions)} sessions saved", (32, 758), 12, MUTED)
        u.text("OFFLINE  /  VERSION 2.0", (24, 851), 10, MUTED, True)
        u.text("WORKSPACE / " + self.screen.upper(), (274, 32), 11, MUTED, True)
        u.text(title, (274, 72), 36, TEXT, True)
        u.text(subtitle, (276, 124), 16, MUTED)
        pygame.draw.line(u.surface, LINE, (274, 161), (1390, 161))

    def training(self):
        self.sidebar("Find your focus.", "A little practice. A clearer aim. Make this session count.")
        u = self.ui
        u.panel((274, 184, 1118, 184), (25, 46, 44))
        u.text("PRECISION IS A PRACTICE", (300, 207), 11, ACCENT, True)
        u.text("Small targets. Big progress.", (300, 236), 30, TEXT, True)
        u.text("Five ways to sharpen your speed, accuracy and control.", (300, 282), 16, MUTED)
        u.text("Choose a mode below, then start your next run.", (300, 313), 14, MUTED)
        phase = 0 if self.settings.reduced_motion else self.uptime * .3
        for r in (37, 66, 91):
            pygame.draw.circle(u.surface, (49, 79, 67), (1252, 276), r, 1)
        u.target((1252, 276), 29)
        if not self.settings.reduced_motion:
            pygame.draw.circle(u.surface, CYAN, (int(1252 + math.cos(phase) * 66), int(276 + math.sin(phase) * 66)), 4)
        u.text("TRAINING MODES", (277, 391), 11, MUTED, True)
        for index, (key, (name, description, hint)) in enumerate(MODES.items()):
            col, row = index % 2, index // 2
            x, y = 274 + col * 567, 418 + row * 111
            selected = self.mode == key
            u.panel((x, y, 550, 96), (33, 49, 45) if selected else PANEL)
            if selected:
                pygame.draw.rect(u.surface, ACCENT, (x, y, 550, 96), 1, border_radius=18)
            u.text(f"0{index + 1}", (x + 18, y + 16), 13, ACCENT if selected else MUTED, True)
            u.text(name, (x + 60, y + 12), 22, TEXT, True)
            u.text(description, (x + 60, y + 46), 14, MUTED)
            u.text(hint, (x + 60, y + 69), 11, CYAN)
            u.button((x + 430, y + 27, 100, 40), "Selected" if selected else "Select", ("mode", key), selected, True)
        u.panel((841, 640, 550, 96), (31, 39, 53))
        u.text("DAILY CHALLENGE", (860, 652), 11, GOLD, True)
        u.text(date.today().strftime("%d %B %Y"), (860, 677), 19, TEXT, True)
        u.text("Same seed. Precision / Medium / 60 s.", (860, 708), 12, MUTED)
        u.button((1240, 663, 132, 45), "Play daily", "daily", small=True)
        u.text(self.settings.difficulty.upper() + "  /  " + ("60 seconds" if self.mode == "classic" else "No time limit" if self.mode in ("practice", "survival") else f"{self.settings.duration} seconds"), (278, 785), 13, MUTED, True)
        u.button((1065, 766, 326, 62), "Start " + MODES[self.mode][0] + "   >", "start", True)
        u.text("ESC pauses  ·  F11 fullscreen  ·  Tab + Enter navigates", (278, 850), 12, MUTED)

    def gameplay(self):
        u, s = self.ui, self.session
        x, y, w, h = ARENA
        u.panel((x, y, w, h), (15, 25, 32), True, 20)
        u.surface.set_clip(pygame.Rect(x + 1, y + 1, w - 2, h - 2))
        for gx in range(48, 1400, 48):
            for gy in range(145, 790, 48):
                pygame.draw.circle(u.surface, (28, 41, 49), (gx, gy), 1)
        if s.mode == "tracking":
            radius = {"Easy": 42, "Medium": 32, "Hard": 24}[s.settings.difficulty]
            on = self.holding and self.pointer and math.dist(self.pointer, s.track_point) <= radius
            u.target(s.track_point, radius, ACCENT if on else CYAN)
        else:
            for t in s.targets:
                u.target((t.x, t.y), t.visible_radius, ACCENT if s.mode != "precision" else CYAN, max(0, 1 - t.age / t.lifetime))
        for p in self.effects:
            pygame.draw.circle(u.surface, ACCENT, (int(p[0]), int(p[1])), max(1, int(p[4] * 8)))
        u.surface.set_clip(None)
        u.text("DAILY PRECISION" if s.daily else MODES[s.mode][0].upper(), (37, 25), 12, ACCENT, True)
        u.fit(s.settings.difficulty + "  /  " + self.store.active, (37, 55), 270, 15, MUTED)
        remaining = max(0, (s.duration - s.elapsed)) if s.duration is not None else s.elapsed
        clock_label = f"{int(remaining) // 60:02}:{int(remaining) % 60:02}"
        for label, value, px in [("TIME LEFT" if s.duration else "ACTIVE TIME", clock_label, 335), ("SCORE", f"{s.score:,}", 535), ("ACCURACY", f"{s.accuracy:.1f}%", 735), ("LIVES" if s.mode != "tracking" else "ON TARGET", ("Unlimited" if s.mode == "practice" else str(s.lives)) if s.mode != "tracking" else f"{s.tracked:.1f}s", 965)]:
            u.text(label, (px, 25), 10, MUTED, True)
            u.text(value, (px, 49), 30, TEXT, True)
        u.button((1275, 28, 125, 48), "Pause", "pause", small=True)
        progress = s.elapsed / s.duration if s.duration else min(1, s.elapsed % 60 / 60)
        pygame.draw.rect(u.surface, LINE, (36, 106, 1366, 3), border_radius=2)
        pygame.draw.rect(u.surface, ACCENT, (36, 106, int(1366 * progress), 3), border_radius=2)
        u.text("Hold LEFT CLICK and follow the target" if s.mode == "tracking" else "LEFT CLICK to hit   /   missed shots and expired targets cost a life" if s.mode != "practice" else "Unlimited practice   /   ESC > End session to save", (40, 819), 14, MUTED)
        u.text(f"{s.hits} HITS   {s.misses} MISSES   {s.expired} EXPIRED", (40, 853), 12, MUTED, True)
        u.text(f"COMBO  {s.combo}     MULTIPLIER  x{s.multiplier}", (1395, 824), 17, ACCENT, True, "right")
        if self.screen == "playing":
            u.crosshair(self.pointer, self.settings)

    def overlay(self):
        u = self.ui
        dim = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA);dim.fill((5, 11, 18, 200));u.surface.blit(dim, (0, 0))
        # Pause is a state: gameplay, spawn scheduling and visual-effect age are frozen.
        u.buttons = []
        if self.screen in ("countdown", "ready"):
            u.text("TAKE A BREATH. FIND YOUR FOCUS.", (720, 322), 15, ACCENT, True, "center")
            u.text(str(max(1, math.ceil(self.countdown))) if self.screen == "countdown" else "Ready when you are.", (720, 370), 98 if self.screen == "countdown" else 40, TEXT, True, "center")
            u.text("Your session starts after the countdown." if self.screen == "countdown" else "Press Enter to restart the countdown.", (720, 505), 17, MUTED, False, "center")
            u.text("ESC returns to Training", (720, 553), 13, MUTED, False, "center")
        else:
            u.panel((450, 222, 540, 450), PANEL)
            u.text("PAUSED", (720, 256), 12, ACCENT, True, "center")
            u.text("Keep your place.", (720, 292), 38, TEXT, True, "center")
            u.text("The clock, targets and combo are frozen.", (720, 350), 16, MUTED, False, "center")
            for y, label, act, primary in [(406, "Resume training", "resume", True), (476, "Restart run", "restart", False), (546, "End session & save", "end", False)]:
                u.button((503, y, 434, 54), label, act, primary)
            u.text("ESC resumes", (720, 625), 13, MUTED, False, "center")

    def results(self):
        u, row = self.ui, self.last_result
        self.sidebar("A session well spent.", "Review the evidence. Reset your focus. Go again.")
        u.panel((274, 191, 1118, 180), (25, 46, 44))
        u.text(("PERSONAL BEST" if self.personal_best and row["mode"] != "practice" else "SESSION RECORDED") + ("  /  DAILY" if row["daily"] else ""), (301, 215), 12, ACCENT, True)
        u.text(f"{row['score']:,}", (300, 246), 62, TEXT, True)
        u.text("POINTS", (535, 281), 12, MUTED, True)
        u.text(MODES[row["mode"]][0] + "  /  " + row["difficulty"], (1360, 234), 21, TEXT, True, "right")
        u.text(row["reason"], (1360, 278), 17, MUTED, False, "right")
        u.text(f"{row['elapsed']:.1f}s active time", (1360, 314), 14, CYAN, False, "right")
        values = [("Accuracy", f"{row['accuracy']:.1f}%"), ("Hits / shots", f"{row['hits']} / {row['shots']}"), ("Missed / expired", f"{row['misses']} / {row['expired']}"), ("Best combo", str(row["best_combo"])), ("Average hit time", f"{row['average_hit_ms']:.0f} ms" if row["average_hit_ms"] is not None else "—"), ("On-target time" if row["mode"] == "tracking" else "Targets / second", f"{row['tracked_seconds']:.1f} s" if row["mode"] == "tracking" else f"{row['targets_per_second']:.2f}")]
        if row["mode"] == "tracking":
            coverage = 100 * row["tracked_seconds"] / row["elapsed"] if row["elapsed"] else 0
            values = [("Tracking accuracy", f"{row['accuracy']:.1f}%"),
                      ("On-target time", f"{row['tracked_seconds']:.2f} s"),
                      ("Time holding", f"{row['held_seconds']:.2f} s"),
                      ("Session coverage", f"{coverage:.1f}%"),
                      ("Points / on-target second", "100"), ("Difficulty", row["difficulty"])]
        for i, (label, value) in enumerate(values):
            x, y = 274 + i % 3 * 379, 397 + i // 3 * 115
            u.panel((x, y, 360, 98))
            u.text(label, (x + 20, y + 15), 13, MUTED)
            u.text(value, (x + 20, y + 43), 28, TEXT, True)
        names = ", ".join(ACHIEVEMENTS[x][0] for x in sorted(self.new_achievements))
        u.fit("Unlocked: " + names if names else "Progress is saved locally to " + self.store.active + ".", (279, 655), 1080, 17, ACCENT if names else MUTED)
        u.text("Tracking accuracy = on-target time / time holding. Hit time includes visual search.", (279, 695), 13, MUTED)
        u.button((274, 758, 250, 60), "Train again  [R]", "restart", True)
        u.button((544, 758, 250, 60), "View statistics", "statistics")
        u.button((814, 758, 250, 60), "Choose another mode", "training")

    def chart(self, rect, rows):
        u = self.ui
        x, y, w, h = rect
        u.panel(rect)
        u.text("ACCURACY TREND", (x + 24, y + 17), 11, MUTED, True)
        for value in (0, 50, 100):
            yy = y + h - 30 - value / 100 * (h - 85)
            pygame.draw.line(u.surface, LINE, (x + 52, yy), (x + w - 24, yy))
            u.text(str(value), (x + 15, yy - 8), 11, MUTED)
        if not rows:
            u.text("Play a session to begin your trend.", (x + w // 2, y + 85), 16, MUTED, False, "center")
        else:
            points = [(int(x + 60 + i / max(1, len(rows) - 1) * (w - 94)), int(y + h - 30 - r["accuracy"] / 100 * (h - 85))) for i, r in enumerate(rows)]
            if len(points) > 1:
                pygame.draw.lines(u.surface, CYAN, False, points, 3)
            for point in points:
                pygame.draw.circle(u.surface, ACCENT, point, 4)
        u.text("Last 12 filtered runs  /  %  /  tracking uses hold accuracy", (x + 24, y + h - 19), 10, MUTED)

    def statistics(self):
        u = self.ui
        self.sidebar("See your progress.", "Your history, personal bests and milestones. Stored on this device.")
        for i, tab in enumerate(("History", "Personal bests", "Achievements")):
            u.button((274 + i * 216, 184, 200, 43), tab, ("stats_tab", tab), self.statistics_tab == tab, True)
        u.button((1182, 184, 210, 43), "Export history CSV", "export", small=True)
        if self.statistics_tab == "Achievements":
            earned = achievement_ids(self.store.sessions)
            for i, (key, (name, description)) in enumerate(ACHIEVEMENTS.items()):
                x, y = 274 + i % 2 * 568, 251 + i // 2 * 134
                u.panel((x, y, 550, 115), (30, 49, 41) if key in earned else PANEL)
                u.text("UNLOCKED" if key in earned else "IN PROGRESS", (x + 22, y + 15), 10, ACCENT if key in earned else MUTED, True)
                u.text(name, (x + 22, y + 38), 21, TEXT, True)
                u.text(description, (x + 22, y + 78), 14, MUTED)
            return
        if self.statistics_tab == "History":
            rows = [r for r in self.store.sessions if self.history_mode == "all" or r["mode"] == self.history_mode]
            u.button((1077, 245, 315, 38), "Mode: " + ("All" if self.history_mode == "all" else MODES[self.history_mode][0]), "filter", small=True)
            u.text(f"{len(rows)} sessions  /  newest first below", (279, 254), 13, MUTED)
            self.chart((274, 301, 1118, 206), rows[-12:])
            display = list(reversed(rows))
            top = 534
            page_size = 4
        else:
            display = self.store.bests()
            top = 266
            page_size = 8
            u.text("Separated by mode, difficulty and duration. Practice is excluded.", (279, 245), 14, MUTED)
        maximum = max(0, (len(display) - 1) // page_size)
        self.history_page = min(self.history_page, maximum)
        u.panel((274, top, 1118, 40), RAISED, False, 8)
        for label, x in [("MODE / DATE", 293), ("DIFFICULTY", 650), ("SCORE", 850), ("ACCURACY", 1000), ("DURATION", 1210)]:
            u.text(label, (x, top + 12), 10, MUTED, True)
        visible = display[self.history_page * page_size:(self.history_page + 1) * page_size]
        for i, r in enumerate(visible):
            y = top + 50 + i * 53
            u.text(("Daily / " if r.get("daily") else "") + MODES[r["mode"]][0], (294, y), 16, TEXT, True)
            u.text(r.get("date", "")[:16].replace("T", " ") + " UTC", (294, y + 24), 10, MUTED)
            u.text(r["difficulty"], (650, y + 9), 15, MUTED)
            u.text(f"{r['score']:,}", (850, y + 6), 19, ACCENT, True)
            u.text(f"{r['accuracy']:.1f}%", (1000, y + 9), 15, TEXT)
            u.text(f"{r['elapsed']:.1f} s", (1210, y + 9), 15, MUTED)
            pygame.draw.line(u.surface, LINE, (291, y + 48), (1374, y + 48))
        if not visible:
            u.text("Your next session starts the story.", (827, top + 110), 20, MUTED, False, "center")
        u.button((1036, 824, 108, 40), "Previous", ("page", -1), small=True)
        u.text(f"{self.history_page + 1} / {maximum + 1}", (1176, 835), 13, MUTED, False, "center")
        u.button((1246, 824, 146, 40), "Next", ("page", 1), small=True)

    def settings_screen(self):
        u = self.ui
        self.sidebar("Make it your own.", "Preferences save automatically for the current profile. Click a value to cycle it.")
        groups = [("TRAINING", [("difficulty", "Difficulty", ["Easy", "Medium", "Hard"]), ("duration", "Precision / tracking duration", [30, 60, 90, 120]), ("target_radius", "Practice target radius", [18, 28, 40, 54]), ("spawn_interval", "Practice spawn seconds", [.4, .65, .9, 1.2])]),
                  ("CROSSHAIR", [("crosshair", "Style", ["Cross", "Dot", "Circle", "Cross + dot"]), ("crosshair_size", "Size", [8, 14, 20, 26]), ("crosshair_color", "Color", ["Mint", "White", "Coral", "Gold"])]),
                  ("AUDIO & COMFORT", [("volume", "Sound volume (%)", [0, 25, 50, 75, 100]), ("particles", "Hit particles", [True, False]), ("screen_shake", "Miss screen shake", [True, False]), ("reduced_motion", "Reduced motion", [False, True]), ("fps", "Frame cap", [60, 120, 144])])]
        for col, (group, items) in enumerate(groups):
            x = 274 + col * 379
            u.panel((x, 195, 360, 495))
            u.text(group, (x + 20, 217), 12, ACCENT, True)
            for i, (key, label, values) in enumerate(items):
                y = 261 + i * 79
                u.text(label, (x + 20, y), 13, MUTED)
                value = getattr(self.settings, key)
                u.button((x + 20, y + 24, 319, 39), ("On" if value else "Off") if type(value) is bool else str(value), ("setting", (key, values)), small=True)
        u.panel((274, 714, 1118, 112), (25, 46, 44))
        u.text("CROSSHAIR PREVIEW", (299, 734), 11, MUTED, True)
        u.crosshair((514, 780), self.settings)
        u.text("Classic always lasts 60 s. Daily uses fixed gameplay settings.", (635, 737), 16, TEXT)
        u.text("Reduced motion suppresses particles and shake. F11 toggles fullscreen.", (635, 774), 14, MUTED)
        if self.audio is None or not self.audio.available:
            u.text("Audio is unavailable on this device. Gameplay remains fully usable.", (280, 848), 13, GOLD)

    def profiles(self):
        u = self.ui
        self.sidebar("A space for your practice.", "Up to 20 local profiles, each with its own preferences and history.")
        u.panel((274, 191, 1118, 168))
        u.text("CREATE A PROFILE", (298, 211), 12, ACCENT, True)
        u.panel((294, 258, 660, 58), BG)
        u.fit(self.profile_input + ("|" if self.profile_editing and int(self.uptime * 2) % 2 == 0 else "") if self.profile_input else "Click here and type a name (24 characters)", (312, 276), 620, 17, TEXT if self.profile_input else MUTED)
        u.button((978, 259, 390, 56), "Create profile", "create_profile", True)
        u.text("Local profiles organize progress; they are not password-protected accounts.", (298, 330), 12, MUTED)
        names = list(self.store.data["profiles"])
        for i, name in enumerate(names):
            col, row = i % 3, i // 3
            x, y = 274 + col * 379, 385 + row * 64
            u.button((x, y, 360, 50), ("Active: " if self.store.active == name else "") + name, ("select_profile", name), self.store.active == name, True)

    def help_screen(self):
        u = self.ui
        self.sidebar("A little guidance.", "Local training. Transparent scores. No accounts, internet connection or GPU needed.")
        rows = [("01 / CONTROLS", "Left click hits a target. In Tracking, hold left click and follow it.", "ESC pauses and resumes. F11 changes fullscreen. Tab / Shift+Tab / Enter navigate."),
                ("02 / SCORING", "Classic / Survival: 100 points per hit. Precision: 150. Combos increase the multiplier.", "The multiplier rises every 3 consecutive quick hits, capped at x8. A gap over 650 ms resets it."),
                ("03 / LIVES & PRACTICE", "Missed arena shots and expired targets each cost one of 10 lives. Tracking has no life penalty.", "Practice has no life or time limit. End from the pause menu to save it. Right clicks never shoot."),
                ("04 / YOUR DATA", "History is local, with up to 1,000 sessions per profile. CSV exports go to the exports subfolder.", "Switching profiles changes the local statistics. Personal bests compare matching mode / difficulty / duration."),
                ("05 / MEASUREMENTS", "Hit time is spawn-to-hit delay, including visual search. It is not a clinical reaction-time test.", "Tracking accuracy is on-target time / held time; points reward total on-target time, not brief holds.")]
        for i, (label, line1, line2) in enumerate(rows):
            y = 190 + i * 108
            u.panel((274, y, 1118, 94))
            u.text(label, (296, y + 12), 11, ACCENT, True)
            u.text(line1, (296, y + 37), 14, TEXT)
            u.text(line2, (296, y + 65), 13, MUTED)
        u.text("DATA FOLDER", (280, 757), 11, MUTED, True)
        u.fit(str(self.store.directory), (280, 782), 1100, 15, CYAN)
        u.fit("Original source and submission reports are preserved in legacy/ and docs/original_v1.0/.", (280, 838), 890, 12, MUTED)
        u.button((1205, 831, 187, 43), "Quit application", "quit", small=True)

    def render(self):
        u = self.ui
        u.begin(self.pointer, self.focus)
        if self.screen in ("playing", "paused", "countdown", "ready"):
            self.gameplay()
            if self.screen != "playing":
                self.overlay()
        elif self.screen == "training":
            self.training()
        elif self.screen == "statistics":
            self.statistics()
        elif self.screen == "settings":
            self.settings_screen()
        elif self.screen == "profiles":
            self.profiles()
        elif self.screen == "results":
            self.results()
        elif self.screen == "help":
            self.help_screen()
        if self.message and self.uptime < self.message_until:
            u.panel((274, 8, 1118, 42), (43, 60, 49))
            u.fit(self.message, (291, 19), 1080, 14, ACCENT)
        ww, wh = self.window.get_size()
        scale = min(ww / WIDTH, wh / HEIGHT)
        w, h = max(1, round(WIDTH * scale)), max(1, round(HEIGHT * scale))
        x, y = (ww - w) // 2, (wh - h) // 2
        self.window.fill((5, 9, 14))
        if self.flash > 0 and self.screen == "playing":
            x += self.effect_rng.randint(-3, 3)
            y += self.effect_rng.randint(-3, 3)
        self.viewport = (x, y, w, h)
        scaled = pygame.transform.smoothscale(u.surface, (w, h)) if (w, h) != (WIDTH, HEIGHT) else u.surface
        self.window.blit(scaled, (x, y))
        pygame.mouse.set_visible(self.screen != "playing")
        pygame.display.flip()

    def run(self):
        clock = pygame.time.Clock()
        try:
            while self.running:
                dt = clock.tick(self.settings.fps) / 1000.0
                for event in pygame.event.get():
                    self.handle(event)
                self.update(dt)
                started = time.perf_counter()
                self.render()
                self.frame_times.append((time.perf_counter() - started) * 1000)
        finally:
            pygame.quit()


def main():
    parser = argparse.ArgumentParser(description="Ultimate Aim Trainer 2.0 — offline Python/Pygame training")
    parser.add_argument("--data-dir", type=Path, help="Use a different local save folder")
    parser.add_argument("--no-audio", action="store_true", help="Start without initializing sound")
    args = parser.parse_args()
    try:
        Game(args.data_dir, silent=args.no_audio).run()
    except pygame.error as exc:
        raise SystemExit(f"The game could not open its display: {exc}\nUse a desktop session with a working display driver.") from exc


if __name__ == "__main__":
    main()
