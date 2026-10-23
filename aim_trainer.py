import pygame
import random
import time
import os
from target import Target
from particle import Particle
from ui_manager import UIManager

pygame.init()
pygame.mixer.init()

WIDTH, HEIGHT = 1280, 720
os.environ['SDL_VIDEO_CENTERED'] = '1'
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ultimate Aim Trainer")

BG_COLOR = (0, 25, 40)
BUTTON_COLOR = (0, 120, 180)
BUTTON_HOVER_COLOR = (0, 150, 210)
TEXT_COLOR = (255, 255, 255)

GAME_DURATION = 60
MAX_LIVES = 10
TARGET_PADDING = 30
FPS = 60
DIFFICULTY_GROWTH = {"Easy": 0.2, "Medium": 0.3, "Hard": 0.4}
TARGET_EVENT = pygame.USEREVENT + 1


def wait_for_first_click(ui_manager, surface):
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 32, bold=True)
    while True:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.MOUSEBUTTONDOWN:
                return True

        surface.fill((0, 0, 0))
        ui_manager.draw_gradient_background(surface)
        message = font.render("Click anywhere to begin!", True, TEXT_COLOR)
        surface.blit(message, (WIDTH // 2 - message.get_width() // 2, HEIGHT // 2))
        pygame.display.update()


def handle_events(ui_manager, targets, particles, hits, misses, score, multiplier,
                  last_hit_time, clicks, start_time, combo, shake_timer):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return "quit", None
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                # Call the pause menu. If the user quits from pause, then exit.
                result = ui_manager.pause_menu()
                if result == "quit":
                    return "quit", None
                # If "resume", then continue with event processing.
        if event.type == TARGET_EVENT:
            x = random.randint(TARGET_PADDING, WIDTH - TARGET_PADDING)
            y = random.randint(TARGET_PADDING + ui_manager.top_bar_height, HEIGHT - TARGET_PADDING)
            targets.append(Target(x, y, DIFFICULTY_GROWTH[ui_manager.current_difficulty]))
        if event.type == pygame.MOUSEBUTTONDOWN:
            clicks += 1
            mx, my = pygame.mouse.get_pos()
            clicked_any = False
            for target in targets[:]:
                if target.collide(mx, my):
                    clicked_any = True
                    hits += 1
                    if time.time() - last_hit_time <= 0.5:
                        combo += 1
                        multiplier = max(multiplier, combo)
                    else:
                        combo = 1
                    score += multiplier
                    last_hit_time = time.time()
                    for _ in range(min(20, 100 - len(particles))):
                        particles.add(Particle(target.x, target.y))
                    targets.remove(target)
                    break
            if not clicked_any:
                misses += 1
                multiplier = 1
                combo = 0
                shake_timer = 10
    return None, (hits, misses, score, multiplier, last_hit_time, clicks, combo, shake_timer)


def update_game(ui_manager, targets, particles, difficulty_multiplier, misses,
                game_surface, multiplier, elapsed_time, score, hits, mouse_pos, combo):
    for target in targets[:]:
        target.update(difficulty_multiplier)
        if target.size <= 0:
            targets.remove(target)
    particles.update()
    ui_manager.draw_game_ui(game_surface, targets, particles, multiplier,
                            elapsed_time, score, hits, misses, mouse_pos, combo, MAX_LIVES)
    return misses


def game_loop(ui_manager, difficulty="Medium", immediate=False):
    ui_manager.current_difficulty = difficulty  # store current difficulty for later use
    targets = []
    particles = pygame.sprite.Group()
    game_surface = pygame.Surface((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    if not immediate:
        if not wait_for_first_click(ui_manager, game_surface):
            return "quit", None

    hits, clicks, misses, score, multiplier, combo = 0, 0, 0, 0, 1, 0
    last_hit_time = 0
    start_time = time.time()
    shake_timer = 0

    pygame.time.set_timer(TARGET_EVENT, ui_manager.difficulty[difficulty])

    while True:
        clock.tick(FPS)
        elapsed_time = time.time() - start_time
        mouse_pos = pygame.mouse.get_pos()

        if misses >= MAX_LIVES:
            action = ui_manager.end_screen(elapsed_time, hits, score, clicks, game_over=True)
            return ("restart", difficulty) if action == "restart" else ("quit", None)
        elif elapsed_time >= GAME_DURATION:
            action = ui_manager.end_screen(elapsed_time, hits, score, clicks, game_over=False)
            return ("restart", difficulty) if action == "restart" else ("quit", None)

        difficulty_multiplier = 1 + (elapsed_time / GAME_DURATION)
        action, updated = handle_events(ui_manager, targets, particles, hits, misses, score,
                                        multiplier, last_hit_time, clicks, start_time,
                                        combo, shake_timer)
        if action:
            return action, None
        (hits, misses, score, multiplier,
         last_hit_time, clicks, combo, shake_timer) = updated

        misses = update_game(ui_manager, targets, particles, difficulty_multiplier,
                             misses, game_surface, multiplier, elapsed_time, score,
                             hits, mouse_pos, combo)
        offset = (random.randint(-5, 5), random.randint(-5, 5)) if shake_timer > 0 else (0, 0)
        shake_timer = max(0, shake_timer - 1)

        WIN.blit(game_surface, offset)
        pygame.display.update()


def main():
    ui_manager = UIManager(WIN, WIDTH, HEIGHT, BG_COLOR, TEXT_COLOR, BUTTON_COLOR, BUTTON_HOVER_COLOR, FPS)
    state = "main_menu"
    difficulty = "Medium"
    immediate_start = False

    while state != "quit":
        if state == "main_menu":
            state = ui_manager.main_menu()
        elif state == "options":
            state, selected = ui_manager.options_menu()
            if selected:
                difficulty = selected
                immediate_start = True
            else:
                immediate_start = False
            state = "start"
        elif state == "start":
            state, new_diff = game_loop(ui_manager, difficulty, immediate=immediate_start)
            immediate_start = False
            if new_diff:
                difficulty = new_diff
        elif state == "restart":
            state, new_diff = game_loop(ui_manager, difficulty, immediate=True)
            if new_diff:
                difficulty = new_diff
            if state != "restart":
                state = "start"

    pygame.quit()


if __name__ == "__main__":
    main()
