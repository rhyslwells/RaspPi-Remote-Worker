"""
Demo Confirm Script
Asks "Are you sure?" before it runs, like restart_pi does. Does nothing else.
"""

CONFIRM = "This is a demo of the Are you sure? box. Nothing will happen."


def main(params=None):
    return (True, "Confirmed and ran", "The confirm box worked.")
