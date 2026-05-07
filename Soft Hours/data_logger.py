import csv
import os
import time
import uuid

# Anchored to this file so saves always land in Soft Hours/data/saves/ regardless of CWD
_HERE    = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(_HERE, "data", "saves", "session_log.csv")

COLUMNS = [
    "session_id",
    "turn_number",
    "patient_name",
    "patient_illness",
    "patient_occupation",
    "emotional_state",
    "choice_made",
    "stat_hope",
    "stat_calm",
    "stat_trust",
    "stat_motivation",
    "stat_exhaustion",
    "stat_loneliness",
    "stat_unique",
    "stat_unique_name",
    "warning_triggered",
    "time_per_turn",
    "session_outcome",
    "session_score",
]


class DataLogger:
    def __init__(self):
        self.session_id   = str(uuid.uuid4())[:8]
        self.turn_rows    = []
        self.session_done = False
        self._ensure_file()

    def _ensure_file(self):
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        if not os.path.exists(LOG_PATH):
            with open(LOG_PATH, "w", newline="", encoding="utf-8") as f:
                csv.DictWriter(f, fieldnames=COLUMNS).writeheader()
            return

        # Prepend header if old CSV was written without one
        with open(LOG_PATH, "r", encoding="utf-8") as f:
            first = f.readline().strip()
        if first != ",".join(COLUMNS):
            with open(LOG_PATH, "r", encoding="utf-8") as f:
                existing = f.read()
            with open(LOG_PATH, "w", newline="", encoding="utf-8") as f:
                f.write(",".join(COLUMNS) + "\n")
                f.write(existing)
            print(f"[DataLogger] Prepended missing header to {LOG_PATH}")

    def log_turn(self, patient, choice_result, emotional_state):
        if self.session_done:
            return

        stats      = choice_result.get("stats_after", {})
        unique_key = patient.unique_stat.capitalize()

        row = {
            "session_id":         self.session_id,
            "turn_number":        choice_result.get("turn", 0),
            "patient_name":       patient.name,
            "patient_illness":    patient.illness,
            "patient_occupation": patient.occupation,
            "emotional_state":    emotional_state,
            "choice_made":        choice_result.get("choice_text", ""),
            "stat_hope":          stats.get("Hope",       0),
            "stat_calm":          stats.get("Calm",       0),
            "stat_trust":         stats.get("Trust",      0),
            "stat_motivation":    stats.get("Motivation", 0),
            "stat_exhaustion":    stats.get("Exhaustion", 0),
            "stat_loneliness":    stats.get("Loneliness", 0),
            "stat_unique":        stats.get(unique_key,   0),
            "stat_unique_name":   unique_key,
            "warning_triggered":  1 if choice_result.get("warning") else 0,
            "time_per_turn":      choice_result.get("time_taken", 0.0),
            "session_outcome":    "PENDING",
            "session_score":      "PENDING",
        }
        self.turn_rows.append(row)

    def log_session_end(self, outcome, score):
        for row in self.turn_rows:
            row["session_outcome"] = outcome
            row["session_score"]   = score
        self._write_rows()
        self.session_done = True
        print(f"[DataLogger] Session {self.session_id} logged "
              f"({len(self.turn_rows)} turns, outcome={outcome}, score={score})"
              f"\n  → {LOG_PATH}")

    def _write_rows(self):
        with open(LOG_PATH, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=COLUMNS)
            for row in self.turn_rows:
                writer.writerow(row)

    def new_session(self):
        self.session_id   = str(uuid.uuid4())[:8]
        self.turn_rows    = []
        self.session_done = False

    def export_csv(self, path=None):
        target = path or LOG_PATH
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=COLUMNS)
            for row in self.turn_rows:
                writer.writerow(row)

    @staticmethod
    def calculate_score(hearts_lost, warning_count, success):
        score = 10 if success else 0
        score -= hearts_lost   * 5
        score -= warning_count * 2
        return score

    def get_session_summary(self):
        if not self.turn_rows:
            return {}
        warnings = sum(r["warning_triggered"] for r in self.turn_rows)
        times    = [r["time_per_turn"] for r in self.turn_rows
                    if isinstance(r["time_per_turn"], (int, float))]
        avg_time = round(sum(times) / len(times), 2) if times else 0.0
        return {
            "session_id":        self.session_id,
            "total_turns":       len(self.turn_rows),
            "total_warnings":    warnings,
            "avg_time_per_turn": avg_time,
            "outcome":           self.turn_rows[-1].get("session_outcome", "PENDING"),
            "score":             self.turn_rows[-1].get("session_score",   "PENDING"),
        }

    def __repr__(self):
        return (f"<DataLogger session={self.session_id!r} "
                f"turns={len(self.turn_rows)} done={self.session_done}>")
