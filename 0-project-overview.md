# Remote Worker: Raspberry Pi Task Runner

## Architecture Overview

This is a classic "Remote Worker" architecture. Using a Raspberry Pi as a persistent execution engine allows you to handle tasks that don't belong on your primary machine or require 24/7 availability.

By using a Google Sheet as a "Control Panel," you bypass the need for a complex web UI or SSH-ing into the Pi every time you want to trigger a task.

**Config Sheet:** https://docs.google.com/spreadsheets/d/1d9QU9st_j2gY4Qp7gkhNu5PB016w58sfkjGkW4JydD8/edit?gid=0#gid=0

### System Components

The system consists of three main components interacting in a loop:

1. **The Controller (Google Sheets):** A simple spreadsheet where Column A is the `Script Name` and Column B is a `Status` (e.g., "START", "RUNNING", "IDLE").

2. **The Worker (Raspberry Pi):** A service running a Python loop that polls the Google Sheet API, checks for the "START" flag, executes the local script, and updates the sheet back to "IDLE" (or "SUCCESS/FAIL").

3. **The Scripts (/scripts folder):** Modular Python scripts that perform specific tasks.

### How It Works

The Raspberry Pi will run a script (managed by `systemd` to ensure it restarts on boot) that performs these steps:

1. Authenticate with Google
2. Read the target Range in your Sheet
3. If a cell matches "START":
   - Import and run the corresponding module from the `/scripts` folder
   - Log the output
   - Update the Sheet cell to "IDLE"

---

## Documentation & Implementation Phases

Follow these phases in order to set up the complete system:

- INSERT RELEVANT LINKS TO OTHER DOCS HERE #TODO

---

## Project Structure

```
/
├── runner.py              # Main polling and execution loop #TODO
├── pyproject.toml       # Python dependencies (gspread, oauth2client)
├── credentials.json       # ⚠️  Service account credentials (NEVER commit)
├── .gitignore            # Excludes credentials.json
├── /scripts/             # Script modules to be executed
├── /docs/                # Documentation
└── /logs/                # Service logs (generated at runtime)
```

---

## Control Panel Status Reference

| Status Value | Meaning |
|-------------|---------|
| `IDLE`     | Ready to execute (default state) |
| `START`    | Trigger script execution |
| `RUNNING`  | Script currently executing |
| `SUCCESS`  | Last execution completed successfully |
| `FAILED`   | Last execution encountered an error |


