"""Build daily roll-ups from stored rows. No API calls; safe to re-run."""

import logging
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from grid.collector import config, db

logger = logging.getLogger(__name__)

_TZ = ZoneInfo(config.TIMEZONE)
_WINDOW_SLOTS = 4  # cheapest 2 hours = 4 half-hour slots


def uk_today() -> date:
    return datetime.now(_TZ).date()


def _parse(ts: str) -> datetime:
    return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def summarise_day(conn, day: date) -> int:
    """Write daily_summary and agile_daily rows for a UK day. Returns rows written."""
    d = day.isoformat()
    written = 0

    periods = conn.execute(
        "SELECT count(DISTINCT ts_utc) FROM generation WHERE settlement_date=?", (d,)
    ).fetchone()[0]
    if periods:
        by_fuel = {
            r["fuel"]: r["mwh"]
            for r in conn.execute(
                "SELECT fuel, sum(mw) * 0.5 AS mwh FROM generation "
                "WHERE settlement_date=? GROUP BY fuel",
                (d,),
            )
        }
        row = {
            "date": d,
            "periods": periods,
            "gen_total_mwh": sum(by_fuel.values()),
            "gen_imports_mwh": sum(
                v for k, v in by_fuel.items() if k.startswith(config.IMPORT_PREFIX)
            ),
            "updated_at": db.utc_now(),
        }
        for name, fuels in config.FUEL_GROUPS.items():
            row[f"gen_{name}_mwh"] = sum(by_fuel.get(f, 0.0) for f in fuels)

        peak = conn.execute(
            "SELECT ts_utc, indo_mw FROM demand WHERE settlement_date=? "
            "AND indo_mw IS NOT NULL ORDER BY indo_mw DESC LIMIT 1",
            (d,),
        ).fetchone()
        if peak:
            row["demand_peak_mw"], row["demand_peak_ts"] = peak["indo_mw"], peak["ts_utc"]

        sp = conn.execute(
            "SELECT avg(sell_gbp_mwh) a, min(sell_gbp_mwh) lo, max(sell_gbp_mwh) hi, "
            "sum(sell_gbp_mwh < 0) neg FROM system_price WHERE settlement_date=?",
            (d,),
        ).fetchone()
        if sp["a"] is not None:
            row.update(
                sys_avg_gbp_mwh=sp["a"], sys_min_gbp_mwh=sp["lo"],
                sys_max_gbp_mwh=sp["hi"], sys_neg_periods=sp["neg"],
            )
        written += db.upsert(conn, "daily_summary", [row])
    else:
        logger.info("No generation rows for %s, daily_summary skipped", d)

    written += _agile_daily(conn, day)
    return written


def _agile_daily(conn, day: date) -> int:
    # Slots are stored in UTC; pick those starting on this UK-local date.
    lo = (datetime.combine(day, datetime.min.time(), tzinfo=timezone.utc)
          - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    hi = (datetime.combine(day, datetime.min.time(), tzinfo=timezone.utc)
          + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
    groups = {}
    for r in conn.execute(
        "SELECT valid_from_utc, valid_to_utc, region, product, inc_vat_p_kwh "
        "FROM agile_price WHERE valid_from_utc >= ? AND valid_from_utc < ? "
        "ORDER BY region, product, valid_from_utc",
        (lo, hi),
    ):
        if _parse(r["valid_from_utc"]).astimezone(_TZ).date() == day:
            groups.setdefault((r["region"], r["product"]), []).append(r)

    rows = []
    for (region, product), slots in groups.items():
        # A UK day has 46 to 50 slots. Fewer means the day is not fully published
        # or fetched yet; leave it for a later run.
        if len(slots) < 46:
            continue
        prices = [s["inc_vat_p_kwh"] for s in slots]
        best_start, best_avg = None, None
        for i in range(len(slots) - _WINDOW_SLOTS + 1):
            win = slots[i : i + _WINDOW_SLOTS]
            if any(win[j]["valid_to_utc"] != win[j + 1]["valid_from_utc"]
                   for j in range(_WINDOW_SLOTS - 1)):
                continue  # gap in the data, not a real consecutive window
            avg = sum(s["inc_vat_p_kwh"] for s in win) / _WINDOW_SLOTS
            if best_avg is None or avg < best_avg:
                best_start, best_avg = win[0]["valid_from_utc"], avg
        rows.append({
            "date": day.isoformat(), "region": region, "product": product,
            "slots": len(slots), "avg_p_kwh": sum(prices) / len(prices),
            "min_p_kwh": min(prices), "max_p_kwh": max(prices),
            "neg_slots": sum(p < 0 for p in prices),
            "cheapest2h_start_utc": best_start, "cheapest2h_avg_p_kwh": best_avg,
            "updated_at": db.utc_now(),
        })
    return db.upsert(conn, "agile_daily", rows)


def collect(conn, start: date, end: date) -> int:
    """Summarise each UK day start..end inclusive, in one transaction."""
    written = 0
    with conn:
        day = start
        while day <= end:
            written += summarise_day(conn, day)
            day += timedelta(days=1)
    logger.info("Summary %s..%s: %d rows", start, end, written)
    return written
