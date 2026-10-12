import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
from threading import Thread
from queue import Queue, Empty
import urllib.request
import urllib.error
import json
import csv
import os

API_URL = "https://open.er-api.com/v6/latest/{}"

# Store database and CSV in the same folder as this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) if "__file__" in locals() else os.getcwd()
DB_NAME = os.path.join(BASE_DIR, "currency_history.db")
CSV_NAME = os.path.join(BASE_DIR, "conversion_history.csv")

CURRENCIES = [
    "USD", "INR", "EUR", "GBP", "JPY", "AUD", "CAD",
    "CHF", "CNY", "SGD", "NZD", "AED", "SAR", "ZAR",
    "BDT", "PKR", "NPR", "LKR", "THB", "MYR", "KRW"
]

BG = "#101820"
PANEL = "#1C2B36"
ACCENT = "#00C9A7"
TEXT = "#F2F5F7"
MUTED = "#AAB7C4"

result_queue = Queue()

def setup_database():
    with sqlite3.connect(DB_NAME) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                amount REAL,
                source TEXT,
                target TEXT,
                rate REAL,
                result REAL
            )
        """)

def save_history(amount, source, target, rate, result):
    with sqlite3.connect(DB_NAME) as con:
        con.execute("""
            INSERT INTO history
            (date, amount, source, target, rate, result)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            amount, source, target, rate, result
        ))

def export_history_to_csv():
    """Exports all database history to an Excel-compatible CSV file."""
    try:
        with sqlite3.connect(DB_NAME) as con:
            rows = con.execute("""
                SELECT date, amount, source, target, rate, result
                FROM history ORDER BY id DESC
            """).fetchall()

        # utf-8-sig ensures Excel on Windows reads UTF-8 characters and columns cleanly
        with open(CSV_NAME, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Date & Time",
                "Amount",
                "From Currency",
                "To Currency",
                "Exchange Rate",
                "Converted Amount"
            ])
            for row in rows:
                date, amount, source, target, rate, result = row
                writer.writerow([
                    date,
                    f"{amount:.2f}",
                    source,
                    target,
                    f"{rate:.6f}",
                    f"{result:.2f}"
                ])
        return True, ""
    except PermissionError:
        return False, "The Excel file is currently open. Please close it in Excel first to save updates."
    except Exception as e:
        return False, str(e)

def open_in_excel():
    """Syncs the latest data and opens the CSV file directly in Microsoft Excel."""
    success, err = export_history_to_csv()
    if not success and not os.path.exists(CSV_NAME):
        messagebox.showerror("Export Error", err)
        return

    if not os.path.exists(CSV_NAME):
        messagebox.showinfo("No History", "No conversion history recorded yet.")
        return

    try:
        # Opens the file in the default Windows app (Microsoft Excel)
        os.startfile(CSV_NAME)
    except Exception as e:
        messagebox.showerror("Error Opening File", f"Could not launch Excel: {e}")

def get_rates(source):
    url = API_URL.format(source)
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "CurrencyConverterApp/1.0"}
    )
    with urllib.request.urlopen(req, timeout=10) as response:
        data = json.loads(response.read().decode("utf-8"))

    if data.get("result") != "success":
        raise ValueError(
            data.get("error-type", "API request failed")
        )

    rates = data.get("rates") or data.get("conversion_rates")
    if not rates:
        raise ValueError("Exchange rates not found in response.")

    return rates, data.get("time_last_update_utc", "Not provided")

def start_conversion():
    try:
        amount = float(amount_entry.get().strip())
        source = source_box.get()
        target = target_box.get()

        if not source or not target:
            raise ValueError("Please select both currencies.")

        if amount <= 0:
            raise ValueError("Amount must be greater than zero.")

        convert_button.config(state="disabled")
        status_label.config(text="Fetching exchange rates...")

        Thread(
            target=conversion_worker,
            args=(amount, source, target),
            daemon=True
        ).start()

    except ValueError as error:
        messagebox.showerror("Invalid Input", str(error))

