"""
Every SQL query the dashboard runs, in one place. Read-only: each call opens a
short-lived read-only connection (SQLite handles this cheaply), so a collector
write in progress never blocks a page for more than the busy timeout.
"""

import shutil
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from grid.collector import config, db
from grid.dashboard import colours

TZ = ZoneInfo(config.TIMEZONE)
FMT = "%Y-%m-%dT%H:%M:%SZ"


@contextmanager
def _conn():
    conn = db.connect_ro()
    try:
        yield conn
    finally:
        conn.close()


def database_available() -> bool:
    return Path(db.DB_PATH).exists()


def to_local(ts_utc: str) -> datetime:
    """UTC ISO string to a naive UK-local datetime (what the charts plot)."""
    return (
        datetime.strptime(ts_utc, FMT).replace(tzinfo=timezone.utc).astimezone(TZ).replace(tzinfo=None)
    )


def uk_today() -> date:
    return datetime.now(TZ).date()


def _utc_now_str() -> str:
    return datetime.now(timezone.utc).strftime(FMT)


# --- freshness ---------------------------------------------------------------

def data_marker() -> str:
    """Cheap value that changes whenever the collector writes something new."""
    with _conn() as c:
        run = c.execute("SELECT max(id) FROM collector_runs").fetchone()[0]
        gen = c.execute("SELECT max(ts_utc) FROM generation").fetchone()[0]
        ag = c.execute("SELECT max(valid_to_utc) FROM agile_price").fetchone()[0]
    return f"{run}|{gen}|{ag}"


def freshness() -> dict:
    """Latest data timestamps and the last successful run per job."""
    with _conn() as c:
        latest_gen = c.execute("SELECT max(ts_utc) FROM generation").fetchone()[0]
        latest_price = c.execute("SELECT max(ts_utc) FROM system_price").fetchone()[0]
        agile_to = c.execute("SELECT max(valid_to_utc) FROM agile_price").fetchone()[0]
        jobs = {
            r["job"]: r["finished_at"]
            for r in c.execute(
                "SELECT job, max(finished_at) AS finished_at FROM collector_runs "
                "WHERE success=1 GROUP BY job"
            )
        }
    return {"generation": latest_gen, "system_price": latest_price, "agile_to": agile_to, "jobs": jobs}


def minutes_since(ts_utc):
    if not ts_utc:
        return None
    return (datetime.now(timezone.utc) - datetime.strptime(ts_utc, FMT).replace(tzinfo=timezone.utc)).total_seconds() / 60


# --- overview ----------------------------------------------------------------

def last_complete_summary():
    """Most recent daily_summary with a full set of periods, with the one before it."""
    with _conn() as c:
        rows = c.execute(
            "SELECT * FROM daily_summary WHERE periods >= 46 ORDER BY date DESC LIMIT 2"
        ).fetchall()
    return (dict(rows[0]) if rows else None, dict(rows[1]) if len(rows) > 1 else None)


def agile_upcoming(region: str):
    """Current and future Agile slots for a region, oldest first."""
    with _conn() as c:
        rows = c.execute(
            "SELECT valid_from_utc, valid_to_utc, inc_vat_p_kwh FROM agile_price "
            "WHERE region=? AND product=? AND valid_to_utc > ? ORDER BY valid_from_utc",
            (region, config.AGILE_PRODUCT, _utc_now_str()),
        ).fetchall()
    return [dict(r) for r in rows]


def cheapest_window(slots: list, n: int = 4):
    """Cheapest run of n consecutive slots: (start_utc, end_utc, avg) or None."""
    best = None
    for i in range(len(slots) - n + 1):
        win = slots[i : i + n]
        if any(win[j]["valid_to_utc"] != win[j + 1]["valid_from_utc"] for j in range(n - 1)):
            continue
        avg = sum(s["inc_vat_p_kwh"] for s in win) / n
        if best is None or avg < best[2]:
            best = (win[0]["valid_from_utc"], win[-1]["valid_to_utc"], avg)
    return best


def latest_demand_and_price():
    with _conn() as c:
        d = c.execute("SELECT ts_utc, indo_mw FROM demand ORDER BY ts_utc DESC LIMIT 1").fetchone()
        p = c.execute("SELECT ts_utc, sell_gbp_mwh FROM system_price ORDER BY ts_utc DESC LIMIT 1").fetchone()
    return (dict(d) if d else None, dict(p) if p else None)


# --- generation --------------------------------------------------------------

def available_dates():
    with _conn() as c:
        row = c.execute("SELECT min(settlement_date), max(settlement_date) FROM generation").fetchone()
    return (row[0], row[1])


def generation_range(start: str, end: str):
    """Grouped generation per half hour for UK days start..end: {group: [(local_dt, mw)]}."""
    out = {}
    with _conn() as c:
        for r in c.execute(
            "SELECT ts_utc, fuel, mw FROM generation WHERE settlement_date BETWEEN ? AND ? ORDER BY ts_utc",
            (start, end),
        ):
            g = colours.group_of(r["fuel"])
            bucket = out.setdefault(g, {})
            t = to_local(r["ts_utc"])
            bucket[t] = bucket.get(t, 0.0) + r["mw"]
    return {g: sorted(v.items()) for g, v in out.items()}


