#!/usr/bin/env python3
"""Entry point for the grid collector. See grid/collector/cli.py for usage."""

import sys
from pathlib import Path

# Same pattern as the task scripts: put scripts/ on the path so `grid` imports.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from grid.collector.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
