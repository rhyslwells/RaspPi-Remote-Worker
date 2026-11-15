#!/usr/bin/env python3
"""
Pulse Monitor Script
Takes snapshots of the Pi's health (CPU temperature, load, memory, disk, uptime,
power/throttle flags), stores them in data/pulse_monitor.db and appends a row to the
"System Health" tab of the Google Sheet (create a line chart on that tab once and
it updates as rows are added).

Parameters (from Google Sheet Config), all optional:
- Parameter-1: Sampling interval in minutes.
               blank   = take one sample now (inside the runner)
               N (1+)  = start sampling every N minutes in the background
               0       = stop the background sampling
- Parameter-2: Maximum CPU temperature in Celsius (default 75)
- Parameter-3: Minimum free disk space in percent (default 10)

Repeating works through a transient systemd timer (needs passwordless sudo, like
restart_pi.py), so the runner is NOT blocked and it survives service restarts. It
does not survive a Pi reboot: START it again afterwards. START with a new interval
replaces the old schedule. Threshold values are fixed when a schedule is started.

A threshold breach, or the Pi being under-voltage or throttled right now, is
reported as "Health warning": FAILED for a single sample, or a FAILED row in the
Log tab for scheduled samples.

Standard library only (reads /proc and /sys), so it needs no new dependency.

Command line (from the repo root):
    python scripts/pulse_monitor.py --sample      # one sample, as the timer runs it
    python scripts/pulse_monitor.py --sample --no-sheet   # database only (pulse-sample.timer)
"""

import argparse
import getpass
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent))

from utils.control_panel import ControlPanel, ScriptStatus
from utils.script_db import connect

SCRIPT_NAME = "pulse_monitor.py"
# Parameters shown as form fields in the web UI (see utils/params.py). A blank
# interval takes one sample now; N starts sampling every N minutes; 0 stops it.
DESCRIPTION = (
    "Takes a health snapshot of the Pi: CPU temperature, load, memory, disk, uptime and "
    "the power/throttle flags. Each sample is stored on the Pi (this is what the Pi "
    "health chart on this page draws) and added to the System Health tab of the Sheet. "
    "Leave Interval blank for one sample now, or give a number of minutes to keep "
    "sampling in the background. Background sampling survives a runner restart but not "
    "a reboot, so start it again afterwards. A reading over a limit, or the Pi being "
    "under-voltage or throttled right now, is reported as a Health warning (a failed run)."
)
PARAMS = [
    {"name": "interval", "label": "Interval in minutes (blank = one sample, 0 = stop)",
     "type": "int", "min": 0, "max": 1440,
     "help": "Blank: take one sample now. 5: sample every 5 minutes in the background "
             "(replaces any earlier schedule). 0: stop the background sampling. Up to 1440."},
    {"name": "max_temp", "label": "Max CPU temperature (C)", "type": "float",
     "default": 75, "min": 0, "max": 120,
     "help": "Warn when the CPU is hotter than this. Fixed when a schedule starts."},
    {"name": "min_free", "label": "Min free disk (%)", "type": "float",
     "default": 10, "min": 0, "max": 100,
     "help": "Warn when free disk space falls below this percentage. Fixed when a schedule starts."},
]
REPO_ROOT = Path(__file__).resolve().parent.parent
HEALTH_SHEET_NAME = "System Health"
HEALTH_HEADERS = [
    "Timestamp", "CPU Temp C", "Load 1m", "Memory Used %",
    "Disk Used %", "Uptime h", "Throttled",
]
DEFAULT_MAX_TEMP_C = 75.0
DEFAULT_MIN_FREE_DISK_PCT = 10.0
MAX_INTERVAL_MINUTES = 1440