def conversion_worker(amount, source, target):
    try:
        rates, updated = get_rates(source)

        if target not in rates:
            raise ValueError(f"Target currency '{target}' is not supported.")

        rate = rates[target]
        result = amount * rate

        save_history(amount, source, target, rate, result)

        result_queue.put((
            "success", amount, source, target,
            rate, result, updated
        ))

    except Exception as error:
        result_queue.put(("error", str(error)))

def check_queue():
    try:
        while True:
            item = result_queue.get_nowait()

            if item[0] == "success":
                _, amount, source, target, rate, result, updated = item

                result_label.config(
                    text=f"{amount:,.2f} {source}\n"
                         f"= {result:,.2f} {target}"
                )
                status_label.config(
                    text=f"Rate: 1 {source} = {rate:.6f} {target}\n"
                         f"Rates updated: {updated}"
                )
                load_history()

            else:
                status_label.config(text="Conversion failed.")
                messagebox.showerror("Conversion Error", item[1])

            convert_button.config(state="normal")

    except Empty:
        pass

    root.after(150, check_queue)

def load_history():
    for item in history_table.get_children():
        history_table.delete(item)

    with sqlite3.connect(DB_NAME) as con:
        rows = con.execute("""
            SELECT date, amount, source, target, rate, result
            FROM history ORDER BY id DESC LIMIT 100
        """).fetchall()

    for row in rows:
        date, amount, source, target, rate, result = row
        history_table.insert("", "end", values=(
            date, f"{amount:.2f}", source, target,
            f"{rate:.6f}", f"{result:.2f}"
        ))

    # Keep the Excel CSV updated with the latest conversions
    export_history_to_csv()

def clear_history():
    if messagebox.askyesno(
        "Confirm", "Delete all conversion history?"
    ):
        with sqlite3.connect(DB_NAME) as con:
            con.execute("DELETE FROM history")
        load_history()
        result_label.config(text="History cleared")
        status_label.config(text="Ready")

def swap_currencies():
    source = source_box.get()
    target = target_box.get()
    source_box.set(target)
    target_box.set(source)

# Initialize database
setup_database()

root = tk.Tk()
root.title("Currency Converter Pro")
root.geometry("940x740")
root.minsize(760, 620)
root.configure(bg=BG)

style = ttk.Style()
style.theme_use("clam")
style.configure(
    "TCombobox",
    fieldbackground=PANEL,
    background=PANEL,
    foreground=TEXT
)
style.configure(
    "Treeview",
    background=PANEL,
    foreground=TEXT,
    fieldbackground=PANEL,
    rowheight=28
)
style.configure(
    "Treeview.Heading",
    background=ACCENT,
    foreground=BG,
    font=("Arial", 9, "bold")
)

tk.Label(
    root, text="CURRENCY CONVERTER",
    font=("Arial", 22, "bold"),
    bg=BG, fg=ACCENT
).pack(pady=(18, 4))

tk.Label(
    root, text="Real-time rates  |  Conversion history",
    font=("Arial", 10), bg=BG, fg=MUTED
).pack(pady=(0, 15))

panel = tk.Frame(root, bg=PANEL, padx=22, pady=18)
panel.pack(fill="x", padx=22)

tk.Label(
    panel, text="Amount", bg=PANEL, fg=TEXT
).grid(row=0, column=0, sticky="w", pady=5)

amount_entry = tk.Entry(
    panel, font=("Arial", 13),
    bg=BG, fg=TEXT, insertbackground=TEXT,
    relief="flat"
)
amount_entry.insert(0, "100")
amount_entry.grid(
    row=1, column=0, sticky="ew", padx=(0, 10), ipady=8
)

tk.Label(
    panel, text="From", bg=PANEL, fg=TEXT
).grid(row=0, column=1, sticky="w", pady=5)

