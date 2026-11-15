# GB grid collector and dashboard

A separate subsystem in `scripts/grid/`. It collects GB electricity data into SQLite on a schedule and shows it in a Dash dashboard. It does **not** use the Google Sheet or `runner.py`: the collector runs from systemd timers.

| Data | Source | Cadence |
|------|--------|---------|
| Generation by fuel, demand, system prices | Elexon Insights API | every 30 minutes |
| Agile unit rates, all 14 regions | Octopus API | every 30 minutes from 15:35 to 17:35 UK time (next-day prices appear around 16:00), plus 00:15 |
| Daily summary | built from stored rows | 00:30 |
| Backup of `data/grid.db` | SQLite online backup, newest 4 kept in `data/backups/` | Sundays 03:00 |

Both APIs are public and need no key. Generation is **metered generation only** (transmission-connected plants and interconnectors): solar and embedded wind are not included, so it is less than total demand. The Elexon attribution line is shown in the dashboard footer.

## Layout

```
scripts/grid/
├── collect.py            # collector entry point
├── seed_demo.py          # fills data/grid_demo.db with synthetic data (testing)
├── collector/            # db.py, fetch_elexon.py, fetch_agile.py, summarise.py, cli.py, config.py
├── dashboard/            # app.py, queries.py (all SQL), pages/, colours.py, assets/
└── deploy/               # systemd units and install_grid.sh
```

## Collector commands

Run from the repo root with the venv Python:

```
python scripts/grid/collect.py elexon                       # last two settlement days
python scripts/grid/collect.py agile                        # yesterday to tomorrow, all regions
python scripts/grid/collect.py summary [--date YYYY-MM-DD]  # default: yesterday
python scripts/grid/collect.py backfill --from D --to D     # fetch and summarise a range
python scripts/grid/collect.py backup
```

Writes are idempotent (re-running a date replaces its rows). Each job runs in one transaction, uses a lock file so runs never overlap, logs to `logs/grid_collector.log`, records itself in the `collector_runs` table, and exits non-zero on failure. Settings (region list, product code `GRID_AGILE_PRODUCT`, timeouts) are in `scripts/grid/collector/config.py`. Timestamps are stored in UTC; UK-local days have 46 to 50 half-hour periods on clock-change days.

`data/grid.db` is gitignored. `GRID_DB=<path>` points the collector and dashboard at a different file.

## Testing without the Pi or the live data

The demo data is synthetic and is written to `data/grid_demo.db`, which is gitignored (everything under `data/` is). Nothing here touches the Pi, the sheet or `data/grid.db`.

```
uv sync --extra grid
python scripts/grid/seed_demo.py                       # 14 days, all regions, plus tomorrow's Agile
GRID_DB=data/grid_demo.db python scripts/grid/dashboard/app.py
```

PowerShell: `$env:GRID_DB="data/grid_demo.db"; python scripts/grid/dashboard/app.py`, then open http://127.0.0.1:8050. To test with real data instead, run `python scripts/grid/collect.py backfill --from D --to D` (reads the public APIs, writes `data/grid.db`) and start the dashboard without `GRID_DB`.

## Dashboard

Pages: Overview (latest-day tiles, upcoming Agile prices with the cheapest 2 hours), Generation (stacked by fuel group with demand), Prices (Agile against system price, weekday heatmap, negative prices), History, Status (last runs, freshness, database size, Pi temperature and disk). The region selector in the header (default N, Southern Scotland) is remembered in the browser. The dashboard opens the database read-only and refreshes panels only when the collector has written new data.

Serving it on the Pi (gunicorn service, Tailscale Funnel) is not set up yet; see the project notes. The development server above is for local testing only.

## Installing the collector timers on the Pi

Run on the Pi from the repo, as the normal user (asks for sudo). It checks the Pi timezone is `Europe/London` first.

```
bash scripts/grid/deploy/install_grid.sh              # install and enable the timers
bash scripts/grid/deploy/install_grid.sh --uninstall  # remove them (data is kept)
systemctl list-timers 'grid-*'
journalctl -u 'grid-collector@*' -n 50
```

The collector needs no extra packages (`requests` already comes with gspread); the dashboard needs `uv sync --extra grid`. Optional heartbeat: set `GRID_HEARTBEAT_URL=...` in `/etc/default/grid-collector`; the `elexon` job pings it after each success.

Collector changes take effect on the next timer run (each job is a one-shot process), so no service restart is needed. `git_pull_update.py` does not touch the timers.
