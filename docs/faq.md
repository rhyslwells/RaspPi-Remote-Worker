# FAQ

Short answers to questions that keep coming up. Add new ones at the bottom of the relevant section. Detail lives in [setup.md](setup.md) and [scripts.md](scripts.md); this page links rather than repeats.

## Deployment

### Does the Pi update automatically when I change the repo?

No. The Pi has its own clone. A change reaches it only after you push to GitHub and then pull on the Pi. Nothing automates this; `git_pull_update.py` does the pull when you set it to `START`.

Three ways to update, after pushing: set `git_pull_update.py` to `START` in the sheet, run `update_raspi_repo` from the helper script on your PC, or run the commands on the Pi. See [setup.md](setup.md#6-updating).

### Does `git_pull_update.py` restart the service?

No, on purpose: restarting from inside the runner would kill it before it could record the result and leave the row on `RUNNING`. It tells you "restart needed" when `runner.py` or `utils/` changed. Restart from the sheet with `restart_pi.py` (it schedules the restart, so the result is recorded first), or with `restart_raspi_service` or `sudo systemctl restart remote-worker.service`. A script-only change needs no restart.

### Why did `git_pull_update.py` fail with "No such file or directory: 'git'"?

The systemd unit sets `PATH` to the venv's `bin` only, so the runner cannot see `/usr/bin/git`. The script now searches `/usr/local/bin`, `/usr/bin` and `/bin` as a fallback. Any new script that shells out to a system tool has the same limit: use the full path or the same fallback. To fix it for every script, add `/usr/bin:/bin` to the `PATH` in `setup_systemd.sh` and reinstall the unit (a systemd change; ask first).

### What version is the Pi on?

The update message shows it (`Updated v0.2.0 -> v0.3.0 ...` or `Already up to date (v0.3.0)`), and `update_raspi_repo` prints it. On the Pi: `grep -m1 '^version' pyproject.toml`. History is in [CHANGELOG.md](../CHANGELOG.md); how to bump is in [scripts.md](scripts.md#versioning). Note this is the version of the code on disk; the running service only picks up `runner.py` and `utils/` changes after a restart.

### Why did the update say "uv sync failed (run `uv lock` and push?)"?

The version was edited in `pyproject.toml` by hand and `uv.lock` was not regenerated (`uv version --bump ... --no-sync` avoids this). The pull succeeded and the Pi's checkout is untouched. On your PC run `uv lock`, commit `uv.lock`, push, and run the update again.

### Why else might `git_pull_update.py` fail?

`git pull failed` with "local changes would be overwritten" means someone edited files on the Pi; with "Not possible to fast-forward" the Pi has commits GitHub does not. The script changes nothing in either case. Fix on the Pi by hand (`git status`).

### After pulling, do I need to restart the service?

| What changed | Needed |
|--------------|--------|
| A task script in `scripts/` | Nothing. It is re-read from disk on every run |
| `runner.py` or anything in `scripts/utils/` | Restart the service (loaded once at startup) |
| `pyproject.toml` dependencies | `uv sync`, then restart |
| `setup_systemd.sh` | Re-run it, then `sudo systemctl daemon-reload` and restart |

### Which files never sync through git?

`credentials.json`, `.env`, `logs/`, `data/` (the per-script databases) and `docs/notes.md` are gitignored. Copy `credentials.json` with `scp` ([setup.md](setup.md#4-deploy-credentials)). `.raspi-config` (your Pi's IP for the helper script) is currently tracked in git, so it does sync.

### Does a push to `main` deploy?

No, it only makes the change available. The Pi still has to pull.

## Using the sheet

### How do I run a script?

Set its `Status` cell in the `Config` tab to `START`. The runner checks every 10 seconds. See [scripts.md](scripts.md#status-lifecycle).

### Why is a row stuck on `RUNNING`?

The Pi restarted (or the runner was stopped) mid-script and nothing resets the row. Set it back to `IDLE` by hand. Automatic recovery is proposed in [improvements.md](improvements.md).

### Why did a run fail with "cannot unpack non-iterable NoneType object"?

The script's `main()` returned `None`. It must return `(success, message, details)` ([scripts.md](scripts.md#writing-a-script)).

### Can I run a script on a schedule?

Not generally: every run needs a `START`. A `Schedule` column is the top proposal in [improvements.md](improvements.md). The exception is `pulse_monitor.py`, which sets up its own systemd timer when `Parameter-1` is a number of minutes ([scripts.md](scripts.md#included-scripts)); it stops with `0` and does not survive a Pi reboot.

### Can two scripts run at once?

No. The runner executes them one at a time, in its own process, with no timeout. A long script delays everything else.

## Stored data

### Where are results and inputs stored?

In one SQLite file per script, `data/<script>.db` on the Pi, created on the first run after the service has been restarted onto the new runner. The `runs` table has one row per execution (parameters, success, message, details, duration); scripts can add their own tables. See [scripts.md](scripts.md#included-scripts).

### How do I see what is in the databases?

Set `db_report.py` to `START`: `Parameter-1` blank lists every database, a script name shows its latest runs, `Parameter-2` is how many (default 20). Or run `python scripts/db_report.py [script] [--limit N]` on the Pi.

### Why does `db_report.py` say "No databases yet" or not show its own run?

No database exists until a script has finished under a runner that has the recording code, so restart the service after updating (the runner is loaded once). A run is recorded after it finishes, so `db_report.py` never shows itself until its next run.

### Are the databases backed up?

No. `data/` is gitignored and not copied anywhere. Copy the `.db` files off the Pi (`scp`) if they matter.

## Project

### Where do new ideas and review findings go?

Script ideas in [script_ideas.md](script_ideas.md); proposed changes to the runner or sheet in [improvements.md](improvements.md). Implemented items are removed from those pages and documented in [scripts.md](scripts.md).