TIMER_UNIT = "pulse-monitor"
# The systemd unit's PATH is the venv bin only, so use absolute paths.
SUDO = "/usr/bin/sudo"
SYSTEMD_RUN = "/usr/bin/systemd-run"
SYSTEMCTL = "/usr/bin/systemctl"
VCGENCMD = "/usr/bin/vcgencmd"
# get_throttled bits that mean "happening right now" (under-voltage, throttled)
THROTTLED_NOW_MASK = 0x1 | 0x4


# --- Reading the Pi ---------------------------------------------------------

def read_cpu_temp() -> Optional[float]:
    try:
        raw = Path("/sys/class/thermal/thermal_zone0/temp").read_text()
        return round(int(raw.strip()) / 1000, 1)
    except (OSError, ValueError):
        return None


def read_load() -> Optional[float]:
    try:
        return round(os.getloadavg()[0], 2)
    except (AttributeError, OSError):
        return None


def read_memory_used_pct() -> Optional[float]:
    try:
        values = {}
        for line in Path("/proc/meminfo").read_text().splitlines():
            key, _, rest = line.partition(":")
            values[key] = int(rest.split()[0])
        total, available = values["MemTotal"], values["MemAvailable"]
        return round((total - available) / total * 100, 1)
    except (OSError, ValueError, KeyError, IndexError, ZeroDivisionError):
        return None


def read_disk_used_pct() -> Optional[float]:
    try:
        usage = shutil.disk_usage("/")
        return round(usage.used / usage.total * 100, 1)
    except OSError:
        return None


def read_uptime_hours() -> Optional[float]:
    try:
        seconds = float(Path("/proc/uptime").read_text().split()[0])
        return round(seconds / 3600, 1)
    except (OSError, ValueError, IndexError):
        return None


def read_throttled() -> Optional[int]:
    """Raspberry Pi power/throttle flags, or None where vcgencmd is unavailable."""
    try:
        out = subprocess.run(
            [VCGENCMD, "get_throttled"], capture_output=True, text=True, timeout=5
        ).stdout
        return int(out.strip().split("=")[1], 16)
    except (OSError, subprocess.SubprocessError, ValueError, IndexError):
        return None


def collect_metrics() -> dict:
    """Take one snapshot. Any metric that cannot be read is None."""
    return {
        "cpu_temp_c": read_cpu_temp(),
        "load_1m": read_load(),
        "mem_used_pct": read_memory_used_pct(),
        "disk_used_pct": read_disk_used_pct(),
        "uptime_h": read_uptime_hours(),
        "throttled": read_throttled(),
    }


def find_warnings(metrics: dict, max_temp_c: float, min_free_disk_pct: float) -> list:
    """Return human-readable threshold breaches (empty list = healthy)."""
    warnings = []
    temp = metrics["cpu_temp_c"]
    if temp is not None and temp > max_temp_c:
        warnings.append(f"CPU {temp}C > {max_temp_c:g}C")
    disk = metrics["disk_used_pct"]
    if disk is not None and 100 - disk < min_free_disk_pct:
        warnings.append(f"disk {100 - disk:.1f}% free < {min_free_disk_pct:g}%")
    throttled = metrics["throttled"]
    if throttled is not None and throttled & THROTTLED_NOW_MASK:
        warnings.append(f"under-voltage or throttled now (flags {throttled:#x})")
    return warnings


# --- Storing a sample -------------------------------------------------------

def store_snapshot(timestamp: str, metrics: dict) -> bool:
    """Save the snapshot to data/pulse_monitor.db. Returns False on failure."""
    try:
        db = connect("pulse_monitor")
        try:
            with db:
                db.execute(
                    "CREATE TABLE IF NOT EXISTS health ("
                    "id INTEGER PRIMARY KEY AUTOINCREMENT, taken_at TEXT NOT NULL, "
                    "cpu_temp_c REAL, load_1m REAL, mem_used_pct REAL, "
                    "disk_used_pct REAL, uptime_h REAL, throttled INTEGER)"
                )
                db.execute(
                    "INSERT INTO health (taken_at, cpu_temp_c, load_1m, mem_used_pct, "
                    "disk_used_pct, uptime_h, throttled) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (timestamp, metrics["cpu_temp_c"], metrics["load_1m"],
                     metrics["mem_used_pct"], metrics["disk_used_pct"],
                     metrics["uptime_h"], metrics["throttled"]),
                )
        finally:
            db.close()
        return True
    except Exception:
        return False


