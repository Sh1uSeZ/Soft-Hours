import pygame
import random
import time

# Text reveal speed (characters per second)
REVEAL_SPEED = 40

# Maximum turns per session
MAX_TURNS = 40

class DialogueManager:
    """
    Manages the full dialogue flow for one patient session.

    Key change: choices are shuffled every time a new dialogue entry loads,
    so no positional pattern (e.g. "choice 3 is always bad") can be exploited.
    """

    def __init__(self, patient, stat_system):
        self.patient     = patient
        self.stat_system = stat_system

        self.current_entry   = None
        self.revealed_chars  = 0
        self.reveal_timer    = 0.0
        self.text_complete   = False

        self.choices         = []
        self.choice_rects    = []
        self.hovered_choice  = -1
        self.waiting_choice  = False
        self.waiting_click   = False

        self.player_emotion  = "idle"
        self.turn_start_time = None
        self.session_done    = False

        # Turn-based shop boost tracking (set externally by Session)
        self.focus_turns_left    = 0   # each good choice gives +bonus stats
        self.empathy_turns_left  = 0   # each positive delta is doubled

        self.load_next()

    def load_next(self):
        if self.patient.turn >= MAX_TURNS:
            self.session_done = True
            return

        entry = self.patient.get_next_dialogue()
        if entry is None:
            self.session_done = True
            return

        self.current_entry  = entry
        self.revealed_chars = 0
        self.reveal_timer   = 0.0
        self.text_complete  = False
        self.waiting_choice = False
        self.waiting_click  = False

        raw_choices = list(entry.get("choices", []))
        random.shuffle(raw_choices)
        self.choices = raw_choices

        self.choice_rects   = []
        self.hovered_choice = -1
        self.turn_start_time = time.time()

        opening_emotion = entry.get("emotion", "idle")
        self.patient.set_emotion(opening_emotion)

    def load_dialogue(self, entry):
        self.current_entry  = entry
        self.revealed_chars = 0
        self.reveal_timer   = 0.0
        self.text_complete  = False
        self.waiting_choice = False
        self.waiting_click  = False
        raw_choices = list(entry.get("choices", []))
        random.shuffle(raw_choices)
        self.choices        = raw_choices
        self.choice_rects   = []
        self.hovered_choice = -1
        self.turn_start_time = time.time()
        self.patient.set_emotion(entry.get("emotion", "idle"))

    def update(self, dt):
        if self.current_entry is None or self.session_done:
            return

        if not self.text_complete:
            self.reveal_timer  += dt
            total_chars         = len(self.get_patient_text())
            self.revealed_chars = min(
                int(self.reveal_timer * REVEAL_SPEED), total_chars)
            if self.revealed_chars >= total_chars:
                self.text_complete  = True
                self.waiting_click  = True
                self.waiting_choice = False

    def skip_reveal(self):
        if not self.text_complete:
            self.revealed_chars = len(self.get_patient_text())
            self.text_complete  = True
            self.waiting_click  = True
            self.waiting_choice = False

    def get_patient_text(self):
        if self.current_entry is None:
            return ""
        return self.current_entry.get("patient_says", "")

    def get_revealed_text(self):
        return self.get_patient_text()[:self.revealed_chars]

    def get_choice_texts(self):
        return [c.get("text", "") for c in self.choices]

    def set_choice_rects(self, rects):
        self.choice_rects = rects

    def handle_event(self, event):
        """
        Three-stage click flow:
          1. Text revealing  → click = skip to full reveal
          2. Text complete, waiting_click → click = show choices
          3. Choices visible → click a button = apply choice
        """
        if event.type == pygame.MOUSEMOTION:
            self.hovered_choice = -1
            for i, rect in enumerate(self.choice_rects):
                if rect.collidepoint(event.pos):
                    self.hovered_choice = i
                    break

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if not self.text_complete:
                self.skip_reveal()
                return None

            if self.waiting_click:
                self.waiting_click  = False
                self.waiting_choice = True
                return None

            if self.waiting_choice:
                for i, rect in enumerate(self.choice_rects):
                    if rect.collidepoint(event.pos):
                        return self.apply_choice(i)

        return None

    def apply_choice(self, index):
        if index < 0 or index >= len(self.choices):
            return None

        choice     = self.choices[index]
        time_taken = time.time() - (self.turn_start_time or time.time())

        # Apply base stat changes
        self.patient.apply_choice(choice)

        # Apply turn-based shop boosts
        raw_stats = choice.get("stats", {})

        if self.focus_turns_left > 0:
            self.focus_turns_left -= 1
            net = sum(raw_stats.values())
            if net > 0:
                # Give a flat +2 bonus to every positive stat this turn
                for stat, delta in raw_stats.items():
                    if delta > 0:
                        self.patient.update_stat(stat, 2)

        if self.empathy_turns_left > 0:
            self.empathy_turns_left -= 1
            for stat, delta in raw_stats.items():
                if delta > 0:
                    self.patient.update_stat(stat, delta)  # extra equal hit

        self.player_emotion = choice.get("player_emotion_after", "idle")

        warnings = self.stat_system.check_range()
        warned   = len(warnings) > 0
        if warned:
            self.stat_system.trigger_warning(self.patient.turn)

        result = {
            "turn":           self.patient.turn,
            "choice_index":   index,
            "choice_text":    choice.get("text", ""),
            "stat_changes":   raw_stats,
            "stats_after":    self.stat_system.snapshot(),
            "warning":        warned,
            "time_taken":     round(time_taken, 2),
            "player_emotion": self.player_emotion,
        }

        self.load_next()
        return result

    def pick_random(self):
        if not self.choices:
            return None
        return self.apply_choice(random.randint(0, len(self.choices) - 1))

    def is_reading_text(self):
        return self.waiting_click and self.text_complete

    def is_waiting(self):
        return self.waiting_choice and self.text_complete

    def is_done(self):
        return self.session_done

    def __repr__(self):
        entry_id = self.current_entry.get("id") if self.current_entry else None
        return (f"<DialogueManager patient={self.patient.name!r} "
                f"turn={self.patient.turn} entry={entry_id} "
                f"waiting={self.waiting_choice}>")