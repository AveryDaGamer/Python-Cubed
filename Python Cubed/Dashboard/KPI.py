import tkinter as tk
from tkinter import ttk
import pandas as pd

df = pd.read_csv("Cleaned_worldwide_video_games.csv")

numeric_columns = [
    "Revenue_M_USD",
    "Avg_User_Rating",
    "Units_Sold_Millions",
    "Price_USD",
    "Monthly_Active_Users"
]

for col in numeric_columns:
    df[col] = pd.to_numeric(df[col], errors="coerce")


root = tk.Tk()

root.title("Worldwide Video Game Dashboard")
root.geometry("1000x600")
root.configure(bg="#f2f2f2")

kpi_frame = tk.Frame(root, bg="#f2f2f2")
kpi_frame.pack(pady=20)

card = tk.Frame(
    kpi_frame,
    bg="white",
    width=180,
    height=100,
    relief="raised",
    bd=2
)

card.grid(row=0, column=0, padx=15)
card.grid_propagate(False)


total_games = len(df)

value = tk.Label(
    card,
    text=str(total_games),
    font=("Arial", 22),
    bg="white",
    fg="blue"
)

value.pack()

def create_card(parent, title, value, row, column):

    card = tk.Frame(
        parent,
        bg="white",
        width=180,
        height=100,
        relief="raised",
        bd=2
    )

    card.grid(row=row, column=column, padx=15, pady=10)
    card.grid_propagate(False)

    tk.Label(
        card,
        text=title,
        font=("Arial", 12, "bold"),
        bg="white"
    ).pack(pady=(15,5))

    tk.Label(
        card,
        text=value,
        font=("Arial",20),
        bg="white",
        fg="blue"
    ).pack()

total_games = len(df)
total_revenue = df["Revenue_M_USD"].sum()
average_rating = df["Avg_User_Rating"].mean()
units_sold = df["Units_Sold_Millions"].sum()
average_price = df["Price_USD"].mean()
average_users = df["Monthly_Active_Users"].mean()


create_card(kpi_frame, "Total Games", total_games, 0, 0)
create_card(kpi_frame, "Revenue", f"${total_revenue:.1f} M", 0, 1)
create_card(kpi_frame, "Avg Rating", f"{average_rating:.2f}", 0, 2)

create_card(kpi_frame, "Units Sold", f"{units_sold:.1f} M", 1, 0)
create_card(kpi_frame, "Avg Price", f"${average_price:.2f}", 1, 1)
create_card(kpi_frame, "Monthly Users", f"{average_users:,.0f}", 1, 2)

root.mainloop()
