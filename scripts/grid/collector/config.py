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

# GSP groups whose metered generation is collected (the letters match the Agile
# regions). Each added group adds roughly 400 rows a day, so keep this short.
GSP_GROUPS = {"N": "Southern Scotland", "P": "Northern Scotland"}

# Transmission-connected plants have no GSP group in Elexon's BM unit reference,
# so they are assigned by hand, by where the plant connects onshore (N is the
# SP Distribution area; P is the SSEN Hydro area, which includes Argyll, the
# Highlands, Moray, Aberdeenshire, Tayside and the islands). Fuel comes from the
# reference. Review this list: it is a judgement, not Elexon data.
TRANSMISSION_UNITS = {
    "N": [
        # Nuclear
        "T_TORN-1", "T_TORN-2",
        # Onshore wind: Ayrshire, Lanarkshire, Dumfries and Galloway, Borders, Lothians
        "T_WHILW-1", "T_WHILW-2", "T_ARCHW-1", "T_BLLA-1", "T_BLLA-2", "T_CLDCW-1", "T_CLDNW-1",
        "T_CLDSW-1", "T_DRSLW-1", "T_HADHW-1", "T_HRSTW-1", "T_KLGLW-1", "T_KLGLW-2", "T_KPMRW-1",
        "T_KYPEW-1", "T_MKHLW-1", "T_NOKYW-1", "T_NOKYW-2", "T_SOKYW-1", "T_ENHLW-1", "T_FALGW-1",
        "T_CRYRW-2", "T_CRYRW-4", "T_DNLWW-1", "T_AKGLW-2", "T_AKGLW-3", "T_TDBNW-1", "T_WHIHW-1",
        "T_HAGHW-2", "T_HAHAW-1", "T_DOUGW-1", "T_DWEXW-1", "T_DALQW-1", "T_CUMHW-1", "T_CUMHW-2",
        "T_KENNW-1", "T_MIDMW-1", "T_GLWSW-1", "T_GNAPW-1", "T_AFTOW-1", "T_BENBW-1", "T_BLKWW-1",
        "T_CRDEW-1", "T_CRDEW-2", "T_EWHLW-1", "T_PLOEW-1", "T_PRSTW-1", "T_SANQW-1", "T_SAKNW-1",
        "T_WDRGW-1", "T_WISTW-2", "T_MYGPW-1", "T_BROCW-1", "T_TWSHW-1",
        # Offshore wind connecting in East Lothian
        "T_NNGAO-1", "T_NNGAO-2", "T_INCWO-1", "T_INCWO-2", "T_INCWO-3", "T_INCWO-4",
        # Batteries
        "T_COALB-1", "T_COALB-2", "T_COALB-3", "T_COALB-4", "T_COALB-5", "T_COYLB-1", "T_NLSTB-1",
        "T_WISHB-1", "T_HRSTB-1",
    ],
    "P": [
        # Gas, pumped storage
        "T_PEHE-1", "T_CRUA-1", "T_CRUA-2", "T_CRUA-3", "T_CRUA-4", "T_FOYE-1", "T_FOYE-2",
        # Hydro
        "M_CAS-BEU01", "M_CAS-CLU01", "M_CAS-CON01", "M_CAS-GAR01", "M_CAS-KIL01", "M_CAS-MOR01",
        "M_SLOY-1", "M_SLOY-4", "T_SLOY-2", "T_SLOY-3", "T_ERRO-1", "T_ERRO-2", "T_ERRO-3",
        "T_FASN-1", "T_FASN-2", "T_FINL-1", "T_GLNDO-1", "T_NANT-1",
        # Onshore wind
        "T_ACHRW-1", "T_BDCHW-1", "T_BEINW-1", "T_BHLAW-1", "T_CGTHW-1", "T_COUWW-1", "T_CREAW-1",
        "T_CRGHW-1", "T_CRMLW-1", "T_DOREW-1", "T_DOREW-2", "T_DUNGW-1", "T_EDINW-1", "T_FARR-1",
        "T_FARR-2", "T_FSDLW-1", "T_GLNKW-1", "T_GORDW-1", "T_GORDW-2", "T_HALSW-1", "T_KILBW-1",
        "T_LCLTW-1", "T_LIMKW-1", "T_MILWW-1", "T_STLGW-1", "T_STLGW-2", "T_STLGW-3", "T_STRNW-1",
        "T_VKNGW-1", "T_VKNGW-2", "T_VKNGW-3", "T_VKNGW-4",
        # Offshore wind
        "T_ABRBO-1", "T_BEATO-1", "T_BEATO-2", "T_BEATO-3", "T_BEATO-4", "T_MOWEO-1", "T_MOWEO-2",
        "T_MOWEO-3", "T_MOWWO-1", "T_MOWWO-2", "T_MOWWO-3", "T_MOWWO-4", "T_SGRWO-1", "T_SGRWO-2",
        "T_SGRWO-3", "T_SGRWO-4", "T_SGRWO-5", "T_SGRWO-6",
        # Batteries
        "T_BLHLB-1", "T_BLHLB-2", "T_BLHLB-3", "T_BLHLB-4",
    ],
}

# Parallel requests per settlement day (Elexon answers one period per request).
GSP_WORKERS = 4

# Raw half-hourly tables keep only this many days. The daily roll-ups
# (daily_summary, agile_daily) are kept, so the History page still shows a year.
RETENTION_DAYS = 30
RUN_HISTORY_DAYS = 90  # collector_runs

# Elexon publishes B1610 (actual output per BM unit) about a week late. The
# daily gsp job looks at settlement days from GSP_LOOKBACK_DAYS ago up to
# GSP_LAG_DAYS ago and fetches the ones not stored yet.
GSP_LAG_DAYS = 3
GSP_LOOKBACK_DAYS = 14

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
