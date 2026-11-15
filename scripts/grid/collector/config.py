"""
Collector settings. Environment variables override the defaults, so nothing
needs editing on the Pi to change region or product.

    GRID_AGILE_PRODUCT   default AGILE-24-10-01 (Octopus replaces product codes
                         from time to time; check https://api.octopus.energy/v1/products/)
"""

import os
from pathlib import Path

ELEXON_BASE = "https://data.elexon.co.uk/bmrs/api/v1"
OCTOPUS_BASE = "https://api.octopus.energy/v1"

AGILE_PRODUCT = os.environ.get("GRID_AGILE_PRODUCT", "AGILE-24-10-01")

# Agile distribution regions (no I or O). N = Southern Scotland (Edinburgh).
REGIONS = list("ABCDEFGHJKLMNP")
DEFAULT_REGION = "N"

REGION_NAMES = {
    "A": "Eastern England", "B": "East Midlands", "C": "London",
    "D": "Merseyside and North Wales", "E": "West Midlands", "F": "North East England",
    "G": "North West England", "H": "Southern England", "J": "South East England",
    "K": "South Wales", "L": "South Western England", "M": "Yorkshire",
    "N": "Southern Scotland", "P": "Northern Scotland",
}

TIMEZONE = "Europe/London"

HTTP_TIMEOUT_S = 30
HTTP_ATTEMPTS = 3
HTTP_BACKOFF_S = (2, 6)  # wait before the 2nd and 3rd attempt

# Elexon settlement dates re-fetched by each run (yesterday and today), because
# recent settlement data is revised after first publication.
ELEXON_TRAILING_DAYS = 2

# Weekly backups of grid.db to data/backups/ (backup job); newest N kept.
BACKUPS_KEPT = 4

# Jobs that ping GRID_HEARTBEAT_URL (if set) on success. One is enough to prove
# the Pi is alive and collecting.
HEARTBEAT_JOBS = {"elexon"}

LOG_DIR = Path(__file__).resolve().parents[3] / "logs"
LOCK_DIR = Path(__file__).resolve().parents[3] / "data"
LOCK_STALE_S = 15 * 60

# Fuel groupings used by the summary. Raw fuel types are stored; this only
# controls the roll-up columns.
FUEL_GROUPS = {
    "wind": {"WIND"},
    "gas": {"CCGT", "OCGT"},
    "nuclear": {"NUCLEAR"},
    "biomass": {"BIOMASS"},
}
IMPORT_PREFIX = "INT"  # INTFR, INTNED, ... (interconnector flows, net)
