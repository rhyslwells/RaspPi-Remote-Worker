# Deployment and Operations

All Pi-facing actions are outward-facing. Run them only when the user asks.

## Environment

| Item | Value |
|------|-------|
| Dev machine | Windows 11; PowerShell or Git Bash; VS Code with Remote SSH |
| Target | Raspberry Pi, Raspberry Pi OS, user `rhyslwells` |
| Pi address | stored in `.raspi-config` (gitignored, private) |
| Service | `remote-worker.service` (systemd) |
| Entry point | `.venv/bin/python3 scripts/runner.py`, working dir = repo root |
| Logs | `logs/service.log` (and `journalctl -u remote-worker.service`) |
| Python env | `uv sync` into `.venv` |

## Scripts

| Script | Purpose |
|--------|---------|
| `setup_initial.sh` | First-time Pi install: clone, uv, venv, deps |
| `setup_systemd.sh` | Writes `/etc/systemd/system/remote-worker.service`, `daemon-reload`, `enable` |
| `raspi-helper.sh` | Source it in bash/WSL for SSH helpers: `connect_raspi`, `copy_credentials_to_raspi`, `start/stop/restart_raspi_service`, `watch_raspi_logs`, `update_raspi_repo`, `test_raspi_connection`, `get_raspi_info` |

Details: `docs/scripts/SETUP_SH_README.md`, `SERVICE_README.md`, `RASPI_HELPER_SH.md`, `docs/Raspberry Pi Remote Worker - Setup & Management.md`.

## Update flow

1. Change and verify locally (see [WORKFLOW.md](WORKFLOW.md)).
2. Commit and push to `main`.
3. On the Pi: `git pull origin main`, `uv sync`, `sudo systemctl restart remote-worker.service` (this is what `update_raspi_repo` does).
4. Check `systemctl status` and the tail of `logs/service.log`.

## Credentials

- `credentials.json` is a service-account key. It reaches the Pi only via `scp`, never via git.
- The Google Sheet must be shared with the service account's email.
- Never echo its contents, put it in docs, or include it in a commit, even to debug.
- If it is ever committed or pasted somewhere, tell the user to rotate the key.

## Constraints

- Low-power hardware: avoid adding heavy dependencies; prefer the standard library.
- Pi may be offline or sleeping: the runner already catches loop-level errors and sleeps 30 s. Do not add retry layers on top without asking.
- Path inconsistency to be aware of: systemd unit uses `/home/rhyslwells/Desktop/RaspPi-Remote-Worker`; `raspi-helper.sh` uses `~/RaspPi-Remote-Worker`. Confirm the real path with the user before running anything that depends on it.
- `*.sh` files must keep LF line endings and be executable (they run on Linux). Do not let an editor rewrite them to CRLF.
