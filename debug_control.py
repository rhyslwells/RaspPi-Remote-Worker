#!/usr/bin/env python3
"""
Run the Remote Worker web UI locally with hot reload, for trying UI changes on the laptop.

    python debug_control.py                # http://127.0.0.1:8051
    python debug_control.py --sheet-log    # also write finished runs to the Sheet Log tab

It runs the real scripts in scripts/ on THIS machine and records into the real data/
folder, exactly as the Pi does. Edits to scripts/web/ reload automatically.

On a laptop:
  - restart_pi does nothing (it only works on Linux).
  - git_pull_update really runs `git pull --ff-only` in this repository (it asks first).
  - pulse_monitor takes a sample of the laptop; most readings show n/a on Windows.
  - Nothing is written to the Google Sheet unless you add --sheet-log. test_connection
    still signs in to the Sheet (read only), because that is what it tests.
"""

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCRIPTS = ROOT / "scripts"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Remote Worker web UI locally.")
    parser.add_argument("--sheet-log", action="store_true",
                        help="write finished runs (and pulse_monitor samples) to the Sheet")
    parser.add_argument("--port", type=int, default=8051)
    args = parser.parse_args()

    # "0" means: never contact the Sheet from the web UI or from pulse_monitor.
    os.environ["PI_CONTROL_SHEET_LOG"] = "1" if args.sheet_log else "0"
    print("Real scripts, real data/ folder. Sheet writes:", "ON" if args.sheet_log else "off")

    import uvicorn

    uvicorn.run(
        "web.app:app",
        host="127.0.0.1",  # local only, always
        port=args.port,
        reload=True,
        reload_dirs=[str(SCRIPTS / "web")],
        app_dir=str(SCRIPTS),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
