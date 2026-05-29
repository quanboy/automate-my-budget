# Automate My Budget

Personal finance automation tool that reads monthly expense notes from an Obsidian vault and uploads them to Google Sheets.

## Architecture

```
Obsidian vault (MONTH.md) → budget.py (gspread) → Google Sheets ("Budget Tracker")
```

The project is migrating off the older iCloud Notes + OCR flow (see `export_month.py`, legacy) toward plain markdown notes in an Obsidian vault.

### Scripts

- `budget.py` — Reads a markdown file from the Obsidian vault (e.g. `"September 2026.md"`), parses `{amount} {category}` lines, and uploads a `{Month} Raw Data` and `{Month} Summary` worksheet to the Google Sheet. Re-running a month clears and reuses the same tabs.
- `export_month.py` — **Legacy.** Browser automation (Edge/Selenium) that opened iCloud Notes, screenshotted pinned notes while scrolling, ran Tesseract OCR, and merged overlapping text with fuzzy matching. Superseded by the Obsidian markdown workflow.

## Data Format

Monthly markdown files live in the Obsidian vault (`VAULT_PATH` in `budget.py`):
```
# September 2026        # optional heading / comment lines (starting with #) are ignored
213 amazon              # {amount} {category}
40 food
70 video games
...
```
Categories are title-cased on import (`video games` → `Video Games`).

## Tech Stack

- **Python 3** — gspread, oauth2client (legacy `export_month.py` also uses Selenium, Pillow, pytesseract)
- **Google Sheets API** — service account auth via `configs/*.json`
- **MS Edge WebDriver** (`msedgedriver.exe`) — only needed by the legacy `export_month.py`

## Key Conventions

- Google Sheet ID: `18KV8RX9smF29hCzfm3Na1kHZdsnJ3VFif--C7DOfsxY` (titled "Budget Tracker")
- Worksheet tabs use the **month word only** — `"May 2026"` → `May Raw Data` / `May Summary` — to match existing tabs
- The Summary sheet uses live `=SUMIF(...)` / `=SUM(...)` formulas so totals recompute in-sheet
- Configure `VAULT_PATH`, `CREDS_PATH`, and `SHEET_ID` at the top of `budget.py`

## Running

```
python budget.py "September 2026"
```

Reads `{VAULT_PATH}/September 2026.md` and uploads the `September Raw Data` / `September Summary` tabs.

## Security

- Service account credentials in `configs/` must not be committed to git
- Credential files were previously removed from history (commit f78eb8c)
