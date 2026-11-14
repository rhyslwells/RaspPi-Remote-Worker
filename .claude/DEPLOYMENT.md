# Deployment and Operations (rules for Claude)

Setup steps, service commands, update flow and helper-script commands are in [docs/setup.md](../docs/setup.md). Rules to apply on top:

All Pi-facing actions are outward-facing and affect a live service. Run them only when the user asks.

- Do not run `ssh`, `scp`, anything from `raspi-helper.sh`, `systemctl`, or `scripts/runner.py` unprompted. Do not run anything that constructs `ControlPanel` against the live sheet unprompted.
- `credentials.json`, `.raspi-config`, `.env*` and `docs/notes.md` are private. Do not read, print, copy or commit them. If a key is ever committed or pasted somewhere, tell the user to rotate it.
- Do not put the Pi's IP, login name, passwords or Wi-Fi details in docs; use placeholders like `<pi-ip>`.
- The service runs from the repo root as `.venv/bin/python3 scripts/runner.py`; the repo is at `~/Desktop/RaspPi-Remote-Worker` on the Pi.
- A push to `main` is effectively a deploy (`update_raspi_repo` pulls it). Commit or push only when asked.
- Low-power hardware: avoid heavy dependencies; prefer the standard library.
- `restart_pi.py`, `git_pull_update.py` and anything that runs `sudo` act on the live Pi. Do not trigger them or mock-test with real `sudo`; test with mocked `subprocess` as was done for `restart_pi.py`.
- A change to `runner.py` or `scripts/utils/` needs a service restart after the pull; say so when proposing the deploy. The first restart onto a new runner must be done the old way (helper or SSH), since the old runner cannot be restarted by the new script.
- `data/*.db` holds run parameters and results: treat as private, never commit (gitignored) or paste. It is not backed up.
- `*.sh` files must keep LF line endings and stay executable.
