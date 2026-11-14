# Deployment and Operations (rules for Claude)

Setup steps, service commands, update flow and helper-script commands are in [docs/setup.md](../docs/setup.md). Rules to apply on top:

All Pi-facing actions are outward-facing and affect a live service. Run them only when the user asks.

- Do not run `ssh`, `scp`, anything from `raspi-helper.sh`, `systemctl`, or `scripts/runner.py` unprompted. Do not run anything that constructs `ControlPanel` against the live sheet unprompted.
- `credentials.json`, `.raspi-config`, `.env*` and `docs/notes.md` are private. Do not read, print, copy or commit them. If a key is ever committed or pasted somewhere, tell the user to rotate it.
- Do not put the Pi's IP, login name, passwords or Wi-Fi details in docs; use placeholders like `<pi-ip>`.
- The service runs from the repo root as `.venv/bin/python3 scripts/runner.py`; the repo is at `~/Desktop/RaspPi-Remote-Worker`, but `raspi-helper.sh` (three functions) uses `~/RaspPi-Remote-Worker`. Confirm the real path before running anything that depends on it.
- A push to `main` is effectively a deploy (`update_raspi_repo` pulls it). Commit or push only when asked.
- Low-power hardware: avoid heavy dependencies; prefer the standard library.
- `*.sh` files must keep LF line endings and stay executable.
