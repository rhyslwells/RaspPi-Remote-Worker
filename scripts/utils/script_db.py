#!/usr/bin/env python3
"""
Per-script SQLite databases (standard library only).

Each script gets its own file: <repo>/data/<script_name>.db

Every database has a standard ``runs`` table that the runner fills in after each
execution (parameters, result, message, details, duration). Scripts can also open
their own database with ``connect()`` and create extra tables for their own data.

Example (inside a task script):
    from utils.script_db import connect

    with connect("prime_hunter") as db:
        db.execute("CREATE TABLE IF NOT EXISTS primes (n INTEGER PRIMARY KEY)")
        db.executemany("INSERT OR IGNORE INTO primes VALUES (?)", [(p,) for p in primes])
"""

import json
import logging
import re
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Anchored to this file, not the working directory, so it resolves the same way
# whether run by the service, from the repo root, or from a script.
DATA_DIR = Path(__file__).resolve().parents[2] / "data"

RUNS_SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at  TEXT    NOT NULL,
    duration_s  REAL,
    success     INTEGER NOT NULL,
    parameters  TEXT,
    message     TEXT,
    details     TEXT
)
"""


def script_key(script_name: str) -> str:
    """
    Normalise a script name ("prime_hunter.py" -> "prime_hunter").

    Only letters, digits, '_' and '-' are kept so a name can never escape DATA_DIR.
    """
    name = Path(str(script_name)).name
    if name.endswith(".py"):
        name = name[:-3]
    name = re.sub(r"[^A-Za-z0-9_-]", "_", name).strip("._")
    if not name:
        raise ValueError(f"Invalid script name: {script_name!r}")
    return name


def db_path(script_name: str) -> Path:
    """Path of the database file for a script."""
    return DATA_DIR / f"{script_key(script_name)}.db"


def connect(script_name: str, create: bool = True) -> sqlite3.Connection:
    """
    Open (and by default create) a script's database with the ``runs`` table present.

    Use as a context manager to commit/rollback; the caller should ``close()`` it
    when finished. Rows are returned as ``sqlite3.Row``.
    """
    path = db_path(script_name)
    if not create and not path.exists():
        raise FileNotFoundError(f"No database for {script_name}: {path}")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute(RUNS_SCHEMA)
    conn.commit()
    return conn


def record_run(
    script_name: str,
    started_at: str,
    duration_s: float,
    success: bool,
    parameters: Optional[Dict[str, str]],
    message: str,
    details: str,
) -> bool:
    """
    Append one execution to the script's ``runs`` table.

    Never raises: a database problem must not turn a good script run into a failure.
    Returns True if the row was written.
    """
    try:
        conn = connect(script_name)
        try:
            with conn:
                conn.execute(
                    "INSERT INTO runs (started_at, duration_s, success, parameters, "
                    "message, details) VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        started_at,
                        round(float(duration_s), 3),
                        1 if success else 0,
                        json.dumps(parameters or {}, sort_keys=True),
                        str(message),
                        str(details),
                    ),
                )
        finally:
            conn.close()
        return True
    except Exception as e:  # noqa: BLE001 - recording is best effort by design
        logger.error(f"Could not record run for {script_name}: {e}")
        return False


def list_databases() -> List[Path]:
    """All per-script database files, sorted by name."""
    if not DATA_DIR.exists():
        return []
    return sorted(DATA_DIR.glob("*.db"))


def get_runs(script_name: str, limit: int = 20) -> List[sqlite3.Row]:
    """Most recent runs first. Raises FileNotFoundError if the script has no database."""
    conn = connect(script_name, create=False)
    try:
        return conn.execute(
            "SELECT * FROM runs ORDER BY id DESC LIMIT ?", (int(limit),)
        ).fetchall()
    finally:
        conn.close()
