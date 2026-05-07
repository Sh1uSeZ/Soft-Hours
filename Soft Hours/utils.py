import pygame
import math
import os
import json
import random


def lerp(a, b, t):
    return a + (b - a) * t


def clamp(value, min_val, max_val):
    return max(min_val, min(max_val, value))


def ease_out(t):
    return 1 - (1 - t) ** 2


def ease_in_out(t):
    return t * t * (3 - 2 * t)


def jump_transform(surface, sprite, x, y, offset_y):
    surface.blit(sprite, (x, y - offset_y))


def draw_sprite_centered(surface, sprite, cx, y):
    x = cx - sprite.get_width() // 2
    surface.blit(sprite, (x, y))


def scale_sprite(sprite, target_width=None, target_height=None):
    w, h = sprite.get_width(), sprite.get_height()
    if target_width:
        ratio = target_width / w
        return pygame.transform.scale(sprite, (target_width, int(h * ratio)))
    elif target_height:
        ratio = target_height / h
        return pygame.transform.scale(sprite, (int(w * ratio), target_height))
    return sprite


def flip_sprite(sprite, horizontal=True, vertical=False):
    return pygame.transform.flip(sprite, horizontal, vertical)


def grayscale_surface(surface):
    gray = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    for x in range(surface.get_width()):
        for y in range(surface.get_height()):
            r, g, b, a = surface.get_at((x, y))
            lum = int(0.299 * r + 0.587 * g + 0.114 * b)
            gray.set_at((x, y), (lum, lum, lum, a))
    return gray


_sprite_cache = {}


def get_sprite(char_name, emotion, size=None):
    key = f"{char_name}_{emotion}_{size}"
    if key in _sprite_cache:
        return _sprite_cache[key]

    path = f"Soft Hours/assets/images/sprites/{char_name}/{char_name}_{emotion}.png"
    try:
        surf = pygame.image.load(path).convert_alpha()
        if size:
            surf = pygame.transform.scale(surf, size)
    except FileNotFoundError:
        w, h = size if size else (200, 400)
        surf = _make_placeholder(char_name, emotion, w, h)

    _sprite_cache[key] = surf
    return surf


def get_background(name, size=None):
    key = f"bg_{name}_{size}"
    if key in _sprite_cache:
        return _sprite_cache[key]

    path = f"Soft Hours/assets/images/bg/{name}.png"
    try:
        surf = pygame.image.load(path).convert()
        if size:
            surf = pygame.transform.scale(surf, size)
    except FileNotFoundError:
        w, h = size if size else (1280, 720)
        surf = pygame.Surface((w, h))
        surf.fill((20, 20, 20))

    _sprite_cache[key] = surf
    return surf


def get_ui_image(name, size=None):
    key = f"ui_{name}_{size}"
    if key in _sprite_cache:
        return _sprite_cache[key]

    path = f"Soft Hours/assets/images/ui/{name}.png"
    try:
        surf = pygame.image.load(path).convert_alpha()
        if size:
            surf = pygame.transform.scale(surf, size)
    except FileNotFoundError:
        w, h = size if size else (64, 64)
        surf = _make_placeholder(name, "", w, h)

    _sprite_cache[key] = surf
    return surf


def clear_sprite_cache():
    global _sprite_cache
    _sprite_cache = {}


