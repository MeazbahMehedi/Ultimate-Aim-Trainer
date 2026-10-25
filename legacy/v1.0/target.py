import pygame
import math
import random

class Target:
    MAX_SIZE = 25
    COLOR = (255, 0, 0)
    SECOND_COLOR = (255, 255, 255)

    def __init__(self, x, y, growth_rate):
        self.x = x
        self.y = y
        self.size = 0
        self.grow = True
        self.growth_rate = growth_rate
        self.pulse_phase = random.random() * 2 * math.pi

    def update(self, difficulty_multiplier):
        rate = self.growth_rate * difficulty_multiplier
        if self.size + rate >= self.MAX_SIZE:
            self.grow = False
        if self.grow:
            self.size += rate
        else:
            self.size -= rate
        self.pulse_phase += 0.1

    def draw(self, surface):
        pulse_scale = 1 + 0.05 * math.sin(self.pulse_phase)
        scaled_radius = int(self.size * pulse_scale)
        pygame.draw.circle(surface, self.COLOR, (int(self.x), int(self.y)), scaled_radius)
        pygame.draw.circle(surface, self.SECOND_COLOR, (int(self.x), int(self.y)), int(scaled_radius * 0.8))
        pygame.draw.circle(surface, self.COLOR, (int(self.x), int(self.y)), int(scaled_radius * 0.6))
        pygame.draw.circle(surface, self.SECOND_COLOR, (int(self.x), int(self.y)), int(scaled_radius * 0.4))

    def collide(self, x, y):
        distance = math.sqrt((x - self.x)**2 + (y - self.y)**2)
        return distance <= self.size
