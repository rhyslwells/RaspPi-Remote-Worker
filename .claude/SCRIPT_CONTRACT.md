# Script Contract

How to add a task that the runner can execute. Reference implementations: `scripts/prime_hunter.py` (parameters), `scripts/test_connection.py` (minimal).

## Requirements

1. File lives in `scripts/` and is named in the sheet's `Script Name` column (`my_task.py`).
2. Defines `main()` returning exactly `(success: bool, message: str, details: str)`.
   - `message`: short, shown in the sheet `Details` cell
   - `details`: longer text, goes to the `Log` sheet
   - Anything else (wrong tuple length, `None`) is reported as FAILED "Script returned invalid format"
3. Catches its own expected errors and returns `(False, "...", str(e))`. Unhandled exceptions are caught by the runner, but the message is generic.
4. Keeps heavy work bounded. The runner executes scripts in-process and sequentially, so a long script delays every other task and the 10 s polling.
5. Does not call `sys.exit()` or change the working directory.

## Template

```python
#!/usr/bin/env python3
"""One-line purpose.

Parameters (from Google Sheet Config):
- Parameter-1: what it is
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from utils.control_panel import ControlPanel


def main():
    try:
        panel = ControlPanel(spreadsheet_name="RaspPI-Remote-Worker")
        params = panel.get_script_parameters_list("my_task.py")
        if len(params) < 1:
            return (False, "Missing parameters", f"Expected 1, got {len(params)}")

        result = do_work(params[0])
        return (True, "Short summary", f"Longer details: {result}")
    except Exception as e:
        return (False, "Error in my_task", f"{type(e).__name__}: {e}")


if __name__ == "__main__":
    ok, message, details = main()
    print(message, details)
    raise SystemExit(0 if ok else 1)
```

## Registering a new script

1. Add `scripts/my_task.py`.
2. Add a row to the `Config` sheet (or call `ControlPanel.add_script_to_config("my_task.py")`), Status `IDLE`.
3. Add `Parameter-N` columns only if needed. Parameters arrive as strings; convert and validate in the script.
4. Document in `docs/scripts/<NAME>_README.md` only if the script has non-obvious setup (see existing READMEs).

## Notes and gotchas

- `ControlPanel(...)` authenticates on construction. Constructing it in a script that the runner already authenticated for is redundant but is the existing pattern; do not refactor it unasked.
- `credentials.json` is resolved relative to the current working directory (repo root under systemd). Local runs must start from the repo root.
- `runner.py` has a special case for `test_connection.py` (`test_sheet_connection`). New scripts must use `main()`.
- Only add dependencies to `pyproject.toml` if the script truly needs them, and tell the user: the Pi runs `uv sync` on every update.
- Ideas for future scripts are in `docs/script_ideas.md` and `scripts/other-ideas.py` / `pulse_monitor.py` (currently notes, not runnable).
