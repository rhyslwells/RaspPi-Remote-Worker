#!/usr/bin/env python3
"""
Prime Hunter Script
Finds prime numbers starting from a range defined in the Config sheet and logs results.

Parameters (from Google Sheet Config):
- Parameter-1: Starting integer (inclusive)
- Parameter-2: Ending integer (inclusive)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from utils.control_panel import ControlPanel


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
        
        # Record all primes in details
        details = f"Primes: {primes}"
        
        return (True, message, details)
        
    except Exception as e:
        return (False, "Error finding primes", str(e))


if __name__ == "__main__":
    main()