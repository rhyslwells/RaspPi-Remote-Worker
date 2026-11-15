"""
Demo Slow Script
Prints a line every second for a chosen time. Use it to watch live output or press Stop.
"""

import time

PARAMS = [
    {"name": "seconds", "label": "How long (seconds)", "type": "int",
     "default": 20, "min": 1, "max": 300},
]


def main(params=None):
    seconds = int((params or {}).get("seconds") or 20)
    for i in range(1, seconds + 1):
        print(f"working... {i}/{seconds}", flush=True)
        time.sleep(1)
    return (True, f"Finished after {seconds}s", "Slow demo complete.")
