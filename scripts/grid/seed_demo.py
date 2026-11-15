#!/usr/bin/env python3
"""
Fill a demo grid database with synthetic data so the dashboard can be tested
without network access or the real collector.

The data is made up (plausible shapes, not real figures). It is written to
data/grid_demo.db, which is gitignored, and never to data/grid.db unless you pass
--db explicitly. Run from the repo root:

    python scripts/grid/seed_demo.py [--days 14] [--db data/grid_demo.db]
    GRID_DB=data/grid_demo.db python scripts/grid/dashboard/app.py
"""

import argparse
import math
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from grid.collector import config, db, summarise  # noqa: E402

TZ = ZoneInfo(config.TIMEZONE)
STEP = timedelta(minutes=30)
FMT = "%Y-%m-%dT%H:%M:%SZ"


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime(FMT)


def settlement(ts: datetime):
    """UK settlement date and period number for a UTC half-hour start."""
    local = ts.astimezone(TZ)
    start_local = datetime.combine(local.date(), datetime.min.time(), tzinfo=TZ)
    period = int((ts - start_local.astimezone(timezone.utc)) / STEP) + 1
    return local.date().isoformat(), period


def build(days: int, seed: int = 42):
    rng = random.Random(seed)
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    if datetime.now(timezone.utc).minute >= 30:
        now += STEP
    uk_today = datetime.now(TZ).date()
    first_local = datetime.combine(uk_today - timedelta(days=days - 1), datetime.min.time(), tzinfo=TZ)
    ts = first_local.astimezone(timezone.utc)

    gen, dem, prices = [], [], []
    wind = 8000.0
    while ts < now - STEP:  # last complete period
        hour = ts.astimezone(TZ).hour + ts.astimezone(TZ).minute / 60
        # Two-peak daily demand shape, lower at weekends.
        shape = 0.55 + 0.25 * math.exp(-((hour - 8) ** 2) / 8) + 0.45 * math.exp(-((hour - 18) ** 2) / 6)
        weekend = 0.93 if ts.astimezone(TZ).weekday() >= 5 else 1.0
        demand = 40000 * shape * weekend * (1 + rng.uniform(-0.02, 0.02))
        wind = min(16000, max(800, wind + rng.gauss(0, 450)))
        nuclear, biomass, hydro = 4700 + rng.uniform(-100, 100), 2500 + rng.uniform(-80, 80), 400 + rng.uniform(-40, 40)
        imports = {"INTFR": 1500, "INTNED": 900, "INTNSL": 1100, "INTIRL": -300, "INTEW": -200}
        imports = {k: v + rng.uniform(-150, 150) for k, v in imports.items()}
        residual = demand + 600 - wind - nuclear - biomass - hydro - sum(imports.values())
        ccgt = max(150.0, residual * 0.93)
        ocgt = max(0.0, residual - ccgt - 50)
        sd, sp = settlement(ts)
        stamp = iso(ts)
        published = iso(ts + STEP)
        fuels = {"WIND": wind, "CCGT": ccgt, "OCGT": ocgt, "NUCLEAR": nuclear, "BIOMASS": biomass,
                 "NPSHYD": hydro, "PS": rng.uniform(-300, 300), "OTHER": 250.0, "COAL": 0.0, "OIL": 0.0, **imports}
        for fuel, mw in fuels.items():
            gen.append(dict(ts_utc=stamp, fuel=fuel, mw=round(mw, 1), settlement_date=sd,
                            settlement_period=sp, published_at=published))
        dem.append(dict(ts_utc=stamp, indo_mw=round(demand), itsdo_mw=round(demand + 1800),
                        settlement_date=sd, settlement_period=sp, published_at=published))
        # Price falls as wind rises, occasionally goes negative when it is very windy.
        price = 140 + 0.012 * (demand - 30000) - 0.011 * (wind - 8000) + rng.gauss(0, 12)
        if wind > 14500 and rng.random() < 0.3:
            price = rng.uniform(-40, -2)
        prices.append(dict(ts_utc=stamp, sell_gbp_mwh=round(price, 2), buy_gbp_mwh=round(price, 2),
                           net_imbalance_mwh=round(rng.gauss(0, 400), 1), settlement_date=sd, settlement_period=sp))
        ts += STEP

    # Agile: 23:00 UK to 23:00 UK next day is published; cover from the first day to tomorrow.
    agile = []
    ts = first_local.astimezone(timezone.utc)
    end = datetime.combine(uk_today + timedelta(days=1), datetime.min.time(), tzinfo=TZ).astimezone(timezone.utc) + timedelta(hours=23)
    base_noise = {}
    while ts < end:
        hour = ts.astimezone(TZ).hour + ts.astimezone(TZ).minute / 60
        peak = 32 if 16 <= hour < 19 else 0
        trough = -14 if 1 <= hour < 5 else 0
        for i, region in enumerate(config.REGIONS):
            key = (ts.date(), region)
            noise = base_noise.setdefault(key, rng.gauss(0, 3))
            p = 24 + peak + trough + (i - 6) * 0.4 + noise + 4 * math.sin(ts.timetuple().tm_yday + hour / 3)
            if 2 <= hour < 4 and rng.random() < 0.04:
                p = rng.uniform(-8, -0.5)
            p = round(p, 2)
            agile.append(dict(valid_from_utc=iso(ts), region=region, product=config.AGILE_PRODUCT,
                              valid_to_utc=iso(ts + STEP), inc_vat_p_kwh=p, exc_vat_p_kwh=round(p / 1.05, 2)))
        ts += STEP
    return gen, dem, prices, agile, uk_today


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=14)
    ap.add_argument("--db", type=Path, default=db.DATA_DIR / "grid_demo.db")
    args = ap.parse_args()
    if args.db.resolve() == (db.DATA_DIR / "grid.db").resolve() and args.db.exists():
        print("Refusing to overwrite the real grid.db with demo data.", file=sys.stderr)
        return 1
    if args.db.exists():
        args.db.unlink()
        for ext in ("-wal", "-shm"):
            Path(str(args.db) + ext).unlink(missing_ok=True)

    gen, dem, prices, agile, uk_today = build(args.days)
    conn = db.connect(args.db)
    with conn:
        db.upsert(conn, "generation", gen)
        db.upsert(conn, "demand", dem)
        db.upsert(conn, "system_price", prices)
        db.upsert(conn, "agile_price", agile)
    first = uk_today - timedelta(days=args.days - 1)
    summarise.collect(conn, first, uk_today)
    now = db.utc_now()
    for job, rows in (("elexon", 2000), ("agile", 2700), ("summary", 15)):
        db.record_run(conn, job, now, 2.0, True, rows)
    counts = {t: conn.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
              for t in ("generation", "demand", "system_price", "agile_price", "daily_summary", "agile_daily")}
    conn.close()
    print(f"Demo database written to {args.db}\n{counts}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
