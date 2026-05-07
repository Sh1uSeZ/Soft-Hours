# Project Description

## 1. Project Overview

- **Project Name:** Soft Hours
- **Brief Description:**
  Soft Hours is a story-driven visual novel where you play a therapist seeing an endless line of patients. Each patient is randomized — different name, age, occupation, background, and one of five mental health conditions: **Overthinking, Anger Issues, Depression, Trauma, and Burnout**. You pick dialogue choices that move the patient's emotional stats up or down. Keep them steady and the session ends well; mismanage them and the patient walks away (or worse). Between sessions you earn coins and spend them in a shop on items that take some of the pressure off the next visit.

  Every turn is logged to a CSV file by the `DataLogger` class. A separate Tkinter dashboard reads that file and turns it into charts (line graphs, bar charts, boxplots), so you can actually see how your decisions trend across sessions instead of guessing.

- **Problem Statement:**
  Most stat-management visual novels follow one character through a long arc, which can feel repetitive and only explores one situation. Soft Hours breaks that into short, repeatable patient sessions and gives you five distinct mental-health archetypes to work with — each with its own unique stat, dialogue pool, and failure consequence — so the emotional struggles change every run while the gameplay loop stays familiar.

- **Target Users:**
  Players who like narrative-driven, low-pressure stat-management games; people curious about mental-health themes wrapped in a visual-novel format; students learning Pygame and OOP through a real project.

- **Key Features:**
  - 5 patient illness types, each with a unique stat and a unique failure consequence (walk away vs. instant game over)
  - Randomized patient identity (name, age, occupation, background) every session
  - Shuffled dialogue choices every turn — no exploitable positional pattern
  - 3-stage click flow (text reveal → confirm → choices) for deliberate pacing
  - End-of-session illness quiz with coin and heart consequences
  - Persistent **Weakness debuff** that doubles negative stat hits and heart loss until cleared
  - Shop with 8 items: single-use, session-wide, and turn-counted boosts
  - Built-in **Tkinter statistics dashboard** with 7 tabs (Summary, Stat Trends, Warnings, Decision Time, Outcomes, Score Trend, Data Log)
  - Volume settings that persist between runs, plus full SFX and BGM, custom font, and original sprite art

- **Screenshots:** see the [`screenshots/`](screenshots/) folder for both gameplay and dashboard screenshots.
- **Proposal:** [`SoftHours_Proposal.pdf`](SoftHours_Proposal.pdf) at the project root.
- **YouTube presentation:** https://youtu.be/BD4Hj3YkZwY — covers (1) intro and demo of the game and statistics, (2) class design and usage, (3) statistics and data visualization.

---

## 2. Concept

### 2.1 Background

- **Why this project exists:**
  The course asked for a Python project that combines a game with structured data collection and visualization. A visual novel works really well for this because every player action produces one well-defined data row — the chosen dialogue, the resulting stat snapshot, the time taken — which is exactly what a dashboard wants to chew on later.

- **What inspired the project:**
  Mechanically the project takes from **NEEDY STREAMER OVERLOAD** and **Volcano Princess** — both are stat-management visual novels where dialogue choices stack up over time. The repeatable session structure comes from **That's Not My Neighbor**, where each visitor is its own self-contained encounter. Soft Hours blends those two ideas with a grounded mental-health theme.

- **Why the topic matters:**
  Mental health is something a lot of people experience but rarely talk about openly. Wrapping it inside a low-pressure game where the player keeps *showing up* — even imperfectly — gives the topic a gentle entry point. The goal isn't clinical accuracy, it's emotional honesty.

### 2.2 Objectives

- Build a complete Pygame application using clean OOP (abstract base class, concrete subclasses, separation of concerns between Game / Session / Patient / Stats / Dialogue / Shop / Logger).
- Generate enough rich gameplay data for real statistical analysis: per-turn rows that accumulate across sessions, with stat snapshots, choice text, decision time, warnings, and outcomes.
- Provide a polished Tkinter dashboard that reads the CSV and renders 6+ visualization types (line graph, bar chart, boxplot, grouped bar chart, line trend, raw data table).
- Make the game replayable through randomization — names, ages, illness types, dialogue entries, and choice positions all change every session.

---

## 3. UML Class Diagram

The full UML class diagram is provided in [`UML.pdf`](UML.pdf) at the project root.

It includes:
- **Classes** (Game, Session, Patient and 5 subclasses, StatSystem, DialogueManager, DataLogger, Shop, ShopUI, IllnessQuiz, GuideBubble, SettingsPanel, Slider, TutorialOverlay, Dashboard)
- **Attributes** for each class
- **Methods** (the key public methods on each class)
- **Relationships** — inheritance (Patient → 5 subclasses), composition (Game owns Shop / DataLogger / Session, Session owns Patient / StatSystem / DialogueManager / IllnessQuiz / GuideBubble), association (Dashboard → DataLogger CSV)

**Submission Requirement:** UML class diagram is attached as `UML.pdf`.

---

## 4. Object-Oriented Programming Implementation

### Core game classes

