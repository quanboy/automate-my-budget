import pandas as pd
import gspread
import os
import re
from oauth2client.service_account import ServiceAccountCredentials


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
txt_file_path = os.path.join(BASE_DIR, 'SEPTEMBER.TXT')

creds_json_path = os.path.join(BASE_DIR, "configs", "automate-budget-keeping-42ad95124088.json")


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
print(df)
