"""
Demo Loop Script
Never finishes by itself: it prints a heartbeat until stopped. Use it to try Stop.
"""

import time

TIMEOUT_S = 600  # a demo should not run forever if you forget it


def main(params=None):
    n = 0
    while True:
        n += 1
        print(f"heartbeat {n}", flush=True)
        time.sleep(2)
