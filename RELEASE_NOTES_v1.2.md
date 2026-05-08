# Soft Hours — v1.2 Release Notes

**Release date:** 2026-05-08
**Codename:** Submission-ready

This is the final submission build. v1.2 is mostly a cleanup and polish pass on top of v1.1 — no new gameplay systems, but a bunch of bug fixes that quietly broke the data side of the game, plus a full documentation overhaul.

---

## Bug fixes

- **Patient stats** — fixed a hardcoded `Clarity` key in the base `Patient` stats dict that was giving every non-Overthinking patient an 8th phantom stat. Each subclass now correctly gets exactly 6 shared stats + 1 unique stat.
- **DataLogger** — `new_session()` was reusing the same `session_id` for every patient in a run, which made the dashboard show "Sessions: 1" no matter how many patients you saw. Each patient now gets a fresh UUID.
- **Empathy Boost** — the extra positive hit was using the raw JSON delta instead of `delta * STAT_SCALE`, so the boost was 5× weaker than intended. Now scales correctly.
- **Calming Tea (slow drain)** — the slow-drain effect only modified the *logged* stat dict but never undid the full-strength delta that was already applied to the patient. Restructured `Session._process_choice_result()` so the correction lands on the actual patient stats, the post-correction values are re-snapshotted, and warnings are re-evaluated. Slow drain and Weakness now also stack correctly (Weakness's second hit uses the halved values).

## Code cleanup

- Stripped redundant comments and section dividers from every `.py` file. What remains explains the *why* behind non-obvious decisions (the `STAT_SCALE` multiplier, the slow-drain correction math, the multiprocessing.spawn dashboard launcher, the per-session UUID).
- Removed the previously-tracked `__pycache__` files from the repo and added them to `.gitignore` so they stop coming back.

## Documentation overhaul

- Rewrote `README.md` to follow the course rubric (project description, install, run, tutorial, features, known bugs, sources).
- Added `DESCRIPTION.md` covering all 7 required sections — overview, concept, UML, OOP implementation, statistical data, changed proposed features, external sources.
- Added `UML.md` (Mermaid source) alongside the official `UML.pdf` so the diagram is editable later.
- Added `screenshots/visualization/VISUALIZATION.md` documenting all 7 dashboard tabs with screenshots and a statistical-measures table.
- Added project-root `LICENSE` (MIT) and `requirements.txt`.

## Repo hygiene

- Added `.gitignore` covering Python caches, virtual environments, IDE files, OS files, and the auto-generated `session_log.csv` / `settings.json` saves.
- Kept the `Soft Hours/data/saves/.gitkeep` placeholder so the folder exists in fresh clones; the CSV is regenerated on first launch.

## Submission additions

- YouTube presentation link added to `DESCRIPTION.md` Section 1: https://youtu.be/BD4Hj3YkZwY
- Gameplay screenshots in `screenshots/gameplay/`
- Dashboard screenshots in `screenshots/visualization/`

---

## Upgrading from v1.1

No migration needed. Existing `session_log.csv` files from v1.1 are still readable — the dashboard auto-detects headerless CSVs and prepends the schema row on startup. New rows logged from v1.2 onwards will have correct per-session UUIDs, so the dashboard's "Sessions" count will start incrementing properly from your first v1.2 session.

If you want a clean slate, delete `Soft Hours/data/saves/session_log.csv` and it will be regenerated on the next launch.

---

## Known issues carried into v1.2

- The "Active turn effects" line inside the shop panel reads from the raw purchase counter and doesn't tick down per turn. The accurate count is shown in the in-session HUD (Focus / Empathy badges below the stat panel).
- The dashboard window may flicker briefly the first time it opens because `multiprocessing.spawn` has to start a fresh Python interpreter on Windows.
