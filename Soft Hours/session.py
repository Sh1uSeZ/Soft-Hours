import pygame
import random
import time

from patient     import create_random_patient, load_random_info, PATIENT_CLASSES
from stats       import StatSystem, draw_stats_panel
from dialogue    import DialogueManager
from data_logger import DataLogger
from ui          import (
    draw_panel, draw_button, draw_dialogue_box,
    draw_choices, make_choice_rects,
    draw_patient_info, draw_dim_overlay,
    draw_centered_message, WarningFlash, JumpTransform,
    load_sprite, load_background
)
from utils       import (
    get_sprite, get_background, FadeTransition,
    Timer, PulseEffect, render_wrapped_text, clamp
)
from shop        import Shop, ShopUI

WHITE      = (255, 255, 255)
BLACK      = (0,   0,   0)
NEAR_BLACK = (10,  10,  10)
DARK_GRAY  = (40,  40,  40)
MID_GRAY   = (100, 100, 100)
LIGHT_GRAY = (180, 180, 180)
GOLD       = (220, 180,  60)
WARN_RED   = (220,  60,  60)
ACCENT_RED = (180,  40,  40)

SCREEN_W, SCREEN_H = 1280, 720

PATIENT_SPRITE_W = 1024
PATIENT_SPRITE_H = 1024
PATIENT_X        = 640
PATIENT_Y        = -125

PLAYER_SPRITE_W  = 1024
PLAYER_SPRITE_H  = 1024
PLAYER_X         = -225
PLAYER_Y         = 50

# Guide drawn at a comfortable size in the bottom-right corner
GUIDE_SPRITE_W   = 380
GUIDE_SPRITE_H   = 380
GUIDE_X          = SCREEN_W - GUIDE_SPRITE_W + 40    # slightly clipped on right edge
GUIDE_Y          = SCREEN_H - GUIDE_SPRITE_H          # flush with bottom

DIALOGUE_X = 360
DIALOGUE_Y = 420
DIALOGUE_W = 880
DIALOGUE_H = 130

CHOICE_X   = 640
CHOICE_Y   = 430
CHOICE_W   = 580
CHOICE_H   = 50     # slightly taller for readability
CHOICE_GAP = 8

STAT_X = 960
STAT_Y = 80

INFO_X = 360
INFO_Y = 80
INFO_W = 560
INFO_H = 200

# How many warnings (per patient session) trigger the guide appearance
GUIDE_MAX_APPEARANCES = 3

ALL_ILLNESSES      = ["overthinking", "anger", "depression", "trauma", "burnout"]
QUIZ_CORRECT_BONUS = 20
QUIZ_WRONG_PENALTY = 10

PHASE_INTRO    = "intro"
PHASE_DIALOGUE = "dialogue"
PHASE_QUIZ     = "quiz"
PHASE_OUTCOME  = "outcome"
PHASE_DONE     = "done"


# ─────────────────────────────────────────────────────────────────────────────
# Guide bubble — guide sprite + speech bubble, only shown on warnings 1-3
# ─────────────────────────────────────────────────────────────────────────────
GUIDE_LINES = [
    # 1st warning
    "Careful! A stat just hit the danger zone.",
    # 2nd warning
    "Another warning! Watch those stats closely.",
    # 3rd warning
    "Third warning — this patient is on the edge!",
]


