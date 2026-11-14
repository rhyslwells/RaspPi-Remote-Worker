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


def main():
    """
    Main entry point for Prime Hunter.
    
    Returns:
        Tuple of (success: bool, message: str, details: str)
    """
    try:
        # Initialize Control Panel to read parameters
        panel = ControlPanel(spreadsheet_name="RaspPI-Remote-Worker")
        
        # Read parameters from Config sheet
        params = panel.get_script_parameters_list("prime_hunter.py")
        
        # Get parameters - both are required
        if len(params) < 2:
            return (False, "Missing parameters", f"Expected 2 parameters, got {len(params)}: {params}")
        
        start = int(params[0])
        end = int(params[1])
        
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