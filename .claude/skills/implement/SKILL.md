---
name: implement
description: Build a locked scope in this repo (task script, ControlPanel or runner change) following the script contract and existing patterns.
---

# Implement

Build to the locked scope. Verification is part of implementation.

## Pre-check

- Scope is stated (goal, criteria). If not, run `/scope` first.
- Read the nearest existing example: `scripts/prime_hunter.py` for task scripts, `scripts/utils/control_panel.py` for sheet access.
- Read `.claude/SCRIPT_CONTRACT.md` for any script work.

## Build

- New task: `scripts/<name>.py` with `main()` returning `(success, message, details)`; parameters via `ControlPanel.get_script_parameters_list`; expected errors returned, not raised.
- Keep the `sys.path.insert(0, str(Path(__file__).parent))` + `from utils.control_panel import ...` pattern.
- Parameters are strings from the sheet: convert and validate at the top of `main()`.
- Keep runtime short; the runner executes scripts in-process, one at a time.
- Do not change the contract, status enum, sheet columns, runner loop or systemd files without approval.
- No new dependencies without telling the user (update `pyproject.toml`, note `uv sync` on the Pi).
- No emojis in docs, comments or identifiers.

## Verify

- `python -m py_compile scripts/<file>.py`
- `ruff check scripts/<file>.py` if ruff is installed
- Call pure functions directly with representative and edge inputs (empty, blank, non-numeric strings, boundaries)
- Anything that constructs `ControlPanel` hits the live sheet. Run it only if the user has asked; otherwise say it was not run

## Do not

- Update docs (use `/docs-capture`)
- Refactor unrelated code or "fix" the known inconsistencies listed in CLAUDE.md
- Scaffold a test suite
- Run ssh/scp/systemctl or the runner

## Output

```
IMPLEMENTATION COMPLETE
Criteria: [each: pass / not verified, and how]
Files: [created / changed]
Not run: [live sheet / Pi steps skipped]
Deploy note: [uv sync needed? sheet row to add? params to set?]
Next: /test or /review
```
