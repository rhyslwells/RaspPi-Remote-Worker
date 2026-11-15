# Changelog

Version lives in `pyproject.toml` (`version = "..."`). Newest first. Bump rules are in [docs/scripts.md](docs/scripts.md#versioning).

## 0.6.0 - 2026-11-15

- Added the GB grid subsystem in `scripts/grid/` (see [docs/grid.md](docs/grid.md)): a collector for Elexon generation, demand and system prices and Octopus Agile rates (all 14 regions) into `data/grid.db`, and a Dash dashboard with a region selector. It runs from systemd timers, not from the sheet, and does not change `runner.py`, `ControlPanel` or any existing script.
- `scripts/grid/deploy/install_grid.sh` installs and removes the timers on the Pi (`--uninstall`). Not run yet.
- `scripts/grid/seed_demo.py` fills `data/grid_demo.db` with synthetic data so the dashboard can be tested locally without the Pi or network.
- New optional dependency group `grid` (`dash`, `plotly`, `gunicorn`, `dash-bootstrap-components`, `requests`). The collector needs none of them on the Pi; the dashboard does (`uv sync --extra grid`). No service restart needed.

## 0.5.2 - 2026-11-14

- `db_report.py`: when `Parameter-1` is blank (so it lists all databases), the result now ends with the parameters it actually received. Makes a value typed in the wrong column visible.

## 0.5.1 - 2026-11-14

- `pulse_monitor.py`: it kept sampling after `Parameter-1` was set to `0` because the row had not been set to `START` again (not a bug; a change only applies on `START`). Made this easier to diagnose: the timer and sample service are now stopped in separate calls; every start/stop result shows what `Parameter-1` was read as and what systemd still has loaded; a blank `Parameter-1` while a schedule runs now says so in the result.

## 0.5.0 - 2026-11-14

- Implemented `scripts/pulse_monitor.py` (was a notes file): snapshot of CPU temperature, load, memory, disk, uptime and power/throttle flags, saved to `data/pulse_monitor.db` and appended to a new `System Health` tab in the sheet. Standard library only, no new dependency.
- `Parameter-1` = interval in minutes: blank takes one sample, `N` starts a background sample every N minutes (transient systemd timer via sudo, so the runner is not blocked), `0` stops it. `Parameter-2` = max CPU temperature, `Parameter-3` = min free disk %. A breach returns FAILED "Health warning" (single sample) or writes a FAILED row to the Log tab (scheduled).

## 0.4.0 - 2026-11-14

- Added `scripts/restart_pi.py`: restart the runner service (default) or reboot the Pi from a Config sheet cell (`Parameter-1` = `service` or `reboot`). The restart is scheduled via systemd so the script can still report SUCCESS first. Needs passwordless sudo for the service user.
- `prime_hunter.py` now stores every prime it finds in a `primes` table in `data/prime_hunter.db` (duplicates ignored) and reports how many were new.

## 0.3.0 - 2026-11-14

- Added per-script SQLite databases (`data/<script>.db`, gitignored) via `scripts/utils/script_db.py` (standard library only). The runner now records every execution (parameters, success, message, details, duration) in the script's `runs` table. Scripts can add their own tables with `connect()`.
- Added `scripts/db_report.py`: lists the databases, or shows the latest runs for one script. Runs from the sheet (`Parameter-1` = script, `Parameter-2` = row limit) or from the command line.
- Runner change: needs a service restart after the update. Recording is best effort and never changes a script's result.

## 0.2.0 - 2026-11-14

- Added `scripts/git_pull_update.py`: update the Pi from a Config sheet cell (pull, `uv sync` if dependencies changed, "restart needed" report). Works when the service PATH lacks `git`.
- Update messages now show the version change (`v0.1.0 -> v0.2.0`).
- Docs consolidated into README, `docs/setup.md`, `docs/scripts.md`, `docs/faq.md`; added `docs/script_ideas.md` and `docs/improvements.md`.
- `raspi-helper.sh` now uses the real Pi path `~/Desktop/RaspPi-Remote-Worker` and prints the version after an update.
- Added `.claude/` project guidance and skills.

## 0.1.0

- Initial release: runner, `ControlPanel`, `test_connection.py`, `prime_hunter.py`, setup scripts and helper script.
