# Soft Hours

A story-driven visual novel where you work as a therapist seeing an endless stream of patients. Through dialogue choices and careful stat management you guide each patient through their session — keeping their emotional wellbeing in a healthy range before the next one arrives.

> *Showing up for someone, even imperfectly, matters.*

---

## Table of Contents

- [Overview](#overview)
- [Requirements](#requirements)
- [Installation](#installation)
- [How to Run](#how-to-run)
- [How to Play](#how-to-play)
  - [Stats](#stats)
  - [Dialogue & Choices](#dialogue--choices)
  - [Illness Quiz](#illness-quiz)
  - [Weakness Debuff](#weakness-debuff)
  - [Hearts & Game Over](#hearts--game-over)
  - [Shop](#shop)
  - [Guide](#guide)
- [Project Structure](#project-structure)
- [Architecture](#architecture)
  - [Classes](#classes)
  - [Data Flow](#data-flow)
- [Data Collection](#data-collection)
  - [CSV Schema](#csv-schema)
  - [Statistics Dashboard](#statistics-dashboard)
- [Changelog](#changelog)

---

## Overview

Soft Hours is a turn-based visual novel built with **Python 3** and **Pygame**. Each run presents an endless loop of randomised patients, each tied to one of five mental health conditions. The player picks dialogue responses that affect the patient's emotional stats. Mismanage the stats and the patient walks out — or worse. Between sessions the player earns coins and buys items from the shop. Every interaction is logged to a CSV file and displayed in a built-in statistics dashboard.

**Inspired by:** NEEDY STREAMER OVERLOAD, Volcano Princess, That's Not My Neighbor.

---

## Requirements

| Dependency | Version | Purpose |
|---|---|---|
| Python | 3.10 + | Runtime |
| pygame | 2.x | Game engine |
| pandas | any | CSV analysis in dashboard |
| matplotlib | any | Charts in dashboard |

Install dependencies:

```bash
pip install pygame pandas matplotlib
```

---

## Installation

1. Clone or download the repository.
2. Place all project files under a folder named `Soft Hours/`.
3. Make sure the following asset folders exist inside `Soft Hours/`:

```
Soft Hours/
├── assets/
│   ├── audio/
│   │   ├── bgm/
│   │   └── sfx/
│   ├── fonts/
│   └── images/
│       ├── bg/
│       ├── sprites/
│       │   ├── blue/
│       │   ├── green/
│       │   ├── orange/
│       │   ├── purple/
│       │   ├── red/
│       │   ├── player/
│       │   └── guide/
│       └── ui/
├── data/
│   └── saves/           ← auto-created on first run
├── stats_panel/
│   └── dashboard.py
├── main.py
├── game.py
├── session.py
└── ...
```

---

## How to Run

```bash
cd "Soft Hours"
python main.py
```

The game saves data to `Soft Hours/data/saves/`:
- `session_log.csv` — all turn-by-turn data
- `settings.json` — volume preferences

---

## How to Play

### Tutorial

Click **Begin** on the main menu. A 5-page tutorial overlay appears before your first session explaining the core systems. Use **Next ▶** to advance or **Skip** to go straight to the game. The guide character appears in each panel and changes expression based on the topic.

---

### Stats

Every patient has **6 emotional stats**, all starting at 50 out of 100:

| Stat | Type | Goal |
|---|---|---|
| Hope | Positive | Keep high |
| Calm | Positive | Keep high |
| Trust | Positive | Keep high |
| Motivation | Positive | Keep high |
| Exhaustion | Pressure | Keep low |
| Loneliness | Pressure | Keep low |

Each patient also has one **unique stat** tied to their illness:

| Patient | Illness | Unique Stat |
|---|---|---|
| Purple | Overthinking | Clarity |
| Red | Anger Issues | Control |
| Blue | Depression | Presence |
| Green | Trauma | Stability |
| Orange | Burnout | Energy |

**Warning zone:** positive stats below 20, pressure stats above 80.  
**Critical zone:** positive stats hit 0, pressure stats hit 100 → session fails.

---

### Dialogue & Choices

Each turn the patient speaks and you choose from 3–4 response options. Choices are **shuffled every turn** so no position is always safe or always harmful.

**Click flow:**
1. Patient text types out → click anywhere to skip to full reveal
2. Full text shown → click anywhere to show your choices
3. Click a choice button to respond

Each choice carries hidden stat modifiers. The `STAT_SCALE` multiplier (×5) is applied to all changes, so a small JSON delta of `−3` becomes `−15` in-game.

---

### Illness Quiz

At the end of every session — whether it succeeded or the patient walked away — you are shown all five illness names and must identify which one the patient had.

| Result | Effect |
|---|---|
| **Correct** | +20 coins, Weakness cleared |
| **Wrong** | −10 coins, −1 heart (−2 if Weakness active), Weakness debuff applied |

---

### Weakness Debuff

Weakness is a persistent debuff applied when you answer the illness quiz wrong. While active:

- All bad dialogue choices deal **double stat damage** (a second equal stat hit is applied immediately after the first)
- Wrong quiz answers cost **2 hearts** instead of 1
- A **⚠ WEAKNESS ACTIVE** badge appears at the top of the screen

Weakness is cleared by:
- Answering the illness quiz correctly
- Buying a **Cleanser** from the shop

---

### Hearts & Game Over

You start with **5 hearts**. Hearts are lost when:

- A patient **walks away** (stats reach critical) → −1 heart (−2 with Weakness)
- An **Anger patient** becomes volatile → −1 heart (−2 with Weakness) + immediate game over
- **Wrong illness quiz answer** → −1 heart (−2 if Weakness already active)

Full hearts are shown as dark red. Lost hearts appear grey. Reach 0 hearts and the run ends.

A **◀ Menu** button appears in the top-left during sessions to return to the main menu at any time.

---

### Shop

Coins are earned after each session (+15 on success). Open the shop with the bag icon during a session.

| Item | Cost | Effect |
|---|---|---|
| Case File | 18c | Reveals patient illness before the session — helps the quiz |
| Coffee | 10c | Reduces patient Exhaustion by 20 at session start |
| Stress Ball | 14c | The next warning this session is ignored |
| Calming Tea | 22c | Session boost: all negative stat changes halved |
| Focus Notes | 20c | Turn boost: +2 bonus to positive stats for 15 turns |
| Empathy Boost | 28c | Turn boost: positive stat gains doubled for 10 turns |
| Cleanser | 30c | Removes Weakness debuff + restores 5 Calm |
| Extra Heart | 40c | Restores 1 lost heart immediately |

---

### Guide

A guide character appears at the bottom-right corner of the screen during dialogue sessions, but **only for the first 3 warnings per patient**. Each appearance shows a speech bubble:

1. *"Careful! A stat just hit the danger zone."*
2. *"Another warning! Watch those stats closely."*
3. *"Third warning — this patient is on the edge!"*

After 3 appearances the guide stays hidden for the rest of that session. She is always drawn on top of all other elements.

---

## Project Structure

```
Soft Hours/
├── main.py          Entry point. Pygame init and main loop.
├── game.py          Game master controller. State machine, UI, hearts, shop icon.
├── session.py       One patient session. Dialogue, quiz, guide bubble, outcome.
├── dialogue.py      Typewriter reveal, choice shuffling, 3-stage click flow.
├── patient.py       Patient base class and five subclasses. Stat logic.
├── stats.py         StatSystem. Warning detection, critical check, draw helper.
├── shop.py          Shop inventory, purchase logic, turn-effect tracking, ShopUI.
├── data_logger.py   Logs every turn to CSV. Header repair on startup.
├── dashboard.py     (in stats_panel/) Tkinter dashboard. 7 tabs of charts + data log.
├── ui.py            Shared draw helpers (dialogue box, buttons, overlays).
├── utils.py         Sprite cache, get_sprite, FadeTransition, Timer, PulseEffect.
├── *.json           Dialogue pools for each illness type.
└── random_info.json Patient name, age, occupation pool.
```

---

## Architecture

### Classes

| Class | File | Role |
|---|---|---|
| `Game` | `game.py` | Master controller. Manages main loop, state transitions, hearts, settings. |
| `TutorialOverlay` | `game.py` | 5-page tutorial overlay shown before first session. |
| `SettingsPanel` | `game.py` | Volume sliders. Saves to `settings.json` on close. |
| `Session` | `session.py` | One full patient visit. Owns dialogue, quiz, guide bubble, outcome logic. |
| `IllnessQuiz` | `session.py` | Post-session quiz. 5 shuffled options. Applies heart/coin/weakness effects. |
| `GuideBubble` | `session.py` | Guide sprite + speech bubble. Appears on warnings 1–3, top z-order. |
| `Patient` | `patient.py` | Abstract base. Stats dict, dialogue loading, `apply_choice`, `on_stat_fail`. |
| `OverthinkingPatient` | `patient.py` | Walks away on fail. Unique stat: Clarity. |
| `AngerPatient` | `patient.py` | Instant game over on fail. Unique stat: Control. |
| `DepressionPatient` | `patient.py` | Walks away on fail. Unique stat: Presence. |
| `TraumaPatient` | `patient.py` | Walks away on fail. Unique stat: Stability. |
| `BurnoutPatient` | `patient.py` | Walks away on fail. Unique stat: Energy. |
| `StatSystem` | `stats.py` | Reads and monitors all stats. Triggers warnings. Drives `draw_stats_panel`. |
| `DialogueManager` | `dialogue.py` | Typewriter reveal, choice shuffle, 3-stage click flow, turn timing. |
| `Shop` | `shop.py` | Inventory, purchase logic, session/turn effect tracking. |
| `ShopUI` | `shop.py` | Sliding panel shop interface. |
| `DataLogger` | `data_logger.py` | Appends one row per turn to CSV. Repairs missing header on startup. |
| `Dashboard` | `dashboard.py` | Tkinter window with 7 data tabs. Launched in separate process. |

### Data Flow

```
Player click
    → DialogueManager.handle_event()
    → patient.apply_choice()  [stat delta × STAT_SCALE applied]
    → StatSystem.check_range()  [warnings detected]
    → Session._process_choice_result()  [weakness second-hit if active]
    → DataLogger.log_turn()  [row written to buffer]
    → [if session ends] DataLogger.log_session_end()  [buffer flushed to CSV]
    → IllnessQuiz  [correct/wrong → coins, hearts, weakness]
```

---

## Data Collection

All data is written to `Soft Hours/data/saves/session_log.csv` in append mode. Each turn produces one row. Session outcome and score are written as `PENDING` each turn and back-filled when the session closes.

### CSV Schema

| Column | Type | Description |
|---|---|---|
| `session_id` | string | 8-character UUID prefix per game run |
| `turn_number` | int | Turn within the session (1–40) |
| `patient_name` | string | Randomised patient name |
| `patient_illness` | string | overthinking / anger / depression / trauma / burnout |
| `patient_occupation` | string | Randomised occupation |
| `emotional_state` | string | Patient emotion at time of choice |
| `choice_made` | string | Full text of the chosen response |
| `stat_hope` | int | Hope value after choice (0–100) |
| `stat_calm` | int | Calm value after choice |
| `stat_trust` | int | Trust value after choice |
| `stat_motivation` | int | Motivation value after choice |
| `stat_exhaustion` | int | Exhaustion value after choice |
| `stat_loneliness` | int | Loneliness value after choice |
| `stat_unique` | int | Illness-specific stat value |
| `stat_unique_name` | string | Name of the unique stat |
| `warning_triggered` | 0 / 1 | Whether any stat entered warning range this turn |
| `time_per_turn` | float | Seconds taken to make this choice |
| `session_outcome` | string | success / walked_away / game_over (PENDING until session ends) |
| `session_score` | int | +10 success, −5 per heart lost, −2 per warning (PENDING until session ends) |

With 40 turns per session and multiple sessions per run, 100+ rows accumulate quickly.

### Statistics Dashboard

Open via **Settings → Stats** in-game. The dashboard runs in a separate process to avoid Tkinter threading conflicts on Windows.

| Tab | Chart Type | Description |
|---|---|---|
| Summary | Text | Session counts, totals, averages |
| Stat Trends | Line chart | All stat values averaged over turn number |
| Warnings | Bar chart | How many times each stat entered the warning zone |
| Decision Time | Boxplot | Time per turn distribution split by illness type |
| Outcomes | Grouped bar | Session outcomes (success / walked away / game over) per illness |
| Score Trend | Line chart | Session score across all runs — tracks player improvement |
| Data Log | Table | Raw CSV rows, newest first. Amber highlight for warning turns. Row count toward 100. |

---

## Changelog

### Post-Build Updates

All changes made after initial project construction.

---

#### Bug Fixes

**Hearts**
- Extra Heart shop item was deducting a heart instead of restoring one. Fixed cap from hardcoded `3` to `MAX_HEARTS`.
- `_handle_fail()` was firing every frame once stats went critical (since `is_critical()` stays `True`). Added `_fail_handled` flag so it fires only once per session.
- Lost hearts were invisible — drawn as white circles on a white box. Changed to grey `(180, 180, 180)`.
- Clicking during the illness quiz while in game-over state was triggering `_full_reset()`. Guarded with `if self.state == STATE_GAME_OVER`.

**Dialogue**
- Choice positions were fixed from the JSON, making "always pick choice 3" a reliable exploit. `random.shuffle()` is now called on choices at every dialogue load.
- Patient text auto-advanced to choices without waiting. Added `waiting_click` intermediate state: text complete → click to reveal choices → click a choice.

**Stats**
- Raw JSON deltas (`+2`, `−3`) were applied directly, making choices feel weak. `STAT_SCALE = 5` multiplier added in `patient.py` so all deltas are scaled before applying.
- Weakness second-hit used the raw unscaled delta instead of the scaled one. Fixed to apply `delta × STAT_SCALE` for the second hit.

**Data / Dashboard**
- `session_log.csv` was saved relative to the working directory instead of the project folder. All paths now use `os.path.abspath(__file__)`.
- Old CSV files had no header row, causing pandas to read the first data row as column names. `data_logger.py` now detects and prepends the correct header on startup. `dashboard.py` falls back to `header=None, names=expected_cols` if the header is still missing.
- All tabs were blank when matplotlib was not installed because `_build_ui` returned early. Each tab now handles its own missing-data state individually.
- `ax.legend()` called even when no lines were plotted, producing `UserWarning`. Fixed to only call `legend()` when at least one artist was drawn.
- `RuntimeError: main thread is not in main loop` on Python 3.10+/Windows when Tkinter's `Variable.__del__` fired from the GC thread. Fixed by launching the dashboard in a separate process via `multiprocessing.get_context("spawn")`.

---

#### New Features

**Illness Quiz**
After every session the player must identify the patient's illness from five options.
- Correct → +20 coins, Weakness cleared
- Wrong → −10 coins, −1 heart (−2 if Weakness active), Weakness applied

**Weakness Debuff**
Applied on wrong quiz answer. While active: bad choices deal double stat damage, wrong quiz costs 2 hearts. Cleared by correct quiz answer or Cleanser item. Shown as red badge at top of screen.

**Tutorial**
5-page overlay shown on first click of Begin. Guide sprite changes expression per page. Skip button available throughout. Pages cover: therapist role, stats and warnings, Weakness debuff, shop and hearts, illness quiz.

**Guide Sprite (In-Session)**
Appears at bottom-right corner for the first 3 warnings per patient session only. Shows a speech bubble with a contextual message each time. Always drawn at top z-order. Uses `pygame.transform.smoothscale` for clean rendering.

**Return to Menu Button**
`◀ Menu` button shown in top-left during sessions. Returns to main menu immediately.

**Shop — Session and Turn Boosts**
Items redesigned around session-wide and turn-counted boosts. Added: Empathy Boost (10-turn positive gain doubler), Focus Notes (15-turn +2 bonus), Cleanser (removes Weakness + restores Calm).

**Settings Persistence**
BGM and SFX slider values saved to `Soft Hours/data/saves/settings.json` on panel close and restored on next launch.

**Dialogue Box — White Theme**
Patient speech box and choice buttons now use white background with black text for readability against dark game backgrounds.

**Stats Panel — Dark Theme**
Stats panel switched to dark background with white text, gold coin display, and cleaner spacing.

**Turn Counter**
Redesigned as a dark pill showing `Turn X / 40` in the medium game font.

**Data Log Tab**
Added to the dashboard. Shows every CSV row in a scrollable table with amber warning highlights, row count, and a progress indicator toward 100 rows.

---

#### Technical Reference

| File | Changes |
|---|---|
| `game.py` | `STATE_TUTORIAL`, `TutorialOverlay`, settings save/load (`settings.json`), guide sprites loaded at native size, return-to-menu button, weakness indicator, `lose_heart(amount)`, `_full_reset` resets weakness and shop UI |
| `session.py` | `IllnessQuiz`, `GuideBubble`, weakness double-hit with `STAT_SCALE`, `_fail_handled` flag, white dialogue/choice boxes, quiz wrong answer loses heart immediately |
| `dialogue.py` | `random.shuffle` on every load, `waiting_click` three-stage flow, unused `json` import removed |
| `patient.py` | `STAT_SCALE = 5` multiplier on all stat deltas |
| `shop.py` | Revised item list with session/turn boosts, `turn_effects` dict, Cleanser item |
| `stats.py` | Draw colours updated for dark panel visibility |
| `data_logger.py` | Path anchored to `__file__`, header detection and repair |
| `dashboard.py` | Per-tab data guards, headerless CSV detection, multiprocess launch, Data Log tab, legend guard, path fallback search, `smoothscale` for guide sprites |