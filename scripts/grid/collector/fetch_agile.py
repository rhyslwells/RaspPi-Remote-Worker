"""Fetch Octopus Agile unit rates for every region and upsert them."""

import logging
from datetime import datetime

from grid.collector import client, config, db

logger = logging.getLogger(__name__)


def _fetch_region(region: str, product: str, start: datetime, end: datetime) -> list:
    url = (
        f"{config.OCTOPUS_BASE}/products/{product}/electricity-tariffs/"
        f"E-1R-{product}-{region}/standard-unit-rates/"
    )
    params = {
        "period_from": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "period_to": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "page_size": 1500,
    }
    rows = []
    # `next` is a full URL carrying the original query; follow it without params.
    body = client.get_json(url, params)
    while True:
        for r in body["results"]:
            rows.append(
                {
                    "valid_from_utc": r["valid_from"],
                    "region": region,
                    "product": product,
                    "valid_to_utc": r["valid_to"],
                    "inc_vat_p_kwh": r["value_inc_vat"],
                    "exc_vat_p_kwh": r.get("value_exc_vat"),
                }
            )
        if not body.get("next"):
            return rows
        body = client.get_json(body["next"])


def collect(conn, start: datetime, end: datetime, regions=None) -> int:
    """
    Fetch rates with a UTC window start..end for the given regions (default all)
    and upsert them in one transaction. A region that fails is logged and skipped
    so one bad region does not lose the rest; the failure is raised afterwards so
    the run is recorded as failed.
    """
    regions = regions or config.REGIONS
    rows, failed = [], []
    for region in regions:
        try:
            rows += _fetch_region(region, config.AGILE_PRODUCT, start, end)
        except Exception as exc:
            logger.error("Agile region %s failed: %s", region, exc)
            failed.append(region)
    with conn:
        written = db.upsert(conn, "agile_price", rows)
    logger.info("Agile %s..%s: %d rows, %d regions failed", start, end, written, len(failed))
    if failed:
        raise RuntimeError(f"Agile fetch failed for region(s): {', '.join(failed)}")
    return written
