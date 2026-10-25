"""Pygame drawing helpers. Cached text and a fixed logical canvas keep UI predictable."""
from collections import OrderedDict
from dataclasses import dataclass
import math
import pygame

WIDTH, HEIGHT = 1440, 900
BG = (13, 20, 27)
SIDE = (16, 25, 33)
PANEL = (22, 33, 43)
RAISED = (29, 43, 54)
LINE = (42, 57, 68)
TEXT = (237, 243, 247)
MUTED = (141, 160, 174)
ACCENT = (184, 239, 112)
CYAN = (104, 212, 218)
CORAL = (245, 132, 123)
GOLD = (245, 204, 123)
COLORS = {"Mint": ACCENT, "White": TEXT, "Coral": CORAL, "Gold": GOLD}


@dataclass
class Button:
    rect: pygame.Rect
    label: str
    action: object
    primary: bool = False


class Painter:
    def __init__(self):
        self.fonts = {}
        self.cache = OrderedDict()
        self.buttons = []
        self.pointer = (0, 0)
        self.focus = -1
        self.dt = 1 / 60
        self.hover = {}
        self.surface = pygame.Surface((WIDTH, HEIGHT))
        self.backdrop = pygame.Surface((WIDTH, HEIGHT))
        for y in range(HEIGHT):
            t = y / HEIGHT
            pygame.draw.line(self.backdrop, (int(15 - t * 3), int(24 - t * 5), int(32 - t * 5)), (0, y), (WIDTH, y))

    def text(self, text, pos, size=18, color=TEXT, bold=False, align="left"):
        text = str(text)
        key = (text, size, color, bold)
        rendered = self.cache.get(key)
        if rendered is None:
            font_key = (size, bold)
            if font_key not in self.fonts:
                self.fonts[font_key] = pygame.font.SysFont("segoeui,dejavusans,arial", size, bold=bold)
            rendered = self.fonts[font_key].render(text, True, color)
            self.cache[key] = rendered
            if len(self.cache) > 768:
                self.cache.popitem(last=False)
        rect = rendered.get_rect()
        if align == "center":
            rect.midtop = pos
        elif align == "right":
            rect.topright = pos
        else:
            rect.topleft = pos
        self.surface.blit(rendered, rect)
        return rect

    def fit(self, text, pos, max_width, size=18, color=TEXT, bold=False):
        font = self.fonts.get((size, bold)) or pygame.font.SysFont("segoeui,dejavusans,arial", size, bold=bold)
        value = str(text)
        while len(value) > 1 and font.size(value)[0] > max_width:
            value = value[:-2].rstrip() + "…"
        return self.text(value, pos, size, color, bold)

    def panel(self, rect, color=PANEL, border=True, radius=18):
        rect = pygame.Rect(rect)
        pygame.draw.rect(self.surface, color, rect, border_radius=radius)
        if border:
            pygame.draw.rect(self.surface, LINE, rect, 1, border_radius=radius)
        return rect

    def button(self, rect, label, action, primary=False, small=False):
        rect = pygame.Rect(rect)
        index = len(self.buttons)
        hovered = self.pointer is not None and rect.collidepoint(self.pointer)
        focused = index == self.focus
        hover_key = (rect.x, rect.y, rect.w, rect.h)
        amount = self.hover.get(hover_key, 0)
        amount += ((1 if hovered else 0) - amount) * (1 - math.exp(-12 * min(self.dt, .1)))
        self.hover[hover_key] = amount
        color = ACCENT if primary else tuple(round(a + (b - a) * amount) for a, b in zip(PANEL, RAISED))
        if primary and hovered:
            color = (201, 250, 138)
        self.panel(rect, color, not primary, 11)
        if focused:
            pygame.draw.rect(self.surface, CYAN, rect.inflate(6, 6), 2, border_radius=13)
        size = 16 if small else 18
        font = self.fonts.get((size, True)) or pygame.font.SysFont("segoeui,dejavusans,arial", size, bold=True)
        display_label = label
        while len(display_label) > 1 and font.size(display_label)[0] > rect.width - 16:
            display_label = display_label[:-2].rstrip() + "…"
        self.text(display_label, (rect.centerx, rect.y + (rect.height - size) // 2 - 2), size, BG if primary else TEXT, True, "center")
        self.buttons.append(Button(rect, label, action, primary))

    def begin(self, pointer, focus):
        self.surface.blit(self.backdrop, (0, 0))
        self.buttons = []
        self.pointer, self.focus = pointer, focus

    def target(self, center, radius, color=ACCENT, progress=None):
        center = (round(center[0]), round(center[1]))
        radius = max(2, int(radius))
        pygame.draw.circle(self.surface, (28, 58, 55), center, radius + 8, 1)
        pygame.draw.circle(self.surface, color, center, radius)
        pygame.draw.circle(self.surface, BG, center, max(2, int(radius * .69)))
        pygame.draw.circle(self.surface, color, center, max(1, int(radius * .34)))
        if progress is not None:
            r = radius + 6
            pygame.draw.arc(self.surface, CYAN, (center[0] - r, center[1] - r, r * 2, r * 2), -math.pi / 2, -math.pi / 2 + max(.01, progress * 2 * math.pi), 2)

    def crosshair(self, pointer, settings):
        if pointer is None:
            return
        x, y = map(round, pointer)
        c = COLORS[settings.crosshair_color]
        radius = settings.crosshair_size
        if settings.crosshair in ("Circle",):
            pygame.draw.circle(self.surface, BG, (x, y), radius, 4)
            pygame.draw.circle(self.surface, c, (x, y), radius, 2)
        if settings.crosshair in ("Cross", "Cross + dot"):
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                a = (x + dx * 5, y + dy * 5)
                b = (x + dx * radius, y + dy * radius)
                pygame.draw.line(self.surface, BG, a, b, 4)
                pygame.draw.line(self.surface, c, a, b, 2)
        if settings.crosshair in ("Dot", "Cross + dot"):
            pygame.draw.circle(self.surface, BG, (x, y), 4)
            pygame.draw.circle(self.surface, c, (x, y), 2)
