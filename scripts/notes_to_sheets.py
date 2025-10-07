import pandas as pd
import gspread
import os
import re
from oauth2client.service_account import ServiceAccountCredentials


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
month_files = [f for f in os.listdir(BASE_DIR) if f.endswith(".TXT")]
if not month_files:
    raise FileNotFoundError("No .TXT file found in the project root directory.")

scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds_file = os.path.join(BASE_DIR, "configs", "automate-budget-keeping-aca1a242f01a.json")
creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scope)
client = gspread.authorize(creds)

sheet_id = "18KV8RX9smF29hCzfm3Na1kHZdsnJ3VFif--C7DOfsxY"
sheet = client.open_by_key(sheet_id)
print(f"Created new sheet: {sheet.url}")

def detect_month_name(txt_file_path):
    with open(txt_file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                return line.capitalize()
            return "Unknown Month"


def parse_expenses(txt_file_path):
    with open(txt_file_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]  

    data = []
    for line in lines:
        if re.match(r"^[a-zA-Z]+(\s+\d{1,2})?$", line.lower()):
            continue  

        
        parts = line.split(maxsplit=1)
        if len(parts) == 2:
            try:
                amount = float(parts[0])
                category = parts[1].lower()
                data.append((amount, category))
            except ValueError:
                continue

    return pd.DataFrame(data, columns=["amount", "category"])

def update_sheet_for_months(sheet, month_name, df, summary):
    raw_tab_name = f"{month_name} Raw Data"
    summary_tab_name = f"{month_name} Summary"
    try:
        raw_ws = sheet.worksheet(raw_tab_name)
        sheet.del_worksheet(raw_ws)
    except:
        pass
    raw_ws = sheet.add_worksheet(title=raw_tab_name, rows="100", cols="20")
    raw_ws.update([df.columns.values.tolist()] + df.values.tolist())

    try:
        summary_worksheet = sheet.worksheet(summary_tab_name)
        sheet.del_worksheet(summary_worksheet)
    except:
        pass
    summary_worksheet = sheet.add_worksheet(title=summary_tab_name, rows="100", cols="20")
    summary_worksheet.update([summary.columns.values.tolist()] + summary.values.tolist())

    print(f"Data for {month_name} uploaded to Google Sheets successfully.")

for filename in sorted(month_files):
    txt_file_path = os.path.join(BASE_DIR, filename)
    print(f"Processing file: {filename}")

    month_name = detect_month_name(txt_file_path)
    df = parse_expenses(txt_file_path)
    summary = df.groupby("category")["amount"].sum().reset_index()
    update_sheet_for_months(sheet, month_name, df, summary)

print("Data uploaded to Google Sheets successfully.")