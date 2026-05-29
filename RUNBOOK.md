# Runbook — Running `budget.py` from cold

Step-by-step reminders for running the budget pipeline after time away.

## The moving parts

All configured at the top of `budget.py`:

| Thing | Value |
| --- | --- |
| **Obsidian vault** | `C:\Users\shuiw\OneDrive\Documents\asdf` |
| **Credentials** | `configs\automate-budget-keeping-9a838892f238.json` (service account) |
| **Target sheet** | "Budget Tracker" — `SHEET_ID` `18KV8RX9smF29hCzfm3Na1kHZdsnJ3VFif--C7DOfsxY` |

## 1. Make sure the month's note exists in the vault

- File named exactly `"<Month> <Year>.md"` — e.g. `May 2026.md`.
- One expense per line as `amount category`:
  ```
  # May 2026          # heading / comment lines starting with # are ignored
  52 gas
  66 food
  250 airpods
  ```
- Plain numbers + words only. No `$`, no `- ` bullets — lines that don't start with a number are skipped.
- Categories are title-cased on import (`video games` → `Video Games`).

## 2. Check Python dependencies (one-time per machine)

```powershell
python -m pip install gspread oauth2client
```

`openpyxl` is no longer needed — the script writes to Google Sheets, not Excel.

## 3. Run it

```powershell
cd c:\Users\shuiw\Projects\automate-my-budget
python budget.py "May 2026"
```

- Pass the **full month + year** (matches the `.md` filename).
- Worksheet tabs are named by the **month word only** → `May Raw Data` / `May Summary`.

## 4. Confirm

- The script prints the updated tab names and a link to the sheet.
- Open: https://docs.google.com/spreadsheets/d/18KV8RX9smF29hCzfm3Na1kHZdsnJ3VFif--C7DOfsxY
- Re-running the same month is safe — it **clears and reuses** those two tabs (no duplicates).
- The Summary tab uses live `=SUMIF(...)` / `=SUM(...)` formulas, so totals recompute in-sheet.

## Gotchas

| Symptom | Fix |
| --- | --- |
| `File not found` | The `.md` name doesn't match your argument — check spacing / capitalization. |
| `No expense lines found` | Lines have `$`, bullets, or text first; make them `amount category`. |
| Auth / permission error | The sheet must stay shared with the service account `sheets-access-service-account@automate-budget-keeping.iam.gserviceaccount.com`. |
