import random
import json

# Stat constants
STAT_MAX     = 100
STAT_MIN     = 0
WARN_LOW     = 20   # warning threshold (too low)
WARN_HIGH    = 90   # warning threshold (too high)
STAT_START   = 50   # default starting value for all stats
STAT_SCALE   = 5    # multiplier applied to all JSON stat deltas for bigger impact
              # e.g. JSON "+2" becomes +10 in-game; JSON "-3" becomes -15

# Base Patient class
class Patient:
    """
    Abstract base class for all patients.
    Do not instantiate directly — use a subclass.
    """

    illness      = "unknown"
    unique_stat  = "unique"
    sprite_color = "blue"    # overridden per subclass

    def __init__(self, name, age, occupation, background):
        self.name       = name
        self.age        = age
        self.occupation = occupation
        self.background = background

        # Shared stats
        self.stats = {
            "Hope":       STAT_START,
            "Calm":       STAT_START,
            "Trust":      STAT_START,
            "Motivation": STAT_START,
            "Exhaustion": STAT_START,
            "Loneliness": STAT_START,
            "Clarity":    STAT_START,
        }

        # Unique stat added by subclass
        self.stats[self.unique_stat.capitalize()] = STAT_START

        # Current emotion (maps to sprite filename suffix)
        self.emotion = "idle"

        # Whether this patient is still in session
        self.active = True

        # Turn counter
        self.turn = 0

        # Dialogue pool loaded from JSON
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
        """
        Pick a random unused dialogue entry.
        If all have been used, reset the used set and pick again.
        Returns the dialogue dict or None if pool is empty.
        """
        available = [d for d in self.dialogue_pool
                     if d["id"] not in self.used_ids]

        if not available:
            self.used_ids.clear()
            available = self.dialogue_pool

        if not available:
            return None

        chosen = random.choice(available)
        self.used_ids.add(chosen["id"])
        return chosen

    def update_stat(self, stat_name, delta):
        """
        Apply a delta to a stat, clamped between STAT_MIN and STAT_MAX.
        stat_name should match a key in self.stats (case-insensitive match).
        """
        # Case-insensitive key lookup
        key = self._resolve_stat_key(stat_name)
        if key is None:
            print(f"[Patient] Unknown stat: {stat_name}")
            return

        self.stats[key] = max(STAT_MIN,
                              min(STAT_MAX, self.stats[key] + delta))

    def apply_choice(self, choice_dict):
        """
        Apply all stat changes from a chosen dialogue option.
        Deltas from the JSON are multiplied by STAT_SCALE so even small
        JSON values (+2, -3) produce meaningful in-game impact.
        Also updates patient and player emotions.
        """
        for stat_name, delta in choice_dict.get("stats", {}).items():
            self.update_stat(stat_name, delta * STAT_SCALE)

        # Update patient emotion
        new_emotion = choice_dict.get("patient_emotion_after", "idle")
        self.set_emotion(new_emotion)

        self.turn += 1

    def _resolve_stat_key(self, name):
        name_lower = name.lower()
        for key in self.stats:
            if key.lower() == name_lower:
                return key
        return None

    def check_stat_range(self):
        """
        Check all stats for out-of-range values.
        Returns a list of stat names that are in warning territory.
        Warning if Hope, Calm, Trust, Motivation, unique_stat < WARN_LOW
        Warning if Exhaustion or Loneliness > WARN_HIGH
        """
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
        """
        Returns True if any stat has crossed the critical threshold.
        Critical means the session should end badly.
        """
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
        """
        Set current emotion for sprite display.
        Valid patient emotions: angry, concern, cry, idle, shock, smile
        """
        valid = {"angry", "concern", "cry", "idle", "shock", "smile"}
        if emotion in valid:
            self.emotion = emotion
        else:
            self.emotion = "idle"

    def get_sprite_name(self):
        return f"{self.sprite_color}_{self.emotion}"

    def on_stat_fail(self):
        """
        Called when stats reach critical level.
        Subclasses override this to define unique consequences.
        Returns a string describing the outcome type:
          "game_over"  — instant game over (aggressive patient)
          "walk_away"  — patient leaves, lose a heart
        """
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

# Subclasses

class OverthinkingPatient(Patient):
    illness      = "overthinking"
    unique_stat  = "clarity"
    sprite_color = "purple"

    def on_stat_fail(self):
        # Spirals and walks away mid session
        return "walk_away"

class AngerPatient(Patient):
    illness      = "anger"
    unique_stat  = "control"
    sprite_color = "red"

    def on_stat_fail(self):
        # Becomes aggressive — instant game over
        return "game_over"

class DepressionPatient(Patient):
    illness      = "depression"
    unique_stat  = "presence"
    sprite_color = "blue"

    def on_stat_fail(self):
        # Goes silent and walks away
        return "walk_away"

class TraumaPatient(Patient):
    illness      = "trauma"
    unique_stat  = "stability"
    sprite_color = "green"

    def on_stat_fail(self):
        # Shuts down and flees
        return "walk_away"

class BurnoutPatient(Patient):
    illness      = "burnout"
    unique_stat  = "energy"
    sprite_color = "orange"

    def on_stat_fail(self):
        # Collapses and becomes unresponsive
        return "walk_away"

# Patient factory — random patient generator

PATIENT_CLASSES = [
    OverthinkingPatient,
    AngerPatient,
    DepressionPatient,
    TraumaPatient,
    BurnoutPatient,
]

def load_random_info():
    """Load the random_info.json pool."""
    try:
        with open("Soft Hours/data/patients/random_info.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("[PatientFactory] random_info.json not found.")
        return None

def create_random_patient(info_pool=None):
    """
    Create a random patient with randomized identity.
    Picks a random illness class, random name, age, occupation, background.
    Returns a Patient subclass instance.
    """
    if info_pool is None:
        info_pool = load_random_info()

    # Fallback if pool missing
    if info_pool is None:
        cls = random.choice(PATIENT_CLASSES)
        return cls(name="Unknown", age=25,
                   occupation="Unknown", background="No background available.")

    # Random origin for name
    origin    = random.choice(["thai", "japanese", "english"])
    first     = random.choice(info_pool["first_names"][origin])
    last      = random.choice(info_pool["last_names"][origin])
    name      = f"{first} {last}"

    age       = random.randint(info_pool["age_range"]["min"],
                               info_pool["age_range"]["max"])

    occupation = random.choice(info_pool["occupations"])

    bg_key     = ("college_student"
                  if occupation == "College Student"
                  else "office_worker")
    background = random.choice(info_pool["backgrounds"][bg_key])

    # Random illness class
    cls = random.choice(PATIENT_CLASSES)

    return cls(name=name, age=age,
               occupation=occupation, background=background)