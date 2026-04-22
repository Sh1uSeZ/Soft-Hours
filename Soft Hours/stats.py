import pygame


# ─────────────────────────────────────────────────────────────────────────────
# Thresholds
# ─────────────────────────────────────────────────────────────────────────────
STAT_MAX   = 100
STAT_MIN   = 0
WARN_LOW   = 20   # positive stats warn below this
WARN_HIGH  = 80   # pressure stats warn above this
CRIT_LOW   = 0    # critical floor
CRIT_HIGH  = 100  # critical ceiling

# Stats that are bad when HIGH (pressure meters)
PRESSURE_STATS = {"exhaustion", "loneliness"}


# ─────────────────────────────────────────────────────────────────────────────
# StatSystem
# ─────────────────────────────────────────────────────────────────────────────
class StatSystem:
    """
    Manages reading, updating, and monitoring all stats for a patient.
    Works directly with a Patient instance's stats dict.
    """

    def __init__(self, patient):
        self.patient       = patient
        self.warning_flags = {}   # stat_name -> True if currently warned
        self.warning_history = [] # list of (turn, stat_name) for logging
        self._init_flags()

    def _init_flags(self):
        """Initialise all warning flags to False."""
        for key in self.patient.stats:
            self.warning_flags[key] = False

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, stat_deltas: dict):
        """
        Apply a dict of stat changes to the patient.
        stat_deltas — e.g. {"hope": 2, "exhaustion": -1}
        Also re-evaluates warning flags after applying.
        Returns list of newly triggered warning stat names.
        """
        for stat_name, delta in stat_deltas.items():
            self.patient.update_stat(stat_name, delta)

        return self.check_range()

    # ── Range checking ────────────────────────────────────────────────────────

    def check_range(self):
        """
        Evaluate all stats against warning thresholds.
        Updates self.warning_flags.
        Returns list of stat names currently in warning state.
        """
        warnings = []

        for key, value in self.patient.stats.items():
            is_pressure = key.lower() in PRESSURE_STATS

            if is_pressure:
                in_warning = value >= WARN_HIGH
            else:
                in_warning = value <= WARN_LOW

            self.warning_flags[key] = in_warning

            if in_warning:
                warnings.append(key)

        return warnings

    def is_critical(self):
        """
        Returns True if any stat has hit the absolute limit.
        Pressure stats critical at CRIT_HIGH, others at CRIT_LOW.
        """
        for key, value in self.patient.stats.items():
            is_pressure = key.lower() in PRESSURE_STATS
            if is_pressure and value >= CRIT_HIGH:
                return True
            if not is_pressure and value <= CRIT_LOW:
                return True
        return False

    def any_warning_active(self):
        """Returns True if at least one stat is currently in warning."""
        return any(self.warning_flags.values())

    # ── Warning trigger ───────────────────────────────────────────────────────

    def trigger_warning(self, turn_number):
        """
        Record which stats triggered warnings this turn for logging.
        Returns list of warned stat names.
        """
        active = [k for k, v in self.warning_flags.items() if v]
        for stat in active:
            self.warning_history.append({
                "turn":  turn_number,
                "stat":  stat,
                "value": self.patient.stats[stat],
            })
        return active

    # ── Snapshot ──────────────────────────────────────────────────────────────

    def snapshot(self):
        """
        Return a flat dict copy of current stat values.
        Used for data logging each turn.
        """
        return dict(self.patient.stats)

    def get_most_neglected(self):
        """
        Returns the stat name that has been warned the most across the session.
        Useful for post-session analysis.
        """
        counts = {}
        for entry in self.warning_history:
            stat = entry["stat"]
            counts[stat] = counts.get(stat, 0) + 1

        if not counts:
            return None
        return max(counts, key=counts.get)

    def get_warning_count(self):
        """Returns total number of warning events recorded this session."""
        return len(self.warning_history)

    # ── Display helper ────────────────────────────────────────────────────────

    def get_display_stats(self):
        """
        Returns stats formatted for UI display.
        Each entry: (label, value, is_warning, is_pressure)
        """
        result = []
        for key, value in self.patient.stats.items():
            is_pressure = key.lower() in PRESSURE_STATS
            in_warning  = self.warning_flags.get(key, False)
            result.append({
                "label":       key,
                "value":       value,
                "is_warning":  in_warning,
                "is_pressure": is_pressure,
            })
        return result

    def __repr__(self):
        return (f"<StatSystem patient={self.patient.name!r} "
                f"warnings={self.get_warning_count()}>")


# ─────────────────────────────────────────────────────────────────────────────
# draw_stats_panel  —  draws all stat bars using ui.py helpers
# ─────────────────────────────────────────────────────────────────────────────
def draw_stats_panel(surface, stat_system, x, y, font,
                     bar_w=160, bar_h=10, gap=36):
    """
    Draw all stat bars for a patient session.
    Designed for a dark panel background — labels and values use light colours.
    Bars turn red when a stat is in warning state.
    """
    WHITE      = (255, 255, 255)
    LIGHT_GRAY = (200, 200, 200)
    DARK_GRAY  = (55,  55,  55)
    MID_GRAY   = (120, 120, 120)
    WARN_RED   = (220,  60,  60)
    WARN_AMBER = (230, 160,  40)

    display = stat_system.get_display_stats()

    for i, entry in enumerate(display):
        label       = entry["label"]
        value       = entry["value"]
        in_warning  = entry["is_warning"]
        is_pressure = entry["is_pressure"]
        bar_y       = y + i * gap

        # Label — amber on warning, light gray otherwise
        label_color = WARN_AMBER if in_warning else LIGHT_GRAY
        label_surf  = font.render(label, True, label_color)
        surface.blit(label_surf, (x, bar_y - label_surf.get_height() - 3))

        # Bar track
        pygame.draw.rect(surface, DARK_GRAY,
                         (x, bar_y, bar_w, bar_h), border_radius=3)

        # Fill
        fill_w = int((value / STAT_MAX) * bar_w)
        if in_warning:
            bar_color = WARN_RED
        elif is_pressure:
            bar_color = (160, 100, 100)  # muted red for pressure stats
        else:
            bar_color = WHITE

        if fill_w > 0:
            pygame.draw.rect(surface, bar_color,
                             (x, bar_y, fill_w, bar_h), border_radius=3)

        # Border
        pygame.draw.rect(surface, MID_GRAY,
                         (x, bar_y, bar_w, bar_h), 1, border_radius=3)

        # Value — white, right of bar
        val_surf = font.render(str(value), True, WHITE)
        surface.blit(val_surf,
                     (x + bar_w + 8,
                      bar_y + bar_h // 2 - val_surf.get_height() // 2))

    return len(display) * gap