- **`Game`** (`game.py`): the master controller. Owns the screen, the state machine (`main_menu`, `tutorial`, `session`, `shop`, `game_over`, `bad_ending`), the heart counter, the global Weakness flag, and all top-level subsystems (Shop, ShopUI, DataLogger, SettingsPanel, TutorialOverlay). Handles state transitions, input routing, music switching, and a full reset on game over.

- **`Session`** (`session.py`): manages one patient visit from intro to outcome. Owns a `Patient`, a `StatSystem`, a `DialogueManager`, an `IllnessQuiz`, and a `GuideBubble`. Drives the phase machine (`intro → dialogue → quiz → outcome → done`), applies shop effects (Calming Tea slow-drain, ignore-warning, reveal-illness), and routes choice results to the logger.

- **`Patient`** (`patient.py`): **abstract base class** for every patient. Holds the shared stats (Hope, Calm, Trust, Motivation, Exhaustion, Loneliness) plus a unique stat that each subclass adds. Loads and tracks dialogue entries from JSON, applies stat deltas with the `STAT_SCALE` multiplier, and manages emotion sprites and a turn counter. Subclasses override `on_stat_fail()` to define their own failure consequence.

- **`OverthinkingPatient`** — unique stat *Clarity*, sprite `purple`, fail = walk away.
- **`AngerPatient`** — unique stat *Control*, sprite `red`, fail = **instant game over**.
- **`DepressionPatient`** — unique stat *Presence*, sprite `blue`, fail = walk away.
- **`TraumaPatient`** — unique stat *Stability*, sprite `green`, fail = walk away.
- **`BurnoutPatient`** — unique stat *Energy*, sprite `orange`, fail = walk away.

### Systems

- **`StatSystem`** (`stats.py`): reads, updates, and watches every patient stat. Pushes deltas through `Patient.update_stat()`, evaluates warning thresholds (`<= 20` for positive stats, `>= 80` for pressure stats), records a per-turn warning history, and exposes `is_critical()`, `get_warning_count()`, and `get_display_stats()` for the UI and the logger.

- **`DialogueManager`** (`dialogue.py`): runs the full dialogue flow for a session. Loads the next entry, runs the typewriter text reveal, drives the 3-stage click flow (skip → confirm → pick), shuffles choices on every load, applies the chosen stat dict (with Focus and Empathy turn-boosts on top), and returns a result dict for logging.

- **`DataLogger`** (`data_logger.py`): writes one CSV row per turn capturing 19 fields (session id, turn number, patient identity, choice text, all stat values, warning flag, decision time, session outcome, session score). Generates a fresh `session_id` for each new patient and finalizes the outcome / score when the session ends. Includes `calculate_score(hearts_lost, warning_count, success)` as a static method.

- **`Shop`** (`shop.py`): inventory, coin tracking, single-use effects (`active_effects`), and turn-counted effects (`turn_effects`). Methods: `earn_coins()`, `buy()`, `can_afford()`, `has_effect()`, `consume_effect()`, `get_turn_effect()`, `reset_session_effects()`.

- **`ShopUI`** (`shop.py`): the Pygame UI for the shop. A sliding two-panel layout (item grid on the left, item details + Buy button on the right) with hover, selected state, out-of-stock dimming, and immediate purchase effects routed back to the game (Extra Heart restores, Cleanser removes Weakness, etc.).

### UI helpers

- **`IllnessQuiz`** (`session.py`): end-of-session 5-option quiz panel with shuffled options, hover highlights, correct / wrong feedback, and a 2.5-second result timer.
- **`GuideBubble`** (`session.py`): the bottom-right speech bubble shown for the first 3 warnings of a session, with an auto-dismiss timer.
- **`SettingsPanel`** (`game.py`): modal panel with BGM and SFX sliders and a "Stats" tab that launches the dashboard.
- **`Slider`** (`game.py`): reusable horizontal slider widget with knob drag, percentage label, and a clamped value.
- **`TutorialOverlay`** (`game.py`): 5-page tutorial shown the first time you click Begin. The guide sprite changes expression per page, with **Next** and **Skip** buttons.

### Statistics

- **`Dashboard`** (`stats_panel/dashboard.py`): Tkinter window built on a `ttk.Notebook` with 7 tabs. Reads `session_log.csv` with pandas, embeds matplotlib figures via `FigureCanvasTkAgg`, and runs in its own process via `multiprocessing.spawn` so it doesn't clash with Tkinter's main-thread restriction.

### Utility classes

- **`Timer`, `FadeTransition`, `PulseEffect`, `JumpTransform`, `WarningFlash`** — small animation helpers in `utils.py` and `ui.py` used for visual polish (intro timer, fade-in / out between phases, pulsing on warnings, jump animation on the patient / player when a choice is made, full-screen red flash on warning).

### Design patterns used

- **State Machine** — `Game.state` and `Session.phase` cleanly separate behavior per state with explicit transitions.
- **Template Method / Inheritance** — `Patient` defines the shared logic, and each subclass overrides `on_stat_fail()` for its own consequence.
- **Strategy / Factory** — `create_random_patient()` picks a random concrete subclass via weighted illness selection and returns a fully initialised instance.
- **Composition** — `Session` is built out of Patient, StatSystem, DialogueManager, etc. instead of inheriting; `Game` is built out of Shop, ShopUI, DataLogger, etc.
- **Observer (light)** — `StatSystem` reacts to changes pushed through `Patient.update_stat()` and re-evaluates flags every turn.

