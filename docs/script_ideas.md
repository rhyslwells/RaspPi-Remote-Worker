# Script ideas

Backlog of scripts to try on the Pi. Status of everything here: **idea, not implemented** unless marked otherwise. Implemented today: `test_connection.py`, `prime_hunter.py`.

## How ideas are tiered

The runner executes scripts in-process, one at a time, with no timeout and no scheduler (see `docs/improvements.md`). So ideas split by what they need:

- **Tier A - works today.** Finishes in seconds to a few minutes, triggered by `START`, parameters from the sheet, result as `(success, message, details)`.
- **Tier B - needs runner work first.** Long-running (hours), periodic, or needs a subprocess with a timeout.

Constraints for all: ARM CPU, limited RAM, no GPU. Prefer the standard library; any new dependency must be added to `pyproject.toml` and installed with `uv sync` on the Pi.

## Tier A: operations and maintenance

| Script | What it does | Parameters | Notes |
|--------|--------------|------------|-------|
| `system_health.py` | CPU temperature, load, memory, disk, uptime, throttling flags into the Log row. Replaces the `pulse_monitor.py` notes | none | CPU temp from `/sys/class/thermal/thermal_zone0/temp`, `vcgencmd get_throttled`; `psutil` optional. Good first script: instant, safe |
| `git_pull_update.py` | `git pull`, `uv sync`, report what changed | optional branch | Do not restart the service from inside itself; report "restart needed" or use a detached `systemctl restart`. Pulls on the Pi only; be careful about repos synced to the laptop |
| `network_check.py` | Ping gateway and a public host, report public IP and DNS result | hosts | Useful when the Pi drops off the network |
| `log_cleanup.py` | Rotate or delete old files in `logs/` | days to keep | Keeps the SD card from filling; dry-run parameter first |
| `sheet_backup.py` | Export Config and Log to CSV under `data/` | none | Cheap insurance against sheet edits |
| `service_report.py` | `systemctl status` and last 20 lines of `logs/service.log` | lines | Reads state without SSH |

## Tier A: quick data and compute

| Script | What it does | Parameters |
|--------|--------------|------------|
| `carbon_intensity.py` | Fetch GB grid carbon intensity from the public National Grid API and append to a CSV and the Log | region (optional) |
| `weather_fetch.py` | Pull a forecast from a free weather API (Open-Meteo needs no key) for a location | lat, lon |
| `forecast_backtest.py` | Compare yesterday's actual values to stored predictions; report MAE / RMSE / MAPE | model name, date |
| `monte_carlo_pi.py` / `random_walk.py` | Short Monte Carlo with a fixed seed; a safe test of parameter handling | n samples, seed |
| `url_status.py` | HTTP status and latency for a list of sites | urls |

Check API terms and rate limits before relying on any external source.

## Tier B: long-running or scheduled (needs runner changes)

| Idea | Why the Pi suits it | Needs |
|------|--------------------|-------|
| Scheduled data pull and ETL into SQLite (hourly API poll) | Always on, I/O bound | Scheduler column, append-only SQLite |
| Regime-shift detector (CUSUM or Bayesian change-point) on a polled series | Needs 24/7 listening; store state per timestamp for a long-term state map | Scheduler, state table |
| MCMC posterior updates (PyMC / NUTS every few hours on the last 30 days) | CPU-heavy, no GPU, runs unattended | Subprocess + timeout, RAM check on the Pi, trace summary written to `model_metadata` |
| Symbolic regression "formula finder" with `gplearn` (see `docs/knowledge/Symbolic_Regression.md`) | Genetic programming is iterative; a run can take many hours | Subprocess + timeout, checkpoint results to disk |
| Differential-equation parameter sweep (grid of initial conditions, look for stable islands and chaotic transitions) | Embarrassingly parallel, set and forget | Subprocess, result file, optional pool |
| Distributed hyperparameter tuning (Optuna worker, shared RDB backend) | Pi as a secondary trial worker | Network-reachable RDB, long subprocess |
| Polite web scraping for a corpus (rate-limited, `BeautifulSoup`/`Scrapy`) | Slow by design, I/O bound | Scheduler, robots/terms check |
| Literature knowledge graph (arXiv/PubMed metadata, NetworkX centrality, rankings in SQL) | Scraping is rate-limited, graph metrics can be computed incrementally | Scheduler, SQLite, subprocess |

## Cross-cutting needs these ideas expose

1. A **Schedule** column and runner support (most Tier B items).
2. **Subprocess execution with a timeout** (anything over a minute).
3. **Result files**: write bulky output to `data/` and put the path in the Log. Sheet cells cap at 50,000 characters.
4. **Failure notification** so unattended jobs do not fail silently.

## Suggested order

1. `system_health.py` - fills the empty `pulse_monitor.py` slot, no parameters, no risk.
2. `git_pull_update.py` - turns a manual SSH step into a sheet button.
3. Fix `docs/improvements.md` items 1-4, then add the Schedule column.
4. `carbon_intensity.py` or `weather_fetch.py` on a schedule - first real unattended data job.
5. One Tier B compute job (Monte Carlo sweep first, MCMC later) once subprocess and timeout exist.