def append_to_sheet(panel: ControlPanel, timestamp: str, metrics: dict) -> Optional[str]:
    """Append a row to the System Health tab. Returns an error string, or None."""
    try:
        sheet = panel._get_or_create_sheet(
            HEALTH_SHEET_NAME, lambda ws: ws.append_row(HEALTH_HEADERS)
        )
        throttled = metrics["throttled"]
        row = [
            timestamp, metrics["cpu_temp_c"], metrics["load_1m"],
            metrics["mem_used_pct"], metrics["disk_used_pct"], metrics["uptime_h"],
            f"{throttled:#x}" if throttled is not None else "",
        ]
        sheet.append_row(["" if v is None else v for v in row])
        return None
    except Exception as e:
        return f"{type(e).__name__}: {e}"


def format_details(metrics: dict) -> str:
    labels = [
        ("CPU temperature (C)", "cpu_temp_c"), ("Load (1 min)", "load_1m"),
        ("Memory used (%)", "mem_used_pct"), ("Disk used (%)", "disk_used_pct"),
        ("Uptime (hours)", "uptime_h"),
    ]
    lines = [f"{label}: {metrics[key] if metrics[key] is not None else 'n/a'}"
             for label, key in labels]
    throttled = metrics["throttled"]
    lines.append(f"Throttle flags: {throttled:#x}" if throttled is not None
                 else "Throttle flags: n/a")
    return "\n".join(lines)


