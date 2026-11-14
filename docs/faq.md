# FAQ

Short answers to questions that keep coming up. Add new ones at the bottom of the relevant section. Detail lives in [setup.md](setup.md) and [scripts.md](scripts.md); this page links rather than repeats.

## Deployment

### Does the Pi update automatically when I change the repo?

No. The Pi has its own clone. A change reaches it only after you push to GitHub and then pull on the Pi. Nothing automates this (a `git_pull_update.py` script is only an idea in [script_ideas.md](script_ideas.md)).

Three ways to update, after pushing: set `git_pull_update.py` to `START` in the sheet, run `update_raspi_repo` from the helper script on your PC, or run the commands on the Pi. See [setup.md](setup.md#6-updating).

### Does `git_pull_update.py` restart the service?

No, on purpose: restarting from inside the runner would kill it before it could record the result and leave the row on `RUNNING`. It tells you "restart needed" when `runner.py` or `utils/` changed; restart with `restart_raspi_service` or `sudo systemctl restart remote-worker.service`. A script-only change needs no restart.

### Why did `git_pull_update.py` fail?

`git pull failed` with "local changes would be overwritten" means someone edited files on the Pi; with "Not possible to fast-forward" the Pi has commits GitHub does not. The script changes nothing in either case. Fix on the Pi by hand (`git status`).

### After pulling, do I need to restart the service?

| What changed | Needed |
|--------------|--------|
| A task script in `scripts/` | Nothing. It is re-read from disk on every run |
| `runner.py` or `scripts/utils/control_panel.py` | Restart the service (loaded once at startup) |
| `pyproject.toml` dependencies | `uv sync`, then restart |
| `setup_systemd.sh` | Re-run it, then `sudo systemctl daemon-reload` and restart |

### Which files never sync through git?

`credentials.json`, `.raspi-config`, `.env`, `logs/` and `docs/notes.md` are gitignored. Copy `credentials.json` with `scp` ([setup.md](setup.md#4-deploy-credentials)).

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

Not yet. Every run needs a `START`. A `Schedule` column is the top proposal in [improvements.md](improvements.md).

### Can two scripts run at once?

No. The runner executes them one at a time, in its own process, with no timeout. A long script delays everything else.

## Project

### Where do new ideas and review findings go?

Script ideas in [script_ideas.md](script_ideas.md); proposed changes to the runner or sheet in [improvements.md](improvements.md). Implemented items are removed from those pages and documented in [scripts.md](scripts.md).
