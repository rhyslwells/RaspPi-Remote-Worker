#!/usr/bin/env python3
"""
Run one task script as a standalone process (used by Pi Control).

    python scripts/run_script.py prime_hunter --params '{"start": 1, "end": 50}'

Imports scripts/<name>.py, validates the parameters against the script's PARAMS list,
calls main(params), prints the result, records the run in data/<name>.db and exits.
Running it as its own process lets the caller stop it and read its output as it goes.

Exit codes: 0 = script succeeded, 1 = script failed, 2 = could not start the script
(unknown name, bad parameters, bad import). Nothing is recorded for exit code 2.

Scripts that predate parameters (main() takes no arguments) still work: they are called
as main() and read their own parameters from the Google Sheet.
"""

import argparse
import importlib.util
import inspect
import json
import sys
import time
from datetime import datetime
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))

from utils.params import coerce_params  # noqa: E402
from utils.script_db import record_run, script_key  # noqa: E402


# Files in scripts/ that are not task scripts. Running "runner" would start the Sheet
# polling loop; running "run_script" would recurse.
NOT_TASK_SCRIPTS = {"runner", "run_script"}


def load_script(name: str):
    """Import scripts/<name>.py. Raises FileNotFoundError or ImportError-like errors."""
    key = script_key(name)
    if key in NOT_TASK_SCRIPTS:
        raise FileNotFoundError(f"{key!r} is not a task script")
    path = SCRIPTS_DIR / f"{key}.py"
    if not path.is_file():
        raise FileNotFoundError(f"No script named {key!r} in {SCRIPTS_DIR}")
    spec = importlib.util.spec_from_file_location(key, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not create a module spec for {key}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return key, module


def accepts_params(func) -> bool:
    """True if main() can take a ``params`` argument."""
    try:
        return "params" in inspect.signature(func).parameters
    except (TypeError, ValueError):
        return False


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Run one task script as its own process.")
    p.add_argument("script", help="script name, with or without .py")
    p.add_argument("--params", default="{}", help="parameters as a JSON object")
    return p.parse_args(argv)


def main(argv=None) -> int:
    # Scripts log emoji; a redirected stdout on Windows defaults to cp1252 and would
    # turn that into a UnicodeEncodeError that fails the run.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

    args = parse_args(argv)

    try:
        raw = json.loads(args.params)
        if not isinstance(raw, dict):
            raise ValueError("must be a JSON object")
    except ValueError as e:
        print(f"[run_script] invalid --params: {e}", flush=True)
        return 2

    try:
        key, module = load_script(args.script)
    except Exception as e:  # noqa: BLE001 - report any import problem, do not crash
        print(f"[run_script] cannot load {args.script}: {type(e).__name__}: {e}", flush=True)
        return 2

    # test_connection.py predates main(); the Sheet runner has the same special case.
    func = getattr(module, "main", None) or getattr(module, "test_sheet_connection", None)
    if not callable(func):
        print(f"[run_script] {key} has no main() function", flush=True)
        return 2

    values, errors = coerce_params(getattr(module, "PARAMS", None), raw)
    if errors:
        print("[run_script] invalid parameters:", flush=True)
        for err in errors:
            print(f"  - {err}", flush=True)
        return 2

    print(f"[run_script] starting {key}", flush=True)
    started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    start = time.monotonic()
    try:
        result = func(values) if accepts_params(func) else func()
        if not (isinstance(result, tuple) and len(result) == 3):
            result = (
                False,
                "Script returned invalid format",
                f"Expected (success, message, details), got: {type(result).__name__}",
            )
    except Exception as e:  # noqa: BLE001 - a crashing script is a failed run
        result = (False, "Error executing script", f"{type(e).__name__}: {e}")

    success, message, details = result
    duration = time.monotonic() - start
    record_run(key, started_at, duration, bool(success), values, message, details)

    print(f"[run_script] {'SUCCESS' if success else 'FAILED'} in {duration:.1f}s", flush=True)
    print(f"message: {message}", flush=True)
    if details:
        print("details:", flush=True)
        print(details, flush=True)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
