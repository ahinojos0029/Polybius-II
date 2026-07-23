# ui.py
import pygame

class UIRenderer:
    def __init__(self):
        try:
            pygame.font.init()
            self.font_sm = pygame.font.SysFont("Courier New", 14)
            self.font_md = pygame.font.SysFont("Courier New", 18, bold=True)
            self.font_lg = pygame.font.SysFont("Courier New", 26, bold=True)
            self.font_xl = pygame.font.SysFont("Courier New", 36, bold=True)
        except Exception:
            self.font_sm = self.font_md = self.font_lg = self.font_xl = None

    def draw_text(self, surface, text, x, y, color, font_type="md", center=False):
        font_map = {
            "sm": self.font_sm,
            "md": self.font_md,
            "lg": self.font_lg,
            "xl": self.font_xl,
        }
        font = font_map.get(font_type, self.font_md)
        if font is None:
            return
        surf = font.render(str(text), True, color)
        rect = surf.get_rect()
        if center:
            rect.center = (x, y)
        else:
            rect.topleft = (x, y)
        surface.blit(surf, rect)