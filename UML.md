# UML Class Diagram — Soft Hours

> **Submission note:** the official submission UML is [`UML.pdf`](UML.pdf) at the project root. This `.md` file is a text source you can keep updated alongside the code — paste the Mermaid block below into <https://mermaid.live> to re-render and export a fresh PDF.

```mermaid
classDiagram
    class Game {
        +screen
        +width: int
        +height: int
        +state: str
        +hearts: int
        +weakness_active: bool
        +patients_seen: int
        +current_session: Session
        +shop: Shop
        +shop_ui: ShopUI
        +logger: DataLogger
        +settings: SettingsPanel
        +tutorial: TutorialOverlay
        +change_state(new_state)
        +lose_heart(amount)
        +open_stats_panel()
        +handle_event(event)
        +update(dt)
        +draw()
    }

    class Session {
        +game: Game
        +shop: Shop
        +logger: DataLogger
        +phase: str
        +outcome: str
        +weakness_active: bool
        +patient: Patient
        +stat_system: StatSystem
        +dialogue_mgr: DialogueManager
        +quiz: IllnessQuiz
        +guide_bubble: GuideBubble
        +slow_drain: bool
        +ignore_next_warning: bool
        +update(dt)
        +handle_event(event)
        +draw()
        +is_done() bool
    }

    class Patient {
        <<abstract>>
        +name: str
        +age: int
        +occupation: str
        +background: str
        +stats: dict
        +emotion: str
        +turn: int
        +illness: str
        +unique_stat: str
        +sprite_color: str
        +update_stat(stat_name, delta)
        +apply_choice(choice_dict)
        +get_next_dialogue() dict
        +set_emotion(emotion)
        +is_critical() bool
        +on_stat_fail() str
    }

    class OverthinkingPatient {
        +illness = "overthinking"
        +unique_stat = "clarity"
        +sprite_color = "purple"
        +on_stat_fail() "walk_away"
    }

    class AngerPatient {
        +illness = "anger"
        +unique_stat = "control"
        +sprite_color = "red"
        +on_stat_fail() "game_over"
    }

    class DepressionPatient {
        +illness = "depression"
        +unique_stat = "presence"
        +sprite_color = "blue"
        +on_stat_fail() "walk_away"
    }

    class TraumaPatient {
        +illness = "trauma"
        +unique_stat = "stability"
        +sprite_color = "green"
        +on_stat_fail() "walk_away"
    }

    class BurnoutPatient {
        +illness = "burnout"
        +unique_stat = "energy"
        +sprite_color = "orange"
        +on_stat_fail() "walk_away"
    }

    class StatSystem {
        +patient: Patient
        +warning_flags: dict
        +warning_history: list
        +update(stat_deltas) list
        +check_range() list
        +is_critical() bool
        +trigger_warning(turn_number)
        +snapshot() dict
        +get_warning_count() int
        +get_display_stats() list
    }

    class DialogueManager {
        +patient: Patient
        +stat_system: StatSystem
        +current_entry: dict
        +choices: list
        +text_complete: bool
        +waiting_choice: bool
        +waiting_click: bool
        +focus_turns_left: int
        +empathy_turns_left: int
        +session_done: bool
        +load_next()
        +handle_event(event) dict
        +apply_choice(index) dict
        +update(dt)
        +is_done() bool
    }

    class DataLogger {
        +session_id: str
        +turn_rows: list
        +session_done: bool
        +log_turn(patient, choice_result, emotional_state)
        +log_session_end(outcome, score)
        +new_session()
        +export_csv(path)
        +calculate_score(hearts_lost, warning_count, success)$ int
    }

    class Shop {
        +inventory: list
        +coins: int
        +active_effects: set
        +turn_effects: dict
        +earn_coins(amount)
        +buy(item_id) bool
        +can_afford(item_id) bool
        +has_effect(name) bool
        +consume_effect(name)
        +get_turn_effect(key) int
        +reset_session_effects()
    }

    class ShopUI {
        +visible: bool
        +selected_index: int
        +panel_rect
        +right_rect
        +icon_rects: list
        +toggle()
        +handle_event(event, shop, game) bool
        +update(dt)
        +draw(surface, shop)
    }

    class IllnessQuiz {
        +correct_illness: str
        +options: list
        +selected: int
        +result: str
        +handle_event(event) str
        +update(dt) bool
        +draw()
    }

    class GuideBubble {
        +sprites: dict
        +visible: bool
        +appearances: int
        +current_line: str
        +trigger()
        +update(dt)
        +draw(surface, fonts)
    }

    class SettingsPanel {
        +visible: bool
        +slider_bgm: Slider
        +slider_sfx: Slider
        +toggle()
        +handle_event(event, game) bool
        +draw(surface)
    }

    class Slider {
        +x: int
        +y: int
        +w: int
        +label: str
        +value: float
        +dragging: bool
        +handle_event(event) bool
        +draw(surface, font)
    }

    class TutorialOverlay {
        +page: int
        +visible: bool
        +guide_sprites: dict
        +handle_event(event) str
        +draw(surface)
    }

    class Dashboard {
        +df: DataFrame
        +root: Tk
        -_build_ui()
        -_tab_summary(parent)
        -_tab_stat_trends(parent)
        -_tab_warnings(parent)
        -_tab_time(parent)
        -_tab_outcomes(parent)
        -_tab_score(parent)
        -_tab_data_log(parent)
        -_refresh()
    }

    Patient <|-- OverthinkingPatient
    Patient <|-- AngerPatient
    Patient <|-- DepressionPatient
    Patient <|-- TraumaPatient
    Patient <|-- BurnoutPatient

    Game *-- Session
    Game *-- Shop
    Game *-- ShopUI
    Game *-- DataLogger
    Game *-- SettingsPanel
    Game *-- TutorialOverlay
    SettingsPanel *-- Slider

    Session *-- Patient
    Session *-- StatSystem
    Session *-- DialogueManager
    Session *-- IllnessQuiz
    Session *-- GuideBubble
    Session --> Shop : uses
    Session --> DataLogger : logs to

    StatSystem --> Patient : reads stats
    DialogueManager --> Patient : applies choices
    DialogueManager --> StatSystem : checks warnings

    Dashboard ..> DataLogger : reads CSV
```

## Relationship summary

| Relationship | Type | Description |
|---|---|---|
| `Patient → 5 subclasses` | Inheritance | Every concrete patient inherits from `Patient` and overrides `on_stat_fail()`. |
| `Game → Session/Shop/ShopUI/DataLogger/SettingsPanel/TutorialOverlay` | Composition | `Game` owns these — they live and die with the Game. |
| `Session → Patient/StatSystem/DialogueManager/IllnessQuiz/GuideBubble` | Composition | Session owns its per-patient subsystems. |
| `Session → Shop / DataLogger` | Association (uses) | Borrowed from Game rather than owned. |
| `StatSystem → Patient` | Association | Reads stats and updates flags. |
| `DialogueManager → Patient / StatSystem` | Association | Calls `apply_choice` / `check_range`. |
| `Dashboard ..> DataLogger CSV` | Dependency | Reads the file produced by DataLogger. |
| `SettingsPanel *-- Slider` | Composition | Settings panel owns two Slider instances. |
