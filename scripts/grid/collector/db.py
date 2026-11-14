#!/usr/bin/env python3
"""
SQLite store for the grid project (standard library only).

One file, <repo>/data/grid.db. The collector writes; the dashboard opens it
read-only with ``connect_ro()``. Timestamps are UTC ISO 8601 ("2026-11-12T23:30:00Z"),
taken straight from the APIs, so rows from Elexon (UK settlement days) and Octopus
(UTC windows) join on the same key even on 46 and 50 period clock-change days.

All writes go through ``upsert()`` so re-running a date or overlapping a fetch
window replaces rows instead of duplicating them.

Schema changes: append a new entry to MIGRATIONS. The version is stored in
``PRAGMA user_version``. Existing files on the Pi are upgraded on the next
``connect()``; never edit an entry that has already shipped.
"""

import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

logger = logging.getLogger(__name__)

# scripts/grid/collector/db.py -> parents[3] is the repo root.
DATA_DIR = Path(__file__).resolve().parents[3] / "data"
DB_PATH = DATA_DIR / "grid.db"

MIGRATIONS = [
    # 1: raw half-hourly data and run history
    """
    CREATE TABLE generation (
        ts_utc        TEXT NOT NULL,      -- period start, UTC
        fuel          TEXT NOT NULL,      -- Elexon fuelType, stored raw
        mw            REAL NOT NULL,      -- half-hour average MW
        settlement_date TEXT NOT NULL,    -- UK-local settlement day
        settlement_period INTEGER NOT NULL,
        published_at  TEXT,
        PRIMARY KEY (ts_utc, fuel)
    ) WITHOUT ROWID;

    CREATE TABLE demand (
        ts_utc        TEXT PRIMARY KEY,
        indo_mw       REAL,               -- initialDemandOutturn
        itsdo_mw      REAL,               -- initialTransmissionSystemDemandOutturn
        settlement_date TEXT NOT NULL,
        settlement_period INTEGER NOT NULL,
        published_at  TEXT
    ) WITHOUT ROWID;

    CREATE TABLE system_price (
        ts_utc        TEXT PRIMARY KEY,
        sell_gbp_mwh  REAL,               -- systemSellPrice
        buy_gbp_mwh   REAL,               -- systemBuyPrice
        net_imbalance_mwh REAL,           -- netImbalanceVolume
        settlement_date TEXT NOT NULL,
        settlement_period INTEGER NOT NULL
    ) WITHOUT ROWID;

    CREATE TABLE agile_price (
        valid_from_utc TEXT NOT NULL,
        region        TEXT NOT NULL,      -- Agile region letter A-P
        product       TEXT NOT NULL,      -- e.g. AGILE-24-10-01
        valid_to_utc  TEXT NOT NULL,
        inc_vat_p_kwh REAL NOT NULL,
        exc_vat_p_kwh REAL,
        PRIMARY KEY (valid_from_utc, region, product)
    ) WITHOUT ROWID;

    CREATE TABLE collector_runs (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        job         TEXT NOT NULL,        -- elexon, agile, summary, backfill
        started_at  TEXT NOT NULL,
        finished_at TEXT,
        duration_s  REAL,
        success     INTEGER NOT NULL,
        rows_written INTEGER,
        error       TEXT
    );
    CREATE INDEX idx_runs_job_started ON collector_runs (job, started_at);
    CREATE INDEX idx_generation_date ON generation (settlement_date);
    CREATE INDEX idx_demand_date ON demand (settlement_date);
    CREATE INDEX idx_system_price_date ON system_price (settlement_date);
    """,
    # 2: daily roll-ups written by the summary job (UK-local days)
    """
    CREATE TABLE daily_summary (
        date            TEXT PRIMARY KEY,  -- UK settlement day
        periods         INTEGER NOT NULL,  -- 48 normally, 46 or 50 on clock changes
        gen_total_mwh   REAL,              -- metered generation only, see docs
        gen_wind_mwh    REAL,
        gen_gas_mwh     REAL,              -- CCGT + OCGT
        gen_nuclear_mwh REAL,
        gen_biomass_mwh REAL,
        gen_imports_mwh REAL,              -- interconnectors, net
        demand_peak_mw  REAL,              -- INDO
        demand_peak_ts  TEXT,
        sys_avg_gbp_mwh REAL,
        sys_min_gbp_mwh REAL,
        sys_max_gbp_mwh REAL,
        sys_neg_periods INTEGER,
        updated_at      TEXT NOT NULL
    );

    CREATE TABLE agile_daily (
        date          TEXT NOT NULL,       -- UK-local date of the slot start
        region        TEXT NOT NULL,
        product       TEXT NOT NULL,
        slots         INTEGER NOT NULL,
        avg_p_kwh     REAL,
        min_p_kwh     REAL,
        max_p_kwh     REAL,
        neg_slots     INTEGER,
        cheapest2h_start_utc TEXT,         -- start of cheapest 4 consecutive slots
        cheapest2h_avg_p_kwh REAL,
        updated_at    TEXT NOT NULL,
        PRIMARY KEY (date, region, product)
    ) WITHOUT ROWID;
    """,
]


