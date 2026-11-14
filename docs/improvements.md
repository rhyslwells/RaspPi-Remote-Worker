# Improvements

Findings from a code review of `scripts/runner.py` and `scripts/utils/control_panel.py` (2026-11-14). Status of everything here: **proposed, not implemented**. Ordered by how likely they are to bite.

## Correctness and robustness

| # | Issue | Where | Suggested fix |
|---|-------|-------|---------------|
| 1 | Runner can launch itself. The live Config sheet has a `runner.py` row. Setting it to `START` makes `run_script` import `runner.py` and call its `main()`, starting a second polling loop inside the first that never returns | `runner.py` `run_script`, Config row 2 | Delete the row and refuse `runner.py` (and anything not a plain `*.py` in `scripts/`) in `run_script` |
| 2 | Rows stuck in `RUNNING`. If the Pi reboots or the service restarts mid-script, the row stays `RUNNING` forever and the Log never records a result | `execute_script_lifecycle` | On runner start, set any `RUNNING` rows to `FAILED` with message "interrupted by restart" |
| 3 | Wrong row updated. `config_sheet.find(script_name)` matches any cell on the sheet. A Description or Details cell mentioning another script's name can be hit first | `get_script_status`, `set_script_status` | Search column A only (`find(name, in_column=1)`) or read all values once and index by row |
| 4 | Sheet-controlled path. The `Script Name` cell is turned into a file path with only `.replace('.py', '')` (which also mangles names like `my.pyramid.py`) | `run_script` | Take `Path(name).stem` and require the file to exist directly under `scripts/` and not be `runner.py` or in `utils/` |
| 5 | No timeout. Scripts run in-process, one at a time. A hang or an infinite loop stops all polling and leaves the row `RUNNING` | `run_script` | Run each script as a subprocess with a timeout (ask first: this changes the script contract's execution model) |
| 6 | Cell size limit. `prime_hunter` returns every prime in `details`; Google Sheets rejects cells over 50,000 characters, so large ranges fail at the Log append | `prime_hunter.py`, `_log_status_change` | Truncate `details` in `ControlPanel` (e.g. 40,000 chars with a "truncated" marker) and have scripts write bulky output to a file |
| 7 | Sheet drift. Live Config has a `Description` column that `_init_config_sheet` does not create; a rebuilt sheet will not match | `_init_config_sheet` | Add `Description`, keep Priority in position F |
| 8 | Lost results on reset. `Last Used` is overwritten on both RUNNING and the final state, so run duration is not recorded | `set_script_status` | Log duration in the final Log row |

| 9 | The service `PATH` contains only `.venv/bin` (set in `setup_systemd.sh`), so scripts cannot run system tools such as `git` by name. `git_pull_update.py` works around it with a fallback search path | `setup_systemd.sh` unit `Environment="PATH=..."` | Append `:/usr/local/bin:/usr/bin:/bin` to the unit's PATH and re-run the setup (systemd change: ask first) |

## Efficiency

- `set_script_status` makes about five API calls per transition (`find`, up to three `update_cell`, one `append_row`). Replace the three `update_cell` calls with a single `update` of the row range, and look the row number up once per run. This matters for Sheets API quotas once scripts are scheduled.
- Every script builds its own `ControlPanel`, which re-authenticates and re-opens the workbook on each run. Passing the runner's panel to `main(panel)` would avoid that, but it changes the script contract (ask first).

## Features worth adding (runner level)

1. **Scheduling.** Today every run needs a human to type `START`. Add a `Schedule` column (for example `every 1h` or a cron string) and let the runner set `START` when due. This unlocks monitoring and ETL scripts, and is the biggest single upgrade.
2. **Failure notification.** Email or push on `FAILED`, so a nightly job failing is noticed without opening the sheet.
3. **Self-restart after update.** `git_pull_update.py` reports "restart needed" but cannot restart the service safely from inside the runner. Partly done: `restart_pi.py` restarts the service (or reboots) from the sheet by scheduling it through systemd, so the result is recorded first. Still open: doing it automatically after an update that touched `runner.py` or `utils/`, and stuck-`RUNNING` recovery (item 2 above) for restarts that were not scheduled.
4. **Concurrency.** Subprocess per script with a timeout, optionally a worker pool. Required for any long-running idea in `docs/script_ideas.md` (tier B).
5. **Per-script output file.** (Run results and parameters are now stored in `data/<script>.db`; this item is only about raw stdout/stderr.) Capture stdout/stderr per run under `logs/<script>/<timestamp>.log` and put the path in the Log row.

## Repo hygiene

- `pyproject.toml` points at a missing `src/remote_worker` package and lists pandas, numpy and matplotlib, none of which any script imports.
- `raspi-helper.sh` header still mentions a `raspi-helper.ps1` that was removed, and `setup_initial.sh` prints "Step N/6" for four steps and an `scp` hint with the wrong path and user.
- `.raspi-config` (the Pi's local IP) is tracked in git. Untrack it with `git rm --cached .raspi-config` and add it to `.gitignore`; it stays in the git history.
- `docs/notes.md` (gitignored) holds a password hint, the Wi-Fi network name, an account email and the Pi's IP. It is not tracked, but it should not live in the repo folder.
- There are no tests. A tiny `pytest` file for the pure functions (e.g. `find_primes`) and a fake-`ControlPanel` test for `run_script` would cover the worst failure modes (items 1, 4) without touching the live sheet.
