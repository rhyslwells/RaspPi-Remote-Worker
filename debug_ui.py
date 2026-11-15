#!/usr/bin/env python3
"""
Run the grid dashboard locally with hot reload, for trying UI changes.

    python debug_ui.py            # real data in data/grid.db (demo data if that is missing)
    python debug_ui.py --demo     # synthetic demo data (seeded automatically if missing)
    python debug_ui.py --reseed   # rebuild the demo data first (implies --demo)

Fill data/grid.db with real data (public Elexon and Octopus APIs, gitignored):
    python scripts/grid/collect.py backfill --from 2026-10-16 --to 2026-11-15

Open http://127.0.0.1:8050. Edits to scripts/grid/dashboard/ reload automatically.
Local only: nothing is deployed, and the demo data lives in data/ (gitignored).
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "scripts"))

use_real = (
    "--demo" not in sys.argv
    and "--reseed" not in sys.argv
    and (ROOT / "data" / "grid.db").exists()
)
if use_real:
    os.environ.pop("GRID_DB", None)
else:
    demo = ROOT / "data" / "grid_demo.db"
    os.environ["GRID_DB"] = str(demo)
    # The reloader restarts this script on every edit; the marker stops each
    # restart from reseeding.
    if ("--reseed" in sys.argv or not demo.exists()) and not os.environ.get("GRID_DEBUG_SEEDED"):
        from grid import seed_demo

        original_argv = sys.argv
        sys.argv = [sys.argv[0]]  # seed_demo has its own arguments
        seed_demo.main()
        sys.argv = original_argv
        os.environ["GRID_DEBUG_SEEDED"] = "1"

if __name__ == "__main__":
    from grid.dashboard.app import app

    print(f"Using database: {os.environ.get('GRID_DB') or 'data/grid.db'}")
    app.run(debug=True, host="127.0.0.1", port=8050)
