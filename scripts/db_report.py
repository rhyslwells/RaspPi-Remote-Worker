#!/usr/bin/env python3
"""
DB Report Script
Reads the per-script SQLite databases in data/ and reports what is in them.

Parameters (from Google Sheet Config):
- Parameter-1: Script name (e.g. "prime_hunter"). Blank = list all databases.
- Parameter-2: Number of recent runs to show (default 20, max 200)

Also works from the command line (run from the repo root):
    python scripts/db_report.py                       # list databases
    python scripts/db_report.py prime_hunter          # last 20 runs
    python scripts/db_report.py prime_hunter --limit 50
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from utils.control_panel import ControlPanel
from utils.script_db import connect, db_path, get_runs, list_databases

DEFAULT_LIMIT = 20
MAX_LIMIT = 200

# Parameters shown as form fields in Pi Control (see utils/params.py).
PARAMS = [
    {"name": "script", "label": "Script name (blank = list all)", "type": "str"},
    # Literals, not the constants above: Pi Control reads PARAMS without running the file.
    {"name": "limit", "label": "Recent runs to show", "type": "int",
     "default": 20, "min": 1, "max": 200},
]
CELL_CHARS = 200  # per-field truncation so the report stays readable
MAX_DETAILS = 40000  # the sheet cell limit is 50,000 characters


def _clip(value, width: int = CELL_CHARS) -> str:
    text = " ".join(str(value if value is not None else "").split())
    return text if len(text) <= width else text[: width - 3] + "..."


def _overview() -> tuple:
    files = list_databases()
    if not files:
        return (True, "No databases yet", "Nothing has been recorded in data/.")
    lines = []
    for path in files:
        conn = connect(path.stem, create=False)
        try:
            runs = conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
            last = conn.execute("SELECT MAX(started_at) FROM runs").fetchone()[0]
        finally:
            conn.close()
        lines.append(f"{path.stem}: {runs} run(s), last {last or 'never'}")
    return (True, f"{len(files)} database(s)", "\n".join(lines))


def _script_report(script: str, limit: int) -> tuple:
    if not db_path(script).exists():
        return (False, f"No database for {script}", f"Expected: {db_path(script).name}")

    rows = get_runs(script, limit)
    conn = connect(script, create=False)
    try:
        total = conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
        tables = [
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name NOT LIKE 'sqlite_%' AND name != 'runs' ORDER BY name"
            )
        ]
        extra = []
        for t in tables:
            count = conn.execute('SELECT COUNT(*) FROM "' + t + '"').fetchone()[0]
            extra.append(f"{t}: {count} row(s)")
    finally:
        conn.close()

    lines = [f"Showing {len(rows)} of {total} run(s), newest first", ""]
    for r in rows:
        lines.append(
            f"#{r['id']} {r['started_at']} "
            f"{'OK' if r['success'] else 'FAILED'} ({r['duration_s']}s)"
        )
        lines.append(f"  params:  {_clip(r['parameters'])}")
        lines.append(f"  message: {_clip(r['message'])}")
        lines.append(f"  details: {_clip(r['details'])}")
    if extra:
        lines += ["", "Other tables: " + "; ".join(extra)]

    details = "\n".join(lines)
    if len(details) > MAX_DETAILS:
        details = details[:MAX_DETAILS] + "\n... (truncated)"
    return (True, f"{script}: {len(rows)} of {total} run(s)", details)


def report(script: str = "", limit: int = DEFAULT_LIMIT) -> tuple:
    """Build the report. Returns (success, message, details)."""
    try:
        limit = max(1, min(int(limit), MAX_LIMIT))
        script = (script or "").strip()
        return _script_report(script, limit) if script else _overview()
    except Exception as e:
        return (False, "Error reading databases", f"{type(e).__name__}: {e}")


def main(params=None):
    """
    Main entry point when run by the runner or Pi Control.

    Args:
        params: dict with "script" and "limit" (from Pi Control / run_script.py). When
            None the values are read from the Config sheet.

    Returns:
        Tuple of (success: bool, message: str, details: str)
    """
    try:
        if params is not None:
            script = params.get("script") or ""
            limit = params.get("limit") or DEFAULT_LIMIT
            return report(script, limit)

        panel = ControlPanel(spreadsheet_name="RaspPI-Remote-Worker")
        params = panel.get_script_parameters("db_report.py")

        script = params.get("Parameter-1", "")
        raw_limit = params.get("Parameter-2", "")
        try:
            limit = int(raw_limit) if raw_limit else DEFAULT_LIMIT
        except ValueError:
            return (False, "Invalid row limit", f"Parameter-2 must be an integer, got: {raw_limit!r}")

        success, message, details = report(script, limit)
        if not script:
            # Show what arrived, so a value in the wrong column is easy to spot
            received = params if params else "none (no Parameter-N cell has a value)"
            details += (
                f"\n\nParameter-1 was blank, so this is the list of all databases. "
                f"Parameters received: {received}"
            )
        return (success, message, details)
    except Exception as e:
        return (False, "Error running db_report", f"{type(e).__name__}: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Show per-script SQLite databases.")
    parser.add_argument("script", nargs="?", default="", help="script name; omit to list all")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    args = parser.parse_args()
    ok, msg, det = report(args.script, args.limit)
    print(f"{'OK' if ok else 'FAILED'}: {msg}\n{det}")
    sys.exit(0 if ok else 1)
