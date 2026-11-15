# Pi Control

Pi Control is a web page for running and watching the task scripts on the Pi, as an alternative to the Google Sheet. It is meant to be used from a phone.

**Status: in progress.** Sections marked (built) exist in the repo; everything else is planned and described so the design is written down before the code. The web app itself is not built yet.

## Purpose

The Sheet works, but it is slow and indirect: you edit cells, then wait for the runner to poll (every 10 seconds) and write the result back. Pi Control sends the command straight to the Pi when you press Run, and shows the result, the parameters and the output on one screen.

It does the same job as the Config sheet:

| Config sheet | Pi Control |
|---|---|
| A row per script | A card per script |
| Status (`START`, `RUNNING`, `SUCCESS`, `FAILED`) | A status badge; the Run button replaces setting `START` |
| Last Used, Details | Last run time, last message and details |
| `Parameter-N` cells | Form fields per script, with saved values |
| Log tab | Run history, with the output of each run |
| (none) | Stop button, live output |

The Sheet and its runner keep working unchanged. Either can be used; they are separate front-ends for the same scripts.

## How it fits together

```mermaid
flowchart LR
    P[Phone browser] -->|Tailscale| W[Pi Control web app]
    W -->|subprocess| R[scripts/run_script.py]
    R -->|main params| S[scripts/*.py]
    R --> D[(data/script.db runs table)]
    W -.->|best effort| L[Sheet Log tab]
    Sheet[Config sheet] --> RN[scripts/runner.py]
    RN -->|in process| S
```

- The web app starts each script as its own process, so it can be stopped and its output read as it is produced. (planned)
- The Sheet runner still imports and calls scripts in its own process. (unchanged)
- Both record runs in the script's `runs` table in `data/`, so history is shared.
- Web runs also append a row to the Sheet's Log tab. This is best effort: if the Sheet is unreachable the run and the page are unaffected. (planned)

## What exists now (built)

- `scripts/run_script.py` runs one script as its own process:
  ```
  python scripts/run_script.py prime_hunter --params '{"start": 1, "end": 50}'
  ```
  It validates the parameters, calls `main(params)`, prints the result, records the run and exits with 0 (succeeded), 1 (failed) or 2 (could not start: unknown script, bad parameters). It refuses `runner` and itself.
- `scripts/utils/params.py` validates and converts parameter values against a script's `PARAMS` list.
- These scripts accept parameters and declare `PARAMS`: `prime_hunter`, `db_report`, `restart_pi`, `pulse_monitor`. `git_pull_update` takes none. `test_connection` still only has its legacy entry point, which `run_script.py` handles.

### Parameters for a script

A script declares what it accepts at module level:

```python
PARAMS = [
    {"name": "start", "label": "Start (inclusive)", "type": "int", "required": True},
    {"name": "mode", "label": "Mode", "type": "choice", "options": ["a", "b"], "default": "a"},
]
CONFIRM = "Shown in an Are you sure? box before this script runs"   # optional

def main(params=None):
    if params is None:
        ...  # started from the Sheet: read Parameter-N as before
    ...      # started from Pi Control: params is a validated dict
    return (success, message, details)
```

Types: `str`, `int`, `float`, `bool`, `date` (YYYY-MM-DD), `choice` (with `options`). Optional keys: `label`, `default`, `required`, `min`, `max`. Unknown names, wrong types and out-of-range values are rejected before the script runs. `main()` with no argument still works for scripts that have not been converted. The return value is unchanged.

## Planned behaviour

- **Script list:** every script in `scripts/` that has a `main`, except non-task files (`runner`, `run_script`, `utils`, grid internals). The same set as the Config sheet.
- **Run:** one tap, with an "Are you sure?" box for scripts that set `CONFIRM`. Parameter values are remembered per script.
- **Stop:** ends the script and its child processes, and records the run as failed ("Stopped by user").
- **Output:** live while running, kept per run. The last 20 per script are retained.
- **No overlap:** a script cannot be started twice from the web app. A Sheet run is not yet checked against this.
- **Timeout:** 30 minutes by default, per-script override.
- **Looping scripts** run until stopped.

## Access and safety

- Reachable only over Tailscale (or localhost while developing). Never exposed to the internet, no Funnel.
- No password: being on the tailnet is the control. Only one user is assumed.
- Only scripts found in `scripts/` can run; there is no way to type a command. Parameters are validated on the server, and passed to the script as JSON, never through a shell.
- Runs as its own low-privilege systemd service, separate from `remote-worker.service`.

## Setup (planned)

1. Install Tailscale on the Pi and sign in; it is already installed on the phone.
2. `git pull` on the Pi, then `uv sync` to install the web dependencies (`fastapi`, `uvicorn`).
3. Install and start the Pi Control service, bound to the Pi's Tailscale address (`<pi-tailscale-ip>`).
4. On the phone, open `http://<pi-tailscale-ip>:8051` and add it to the home screen.

The exact commands go in [setup.md](setup.md) when the service exists.

## Trying it on a laptop (planned)

`python debug_control.py` will start the app on `http://127.0.0.1:8051` with fake demo scripts and its own throwaway data, so nothing touches real history and the Sheet is never contacted. `--real` runs the real scripts instead. Modelled on `debug_ui.py` for the grid dashboard.

## Not part of this

- The public grid dashboard ([grid.md](grid.md)); that is a separate app.
- Notifications on failure, retiring the Sheet, or multiple users.
