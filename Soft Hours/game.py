import pygame
import sys
import math
import json
import os

from shop        import Shop, ShopUI
from data_logger import DataLogger

# ── Game States ───────────────────────────────────────────────────────────────
STATE_MAIN_MENU  = "main_menu"
STATE_TUTORIAL   = "tutorial"
STATE_SESSION    = "session"
STATE_SHOP       = "shop"
STATE_GAME_OVER  = "game_over"
STATE_BAD_ENDING = "bad_ending"
STATE_STATS      = "stats"

# ── Character border colors ───────────────────────────────────────────────────
CHAR_COLORS = {
    "blue":   (100, 149, 237),
    "green":  (100, 200, 120),
    "orange": (230, 150,  80),
    "purple": (160, 100, 210),
    "red":    (210,  80,  80),
}

MAX_HEARTS = 5

WHITE       = (255, 255, 255)
BLACK       = (0,   0,   0)
NEAR_BLACK  = (10,  10,  10)
DARK_GRAY   = (40,  40,  40)
MID_GRAY    = (100, 100, 100)
LIGHT_GRAY  = (180, 180, 180)
DARK_RED    = (120, 30,  30)
GOLD        = (220, 180,  60)

# ── Settings persistence ──────────────────────────────────────────────────────
# game.py lives at Soft Hours/ root — saves go to Soft Hours/data/saves/
_HERE         = os.path.dirname(os.path.abspath(__file__))
SETTINGS_PATH = os.path.join(_HERE, "data", "saves", "settings.json")

def load_settings():
    defaults = {"bgm": 0.8, "sfx": 1.0}
    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        defaults["bgm"] = float(data.get("bgm", 0.8))
        defaults["sfx"] = float(data.get("sfx", 1.0))
    except Exception:
        pass
    return defaults

def save_settings(bgm_vol, sfx_vol):
    os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
    try:
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump({"bgm": round(bgm_vol, 3), "sfx": round(sfx_vol, 3)}, f)
    except Exception as e:
        print(f"[Settings] Could not save: {e}")