def utc_now() -> str:
    """Current time as UTC ISO 8601 with a trailing Z, to the second."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _migrate(conn: sqlite3.Connection) -> None:
    version = conn.execute("PRAGMA user_version").fetchone()[0]
    if version > len(MIGRATIONS):
        raise RuntimeError(
            f"grid.db is schema v{version}, code only knows v{len(MIGRATIONS)}"
        )
    for number in range(version + 1, len(MIGRATIONS) + 1):
        logger.info("Migrating grid.db to schema v%d", number)
        # One script: apply the migration and stamp the version together, so a
        # failure leaves user_version at its old value.
        conn.executescript(
            f"BEGIN;\n{MIGRATIONS[number - 1]}\nPRAGMA user_version = {number};\nCOMMIT;"
        )


def connect(path: Optional[Path] = None) -> sqlite3.Connection:
    """Open (creating and migrating if needed) the writable database."""
    path = Path(path) if path else DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA busy_timeout=10000")
    _migrate(conn)
    return conn


def connect_ro(path: Optional[Path] = None) -> sqlite3.Connection:
    """Open the database read-only (for the dashboard). The file must exist."""
    path = Path(path) if path else DB_PATH
    conn = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=10000")
    return conn


def upsert(conn: sqlite3.Connection, table: str, rows: Iterable[dict]) -> int:
    """
    Insert rows, replacing the non-key columns of any existing row with the same
    primary key. Returns the number of rows submitted. Does not commit; wrap a
    whole job in ``with conn:`` so it is one transaction.

    The table name is checked against the schema and the column names against the
    table, so nothing from an API response is spliced into SQL unchecked.
    """
    rows = list(rows)
    if not rows:
        return 0
    # Check the name with a bound parameter before it is used in any SQL text.
    known = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone()
    if not known:
        raise ValueError(f"Unknown table: {table!r}")
    info = conn.execute(f"PRAGMA table_info({table})").fetchall()
    columns = [r["name"] for r in info]
    pk = [r["name"] for r in sorted(info, key=lambda r: r["pk"]) if r["pk"]]
    keys = list(rows[0].keys())
    unknown = [k for k in keys if k not in columns]
    if unknown:
        raise ValueError(f"{table} has no column(s) {unknown}")
    updates = [k for k in keys if k not in pk]
    placeholders = ", ".join("?" for _ in keys)
    sql = f"INSERT INTO {table} ({', '.join(keys)}) VALUES ({placeholders})"
    if updates:
        sets = ", ".join(f"{k}=excluded.{k}" for k in updates)
        sql += f" ON CONFLICT ({', '.join(pk)}) DO UPDATE SET {sets}"
    else:
        sql += " ON CONFLICT DO NOTHING"
    conn.executemany(sql, [tuple(r[k] for k in keys) for r in rows])
    return len(rows)


def record_run(
    conn: sqlite3.Connection,
    job: str,
    started_at: str,
    duration_s: float,
    success: bool,
    rows_written: int = 0,
    error: Optional[str] = None,
) -> None:
    """Append a row to collector_runs and commit (call after the job's transaction)."""
    with conn:
        conn.execute(
            "INSERT INTO collector_runs "
            "(job, started_at, finished_at, duration_s, success, rows_written, error) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                job,
                started_at,
                utc_now(),
                round(duration_s, 2),
                int(success),
                rows_written,
                error[:500] if error else None,
            ),
        )


if __name__ == "__main__":
    # Create/migrate the default database and print its schema version.
    c = connect()
    print(f"{DB_PATH} schema v{c.execute('PRAGMA user_version').fetchone()[0]}")
    c.close()