---

## 5. Statistical Data

### 5.1 Data Recording Method

All gameplay data is saved to `Soft Hours/data/saves/session_log.csv` using Python's built-in `csv` module. The `DataLogger` class writes one row **per turn** in append mode, capturing every tracked feature at the moment a choice is made. `session_outcome` and `session_score` are written as `PENDING` placeholders during the session and back-filled to their final values when the session closes (success / walked_away / game_over and the computed score), which keeps every row the same shape.

A new `session_id` (8-char UUID) is generated at the start of each patient session via `DataLogger.new_session()`, so multiple playthroughs and multiple patients within one run all accumulate in the same CSV file but stay distinguishable for per-session analysis.

The CSV is auto-created on first launch with a header row. If an old headerless CSV is detected on startup, `DataLogger._ensure_file()` repairs it by prepending the header.

### 5.2 Data Features

The CSV records 19 columns per turn. The 7 player-meaningful features (per the proposal table) are:

| Feature | Why collect it | Source | Display |
|---|---|---|---|
| **Turn Number** | Aligns every other feature to a point in time and measures session length. | `Patient.turn` via `DataLogger` | X-axis for time-series charts |
| **Patient Illness** | Lets us compare difficulty and outcomes across illness categories. | `Patient.illness` | Category axis (bar / pie) |
| **Stat Values** | Tracks all 7 emotional stats per turn so we can see how the player's choices affect the patient's wellbeing over time. | `StatSystem.snapshot()` | Line graph (stat trends) |
| **Warning Triggered** | Shows which stats are hardest to manage and which illness is the most demanding. | `StatSystem.check_range()` | Bar chart, correlation heatmap |
| **Time Per Turn** | Shows where the player hesitated; gives a sense of difficulty per illness type. | `time.time()` diff in `DialogueManager.apply_choice()` | Boxplot per illness |
| **Session Outcome** | Measures overall player performance and success rate per illness. | Set at session end | Bar chart per illness |
| **Session Score** | Tracks player improvement across runs (`+10 success, −5 per heart lost, −2 per warning`). | `DataLogger.calculate_score()` | Line graph trend |

The dashboard computes **mean** (avg time per turn, mean stat per turn), **frequency counts** (warnings per stat, outcomes per illness), **min / max** (score axis bounds), and **mode** (most-seen illness in the summary).

### Volume guarantee

A typical session is 20–40 turns, so even one short run of 5+ patients produces well over 100 rows. The CSV is in append mode so playthroughs accumulate naturally — the dashboard's Data Log tab shows a live row-count indicator that turns green once 100 rows is reached.

---

## 6. Changed Proposed Features

A few things shifted between the proposal and the final implementation:

- **Hearts:** the proposal said 3 hearts; the final build uses **5 hearts** for a longer, more forgiving run.
- **Shop:** the proposal had a smaller shop concept; the final shop has 8 items spanning single-use, session-wide, and turn-counted boosts (Case File, Extra Heart, Coffee, Calming Tea, Empathy Boost, Focus Notes, Cleanser, Stress Ball).
- **Illness quiz and Weakness debuff** were added on top of the proposal's "consequence resolution" — they were implied there, but became a dedicated quiz screen and a persistent debuff system.
- **Correlation heatmap** (graph 5 in the proposal) was replaced with the **Score Trend**, **Warnings**, and **Outcomes** tabs, which together tell the same story (stat neglect ↔ session outcome) more clearly than a single heatmap would.
- **Stat scaling:** added the `STAT_SCALE = 5` multiplier so the JSON deltas (kept small for readable dialogue files) produce meaningful in-game changes.

---

## 7. External Sources

### Source code / libraries

- **Pygame** — https://www.pygame.org — game engine and rendering. License: LGPL.
- **Pandas** — https://pandas.pydata.org — CSV loading and analysis in the dashboard. License: BSD-3.
- **Matplotlib** — https://matplotlib.org — chart rendering. License: Matplotlib License (PSF-style).
- **Tkinter** — Python standard library.
- **Python `csv`, `uuid`, `multiprocessing`, `os`, `json`** — standard library modules.

### Fonts

- **Pencilant Script** — used for in-game UI. Free font for personal use.

### Art / audio

All sprite art (5 patient color sets × 6 emotions, the player therapist × 14 emotions, the guide × 2 expressions), the hospital_entrance background, and every BGM and SFX track were made from scratch for this project.

### Mechanical inspiration

- **NEEDY STREAMER OVERLOAD** (WSS playground) — stat-management visual novel concept.
- **Volcano Princess** (CE-Asia) — emotional stat compounding.
- **That's Not My Neighbor** (Nacho Sama) — repeatable per-encounter loop.

Only the design philosophy of those games was used as inspiration. **No assets, code, or text were copied.**
