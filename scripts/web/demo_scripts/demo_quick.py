"""
Demo Quick Script
Finishes straight away with a greeting. Shows a successful run.
"""

PARAMS = [
    {"name": "name", "label": "Who to greet", "type": "str", "default": "world"},
]


def main(params=None):
    name = (params or {}).get("name") or "world"
    return (True, f"Hello, {name}", "Nothing was changed.")
