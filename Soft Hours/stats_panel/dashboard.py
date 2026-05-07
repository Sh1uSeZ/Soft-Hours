import tkinter as tk
from tkinter import ttk
import os

try:
    import pandas as pd
    import matplotlib
    matplotlib.use("TkAgg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    PANDAS_OK = True
except ImportError:
    PANDAS_OK = False

# dashboard.py is inside stats_panel/ — go up once to reach Soft Hours/ root
_HERE    = os.path.dirname(os.path.abspath(__file__))
_ROOT    = os.path.dirname(_HERE)
LOG_PATH = os.path.join(_ROOT, "data", "saves", "session_log.csv")

BG      = "#ffffff"
PANEL   = "#f5f5f5"
BORDER  = "#cccccc"
FG      = "#111111"
FG_DIM  = "#555555"
ACCENT  = "#222222"
DANGER  = "#cc3333"
SUCCESS = "#228833"
WARN_BG = "#fff3cd"


def load_data():
    if not PANDAS_OK:
        return None
    candidates = [
        LOG_PATH,
        os.path.join(_HERE, "data", "saves", "session_log.csv"),
    ]
    found = next((p for p in candidates if os.path.exists(p)), None)
    if not found:
        print(f"[Dashboard] CSV not found. Tried: {candidates}")
        return None
    print(f"[Dashboard] Reading: {found}")
    try:
        df = pd.read_csv(found)
        if df.empty:
            return None

        expected_cols = [
            "session_id", "turn_number", "patient_name", "patient_illness",
            "patient_occupation", "emotional_state", "choice_made",
            "stat_hope", "stat_calm", "stat_trust", "stat_motivation",
            "stat_exhaustion", "stat_loneliness", "stat_unique", "stat_unique_name",
            "warning_triggered", "time_per_turn", "session_outcome", "session_score",
        ]
        # Headerless CSV: first column name will not be 'session_id'
        if df.columns[0] != "session_id":
            print("[Dashboard] No header detected — re-reading with forced column names.")
            df = pd.read_csv(found, header=None, names=expected_cols)

        for col in ["turn_number", "stat_hope", "stat_calm", "stat_trust",
                    "stat_motivation", "stat_exhaustion", "stat_loneliness",
                    "stat_unique", "warning_triggered", "time_per_turn"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        print(f"[Dashboard] Loaded {len(df)} rows. Columns: {list(df.columns)}")
        return df
    except Exception as e:
        print(f"[Dashboard] Load error: {e}")
        return None


def _chart_style(ax, title=""):
    ax.set_facecolor(PANEL)
    ax.tick_params(colors=FG_DIM, labelsize=8)
    for spine in ax.spines.values():
        spine.set_edgecolor(BORDER)
    ax.xaxis.label.set_color(FG_DIM)
    ax.yaxis.label.set_color(FG_DIM)
    if title:
        ax.set_title(title, color=FG, fontsize=10, pad=8, fontweight="bold")


def _no_data_label(parent, msg="No data available."):
    tk.Label(parent, text=msg, bg=BG, fg=FG_DIM,
             font=("Arial", 12), justify="center").pack(expand=True)


class Dashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Soft Hours — Statistics")
        self.root.configure(bg=BG)
        self.root.geometry("980x680")
        self.root.resizable(True, True)
        self.df = load_data()
        self._build_ui()

    def _build_ui(self):
        top = tk.Frame(self.root, bg=BG, pady=8)
        top.pack(fill="x", padx=20)
        tk.Label(top, text="Soft Hours", bg=BG, fg=FG,
                 font=("Arial", 20, "bold")).pack(side="left")
        tk.Label(top, text="Session Statistics", bg=BG, fg=FG_DIM,
                 font=("Arial", 12)).pack(side="left", padx=14)
        tk.Button(top, text="↺  Refresh", bg=ACCENT, fg=BG, relief="flat",
                  bd=0, padx=14, pady=5, font=("Arial", 10, "bold"),
                  command=self._refresh).pack(side="right")
        tk.Label(top, text=LOG_PATH, bg=BG, fg=FG_DIM,
                 font=("Arial", 8)).pack(side="right", padx=6)

        tk.Frame(self.root, bg=BORDER, height=1).pack(fill="x", padx=20, pady=(0, 6))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook",     background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=PANEL, foreground=FG_DIM,
                        padding=[14, 6], font=("Arial", 10))
        style.map("TNotebook.Tab",
                  background=[("selected", BG)],
                  foreground=[("selected", FG)])
        style.configure("Treeview",
                        background=BG, foreground=FG,
                        fieldbackground=BG, rowheight=22, font=("Arial", 9))
        style.configure("Treeview.Heading",
                        background=PANEL, foreground=FG, font=("Arial", 9, "bold"))
        style.map("Treeview",
                  background=[("selected", ACCENT)],
                  foreground=[("selected", BG)])

        nb = ttk.Notebook(self.root)
        nb.pack(fill="both", expand=True, padx=16, pady=4)

        for label, builder in [
            ("Summary",       self._tab_summary),
            ("Stat Trends",   self._tab_stat_trends),
            ("Warnings",      self._tab_warnings),
            ("Decision Time", self._tab_time),
            ("Outcomes",      self._tab_outcomes),
            ("Score Trend",   self._tab_score),
            ("Data Log",      self._tab_data_log),
        ]:
            frame = tk.Frame(nb, bg=BG)
            nb.add(frame, text=label)
            try:
                builder(frame)
            except Exception as e:
                _no_data_label(frame, f"Error building tab: {e}")

    def _tab_summary(self, parent):
        df = self.df
        if df is None:
            _no_data_label(parent, f"No data found.\nExpected: {LOG_PATH}")
            return

        total_turns    = len(df)
        total_sessions = df["session_id"].nunique() if "session_id" in df.columns else 0
        total_warnings = int(df["warning_triggered"].sum()) if "warning_triggered" in df.columns else 0
        avg_time       = round(df["time_per_turn"].mean(), 2) if "time_per_turn" in df.columns else 0
        outcomes       = {}
        if "session_outcome" in df.columns:
            valid    = df[df["session_outcome"] != "PENDING"]
            outcomes = valid["session_outcome"].value_counts().to_dict()

        rows = [
            ("Total Rows Logged",   str(total_turns)),
            ("Sessions",            str(total_sessions)),
            ("Total Warnings",      str(total_warnings)),
            ("Avg Time Per Turn",   f"{avg_time}s"),
            ("Successful Sessions", str(outcomes.get("success", 0))),
            ("Walked Away",         str(outcomes.get("walked_away", 0))),
            ("Game Overs",          str(outcomes.get("game_over", 0))),
        ]
        if "patient_illness" in df.columns:
            rows.append(("Most Seen Illness",
                         df["patient_illness"].mode()[0].replace("_", " ").title()))

        frame = tk.Frame(parent, bg=BG)
        frame.pack(padx=24, pady=20, anchor="w")
        tk.Label(frame, text="Session Overview", bg=BG, fg=FG,
                 font=("Arial", 15, "bold")).grid(row=0, column=0, columnspan=2,
                                                   sticky="w", pady=(0, 14))
        for i, (lbl, val) in enumerate(rows, 1):
            tk.Label(frame, text=lbl, bg=BG, fg=FG_DIM,
                     font=("Arial", 11), width=26, anchor="w").grid(
                         row=i, column=0, sticky="w", pady=4)
            tk.Label(frame, text=val, bg=BG, fg=FG,
                     font=("Arial", 11, "bold"), width=20, anchor="w").grid(
                         row=i, column=1, sticky="w", pady=4)

    def _tab_stat_trends(self, parent):
        df = self.df
        if df is None:
            _no_data_label(parent); return
        if not PANDAS_OK:
            _no_data_label(parent, "Install pandas & matplotlib to see charts."); return

        stat_cols = ["stat_hope", "stat_calm", "stat_trust",
                     "stat_motivation", "stat_exhaustion", "stat_loneliness"]
        available = [c for c in stat_cols if c in df.columns]

        if not available:
            _no_data_label(parent,
                f"Stat columns not found in CSV.\nFound columns: {list(df.columns)[:8]}")
            return

        grays  = ["#111111", "#333333", "#555555", "#777777", "#999999", "#bbbbbb"]
        styles = ["-", "--", "-.", ":", "-", "--"]

        fig, ax = plt.subplots(figsize=(8, 3.6), facecolor=BG)
        fig.patch.set_facecolor(BG)
        _chart_style(ax, "Stat Values Over Turns (session mean)")
        plotted = 0
        for col, g, ls in zip(available, grays, styles):
            mean_per = df.groupby("turn_number")[col].mean().dropna()
            if mean_per.empty:
                continue
            ax.plot(mean_per.index, mean_per.values,
                    label=col.replace("stat_", "").capitalize(),
                    color=g, linewidth=1.8, linestyle=ls)
            plotted += 1
        ax.set_xlabel("Turn"); ax.set_ylabel("Value"); ax.set_ylim(0, 100)
        if plotted > 0:
            ax.legend(fontsize=8, facecolor=PANEL, edgecolor=BORDER,
                      labelcolor=FG, loc="upper right")
        fig.tight_layout()
        self._embed(fig, parent)

    def _tab_warnings(self, parent):
        df = self.df
        if df is None:
            _no_data_label(parent); return
        if not PANDAS_OK:
            _no_data_label(parent, "Install pandas & matplotlib to see charts."); return

        stat_cols   = ["stat_hope", "stat_calm", "stat_trust",
                       "stat_motivation", "stat_exhaustion", "stat_loneliness", "stat_unique"]
        warn_counts = {}
        for col in [c for c in stat_cols if c in df.columns]:
            lbl = col.replace("stat_", "").capitalize()
            warn_counts[lbl] = int(
                (df[col] >= 80).sum() if col in ["stat_exhaustion", "stat_loneliness"]
                else (df[col] <= 20).sum()
            )

        if not warn_counts:
            _no_data_label(parent, f"Stat columns not found.\nFound: {list(df.columns)[:8]}")
            return

        fig, ax = plt.subplots(figsize=(8, 3.6), facecolor=BG)
        fig.patch.set_facecolor(BG)
        _chart_style(ax, "Warning Frequency Per Stat")
        bars = ax.bar(list(warn_counts.keys()), list(warn_counts.values()),
                      color=FG_DIM, edgecolor=FG, linewidth=0.8)
        for bar, val in zip(bars, warn_counts.values()):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                    str(val), ha="center", va="bottom", color=FG, fontsize=9)
        ax.set_xlabel("Stat"); ax.set_ylabel("Count")
        fig.tight_layout()
        self._embed(fig, parent)

    def _tab_time(self, parent):
        df = self.df
        if df is None:
            _no_data_label(parent); return
        if not PANDAS_OK:
            _no_data_label(parent, "Install pandas & matplotlib to see charts."); return
        if "time_per_turn" not in df.columns or "patient_illness" not in df.columns:
            _no_data_label(parent, "No time data yet."); return

        grouped   = df.groupby("patient_illness")["time_per_turn"]
        illnesses = list(grouped.groups.keys())
        data      = [grouped.get_group(ill).dropna().values for ill in illnesses]
        labels    = [ill.replace("_", " ").title() for ill in illnesses]

        fig, ax = plt.subplots(figsize=(8, 3.6), facecolor=BG)
        fig.patch.set_facecolor(BG)
        _chart_style(ax, "Decision Time by Illness (seconds)")
        bp = ax.boxplot(data, labels=labels, patch_artist=True,
                        medianprops=dict(color=FG, linewidth=2))
        for p in bp["boxes"]:    p.set(facecolor=PANEL, edgecolor=FG)
        for w in bp["whiskers"]: w.set_color(FG_DIM)
        for c in bp["caps"]:     c.set_color(FG_DIM)
        for f in bp["fliers"]:   f.set(markerfacecolor=FG_DIM, markersize=4)
        ax.set_ylabel("Seconds")
        ax.tick_params(axis="x", labelrotation=15)
        fig.tight_layout()
        self._embed(fig, parent)

    def _tab_outcomes(self, parent):
        df = self.df
        if df is None:
            _no_data_label(parent); return
        if not PANDAS_OK:
            _no_data_label(parent, "Install pandas & matplotlib to see charts."); return
        if "session_outcome" not in df.columns:
            _no_data_label(parent, "No outcome data yet."); return

        valid = df[df["session_outcome"] != "PENDING"].copy()
        if valid.empty:
            _no_data_label(parent, "No completed sessions yet."); return

        session_rows = valid.groupby("session_id").last().reset_index()
        pivot = session_rows.groupby(
            ["patient_illness", "session_outcome"]).size().unstack(fill_value=0)
        illnesses = [ill.replace("_", " ").title() for ill in pivot.index]
        outcomes  = list(pivot.columns)
        x         = range(len(illnesses))
        bar_w     = 0.25
        gray_map  = {"success": "#333333", "walked_away": "#888888", "game_over": "#cccccc"}
        hatch_map = {"success": "", "walked_away": "//", "game_over": "xx"}

        fig, ax = plt.subplots(figsize=(8, 3.6), facecolor=BG)
        fig.patch.set_facecolor(BG)
        _chart_style(ax, "Session Outcomes by Illness")
        for i, outcome in enumerate(outcomes):
            offset = (i - len(outcomes) / 2) * bar_w + bar_w / 2
            ax.bar([xi + offset for xi in x], pivot[outcome].values,
                   width=bar_w,
                   label=outcome.replace("_", " ").title(),
                   color=gray_map.get(outcome, FG_DIM),
                   hatch=hatch_map.get(outcome, ""),
                   edgecolor=FG, linewidth=0.6)
        ax.set_xticks(list(x))
        ax.set_xticklabels(illnesses, rotation=15, ha="right")
        ax.set_ylabel("Sessions")
        if outcomes:
            ax.legend(fontsize=8, facecolor=PANEL, edgecolor=BORDER, labelcolor=FG)
        fig.tight_layout()
        self._embed(fig, parent)

    def _tab_score(self, parent):
        df = self.df
        if df is None:
            _no_data_label(parent); return
        if not PANDAS_OK:
            _no_data_label(parent, "Install pandas & matplotlib to see charts."); return
        if "session_score" not in df.columns:
            _no_data_label(parent, "No score data yet."); return

        valid = df[df["session_score"] != "PENDING"].copy()
        if valid.empty:
            _no_data_label(parent, "No completed sessions yet."); return

        valid["session_score"] = pd.to_numeric(valid["session_score"], errors="coerce")
        scores = valid.groupby("session_id")["session_score"].last().reset_index()
        scores["run"] = range(1, len(scores) + 1)

        fig, ax = plt.subplots(figsize=(8, 3.6), facecolor=BG)
        fig.patch.set_facecolor(BG)
        _chart_style(ax, "Session Score Over Time")
        ax.plot(scores["run"], scores["session_score"],
                color=FG, linewidth=2, marker="o", markersize=5)
        ax.axhline(0, color=BORDER, linewidth=1, linestyle="--")
        ax.fill_between(scores["run"], scores["session_score"], 0,
                        where=(scores["session_score"] >= 0), alpha=0.12, color=FG)
        ax.fill_between(scores["run"], scores["session_score"], 0,
                        where=(scores["session_score"] < 0), alpha=0.12, color=DANGER)
        ax.set_xlabel("Session"); ax.set_ylabel("Score")
        fig.tight_layout()
        self._embed(fig, parent)

    def _tab_data_log(self, parent):
        df = self.df

        header = tk.Frame(parent, bg=BG)
        header.pack(fill="x", padx=12, pady=(10, 4))

        if df is None:
            tk.Label(header, text="No data yet — play some sessions first.",
                     bg=BG, fg=FG_DIM, font=("Arial", 13)).pack(side="left")
            tk.Label(header, text=f"File: {LOG_PATH}",
                     bg=BG, fg=FG_DIM, font=("Arial", 8)).pack(side="right")
            return

        total = len(df)
        color = SUCCESS if total >= 100 else (DANGER if total == 0 else FG)
        tk.Label(header, text=f"Rows collected: {total}",
                 bg=BG, fg=color, font=("Arial", 14, "bold")).pack(side="left")
        goal_txt = "  ✔ 100+ rows reached!" if total >= 100 else f"  ({100 - total} more to reach 100)"
        tk.Label(header, text=goal_txt,
                 bg=BG, fg=SUCCESS if total >= 100 else FG_DIM,
                 font=("Arial", 10)).pack(side="left")
        tk.Label(header, text=f"  {LOG_PATH}",
                 bg=BG, fg=FG_DIM, font=("Arial", 8)).pack(side="right")

        cols = list(df.columns)
        container = tk.Frame(parent, bg=BG)
        container.pack(fill="both", expand=True, padx=12, pady=(0, 8))

        vsb = ttk.Scrollbar(container, orient="vertical")
        hsb = ttk.Scrollbar(container, orient="horizontal")
        vsb.pack(side="right",  fill="y")
        hsb.pack(side="bottom", fill="x")

        tree = ttk.Treeview(container, columns=cols, show="headings",
                            yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.config(command=tree.yview)
        hsb.config(command=tree.xview)
        tree.pack(fill="both", expand=True)

        widths = {
            "session_id": 70, "turn_number": 50, "patient_name": 100,
            "patient_illness": 90, "patient_occupation": 110,
            "emotional_state": 80, "choice_made": 200,
            "stat_hope": 50, "stat_calm": 50, "stat_trust": 50,
            "stat_motivation": 72, "stat_exhaustion": 72, "stat_loneliness": 72,
            "stat_unique": 60, "stat_unique_name": 80,
            "warning_triggered": 82, "time_per_turn": 80,
            "session_outcome": 90, "session_score": 70,
        }
        for col in cols:
            tree.heading(col, text=col.replace("_", " ").title())
            tree.column(col, width=widths.get(col, 80), minwidth=40, anchor="center")

        tree.tag_configure("warn",   background=WARN_BG, foreground="#7a4800")
        tree.tag_configure("normal", background=BG,      foreground=FG)

        for _, row in df.tail(500).iloc[::-1].reset_index(drop=True).iterrows():
            vals = [str(row[c]) if not (PANDAS_OK and pd.isna(row[c])) else "" for c in cols]
            tag  = "warn" if str(row.get("warning_triggered", "0")) == "1" else "normal"
            tree.insert("", "end", values=vals, tags=(tag,))

        if total > 500:
            tk.Label(parent,
                     text=f"Showing last 500 of {total} rows.",
                     bg=BG, fg=FG_DIM, font=("Arial", 8)).pack(pady=(0, 4))

    def _embed(self, fig, parent):
        fig.patch.set_facecolor(BG)
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=8)
        plt.close(fig)

    def _refresh(self):
        for w in self.root.winfo_children():
            w.destroy()
        self.df = load_data()
        self._build_ui()


def _dashboard_process():
    import tkinter as _tk
    _root = _tk.Tk()
    Dashboard(_root)
    _root.mainloop()


def open_dashboard():
    # Tkinter must run on the main thread of its own process;
    # spawn (not fork) avoids inheriting pygame's SDL state on Windows
    import multiprocessing
    ctx = multiprocessing.get_context("spawn")
    ctx.Process(target=_dashboard_process, daemon=True).start()


if __name__ == "__main__":
    root = tk.Tk()
    Dashboard(root)
    root.mainloop()
