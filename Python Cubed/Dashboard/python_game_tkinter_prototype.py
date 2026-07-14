import tkinter as tk
from tkinter import ttk, filedialog
import pandas as pd


df = None

def load_csv():
    global df

    file_path = filedialog.askopenfilename(
        filetypes=[("CSV Files", "*.csv")]
    )

    if file_path:
        df = pd.read_csv(file_path)
        status_label.config(text=f"Loaded: {file_path.split('/')[-1]}")


def apply_filter():
    print("Filter applied")


def create_chart():
    chart_label.config(text="Chart will appear here")


root = tk.Tk()
root.title("Game Sales Dashboard Prototype")
root.geometry("1000x650")

title = tk.Label(
    root,
    text="Game Sales Dashboard",
    font=("Arial", 20, "bold")
)
title.pack(pady=10)

top_frame = tk.Frame(root)
top_frame.pack(fill="x", padx=10)

load_button = tk.Button(
    top_frame,
    text="Load CSV",
    command=load_csv
)
load_button.pack(side="left", padx=5)

status_label = tk.Label(
    top_frame,
    text="No file loaded"
)
status_label.pack(side="left", padx=10)

filter_frame = tk.LabelFrame(root, text="Filters")
filter_frame.pack(fill="x", padx=10, pady=10)

tk.Label(filter_frame, text="Genre:").pack(side="left", padx=5)

genre_filter = ttk.Combobox(
    filter_frame,
    values=["All", "Action", "Sports", "RPG", "Adventure"]
)
genre_filter.current(0)
genre_filter.pack(side="left", padx=5)

filter_button = tk.Button(
    filter_frame,
    text="Apply Filter",
    command=apply_filter
)
filter_button.pack(side="left", padx=10)

chart_frame = tk.LabelFrame(root, text="Visualization")
chart_frame.pack(fill="both", expand=True, padx=10, pady=10)

chart_label = tk.Label(
    chart_frame,
    text="Chart Placeholder",
    font=("Arial", 16)
)
chart_label.pack(expand=True)

show_chart = tk.Button(
    chart_frame,
    text="Create Chart",
    command=create_chart
)
show_chart.pack(pady=10)

root.mainloop()