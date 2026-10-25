"""Small generated tones; audio failure never prevents playing."""
from array import array
import math
import pygame


class Audio:
    def __init__(self):
        self.available = False
        self.sounds = {}
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
            for name, frequency, duration in [("hit", 880, .07), ("miss", 180, .09), ("click", 520, .035), ("finish", 660, .2)]:
                samples = array("h", (int(6500 * math.sin(2 * math.pi * frequency * i / 22050) * (1 - i / (22050 * duration)) ** 2) for i in range(int(22050 * duration))))
                self.sounds[name] = pygame.mixer.Sound(buffer=samples)
            self.available = True
        except (pygame.error, OSError, ValueError):
            pass

    def play(self, name, volume):
        if self.available and volume and name in self.sounds:
            self.sounds[name].set_volume(volume / 100)
            self.sounds[name].play()
