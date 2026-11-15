#!/usr/bin/env python3
"""
Prime Hunter Script
Finds prime numbers starting from a range defined in the Config sheet and logs results.

Parameters (from Google Sheet Config):
- Parameter-1: Starting integer (inclusive)
- Parameter-2: Ending integer (inclusive)
"""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from utils.control_panel import ControlPanel
from utils.script_db import connect

# Parameters shown as form fields in Pi Control (see utils/params.py).
PARAMS = [
    {"name": "start", "label": "Start (inclusive)", "type": "int", "required": True},
    {"name": "end", "label": "End (inclusive)", "type": "int", "required": True},
]


def find_primes(start: int, end: int) -> list:
    """
    Find all primes between start and end (inclusive).
    
    Args:
        start: Starting integer
        end: Ending integer
        
    Returns:
        List of prime numbers found
    """
    if start < 2:
        start = 2
    
    primes = []
    for num in range(start, end + 1):
        is_prime = all(num % i != 0 for i in range(2, int(num ** 0.5) + 1))
        if is_prime:
            primes.append(num)
    return primes


def store_primes(primes: list):
    """
    Save primes to the 'primes' table in data/prime_hunter.db (duplicates ignored).

    Returns:
        Number of primes not seen before, or None if the database was unavailable
        (a database problem must not fail the run).
    """
    try:
        db = connect("prime_hunter")
        try:
            with db:
                db.execute(
                    "CREATE TABLE IF NOT EXISTS primes ("
                    "n INTEGER PRIMARY KEY, first_found TEXT NOT NULL)"
                )
                before = db.execute("SELECT COUNT(*) FROM primes").fetchone()[0]
                db.executemany(
                    "INSERT OR IGNORE INTO primes (n, first_found) VALUES (?, ?)",
                    [(p, datetime.now().strftime("%Y-%m-%d %H:%M:%S")) for p in primes],
                )
                after = db.execute("SELECT COUNT(*) FROM primes").fetchone()[0]
        finally:
            db.close()
        return after - before
    except Exception:
        return None


def main(params=None):
    """
    Main entry point for Prime Hunter.

    Args:
        params: dict with "start" and "end" (from Pi Control / run_script.py). When None
            the values are read from the Config sheet, as the Sheet runner expects.

    Returns:
        Tuple of (success: bool, message: str, details: str)
    """
    try:
        if params is None:
            # Initialize Control Panel to read parameters
            panel = ControlPanel(spreadsheet_name="RaspPI-Remote-Worker")

            # Read parameters from Config sheet
            sheet_params = panel.get_script_parameters_list("prime_hunter.py")

            # Both are required
            if len(sheet_params) < 2:
                return (False, "Missing parameters", f"Expected 2 parameters, got {len(sheet_params)}: {sheet_params}")

            params = {"start": sheet_params[0], "end": sheet_params[1]}

        if params.get("start") is None or params.get("end") is None:
            return (False, "Missing parameters", f"Expected start and end, got: {params}")

        start = int(params["start"])
        end = int(params["end"])
        
        # Find primes in the specified range
        primes = find_primes(start, end)

        message = f"Found {len(primes)} primes between {start} and {end}"
        new_count = store_primes(primes)
        if new_count is not None:
            message += f" ({new_count} new stored)"
        
        # Record all primes in details
        details = f"Primes: {primes}"
        
        return (True, message, details)
        
    except Exception as e:
        return (False, "Error finding primes", str(e))


if __name__ == "__main__":
    main()