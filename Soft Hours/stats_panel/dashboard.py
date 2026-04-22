"""
dashboard.py — Soft Hours statistics dashboard
Clean black-and-white theme.

Place this file inside the stats_panel/ folder (imported as stats_panel.dashboard).
The CSV path is resolved relative to THIS file so it always finds the correct
Soft Hours/data/saves/session_log.csv regardless of working directory.
"""
import tkinter as tk
from tkinter import ttk
import os
import threading

try:
    import pandas as pd
    import matplotlib
    matplotlib.use("TkAgg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    PANDAS_OK = True
except ImportError:
    PANDAS_OK = False
    print("[Dashboard] pandas or matplotlib not installed.")

# ── Path — anchored to dashboard.py location ─────────────────────────────────
# stats_panel/dashboard.py  →  go up one level to reach project root,
# then descend into data/saves/
_HERE    = os.path.dirname(os.path.abspath(__file__))
_ROOT    = os.path.dirname(_HERE)                        # project root (Soft Hours/)
LOG_PATH = os.path.join(_ROOT, "data", "saves", "session_log.csv")

# ── Palette ───────────────────────────────────────────────────────────────────
BG        = "#ffffff"
PANEL     = "#f5f5f5"
BORDER    = "#cccccc"
FG        = "#111111"
FG_DIM    = "#555555"
ACCENT    = "#222222"
HIGHLIGHT = "#000000"
DANGER    = "#cc3333"
SUCCESS   = "#228833"
WARN_BG   = "#fff3cd"    # light amber row highlight for warnings in data log


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def load_data():
    if not PANDAS_OK:
        return None
    if not os.path.exists(LOG_PATH):
        return None
    try:
        df = pd.read_csv(LOG_PATH)
        if df.empty:
            return None
        num_cols = ["turn_number", "stat_hope", "stat_calm", "stat_trust",
                    "stat_motivation", "stat_exhaustion", "stat_loneliness",
                    "stat_unique", "warning_triggered", "time_per_turn"]
        for col in num_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        return df
    except Exception as e:
        print(f"[Dashboard] Error loading CSV: {e}")
        return None


def apply_style(ax, title=""):
    ax.set_facecolor(PANEL)
    ax.tick_params(colors=FG_DIM, labelsize=8)
    for spine in ax.spines.values():
        spine.set_edgecolor(BORDER)
    ax.xaxis.label.set_color(FG_DIM)
    ax.yaxis.label.set_color(FG_DIM)
    if title:
        ax.set_title(title, color=FG, fontsize=10, pad=8, fontweight="bold")


# ─────────────────────────────────────────────────────────────────────────────
# Dashboard
# ─────────────────────────────────────────────────────────────────────────────

class Dashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Soft Hours — Statistics")
        self.root.configure(bg=BG)
        self.root.geometry("980x680")
        self.root.resizable(True, True)

        self.df = load_data()
        self._build_ui()

    # ── UI skeleton ───────────────────────────────────────────────────────────

    def _build_ui(self):
        # Top bar
        top = tk.Frame(self.root, bg=BG, pady=8)
        top.pack(fill="x", padx=20)

        tk.Label(top, text="Soft Hours", bg=BG, fg=FG,
                 font=("Arial", 20, "bold")).pack(side="left")
        tk.Label(top, text="Session Statistics", bg=BG, fg=FG_DIM,
                 font=("Arial", 12)).pack(side="left", padx=14)

        tk.Button(top, text="↺  Refresh", bg=ACCENT, fg=BG,
                  relief="flat", bd=0, padx=14, pady=5,
                  font=("Arial", 10, "bold"),
                  command=self._refresh).pack(side="right")

        # Show exact path so user knows where data is saved
        path_label = tk.Label(top, text=f"  {LOG_PATH}",
                              bg=BG, fg=FG_DIM, font=("Arial", 8))
        path_label.pack(side="right", padx=4)

        tk.Frame(self.root, bg=BORDER, height=1).pack(fill="x", padx=20, pady=(0, 6))

        if not PANDAS_OK:
            tk.Label(self.root,
                     text="pandas and matplotlib are required.\nRun: pip install pandas matplotlib",
                     bg=BG, fg=DANGER, font=("Arial", 13)).pack(expand=True)
            return

        if self.df is None:
            tk.Label(self.root,
                     text=f"No session data found.\n\nExpected file:\n{LOG_PATH}\n\nPlay some sessions first!",
                     bg=BG, fg=FG_DIM, font=("Arial", 13),
                     justify="center").pack(expand=True)
            return

        # Tabs
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook",     background=BG,    borderwidth=0)
        style.configure("TNotebook.Tab", background=PANEL, foreground=FG_DIM,
                        padding=[14, 6], font=("Arial", 10))
        style.map("TNotebook.Tab",
                  background=[("selected", BG)],
                  foreground=[("selected", FG)])
        style.configure("Treeview",
                        background=BG, foreground=FG,
                        fieldbackground=BG, rowheight=22,
                        font=("Arial", 9))
        style.configure("Treeview.Heading",
                        background=PANEL, foreground=FG,
                        font=("Arial", 9, "bold"))
        style.map("Treeview",
                  background=[("selected", ACCENT)],
                  foreground=[("selected", BG)])

        nb = ttk.Notebook(self.root)
        nb.pack(fill="both", expand=True, padx=16, pady=4)

        tabs = [
            ("Summary",       self._build_summary),
            ("Stat Trends",   self._build_stat_trends),
            ("Warnings",      self._build_warnings),
            ("Decision Time", self._build_time),
            ("Outcomes",      self._build_outcomes),
            ("Score Trend",   self._build_score),
            ("Data Log",      self._build_data_log),
        ]
        for label, builder in tabs:
            frame = tk.Frame(nb, bg=BG)
            nb.add(frame, text=label)
            builder(frame)

    # ── Tab: Summary ──────────────────────────────────────────────────────────

    def _build_summary(self, parent):
        df = self.df
        total_turns    = len(df)
        total_sessions = df["session_id"].nunique() if "session_id" in df.columns else 0
        total_warnings = int(df["warning_triggered"].sum()) if "warning_triggered" in df.columns else 0
        avg_time       = round(df["time_per_turn"].mean(), 2) if "time_per_turn" in df.columns else 0

        outcomes = {}
        if "session_outcome" in df.columns:
            valid    = df[df["session_outcome"] != "PENDING"]
            outcomes = valid["session_outcome"].value_counts().to_dict()

        stats_data = [
            ("Total Rows (Turns) Logged", str(total_turns)),
            ("Total Sessions",            str(total_sessions)),
            ("Total Warnings",            str(total_warnings)),
            ("Avg Time Per Turn",         f"{avg_time}s"),
            ("Successful Sessions",       str(outcomes.get("success", 0))),
            ("Walked Away",               str(outcomes.get("walked_away", 0))),
            ("Game Overs",                str(outcomes.get("game_over", 0))),
        ]

        frame = tk.Frame(parent, bg=BG)
        frame.pack(padx=24, pady=20, anchor="w")

        tk.Label(frame, text="Session Overview", bg=BG, fg=FG,
                 font=("Arial", 15, "bold")).grid(
                     row=0, column=0, columnspan=2, sticky="w", pady=(0, 14))

        for i, (label, value) in enumerate(stats_data, 1):
            tk.Label(frame, text=label, bg=BG, fg=FG_DIM,
                     font=("Arial", 11), width=28, anchor="w").grid(
                         row=i, column=0, sticky="w", pady=4)
            tk.Label(frame, text=value, bg=BG, fg=FG,
                     font=("Arial", 11, "bold"), width=14, anchor="w").grid(
                         row=i, column=1, sticky="w", pady=4)

        if "patient_illness" in df.columns:
            most_common = df["patient_illness"].mode()[0]
            r = len(stats_data) + 1
            tk.Label(frame, text="Most Seen Illness", bg=BG, fg=FG_DIM,
                     font=("Arial", 11), width=28, anchor="w").grid(
                         row=r, column=0, sticky="w", pady=4)
            tk.Label(frame, text=most_common.replace("_", " ").title(),
                     bg=BG, fg=HIGHLIGHT,
                     font=("Arial", 11, "bold"), width=20, anchor="w").grid(
                         row=r, column=1, sticky="w", pady=4)

    # ── Tab: Stat Trends ──────────────────────────────────────────────────────

    def _build_stat_trends(self, parent):
        df        = self.df
        stat_cols = ["stat_hope", "stat_calm", "stat_trust",
                     "stat_motivation", "stat_exhaustion", "stat_loneliness"]
        available = [c for c in stat_cols if c in df.columns]
        grays     = ["#111111", "#333333", "#555555", "#777777", "#999999", "#bbbbbb"]
        styles    = ["-", "--", "-.", ":", "-", "--"]

        fig, ax = plt.subplots(figsize=(8, 3.6), facecolor=BG)
        fig.patch.set_facecolor(BG)
        apply_style(ax, "Stat Values Over Turns (session mean)")

        for col, gray, ls in zip(available, grays, styles):
            label = col.replace("stat_", "").capitalize()
            mean_per_turn = df.groupby("turn_number")[col].mean()
            ax.plot(mean_per_turn.index, mean_per_turn.values,
                    label=label, color=gray, linewidth=1.8, linestyle=ls)

        ax.set_xlabel("Turn Number")
        ax.set_ylabel("Stat Value")
        ax.set_ylim(0, 100)
        ax.legend(fontsize=8, facecolor=PANEL, edgecolor=BORDER,
                  labelcolor=FG, loc="upper right")
        fig.tight_layout()
        self._embed_figure(fig, parent)

    # ── Tab: Warnings ─────────────────────────────────────────────────────────

    def _build_warnings(self, parent):
        df = self.df
        stat_cols = ["stat_hope", "stat_calm", "stat_trust",
                     "stat_motivation", "stat_exhaustion", "stat_loneliness", "stat_unique"]
        available = [c for c in stat_cols if c in df.columns]

        warn_counts = {}
        for col in available:
            label = col.replace("stat_", "").capitalize()
            if col in ["stat_exhaustion", "stat_loneliness"]:
                count = int((df[col] >= 80).sum())
            else:
                count = int((df[col] <= 20).sum())
            warn_counts[label] = count

        fig, ax = plt.subplots(figsize=(8, 3.6), facecolor=BG)
        fig.patch.set_facecolor(BG)
        apply_style(ax, "Warning Frequency Per Stat")

        bars = ax.bar(list(warn_counts.keys()), list(warn_counts.values()),
                      color=FG_DIM, edgecolor=FG, linewidth=0.8)
        for bar, val in zip(bars, warn_counts.values()):
            ax.text(bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.3,
                    str(val), ha="center", va="bottom", color=FG, fontsize=9)

        ax.set_xlabel("Stat")
        ax.set_ylabel("Warning Count")
        fig.tight_layout()
        self._embed_figure(fig, parent)

    # ── Tab: Decision Time ────────────────────────────────────────────────────

    def _build_time(self, parent):
        df = self.df
        if "time_per_turn" not in df.columns or "patient_illness" not in df.columns:
            tk.Label(parent, text="No time data available.", bg=BG, fg=FG_DIM).pack(expand=True)
            return

        grouped   = df.groupby("patient_illness")["time_per_turn"]
        illnesses = list(grouped.groups.keys())
        data      = [grouped.get_group(ill).dropna().values for ill in illnesses]
        labels    = [ill.replace("_", " ").title() for ill in illnesses]

        fig, ax = plt.subplots(figsize=(8, 3.6), facecolor=BG)
        fig.patch.set_facecolor(BG)
        apply_style(ax, "Decision Time by Illness (seconds)")

        bp = ax.boxplot(data, labels=labels, patch_artist=True,
                        medianprops=dict(color=FG, linewidth=2))
        for patch in bp["boxes"]:
            patch.set_facecolor(PANEL)
            patch.set_edgecolor(FG)
        for w in bp["whiskers"]:  w.set_color(FG_DIM)
        for c in bp["caps"]:      c.set_color(FG_DIM)
        for f in bp["fliers"]:    f.set(markerfacecolor=FG_DIM, markersize=4)

        ax.set_ylabel("Seconds")
        ax.tick_params(axis="x", labelrotation=15)
        fig.tight_layout()
        self._embed_figure(fig, parent)

    # ── Tab: Outcomes ─────────────────────────────────────────────────────────

    def _build_outcomes(self, parent):
        df = self.df
        if "session_outcome" not in df.columns or "patient_illness" not in df.columns:
            tk.Label(parent, text="No outcome data.", bg=BG, fg=FG_DIM).pack(expand=True)
            return

        valid = df[df["session_outcome"] != "PENDING"].copy()
        if valid.empty:
            tk.Label(parent, text="No completed sessions yet.", bg=BG, fg=FG_DIM).pack(expand=True)
            return

        session_rows = valid.groupby("session_id").last().reset_index()
        pivot = session_rows.groupby(
            ["patient_illness", "session_outcome"]).size().unstack(fill_value=0)

        illnesses = [ill.replace("_", " ").title() for ill in pivot.index]
        outcomes  = list(pivot.columns)
        x         = range(len(illnesses))
        bar_w     = 0.25
        gray_map  = {"success": "#333333", "walked_away": "#888888", "game_over": "#cccccc"}
        hatch_map = {"success": "",         "walked_away": "//",      "game_over": "xx"}

        fig, ax = plt.subplots(figsize=(8, 3.6), facecolor=BG)
        fig.patch.set_facecolor(BG)
        apply_style(ax, "Session Outcomes by Illness")

        for i, outcome in enumerate(outcomes):
            vals   = pivot[outcome].values
            offset = (i - len(outcomes) / 2) * bar_w + bar_w / 2
            ax.bar([xi + offset for xi in x], vals, width=bar_w,
                   label=outcome.replace("_", " ").title(),
                   color=gray_map.get(outcome, FG_DIM),
                   hatch=hatch_map.get(outcome, ""),
                   edgecolor=FG, linewidth=0.6)

        ax.set_xticks(list(x))
        ax.set_xticklabels(illnesses, rotation=15, ha="right")
        ax.set_ylabel("Session Count")
        ax.legend(fontsize=8, facecolor=PANEL, edgecolor=BORDER, labelcolor=FG)
        fig.tight_layout()
        self._embed_figure(fig, parent)

    # ── Tab: Score Trend ──────────────────────────────────────────────────────

    def _build_score(self, parent):
        df = self.df
        if "session_score" not in df.columns:
            tk.Label(parent, text="No score data.", bg=BG, fg=FG_DIM).pack(expand=True)
            return

        valid = df[df["session_score"] != "PENDING"].copy()
        if valid.empty:
            tk.Label(parent, text="No completed sessions yet.", bg=BG, fg=FG_DIM).pack(expand=True)
            return

        valid["session_score"] = pd.to_numeric(valid["session_score"], errors="coerce")
        scores = valid.groupby("session_id")["session_score"].last().reset_index()
        scores["run"] = range(1, len(scores) + 1)

        fig, ax = plt.subplots(figsize=(8, 3.6), facecolor=BG)
        fig.patch.set_facecolor(BG)
        apply_style(ax, "Session Score Over Time")

        ax.plot(scores["run"], scores["session_score"],
                color=FG, linewidth=2, marker="o", markersize=5)
        ax.axhline(0, color=BORDER, linewidth=1, linestyle="--")
        ax.fill_between(scores["run"], scores["session_score"], 0,
                        where=(scores["session_score"] >= 0), alpha=0.12, color=FG)
        ax.fill_between(scores["run"], scores["session_score"], 0,
                        where=(scores["session_score"] < 0), alpha=0.12, color=DANGER)
        ax.set_xlabel("Session Number")
        ax.set_ylabel("Score")
        fig.tight_layout()
        self._embed_figure(fig, parent)

    # ── Tab: Data Log ─────────────────────────────────────────────────────────

    def _build_data_log(self, parent):
        """
        Raw CSV viewer: scrollable table of every row collected.
        - Row count prominently displayed at top.
        - Rows where warning_triggered == 1 are highlighted in amber.
        - Horizontal + vertical scrollbars.
        - Last 200 rows shown by default (full data still in CSV).
        """
        df = self.df

        total_rows = len(df)

        # ── Header bar ────────────────────────────────────────────────────────
        header = tk.Frame(parent, bg=BG)
        header.pack(fill="x", padx=12, pady=(10, 4))

        count_color = SUCCESS if total_rows >= 100 else (DANGER if total_rows == 0 else FG)
        tk.Label(header,
                 text=f"Total rows in CSV: {total_rows}",
                 bg=BG, fg=count_color,
                 font=("Arial", 14, "bold")).pack(side="left")

        target_label = ("  ✔ Target of 100 rows reached!" if total_rows >= 100
                        else f"  ({100 - total_rows} more rows needed to reach 100)")
        tk.Label(header, text=target_label, bg=BG,
                 fg=SUCCESS if total_rows >= 100 else FG_DIM,
                 font=("Arial", 10)).pack(side="left")

        # Path reminder
        tk.Label(header, text=f"  File: {LOG_PATH}",
                 bg=BG, fg=FG_DIM, font=("Arial", 8)).pack(side="right")

        # ── Treeview ──────────────────────────────────────────────────────────
        cols = list(df.columns)

        container = tk.Frame(parent, bg=BG)
        container.pack(fill="both", expand=True, padx=12, pady=(0, 8))

        # Scrollbars
        vsb = ttk.Scrollbar(container, orient="vertical")
        hsb = ttk.Scrollbar(container, orient="horizontal")
        vsb.pack(side="right",  fill="y")
        hsb.pack(side="bottom", fill="x")

        tree = ttk.Treeview(
            container,
            columns=cols,
            show="headings",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set,
        )
        vsb.config(command=tree.yview)
        hsb.config(command=tree.xview)
        tree.pack(fill="both", expand=True)

        # Column headings + widths
        col_widths = {
            "session_id": 70, "turn_number": 50, "patient_name": 100,
            "patient_illness": 90, "patient_occupation": 100,
            "emotional_state": 80, "choice_made": 200,
            "stat_hope": 50, "stat_calm": 50, "stat_trust": 50,
            "stat_motivation": 70, "stat_exhaustion": 70, "stat_loneliness": 70,
            "stat_unique": 60, "stat_unique_name": 80,
            "warning_triggered": 80, "time_per_turn": 80,
            "session_outcome": 90, "session_score": 70,
        }
        for col in cols:
            w = col_widths.get(col, 80)
            tree.heading(col, text=col.replace("_", " ").title())
            tree.column(col, width=w, minwidth=40, anchor="center")

        # Row tags for warning highlight
        tree.tag_configure("warning", background=WARN_BG, foreground="#7a4800")
        tree.tag_configure("normal",  background=BG,      foreground=FG)

        # Show up to 500 rows (most recent first)
        display_df = df.tail(500).iloc[::-1].reset_index(drop=True)

        for _, row in display_df.iterrows():
            values = [str(row[c]) if not pd.isna(row[c]) else "" for c in cols]
            tag    = "warning" if str(row.get("warning_triggered", "0")) == "1" else "normal"
            tree.insert("", "end", values=values, tags=(tag,))

        # Show note if data was truncated
        if total_rows > 500:
            note = tk.Label(parent,
                            text=f"Showing last 500 of {total_rows} rows. Open the CSV directly to see all.",
                            bg=BG, fg=FG_DIM, font=("Arial", 8))
            note.pack(pady=(0, 4))

    # ── Embed helper ──────────────────────────────────────────────────────────

    def _embed_figure(self, fig, parent):
        fig.patch.set_facecolor(BG)
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=8)
        plt.close(fig)

    # ── Refresh ───────────────────────────────────────────────────────────────

    def _refresh(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        self.df = load_data()
        self._build_ui()


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

def _dashboard_process():
    """
    Runs in a separate process so Tkinter has its own main thread.
    Avoids RuntimeError: main thread is not in main loop on Python 3.10+/Windows.
    """
    import tkinter as _tk
    _root = _tk.Tk()
    Dashboard(_root)
    _root.mainloop()


def open_dashboard():
    """
    Open the dashboard in a completely separate process.
    multiprocessing 'spawn' gives Tkinter its own main thread.
    """
    import multiprocessing
    ctx = multiprocessing.get_context("spawn")
    p   = ctx.Process(target=_dashboard_process, daemon=True)
    p.start()


if __name__ == "__main__":
    root = tk.Tk()
    Dashboard(root)
    root.mainloop()