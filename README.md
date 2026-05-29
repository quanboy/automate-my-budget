# Automate My Budget

Reads monthly expense notes from an Obsidian vault and uploads them to the
"Budget Tracker" Google Sheet.

```
Obsidian vault (MONTH.md) → budget.py (gspread) → Google Sheets
```

## Quick start

```powershell
python -m pip install gspread oauth2client     # one-time
python budget.py "May 2026"
```

This reads `<vault>\May 2026.md`, parses `amount category` lines, and writes a
`May Raw Data` and `May Summary` worksheet to the sheet. Re-running a month
clears and reuses the same tabs.

**Note format** — one expense per line, lines starting with `#` are ignored:

```
# May 2026
52 gas
66 food
250 airpods
```

## More

- **First time in a while?** See [RUNBOOK.md](RUNBOOK.md) for the full cold-start
  checklist (config locations, dependencies, gotchas).
- **Architecture, conventions, security** — see [CLAUDE.md](CLAUDE.md).
- `export_month.py` is the **legacy** iCloud Notes + OCR exporter, superseded by
  the Obsidian markdown workflow.
