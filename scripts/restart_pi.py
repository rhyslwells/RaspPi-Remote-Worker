#!/usr/bin/env python3
"""
Restart Pi Script
Restarts the runner service, or reboots the whole Pi, from a Config sheet cell.

The restart is SCHEDULED, not immediate: the script returns SUCCESS first so the
runner can record the result, then systemd does the restart a moment later.
(Restarting immediately would kill the runner mid-run and leave the Config row
stuck on RUNNING.)

Parameters (from Google Sheet Config):
- Parameter-1: "service" (default) restarts remote-worker.service in ~15 seconds
               "reboot" reboots the Pi in ~1 minute

Needs passwordless sudo for the service user (the Raspberry Pi OS default).
After "service", the row shows SUCCESS and the runner is briefly offline.
After "reboot", the Pi is offline for about a minute; cancel within the first
minute with `sudo shutdown -c` over SSH.
"""

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from utils.control_panel import ControlPanel

# Parameters shown as form fields in the web UI (see utils/params.py).
DESCRIPTION = (
    "Restarts the Remote Worker runner service, or reboots the whole Pi. The restart is "
    "scheduled a moment after this script finishes, so its result is recorded first. A "
    "reboot takes the Pi offline for about a minute and ends anything that is running, "
    "including this web page until the Pi is back. Needs passwordless sudo."
)
PARAMS = [
    {"name": "mode", "label": "What to restart", "type": "choice",
     "options": ["service", "reboot"], "default": "service",
     "help": "service: restart the runner service in about 15 seconds. reboot: reboot "
             "the Pi in about a minute (cancel within that minute over SSH with "
             "sudo shutdown -c)."},
]
# The web UI asks "Are you sure?" before running this script.
CONFIRM = "This restarts the runner service or reboots the Pi."

SERVICE_NAME = "remote-worker.service"
SERVICE_DELAY_SECONDS = 15
# The systemd unit's PATH is the venv bin only, so use absolute paths.
SUDO = "/usr/bin/sudo"
SYSTEMD_RUN = "/usr/bin/systemd-run"
SYSTEMCTL = "/usr/bin/systemctl"
SHUTDOWN = "/usr/sbin/shutdown"


def _sudo(args: list, timeout: int = 15) -> subprocess.CompletedProcess:
    # -n: never prompt for a password (there is no terminal); fail instead
    return subprocess.run(
        [SUDO, "-n", *args], capture_output=True, text=True, timeout=timeout
    )


def restart(mode: str) -> tuple:
    """Schedule the restart. Returns (success, message, details)."""
    if not sys.platform.startswith("linux"):
        return (False, "Not running on Linux", f"Platform is {sys.platform}; nothing done")

    mode = (mode or "service").strip().lower()
    if mode not in ("service", "reboot"):
        return (False, "Invalid mode", f"Parameter-1 must be 'service' or 'reboot', got: {mode!r}")

    try:
        check = _sudo(["true"])
        if check.returncode != 0:
            return (
                False,
                "sudo needs a password",
                "The service user needs passwordless sudo. "
                f"sudo said: {check.stderr.strip()[:200]}",
            )

        if mode == "service":
            # A transient timer runs outside the service's cgroup, so it survives
            # the service being stopped and started again.
            result = _sudo([
                SYSTEMD_RUN, f"--on-active={SERVICE_DELAY_SECONDS}s",
                SYSTEMCTL, "restart", SERVICE_NAME,
            ])
            message = f"Service restart scheduled in {SERVICE_DELAY_SECONDS}s"
            details = f"{SERVICE_NAME} will restart; the runner is offline for a few seconds"
        else:
            result = _sudo([SHUTDOWN, "-r", "+1", "Reboot requested from Config sheet"])
            message = "Reboot scheduled in about 1 minute"
            details = "The Pi will go offline for about a minute. Cancel with: sudo shutdown -c"

        if result.returncode != 0:
            return (
                False,
                f"Could not schedule {mode} restart",
                (result.stderr or result.stdout).strip()[:500] or f"exit code {result.returncode}",
            )
        return (True, message, details)

    except Exception as e:
        return (False, "Error scheduling restart", f"{type(e).__name__}: {e}")


def main(params=None):
    """
    Main entry point for Restart Pi.

    Args:
        params: dict with "mode" (from the web UI / run_script.py). When None the mode
            is read from the Config sheet.

    Returns:
        Tuple of (success: bool, message: str, details: str)
    """
    try:
        if params is not None:
            return restart(params.get("mode") or "service")
        panel = ControlPanel(spreadsheet_name="RaspPI-Remote-Worker")
        params = panel.get_script_parameters("restart_pi.py")
        return restart(params.get("Parameter-1", "service"))
    except Exception as e:
        return (False, "Error running restart_pi", f"{type(e).__name__}: {e}")


if __name__ == "__main__":
    print(main())
