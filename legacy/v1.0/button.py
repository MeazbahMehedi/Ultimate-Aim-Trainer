import pygame

class Button:
    def __init__(self, x, y, width, height, text,
                 button_color=(0, 120, 180),
                 hover_color=(0, 150, 210),
                 text_color=(255, 255, 255)):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.hovered = False
        self.scale = 1.0
        self.button_color = button_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.font = pygame.font.SysFont("arial", 28, bold=True)

    def update(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)
        self.scale = 1.1 if self.hovered else 1.0

    def draw(self, surface):
        color = self.hover_color if self.hovered else self.button_color
        scaled_rect = self.rect.inflate(
            self.rect.width * (self.scale - 1),
            self.rect.height * (self.scale - 1)
        )
        pygame.draw.rect(surface, color, scaled_rect, border_radius=10)

        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=scaled_rect.center)
        surface.blit(text_surf, text_rect)

    def is_clicked(self, mouse_pos, mouse_pressed):
        return self.rect.collidepoint(mouse_pos) and mouse_pressed[0]
