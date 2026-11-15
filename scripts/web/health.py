#!/usr/bin/env python3
"""
Pi health for the web UI: the current reading, the samples pulse_monitor has stored,
and whether background sampling is running.

Read only. The readings come from pulse_monitor.py (so there is one place that knows
how to read the Pi), and the history from the `health` table of data/pulse_monitor.db.
Nothing here uses the Google Sheet. Off the Pi most readings are None.
"""

import sqlite3
import subprocess
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from utils import script_db

BACKGROUND_TIMER = "pulse-sample"  # permanent timer, installed by install_web.sh
RANGES_HOURS = (1, 6, 24, 168)  # 1h, 6h, 24h, 7d
MAX_POINTS = 240                # thin out long ranges so the page stays light
COLUMNS = ["taken_at", "cpu_temp_c", "load_1m", "mem_used_pct", "disk_used_pct", "uptime_h"]


def _monitor():
    # Imported on first use: it pulls in the Sheet client (not used here, only imported).
    import pulse_monitor

    return pulse_monitor


def current() -> Dict[str, Any]:
    pm = _monitor()
    metrics = pm.collect_metrics()
    warnings = pm.find_warnings(metrics, pm.DEFAULT_MAX_TEMP_C, pm.DEFAULT_MIN_FREE_DISK_PCT)
    return {**metrics, "warnings": warnings}


def schedule() -> str:
    """'active' or 'inactive' for the pulse-sample timer, 'unknown' off the Pi."""
    if not sys.platform.startswith("linux"):
        return "unknown"
    pm = _monitor()
    try:
        result = subprocess.run(
            [pm.SYSTEMCTL, "is-active", f"{BACKGROUND_TIMER}.timer"],
            capture_output=True, text=True, timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return "unknown"
    return "active" if result.stdout.strip() == "active" else "inactive"


def history(hours: int) -> tuple:
    """(rows, last_sample_time). Each row follows COLUMNS."""
    since = (datetime.now() - timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
    try:
        conn = script_db.connect("pulse_monitor", create=False)
    except FileNotFoundError:
        return [], None
    try:
        rows = conn.execute(
            f"SELECT {', '.join(COLUMNS)} FROM health WHERE taken_at >= ? ORDER BY taken_at",
            (since,),
        ).fetchall()
        last = conn.execute("SELECT MAX(taken_at) FROM health").fetchone()[0]
    except sqlite3.Error:  # no health table yet
        return [], None
    finally:
        conn.close()
    stride = max(1, -(-len(rows) // MAX_POINTS))  # ceiling division
    return [list(r) for r in rows[::stride]], last


def snapshot(hours: int = 24) -> Dict[str, Any]:
    if hours not in RANGES_HOURS:
        hours = 24
    points, last = history(hours)
    return {
        "server_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "now": current(),
        "schedule": schedule(),
        "last_sample": last,
        "hours": hours,
        "columns": COLUMNS,
        "points": points,
    }
