#!/usr/bin/env python3
"""
Prime Hunter Script


Parameters (from Google Sheet Config):
- Parameter-1: Starting integer (inclusive)
- Parameter-2: Ending integer (inclusive)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from utils.control_panel import ControlPanel, ScriptStatus


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
    # Initialize Control Panel
    panel = ControlPanel(spreadsheet_name="RaspPI-Remote-Worker")
    
    # Read parameters from Config sheet
    params = panel.get_script_parameters_list("prime_hunter")
    
    # Set defaults if parameters are missing
    start = int(params[0]) if len(params) > 0 else 100
    end = int(params[1]) if len(params) > 1 else 200
    
    # Define the actual script logic
    def execution_func():
        try:
            # Find primes in the specified range
            primes = find_primes(start, end)
            
            message = f"Found {len(primes)} primes between {start} and {end}"
            
            # Format details: show first 5 primes and last 5 primes if there are many
            if len(primes) <= 10:
                details = f"Primes: {primes}"
            else:
                first_five = primes[:5]
                last_five = primes[-5:]
                details = f"First 5: {first_five} ... Last 5: {last_five} (Total: {len(primes)})"
            
            return (True, message, details)
        except Exception as e:
            return (False, "Error finding primes", str(e))
    
    # Execute with full lifecycle management
    success = panel.execute_script_lifecycle(
        script_name="prime_hunter",
        execution_func=execution_func
    )
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())