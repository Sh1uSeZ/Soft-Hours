import pygame
import math

WHITE      = (255, 255, 255)
BLACK      = (0,   0,   0)
NEAR_BLACK = (10,  10,  10)
DARK_GRAY  = (40,  40,  40)
MID_GRAY   = (100, 100, 100)
LIGHT_GRAY = (180, 180, 180)

CHAR_COLORS = {
    "blue":   (100, 149, 237),
    "green":  (100, 200, 120),
    "orange": (230, 150,  80),
    "purple": (160, 100, 210),
    "red":    (210,  80,  80),
}


def draw_panel(surface, rect, border_color=WHITE, bg_color=NEAR_BLACK,
               border_width=2, radius=10):
    pygame.draw.rect(surface, bg_color,     rect, border_radius=radius)
    pygame.draw.rect(surface, border_color, rect, border_width, border_radius=radius)


def draw_button(surface, rect, label, font,
                bg=DARK_GRAY, fg=WHITE, border=WHITE,
                hover=False, radius=6):
    actual_bg = tuple(min(c + 20, 255) for c in bg) if hover else bg
    pygame.draw.rect(surface, actual_bg, rect, border_radius=radius)
    pygame.draw.rect(surface, border,    rect, 1,  border_radius=radius)
    text = font.render(label, True, fg)
    surface.blit(text, (rect.centerx - text.get_width()  // 2,
                         rect.centery - text.get_height() // 2))


def is_hovered(rect):
    return rect.collidepoint(pygame.mouse.get_pos())


def draw_text(surface, text, font, color, x, y, anchor="topleft"):
    surf = font.render(text, True, color)
    if anchor == "center":
        surface.blit(surf, (x - surf.get_width() // 2,
                            y - surf.get_height() // 2))
    elif anchor == "topright":
        surface.blit(surf, (x - surf.get_width(), y))
    else:
        surface.blit(surf, (x, y))
    return surf.get_rect()


def draw_text_wrapped(surface, text, font, color, x, y, max_width, line_spacing=6):
    words   = text.split(" ")
    lines   = []
    current = ""

    for word in words:
        test = current + (" " if current else "") + word
        if font.size(test)[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)

    line_h = font.get_linesize() + line_spacing
    for i, line in enumerate(lines):
        surf = font.render(line, True, color)
        surface.blit(surf, (x, y + i * line_h))

    return len(lines) * line_h


def draw_sprite_frame(surface, sprite_surface, x, y,
                      char_color=WHITE, border_width=3, padding=6):
    w = sprite_surface.get_width()  + padding * 2
    h = sprite_surface.get_height() + padding * 2
    frame_rect = pygame.Rect(x - padding, y - padding, w, h)
    pygame.draw.rect(surface, NEAR_BLACK, frame_rect, border_radius=4)
    pygame.draw.rect(surface, char_color, frame_rect, border_width, border_radius=4)
    surface.blit(sprite_surface, (x, y))


def draw_dialogue_box(surface, rect, speaker_name, dialogue_text,
                      font_name, font_body, name_color=WHITE):
    pygame.draw.rect(surface, WHITE, rect, border_radius=6)
    pygame.draw.rect(surface, BLACK, rect, 2, border_radius=6)

    name_surf = font_name.render(speaker_name, True, BLACK)
    surface.blit(name_surf, (rect.x + 20, rect.y + 14))

    pygame.draw.line(surface, MID_GRAY,
                     (rect.x + 16,    rect.y + 42),
                     (rect.right - 16, rect.y + 42), 1)

    draw_text_wrapped(surface, dialogue_text, font_body, BLACK,
                      rect.x + 20, rect.y + 54, rect.width - 40)


def draw_choices(surface, choices, rects, font, mouse_pos):
    hovered = -1
    for i, (text, rect) in enumerate(zip(choices, rects)):
        hover = rect.collidepoint(mouse_pos)
        if hover:
            hovered = i
        draw_button(surface, rect, text, font, bg=DARK_GRAY, hover=hover)
    return hovered


def make_choice_rects(num_choices, base_x, base_y, btn_w, btn_h, gap=10):
    rects = []
    for i in range(num_choices):
        rects.append(pygame.Rect(base_x, base_y + i * (btn_h + gap), btn_w, btn_h))
    return rects


def draw_stat_bar(surface, label, value, max_value,
                  x, y, w, h, font,
                  bar_color=WHITE, warn_color=(220, 80, 80)):
    label_surf = font.render(label, True, LIGHT_GRAY)
    surface.blit(label_surf, (x, y - label_surf.get_height() - 2))

    pygame.draw.rect(surface, DARK_GRAY, (x, y, w, h), border_radius=3)

    fill_w = int((value / max_value) * w)
    color  = warn_color if (value / max_value) < 0.2 else bar_color
    if fill_w > 0:
        pygame.draw.rect(surface, color, (x, y, fill_w, h), border_radius=3)

    pygame.draw.rect(surface, MID_GRAY, (x, y, w, h), 1, border_radius=3)

    val_surf = font.render(f"{value}", True, MID_GRAY)
    surface.blit(val_surf, (x + w + 6, y + h // 2 - val_surf.get_height() // 2))


def draw_all_stats(surface, stats_dict, x, y, font,
                   bar_w=160, bar_h=10, gap=24, max_val=100):
    for i, (label, value) in enumerate(stats_dict.items()):
        draw_stat_bar(surface, label, value, max_val,
                      x, y + i * gap, bar_w, bar_h, font)
    return len(stats_dict) * gap


def draw_patient_info(surface, name, age, occupation, background,
                      rect, font_name, font_body, char_color=WHITE):
    pygame.draw.rect(surface, WHITE, rect, border_radius=6)
    pygame.draw.rect(surface, BLACK, rect, 2, border_radius=6)

    y = rect.y + 16

    header = font_name.render(f"{name},  {age}", True, BLACK)
    surface.blit(header, (rect.x + 16, y))
    y += header.get_height() + 8

    occ = font_body.render(occupation, True, BLACK)
    surface.blit(occ, (rect.x + 16, y))
    y += occ.get_height() + 12

    pygame.draw.line(surface, MID_GRAY,
                     (rect.x + 12,     y),
                     (rect.right - 12, y), 1)
    y += 10

    draw_text_wrapped(surface, background, font_body, BLACK,
                      rect.x + 16, y, rect.width - 32)


class WarningFlash:
    def __init__(self, screen_w, screen_h, duration=0.6):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.duration = duration
        self.timer    = 0.0
        self.active   = False

    def trigger(self):
        self.active = True
        self.timer  = self.duration

    def update(self, dt):
        if self.active:
            self.timer -= dt
            if self.timer <= 0:
                self.active = False

    def draw(self, surface):
        if not self.active:
            return
        alpha   = int(180 * (self.timer / self.duration))
        overlay = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
        pygame.draw.rect(overlay, (220, 60, 60, alpha),
                         (0, 0, self.screen_w, self.screen_h), 8)
        surface.blit(overlay, (0, 0))


class JumpTransform:
    def __init__(self, height=12, duration=0.35):
        self.height   = height
        self.duration = duration
        self.timer    = 0.0
        self.active   = False

    @property
    def offset_y(self):
        if not self.active:
            return 0
        progress = self.timer / self.duration
        return int(self.height * math.sin(progress * math.pi))  # sine arc up then back

    def trigger(self):
        self.active = True
        self.timer  = 0.0

    def update(self, dt):
        if self.active:
            self.timer += dt
            if self.timer >= self.duration:
                self.active = False
                self.timer  = 0.0


def load_sprite(char_name, emotion, size=None):
    path = f"Soft Hours/assets/images/sprites/{char_name}/{char_name}_{emotion}.png"
    try:
        surf = pygame.image.load(path).convert_alpha()
        if size:
            surf = pygame.transform.scale(surf, size)
        return surf
    except FileNotFoundError:
        w, h = size if size else (200, 400)
        placeholder = pygame.Surface((w, h), pygame.SRCALPHA)
        placeholder.fill((60, 60, 60, 200))
        pygame.draw.rect(placeholder, LIGHT_GRAY, (0, 0, w, h), 2)
        try:
            font  = pygame.font.SysFont("arial", 14)
            label = font.render(f"{char_name}", True, LIGHT_GRAY)
            emo   = font.render(f"{emotion}",   True, MID_GRAY)
            placeholder.blit(label, (w // 2 - label.get_width() // 2, h // 2 - 16))
            placeholder.blit(emo,   (w // 2 - emo.get_width()   // 2, h // 2 + 4))
        except Exception:
            pass
        return placeholder


def load_background(name, size=None):
    path = f"Soft Hours/assets/images/bg/{name}.png"
    try:
        surf = pygame.image.load(path).convert()
        if size:
            surf = pygame.transform.scale(surf, size)
        return surf
    except FileNotFoundError:
        w, h = size if size else (1280, 720)
        placeholder = pygame.Surface((w, h))
        placeholder.fill((20, 20, 20))
        return placeholder


def draw_dim_overlay(surface, alpha=160):
    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, alpha))
    surface.blit(overlay, (0, 0))


def draw_centered_message(surface, message, font, color=WHITE,
                           sub_message=None, sub_font=None, sub_color=LIGHT_GRAY):
    w, h = surface.get_size()
    text = font.render(message, True, color)
    surface.blit(text, (w // 2 - text.get_width() // 2,
                         h // 2 - text.get_height() // 2 - 20))
    if sub_message and sub_font:
        sub = sub_font.render(sub_message, True, sub_color)
        surface.blit(sub, (w // 2 - sub.get_width() // 2, h // 2 + 20))
