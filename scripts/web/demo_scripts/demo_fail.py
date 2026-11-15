"""
Demo Fail Script
Always reports an expected failure. Shows how a failed run looks.
"""


def main(params=None):
    return (False, "This demo always fails", "Expected failures are returned, not raised.")
