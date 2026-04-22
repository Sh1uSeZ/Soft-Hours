import pygame
import math

# ── Colors (same as game.py for consistency) ──────────────────────────────────
WHITE      = (255, 255, 255)
BLACK      = (0,   0,   0)
NEAR_BLACK = (10,  10,  10)
DARK_GRAY  = (40,  40,  40)
MID_GRAY   = (100, 100, 100)
LIGHT_GRAY = (180, 180, 180)

# Character border colors
CHAR_COLORS = {
    "blue":   (100, 149, 237),
    "green":  (100, 200, 120),
    "orange": (230, 150,  80),
    "purple": (160, 100, 210),
    "red":    (210,  80,  80),
}


# ─────────────────────────────────────────────────────────────────────────────
# Panel — white border black rounded rect (the game's main UI element)
# ─────────────────────────────────────────────────────────────────────────────
def draw_panel(surface, rect, border_color=WHITE, bg_color=NEAR_BLACK,
               border_width=2, radius=10):
    """Draw a rounded rectangle panel with a colored border."""
    pygame.draw.rect(surface, bg_color,      rect, border_radius=radius)
    pygame.draw.rect(surface, border_color,  rect, border_width, border_radius=radius)


# ─────────────────────────────────────────────────────────────────────────────
# Button — draw + hit test
# ─────────────────────────────────────────────────────────────────────────────
def draw_button(surface, rect, label, font,
                bg=DARK_GRAY, fg=WHITE, border=WHITE,
                hover=False, radius=6):
    """Draw a button. Returns True if mouse is hovering."""
    actual_bg = tuple(min(c + 20, 255) for c in bg) if hover else bg
    pygame.draw.rect(surface, actual_bg, rect, border_radius=radius)
    pygame.draw.rect(surface, border,    rect, 1,  border_radius=radius)
    text = font.render(label, True, fg)
    surface.blit(text, (rect.centerx - text.get_width()  // 2,
                         rect.centery - text.get_height() // 2))


def is_hovered(rect):
    """Check if mouse is over a rect."""
    return rect.collidepoint(pygame.mouse.get_pos())


# ─────────────────────────────────────────────────────────────────────────────
# Text rendering helpers
# ─────────────────────────────────────────────────────────────────────────────
def draw_text(surface, text, font, color, x, y, anchor="topleft"):
    """Draw text with anchor point: topleft, center, topright."""
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
    """
    Draw text that wraps within max_width.
    Returns the total height used.
    """
    words    = text.split(" ")
    lines    = []
    current  = ""

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


# ─────────────────────────────────────────────────────────────────────────────
# Sprite frame — draws a sprite with a colored character border
# ─────────────────────────────────────────────────────────────────────────────
def draw_sprite_frame(surface, sprite_surface, x, y,
                      char_color=WHITE, border_width=3, padding=6):
    """
    Draw a sprite with a colored border frame around it.
    char_color should be one of the CHAR_COLORS values.
    """
    w = sprite_surface.get_width()  + padding * 2
    h = sprite_surface.get_height() + padding * 2
    frame_rect = pygame.Rect(x - padding, y - padding, w, h)

    # Background
    pygame.draw.rect(surface, NEAR_BLACK, frame_rect, border_radius=4)
    # Colored border
    pygame.draw.rect(surface, char_color, frame_rect, border_width, border_radius=4)
    # Sprite
    surface.blit(sprite_surface, (x, y))


# ─────────────────────────────────────────────────────────────────────────────
# Dialogue box
# ─────────────────────────────────────────────────────────────────────────────
def draw_dialogue_box(surface, rect, speaker_name, dialogue_text,
                      font_name, font_body, name_color=WHITE):
    """
    Draw the main dialogue box.
    rect      — the box area
    speaker   — name shown above text
    dialogue  — the patient's line
    """
    # Draw panel with white background and black border
    pygame.draw.rect(surface, WHITE, rect, border_radius=6)
    pygame.draw.rect(surface, BLACK, rect, 2, border_radius=6)

    # Speaker name in black
    name_surf = font_name.render(speaker_name, True, BLACK)
    surface.blit(name_surf, (rect.x + 20, rect.y + 14))

    # Divider
    pygame.draw.line(surface, MID_GRAY,
                     (rect.x + 16,          rect.y + 42),
                     (rect.right - 16,       rect.y + 42), 1)

    # Dialogue text (wrapped) in black
    draw_text_wrapped(surface, dialogue_text, font_body, BLACK,
                      rect.x + 20, rect.y + 54,
                      rect.width  - 40)


# ─────────────────────────────────────────────────────────────────────────────
# Choice buttons
# ─────────────────────────────────────────────────────────────────────────────
def draw_choices(surface, choices, rects, font, mouse_pos):
    """
    Draw choice buttons.
    choices   — list of choice text strings
    rects     — list of pygame.Rect for each button
    Returns   — index of hovered button or -1
    """
    hovered = -1
    for i, (text, rect) in enumerate(zip(choices, rects)):
        hover = rect.collidepoint(mouse_pos)
        if hover:
            hovered = i
        draw_button(surface, rect, text, font,
                    bg=DARK_GRAY, hover=hover)
    return hovered


def make_choice_rects(num_choices, base_x, base_y, btn_w, btn_h, gap=10):
    """
    Generate a list of Rects for choice buttons stacked vertically.
    """
    rects = []
    for i in range(num_choices):
        rects.append(pygame.Rect(base_x, base_y + i * (btn_h + gap), btn_w, btn_h))
    return rects


# ─────────────────────────────────────────────────────────────────────────────
# Stat bars
# ─────────────────────────────────────────────────────────────────────────────
def draw_stat_bar(surface, label, value, max_value,
                  x, y, w, h, font,
                  bar_color=WHITE, warn_color=(220, 80, 80)):
    """
    Draw a single stat bar.
    value / max_value controls fill width.
    Turns red if value is critically low (below 20%).
    """
    # Label
    label_surf = font.render(label, True, LIGHT_GRAY)
    surface.blit(label_surf, (x, y - label_surf.get_height() - 2))

    # Track
    pygame.draw.rect(surface, DARK_GRAY, (x, y, w, h), border_radius=3)

    # Fill
    fill_w   = int((value / max_value) * w)
    ratio    = value / max_value
    color    = warn_color if ratio < 0.2 else bar_color
    if fill_w > 0:
        pygame.draw.rect(surface, color, (x, y, fill_w, h), border_radius=3)

    # Border
    pygame.draw.rect(surface, MID_GRAY, (x, y, w, h), 1, border_radius=3)

    # Value text
    val_surf = font.render(f"{value}", True, MID_GRAY)
    surface.blit(val_surf, (x + w + 6, y + h // 2 - val_surf.get_height() // 2))


def draw_all_stats(surface, stats_dict, x, y, font,
                   bar_w=160, bar_h=10, gap=24, max_val=100):
    """
    Draw all stats from a dict like {"Hope": 70, "Calm": 50, ...}
    Returns the total height used.
    """
    for i, (label, value) in enumerate(stats_dict.items()):
        draw_stat_bar(surface, label, value, max_val,
                      x, y + i * gap, bar_w, bar_h, font)
    return len(stats_dict) * gap


# ─────────────────────────────────────────────────────────────────────────────
# Patient info card
# ─────────────────────────────────────────────────────────────────────────────
def draw_patient_info(surface, name, age, occupation, background,
                      rect, font_name, font_body, char_color=WHITE):
    """
    Draw the patient info card shown at the start of each session.
    """
    # Draw panel with white background and black border
    pygame.draw.rect(surface, WHITE, rect, border_radius=6)
    pygame.draw.rect(surface, BLACK, rect, 2, border_radius=6)

    y = rect.y + 16

    # Name + age in black
    header = font_name.render(f"{name},  {age}", True, BLACK)
    surface.blit(header, (rect.x + 16, y))
    y += header.get_height() + 8

    # Occupation in black
    occ = font_body.render(occupation, True, BLACK)
    surface.blit(occ, (rect.x + 16, y))
    y += occ.get_height() + 12

    # Divider
    pygame.draw.line(surface, MID_GRAY,
                     (rect.x + 12,    y),
                     (rect.right - 12, y), 1)
    y += 10

    # Background text wrapped in black
    draw_text_wrapped(surface, background, font_body, BLACK,
                      rect.x + 16, y, rect.width - 32)


# ─────────────────────────────────────────────────────────────────────────────
# Warning flash
# ─────────────────────────────────────────────────────────────────────────────
class WarningFlash:
    """
    A brief red border flash to warn the player a stat is critical.
    Call update(dt) each frame and draw(surface) to render.
    Trigger with trigger().
    """
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
        alpha  = int(180 * (self.timer / self.duration))
        overlay = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
        # Red border around screen edges
        border = 8
        pygame.draw.rect(overlay, (220, 60, 60, alpha),
                         (0, 0, self.screen_w, self.screen_h),
                         border)
        surface.blit(overlay, (0, 0))


# ─────────────────────────────────────────────────────────────────────────────
# Jump transform (sprite bounce when speaking)
# ─────────────────────────────────────────────────────────────────────────────
class JumpTransform:
    """
    Tracks a vertical bounce offset for a sprite.
    Call trigger() when the character starts speaking.
    Call update(dt) each frame.
    Use offset_y in your sprite draw call.
    """
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
        # Sine arc: goes up then comes back
        return int(self.height * math.sin(progress * math.pi))

    def trigger(self):
        self.active = True
        self.timer  = 0.0

    def update(self, dt):
        if self.active:
            self.timer += dt
            if self.timer >= self.duration:
                self.active = False
                self.timer  = 0.0


# ─────────────────────────────────────────────────────────────────────────────
# Sprite loader
# ─────────────────────────────────────────────────────────────────────────────
def load_sprite(char_name, emotion, size=None):
    """
    Load a character sprite from the sprites folder.
    char_name — "blue", "red", "player", "guide" etc.
    emotion   — "idle", "smile", "angry" etc.
    size      — optional (w, h) to scale to. If None uses original size.

    Returns the surface or a placeholder colored rect if not found.
    """
    path = f"Soft Hours/assets/images/sprites/{char_name}/{char_name}_{emotion}.png"
    try:
        surf = pygame.image.load(path).convert_alpha()
        if size:
            surf = pygame.transform.scale(surf, size)
        return surf
    except FileNotFoundError:
        # Placeholder: a gray rect with text
        w, h = size if size else (200, 400)
        placeholder = pygame.Surface((w, h), pygame.SRCALPHA)
        placeholder.fill((60, 60, 60, 200))
        pygame.draw.rect(placeholder, LIGHT_GRAY, (0, 0, w, h), 2)
        try:
            font = pygame.font.SysFont("arial", 14)
            label = font.render(f"{char_name}", True, LIGHT_GRAY)
            emo   = font.render(f"{emotion}",   True, MID_GRAY)
            placeholder.blit(label, (w // 2 - label.get_width() // 2, h // 2 - 16))
            placeholder.blit(emo,   (w // 2 - emo.get_width()   // 2, h // 2 + 4))
        except Exception:
            pass
        return placeholder


def load_background(name, size=None):
    """
    Load a background image.
    name — filename without extension e.g. "hospital_entrance"
    """
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


# ─────────────────────────────────────────────────────────────────────────────
# Overlay helpers
# ─────────────────────────────────────────────────────────────────────────────
def draw_dim_overlay(surface, alpha=160):
    """Draw a semi-transparent black overlay over the whole screen."""
    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, alpha))
    surface.blit(overlay, (0, 0))


def draw_centered_message(surface, message, font, color=WHITE,
                           sub_message=None, sub_font=None, sub_color=LIGHT_GRAY):
    """Draw a centered message on screen, with optional subtitle."""
    w, h = surface.get_size()
    text = font.render(message, True, color)
    surface.blit(text, (w // 2 - text.get_width() // 2,
                         h // 2 - text.get_height() // 2 - 20))
    if sub_message and sub_font:
        sub = sub_font.render(sub_message, True, sub_color)
        surface.blit(sub, (w // 2 - sub.get_width() // 2,
                            h // 2 + 20))