def _make_placeholder(name, label, w, h):
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    surf.fill((60, 60, 60, 180))
    pygame.draw.rect(surf, (150, 150, 150), (0, 0, w, h), 2)
    try:
        font  = pygame.font.SysFont("arial", 13)
        t1    = font.render(str(name),  True, (180, 180, 180))
        t2    = font.render(str(label), True, (120, 120, 120))
        surf.blit(t1, (w // 2 - t1.get_width() // 2, h // 2 - 16))
        surf.blit(t2, (w // 2 - t2.get_width() // 2, h // 2 + 4))
    except Exception:
        pass
    return surf


_random_info_cache = None


def load_random_info():
    global _random_info_cache
    if _random_info_cache is not None:
        return _random_info_cache
    try:
        with open("data/patients/random_info.json", "r", encoding="utf-8") as f:
            _random_info_cache = json.load(f)
    except FileNotFoundError:
        print("[Utils] random_info.json not found.")
        _random_info_cache = {}
    return _random_info_cache


def random_patient_name():
    info   = load_random_info()
    if not info:
        return "Unknown", "Patient", "english"
    origin = random.choice(["thai", "japanese", "english"])
    first  = random.choice(info["first_names"][origin])
    last   = random.choice(info["last_names"][origin])
    return first, last, origin


def random_patient_info():
    info = load_random_info()
    if not info:
        return {
            "name":       "Unknown Patient",
            "age":        25,
            "occupation": "Unknown",
            "background": "No background available.",
        }

    origin     = random.choice(["thai", "japanese", "english"])
    first      = random.choice(info["first_names"][origin])
    last       = random.choice(info["last_names"][origin])
    name       = f"{first} {last}"
    age        = random.randint(info["age_range"]["min"], info["age_range"]["max"])
    occupation = random.choice(info["occupations"])
    bg_key     = "college_student" if occupation == "College Student" else "office_worker"
    background = random.choice(info["backgrounds"][bg_key])

    return {
        "name":       name,
        "age":        age,
        "occupation": occupation,
        "background": background,
    }


def wrap_text(text, font, max_width):
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

    return lines


def render_wrapped_text(surface, text, font, color, x, y, max_width, line_spacing=6):
    lines  = wrap_text(text, font, max_width)
    line_h = font.get_linesize() + line_spacing

    for i, line in enumerate(lines):
        surf = font.render(line, True, color)
        surface.blit(surf, (x, y + i * line_h))

    return len(lines) * line_h


class Timer:
    def __init__(self, duration):
        self.duration = duration
        self.elapsed  = 0.0
        self.running  = False
        self.finished = False

    def start(self):
        self.elapsed  = 0.0
        self.running  = True
        self.finished = False

    def reset(self):
        self.elapsed  = 0.0
        self.finished = False

    def update(self, dt):
        if not self.running or self.finished:
            return False
        self.elapsed += dt
        if self.elapsed >= self.duration:
            self.finished = True
            self.running  = False
            return True
        return False

    @property
    def progress(self):
        return clamp(self.elapsed / self.duration, 0.0, 1.0)


class FadeTransition:
    def __init__(self, duration=0.4):
        self.duration  = duration
        self.timer     = 0.0
        self.direction = "in"
        self.active    = False
        self.done      = False
        self._overlay  = None

    def _get_overlay(self, surface):
        if (self._overlay is None or
                self._overlay.get_size() != surface.get_size()):
            self._overlay = pygame.Surface(surface.get_size())
            self._overlay.fill((0, 0, 0))
        return self._overlay

    def fade_in(self):
        self.direction = "in"
        self.timer     = 0.0
        self.active    = True
        self.done      = False

    def fade_out(self):
        self.direction = "out"
        self.timer     = 0.0
        self.active    = True
        self.done      = False

    def update(self, dt):
        if not self.active or self.done:
            return False
        self.timer += dt
        if self.timer >= self.duration:
            self.done   = True
            self.active = False
            return True
        return False

    def draw(self, surface):
        if not self.active and not self.done:
            return
        overlay = self._get_overlay(surface)
        t       = clamp(self.timer / self.duration, 0.0, 1.0)
        alpha   = int(255 * ease_in_out(t)) if self.direction == "out" else int(255 * (1 - ease_in_out(t)))
        overlay.set_alpha(alpha)
        surface.blit(overlay, (0, 0))


class PulseEffect:
    def __init__(self, speed=2.0, min_val=80, max_val=255):
        self.speed   = speed
        self.min_val = min_val
        self.max_val = max_val
        self.elapsed = 0.0

    def update(self, dt):
        self.elapsed += dt

    @property
    def value(self):
        t = (math.sin(self.elapsed * self.speed) + 1) / 2
        return int(lerp(self.min_val, self.max_val, t))
