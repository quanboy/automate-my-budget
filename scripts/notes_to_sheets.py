import pandas as pd
import gspread
import os
import re
from oauth2client.service_account import ServiceAccountCredentials


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
txt_file_path = os.path.join(BASE_DIR, 'SEPTEMBER.TXT')


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


df = parse_expenses(txt_file_path)
summary = df.groupby("category")["amount"].sum().reset_index()
print(df)
print(summary)

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

creds_file = os.path.join(BASE_DIR, "configs", "automate-budget-keeping-ff165a769354.json")
creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scope)
client = gspread.authorize(creds)

# sheet = client.create("September Expenses")
sheet_id = "18KV8RX9smF29hCzfm3Na1kHZdsnJ3VFif--C7DOfsxY"
sheet = client.open_by_key(sheet_id)
print(f"Created new sheet: {sheet.url}")

month_name = "September"
raw_tab_name = f"{month_name} Raw Data"
summary_tab_name = f"{month_name} Summary"

raw_worksheet = sheet.get_worksheet(0)
if raw_worksheet.title == "Sheet1":
    raw_ws = raw_worksheet
    raw_ws.update_title(raw_tab_name)
else:
    try:
        raw_ws = sheet.worksheet(raw_tab_name)
        sheet.del_worksheet(raw_ws)
    except:
        pass
    raw_ws = sheet.add_worksheet(title=raw_tab_name, rows="100", cols="20")

raw_ws.update([df.columns.values.tolist()] + df.values.tolist())

summary_worksheet_placeholder = sheet.get_worksheet(1)
if summary_worksheet_placeholder.title == "September Summary" or summary_worksheet_placeholder.title == "Sheet2":
    summary_worksheet = summary_worksheet_placeholder
    summary_worksheet.update_title(summary_tab_name)
else:
    try:
        summary_worksheet = sheet.worksheet(summary_tab_name)
        sheet.del_worksheet(summary_worksheet)
    except:
        pass
    summary_worksheet = sheet.add_worksheet(title="September Summary", rows="100", cols="20")

summary_worksheet.update([summary.columns.values.tolist()] + summary.values.tolist())

print("Data uploaded to Google Sheets successfully.")