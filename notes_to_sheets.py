import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Step 1 - Read and process the text file
with open('SEPTEMBER.TXT', 'r', encoding="utf-8") as f:
    lines = [line.strip() for line in f if line.strip()]

data = []
for line in lines[1:]:
    parts = line.split(maxsplit=1)
    if len(parts) == 2:
        try:
            amount = float(parts[0])
            category = parts[1].lower()
            data.append((amount, category))
        except ValueError:
            pass

df = pd.DataFrame(data, columns=['Amount', 'Category'])


# Step 2 - Authorize Google Sheets API
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

creds = ServiceAccountCredentials.from_json_keyfile_name('automate-budget-keeping-42ad95124088.json', scope)
client = gspread.authorize(creds)

# Step 3 - Create a new Google Sheet and export data
sheet = client.create("September Budget")
worksheet = sheet.get_worksheet(0)