def demand_range(start: str, end: str):
    with _conn() as c:
        rows = c.execute(
            "SELECT ts_utc, indo_mw FROM demand WHERE settlement_date BETWEEN ? AND ? ORDER BY ts_utc",
            (start, end),
        ).fetchall()
    return [(to_local(r["ts_utc"]), r["indo_mw"]) for r in rows]


def gsp_dates(group: str):
    """First and last settlement date stored for a GSP group, or (None, None)."""
    with _conn() as c:
        row = c.execute(
            "SELECT min(settlement_date), max(settlement_date) FROM gsp_generation WHERE gsp_group=?",
            (group,),
        ).fetchone()
    return (row[0], row[1])


def gsp_range(group: str, start: str, end: str):
    """Metered output per category for UK days start..end: {category: [(local_dt, mw)]}."""
    out = {}
    with _conn() as c:
        for r in c.execute(
            "SELECT ts_utc, category, mwh FROM gsp_generation "
            "WHERE gsp_group=? AND settlement_date BETWEEN ? AND ? ORDER BY ts_utc",
            (group, start, end),
        ):
            out.setdefault(r["category"], []).append((to_local(r["ts_utc"]), r["mwh"] * 2))  # MWh per half hour to MW
    return out


# --- prices ------------------------------------------------------------------

def agile_range(region: str, start: str, end: str):
    """Agile slots for a region whose UK-local start date is in start..end."""
    lo = (date.fromisoformat(start) - timedelta(days=1)).isoformat() + "T00:00:00Z"
    hi = (date.fromisoformat(end) + timedelta(days=2)).isoformat() + "T00:00:00Z"
    with _conn() as c:
        rows = c.execute(
            "SELECT valid_from_utc, inc_vat_p_kwh FROM agile_price WHERE region=? AND product=? "
            "AND valid_from_utc >= ? AND valid_from_utc < ? ORDER BY valid_from_utc",
            (region, config.AGILE_PRODUCT, lo, hi),
        ).fetchall()
    out = []
    for r in rows:
        t = to_local(r["valid_from_utc"])
        if start <= t.date().isoformat() <= end:
            out.append((t, r["inc_vat_p_kwh"]))
    return out


def system_price_range(start: str, end: str):
    """System price in p/kWh (GBP/MWh divided by 10) for UK days start..end."""
    with _conn() as c:
        rows = c.execute(
            "SELECT ts_utc, sell_gbp_mwh FROM system_price WHERE settlement_date BETWEEN ? AND ? "
            "AND sell_gbp_mwh IS NOT NULL ORDER BY ts_utc",
            (start, end),
        ).fetchall()
    return [(to_local(r["ts_utc"]), r["sell_gbp_mwh"] / 10.0) for r in rows]


def agile_heatmap(region: str, days: int = 28):
    """Average Agile price by weekday (0=Mon) and half-hour of day over the last days."""
    end = uk_today() + timedelta(days=1)
    slots = agile_range(region, (end - timedelta(days=days)).isoformat(), end.isoformat())
    acc = {}
    for t, p in slots:
        key = (t.weekday(), t.hour * 2 + t.minute // 30)
        n, s = acc.get(key, (0, 0.0))
        acc[key] = (n + 1, s + p)
    return {k: s / n for k, (n, s) in acc.items()}


# --- history -----------------------------------------------------------------

def daily_summaries(days: int):
    since = (uk_today() - timedelta(days=days)).isoformat()
    with _conn() as c:
        rows = c.execute(
            "SELECT * FROM daily_summary WHERE date >= ? AND periods >= 46 ORDER BY date", (since,)
        ).fetchall()
    return [dict(r) for r in rows]


def agile_dailies(region: str, days: int):
    since = (uk_today() - timedelta(days=days)).isoformat()
    with _conn() as c:
        rows = c.execute(
            "SELECT * FROM agile_daily WHERE region=? AND product=? AND date >= ? ORDER BY date",
            (region, config.AGILE_PRODUCT, since),
        ).fetchall()
    return [dict(r) for r in rows]


# --- status ------------------------------------------------------------------

def recent_runs(limit: int = 30):
    with _conn() as c:
        rows = c.execute(
            "SELECT job, started_at, duration_s, success, rows_written, error "
            "FROM collector_runs ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def table_counts():
    with _conn() as c:
        return {
            t: c.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
            for t in ("generation", "demand", "system_price", "agile_price", "daily_summary", "agile_daily", "gsp_generation")
        }


def system_info() -> dict:
    """Database size and free disk. Local reads only."""
    info = {"db_mb": None, "disk_free_pct": None}
    try:
        info["db_mb"] = Path(db.DB_PATH).stat().st_size / 1e6
    except OSError:
        pass
    try:
        du = shutil.disk_usage(Path(db.DB_PATH).parent)
        info["disk_free_pct"] = du.free / du.total * 100
    except OSError:
        pass
    return info
