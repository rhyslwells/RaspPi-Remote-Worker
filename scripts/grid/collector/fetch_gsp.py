"""
Metered output per GSP group from Elexon.

Two public datasets are joined:
  * BM unit reference (/reference/bmunits/all): which GSP group each unit is in,
    and its fuel type where one is registered.
  * B1610 (actual output per BM unit): metered MWh per half hour. One request
    returns one settlement period, and the data appears about a week after the day.

Only the groups in config.GSP_GROUPS are fetched, and units are summed per
category before storing, so the table stays small.

Transmission-connected plants (Torness, Whitelee, Peterhead, ...) have no GSP
group in the reference, so config.TRANSMISSION_UNITS assigns them by hand. The
rest is distribution-connected generation and storage, plus the suppliers'
aggregated meter volumes (negative: electricity taken from the grid).
"""

import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from grid.collector import client, config, db

logger = logging.getLogger(__name__)

TZ = ZoneInfo(config.TIMEZONE)
FMT = "%Y-%m-%dT%H:%M:%SZ"
SUPPLIER = "Supplier (net demand)"

_FUEL_CATEGORY = {
    "WIND": "Wind",
    "CCGT": "Gas",
    "OCGT": "Gas",
    "NUCLEAR": "Nuclear",
    "BIOMASS": "Biomass",
    "NPSHYD": "Hydro",
    "PS": "Pumped storage",
}
_STORAGE_WORDS = ("BESS", "BATTERY", "STORAGE")


def categorise(unit: dict) -> str:
    """Display category for a BM unit from the reference list."""
    fuel = unit.get("fuelType")
    name = f"{unit.get('bmUnitName') or ''} {unit.get('elexonBmUnit') or ''}".upper()
    if fuel in (None, "OTHER") and any(w in name for w in _STORAGE_WORDS):
        return "Battery"
    if fuel:
        return _FUEL_CATEGORY.get(fuel, "Other")
    # No fuel registered: an embedded generator of unknown type, or a supplier /
    # virtual lead party meter aggregate (consumption).
    return "Other" if unit.get("bmUnitType") == "E" else SUPPLIER


def load_units() -> dict:
    """{bm unit id: (gsp letter, category)} for the configured groups."""
    wanted = {f"_{letter}": letter for letter in config.GSP_GROUPS}
    manual = {
        unit: letter
        for letter, ids in config.TRANSMISSION_UNITS.items()
        if letter in config.GSP_GROUPS
        for unit in ids
    }
    out, seen = {}, set()
    for u in client.get_json(f"{config.ELEXON_BASE}/reference/bmunits/all", {"format": "json"}):
        unit_id = u.get("elexonBmUnit")
        if not unit_id:
            continue
        letter = wanted.get(u.get("gspGroupId")) or manual.get(unit_id)
        if letter:
            out[unit_id] = (letter, categorise(u))
            seen.add(unit_id)
    missing = sorted(set(manual) - seen)
    if missing:
        logger.warning("TRANSMISSION_UNITS not in the BM unit reference: %s", ", ".join(missing))
    return out


def period_start_utc(day: date, period: int) -> str:
    """UTC start of a settlement period (period 1 starts at UK-local midnight)."""
    midnight = datetime.combine(day, time(0, 0), tzinfo=TZ).astimezone(timezone.utc)
    return (midnight + timedelta(minutes=30 * (period - 1))).strftime(FMT)


def periods_in_day(day: date) -> int:
    """48 normally, 46 or 50 on the clock-change days."""
    start = datetime.combine(day, time(0, 0), tzinfo=TZ).astimezone(timezone.utc)
    end = datetime.combine(day + timedelta(days=1), time(0, 0), tzinfo=TZ).astimezone(timezone.utc)
    return int((end - start).total_seconds() // 1800)


def _fetch_period(day: date, period: int, unit_ids: list) -> list:
    body = client.get_json(
        f"{config.ELEXON_BASE}/datasets/B1610",
        {
            "settlementDate": day.isoformat(),
            "settlementPeriod": period,
            "bmUnit": unit_ids,
            "format": "json",
        },
    )
    return body.get("data", [])


def collect_day(conn, day: date, units: dict) -> int:
    """Fetch and store one settlement day. Returns rows written (0 if not published yet)."""
    unit_ids = sorted(units)
    # B1610 is published late; one cheap request tells us whether the day exists.
    if not _fetch_period(day, 1, unit_ids):
        logger.info("B1610 for %s not published yet", day)
        return 0
    periods = list(range(1, periods_in_day(day) + 1))
    with ThreadPoolExecutor(max_workers=config.GSP_WORKERS) as pool:
        fetched = list(pool.map(lambda p: _fetch_period(day, p, unit_ids), periods))
    rows = []
    for period, records in zip(periods, fetched):
        sums = {}
        for rec in records:
            group_cat = units.get(rec["bmUnit"])
            if group_cat is None or rec.get("quantity") is None:
                continue
            total, count = sums.get(group_cat, (0.0, 0))
            sums[group_cat] = (total + rec["quantity"], count + 1)
        ts = period_start_utc(day, period)
        rows += [
            {
                "ts_utc": ts,
                "gsp_group": group,
                "category": category,
                "mwh": round(total, 3),
                "units": count,
                "settlement_date": day.isoformat(),
                "settlement_period": period,
            }
            for (group, category), (total, count) in sums.items()
        ]
    with conn:
        written = db.upsert(conn, "gsp_generation", rows)
    logger.info("GSP generation %s: %d rows", day, written)
    return written


def _stored_days(conn, start: date, end: date) -> set:
    rows = conn.execute(
        "SELECT DISTINCT settlement_date FROM gsp_generation WHERE settlement_date BETWEEN ? AND ?",
        (start.isoformat(), end.isoformat()),
    )
    return {r[0] for r in rows}


def collect(conn, start: date, end: date, refetch: bool = False) -> int:
    """Fetch settlement days start..end. Days already stored are skipped unless refetch."""
    units = load_units()
    if not units:
        raise RuntimeError("BM unit reference returned no units for the configured GSP groups")
    have = set() if refetch else _stored_days(conn, start, end)
    written = 0
    day = start
    while day <= end:
        if day.isoformat() not in have:
            written += collect_day(conn, day, units)
        day += timedelta(days=1)
    return written
