"""
budget.py — Obsidian → Excel budget pipeline

Usage:
    python budget.py "September 2026"

Reads a markdown file from your Obsidian vault (e.g. "September 2026.md"),
parses lines in the format "amount category", and writes a raw data sheet
and a category summary sheet to a local "Budget Tracker" Excel workbook.
"""

import sys
import re
import os
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font

# ── CONFIG (edit once) ────────────────────────────────────────────────────────

VAULT_PATH = r"C:\Users\victo\Documents\asdf\Finances"
WORKBOOK_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "budget.xlsx")

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


# ── EXCEL OUTPUT ──────────────────────────────────────────────────────────────

def load_workbook_or_new():
    if os.path.exists(WORKBOOK_PATH):
        return load_workbook(WORKBOOK_PATH)
    wb = Workbook()
    wb.remove(wb.active)  # drop the default blank sheet
    return wb


def get_or_create_worksheet(workbook, title: str):
    """Return a cleared worksheet with the given title, creating it if needed."""
    if title in workbook.sheetnames:
        ws = workbook[title]
        workbook.remove(ws)
    return workbook.create_sheet(title=title)


def upload_month(workbook, expenses: list[dict], month: str):
    raw_title = f"{month} Raw Data"
    sum_title = f"{month} Summary"
    bold = Font(bold=True)

    # ── Raw Data sheet ──
    ws_raw = get_or_create_worksheet(workbook, raw_title)
    ws_raw.append(["Amount", "Category"])
    for cell in ws_raw[1]:
        cell.font = bold
    for e in expenses:
        ws_raw.append([e["amount"], e["category"]])

    # ── Summary sheet ──
    categories = {}
    for exp in expenses:
        categories[exp["category"]] = categories.get(exp["category"], 0) + exp["amount"]
    sorted_cats = sorted(categories.items(), key=lambda x: x[1], reverse=True)

    ws_sum = get_or_create_worksheet(workbook, sum_title)
    ws_sum.append(["Category", "Total"])
    for cell in ws_sum[1]:
        cell.font = bold

    for i, (cat, _) in enumerate(sorted_cats, start=2):
        formula = f"=SUMIF('{raw_title}'!B:B,A{i},'{raw_title}'!A:A)"
        ws_sum.append([cat, formula])
    total_row = len(sorted_cats) + 2
    ws_sum.append(["TOTAL", f"=SUM(B2:B{total_row - 1})"])
    for cell in ws_sum[total_row]:
        cell.font = bold

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

    print(f"Loading workbook: {WORKBOOK_PATH}")
    workbook = load_workbook_or_new()

    print("Writing worksheets...")
    raw_title, sum_title = upload_month(workbook, expenses, tab_month)
    workbook.save(WORKBOOK_PATH)

    print(f"\nUpdated worksheets: '{raw_title}', '{sum_title}'")
    print(f"Saved to {WORKBOOK_PATH}")
    print("Done!")


if __name__ == "__main__":
    main()
