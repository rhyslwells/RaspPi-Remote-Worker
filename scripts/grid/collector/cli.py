"""
Command line for the grid collector. Run through scripts/grid/collect.py:

    python scripts/grid/collect.py elexon                 # trailing 2 settlement days
    python scripts/grid/collect.py agile                  # all regions, yesterday..tomorrow
    python scripts/grid/collect.py summary [--date D]     # default: yesterday (UK)
    python scripts/grid/collect.py backfill --from D --to D

Exit code 0 on success, 1 on failure (so systemd marks the unit failed).
Every run is recorded in collector_runs.
"""

import argparse
import logging
import logging.handlers
import os
import sqlite3
import sys
import time
import traceback
from datetime import date, datetime, timedelta, timezone

from grid.collector import client, config, db, fetch_agile, fetch_elexon, summarise

logger = logging.getLogger("grid.collector")


class Locked(Exception):
    pass


class JobLock:
    """One run per job at a time. A lock older than LOCK_STALE_S is taken over."""

    def __init__(self, job: str):
        self.path = config.LOCK_DIR / f"grid_{job}.lock"

    def __enter__(self):
        config.LOCK_DIR.mkdir(parents=True, exist_ok=True)
        for _ in range(2):
            try:
                fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(fd, str(os.getpid()).encode())
                os.close(fd)
                return self
            except FileExistsError:
                age = time.time() - self.path.stat().st_mtime
                if age < config.LOCK_STALE_S:
                    raise Locked(f"{self.path.name} held (age {age:.0f}s)")
                logger.warning("Removing stale lock %s (age %.0fs)", self.path.name, age)
                self.path.unlink(missing_ok=True)
        raise Locked(f"could not take {self.path.name}")

    def __exit__(self, *exc):
        self.path.unlink(missing_ok=True)


def _setup_logging() -> None:
    root = logging.getLogger()
    if getattr(root, "_grid_configured", False):
        return
    root._grid_configured = True
    config.LOG_DIR.mkdir(parents=True, exist_ok=True)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    file_handler = logging.handlers.RotatingFileHandler(
        config.LOG_DIR / "grid_collector.log", maxBytes=1_000_000, backupCount=3
    )
    stream = logging.StreamHandler()
    root.setLevel(logging.INFO)
    for h in (file_handler, stream):
        h.setFormatter(fmt)
        root.addHandler(h)


def _day(value: str) -> date:
    return date.fromisoformat(value)


def _agile_window(first: date, last: date):
    """UTC window covering UK dates first..last inclusive, widened by a day."""
    start = datetime.combine(first - timedelta(days=1), datetime.min.time(), timezone.utc)
    end = datetime.combine(last + timedelta(days=2), datetime.min.time(), timezone.utc)
    return start, end


def _run_elexon(conn, args) -> int:
    today = summarise.uk_today()
    return fetch_elexon.collect(conn, today - timedelta(days=config.ELEXON_TRAILING_DAYS - 1), today)


def _run_agile(conn, args) -> int:
    today = summarise.uk_today()
    start, end = _agile_window(today - timedelta(days=1), today + timedelta(days=1))
    return fetch_agile.collect(conn, start, end)


def _run_summary(conn, args) -> int:
    day = args.date or summarise.uk_today() - timedelta(days=1)
    return summarise.collect(conn, day, day)


def _run_backfill(conn, args) -> int:
    if args.to < args.start:
        raise ValueError("--to is before --from")
    written = fetch_elexon.collect(conn, args.start, args.to)
    start, end = _agile_window(args.start, args.to)
    written += fetch_agile.collect(conn, start, end)
    written += summarise.collect(conn, args.start, args.to)
    return written


def _run_backup(conn, args) -> int:
    """Copy grid.db with SQLite's online backup (safe while it is being written)."""
    backup_dir = db.DB_PATH.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    target = backup_dir / f"grid-{datetime.now(timezone.utc):%Y%m%d}.db"
    dest = sqlite3.connect(target)
    try:
        conn.backup(dest)
    finally:
        dest.close()
    # Keep the newest BACKUPS_KEPT files.
    for old in sorted(backup_dir.glob("grid-*.db"))[: -config.BACKUPS_KEPT]:
        old.unlink()
    logger.info("Backup written to %s", target)
    return 1


def _heartbeat() -> None:
    """Ping GRID_HEARTBEAT_URL after a successful run, if one is configured."""
    url = os.environ.get("GRID_HEARTBEAT_URL")
    if not url:
        return
    try:
        client.get_text(url)
    except Exception as exc:  # monitoring must never fail a job
        logger.warning("Heartbeat ping failed: %s", exc)


JOBS = {
    "elexon": _run_elexon,
    "agile": _run_agile,
    "summary": _run_summary,
    "backfill": _run_backfill,
    "backup": _run_backup,
}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="GB grid data collector")
    sub = parser.add_subparsers(dest="job", required=True)
    sub.add_parser("elexon", help="fetch generation, demand and system prices")
    sub.add_parser("agile", help="fetch Agile rates for all regions")
    sub.add_parser("backup", help="copy grid.db to data/backups/")
    p_sum = sub.add_parser("summary", help="build daily roll-ups")
    p_sum.add_argument("--date", type=_day, help="UK date (default yesterday)")
    p_back = sub.add_parser("backfill", help="fetch and summarise a date range")
    p_back.add_argument("--from", dest="start", type=_day, required=True)
    p_back.add_argument("--to", type=_day, required=True)
    args = parser.parse_args(argv)

    _setup_logging()
    started = db.utc_now()
    t0 = time.monotonic()
    try:
        with JobLock(args.job):
            conn = db.connect()
            try:
                written, error = 0, None
                try:
                    written = JOBS[args.job](conn, args)
                except Exception as exc:
                    error = f"{type(exc).__name__}: {exc}"
                    logger.error("Job %s failed: %s\n%s", args.job, error, traceback.format_exc())
                db.record_run(
                    conn, args.job, started, time.monotonic() - t0,
                    error is None, written, error,
                )
            finally:
                conn.close()
    except Locked as exc:
        logger.warning("Job %s skipped, already running: %s", args.job, exc)
        return 0
    if error:
        return 1
    if args.job in config.HEARTBEAT_JOBS:
        _heartbeat()
    logger.info("Job %s ok, %d rows in %.1fs", args.job, written, time.monotonic() - t0)
    return 0