class Slider:
    def __init__(self, x, y, w, label, initial=1.0):
        self.x        = x
        self.y        = y
        self.w        = w
        self.label    = label
        self.value    = initial
        self.dragging = False
        self.track_h  = 4
        self.knob_r   = 8

    @property
    def knob_x(self):
        return int(self.x + self.value * self.w)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if (mx - self.knob_x) ** 2 + (my - self.y) ** 2 <= (self.knob_r + 4) ** 2:
                self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            raw        = (event.pos[0] - self.x) / self.w
            self.value = max(0.0, min(1.0, raw))
            return True
        return False

    def draw(self, surface, font):
        label_surf = font.render(self.label, True, WHITE)
        surface.blit(label_surf, (self.x, self.y - 28))
        pygame.draw.rect(surface, MID_GRAY,
                         (self.x, self.y - self.track_h // 2, self.w, self.track_h))
        fill_w = int(self.value * self.w)
        if fill_w > 0:
            pygame.draw.rect(surface, WHITE,
                             (self.x, self.y - self.track_h // 2, fill_w, self.track_h))
        pygame.draw.circle(surface, WHITE, (self.knob_x, self.y), self.knob_r)
        pygame.draw.circle(surface, BLACK, (self.knob_x, self.y), self.knob_r, 2)
        pct = font.render(f"{int(self.value * 100)}%", True, LIGHT_GRAY)
        surface.blit(pct, (self.x + self.w + 12, self.y - pct.get_height() // 2))

class SettingsPanel:
    def __init__(self, screen_w, screen_h, font_small, font_medium, font_large,
                 saved_bgm=0.8, saved_sfx=1.0):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.font_s   = font_small
        self.font_m   = font_medium
        self.font_l   = font_large
        self.visible  = False
        self.tab      = "sound"

        pw, ph    = 500, 360
        self.rect = pygame.Rect(screen_w // 2 - pw // 2,
                                screen_h // 2 - ph // 2, pw, ph)

        sx = self.rect.x + 60
        self.slider_bgm = Slider(sx, self.rect.y + 150, 340, "BGM Volume", saved_bgm)
        self.slider_sfx = Slider(sx, self.rect.y + 240, 340, "SFX Volume", saved_sfx)

        tab_y          = self.rect.y + 56
        self.btn_sound = pygame.Rect(self.rect.x + 70,  tab_y, 110, 36)
        self.btn_stats = pygame.Rect(self.rect.x + 210, tab_y, 110, 36)
        self.btn_close = pygame.Rect(self.rect.right - 38, self.rect.y + 10, 28, 28)

        self.overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        self.overlay.fill((0, 0, 0, 160))

    def toggle(self):
        self.visible = not self.visible
        if not self.visible:
            save_settings(self.slider_bgm.value, self.slider_sfx.value)

    def handle_event(self, event, game):
        if not self.visible:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.btn_close.collidepoint(event.pos):
                game.play_sound("click")
                self.visible = False
                save_settings(self.slider_bgm.value, self.slider_sfx.value)
                return True
            if self.btn_sound.collidepoint(event.pos):
                game.play_sound("click")
                self.tab = "sound"
                return True
            if self.btn_stats.collidepoint(event.pos):
                game.play_sound("click")
                self.tab = "stats"
                game.open_stats_panel()
                return True
        if self.tab == "sound":
            if self.slider_bgm.handle_event(event):
                pygame.mixer.music.set_volume(self.slider_bgm.value)
            if self.slider_sfx.handle_event(event):
                vol = self.slider_sfx.value
                for snd in game.sounds.values():
                    if snd:
                        snd.set_volume(vol)
        return True

    def draw(self, surface):
        if not self.visible:
            return
        surface.blit(self.overlay, (0, 0))
        pygame.draw.rect(surface, NEAR_BLACK, self.rect, border_radius=10)
        pygame.draw.rect(surface, WHITE,      self.rect, 2,  border_radius=10)
        title = self.font_l.render("Settings", True, WHITE)
        surface.blit(title, (self.rect.centerx - title.get_width() // 2,
                              self.rect.y + 14))
        pygame.draw.rect(surface, DARK_GRAY, self.btn_close, border_radius=4)
        x_surf = self.font_m.render("x", True, WHITE)
        surface.blit(x_surf, (self.btn_close.centerx - x_surf.get_width()  // 2,
                               self.btn_close.centery - x_surf.get_height() // 2))
        for btn, label, key in [
            (self.btn_sound, "Sound", "sound"),
            (self.btn_stats, "Stats", "stats"),
        ]:
            active = self.tab == key
            bg, fg = (WHITE, BLACK) if active else (DARK_GRAY, WHITE)
            pygame.draw.rect(surface, bg,    btn, border_radius=6)
            pygame.draw.rect(surface, WHITE, btn, 1,  border_radius=6)
            t = self.font_m.render(label, True, fg)
            surface.blit(t, (btn.centerx - t.get_width()  // 2,
                             btn.centery - t.get_height() // 2))
        if self.tab == "sound":
            self.slider_bgm.draw(surface, self.font_m)
            self.slider_sfx.draw(surface, self.font_m)
        elif self.tab == "stats":
            msg = self.font_m.render("Stats panel opened in a separate window.", True, LIGHT_GRAY)
            surface.blit(msg, (self.rect.centerx - msg.get_width() // 2,
                               self.rect.centery - msg.get_height() // 2))

TUTORIAL_PAGES = [
    {
        "guide": "lookplayer",
        "title": "Welcome to Soft Hours",
        "body": (
            "You are a therapist. Each session you meet a patient struggling "
            "with a mental health condition. Listen carefully and choose your "
            "words wisely — your responses affect their emotional stats."
        ),
    },
    {
        "guide": "lookplayer",
        "title": "Stats & Warnings",
        "body": (
            "Watch the stat panel on the right. Positive stats like Hope, "
            "Calm and Trust should stay high. Pressure stats like Exhaustion "
            "and Loneliness must stay low. A warning flashes red when a stat "
            "enters the danger zone. If any stat hits the critical limit the "
            "patient leaves."
        ),
    },
    {
        "guide": "lookdemon",
        "title": "The Weakness Debuff",
        "body": (
            "If you guess the patient's illness wrong at the end of a session "
            "you will receive the Weakness debuff. Under Weakness all bad "
            "dialogue choices deal double stat damage, and if the patient "
            "walks away you lose two hearts instead of one."
        ),
    },
    {
        "guide": "lookplayer",
        "title": "Shop & Hearts",
        "body": (
            "You start with five hearts. Lose them all and it is game over. "
            "After each session you earn coins. Open the shop to buy items "
            "like Coffee, Calming Tea, or a Case File that reveals the "
            "patient's illness before the session starts."
        ),
    },
    {
        "guide": "lookplayer",
        "title": "Illness Quiz",
        "body": (
            "At the end of every session you will be asked to identify the "
            "patient's illness. Guess correctly for a coin bonus. Guess wrong "
            "and you lose a few coins and gain the Weakness debuff for the "
            "next session. Good luck!"
        ),
    },
]

class TutorialOverlay:
    """Full-screen tutorial shown after clicking Begin. Blurs menu behind it."""

    GUIDE_W = 380
    GUIDE_H = 380

    def __init__(self, screen_w, screen_h, fonts, guide_sprites):
        self.screen_w      = screen_w
        self.screen_h      = screen_h
        self.fonts         = fonts
        self.guide_sprites = guide_sprites
        self.page          = 0
        self.visible       = True

        pw, ph       = 860, 480
        self.panel   = pygame.Rect(screen_w // 2 - pw // 2,
                                   screen_h // 2 - ph // 2, pw, ph)
        btn_y = self.panel.bottom - 58
        self.btn_next = pygame.Rect(self.panel.right  - 170, btn_y, 140, 40)
        self.btn_skip = pygame.Rect(self.panel.x + 30, btn_y, 120, 40)

        self.overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        self.overlay.fill((0, 0, 0, 200))

    def handle_event(self, event):
        if not self.visible:
            return "done"
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.btn_skip.collidepoint(event.pos):
                self.visible = False
                return "done"
            if self.btn_next.collidepoint(event.pos):
                self.page += 1
                if self.page >= len(TUTORIAL_PAGES):
                    self.visible = False
                    return "done"
        return None

    def draw(self, surface):
        if not self.visible:
            return
        surface.blit(self.overlay, (0, 0))
        pygame.draw.rect(surface, NEAR_BLACK, self.panel, border_radius=12)
        pygame.draw.rect(surface, WHITE,      self.panel, 2,  border_radius=12)

        page = TUTORIAL_PAGES[self.page]

        # Guide sprite (right side)
        guide_key  = page["guide"]
        guide_surf = self.guide_sprites.get(guide_key)
        if guide_surf:
            gs = pygame.transform.smoothscale(guide_surf, (self.GUIDE_W, self.GUIDE_H))
            gx = self.panel.right - self.GUIDE_W - 10
            gy = self.panel.y + self.panel.height // 2 - self.GUIDE_H // 2
            surface.blit(gs, (gx, gy))

        text_x = self.panel.x + 30
        text_w  = self.panel.width - self.GUIDE_W - 60
        text_y  = self.panel.y + 40

        pages_surf = self.fonts["small"].render(
            f"{self.page + 1} / {len(TUTORIAL_PAGES)}", True, MID_GRAY)
        surface.blit(pages_surf, (text_x, text_y))
        text_y += pages_surf.get_height() + 10

        title_surf = self.fonts["large"].render(page["title"], True, WHITE)
        surface.blit(title_surf, (text_x, text_y))
        text_y += title_surf.get_height() + 16

        words, line = page["body"].split(), ""
        line_h = self.fonts["small"].get_linesize() + 4
        for word in words:
            test = line + (" " if line else "") + word
            if self.fonts["small"].size(test)[0] <= text_w:
                line = test
            else:
                if line:
                    surface.blit(self.fonts["small"].render(line, True, LIGHT_GRAY),
                                 (text_x, text_y))
                    text_y += line_h
                line = word
        if line:
            surface.blit(self.fonts["small"].render(line, True, LIGHT_GRAY),
                         (text_x, text_y))

        is_last   = self.page == len(TUTORIAL_PAGES) - 1
        next_label = "Start!" if is_last else "Next ▶"
        for btn, label in [(self.btn_next, next_label), (self.btn_skip, "Skip")]:
            hover = btn.collidepoint(pygame.mouse.get_pos())
            bg, fg = (WHITE, BLACK) if hover else (DARK_GRAY, WHITE)
            pygame.draw.rect(surface, bg,    btn, border_radius=6)
            pygame.draw.rect(surface, WHITE, btn, 1, border_radius=6)
            t = self.fonts["medium"].render(label, True, fg)
            surface.blit(t, (btn.centerx - t.get_width()  // 2,
                             btn.centery - t.get_height() // 2))

class Game:
    def __init__(self, screen, width, height):
        self.screen  = screen
        self.width   = width
        self.height  = height
        self.state   = STATE_MAIN_MENU
        self.hearts  = MAX_HEARTS

        self.session_score   = 0
        self.patients_seen   = 0
        self.current_session = None
        self.start_btn       = pygame.Rect(0, 0, 0, 0)
        self.weakness_active = False   # Weakness debuff — set by illness quiz

        self._load_fonts()
        self._load_sounds()
        self._load_music()
        self._load_ui_assets()

        # Load saved volumes and apply them
        saved = load_settings()
        self.settings = SettingsPanel(self.width, self.height,
                                      self.font_small, self.font_medium, self.font_large,
                                      saved_bgm=saved["bgm"], saved_sfx=saved["sfx"])
        # Apply saved SFX volume to loaded sounds
        for snd in self.sounds.values():
            if snd:
                snd.set_volume(saved["sfx"])

        self.shop     = Shop()
        self.shop_ui  = ShopUI(self.width, self.height,
                               self.font_small, self.font_medium, self.font_large)
        self.logger   = DataLogger()

        # Guide sprites for tutorial
        from utils import get_sprite
        self.guide_sprites = {
            "lookplayer": get_sprite("guide", "lookplayer", None),
            "lookdemon":  get_sprite("guide", "lookdemon",  None),
        }

        self.tutorial = None
        self.menu_btn = pygame.Rect(0, 0, 0, 0)

        self._play_music("menu")

  

    def _load_fonts(self):
        path = "Soft Hours/assets/fonts/Pencilant Script.ttf"
        try:
            self.font_small  = pygame.font.Font(path, 16)
            self.font_medium = pygame.font.Font(path, 22)
            self.font_large  = pygame.font.Font(path, 34)
            self.font_title  = pygame.font.Font(path, 56)
        except FileNotFoundError:
            print("Warning: Pencilant Script.ttf not found. Using system font.")
            self.font_small  = pygame.font.SysFont("arial", 16)
            self.font_medium = pygame.font.SysFont("arial", 22)
            self.font_large  = pygame.font.SysFont("arial", 34)
            self.font_title  = pygame.font.SysFont("arial", 56)

    def _load_sounds(self):
        self.sounds = {}
        files = {
            "click":      "Soft Hours/assets/audio/sfx/click.mp3",
            "warning":    "Soft Hours/assets/audio/sfx/warning.mp3",
            "heart_lost": "Soft Hours/assets/audio/sfx/heart_lost.mp3",
        }
        for name, path in files.items():
            try:
                self.sounds[name] = pygame.mixer.Sound(path)
            except FileNotFoundError:
                print(f"Warning: SFX not found: {path}")
                self.sounds[name] = None

    def _load_music(self):
        self.music_tracks = {
            "menu":       "Soft Hours/assets/audio/bgm/menu_bgm.mp3",
            "ingame":     "Soft Hours/assets/audio/bgm/ingame_bgm.mp3",
            "bad_ending": "Soft Hours/assets/audio/bgm/bad_ending_bgm.mp3",
        }
        self.current_track = None

    def _load_ui_assets(self):
        try:
            raw = pygame.image.load("Soft Hours/assets/images/ui/setting.png").convert_alpha()
            self.setting_icon = pygame.transform.scale(raw, (36, 36))
        except FileNotFoundError:
            self.setting_icon = None
        self.setting_btn = pygame.Rect(16, 16, 36, 36)

        try:
            raw = pygame.image.load("Soft Hours/assets/images/ui/shop_icon.png").convert_alpha()
            self.shop_icon = pygame.transform.scale(raw, (36, 36))
        except FileNotFoundError:
            self.shop_icon = None
        self.shop_icon_btn = pygame.Rect(16, 60, 36, 36)

    def play_sound(self, name):
        sfx = self.sounds.get(name)
        if sfx:
            sfx.play()

    def _play_music(self, track):
        if self.current_track == track:
            return
        path = self.music_tracks.get(track)
        if not path:
            return
        try:
            pygame.mixer.music.load(path)
            vol = self.settings.slider_bgm.value if hasattr(self, "settings") else 0.8
            pygame.mixer.music.set_volume(vol)
            pygame.mixer.music.play(-1)
            self.current_track = track
        except FileNotFoundError:
            print(f"Warning: BGM not found: {path}")

  

    def change_state(self, new_state):
        self.state = new_state
        if new_state == STATE_MAIN_MENU:
            self._play_music("menu")
            self.current_session = None
        elif new_state == STATE_SESSION:
            self._play_music("ingame")
            self._start_session()
        elif new_state == STATE_BAD_ENDING:
            self._play_music("bad_ending")
        print(f"[Game] State -> {new_state}")

    def _start_session(self):
        from session import Session
        fonts = {
            "small":  self.font_small,
            "medium": self.font_medium,
            "large":  self.font_large,
            "title":  self.font_title,
        }
        self.current_session = Session(
            screen      = self.screen,
            fonts       = fonts,
            game        = self,
            shop        = self.shop,
            data_logger = self.logger,
            weakness_active = self.weakness_active,
        )
        self.patients_seen += 1

    def lose_heart(self, amount=1):
        self.play_sound("heart_lost")
        self.hearts -= amount
        self.hearts  = max(0, self.hearts)   # floor at 0, never go negative
        print(f"[Game] Hearts remaining: {self.hearts}")
        if self.hearts <= 0 and self.state != STATE_GAME_OVER:
            self.change_state(STATE_GAME_OVER)

    def open_stats_panel(self):
        try:
            from stats_panel.dashboard import open_dashboard
            open_dashboard()
        except Exception as e:
            print(f"[Game] Stats panel error: {e}")

  

    def handle_event(self, event):
        # Tutorial intercepts ALL events while active
        if self.state == STATE_TUTORIAL and self.tutorial:
            result = self.tutorial.handle_event(event)
            if result == "done":
                self.change_state(STATE_SESSION)
            return

        if self.settings.handle_event(event, self):
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.setting_btn.collidepoint(event.pos):
                self.play_sound("click")
                self.settings.toggle()
                return
            # Return-to-menu button (in-session)
            if self.state == STATE_SESSION and self.menu_btn.collidepoint(event.pos):
                self.play_sound("click")
                self.change_state(STATE_MAIN_MENU)
                return

        if self.state == STATE_MAIN_MENU:
            self._handle_main_menu(event)
        elif self.state == STATE_SESSION:
            self._handle_session(event)
        elif self.state == STATE_GAME_OVER:
            self._handle_gameover(event)

    def _handle_main_menu(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            self._begin_clicked()
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.start_btn.collidepoint(event.pos):
                self._begin_clicked()

    def _begin_clicked(self):
        self.play_sound("click")
        self.tutorial = TutorialOverlay(
            self.width, self.height,
            {"small": self.font_small, "medium": self.font_medium,
             "large": self.font_large},
            self.guide_sprites,
        )
        self.state = STATE_TUTORIAL

    def _handle_session(self, event):
        # Shop UI
        if self.shop_ui.handle_event(event, self.shop, self):
            return
        # Shop icon
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.shop_icon_btn.collidepoint(event.pos):
                self.play_sound("click")
                self.shop_ui.toggle()
                return
        # Session
        if self.current_session:
            self.current_session.handle_event(event)

    def _handle_gameover(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            self._full_reset()
        # Only reset on click if the user is actually ON the game-over screen
        # (not just a click that happened to propagate from the quiz)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.state == STATE_GAME_OVER:
                self._full_reset()

    def _full_reset(self):
        self.hearts          = MAX_HEARTS
        self.session_score   = 0
        self.patients_seen   = 0
        self.weakness_active = False
        self.shop            = Shop()
        self.shop_ui         = ShopUI(self.width, self.height,
                                      self.font_small, self.font_medium, self.font_large)
        self.logger          = DataLogger()
        self.change_state(STATE_MAIN_MENU)

  

    def update(self, dt):
        if self.state == STATE_SESSION:
            if self.current_session:
                self.current_session.update(dt)
                if self.current_session.is_done():
                    self.current_session = None
                    self._start_session()
            self.shop_ui.update(dt)

  

    def draw(self):
        self.screen.fill(WHITE if self.state == STATE_MAIN_MENU else NEAR_BLACK)

        if self.state == STATE_MAIN_MENU:
            self._draw_main_menu()
        elif self.state == STATE_TUTORIAL:
            self.screen.fill(WHITE)
            self._draw_main_menu()
            if self.tutorial:
                self.tutorial.draw(self.screen)
        elif self.state == STATE_SESSION:
            self._draw_session()
        elif self.state == STATE_GAME_OVER:
            self._draw_gameover()
        elif self.state == STATE_BAD_ENDING:
            self._draw_bad_ending()

        if self.state not in (STATE_MAIN_MENU, STATE_TUTORIAL,
                              STATE_GAME_OVER, STATE_BAD_ENDING, STATE_STATS):
            self._draw_hearts()
            self._draw_shop_icon()
            self._draw_menu_btn()
            if self.weakness_active:
                self._draw_weakness_indicator()

        self._draw_setting_icon()
        if self.state != STATE_TUTORIAL:
            self.settings.draw(self.screen)

        if self.state == STATE_SESSION:
            self.shop_ui.draw(self.screen, self.shop)

    def _draw_setting_icon(self):
        is_light   = self.state == STATE_MAIN_MENU
        icon_color = BLACK if is_light else WHITE
        box_color  = BLACK if is_light else WHITE
        
        box = pygame.Rect(self.setting_btn.x - 6, self.setting_btn.y - 6, 
                         self.setting_btn.w + 12, self.setting_btn.h + 12)
        pygame.draw.rect(self.screen, box_color, box, 2, border_radius=6)
        
        if self.setting_icon:
            self.screen.blit(self.setting_icon, self.setting_btn.topleft)
        else:
            cx, cy = self.setting_btn.center
            pygame.draw.circle(self.screen, icon_color, (cx, cy), 14, 2)
            pygame.draw.circle(self.screen, icon_color, (cx, cy),  6, 2)
            for angle in range(0, 360, 45):
                rad = math.radians(angle)
                x1  = int(cx + 10 * math.cos(rad))
                y1  = int(cy + 10 * math.sin(rad))
                x2  = int(cx + 14 * math.cos(rad))
                y2  = int(cy + 14 * math.sin(rad))
                pygame.draw.line(self.screen, icon_color, (x1, y1), (x2, y2), 2)

    def _draw_shop_icon(self):
        box = pygame.Rect(self.shop_icon_btn.x - 6, self.shop_icon_btn.y - 6,
                         self.shop_icon_btn.w + 12, self.shop_icon_btn.h + 12)
        pygame.draw.rect(self.screen, WHITE, box, 2, border_radius=6)
        
        if self.shop_icon:
            self.screen.blit(self.shop_icon, self.shop_icon_btn.topleft)
        else:
            cx, cy = self.shop_icon_btn.center
            pygame.draw.rect(self.screen, WHITE,
                             (cx - 12, cy - 10, 24, 20), 2, border_radius=3)
            pygame.draw.line(self.screen, WHITE,
                             (cx - 6, cy - 10), (cx - 6, cy - 16), 2)
            pygame.draw.line(self.screen, WHITE,
                             (cx + 6, cy - 10), (cx + 6, cy - 16), 2)

    def _draw_menu_btn(self):
        """Return-to-menu button shown during a session (below shop icon)."""
        btn_w, btn_h = 110, 30
        bx = self.shop_icon_btn.x - 6
        by = self.shop_icon_btn.bottom + 12
        self.menu_btn = pygame.Rect(bx, by, btn_w, btn_h)
        hover = self.menu_btn.collidepoint(pygame.mouse.get_pos())
        bg, fg = (WHITE, BLACK) if hover else (DARK_GRAY, WHITE)
        pygame.draw.rect(self.screen, bg,    self.menu_btn, border_radius=6)
        pygame.draw.rect(self.screen, WHITE, self.menu_btn, 1, border_radius=6)
        t = self.font_small.render("◀ Menu", True, fg)
        self.screen.blit(t, (self.menu_btn.centerx - t.get_width()  // 2,
                              self.menu_btn.centery - t.get_height() // 2))

    def _draw_weakness_indicator(self):
        """Red badge in top-centre warning player that Weakness is active."""
        surf = self.font_small.render("⚠ WEAKNESS ACTIVE", True, (220, 60, 60))
        bx   = self.width // 2 - surf.get_width() // 2 - 10
        by   = 10
        bw   = surf.get_width() + 20
        bh   = surf.get_height() + 8
        pygame.draw.rect(self.screen, DARK_GRAY,     (bx, by, bw, bh), border_radius=6)
        pygame.draw.rect(self.screen, (220, 60, 60), (bx, by, bw, bh), 2, border_radius=6)
        self.screen.blit(surf, (bx + 10, by + 4))

    def _draw_main_menu(self):
        title = self.font_title.render("Soft Hours", True, BLACK)
        self.screen.blit(title, (self.width  // 2 - title.get_width()  // 2, 200))
        pygame.draw.line(self.screen, BLACK,
                         (self.width // 2 - 180, 290),
                         (self.width // 2 + 180, 290), 1)
        btn_w, btn_h   = 200, 50
        bx             = self.width  // 2 - btn_w // 2
        by             = 320
        self.start_btn = pygame.Rect(bx, by, btn_w, btn_h)
        pygame.draw.rect(self.screen, BLACK, self.start_btn, border_radius=6)
        label = self.font_medium.render("Begin", True, WHITE)
        self.screen.blit(label,
                         (self.start_btn.centerx - label.get_width()  // 2,
                          self.start_btn.centery - label.get_height() // 2))

    def _draw_session(self):
        if self.current_session:
            self.current_session.draw()

    def _draw_gameover(self):
        text = self.font_large.render("Game Over", True, WHITE)
        self.screen.blit(text, (self.width  // 2 - text.get_width()  // 2, 280))
        hint = self.font_medium.render("Press R to restart", True, LIGHT_GRAY)
        self.screen.blit(hint, (self.width  // 2 - hint.get_width()  // 2, 360))

    def _draw_bad_ending(self):
        text = self.font_large.render("...", True, LIGHT_GRAY)
        self.screen.blit(text, (self.width  // 2 - text.get_width()  // 2, 300))

    def _draw_hearts(self):
        x_start = self.width - 50
        y, radius, gap = 40, 12, 32
        box_left   = x_start - (MAX_HEARTS - 1) * gap - radius - 8
        box_top    = y - radius - 8
        box_width  = (MAX_HEARTS - 1) * gap + 2 * radius + 16
        box_height = 2 * radius + 16
        pygame.draw.rect(self.screen, WHITE,
                         (box_left, box_top, box_width, box_height), border_radius=8)
        pygame.draw.rect(self.screen, BLACK,
                         (box_left, box_top, box_width, box_height), 2, border_radius=8)
        for i in range(MAX_HEARTS):
            x = x_start - i * gap
            if i < self.hearts:
                pygame.draw.circle(self.screen, DARK_RED, (x, y), radius)
                pygame.draw.circle(self.screen, BLACK,    (x, y), radius, 2)
            else:
                pygame.draw.circle(self.screen, (180, 180, 180), (x, y), radius)
                pygame.draw.circle(self.screen, BLACK,           (x, y), radius, 2)