import random
import json

STAT_MAX     = 100
STAT_MIN     = 0
WARN_LOW     = 20
WARN_HIGH    = 90
STAT_START   = 50
STAT_SCALE   = 5    # JSON deltas are small (±2–3); multiplied so in-game impact is meaningful

class Patient:
    illness      = "unknown"
    unique_stat  = "unique"
    sprite_color = "blue"

    def __init__(self, name, age, occupation, background):
        self.name       = name
        self.age        = age
        self.occupation = occupation
        self.background = background

        self.stats = {
            "Hope":       STAT_START,
            "Calm":       STAT_START,
            "Trust":      STAT_START,
            "Motivation": STAT_START,
            "Exhaustion": STAT_START,
            "Loneliness": STAT_START,
        }
        # Added separately so each subclass defines its own unique stat key
        self.stats[self.unique_stat.capitalize()] = STAT_START

        self.emotion = "idle"
        self.active  = True
        self.turn    = 0

        self.dialogue_pool = []
        self.used_ids      = set()

        self._load_dialogue()

    def _load_dialogue(self):
        path = f"Soft Hours/data/dialogue/{self.illness}.json"
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.dialogue_pool = data.get("dialogues", [])
        except FileNotFoundError:
            print(f"[Patient] Dialogue file not found: {path}")
            self.dialogue_pool = []

    def get_next_dialogue(self):
        available = [d for d in self.dialogue_pool if d["id"] not in self.used_ids]
        if not available:
            self.used_ids.clear()
            available = self.dialogue_pool
        if not available:
            return None
        chosen = random.choice(available)
        self.used_ids.add(chosen["id"])
        return chosen

    def update_stat(self, stat_name, delta):
        key = self._resolve_stat_key(stat_name)
        if key is None:
            print(f"[Patient] Unknown stat: {stat_name}")
            return
        self.stats[key] = max(STAT_MIN, min(STAT_MAX, self.stats[key] + delta))

    def apply_choice(self, choice_dict):
        for stat_name, delta in choice_dict.get("stats", {}).items():
            self.update_stat(stat_name, delta * STAT_SCALE)
        self.set_emotion(choice_dict.get("patient_emotion_after", "idle"))
        self.turn += 1

    def _resolve_stat_key(self, name):
        name_lower = name.lower()
        for key in self.stats:
            if key.lower() == name_lower:
                return key
        return None

    def check_stat_range(self):
        warnings = []
        pressure_stats = {"exhaustion", "loneliness"}
        for key, value in self.stats.items():
            if key.lower() in pressure_stats:
                if value >= WARN_HIGH:
                    warnings.append(key)
            else:
                if value <= WARN_LOW:
                    warnings.append(key)
        return warnings

    def is_critical(self):
        pressure_stats = {"exhaustion", "loneliness"}
        for key, value in self.stats.items():
            if key.lower() in pressure_stats:
                if value >= STAT_MAX:
                    return True
            else:
                if value <= STAT_MIN:
                    return True
        return False

    def set_emotion(self, emotion):
        valid = {"angry", "concern", "cry", "idle", "shock", "smile"}
        self.emotion = emotion if emotion in valid else "idle"

    def get_sprite_name(self):
        return f"{self.sprite_color}_{self.emotion}"

    def on_stat_fail(self):
        return "walk_away"

    def get_summary(self):
        return {
            "name":       self.name,
            "age":        self.age,
            "occupation": self.occupation,
            "illness":    self.illness,
            "turns":      self.turn,
            "stats":      dict(self.stats),
        }

    def __repr__(self):
        return (f"<{self.__class__.__name__} "
                f"name={self.name!r} illness={self.illness!r} "
                f"turn={self.turn}>")


class OverthinkingPatient(Patient):
    illness      = "overthinking"
    unique_stat  = "clarity"
    sprite_color = "purple"

    def on_stat_fail(self):
        return "walk_away"

class AngerPatient(Patient):
    illness      = "anger"
    unique_stat  = "control"
    sprite_color = "red"

    def on_stat_fail(self):
        return "game_over"  # only illness that triggers instant game over

class DepressionPatient(Patient):
    illness      = "depression"
    unique_stat  = "presence"
    sprite_color = "blue"

    def on_stat_fail(self):
        return "walk_away"

class TraumaPatient(Patient):
    illness      = "trauma"
    unique_stat  = "stability"
    sprite_color = "green"

    def on_stat_fail(self):
        return "walk_away"

class BurnoutPatient(Patient):
    illness      = "burnout"
    unique_stat  = "energy"
    sprite_color = "orange"

    def on_stat_fail(self):
        return "walk_away"


PATIENT_CLASSES = [
    OverthinkingPatient,
    AngerPatient,
    DepressionPatient,
    TraumaPatient,
    BurnoutPatient,
]

def load_random_info():
    try:
        with open("Soft Hours/data/patients/random_info.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("[PatientFactory] random_info.json not found.")
        return None

def create_random_patient(info_pool=None):
    if info_pool is None:
        info_pool = load_random_info()

    if info_pool is None:
        cls = random.choice(PATIENT_CLASSES)
        return cls(name="Unknown", age=25,
                   occupation="Unknown", background="No background available.")

    origin     = random.choice(["thai", "japanese", "english"])
    first      = random.choice(info_pool["first_names"][origin])
    last       = random.choice(info_pool["last_names"][origin])
    name       = f"{first} {last}"
    age        = random.randint(info_pool["age_range"]["min"], info_pool["age_range"]["max"])
    occupation = random.choice(info_pool["occupations"])
    bg_key     = "college_student" if occupation == "College Student" else "office_worker"
    background = random.choice(info_pool["backgrounds"][bg_key])
    cls        = random.choice(PATIENT_CLASSES)

    return cls(name=name, age=age, occupation=occupation, background=background)