def take_sample(panel: ControlPanel, max_temp: float, min_free: float,
                log_warnings: bool = False, use_sheet: bool = True) -> tuple:
    """
    Collect, store and report one sample.

    Args:
        panel: ControlPanel used for the System Health tab (and the Log if asked)
        max_temp: CPU temperature warning threshold in Celsius
        min_free: Minimum free disk percent before warning
        log_warnings: Also write a FAILED row to the Log tab on a warning (used by
            scheduled samples, which have no Config row to show the result)
        use_sheet: False never touches the Sheet (the permanent background timer)

    Returns:
        Tuple of (success: bool, message: str, details: str)
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    metrics = collect_metrics()
    if all(v is None for v in metrics.values()):
        return (False, "No metrics could be read", "Is this running on the Pi?")

    warnings = find_warnings(metrics, max_temp, min_free)
    notes = []
    if not store_snapshot(timestamp, metrics):
        notes.append("database not updated")
    if not use_sheet:
        sheet_error = None
    elif panel is not None:
        sheet_error = append_to_sheet(panel, timestamp, metrics)
    else:
        sheet_error = "no Google Sheet connection"
    if sheet_error:
        notes.append(f"System Health tab not updated ({sheet_error})")

    temp = metrics["cpu_temp_c"]
    disk = metrics["disk_used_pct"]
    summary = (
        f"CPU {temp if temp is not None else 'n/a'}C, "
        f"disk {disk if disk is not None else 'n/a'}% used"
    )
    details = format_details(metrics)
    if notes:
        details += "\nNote: " + "; ".join(notes)

    if warnings:
        message = "Health warning: " + "; ".join(warnings)
        if log_warnings and panel is not None:
            panel.log_execution(SCRIPT_NAME, ScriptStatus.FAILED, message, details)
        return (False, message, details)
    return (True, summary, details)


# --- Background schedule (systemd timer) ------------------------------------

def _sudo(args: list, timeout: int = 15) -> subprocess.CompletedProcess:
    # -n: never prompt for a password (there is no terminal); fail instead
    return subprocess.run(
        [SUDO, "-n", *args], capture_output=True, text=True, timeout=timeout
    )


def _stop_timer() -> None:
    """Stop and clear any existing schedule. Errors are ignored (may not exist)."""
    # Timer first and on its own: the sample service is usually not loaded between
    # runs, and an error for it must not be able to affect stopping the timer.
    for unit in (f"{TIMER_UNIT}.timer", f"{TIMER_UNIT}.service"):
        _sudo([SYSTEMCTL, "stop", unit])
    for unit in (f"{TIMER_UNIT}.timer", f"{TIMER_UNIT}.service"):
        _sudo([SYSTEMCTL, "reset-failed", unit])


def _unit_listing() -> str:
    """What systemd currently has loaded for the schedule, for diagnostics."""
    try:
        result = subprocess.run(
            [SYSTEMCTL, "list-units", "--all", "--no-legend", f"{TIMER_UNIT}*"],
            capture_output=True, text=True, timeout=10,
        )
        return " ".join(result.stdout.split()) or "no pulse-monitor units loaded"
    except (OSError, subprocess.SubprocessError) as e:
        return f"could not list units ({type(e).__name__})"


def _timer_active() -> bool:
    result = subprocess.run(
        [SYSTEMCTL, "is-active", f"{TIMER_UNIT}.timer"],
        capture_output=True, text=True, timeout=10,
    )
    return result.stdout.strip() == "active"


def start_schedule(minutes: int, max_temp: float, min_free: float) -> tuple:
    """Install (or replace) the transient timer. Returns (success, message, details)."""
    check = _sudo(["true"])
    if check.returncode != 0:
        return (False, "sudo needs a password",
                "The service user needs passwordless sudo. "
                f"sudo said: {check.stderr.strip()[:200]}")

    _stop_timer()
    result = _sudo([
        SYSTEMD_RUN,
        f"--unit={TIMER_UNIT}",
        f"--uid={getpass.getuser()}",
        f"--working-directory={REPO_ROOT}",  # credentials.json is relative to this
        "--description=Pi health sample (pulse_monitor.py)",
        "--on-active=1s",
        f"--on-unit-active={minutes}min",
        "--timer-property=AccuracySec=1s",  # default is 1 minute of slack
        "--",
        sys.executable, str(Path(__file__).resolve()), "--sample",
        "--max-temp", f"{max_temp:g}", "--min-free", f"{min_free:g}",
    ])
    if result.returncode != 0:
        return (False, "Could not start the schedule",
                (result.stderr or result.stdout).strip()[:500]
                or f"exit code {result.returncode}")

    state = "active" if _timer_active() else "NOT active (check systemctl status)"
    return (True, f"Sampling every {minutes} min",
            f"Timer {TIMER_UNIT}.timer is {state}. First sample in about a second. "
            f"Warn above {max_temp:g}C or below {min_free:g}% free disk (warnings go "
            "to the Log tab). Rows are added to the System Health tab. Stop with "
            "Parameter-1 = 0. The schedule does not survive a Pi reboot.")


def stop_schedule() -> tuple:
    """Stop the background sampling. Returns (success, message, details)."""
    check = _sudo(["true"])
    if check.returncode != 0:
        return (False, "sudo needs a password",
                f"sudo said: {check.stderr.strip()[:200]}")
    was_active = _timer_active()
    _stop_timer()
    if _timer_active():
        return (False, "Schedule still active",
                f"{TIMER_UNIT}.timer did not stop. systemd shows: {_unit_listing()}")
    return (True, "Sampling stopped" if was_active else "Sampling was not running",
            f"No background schedule is active now. systemd shows: {_unit_listing()}")


# --- Entry points -----------------------------------------------------------

def _parse_threshold(params: list, index: int, default: float) -> float:
    return float(params[index]) if len(params) > index and params[index] else default


def main(params=None):
    """
    Main entry point for Pulse Monitor when run by the runner or the web UI.

    Args:
        params: dict with "interval", "max_temp" and "min_free" (from the web UI /
            run_script.py). When None the values are read from the Config sheet.

    Returns:
        Tuple of (success: bool, message: str, details: str)
    """
    try:
        from_sheet = params is None
        if from_sheet:
            panel = ControlPanel(spreadsheet_name="RaspPI-Remote-Worker")
            # Use the dict so a blank Parameter-1 does not shift Parameter-2/3
            params_by_name = panel.get_script_parameters(SCRIPT_NAME)
            raw = [params_by_name.get(f"Parameter-{i}", "") for i in (1, 2, 3)]

            try:
                max_temp = _parse_threshold(raw, 1, DEFAULT_MAX_TEMP_C)
                min_free = _parse_threshold(raw, 2, DEFAULT_MIN_FREE_DISK_PCT)
                minutes = int(raw[0]) if raw[0] else None
            except ValueError:
                return (False, "Invalid parameters",
                        "Parameter-1 must be a whole number of minutes; Parameter-2 and "
                        f"Parameter-3 must be numbers. Got: {raw}")
            blank_hint = "Parameter-1 was blank"
            stop_hint = "set Parameter-1 to 0 and START to stop it"
        else:
            # The Google Sheet is only needed for the System Health tab. If it is not
            # reachable (no credentials, offline) the sample is still taken and stored.
            panel = None
            if os.environ.get("PI_CONTROL_SHEET_LOG") != "0":  # "0" = never touch the Sheet
                try:
                    panel = ControlPanel(spreadsheet_name="RaspPI-Remote-Worker")
                except Exception:
                    panel = None
            minutes = params.get("interval")
            max_temp = params.get("max_temp")
            min_free = params.get("min_free")
            max_temp = DEFAULT_MAX_TEMP_C if max_temp is None else float(max_temp)
            min_free = DEFAULT_MIN_FREE_DISK_PCT if min_free is None else float(min_free)
            blank_hint = "Interval was blank"
            stop_hint = "run again with interval 0 to stop it"

        if minutes is None:
            success, message, details = take_sample(panel, max_temp, min_free)
            # A blank interval is a single sample, never a stop: say so if a
            # schedule is still running, because "0" is what stops it.
            if sys.platform.startswith("linux") and _timer_active():
                details += (
                    f"\nNote: {blank_hint}, so this was one extra sample. A "
                    f"background schedule is still running ({TIMER_UNIT}.timer); "
                    f"{stop_hint}."
                )
            return (success, message, details)

        if minutes < 0 or minutes > MAX_INTERVAL_MINUTES:
            return (False, "Invalid interval",
                    f"Interval must be 0 (stop) to {MAX_INTERVAL_MINUTES} minutes")

        if not sys.platform.startswith("linux"):
            return (False, "Not running on Linux", f"Platform is {sys.platform}")

        if minutes == 0:
            success, message, details = stop_schedule()
        else:
            success, message, details = start_schedule(minutes, max_temp, min_free)
        if from_sheet:
            details += f"\nParameter-1 was read as {raw[0]!r}."
        return (success, message, details)
    except Exception as e:
        return (False, "Error running pulse_monitor", f"{type(e).__name__}: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pi health snapshot.")
    parser.add_argument("--sample", action="store_true",
                        help="take one sample now (how the timer runs it)")
    parser.add_argument("--no-sheet", action="store_true",
                        help="store the sample in the database only; never contact the Sheet")
    parser.add_argument("--max-temp", type=float, default=DEFAULT_MAX_TEMP_C)
    parser.add_argument("--min-free", type=float, default=DEFAULT_MIN_FREE_DISK_PCT)
    args = parser.parse_args()
    if args.sample:
        sheet = not args.no_sheet
        ok, msg, det = take_sample(
            ControlPanel(spreadsheet_name="RaspPI-Remote-Worker") if sheet else None,
            args.max_temp, args.min_free, log_warnings=sheet, use_sheet=sheet,
        )
        print(f"{'OK' if ok else 'FAILED'}: {msg}\n{det}")
    else:
        print(main())
