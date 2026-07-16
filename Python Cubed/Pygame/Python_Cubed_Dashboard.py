import os
import sys
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


# ============================================================
# APPLICATION SETTINGS
# ============================================================

APP_TITLE = "Python Cubed"
TEAM_NAME = "Kalel, Avery, and Justin"
DEFAULT_CSV = "Cleaned_worldwide_video_games(2).csv"
GAME_MENU_FILE = "menu.py"

BG = "#17130f"
PANEL = "#2b2119"
CARD = "#3b2b20"
GOLD = "#e6c832"
CREAM = "#fff0cd"
MUTED = "#c8ad87"
GREEN = "#5ca66b"
BUTTON = "#80583a"
BUTTON_HOVER = "#ac784e"
BORDER = "#62402c"


class PythonCubedDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_TITLE} - Data Dashboard")
        self.root.geometry("1400x900")
        self.root.minsize(1180, 760)
        self.root.configure(bg=BG)

        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.df = None
        self.canvas = None
        self.active_chart = "Revenue by Genre"

        self.region_var = tk.StringVar(value="All")
        self.genre_var = tk.StringVar(value="All")
        self.publisher_var = tk.StringVar(value="All")

        self.dataset_name_var = tk.StringVar(value="Not loaded")
        self.record_count_var = tk.StringVar(value="--")
        self.status_var = tk.StringVar(value="Waiting for dataset")

        self.kpi_total_games_var = tk.StringVar(value="--")  # Action-market KPI
        self.kpi_market_opportunity_var = tk.StringVar(value="--")
        self.kpi_rating_var = tk.StringVar(value="--")
        self.insight_var = tk.StringVar(value="Load the dataset to view a key insight.")

        self.configure_styles()
        self.create_page_container()
        self.create_welcome_page()
        self.create_dashboard_page()
        self.show_page(self.welcome_page)

        self.root.after(250, self.try_auto_load_csv)

    # ========================================================
    # GENERAL HELPERS
    # ========================================================

    def configure_styles(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "Dark.TCombobox",
            fieldbackground=CREAM,
            background=CREAM,
            foreground="#1e1813",
            arrowcolor="#1e1813",
            padding=5,
        )

    def create_page_container(self):
        self.page_container = tk.Frame(self.root, bg=BG)
        self.page_container.pack(fill="both", expand=True)
        self.page_container.grid_rowconfigure(0, weight=1)
        self.page_container.grid_columnconfigure(0, weight=1)

    def show_page(self, page):
        page.tkraise()

    def make_button(self, parent, text, command, width=None, prominent=False):
        bg = GOLD if prominent else BUTTON
        fg = "#1a140f" if prominent else CREAM
        active_bg = "#f2db56" if prominent else BUTTON_HOVER

        button = tk.Button(
            parent,
            text=text,
            command=command,
            width=width,
            bg=bg,
            fg=fg,
            activebackground=active_bg,
            activeforeground="#1a140f" if prominent else CREAM,
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            bd=0,
            padx=14,
            pady=8,
            cursor="hand2",
        )
        return button

    def make_section(self, parent, title):
        frame = tk.Frame(
            parent,
            bg=PANEL,
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        tk.Label(
            frame,
            text=title,
            bg=PANEL,
            fg=GOLD,
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor="w", padx=14, pady=(10, 4))
        return frame

    # ========================================================
    # WELCOME PAGE - BASED ON PDF PAGE 3
    # ========================================================

    def create_welcome_page(self):
        self.welcome_page = tk.Frame(self.page_container, bg=BG)
        self.welcome_page.grid(row=0, column=0, sticky="nsew")

        center = tk.Frame(self.welcome_page, bg=BG)
        center.place(relx=0.5, rely=0.48, anchor="center")

        tk.Label(
            center,
            text="WELCOME TO",
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 15, "bold"),
        ).pack(pady=(0, 8))

        tk.Label(
            center,
            text="PYTHON CUBED",
            bg=BG,
            fg=GOLD,
            font=("Segoe UI", 42, "bold"),
        ).pack()

        tk.Label(
            center,
            text="Explore how our team transformed worldwide video game market data\n"
                 "into a competitive, multi-level snake fighting game.",
            bg=BG,
            fg=CREAM,
            font=("Segoe UI", 14),
            justify="center",
        ).pack(pady=(16, 32))

        self.make_button(
            center,
            "EXPLORE THE DASHBOARD",
            lambda: self.show_page(self.dashboard_page),
            width=30,
            prominent=True,
        ).pack(pady=8)

        self.make_button(
            center,
            "PLAY PYTHON CUBED",
            self.launch_game,
            width=30,
        ).pack(pady=8)

        self.make_button(
            center,
            "ABOUT OUR TEAM",
            self.show_about,
            width=30,
        ).pack(pady=8)

        tk.Label(
            self.welcome_page,
            text=f"Created by {TEAM_NAME}",
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 10),
        ).pack(side="bottom", pady=20)

    # ========================================================
    # DASHBOARD PAGE - BASED ON PDF PAGE 1
    # ========================================================

    def create_dashboard_page(self):
        self.dashboard_page = tk.Frame(self.page_container, bg=BG)
        self.dashboard_page.grid(row=0, column=0, sticky="nsew")

        # A canvas allows the full dashboard to scroll on smaller screens.
        outer_canvas = tk.Canvas(
            self.dashboard_page,
            bg=BG,
            highlightthickness=0,
        )
        scrollbar = ttk.Scrollbar(
            self.dashboard_page,
            orient="vertical",
            command=outer_canvas.yview,
        )
        outer_canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        outer_canvas.pack(side="left", fill="both", expand=True)

        self.dashboard_content = tk.Frame(outer_canvas, bg=BG)
        canvas_window = outer_canvas.create_window(
            (0, 0),
            window=self.dashboard_content,
            anchor="nw",
        )

        self.dashboard_content.bind(
            "<Configure>",
            lambda event: outer_canvas.configure(
                scrollregion=outer_canvas.bbox("all")
            ),
        )
        outer_canvas.bind(
            "<Configure>",
            lambda event: outer_canvas.itemconfigure(
                canvas_window,
                width=event.width,
            ),
        )
        outer_canvas.bind_all(
            "<MouseWheel>",
            lambda event: outer_canvas.yview_scroll(
                int(-1 * (event.delta / 120)),
                "units",
            ),
        )

        self.create_dashboard_header()
        self.create_dataset_strip()
        self.create_filter_bar()
        self.create_kpi_section()
        self.create_visualization_section()
        self.create_story_section()
        self.create_dashboard_footer()

    def create_dashboard_header(self):
        header = tk.Frame(self.dashboard_content, bg=BG)
        header.pack(fill="x", padx=24, pady=(18, 10))

        left = tk.Frame(header, bg=BG)
        left.pack(side="left", fill="x", expand=True)

        tk.Label(
            left,
            text="PYTHON CUBED",
            bg=BG,
            fg=GOLD,
            font=("Segoe UI", 28, "bold"),
        ).pack(anchor="w")

        tk.Label(
            left,
            text="A data-driven snake fighting game inspired by worldwide video game market research.",
            bg=BG,
            fg=CREAM,
            font=("Segoe UI", 12),
        ).pack(anchor="w", pady=(4, 0))

        self.make_button(header, "? HELP", self.show_help, width=10).pack(
            side="right", padx=(8, 0)
        )
        self.make_button(
            header,
            "HOME",
            lambda: self.show_page(self.welcome_page),
            width=10,
        ).pack(side="right")

    def create_dataset_strip(self):
        strip = tk.Frame(
            self.dashboard_content,
            bg=PANEL,
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        strip.pack(fill="x", padx=24, pady=6)

        items = [
            ("DATASET", self.dataset_name_var),
            ("RECORDS", self.record_count_var),
            ("STATUS", self.status_var),
            ("YOUR TEAM", tk.StringVar(value=TEAM_NAME)),
        ]

        for index, (label, variable) in enumerate(items):
            block = tk.Frame(strip, bg=PANEL)
            block.grid(row=0, column=index, sticky="ew", padx=12, pady=10)
            strip.grid_columnconfigure(index, weight=1)

            tk.Label(
                block,
                text=label,
                bg=PANEL,
                fg=MUTED,
                font=("Segoe UI", 8, "bold"),
            ).pack(anchor="w")
            tk.Label(
                block,
                textvariable=variable,
                bg=PANEL,
                fg=CREAM,
                font=("Segoe UI", 10, "bold"),
            ).pack(anchor="w", pady=(2, 0))

    def create_filter_bar(self):
        frame = tk.Frame(self.dashboard_content, bg=BG)
        frame.pack(fill="x", padx=24, pady=8)

        self.make_button(frame, "LOAD CSV", self.load_csv).pack(side="left", padx=(0, 12))

        tk.Label(frame, text="Region", bg=BG, fg=CREAM).pack(side="left")
        self.region_combo = ttk.Combobox(
            frame,
            textvariable=self.region_var,
            state="readonly",
            width=15,
            style="Dark.TCombobox",
        )
        self.region_combo.pack(side="left", padx=(5, 12))

        tk.Label(frame, text="Genre", bg=BG, fg=CREAM).pack(side="left")
        self.genre_combo = ttk.Combobox(
            frame,
            textvariable=self.genre_var,
            state="readonly",
            width=15,
            style="Dark.TCombobox",
        )
        self.genre_combo.pack(side="left", padx=(5, 12))

        tk.Label(frame, text="Publisher", bg=BG, fg=CREAM).pack(side="left")
        self.publisher_combo = ttk.Combobox(
            frame,
            textvariable=self.publisher_var,
            state="readonly",
            width=22,
            style="Dark.TCombobox",
        )
        self.publisher_combo.pack(side="left", padx=(5, 12))

        self.make_button(
            frame,
            "APPLY FILTERS",
            self.update_dashboard,
            prominent=True,
        ).pack(side="left", padx=4)

        self.make_button(frame, "RESET", self.reset_dashboard).pack(side="left", padx=4)

    # ========================================================
    # EXACTLY THREE KPI CARDS
    # ========================================================

    def create_kpi_section(self):
        container = tk.Frame(self.dashboard_content, bg=BG)
        container.pack(fill="x", padx=19, pady=8)

        cards = [
            (
                "ACTION MARKET STRENGTH",
                self.kpi_total_games_var,
                "Action's revenue rank and total support choosing a fast, competitive fighting-game format.",
            ),
            (
                "LATIN AMERICA OPPORTUNITY",
                self.kpi_market_opportunity_var,
                "Latin America is the CSV's closest regional proxy for a South American launch market.",
            ),
            (
                "TOP USER RATING",
                self.kpi_rating_var,
                "The strongest rating in the data supports emphasizing polish, depth, and replayability.",
            ),
        ]

        for column, (title, variable, explanation) in enumerate(cards):
            card = tk.Frame(
                container,
                bg=CARD,
                highlightbackground=BORDER,
                highlightthickness=1,
                height=155,
            )
            card.grid(row=0, column=column, sticky="nsew", padx=5)
            card.grid_propagate(False)
            container.grid_columnconfigure(column, weight=1)

            tk.Label(
                card,
                text=title,
                bg=CARD,
                fg=MUTED,
                font=("Segoe UI", 10, "bold"),
            ).pack(pady=(18, 6))
            tk.Label(
                card,
                textvariable=variable,
                bg=CARD,
                fg=GOLD,
                font=("Segoe UI", 24, "bold"),
                wraplength=320,
            ).pack()
            tk.Label(
                card,
                text=explanation,
                bg=CARD,
                fg=CREAM,
                font=("Segoe UI", 9),
                wraplength=330,
                justify="center",
            ).pack(padx=12, pady=(7, 12))

    # ========================================================
    # EXACTLY THREE SELECTABLE VISUALIZATIONS
    # ========================================================

    def create_visualization_section(self):
        section = self.make_section(
            self.dashboard_content,
            "EXPLORE THE DATA - 3 VISUALIZATIONS",
        )
        section.pack(fill="both", expand=True, padx=24, pady=8)

        controls = tk.Frame(section, bg=PANEL)
        controls.pack(fill="x", padx=12, pady=(4, 8))

        chart_names = [
            "Revenue by Genre",
            "Regional Opportunity",
            "Revenue vs Rating",
        ]

        for name in chart_names:
            self.make_button(
                controls,
                name.upper(),
                lambda selected=name: self.select_chart(selected),
            ).pack(side="left", padx=(0, 8))

        self.chart_frame = tk.Frame(
            section,
            bg=CREAM,
            height=440,
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        self.chart_frame.pack(fill="both", expand=True, padx=12, pady=(0, 8))
        self.chart_frame.pack_propagate(False)

        insight_frame = tk.Frame(section, bg=CARD)
        insight_frame.pack(fill="x", padx=12, pady=(0, 12))
        tk.Label(
            insight_frame,
            text="KEY INSIGHT:",
            bg=CARD,
            fg=GOLD,
            font=("Segoe UI", 10, "bold"),
        ).pack(side="left", padx=(12, 6), pady=10)
        tk.Label(
            insight_frame,
            textvariable=self.insight_var,
            bg=CARD,
            fg=CREAM,
            font=("Segoe UI", 10),
            wraplength=1050,
            justify="left",
        ).pack(side="left", fill="x", expand=True, padx=(0, 12), pady=10)

    def create_story_section(self):
        wrapper = tk.Frame(self.dashboard_content, bg=BG)
        wrapper.pack(fill="x", padx=19, pady=8)
        wrapper.grid_columnconfigure(0, weight=1)
        wrapper.grid_columnconfigure(1, weight=1)

        findings = self.make_section(wrapper, "WHAT OUR TEAM DISCOVERED")
        findings.grid(row=0, column=0, sticky="nsew", padx=5)

        self.findings_label = tk.Label(
            findings,
            text=(
                "1. Load the dataset to calculate the first finding.\n\n"
                "2. The second finding will compare game audiences.\n\n"
                "3. The third finding will summarize ratings and revenue."
            ),
            bg=PANEL,
            fg=CREAM,
            font=("Segoe UI", 10),
            justify="left",
            anchor="nw",
            wraplength=560,
        )
        self.findings_label.pack(fill="both", expand=True, padx=14, pady=(5, 16))

        game_story = self.make_section(wrapper, "HOW DATA SHAPED PYTHON CUBED")
        game_story.grid(row=0, column=1, sticky="nsew", padx=5)

        tk.Label(
            game_story,
            text=(
                "DATA FINDING\n"
                "Action is one of the dataset's two highest-revenue genres, while highly rated games reach 9.8/10.\n\n"
                "↓\n\n"
                "DESIGN DECISION\n"
                "Build a polished, competitive, Street Fighter-style action game with a memorable Python theme.\n\n"
                "↓\n\n"
                "GAME FEATURE\n"
                "One-on-one snake combat, light and heavy attacks, blocking, dodging, special moves, multiplayer, "
                "and six progressively harder CPU levels. Latin America's strong per-title performance also supports "
                "testing a localized South American release."
            ),
            bg=PANEL,
            fg=CREAM,
            font=("Segoe UI", 10),
            justify="center",
            wraplength=560,
        ).pack(fill="both", expand=True, padx=14, pady=(5, 16))

    def create_dashboard_footer(self):
        section = tk.Frame(self.dashboard_content, bg=BG)
        section.pack(fill="x", padx=24, pady=(10, 24))

        tk.Label(
            section,
            text="READY TO EXPERIENCE OUR DATA-DRIVEN GAME?",
            bg=BG,
            fg=GOLD,
            font=("Segoe UI", 13, "bold"),
        ).pack(pady=(0, 10))

        buttons = tk.Frame(section, bg=BG)
        buttons.pack()

        self.make_button(
            buttons,
            "▶ PLAY THE GAME",
            self.launch_game,
            prominent=True,
        ).pack(side="left", padx=5)
        self.make_button(buttons, "VIEW INSTRUCTIONS", self.show_help).pack(side="left", padx=5)
        self.make_button(buttons, "ABOUT OUR TEAM", self.show_about).pack(side="left", padx=5)
        self.make_button(
            buttons,
            "HOME",
            lambda: self.show_page(self.welcome_page),
        ).pack(side="left", padx=5)
        self.make_button(buttons, "EXIT", self.root.destroy).pack(side="left", padx=5)

    # ========================================================
    # DATA LOADING AND FILTERING
    # ========================================================

    def try_auto_load_csv(self):
        default_path = os.path.join(self.base_dir, DEFAULT_CSV)
        if os.path.exists(default_path):
            self.read_csv(default_path)

    def load_csv(self):
        file_path = filedialog.askopenfilename(
            title="Choose the cleaned video game dataset",
            initialdir=self.base_dir,
            filetypes=[("CSV Files", "*.csv")],
        )
        if file_path:
            self.read_csv(file_path)

    def read_csv(self, file_path):
        required_columns = {
            "Game_Title",
            "Publisher",
            "Genre",
            "Region",
            "Avg_User_Rating",
            "Units_Sold_Millions",
            "Revenue_M_USD",
        }

        try:
            new_df = pd.read_csv(file_path)
            missing = required_columns.difference(new_df.columns)
            if missing:
                raise ValueError(
                    "Missing required columns: " + ", ".join(sorted(missing))
                )

            numeric_columns = [
                "Avg_User_Rating",
                "Units_Sold_Millions",
                "Revenue_M_USD",
            ]
            for column in numeric_columns:
                new_df[column] = pd.to_numeric(new_df[column], errors="coerce")

            self.df = new_df
            self.dataset_name_var.set(os.path.basename(file_path))
            self.record_count_var.set(f"{len(self.df):,}")
            self.status_var.set("CLEANED / LOADED")

            self.populate_filter_values()
            self.update_dashboard()
        except (OSError, pd.errors.ParserError, ValueError) as error:
            messagebox.showerror("Dataset Error", str(error))
            self.status_var.set("LOAD FAILED")

    def populate_filter_values(self):
        self.region_combo["values"] = ["All"] + sorted(
            self.df["Region"].dropna().astype(str).unique().tolist()
        )
        self.genre_combo["values"] = ["All"] + sorted(
            self.df["Genre"].dropna().astype(str).unique().tolist()
        )
        self.publisher_combo["values"] = ["All"] + sorted(
            self.df["Publisher"].dropna().astype(str).unique().tolist()
        )

        self.region_var.set("All")
        self.genre_var.set("All")
        self.publisher_var.set("All")

    def get_filtered_data(self):
        if self.df is None:
            return None

        filtered = self.df.copy()

        if self.region_var.get() != "All":
            filtered = filtered[filtered["Region"] == self.region_var.get()]
        if self.genre_var.get() != "All":
            filtered = filtered[filtered["Genre"] == self.genre_var.get()]
        if self.publisher_var.get() != "All":
            filtered = filtered[filtered["Publisher"] == self.publisher_var.get()]

        return filtered

    def reset_dashboard(self):
        self.region_var.set("All")
        self.genre_var.set("All")
        self.publisher_var.set("All")
        self.active_chart = "Revenue by Genre"
        self.update_dashboard()

    # ========================================================
    # KPI, FINDING, AND VISUALIZATION UPDATES
    # ========================================================

    def update_dashboard(self):
        data = self.get_filtered_data()
        if data is None:
            messagebox.showinfo("Dataset Needed", "Load the CSV dataset first.")
            return

        if data.empty:
            self.kpi_total_games_var.set("0")
            self.kpi_market_opportunity_var.set("No data")
            self.kpi_rating_var.set("--")
            self.insight_var.set("No rows match the selected filters.")
            self.findings_label.config(text="No findings are available for the current filters.")
            self.clear_chart("No data matches the selected filters.")
            return

        self.record_count_var.set(f"{len(data):,} filtered")
        self.update_kpis(data)
        self.update_findings(data)
        self.create_chart(data)

    def update_kpis(self, data):
        revenue_by_genre = (
            data.groupby("Genre")["Revenue_M_USD"]
            .sum()
            .sort_values(ascending=False)
        )

        # KPI 1: Action-market strength. We report its real rank rather than
        # claiming it is first when another genre leads the current selection.
        if "Action" in revenue_by_genre.index:
            action_revenue = revenue_by_genre.loc["Action"]
            action_rank = revenue_by_genre.index.tolist().index("Action") + 1
            self.kpi_total_games_var.set(
                f"#{action_rank} genre\n${action_revenue:,.1f}M"
            )
        else:
            self.kpi_total_games_var.set("No Action data")

        # KPI 2: Latin America is the dataset's closest available proxy for
        # South America. This measures revenue opportunity, not accounting profit.
        latin_america = data[data["Region"] == "Latin America"]
        overall_revenue_per_title = data["Revenue_M_USD"].mean()
        latin_revenue_per_title = latin_america["Revenue_M_USD"].mean()

        if latin_america.empty or not pd.notna(latin_revenue_per_title):
            self.kpi_market_opportunity_var.set("No Latin America data")
        else:
            lift = (
                (latin_revenue_per_title / overall_revenue_per_title - 1) * 100
                if overall_revenue_per_title else 0
            )
            self.kpi_market_opportunity_var.set(
                f"${latin_revenue_per_title:,.1f}M/title\n({lift:+.1f}% vs avg)"
            )

        # KPI 3: the CSV uses a 10-point rating scale (values reach 9.8).
        top_rating = data["Avg_User_Rating"].max()
        self.kpi_rating_var.set(
            f"{top_rating:.1f} / 10" if pd.notna(top_rating) else "--"
        )

    def update_findings(self, data):
        revenue_by_genre = (
            data.groupby("Genre")["Revenue_M_USD"]
            .sum()
            .sort_values(ascending=False)
        )

        top_genre = revenue_by_genre.index[0]
        top_revenue = revenue_by_genre.iloc[0]
        if "Action" in revenue_by_genre.index:
            action_revenue = revenue_by_genre.loc["Action"]
            action_rank = revenue_by_genre.index.tolist().index("Action") + 1
            action_text = (
                f"Action ranks #{action_rank} of {len(revenue_by_genre)} genres with "
                f"${action_revenue:,.1f}M in revenue. Together with {top_genre}'s "
                f"${top_revenue:,.1f}M lead, the data shows strong demand for competitive, "
                f"high-energy play—supporting our Street Fighter-style format."
            )
        else:
            action_text = "No Action records remain under the selected filters."

        latin_america = data[data["Region"] == "Latin America"]
        overall_avg_revenue = data["Revenue_M_USD"].mean()
        latin_avg_revenue = latin_america["Revenue_M_USD"].mean()
        latin_avg_units = latin_america["Units_Sold_Millions"].mean()
        region_share = len(latin_america) / len(data) * 100 if len(data) else 0

        if latin_america.empty:
            opportunity_text = "No Latin America records remain under the selected filters."
        else:
            lift = ((latin_avg_revenue / overall_avg_revenue) - 1) * 100 if overall_avg_revenue else 0
            opportunity_text = (
                f"Latin America represents only {region_share:.1f}% of records but averages "
                f"${latin_avg_revenue:,.1f}M revenue and {latin_avg_units:.2f}M units per title "
                f"({lift:+.1f}% revenue per title versus average). This supports testing a "
                f"localized South American release, though costs are needed to prove profit."
            )

        top_rating = data["Avg_User_Rating"].max()
        high_rated = data[data["Avg_User_Rating"] >= 8.0]
        high_rated_share = len(high_rated) / len(data) * 100 if len(data) else 0
        rating_text = (
            f"The highest user rating is {top_rating:.1f}/10, and {high_rated_share:.1f}% of selected titles "
            f"score at least 8.0. That encouraged polished mechanics and replay value: blocking, dodging, "
            f"special attacks, multiplayer, and six CPU levels."
        )

        self.findings_label.config(
            text=(
                f"1. {action_text}\n\n"
                f"2. {rating_text}\n\n"
                f"3. {opportunity_text}"
            )
        )

    def select_chart(self, chart_name):
        self.active_chart = chart_name
        self.update_dashboard()

    def clear_chart(self, message):
        if self.canvas is not None:
            self.canvas.get_tk_widget().destroy()
            self.canvas = None

        for widget in self.chart_frame.winfo_children():
            widget.destroy()

        tk.Label(
            self.chart_frame,
            text=message,
            bg=CREAM,
            fg="#1e1813",
            font=("Segoe UI", 16, "bold"),
        ).pack(expand=True)

    def create_chart(self, data):
        if self.canvas is not None:
            self.canvas.get_tk_widget().destroy()
            self.canvas = None

        plt.close("all")
        fig, ax = plt.subplots(figsize=(11, 4.6), dpi=100)
        fig.patch.set_facecolor(CREAM)
        ax.set_facecolor(CREAM)

        if self.active_chart == "Revenue by Genre":
            graph = (
                data.groupby("Genre")["Revenue_M_USD"]
                .sum()
                .sort_values(ascending=False)
            )
            graph.plot(kind="bar", ax=ax, color="#80583a")
            ax.set_title("Total Revenue by Genre", fontsize=15, fontweight="bold")
            ax.set_xlabel("Genre")
            ax.set_ylabel("Revenue (Millions USD)")
            ax.tick_params(axis="x", rotation=35)

            top_genre = graph.index[0]
            top_value = graph.iloc[0]
            if "Action" in graph.index:
                action_value = graph.loc["Action"]
                action_rank = graph.index.tolist().index("Action") + 1
                self.insight_var.set(
                    f"{top_genre} leads at ${top_value:,.1f}M, while Action ranks #{action_rank} "
                    f"at ${action_value:,.1f}M. Action's top-tier performance supports choosing "
                    f"a fast, competitive Street Fighter-style game."
                )
            else:
                self.insight_var.set(
                    f"{top_genre} produces the highest total revenue in the current selection "
                    f"at ${top_value:,.1f} million; no Action records remain under these filters."
                )

        elif self.active_chart == "Regional Opportunity":
            regional = (
                data.groupby("Region")
                .agg(
                    average_revenue_per_title=("Revenue_M_USD", "mean"),
                    records=("Game_Title", "size"),
                    average_units_per_title=("Units_Sold_Millions", "mean"),
                )
                .sort_values("average_revenue_per_title", ascending=False)
            )

            colors = [
                GOLD if region == "Latin America" else BUTTON
                for region in regional.index
            ]
            regional["average_revenue_per_title"].plot(
                kind="bar", ax=ax, color=colors
            )
            ax.set_title(
                "Regional Market Opportunity: Average Revenue per Title",
                fontsize=15,
                fontweight="bold",
            )
            ax.set_xlabel("Region (Latin America is used as the South America proxy)")
            ax.set_ylabel("Average Revenue per Title (Millions USD)")
            ax.tick_params(axis="x", rotation=30)

            if "Latin America" in regional.index:
                latin = regional.loc["Latin America"]
                overall = data["Revenue_M_USD"].mean()
                lift = ((latin["average_revenue_per_title"] / overall) - 1) * 100 if overall else 0
                share = latin["records"] / len(data) * 100 if len(data) else 0
                self.insight_var.set(
                    f"Latin America accounts for only {share:.1f}% of the selected records but averages "
                    f"${latin['average_revenue_per_title']:,.1f}M revenue per title ({lift:+.1f}% versus "
                    f"the dataset average) and {latin['average_units_per_title']:.2f}M units per title. "
                    f"That combination suggests an underrepresented South American market opportunity; "
                    f"profit cannot be confirmed without cost data."
                )
            else:
                self.insight_var.set(
                    "No Latin America records remain under the selected filters, so the South America proxy cannot be evaluated."
                )

        else:
            clean = data[["Avg_User_Rating", "Revenue_M_USD"]].dropna()
            ax.scatter(
                clean["Avg_User_Rating"],
                clean["Revenue_M_USD"],
                color="#5ca66b",
                edgecolors="#2b2119",
                alpha=0.75,
            )
            ax.set_title("Revenue Compared with Average User Rating", fontsize=15, fontweight="bold")
            ax.set_xlabel("Average User Rating")
            ax.set_ylabel("Revenue (Millions USD)")
            ax.grid(alpha=0.25)

            correlation = clean["Avg_User_Rating"].corr(clean["Revenue_M_USD"])
            if pd.isna(correlation):
                self.insight_var.set("There is not enough data to calculate the relationship.")
            elif correlation >= 0.25:
                self.insight_var.set(
                    f"Ratings and revenue show a positive relationship (correlation {correlation:.2f}). "
                    f"This supports investing in polished controls, defensive options, special moves, and replayability."
                )
            elif correlation <= -0.25:
                self.insight_var.set(
                    f"Ratings and revenue show a negative relationship here (correlation {correlation:.2f}), "
                    f"so our design case rests on Action's market strength—not a claim that ratings guarantee revenue."
                )
            else:
                self.insight_var.set(
                    f"Ratings and revenue have a weak relationship (correlation {correlation:.2f}). "
                    f"We therefore use the 9.8/10 ceiling as a quality benchmark, not proof that ratings cause sales."
                )

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        fig.tight_layout()

        self.canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    # ========================================================
    # GAME, HELP, AND ABOUT WINDOWS
    # ========================================================

    def launch_game(self):
        menu_path = os.path.join(self.base_dir, GAME_MENU_FILE)
        if not os.path.exists(menu_path):
            messagebox.showerror(
                "Game File Missing",
                f"Place {GAME_MENU_FILE} in the same folder as this dashboard.",
            )
            return

        try:
            subprocess.Popen(
                [sys.executable, menu_path],
                cwd=self.base_dir,
            )
        except OSError as error:
            messagebox.showerror("Could Not Start Game", str(error))

    def show_help(self):
        help_window = tk.Toplevel(self.root)
        help_window.title("Python Cubed Instructions")
        help_window.geometry("690x600")
        help_window.configure(bg=BG)
        help_window.transient(self.root)

        tk.Label(
            help_window,
            text="PYTHON CUBED INSTRUCTIONS",
            bg=BG,
            fg=GOLD,
            font=("Segoe UI", 20, "bold"),
        ).pack(pady=(20, 10))

        instructions = (
            "DASHBOARD\n"
            "• Use Region, Genre, and Publisher to filter the CSV data.\n"
            "• Select one of the three chart buttons to change the visualization.\n"
            "• Reset returns all filters and charts to their defaults.\n\n"
            "PLAYER 1 CONTROLS\n"
            "Move: A / D     Jump: W     Crouch: S\n"
            "Punch: Q       Heavy: E    Special: R\n"
            "Block: F       Dodge: Left Shift\n\n"
            "PLAYER 2 CONTROLS\n"
            "Move: J / L     Jump: I     Crouch: K\n"
            "Punch: U       Heavy: O    Special: P\n"
            "Block: ;       Dodge: Right Shift\n\n"
            "GAMEPLAY\n"
            "Beat CPU levels to unlock harder opponents. Attacks have visible windups. "
            "Block, crouch, or dodge at the right time, and fill the meter to use a special attack."
        )

        tk.Label(
            help_window,
            text=instructions,
            bg=PANEL,
            fg=CREAM,
            font=("Segoe UI", 11),
            justify="left",
            wraplength=620,
            padx=20,
            pady=20,
        ).pack(fill="both", expand=True, padx=20, pady=10)

        self.make_button(help_window, "CLOSE", help_window.destroy).pack(pady=(0, 20))

    def show_about(self):
        about_window = tk.Toplevel(self.root)
        about_window.title("About the Python Cubed Team")
        about_window.geometry("720x640")
        about_window.configure(bg=BG)
        about_window.transient(self.root)

        tk.Label(
            about_window,
            text="ABOUT PYTHON CUBED",
            bg=BG,
            fg=GOLD,
            font=("Segoe UI", 22, "bold"),
        ).pack(pady=(20, 10))

        about_text = (
            "PROJECT GOAL\n"
            "Analyze worldwide video game market data and use the findings to design an "
            "interactive fighting game with clear competition, progression, and replay value.\n\n"
            f"The Python Cubed Team:\n"
            "Avery - Project Manager & Dashboard Creator\nKalel - Game Designer & Trello Overseer\nJustin - Sprite Artist & Tester\n\n"
            "TOOLS\n"
            "Python, pandas, Matplotlib, Tkinter, Pygame, CSV, JSON, and Trello.\n\n"
            "SKILLS\n"
            "Data cleaning, visualization, GUI design, game development, CSV storage, "
            "Agile workflow, testing, debugging, and collaboration.\n\n"
            "COMPLETE DATA FEEDBACK LOOP\n"
            "Existing Dataset → Clean Data → 3 KPIs → 3 Visualizations → 3 Findings → "
            "Game Design → Visitor Plays → Player Results Saved → New Data Available for Analysis"
        )

        tk.Label(
            about_window,
            text=about_text,
            bg=PANEL,
            fg=CREAM,
            font=("Segoe UI", 11),
            justify="left",
            anchor="nw",
            wraplength=650,
            padx=20,
            pady=20,
        ).pack(fill="both", expand=True, padx=20, pady=10)

        self.make_button(about_window, "CLOSE", about_window.destroy).pack(pady=(0, 20))


def main():
    root = tk.Tk()
    PythonCubedDashboard(root)
    root.mainloop()


if __name__ == "__main__":
    main()
