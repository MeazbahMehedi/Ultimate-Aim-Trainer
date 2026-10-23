import pygame
import math
from button import Button


class UIManager:
    def __init__(self, window, width, height, bg_color, text_color, button_color, hover_color, fps):
        self.window = window
        self.width = width
        self.height = height
        self.bg_color = bg_color
        self.text_color = text_color
        self.button_color = button_color
        self.hover_color = hover_color
        self.fps = fps

        self.title_font = pygame.font.SysFont("arial", 60, bold=True)
        self.label_font = pygame.font.SysFont("arial", 24)
        self.cursor_size = 20
        self.cursor_color = (255, 255, 255)
        self.cursor_outline = (0, 0, 0)
        self.top_bar_height = 50

        self.difficulty = {"Easy": 500, "Medium": 400, "Hard": 300}
        self.gradient_bg = self.create_gradient_surface(width, height)
        self.current_difficulty = "Medium"

    def create_gradient_surface(self, width, height):
        gradient = pygame.Surface((1, height))
        for y in range(height):
            ratio = y / height
            r = int(self.bg_color[0] * (1 - ratio) + 10 * ratio)
            g = int(self.bg_color[1] * (1 - ratio) + 20 * ratio)
            b = int(self.bg_color[2] * (1 - ratio) + 40 * ratio)
            gradient.set_at((0, y), (r, g, b))
        return pygame.transform.scale(gradient, (width, height))

    def fade_transition(self, fade_in=True, duration=500):
        fade = pygame.Surface((self.width, self.height))
        fade.fill((0, 0, 0))
        clock = pygame.time.Clock()
        steps = 30
        for i in range(steps + 1):
            alpha = int(255 * (1 - i / steps)) if fade_in else int(255 * (i / steps))
            fade.set_alpha(alpha)
            self.draw_gradient_background(self.window)
            self.window.blit(fade, (0, 0))
            pygame.display.update()
            clock.tick(int(1000 / (duration / steps)))

    def format_time(self, secs):
        milli = math.floor(int(secs * 1000 % 1000) / 100)
        seconds = int(secs % 60)
        minutes = int(secs // 60)
        return f"{minutes:02d}:{seconds:02d}.{milli}"

    def get_middle(self, surface):
        return self.width // 2 - surface.get_width() // 2

    def draw_gradient_background(self, surface):
        surface.blit(self.gradient_bg, (0, 0))

    def draw_cursor(self, surface, mouse_pos):
        x, y = mouse_pos
        pygame.draw.circle(surface, self.cursor_outline, (x, y), self.cursor_size // 2 + 2, 2)
        pygame.draw.circle(surface, self.cursor_color, (x, y), self.cursor_size // 2, 2)
        pygame.draw.line(surface, self.cursor_outline, (x - self.cursor_size, y), (x + self.cursor_size, y), 2)
        pygame.draw.line(surface, self.cursor_outline, (x, y - self.cursor_size), (x, y + self.cursor_size), 2)

    def draw_top_bar(self, surface, elapsed_time, hits, misses, multiplier, score, combo, max_lives):
        top_bar = pygame.Surface((self.width, self.top_bar_height), pygame.SRCALPHA)
        top_bar.fill((0, 0, 0, 150))
        surface.blit(top_bar, (0, 0))

        stats = [
            f"Time: {self.format_time(elapsed_time)}",
            f"Speed: {round(hits / elapsed_time, 1) if elapsed_time > 0 else 0} t/s",
            f"Hits: {hits}",
            f"Lives: {max_lives - misses}",
            f"Multiplier: x{multiplier}",
            f"Combo: {combo}",
            f"Score: {score}"
        ]
        x = 10
        for text in stats:
            shadow = self.label_font.render(text, True, (0, 0, 0))
            rendered = self.label_font.render(text, True, self.text_color)
            surface.blit(shadow, (x + 1, 11))
            surface.blit(rendered, (x, 10))
            x += rendered.get_width() + 20

    def draw_game_ui(self, surface, targets, particles, multiplier, elapsed_time, score, hits, misses, mouse_pos, combo, max_lives):
        self.draw_gradient_background(surface)
        for target in targets:
            target.draw(surface)
        particles.draw(surface)
        self.draw_top_bar(surface, elapsed_time, hits, misses, multiplier, score, combo, max_lives)
        self.draw_cursor(surface, mouse_pos)

    def main_menu(self):
        self.fade_transition(fade_in=True, duration=500)
        title_text = self.title_font.render("Ultimate Aim Trainer", True, self.text_color)
        shadow = self.title_font.render("Ultimate Aim Trainer", True, (0, 0, 0))

        buttons = [
            Button(self.width // 2 - 100, 250, 200, 50, "Start", self.button_color, self.hover_color, self.text_color),
            Button(self.width // 2 - 100, 320, 200, 50, "Options", self.button_color, self.hover_color, self.text_color),
            Button(self.width // 2 - 100, 390, 200, 50, "Quit", self.button_color, self.hover_color, self.text_color)
        ]

        clock = pygame.time.Clock()
        title_phase = 0

        while True:
            clock.tick(self.fps)
            mouse_pos = pygame.mouse.get_pos()
            mouse_pressed = pygame.mouse.get_pressed()
            title_phase += 0.05

            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    return "quit"

            for button in buttons:
                button.update(mouse_pos)
                if button.is_clicked(mouse_pos, mouse_pressed):
                    self.fade_transition(fade_in=False, duration=300)
                    return button.text.lower()

            self.window.fill(self.bg_color)
            self.draw_gradient_background(self.window)
            self.window.blit(shadow, (self.get_middle(shadow), 102))
            self.window.blit(title_text, (self.get_middle(title_text), 100 + math.sin(title_phase) * 10))
            for button in buttons:
                button.draw(self.window)
            self.draw_cursor(self.window, mouse_pos)
            pygame.display.update()

    def options_menu(self):
        self.fade_transition(fade_in=True, duration=500)
        pygame.event.clear()
        while pygame.mouse.get_pressed()[0]:
            pygame.event.pump()
            pygame.time.delay(50)

        title = self.title_font.render("Options", True, self.text_color)
        buttons = [
            Button(self.width // 2 - 100, 200, 200, 50, "Easy", self.button_color, self.hover_color, self.text_color),
            Button(self.width // 2 - 100, 270, 200, 50, "Medium", self.button_color, self.hover_color, self.text_color),
            Button(self.width // 2 - 100, 340, 200, 50, "Hard", self.button_color, self.hover_color, self.text_color),
            Button(self.width // 2 - 100, 410, 200, 50, "Back", self.button_color, self.hover_color, self.text_color)
        ]

        clock = pygame.time.Clock()
        while True:
            clock.tick(self.fps)
            mouse_pos = pygame.mouse.get_pos()
            mouse_pressed = pygame.mouse.get_pressed()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit", None
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return "main_menu", None

            for button in buttons:
                button.update(mouse_pos)
                if button.is_clicked(mouse_pos, mouse_pressed):
                    self.fade_transition(fade_in=False, duration=300)
                    if button.text in self.difficulty:
                        return "start", button.text
                    elif button.text == "Back":
                        return "main_menu", None

            self.window.fill(self.bg_color)
            self.draw_gradient_background(self.window)
            self.window.blit(title, (self.get_middle(title), 100))
            for button in buttons:
                button.draw(self.window)
            self.draw_cursor(self.window, mouse_pos)
            pygame.display.update()

    def end_screen(self, elapsed_time, hits, score, clicks, game_over=False):
        accuracy = round((hits / clicks) * 100, 1) if clicks > 0 else 0
        title_text = "Game Over!" if game_over else "Time's Up!"
        title_font = pygame.font.SysFont("arial", 48, bold=True)
        stats_font = pygame.font.SysFont("arial", 28)

        # Added Restart button
        buttons = [
            Button(self.width // 2 - 220, 450, 200, 50, "Restart", self.button_color, self.hover_color, self.text_color),
            Button(self.width // 2 + 20, 450, 200, 50, "Quit", self.button_color, self.hover_color, self.text_color)
        ]

        clock = pygame.time.Clock()
        while True:
            clock.tick(self.fps)
            mouse_pos = pygame.mouse.get_pos()
            mouse_pressed = pygame.mouse.get_pressed()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return "quit"

            for button in buttons:
                button.update(mouse_pos)
                if button.is_clicked(mouse_pos, mouse_pressed):
                    return "restart" if button.text == "Restart" else "quit"

            self.window.fill(self.bg_color)
            self.draw_gradient_background(self.window)

            title_surface = title_font.render(title_text, True, self.text_color)
            self.window.blit(title_surface, (self.get_middle(title_surface), 100))

            stats_list = [
                f"Time: {self.format_time(elapsed_time)}",
                f"Hits: {hits}",
                f"Clicks: {clicks}",
                f"Accuracy: {accuracy}%",
                f"Score: {score}"
            ]
            for i, stat in enumerate(stats_list):
                stat_surface = stats_font.render(stat, True, self.text_color)
                self.window.blit(stat_surface, (self.get_middle(stat_surface), 180 + i * 35))

            for button in buttons:
                button.draw(self.window)
            self.draw_cursor(self.window, mouse_pos)
            pygame.display.update()

    def pause_menu(self):
        title = self.title_font.render("Paused", True, self.text_color)
        resume_button = Button(self.width // 2 - 100, 250, 200, 50, "Resume", self.button_color, self.hover_color, self.text_color)
        quit_button = Button(self.width // 2 - 100, 320, 200, 50, "Quit", self.button_color, self.hover_color, self.text_color)
        buttons = [resume_button, quit_button]
        clock = pygame.time.Clock()

        while True:
            clock.tick(self.fps)
            mouse_pos = pygame.mouse.get_pos()
            mouse_pressed = pygame.mouse.get_pressed()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"

            for button in buttons:
                button.update(mouse_pos)
                if button.is_clicked(mouse_pos, mouse_pressed):
                    self.fade_transition(fade_in=False, duration=300)
                    return "resume" if button.text == "Resume" else "quit"

            self.window.fill(self.bg_color)
            self.draw_gradient_background(self.window)
            self.window.blit(title, (self.get_middle(title), 150))
            for button in buttons:
                button.draw(self.window)
            self.draw_cursor(self.window, mouse_pos)
            pygame.display.update()