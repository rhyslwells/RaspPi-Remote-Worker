# Changelog

Version lives in `pyproject.toml` (`version = "..."`). Newest first. Bump rules are in [docs/scripts.md](docs/scripts.md#versioning).

## 0.9.0 - 2026-11-15

- Web UI (`scripts/web/`): run, stop and watch the task scripts from a browser, without the Sheet. One card per script: a status badge, its parameters in a collapsible section (the collapsed line shows the current values), Run and Stop, the last result, and that script's own live output inside the card. Recent runs are listed at the bottom; tapping one opens its output in the script's card. Plain HTML/CSS/JS page and a small FastAPI JSON API; no front-end framework. Design and status: [docs/web-ui.md](docs/pi-control.md).
- Scripts are found by reading the files (nothing is imported): any `scripts/*.py` with `main` except `runner` and `run_script`. Each runs through `run_script.py` as its own process, so Stop ends the whole process tree. One run per script at a time (lock file plus database), a 30 minute timeout (override with `TIMEOUT_S`), the last 20 runs and logs kept per script, and `CONFIRM` scripts need confirmation (enforced by the server, not just the page).
- State is in `data/pi_control/state.db` (saved parameter values, history) and logs in `logs/`. The per-script `runs` tables are unchanged, so Sheet runs and web runs show in one history. A run still going when Pi Control restarts is picked up again.
- Each finished web run is also appended to the Sheet Log tab, best effort (never affects the run). Not verified against the live Sheet.
- `python debug_control.py` runs the app on localhost with hot reload, using the real scripts and the real `data/` folder (there is no demo mode). Nothing is written to the Sheet unless `--sheet-log` is given.
- Pi health card at the top of the page: live CPU temperature, load, memory, disk, uptime and power status, a "sampling" badge for the background timer, and a graph of the samples Pulse Monitor has stored (1h, 6h, 24h, 7d; CPU temp, load, or memory and disk). Reads `data/pulse_monitor.db`; no Sheet needed. New `scripts/web/health.py` and `GET /api/health`.
- Every script explains itself on its card: a `DESCRIPTION` (what it is for and what it changes) and a `help` sentence on each parameter. Both must be literals, like `PARAMS`.
- `pulse_monitor` skips the System Health tab when started from the web UI with `PI_CONTROL_SHEET_LOG=0` (what `debug_control.py` sets), so a laptop sample cannot land in the Pi's chart.
- Safety: changing requests need an `X-Pi-Control` header (stops other web pages firing runs), only discovered scripts can run, parameters are validated on the server and passed as JSON, no shell. Binds to 127.0.0.1 unless `PI_CONTROL_HOST` is set. Not yet installed as a service on the Pi, and Tailscale is not set up there, so nothing is reachable from outside the laptop.
- New dependencies: `fastapi` and `uvicorn`. The Pi needs `uv sync` (`git_pull_update` does it). Nothing to restart: the web app is not a service yet and `runner.py` is unchanged.
- `db_report.py`'s `PARAMS` uses literal values so the app can read it without running the file; `run_script.py` honours `PI_CONTROL_DATA` (optional, to keep databases elsewhere).

## 0.8.1 - 2026-11-15

- Pi Control step 2: the remaining Sheet scripts can now take parameters without the Sheet. `db_report`, `restart_pi` and `pulse_monitor` declare `PARAMS` and accept `main(params=None)`; with `None` they read the Sheet exactly as before. `restart_pi` and `git_pull_update` set `CONFIRM`, which Pi Control will use for an "Are you sure?" step.
- `pulse_monitor` run with parameters still takes and stores the sample and tries the System Health tab, but carries on with a note if the Sheet is unreachable.
- `run_script.py` also runs `test_connection.py` (it has only the legacy `test_sheet_connection`, as in `runner.py`).
- `runner.py` is unchanged and nothing was verified against the live Sheet, so the Sheet paths of the edited scripts are untested here. No new dependencies. No service restart needed.

## 0.8.0 - 2026-11-15

- First step towards Pi Control, a web UI that does what the Sheet does (scope in `debug/pi-control/scope.md`). Nothing in the UI exists yet.
- New `scripts/run_script.py`: runs one task script as its own process (`python scripts/run_script.py prime_hunter --params '{"start": 1, "end": 50}'`), validates the parameters, records the run in the script's `runs` table and exits 0 (success), 1 (failed) or 2 (could not start). It refuses `runner` and itself, and forces UTF-8 output so emoji in script logs do not crash a run on Windows.
- New `scripts/utils/params.py`: a script can declare a module-level `PARAMS` list (name, label, type, default, required, min, max, options) that is validated and converted before `main` runs.
- Script contract extended, not broken: `main(params=None)` may take a `params` dict; with `None` it reads the Sheet as before. `main()` with no argument still works. `prime_hunter.py` is the first script converted; the rest follow.
- The Sheet runner (`runner.py`) is unchanged. No new dependencies. No service restart needed.

## 0.7.1 - 2026-11-15

- Grid dashboard: the region selector moved out of the header into the pages that use it (Overview, Prices, and above the price chart on History). It is one shared choice, remembered in the browser. Generation, Status and Glossary no longer show one.
- Regional page: a date range picker limited to the days stored (opens on the newest 7 days; a single day is allowed) replaces the day buttons and calendar. Period averages are tiles above the chart, as on Overview. It has its own Southern or Northern Scotland choice. The empty state shows a message instead of a blank chart, and the controls line up.
- History only offers date ranges the stored daily history can fill, plus "All (N days)", instead of always listing 90 days and 1 year.
- Prices: removed the negative-prices-per-day chart.
- Dashboard only: no collector, schema or timer changes, no new dependencies, no service restart needed.

## 0.7.0 - 2026-11-15

- Grid dashboard: dark mode switch (remembered per browser), one-line overview tiles, dates on the Agile and price time axes, a collapsed "About this chart" box on every chart, a Glossary page, a searchable region dropdown (names only), a navbar that follows the theme, and dark hover labels. The weekday heatmap on Prices is now a typical weekday and weekend line chart. The Status page no longer shows CPU temperature.
- New Regional page: metered output for Southern and Northern Scotland by fuel, from Elexon B1610 and the BM unit reference. New `gsp` collector job and `gsp_generation` table (schema v3; existing `grid.db` files migrate on the next connect). Transmission-connected plants have no GSP group in Elexon's data, so `TRANSMISSION_UNITS` in `config.py` assigns them by hand. Elexon publishes this about a week late. Timer `grid-gsp` runs it daily at 04:00.
- New `prune` job: raw half-hourly tables keep the last `RETENTION_DAYS` (30) days; `daily_summary` and `agile_daily` are kept so History still shows a year. Timer `grid-prune` runs it daily at 03:30.
- `install_grid.sh` now installs the `grid-gsp` and `grid-prune` timers too, and the collector service timeout is 30 minutes (the first `gsp` run can take a while). Not installed on the Pi yet: re-run `install_grid.sh` there after pulling.
- `python debug_ui.py` runs the dashboard locally with hot reload on `data/grid.db` (`--demo` for synthetic data).
- No new dependencies. No service restart needed; nothing here touches `runner.py` or the sheet.

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