source_box = ttk.Combobox(
    panel, values=CURRENCIES, state="readonly",
    font=("Arial", 11), width=12
)
source_box.set("USD")
source_box.grid(row=1, column=1, padx=6, ipady=5)

tk.Label(
    panel, text="To", bg=PANEL, fg=TEXT
).grid(row=0, column=3, sticky="w", pady=5)

target_box = ttk.Combobox(
    panel, values=CURRENCIES, state="readonly",
    font=("Arial", 11), width=12
)
target_box.set("INR")
target_box.grid(row=1, column=3, padx=6, ipady=5)

swap_button = tk.Button(
    panel, text="⇄", command=swap_currencies,
    bg=PANEL, fg=ACCENT, font=("Arial", 18, "bold"),
    relief="flat", cursor="hand2"
)
swap_button.grid(row=1, column=2, padx=5)

panel.columnconfigure(0, weight=1)

convert_button = tk.Button(
    panel, text="CONVERT",
    command=start_conversion,
    bg=ACCENT, fg=BG,
    font=("Arial", 11, "bold"),
    relief="flat", cursor="hand2",
    padx=22, pady=10
)
convert_button.grid(
    row=2, column=0, columnspan=4,
    sticky="ew", pady=(18, 8)
)

result_label = tk.Label(
    root, text="Enter an amount and click Convert",
    font=("Arial", 19, "bold"),
    bg=BG, fg=TEXT, justify="center"
)
result_label.pack(pady=(18, 5))

status_label = tk.Label(
    root, text="Ready",
    font=("Arial", 9), bg=BG, fg=MUTED,
    justify="center", wraplength=850
)
status_label.pack(pady=(0, 14))

history_frame = tk.Frame(root, bg=BG)
history_frame.pack(
    fill="both", expand=True, padx=22, pady=(0, 8)
)

tk.Label(
    history_frame, text="CONVERSION HISTORY",
    font=("Arial", 12, "bold"), bg=BG, fg=ACCENT
).pack(anchor="w", pady=(0, 8))

columns = (
    "Date", "Amount", "From", "To", "Rate", "Result"
)

table_frame = tk.Frame(history_frame, bg=BG)
table_frame.pack(fill="both", expand=True)

history_table = ttk.Treeview(
    table_frame, columns=columns,
    show="headings", height=7
)

widths = (150, 90, 60, 60, 110, 110)
for col, width in zip(columns, widths):
    history_table.heading(col, text=col)
    history_table.column(
        col, width=width, minwidth=50, anchor="center"
    )

scrollbar = ttk.Scrollbar(
    table_frame, orient="vertical",
    command=history_table.yview
)
history_table.configure(yscrollcommand=scrollbar.set)
history_table.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

# Bottom control buttons
bottom = tk.Frame(root, bg=BG)
bottom.pack(fill="x", padx=22, pady=(0, 8))

# Button to open the file directly in Excel
tk.Button(
    bottom, text="📊 Open in Excel",
    command=open_in_excel, cursor="hand2",
    bg=ACCENT, fg=BG, font=("Arial", 9, "bold"),
    relief="flat", padx=12, pady=4
).pack(side="left")

tk.Button(
    bottom, text="Refresh History",
    command=load_history, cursor="hand2",
    bg=PANEL, fg=TEXT, font=("Arial", 9),
    relief="flat", padx=10, pady=4
).pack(side="left", padx=8)

tk.Button(
    bottom, text="Clear History",
    command=clear_history, cursor="hand2",
    bg=PANEL, fg="#FF6B6B", font=("Arial", 9),
    relief="flat", padx=10, pady=4
).pack(side="left")

tk.Label(
    root,
    text="Exchange-rate data: open.er-api.com | "
         "Rates are indicative and may be delayed.",
    bg=BG, fg=MUTED, font=("Arial", 8)
).pack(pady=(0, 10))

load_history()
root.after(150, check_queue)
root.mainloop()