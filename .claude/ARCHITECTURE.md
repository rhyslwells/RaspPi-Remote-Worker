# Architecture

Behaviour (runner loop, sheet layout, status lifecycle, `ControlPanel` API) is documented in [docs/scripts.md](../docs/scripts.md) and the README. This file holds the design decisions and what follows from them.

## Shape

Controller (Google Sheet) -> worker (`scripts/runner.py` under systemd) -> task scripts (`scripts/*.py`). Everything that touches Google Sheets goes through `ControlPanel`; scripts and the runner do not call gspread directly (the exception is `scripts/utils/list_sheets.py`, a standalone diagnostic).

## Design decisions

- **Polling, not push.** Simplest thing that works behind home NAT; no inbound ports. Interval 10 s, 30 s back-off after a loop-level exception.
- **Scripts are imported into the runner process**, not run as subprocesses. A hung script blocks all polling; a script calling `sys.exit()` affects the runner. Scripts run sequentially. Moving to subprocess or multiprocessing is an "ask first" change.
- **Result as a return tuple**, so the sheet gets a readable message and details. Exceptions are still caught and reported as FAILED.
- **Service-account auth via `credentials.json`** with `oauth2client` + `gspread.authorize`. Legacy but working; migrating is a possible cleanup, not a drive-by change.
- **Parameters live in the sheet**, so changing a run's inputs needs no deploy.
- **systemd owns persistence**: `Restart=always`, `RestartSec=10`, output to `logs/service.log`.

## Consequences to keep in mind

- Columns A-D of `Config` are addressed by position (1-4) in `set_script_status` and `reset_all_to_idle`; the rest is read by header name. The live sheet has drifted from `_init_config_sheet` (extra `Description` column).
- `ControlPanel` finds a row with `worksheet.find(script_name)`, which searches every cell, so a cell mentioning another script's name can be matched first.
- Nothing recovers a row left on `RUNNING` by a restart; nothing prevents `runner.py` being triggered as a script from the sheet. Both are in `docs/improvements.md`.
