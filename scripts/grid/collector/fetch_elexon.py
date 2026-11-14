"""Fetch Elexon generation, demand and system prices and upsert them."""

import logging
from datetime import date, timedelta

from grid.collector import client, config, db

logger = logging.getLogger(__name__)

# FUELHH and demand accept a date range; chunk long backfills.
CHUNK_DAYS = 7


def _generation_rows(data: list) -> list:
    return [
        {
            "ts_utc": r["startTime"],
            "fuel": r["fuelType"],
            "mw": r["generation"],
            "settlement_date": r["settlementDate"],
            "settlement_period": r["settlementPeriod"],
            "published_at": r.get("publishTime"),
        }
        for r in data
        if r.get("generation") is not None
    ]


def _demand_rows(data: list) -> list:
    return [
        {
            "ts_utc": r["startTime"],
            "indo_mw": r.get("initialDemandOutturn"),
            "itsdo_mw": r.get("initialTransmissionSystemDemandOutturn"),
            "settlement_date": r["settlementDate"],
            "settlement_period": r["settlementPeriod"],
            "published_at": r.get("publishTime"),
        }
        for r in data
    ]


def _price_rows(data: list) -> list:
    return [
        {
            "ts_utc": r["startTime"],
            "sell_gbp_mwh": r.get("systemSellPrice"),
            "buy_gbp_mwh": r.get("systemBuyPrice"),
            "net_imbalance_mwh": r.get("netImbalanceVolume"),
            "settlement_date": r["settlementDate"],
            "settlement_period": r["settlementPeriod"],
        }
        for r in data
    ]


def _chunks(start: date, end: date):
    while start <= end:
        stop = min(start + timedelta(days=CHUNK_DAYS - 1), end)
        yield start, stop
        start = stop + timedelta(days=1)


def collect(conn, start: date, end: date) -> int:
    """
    Fetch settlement dates start..end inclusive and upsert them in one transaction.
    Everything is fetched before anything is written, so a failed call leaves the
    database untouched. Returns the number of rows written.
    """
    gen, dem, prices = [], [], []
    for lo, hi in _chunks(start, end):
        params = {
            "settlementDateFrom": lo.isoformat(),
            "settlementDateTo": hi.isoformat(),
            "format": "json",
        }
        gen += _generation_rows(
            client.get_json(f"{config.ELEXON_BASE}/datasets/FUELHH", params)["data"]
        )
        dem += _demand_rows(
            client.get_json(f"{config.ELEXON_BASE}/demand/outturn", params)["data"]
        )
    day = start
    while day <= end:
        body = client.get_json(
            f"{config.ELEXON_BASE}/balancing/settlement/system-prices/{day.isoformat()}",
            {"format": "json"},
        )
        prices += _price_rows(body["data"])
        day += timedelta(days=1)

    with conn:
        written = (
            db.upsert(conn, "generation", gen)
            + db.upsert(conn, "demand", dem)
            + db.upsert(conn, "system_price", prices)
        )
    logger.info(
        "Elexon %s..%s: generation=%d demand=%d system_price=%d",
        start, end, len(gen), len(dem), len(prices),
    )
    return written
