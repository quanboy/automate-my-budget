"""
budget.py — Obsidian → Google Sheets budget pipeline

Usage:
    python budget.py "September 2026"

Reads a markdown file from your Obsidian vault (e.g. "September 2026.md"),
parses lines in the format "amount category", and uploads a raw data sheet
and a category summary sheet to the "Budget Tracker" Google Sheet.
"""

import sys
import re
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ── CONFIG (edit once) ────────────────────────────────────────────────────────

VAULT_PATH = r"C:\Users\shuiw\OneDrive\Documents\asdf"
CONFIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "configs")
CREDS_PATH = os.path.join(CONFIG_DIR, "automate-budget-keeping-9a838892f238.json")
SHEET_ID = "18KV8RX9smF29hCzfm3Na1kHZdsnJ3VFif--C7DOfsxY"

# ── PARSING ───────────────────────────────────────────────────────────────────

def read_note(vault_path: str, month: str) -> str:
    filepath = os.path.join(vault_path, f"{month}.md")
    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}")
        sys.exit(1)
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def parse_expenses(text: str) -> list[dict]:
    pattern = re.compile(r"^\s*(\d+(?:\.\d+)?)\s+(.+)$")
    rows = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        match = pattern.match(stripped)
        if match:
            amount = float(match.group(1))
            category = match.group(2).strip().title()
            rows.append({"amount": amount, "category": category})

    if not rows:
        print("Error: No expense lines found. Expected format: 'amount category' per line.")
        sys.exit(1)

    return rows


# ── GOOGLE SHEETS OUTPUT ──────────────────────────────────────────────────────

SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]


def connect_sheet():
    if not os.path.exists(CREDS_PATH):
        print(f"Error: Service account credentials not found: {CREDS_PATH}")
        sys.exit(1)
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_PATH, SCOPE)
    gc = gspread.authorize(creds)
    return gc.open_by_key(SHEET_ID)


def get_or_create_worksheet(spreadsheet, title: str, rows: int, cols: int):
    """Return a cleared worksheet with the given title, creating it if needed."""
    try:
        ws = spreadsheet.worksheet(title)
        ws.clear()
        return ws
    except gspread.WorksheetNotFound:
        return spreadsheet.add_worksheet(title=title, rows=rows, cols=cols)


def upload_month(spreadsheet, expenses: list[dict], month: str):
    raw_title = f"{month} Raw Data"
    sum_title = f"{month} Summary"

    # ── Raw Data sheet ──
    raw_rows = [["Amount", "Category"]] + [[e["amount"], e["category"]] for e in expenses]
    ws_raw = get_or_create_worksheet(spreadsheet, raw_title, rows=len(raw_rows) + 10, cols=2)
    ws_raw.update(raw_rows, "A1")
    ws_raw.format("A1:B1", {"textFormat": {"bold": True}})

    # ── Summary sheet ──
    categories = {}
    for exp in expenses:
        categories[exp["category"]] = categories.get(exp["category"], 0) + exp["amount"]
    sorted_cats = sorted(categories.items(), key=lambda x: x[1], reverse=True)

    sum_rows = [["Category", "Total"]]
    for i, (cat, _) in enumerate(sorted_cats, start=2):
        formula = f"=SUMIF('{raw_title}'!B:B,A{i},'{raw_title}'!A:A)"
        sum_rows.append([cat, formula])
    total_row = len(sorted_cats) + 2
    sum_rows.append(["TOTAL", f"=SUM(B2:B{total_row - 1})"])

    ws_sum = get_or_create_worksheet(spreadsheet, sum_title, rows=len(sum_rows) + 10, cols=2)
    ws_sum.update(sum_rows, "A1", value_input_option="USER_ENTERED")
    ws_sum.format("A1:B1", {"textFormat": {"bold": True}})
    ws_sum.format(f"A{total_row}:B{total_row}", {"textFormat": {"bold": True}})

    return raw_title, sum_title


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print('Usage: python budget.py "September 2026"')
        sys.exit(1)

    month = sys.argv[1]
    # Worksheet tabs use the month word only (e.g. "May"), matching existing tabs.
    tab_month = month.split()[0]

    print(f"Reading: {month}.md")
    text = read_note(VAULT_PATH, month)

    print("Parsing expenses...")
    expenses = parse_expenses(text)
    print(f"Found {len(expenses)} expenses")

    print("Connecting to Google Sheets...")
    spreadsheet = connect_sheet()

    print(f"Uploading to '{spreadsheet.title}'...")
    raw_title, sum_title = upload_month(spreadsheet, expenses, tab_month)

    print(f"\nUpdated worksheets: '{raw_title}', '{sum_title}'")
    print(f"https://docs.google.com/spreadsheets/d/{SHEET_ID}")
    print("Done!")


if __name__ == "__main__":
    main()
