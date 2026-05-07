import pygame

STAT_MAX   = 100
STAT_MIN   = 0
WARN_LOW   = 20
WARN_HIGH  = 80
CRIT_LOW   = 0
CRIT_HIGH  = 100

PRESSURE_STATS = {"exhaustion", "loneliness"}  # bad when HIGH, unlike all other stats


class StatSystem:
    def __init__(self, patient):
        self.patient         = patient
        self.warning_flags   = {}   # stat_name -> bool
        self.warning_history = []
        self._init_flags()

    def _init_flags(self):
        for key in self.patient.stats:
            self.warning_flags[key] = False

    def update(self, stat_deltas: dict):
        for stat_name, delta in stat_deltas.items():
            self.patient.update_stat(stat_name, delta)
        return self.check_range()

    def check_range(self):
        warnings = []
        for key, value in self.patient.stats.items():
            is_pressure = key.lower() in PRESSURE_STATS
            in_warning  = value >= WARN_HIGH if is_pressure else value <= WARN_LOW
            self.warning_flags[key] = in_warning
            if in_warning:
                warnings.append(key)
        return warnings

    def is_critical(self):
        for key, value in self.patient.stats.items():
            is_pressure = key.lower() in PRESSURE_STATS
            if is_pressure and value >= CRIT_HIGH:
                return True
            if not is_pressure and value <= CRIT_LOW:
                return True
        return False

    def any_warning_active(self):
        return any(self.warning_flags.values())

    def trigger_warning(self, turn_number):
        active = [k for k, v in self.warning_flags.items() if v]
        for stat in active:
            self.warning_history.append({
                "turn":  turn_number,
                "stat":  stat,
                "value": self.patient.stats[stat],
            })
        return active

    def snapshot(self):
        return dict(self.patient.stats)

    def get_most_neglected(self):
        counts = {}
        for entry in self.warning_history:
            stat = entry["stat"]
            counts[stat] = counts.get(stat, 0) + 1
        if not counts:
            return None
        return max(counts, key=counts.get)

    def get_warning_count(self):
        return len(self.warning_history)

    def get_display_stats(self):
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


def draw_stats_panel(surface, stat_system, x, y, font,
                     bar_w=160, bar_h=10, gap=36):
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

        label_color = WARN_AMBER if in_warning else LIGHT_GRAY
        label_surf  = font.render(label, True, label_color)
        surface.blit(label_surf, (x, bar_y - label_surf.get_height() - 3))

        pygame.draw.rect(surface, DARK_GRAY, (x, bar_y, bar_w, bar_h), border_radius=3)

        fill_w = int((value / STAT_MAX) * bar_w)
        if in_warning:
            bar_color = WARN_RED
        elif is_pressure:
            bar_color = (160, 100, 100)
        else:
            bar_color = WHITE

        if fill_w > 0:
            pygame.draw.rect(surface, bar_color, (x, bar_y, fill_w, bar_h), border_radius=3)

        pygame.draw.rect(surface, MID_GRAY, (x, bar_y, bar_w, bar_h), 1, border_radius=3)

        val_surf = font.render(str(value), True, WHITE)
        surface.blit(val_surf,
                     (x + bar_w + 8,
                      bar_y + bar_h // 2 - val_surf.get_height() // 2))

    return len(display) * gap
