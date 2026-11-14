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

TIMEZONE = "Europe/London"

HTTP_TIMEOUT_S = 30
HTTP_ATTEMPTS = 3
HTTP_BACKOFF_S = (2, 6)  # wait before the 2nd and 3rd attempt

# Elexon settlement dates re-fetched by each run (yesterday and today), because
# recent settlement data is revised after first publication.
ELEXON_TRAILING_DAYS = 2

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
