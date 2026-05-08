# Soft Hours

## Project Description

- **Project by:** Apichai Pattanakamolkul
- **Game Genre:** Visual Novel / Stat-Management

Soft Hours is a turn-based visual novel made with **Python 3** and **Pygame**. You play a therapist seeing one patient after another, and each patient comes in with a different name, age, background, and one of five mental health conditions (Overthinking, Anger, Depression, Trauma, Burnout). The dialogue choices you pick quietly push their emotional stats up or down — your job is to keep them stable until the session ends. Every turn you play is saved to a CSV file, and the game ships with a built-in Tkinter statistics dashboard that turns that file into charts.

For the full breakdown of the OOP design, the UML diagram, and how the data is collected and visualized, see [DESCRIPTION.md](DESCRIPTION.md).

For a tour of the statistics dashboard tab-by-tab (with screenshots and the statistical measures used), see [VISUALIZATION.md](screenshots/visualization/VISUALIZATION.md).

---

## Installation

Clone the project:

```sh
git clone https://github.com/<username>/<project-name>.git
```

Set up a Python environment and install the dependencies:

**Windows**

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

**Mac**

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Running Guide

Once the environment is active, run the game from the project root (the folder that contains `Soft Hours/`):

**Windows**

```bat
python "Soft Hours/main.py"
```

**Mac**

```sh
python3 "Soft Hours/main.py"
```

The first time you run the game, it creates `Soft Hours/data/saves/` for you. That folder will hold `session_log.csv` (your gameplay data) and `settings.json` (volume preferences).

---

## Tutorial / Usage

1. Click **Begin** on the main menu. A 5-page tutorial walks you through the basics.
2. A patient walks in. You see their name, age, occupation, and a short background.
3. Read what they say — click once to skip the typewriter reveal, click again to bring up the choices.
4. Pick a response. Each choice quietly nudges the patient's stats.
5. Watch the stat panel on the right. Hope, Calm, Trust, Motivation, and the unique stat should stay high. Exhaustion and Loneliness should stay low.
6. If a stat hits the danger zone the screen flashes red. If it hits the absolute limit the patient leaves.
7. After the session you take the **illness quiz** — guess what the patient was struggling with for a coin reward.
8. Click the **shop** icon (top-left) to spend your coins on items like Coffee, Calming Tea, Case File, Empathy Boost, Cleanser, or an Extra Heart.
9. Open **Settings → Stats** any time to launch the statistics dashboard in a separate window.

**Controls:** mouse only. `R` restarts after a game over, and `Enter` starts the game from the main menu.

---

## Game Features

- 5 patient illness types, each with a unique stat and its own failure consequence
- Randomized identity per patient — name (Thai / Japanese / English pools), age, occupation, background
- 6 shared emotional stats plus 1 unique stat tied to the illness
- Choice positions are shuffled every turn so there's no positional pattern to memorize
- 3-stage click flow — text reveal → confirm → choices — for deliberate pacing
- End-of-session illness quiz with coin and heart consequences
- **Weakness debuff** that carries between sessions, doubling bad stat hits and heart loss
- Shop with 8 items split between single-use, session-wide, and turn-counted boosts
- 5 hearts; lose them all and it's game over
- Guide character that appears in the tutorial and during the first 3 warnings of each session
- Built-in statistics dashboard with 7 tabs (Summary, Stat Trends, Warnings, Decision Time, Outcomes, Score Trend, Data Log) using Tkinter and matplotlib
- Volume settings persist between runs
- Custom font, original sprite art, and original BGM / SFX for each game state

---

## Known Bugs

- The "Active turn effects" line inside the shop panel reads from the raw purchase counter, so it doesn't tick down as you spend turns. The accurate per-turn count is shown in the in-session HUD (the Focus / Empathy badges below the stat panel).
- On some systems the dashboard window flickers briefly the first time it opens because `multiprocessing.spawn` has to start a fresh Python interpreter.

---

## Unfinished Works

Everything from the original proposal made it into the final build, so there's nothing left unfinished.

---

## External sources

1. **Pygame** — game engine, https://www.pygame.org [LGPL]
2. **Pandas** — CSV analysis in the dashboard, https://pandas.pydata.org [BSD-3]
3. **Matplotlib** — chart rendering, https://matplotlib.org [Matplotlib License]
4. **Pencilant Script** font — used for in-game UI; free for personal use
5. All sprite art (5 patient color sets, the player therapist, the guide), the background image, and every BGM and SFX track were drawn or recorded from scratch for this project.
6. Mechanical inspiration from **NEEDY STREAMER OVERLOAD**, **Volcano Princess**, and **That's Not My Neighbor** — only the design ideas of repeatable stat-management loops were borrowed; no assets or code were copied.
