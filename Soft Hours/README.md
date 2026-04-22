# Soft Hours

> *A visual-novel-style therapy simulation game built in Python & Pygame.*

---

## Table of Contents

- [About](#about)
- [How the Game Works](#how-the-game-works)
- [How to Play](#how-to-play)
- [Patient Types](#patient-types)
- [Stats System](#stats-system)
- [Shop](#shop)
- [Scoring & Data Logging](#scoring--data-logging)
- [Known Bugs (Current Build)](#known-bugs-current-build)
- [Running the Game](#running-the-game)
- [Credits](#credits)

---

## About

**Soft Hours** is a single-player dialogue-driven game where you play as a therapist managing sessions with patients who each carry a different mental health condition. Your job is to listen, respond carefully, and guide the conversation without letting the patient's emotional stats fall into critical territory.

The game tracks your decisions and saves them to a CSV file so you can review your performance in a statistics dashboard after playing.

---

## How the Game Works

### The Core Loop

1. A new patient arrives. They are **randomly generated** — name, age, occupation, background, and illness type are all randomised each time.
2. The patient speaks. Text is revealed character by character.
3. Once the text finishes, you click to reveal **four response choices**.
4. Each choice carries **hidden stat modifiers** — some help, some hurt, some are neutral. You won't always know which is which until you learn the patterns.
5. After your choice is applied, the patient's stats update and the next dialogue loads.
6. A session continues for up to **40 turns** or until it ends early due to a critical stat failure.
7. Between sessions you can spend coins in the **Shop** to buy items that give you an edge.

### Session Outcomes

| Outcome | What happened |
|---|---|
| **Success** | Session completed without stats going critical |
| **Walked Away** | Patient's stats reached a breaking point — they left |
| **Game Over** | A specific patient type (anger) reached critical — triggered instant game over |

### Hearts

You have **5 hearts**. Losing a session (walk-away or game over) costs hearts. Losing all 5 hearts ends the run. A new run resets everything.

---

## How to Play

### Starting the Game

1. Clone or download the project.
2. Make sure Python and Pygame are installed (see [Running the Game](#running-the-game)).
3. Run **`main.py`** from the project root (inside the `Soft Hours/` folder).
4. From the main menu, press **Enter** or click **Begin**.

### In a Session

| Action | How |
|---|---|
| Skip text reveal | Click anywhere during text animation |
| Show choices | Click after text has finished revealing |
| Make a choice | Click one of the four response buttons |
| Open shop | Click the shop icon (top-left, below settings) |
| Open settings | Click the gear icon (top-left) |

### Three-Click Flow

Each turn works in three stages:
1. **Text is revealing** → Click to skip to full reveal
2. **Text fully shown** → Click to display your four choices
3. **Choices visible** → Click a button to make your pick

### Reading the UI

- **Hearts** (top-right): Your remaining lives — circles filled with dark red are active hearts; empty circles are lost.
- **Stat bars** (side panel): Each stat has a bar from 0–100. Bars turn red when a stat is in warning range.
- **Warning stats**: Hope, Calm, Trust, Motivation, and the patient's unique stat warn when they fall **below 20**. Exhaustion and Loneliness warn when they rise **above 80**.

---

## Patient Types

Each patient has a unique **colour, illness, and special stat**. The same choice can land very differently depending on who you're talking to.

| Patient | Colour | Illness | Unique Stat | Critical Reaction |
|---|---|---|---|---|
| Overthinking | Purple | Overthinking | Clarity | Walks away |
| Anger | Red | Anger Issues | Control | **Instant game over** |
| Depression | Blue | Depression | Presence | Walks away |
| Trauma | Green | Trauma | Stability | Walks away |
| Burnout | Orange | Burnout | Energy | Walks away |

> ⚠️ Be especially careful with the **Anger patient**. A critical stat failure triggers an immediate game over rather than a gentle walk-away.

---

## Stats System

Every patient has **7 shared stats** plus **1 unique stat** tied to their illness:

| Stat | Type | Dangerous when… |
|---|---|---|
| Hope | Positive | Falls below 20 |
| Calm | Positive | Falls below 20 |
| Trust | Positive | Falls below 20 |
| Motivation | Positive | Falls below 20 |
| Exhaustion | Pressure | Rises above 80 |
| Loneliness | Pressure | Rises above 80 |
| Clarity / Control / Presence / Stability / Energy | Unique | Falls below 20 |

All stats start at **50** and are clamped between 0 and 100. JSON choice deltas are multiplied by **×5** in-game, so small numbers in the dialogue files produce meaningful swings on screen.

When a stat hits its warning threshold a **red flash border** appears on screen and the warning is logged.

---

## Shop

Between or during sessions you can open the **Shop** (top-left icon) and spend **coins** on items.

Coins are earned by completing sessions successfully.

| Item | Effect | Price |
|---|---|---|
| Case File | Reveals the patient's illness before the session | 18c |
| Extra Heart | Restores 1 lost heart immediately | 40c |
| Coffee | Reduces patient Exhaustion by 20 at session start | 10c |
| Calming Tea | All negative stat changes halved for the whole session | 22c |
| Empathy Boost | Every positive stat gain doubled for next 10 turns | 28c |
| Focus Notes | Every good choice gives +2 bonus to positive stats for 15 turns | 20c |
| Cleanser | Removes the Weakness debuff; restores 5 Calm | 30c |
| Stress Ball | Next stat warning this session is completely ignored | 14c |

---

## Scoring & Data Logging

At the end of each session a score is calculated:

```
+10   successful session
 -5   per heart lost
 -2   per warning triggered
```

Every turn is written to a CSV file at:
```
Soft Hours/data/saves/session_log.csv
```

The file accumulates across multiple runs. You can view it through the **Stats panel** (Settings → Stats tab) which opens a Tkinter window with charts including stat trend lines, warning frequency bars, decision time boxplots, and session score over time.

---

## Known Bugs (Current Build)

This release is **fully playable from start to finish**, but a few systems are not working correctly yet:

- **Heart loss does not trigger properly** — you can play through sessions without actually losing hearts when you should. This means you likely cannot lose a run in this build.
- **Tutorial does not display** — the opening tutorial/guide screen is missing in this version.
- **Stats dashboard (Tkinter window)** — the statistics panel opens but may display data in an unformatted or unexpected way. The CSV data itself is still being recorded correctly.

These are known issues being actively worked on. The core gameplay loop — dialogue, choices, stat management, shop — works as intended.

---

## Running the Game

### Requirements

```
Python 3.10+
pygame
pandas
matplotlib
```

Install dependencies:
```bash
pip install pygame pandas matplotlib
```

### Running

Navigate into the project folder and run:
```bash
python main.py
```

If you're new to Python and just want to get it running:
1. Make sure Python is installed from [python.org](https://python.org)
2. Open a terminal / command prompt in the `Soft Hours/` folder
3. Run `pip install pygame pandas matplotlib`
4. Run `python main.py`

---

## Credits

**Development**
Apichai Pattanakamolkul

**Fonts**
- *Architext* by Grant Marshall — [1001fonts.com](https://www.1001fonts.com/) *(Free for commercial use)*
- *Pencilant Script* by Glotta Studio — [1001fonts.com](https://www.1001fonts.com/) *(Free for commercial use)*

**Music**
- BGM generated with Suno.AI

**Sound Effects**
- Driken Stan — Pixabay
- u_u4pf5h7zip — Pixabay

---

*Soft Hours — Version 0.1 (playable build, in development)*