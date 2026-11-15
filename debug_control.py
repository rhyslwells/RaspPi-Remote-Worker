#!/usr/bin/env python3
"""
Run Pi Control locally with hot reload, for trying UI changes on the laptop.

    python debug_control.py             # demo mode: fake scripts, throwaway data
    python debug_control.py --reset     # wipe the demo data and logs first
    python debug_control.py --real      # the real scripts/ and data/ (see warning below)
    python debug_control.py --real --sheet-log   # also write finished runs to the Sheet

Open http://127.0.0.1:8051. Edits to scripts/web/ reload automatically.
Demo mode keeps everything in data/demo/ and logs/demo/ (both gitignored), never
touches your real run history, and never contacts Google Sheets or the Pi.

--real runs the actual task scripts on THIS machine and records into the real data/
folder. Scripts that need credentials.json or Pi-only commands will fail here, which is
expected, but a script that works (db_report, prime_hunter) really runs. The Sheet Log
tab is only written with --sheet-log.
"""

import argparse
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCRIPTS = ROOT / "scripts"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Pi Control locally.")
    parser.add_argument("--real", action="store_true", help="use the real scripts and data")
    parser.add_argument("--reset", action="store_true", help="wipe the demo data and logs first")
    parser.add_argument("--sheet-log", action="store_true", help="with --real: write results to the Sheet Log tab")
    parser.add_argument("--port", type=int, default=8051)
    args = parser.parse_args()

    if args.reset and args.real:
        print("--reset only applies to demo mode; refusing to touch real data.")
        return 2
    if args.sheet_log and not args.real:
        print("--sheet-log only applies with --real.")
        return 2

    if args.real:
        os.environ["PI_CONTROL_SHEET_LOG"] = "1" if args.sheet_log else "0"
        print("REAL mode: real scripts, real data/ folder. Sheet log:",
              "on" if args.sheet_log else "off")
    else:
        data, logs = ROOT / "data" / "demo", ROOT / "logs" / "demo"
        if args.reset:
            for folder in (data, logs):
                shutil.rmtree(folder, ignore_errors=True)
            print("Demo data and logs wiped.")
        os.environ["PI_CONTROL_SCRIPTS_DIR"] = str(SCRIPTS / "web" / "demo_scripts")
        os.environ["PI_CONTROL_DATA"] = str(data)
        os.environ["PI_CONTROL_LOGS"] = str(logs)
        os.environ["PI_CONTROL_SHEET_LOG"] = "0"
        print("Demo mode: fake scripts, data in data/demo/, Sheet never contacted.")

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