class GuideBubble:
    """
    Draws the guide sprite + a speech bubble at the bottom-right corner.
    Visible only for GUIDE_MAX_APPEARANCES warnings per session.
    Always drawn LAST (top z-order) in Session.draw().
    """
    BUBBLE_W   = 280
    BUBBLE_H   = 70
    DISPLAY_DUR = 4.0   # seconds to show per appearance

    def __init__(self, guide_sprites):
        self.sprites      = guide_sprites   # {"lookplayer": surf, "lookdemon": surf}
        self.visible      = False
        self.timer        = 0.0
        self.appearances  = 0              # how many times shown this session
        self.current_line = ""
        self.state        = "lookdemon"    # sprite face

    def trigger(self):
        """Call when a warning fires. Shows guide if under the limit."""
        if self.appearances >= GUIDE_MAX_APPEARANCES:
            return
        self.appearances  += 1
        self.visible       = True
        self.timer         = self.DISPLAY_DUR
        self.current_line  = (GUIDE_LINES[self.appearances - 1]
                              if self.appearances <= len(GUIDE_LINES) else "")
        self.state         = "lookdemon"

    def update(self, dt):
        if self.visible:
            self.timer -= dt
            if self.timer <= 0:
                self.visible = False

    def draw(self, surface, fonts):
        """Always called last so guide renders on top of everything."""
        if not self.visible:
            return

        # Guide sprite
        surf = self.sprites.get(self.state, self.sprites.get("lookplayer"))
        if surf:
            gs = pygame.transform.scale(surf, (GUIDE_SPRITE_W, GUIDE_SPRITE_H))
            surface.blit(gs, (GUIDE_X, GUIDE_Y))

        # Speech bubble (above guide sprite, slightly to the left)
        bx = GUIDE_X - self.BUBBLE_W + 40
        by = GUIDE_Y - self.BUBBLE_H - 10

        pygame.draw.rect(surface, WHITE, (bx, by, self.BUBBLE_W, self.BUBBLE_H),
                         border_radius=10)
        pygame.draw.rect(surface, WARN_RED, (bx, by, self.BUBBLE_W, self.BUBBLE_H),
                         2, border_radius=10)

        # Tail triangle pointing down-right toward guide
        tail_pts = [
            (bx + self.BUBBLE_W - 30, by + self.BUBBLE_H),
            (bx + self.BUBBLE_W - 10, by + self.BUBBLE_H),
            (bx + self.BUBBLE_W + 5,  by + self.BUBBLE_H + 20),
        ]
        pygame.draw.polygon(surface, WHITE, tail_pts)
        pygame.draw.lines(surface, WARN_RED, False,
                          [tail_pts[0], tail_pts[2], tail_pts[1]], 2)

        # Text (word-wrapped inside bubble)
        pad = 10
        words, line = self.current_line.split(), ""
        lines_out = []
        for word in words:
            test = line + (" " if line else "") + word
            if fonts["small"].size(test)[0] <= self.BUBBLE_W - pad * 2:
                line = test
            else:
                if line:
                    lines_out.append(line)
                line = word
        if line:
            lines_out.append(line)

        lh = fonts["small"].get_linesize() + 2
        ty = by + pad
        for l in lines_out:
            t = fonts["small"].render(l, True, BLACK)
            surface.blit(t, (bx + pad, ty))
            ty += lh


