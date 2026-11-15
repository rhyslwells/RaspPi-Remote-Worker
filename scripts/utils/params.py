#!/usr/bin/env python3
"""
Parameter declarations for task scripts (standard library only).

A script may declare the parameters it accepts at module level:

    PARAMS = [
        {"name": "start", "label": "Start", "type": "int", "required": True},
        {"name": "dry_run", "label": "Dry run", "type": "bool", "default": False},
    ]

Pi Control builds its form from this list and ``run_script.py`` validates the values
with ``coerce_params`` before calling ``main(params)``. Values may arrive as strings
(the Google Sheet, a form) or already typed (JSON); both are accepted.

Supported types: str, int, float, bool, date (YYYY-MM-DD), choice (needs "options").
Optional keys per field: label, default, required (default False), min, max (int and
float), options (choice).
"""

from datetime import date
from typing import Any, Dict, List, Optional, Tuple

TYPES = ("str", "int", "float", "bool", "date", "choice")

_TRUE = {"true", "1", "yes", "y", "on"}
_FALSE = {"false", "0", "no", "n", "off", ""}


def _coerce_value(spec: Dict[str, Any], raw: Any) -> Any:
    """Convert one raw value to the field's type. Raises ValueError with a short reason."""
    kind = spec.get("type", "str")
    if kind not in TYPES:
        raise ValueError(f"unknown type {kind!r}")

    if kind == "str":
        return str(raw).strip()

    if kind == "bool":
        if isinstance(raw, bool):
            return raw
        text = str(raw).strip().lower()
        if text in _TRUE:
            return True
        if text in _FALSE:
            return False
        raise ValueError("must be true or false")

    if kind in ("int", "float"):
        noun = "a whole number" if kind == "int" else "a number"
        if isinstance(raw, bool):
            raise ValueError(f"must be {noun}")
        try:
            value = int(str(raw).strip()) if kind == "int" else float(str(raw).strip())
        except ValueError:
            raise ValueError(f"must be {noun}") from None
        if "min" in spec and value < spec["min"]:
            raise ValueError(f"must be at least {spec['min']}")
        if "max" in spec and value > spec["max"]:
            raise ValueError(f"must be at most {spec['max']}")
        return value

    if kind == "date":
        text = str(raw).strip()
        try:
            return date.fromisoformat(text).isoformat()
        except ValueError:
            raise ValueError("must be a date as YYYY-MM-DD") from None

    # choice
    text = str(raw).strip()
    options = [str(o) for o in spec.get("options", [])]
    if text not in options:
        raise ValueError(f"must be one of: {', '.join(options)}")
    return text


def _is_blank(raw: Any) -> bool:
    return raw is None or (isinstance(raw, str) and raw.strip() == "")


def coerce_params(
    specs: Optional[List[Dict[str, Any]]], raw: Optional[Dict[str, Any]]
) -> Tuple[Dict[str, Any], List[str]]:
    """
    Validate and convert raw parameter values against a PARAMS list.

    Returns ``(values, errors)``. ``values`` holds every declared name (defaults filled
    in, None when blank and optional). ``errors`` is a list of readable messages; when
    it is not empty the values must not be used. Names not declared are errors, so a
    typo cannot silently be ignored.
    """
    specs = specs or []
    raw = dict(raw or {})
    values: Dict[str, Any] = {}
    errors: List[str] = []

    declared = {s["name"] for s in specs}
    for extra in sorted(set(raw) - declared):
        errors.append(f"{extra}: not a parameter of this script")

    for spec in specs:
        name = spec["name"]
        label = spec.get("label", name)
        value = raw.get(name)
        if _is_blank(value):
            value = spec.get("default")
        if _is_blank(value):
            if spec.get("required"):
                errors.append(f"{label}: required")
            values[name] = None
            continue
        try:
            values[name] = _coerce_value(spec, value)
        except ValueError as e:
            errors.append(f"{label}: {e}")

    return values, errors
