import tkinter as tk
from tkinter import ttk


# ----------------------------
# Functions (Empty Placeholders)
# ----------------------------
def load_csv():
    pass


def apply_filter():
    pass


def show_chart():
    pass


# ----------------------------
# Main Window
# ----------------------------
root = tk.Tk()
root.title("Video Game Sales Dashboard")
root.geometry("900x600")


# ----------------------------
# Title
# ----------------------------
title_label = tk.Label(
    root,
    text="Video Game Sales Dashboard",
    font=("Arial", 18, "bold")
)
title_label.pack(pady=10)


# ----------------------------
# Top Controls
# ----------------------------
top_frame = tk.Frame(root)
top_frame.pack(pady=10)

load_button = tk.Button(
    top_frame,
    text="Load CSV",
    command=load_csv
)
load_button.grid(row=0, column=0, padx=5)

tk.Label(top_frame, text="Genre").grid(row=0, column=1, padx=5)

genre_filter = ttk.Combobox(
    top_frame,
    values=["Action", "Adventure", "Sports", "Racing"]
)
genre_filter.grid(row=0, column=2, padx=5)

filter_button = tk.Button(
    top_frame,
    text="Apply Filter",
    command=apply_filter
)
filter_button.grid(row=0, column=3, padx=5)


# ----------------------------
# KPI Placeholder
# ----------------------------
kpi_frame = tk.Frame(root)
kpi_frame.pack(pady=15)

tk.Label(kpi_frame, text="Total Sales: ______").pack()
tk.Label(kpi_frame, text="Top Genre: ______").pack()
tk.Label(kpi_frame, text="Top Region: ______").pack()


# ----------------------------
# Chart Placeholder
# ----------------------------
chart_frame = tk.Frame(
    root,
    width=600,
    height=300,
    bg="lightgray"
)
chart_frame.pack(pady=20)

chart_frame.pack_propagate(False)

chart_label = tk.Label(
    chart_frame,
    text="Chart Will Be Displayed Here",
    bg="lightgray",
    font=("Arial", 14)
)
chart_label.pack(expand=True)


# ----------------------------
# Run Program
# ----------------------------
root.mainloop()