# ─────────────────────────────────────────────────────────────────────────────
# IllnessQuiz
# ─────────────────────────────────────────────────────────────────────────────
class IllnessQuiz:
    BTN_W, BTN_H = 220, 48
    BTN_GAP      = 12

    def __init__(self, screen, fonts, correct_illness):
        self.screen          = screen
        self.fonts           = fonts
        self.correct_illness = correct_illness
        self.options         = self._build_options()
        self.selected        = None
        self.result          = None
        self.result_timer    = Timer(2.5)
        self.btn_rects       = []
        self._build_rects()

    def _build_options(self):
        opts = list(ALL_ILLNESSES)
        random.shuffle(opts)
        return opts

    def _build_rects(self):
        total_w = self.BTN_W * 2 + self.BTN_GAP
        start_x = SCREEN_W // 2 - total_w // 2
        start_y = SCREEN_H // 2 + 10
        self.btn_rects = []
        cols = 2
        for i in range(len(self.options)):
            col = i % cols
            row = i // cols
            x   = start_x + col * (self.BTN_W + self.BTN_GAP)
            y   = start_y + row * (self.BTN_H + self.BTN_GAP)
            self.btn_rects.append(pygame.Rect(x, y, self.BTN_W, self.BTN_H))
        # Centre lone 5th button
        if len(self.options) % 2 == 1:
            last = len(self.options) - 1
            row  = last // cols
            self.btn_rects[last] = pygame.Rect(
                SCREEN_W // 2 - self.BTN_W // 2,
                start_y + row * (self.BTN_H + self.BTN_GAP),
                self.BTN_W, self.BTN_H)

    def handle_event(self, event):
        if self.result is not None:
            return None
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, rect in enumerate(self.btn_rects):
                if rect.collidepoint(event.pos):
                    self.selected = i
                    self.result   = ("correct" if self.options[i] == self.correct_illness
                                     else "wrong")
                    self.result_timer.start()
                    return self.result
        return None

    def update(self, dt):
        if self.result is not None:
            return self.result_timer.update(dt)
        return False

    def draw(self):
        draw_dim_overlay(self.screen, alpha=190)

        panel_w, panel_h = 700, 170
        panel_rect = pygame.Rect(SCREEN_W // 2 - panel_w // 2,
                                 SCREEN_H // 2 - panel_h - 16,
                                 panel_w, panel_h)
        pygame.draw.rect(self.screen, WHITE, panel_rect, border_radius=12)
        pygame.draw.rect(self.screen, BLACK, panel_rect, 2,  border_radius=12)

        q = self.fonts["large"].render("What was this patient's condition?", True, BLACK)
        self.screen.blit(q, (SCREEN_W // 2 - q.get_width() // 2, panel_rect.y + 18))

        hint = self.fonts["small"].render(
            f"Correct: +{QUIZ_CORRECT_BONUS} coins     "
            f"Wrong: −{QUIZ_WRONG_PENALTY} coins + Weakness debuff",
            True, MID_GRAY)
        self.screen.blit(hint, (SCREEN_W // 2 - hint.get_width() // 2,
                                 panel_rect.y + 68))

        mouse_pos = pygame.mouse.get_pos()
        for i, (illness, rect) in enumerate(zip(self.options, self.btn_rects)):
            if self.result is not None:
                if illness == self.correct_illness:
                    bg, fg = (60, 160, 80), WHITE
                elif i == self.selected:
                    bg, fg = (180, 50, 50), WHITE
                else:
                    bg, fg = WHITE, MID_GRAY
            else:
                hover = rect.collidepoint(mouse_pos)
                bg, fg = ((220, 220, 220) if hover else WHITE), BLACK

            pygame.draw.rect(self.screen, bg,    rect, border_radius=8)
            pygame.draw.rect(self.screen, BLACK, rect, 1, border_radius=8)
            label = illness.replace("_", " ").title()
            t = self.fonts["medium"].render(label, True, fg)
            self.screen.blit(t, (rect.centerx - t.get_width()  // 2,
                                  rect.centery - t.get_height() // 2))

        if self.result == "correct":
            fb = self.fonts["large"].render(
                f"Correct!  +{QUIZ_CORRECT_BONUS} coins", True, (40, 160, 60))
        elif self.result == "wrong":
            fb = self.fonts["large"].render(
                f"Wrong!  −{QUIZ_WRONG_PENALTY} coins  +  Weakness", True, WARN_RED)
        else:
            return
        self.screen.blit(fb, (SCREEN_W // 2 - fb.get_width() // 2,
                                self.btn_rects[-1].bottom + 14))


# ─────────────────────────────────────────────────────────────────────────────
# Session
# ─────────────────────────────────────────────────────────────────────────────
class Session:
    """
    Fixed issues in this version:
      - _fail_handled flag: _handle_fail() can only fire ONCE per session
        (prevents multiple heart losses from is_critical() firing every frame)
      - Guide only appears on warnings 1-3, always drawn at top z-order
      - Dialogue box + choices use white background / black text
      - Weakness heart loss = 2 ONLY when weakness_active at time of fail;
        weakness does NOT stack beyond ×2 per fail event
      - Choice positions shuffle every turn (done in dialogue.py)
    """

    def __init__(self, screen, fonts, game, shop, data_logger,
                 weakness_active=False):
        self.screen  = screen
        self.fonts   = fonts
        self.game    = game
        self.shop    = shop
        self.logger  = data_logger

        self.phase   = PHASE_INTRO
        self.outcome = None

        # Weakness: doubles negative stat hits AND costs 2 hearts on fail
        self.weakness_active = weakness_active

        # Critical-fail guard — prevents multiple triggers per session
        self._fail_handled = False

        # Patient + systems
        self._info_pool   = load_random_info()
        self.patient      = create_random_patient(self._info_pool)
        self.stat_system  = StatSystem(self.patient)
        self.dialogue_mgr = DialogueManager(self.patient, self.stat_system)

        # Push any existing turn effects from shop into dialogue manager
        self.dialogue_mgr.focus_turns_left   = shop.get_turn_effect("focus_notes")
        self.dialogue_mgr.empathy_turns_left  = shop.get_turn_effect("empathy_boost")

        # Shop session effects
        self.illness_revealed    = self.shop.has_effect("reveal_illness")
        if self.illness_revealed:
            self.shop.consume_effect("reveal_illness")
        self.slow_drain          = self.shop.has_effect("slow_drain")
        self.ignore_next_warning = self.shop.has_effect("ignore_warning")

        # Apply coffee stat boost at session start
        if self.shop.has_effect("coffee_applied"):
            pass  # handled at buy time
        # Apply coffee if bought (stat item)
        coffee_item = self.shop._get_item("coffee")
        # (coffee effect is applied by use_stat_item externally if needed)

        # Animations
        self.patient_jump = JumpTransform(height=14, duration=0.35)
        self.player_jump  = JumpTransform(height=8,  duration=0.28)
        self.warn_flash   = WarningFlash(SCREEN_W, SCREEN_H)
        self.fade         = FadeTransition(duration=0.4)
        self.fade.fade_in()

        self.intro_timer   = Timer(3.5)
        self.intro_timer.start()
        self.outcome_timer = Timer(2.0)
        self.pulse         = PulseEffect(speed=3.0, min_val=100, max_val=220)

        self.player_emotion      = "idle"
        self.quiz                = None
        self.bg                  = get_background("hospital_entrance", (SCREEN_W, SCREEN_H))
        self.choice_rects        = []
        self.warning_label_timer = 0.0

        # Guide bubble — only shown for first 3 warnings
        self._load_sprites()
        self.guide_bubble = GuideBubble(self.guide_sprites)

        print(f"[Session] Started: {self.patient}  weakness={weakness_active}")

    # ── Sprites ───────────────────────────────────────────────────────────────

    def _load_sprites(self):
        color = self.patient.sprite_color
        self.patient_sprites = {
            emo: get_sprite(color, emo, (PATIENT_SPRITE_W, PATIENT_SPRITE_H))
            for emo in ["idle", "smile", "angry", "concern", "cry", "shock"]
        }
        self.player_sprites = {
            emo: get_sprite("player", emo, (PLAYER_SPRITE_W, PLAYER_SPRITE_H))
            for emo in ["idle", "happy", "sad", "angry", "anxious", "thinking",
                        "concerned", "surprised", "closeeye", "drysmile",
                        "shock", "surprise", "concern", "cry"]
        }
        self.guide_sprites = {
            s: get_sprite("guide", s, (GUIDE_SPRITE_W, GUIDE_SPRITE_H))
            for s in ["lookdemon", "lookplayer"]
        }

    def _get_patient_sprite(self):
        return self.patient_sprites.get(self.patient.emotion,
                                        self.patient_sprites["idle"])

    def _get_player_sprite(self):
        return self.player_sprites.get(self.player_emotion,
                                       self.player_sprites["idle"])

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, dt):
        self.fade.update(dt)
        self.warn_flash.update(dt)
        self.pulse.update(dt)
        self.patient_jump.update(dt)
        self.player_jump.update(dt)
        self.guide_bubble.update(dt)

        if self.warning_label_timer > 0:
            self.warning_label_timer -= dt

        if self.phase == PHASE_INTRO:
            if self.intro_timer.update(dt):
                self.phase = PHASE_DIALOGUE

        elif self.phase == PHASE_DIALOGUE:
            self.dialogue_mgr.update(dt)
            # ── Critical stat check — guard so it fires only once ──
            if not self._fail_handled and self.stat_system.is_critical():
                self._fail_handled = True
                self._handle_fail()

        elif self.phase == PHASE_QUIZ:
            if self.quiz and self.quiz.update(dt):
                self.phase = PHASE_OUTCOME
                self.outcome_timer.start()
                self.fade.fade_out()

        elif self.phase == PHASE_OUTCOME:
            if self.outcome_timer.update(dt):
                self.phase = PHASE_DONE

    # ── Events ────────────────────────────────────────────────────────────────

    def handle_event(self, event):
        if self.phase == PHASE_INTRO:
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.intro_timer.elapsed = self.intro_timer.duration
                self.phase = PHASE_DIALOGUE

        elif self.phase == PHASE_DIALOGUE:
            self.dialogue_mgr.set_choice_rects(self.choice_rects)
            result = self.dialogue_mgr.handle_event(event)
            if result:
                self._process_choice_result(result)

        elif self.phase == PHASE_QUIZ:
            if self.quiz:
                quiz_result = self.quiz.handle_event(event)
                if quiz_result == "correct":
                    self.shop.earn_coins(QUIZ_CORRECT_BONUS)
                    self.game.weakness_active = False
                elif quiz_result == "wrong":
                    self.shop.coins = max(0, self.shop.coins - QUIZ_WRONG_PENALTY)
                    self.game.weakness_active = True

    def _process_choice_result(self, result):
        # Weakness: double every negative stat delta (extra hit on bad choices)
        if self.weakness_active:
            raw = result.get("stat_changes", {})
            if sum(raw.values()) < 0:
                for stat, delta in raw.items():
                    if delta < 0:
                        self.patient.update_stat(stat, delta)  # second hit

        # Slow drain: halve negative deltas for logging (stats already applied)
        if self.slow_drain:
            result["stat_changes"] = {
                s: d // 2 if d < 0 else d
                for s, d in result.get("stat_changes", {}).items()
            }

        self.patient_jump.trigger()
        self.player_jump.trigger()
        self.player_emotion = result.get("player_emotion", "idle")

        if result.get("warning"):
            if self.ignore_next_warning:
                self.ignore_next_warning = False
                self.shop.consume_effect("ignore_warning")
            else:
                self.warn_flash.trigger()
                self.game.play_sound("warning")
                self.warning_label_timer = 2.5
                # Guide appears for first 3 warnings only
                self.guide_bubble.trigger()

        self.logger.log_turn(
            patient        = self.patient,
            choice_result  = result,
            emotional_state= self.patient.emotion,
        )

        if self.dialogue_mgr.is_done():
            self._handle_success()

    def _handle_success(self):
        if self._fail_handled:
            return   # safety guard
        self.outcome = "success"
        warnings = self.stat_system.get_warning_count()
        score = DataLogger.calculate_score(
            hearts_lost=5 - self.game.hearts,
            warning_count=warnings, success=True)
        self.logger.log_session_end("success", score)
        self.logger.new_session()
        self.shop.earn_coins(15)
        self.shop.reset_session_effects()
        self._start_quiz()

    def _handle_fail(self):
        """
        Called exactly once per session (guarded by _fail_handled flag).
        Weakness causes ×2 heart loss — this is a flat multiplier per fail event,
        NOT cumulative. After the fail the weakness flag remains until the
        player answers the quiz correctly or buys a Cleanser.
        """
        consequence = self.patient.on_stat_fail()
        self.patient.set_emotion("idle")
        warnings = self.stat_system.get_warning_count()
        score = DataLogger.calculate_score(
            hearts_lost=5 - self.game.hearts,
            warning_count=warnings, success=False)

        # ×2 hearts lost if weakness is active, else ×1
        hearts_to_lose = 2 if self.weakness_active else 1

        if consequence == "game_over":
            self.outcome = "game_over"
            self.logger.log_session_end("game_over", score)
            self.logger.new_session()
            self.game.lose_heart(hearts_to_lose)
            # Only call change_state if still alive
            if self.game.hearts > 0:
                self.game.change_state("game_over")
        else:
            self.outcome = "walked_away"
            self.logger.log_session_end("walked_away", score)
            self.logger.new_session()
            self.game.lose_heart(hearts_to_lose)
            self.shop.reset_session_effects()
            # Only show quiz if game is still running
            if self.game.hearts > 0:
                self._start_quiz()
            # If hearts hit 0 the game_over state was set inside lose_heart

        print(f"[Session] Fail ({consequence}) hearts_lost={hearts_to_lose} "
              f"remaining={self.game.hearts}")

    def _start_quiz(self):
        self.quiz  = IllnessQuiz(self.screen, self.fonts, self.patient.illness)
        self.phase = PHASE_QUIZ

    # ── Draw ──────────────────────────────────────────────────────────────────

    def draw(self):
        self.screen.blit(self.bg, (0, 0))

        if self.phase == PHASE_INTRO:
            self._draw_intro()
        elif self.phase == PHASE_DIALOGUE:
            self._draw_dialogue()
            # Guide drawn last = top z-order
            self.guide_bubble.draw(self.screen, self.fonts)
        elif self.phase == PHASE_QUIZ:
            self._draw_dialogue()
            if self.quiz:
                self.quiz.draw()
            # Guide still on top even during quiz
            self.guide_bubble.draw(self.screen, self.fonts)
        elif self.phase == PHASE_OUTCOME:
            self._draw_dialogue()
            self._draw_outcome()

        self.warn_flash.draw(self.screen)
        self.fade.draw(self.screen)

    # ── Draw: Intro ───────────────────────────────────────────────────────────

    def _draw_intro(self):
        draw_dim_overlay(self.screen, alpha=120)
        char_color = self._get_char_color()
        illness_display = (self.patient.illness.replace("_", " ").title()
                           if self.illness_revealed else "???")
        draw_patient_info(
            self.screen,
            name=self.patient.name, age=self.patient.age,
            occupation=self.patient.occupation,
            background=self.patient.background,
            rect=pygame.Rect(INFO_X, INFO_Y, INFO_W, INFO_H),
            font_name=self.fonts["medium"],
            font_body=self.fonts["small"],
            char_color=char_color,
        )
        ill = self.fonts["small"].render(
            f"Illness: {illness_display}", True, char_color)
        self.screen.blit(ill, (INFO_X + 16, INFO_Y + INFO_H - 30))
        hint = self.fonts["small"].render("Click to continue", True, MID_GRAY)
        self.screen.blit(hint, (SCREEN_W // 2 - hint.get_width() // 2,
                                 SCREEN_H - 40))

    # ── Draw: Dialogue ────────────────────────────────────────────────────────

    def _draw_dialogue(self):
        char_color = self._get_char_color()

        # Sprites
        self.screen.blit(self._get_patient_sprite(),
                         (PATIENT_X - PATIENT_SPRITE_W // 2,
                          PATIENT_Y - self.patient_jump.offset_y))
        self.screen.blit(self._get_player_sprite(),
                         (PLAYER_X, PLAYER_Y - self.player_jump.offset_y))

        # ── Stats panel ───────────────────────────────────────────────────────
        stat_bar_w = 150
        bar_h, gap = 12, 38
        num_stats  = len(self.stat_system.patient.stats)
        px, py     = STAT_X - 14, STAT_Y - 14
        pw         = stat_bar_w + 70
        title_h    = 30
        coin_h     = 24
        ph         = title_h + coin_h + num_stats * gap + 24
        prect      = pygame.Rect(px, py, pw, ph)

        pygame.draw.rect(self.screen, DARK_GRAY,  prect, border_radius=8)
        pygame.draw.rect(self.screen, LIGHT_GRAY, prect, 2, border_radius=8)

        ts = self.fonts["medium"].render("Stats", True, WHITE)
        self.screen.blit(ts, (px + (pw - ts.get_width()) // 2, py + 6))
        pygame.draw.line(self.screen, MID_GRAY,
                         (px + 8, py + title_h - 2),
                         (px + pw - 8, py + title_h - 2), 1)

        cs = self.fonts["small"].render(f"◆ {self.shop.coins} coins", True, GOLD)
        self.screen.blit(cs, (px + (pw - cs.get_width()) // 2,
                               py + title_h + 2))

        draw_stats_panel(self.screen, self.stat_system,
                         x=STAT_X, y=py + title_h + coin_h + 4,
                         font=self.fonts["small"],
                         bar_w=stat_bar_w, bar_h=bar_h, gap=gap)

        # Weakness badge under stat panel
        if self.weakness_active:
            wb = self.fonts["small"].render("⚠ WEAKNESS", True, WARN_RED)
            self.screen.blit(wb, (px + (pw - wb.get_width()) // 2, py + ph + 6))

        # Turn-boost badges
        foc = self.dialogue_mgr.focus_turns_left
        emp = self.dialogue_mgr.empathy_turns_left
        badge_y = py + ph + (26 if self.weakness_active else 6)
        if foc > 0:
            bs = self.fonts["small"].render(f"Focus {foc}t", True, GOLD)
            self.screen.blit(bs, (px + (pw - bs.get_width()) // 2, badge_y))
            badge_y += 18
        if emp > 0:
            bs = self.fonts["small"].render(f"Empathy {emp}t", True, GOLD)
            self.screen.blit(bs, (px + (pw - bs.get_width()) // 2, badge_y))

        # ── Dialogue box or choices (WHITE background, BLACK text) ────────────
        if not self.dialogue_mgr.is_waiting():
            self._draw_dialogue_box(char_color)
        else:
            self._draw_choices()

        if self.warning_label_timer > 0:
            self._draw_warning_label()

        # ── Turn counter ──────────────────────────────────────────────────────
        ts2 = self.fonts["medium"].render(
            f"Turn  {self.patient.turn} / 40", True, WHITE)
        tpx, tpy = 14, 8
        tbw = ts2.get_width()  + tpx * 2
        tbh = ts2.get_height() + tpy * 2
        tbx, tby = DIALOGUE_X, 32
        tb = pygame.Rect(tbx, tby, tbw, tbh)
        pygame.draw.rect(self.screen, DARK_GRAY,  tb, border_radius=8)
        pygame.draw.rect(self.screen, LIGHT_GRAY, tb, 2, border_radius=8)
        self.screen.blit(ts2, (tbx + tpx, tby + tpy))

    def _draw_dialogue_box(self, char_color):
        """Patient speech box — white background, black text."""
        box_rect = pygame.Rect(DIALOGUE_X, DIALOGUE_Y, DIALOGUE_W, DIALOGUE_H)

        # White background, black border
        pygame.draw.rect(self.screen, WHITE, box_rect, border_radius=8)
        pygame.draw.rect(self.screen, BLACK, box_rect, 2, border_radius=8)

        # Speaker name in char_color
        name_surf = self.fonts["medium"].render(self.patient.name, True, char_color)
        self.screen.blit(name_surf, (box_rect.x + 16, box_rect.y + 10))

        # Thin divider
        pygame.draw.line(self.screen, LIGHT_GRAY,
                         (box_rect.x + 12, box_rect.y + 38),
                         (box_rect.right - 12, box_rect.y + 38), 1)

        # Dialogue text — BLACK
        text = self.dialogue_mgr.get_revealed_text()
        words, line = text.split(), ""
        lines_out   = []
        max_w       = DIALOGUE_W - 36
        for word in words:
            test = line + (" " if line else "") + word
            if self.fonts["small"].size(test)[0] <= max_w:
                line = test
            else:
                lines_out.append(line)
                line = word
        if line:
            lines_out.append(line)

        lh = self.fonts["small"].get_linesize() + 3
        ty = box_rect.y + 46
        for l in lines_out:
            self.screen.blit(self.fonts["small"].render(l, True, BLACK),
                             (box_rect.x + 16, ty))
            ty += lh

        # Click hint
        if not self.dialogue_mgr.text_complete:
            hint = self.fonts["small"].render("Click to skip ▶", True, MID_GRAY)
        elif self.dialogue_mgr.is_reading_text():
            hint = self.fonts["small"].render("Click to continue ▶", True, MID_GRAY)
        else:
            return
        self.screen.blit(hint, (box_rect.right - hint.get_width() - 12,
                                 box_rect.bottom - hint.get_height() - 8))

    def _draw_choices(self):
        """Choice buttons — white background, black text, dark hover."""
        texts = self.dialogue_mgr.get_choice_texts()
        if not texts:
            return

        self.choice_rects = make_choice_rects(
            len(texts), CHOICE_X, CHOICE_Y, CHOICE_W, CHOICE_H, CHOICE_GAP)

        mouse_pos = pygame.mouse.get_pos()
        for text, rect in zip(texts, self.choice_rects):
            hover = rect.collidepoint(mouse_pos)
            bg    = (220, 220, 220) if hover else WHITE
            fg    = BLACK

            pygame.draw.rect(self.screen, bg,    rect, border_radius=7)
            pygame.draw.rect(self.screen, BLACK, rect, 2, border_radius=7)

            # Word-wrap
            lines, line = [], ""
            for word in text.split():
                test = line + (" " if line else "") + word
                if self.fonts["small"].size(test)[0] <= CHOICE_W - 24:
                    line = test
                else:
                    lines.append(line); line = word
            if line:
                lines.append(line)

            lh      = self.fonts["small"].get_linesize() + 2
            start_y = rect.centery - len(lines) * lh // 2
            for j, l in enumerate(lines):
                t = self.fonts["small"].render(l, True, fg)
                self.screen.blit(t, (rect.x + 12, start_y + j * lh))

    def _draw_warning_label(self):
        alpha  = int(255 * clamp(self.warning_label_timer / 2.5, 0, 1))
        warned = [k for k, v in self.stat_system.warning_flags.items() if v]
        if not warned:
            return
        surf = self.fonts["small"].render(
            f"Warning: {', '.join(warned)}", True, WARN_RED)
        surf.set_alpha(alpha)
        self.screen.blit(surf, (DIALOGUE_X, DIALOGUE_Y - 36))

    def _draw_outcome(self):
        draw_dim_overlay(self.screen, alpha=160)
        if self.outcome == "success":
            msg, sub, color = ("Session Complete",
                               f"{self.patient.name} is doing better.", WHITE)
        elif self.outcome == "walked_away":
            msg, sub, color = ("Patient Left",
                               f"{self.patient.name} wasn't ready.", (220, 160, 80))
        else:
            msg, sub, color = "Session Failed", "", (220, 80, 80)
        draw_centered_message(self.screen, msg,
                              font=self.fonts["large"], color=color,
                              sub_message=sub, sub_font=self.fonts["medium"])

    def _get_char_color(self):
        from game import CHAR_COLORS
        return CHAR_COLORS.get(self.patient.sprite_color, WHITE)

    def is_done(self):
        return self.phase == PHASE_DONE