"""
Demo All Params Script
Has one field of every type and echoes back what it received.
"""

import json

PARAMS = [
    {"name": "text", "label": "Text", "type": "str", "default": "hello"},
    {"name": "count", "label": "Whole number (1-10)", "type": "int", "default": 3, "min": 1, "max": 10},
    {"name": "ratio", "label": "Number (0-1)", "type": "float", "default": 0.5, "min": 0, "max": 1},
    {"name": "enabled", "label": "Switch", "type": "bool", "default": True},
    {"name": "day", "label": "Date", "type": "date"},
    {"name": "mode", "label": "Choice", "type": "choice", "options": ["fast", "normal", "careful"], "default": "normal"},
    {"name": "required_note", "label": "Required text", "type": "str", "required": True},
]


def main(params=None):
    params = params or {}
    return (True, "Received parameters", json.dumps(params, indent=2, sort_keys=True))
