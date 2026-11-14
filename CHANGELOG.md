# Changelog

Version lives in `pyproject.toml` (`version = "..."`). Newest first. Bump rules are in [docs/scripts.md](docs/scripts.md#versioning).

## 0.2.0 - 2026-11-14

- Added `scripts/git_pull_update.py`: update the Pi from a Config sheet cell (pull, `uv sync` if dependencies changed, "restart needed" report). Works when the service PATH lacks `git`.
- Update messages now show the version change (`v0.1.0 -> v0.2.0`).
- Docs consolidated into README, `docs/setup.md`, `docs/scripts.md`, `docs/faq.md`; added `docs/script_ideas.md` and `docs/improvements.md`.
- `raspi-helper.sh` now uses the real Pi path `~/Desktop/RaspPi-Remote-Worker` and prints the version after an update.
- Added `.claude/` project guidance and skills.

## 0.1.0

- Initial release: runner, `ControlPanel`, `test_connection.py`, `prime_hunter.py`, setup scripts and helper script.
