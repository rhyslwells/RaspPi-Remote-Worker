"""
Demo Crash Script
Raises an exception. Shows that a crashing script becomes a failed run.
"""


def main(params=None):
    raise RuntimeError("demo crash")
