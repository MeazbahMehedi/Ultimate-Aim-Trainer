import pygame
import random
import time

class Particle(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.x = x
        self.y = y
        self.radius = random.randint(3, 6)
        self.color = random.choice([
            (255, 200, 0),
            (255, 100, 0),
            (255, 255, 100)
        ])
        self.life = 1.0
        self.vx = random.uniform(-3, 3)
        self.vy = random.uniform(-3, 3)
        self.creation_time = time.time()
        self.image = None
        self.rect = None
        self.update()

    def update(self):
        self.x += self.vx
        self.y += self.vy
        elapsed = time.time() - self.creation_time
        self.life = max(1 - elapsed, 0)
        if self.life > 0:
            current_radius = max(int(self.radius * self.life), 1)
            size = 2 * current_radius
            self.image = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.circle(
                self.image,
                self.color,
                (current_radius, current_radius),
                current_radius
            )
            self.rect = self.image.get_rect(center=(int(self.x), int(self.y)))
        else:
            self.kill()
