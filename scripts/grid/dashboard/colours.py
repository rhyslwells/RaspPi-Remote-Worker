"""Fuel groups and one colour per group, used by every chart."""

# Raw Elexon fuel types are stored; the dashboard groups them for display.
GROUPS = {
    "Wind": {"WIND"},
    "Gas": {"CCGT", "OCGT"},
    "Nuclear": {"NUCLEAR"},
    "Biomass": {"BIOMASS"},
    "Hydro": {"NPSHYD"},
    "Pumped storage": {"PS"},
    "Other": {"OTHER", "COAL", "OIL"},
}
IMPORTS = "Interconnectors (net)"  # every fuel starting with INT

# Draw order, bottom to top.
ORDER = ["Nuclear", "Biomass", "Hydro", "Wind", "Gas", "Other", "Pumped storage", IMPORTS]

COLOURS = {
    "Nuclear": "#7e57c2",
    "Biomass": "#8d6e63",
    "Hydro": "#26a69a",
    "Wind": "#42a5f5",
    "Gas": "#ef6c00",
    "Other": "#9e9e9e",
    "Pumped storage": "#ec407a",
    IMPORTS: "#cfae2b",
}

AGILE = "#00897b"
SYSTEM_PRICE = "#5c6bc0"
NEGATIVE = "#d32f2f"

ATTRIBUTION = "Contains BMRS data © Elexon Limited copyright and database right."

_LOOKUP = {fuel: group for group, fuels in GROUPS.items() for fuel in fuels}


def group_of(fuel: str) -> str:
    if fuel.startswith("INT"):
        return IMPORTS
    return _LOOKUP.get(fuel, "Other")
