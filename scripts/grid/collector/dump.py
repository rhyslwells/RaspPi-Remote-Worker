#!/usr/bin/env python3
"""
Phase 0 of the grid project: dump raw API responses and print a field summary.

Standard library only. Makes read-only GET requests to the public Elexon Insights
and Octopus APIs. Touches no database, sheet or Pi service.

Usage (from the repo root):
    python scripts/grid/collector/dump.py --out <dir> [--date YYYY-MM-DD] [--region N]
"""

import argparse
import json
import sys
import urllib.parse
import urllib.request
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ELEXON = "https://data.elexon.co.uk/bmrs/api/v1"
OCTOPUS = "https://api.octopus.energy/v1"
PRODUCT = "AGILE-24-10-01"
TIMEOUT = 30


def get_json(url: str, params: dict = None):
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": "grid-dump/0.1"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.load(resp), dict(resp.headers)


def summarise(name: str, rows: list) -> None:
    print(f"\n== {name}: {len(rows)} rows")
    if not rows:
        return
    print("   fields:", ", ".join(rows[0].keys()))
    print("   first:", json.dumps(rows[0])[:300])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True, help="directory for raw JSON")
    ap.add_argument("--date", default=(date.today() - timedelta(days=2)).isoformat())
    ap.add_argument("--region", default="N")
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    day = args.date
    nxt = (date.fromisoformat(day) + timedelta(days=1)).isoformat()

    sources = {
        "fuelhh": (
            f"{ELEXON}/datasets/FUELHH",
            {"settlementDateFrom": day, "settlementDateTo": day, "format": "json"},
        ),
        "demand": (
            f"{ELEXON}/demand/outturn",
            {"settlementDateFrom": day, "settlementDateTo": day, "format": "json"},
        ),
        "system_prices": (
            f"{ELEXON}/balancing/settlement/system-prices/{day}",
            {"format": "json"},
        ),
        "agile": (
            f"{OCTOPUS}/products/{PRODUCT}/electricity-tariffs/"
            f"E-1R-{PRODUCT}-{args.region}/standard-unit-rates/",
            {
                "period_from": f"{day}T00:00:00Z",
                "period_to": f"{nxt}T00:00:00Z",
                "page_size": 200,
            },
        ),
    }

    failures = 0
    for name, (url, params) in sources.items():
        try:
            body, headers = get_json(url, params)
        except Exception as exc:  # report and carry on with the other sources
            print(f"\n== {name}: FAILED {exc}")
            failures += 1
            continue
        (out / f"{name}.json").write_text(json.dumps(body, indent=1), encoding="utf-8")
        rows = body["data"] if isinstance(body, dict) and "data" in body else body
        if isinstance(body, dict) and "results" in body:
            rows = body["results"]
            print(f"\n(agile pagination: count={body.get('count')} next={body.get('next')})")
        summarise(name, rows)
        rl = {k: v for k, v in headers.items() if "limit" in k.lower() or "remaining" in k.lower()}
        if rl:
            print("   rate headers:", rl)

        if name == "fuelhh":
            periods = {r["settlementPeriod"] for r in rows}
            print("   periods:", len(periods), "fuels:", sorted({r["fuelType"] for r in rows}))
        elif name in ("demand", "system_prices"):
            print("   periods:", len({r["settlementPeriod"] for r in rows}))
        elif name == "agile":
            print("   sample:", rows[:2])

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
