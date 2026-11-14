# Workflow

## Develop, verify, deploy

1. **Develop locally (Windows).** Edit scripts in `scripts/`. Activate `.venv` (`.venv\Scripts\activate` in PowerShell) or use `uv run`.
2. **Verify without side effects first.**
   - Pure logic (e.g. `find_primes` in `prime_hunter.py`): import and call the function directly
   - Syntax / lint: `python -m py_compile scripts/<file>.py`, `ruff check scripts/`
   - Anything that constructs `ControlPanel` talks to the live Google Sheet and needs `credentials.json`; only do this when the user asks
3. **Verify against the sheet when asked.** Run from the repo root so `credentials.json` resolves: `python scripts/test_connection.py`. To exercise a script as the runner would, set its row to `START` on the sheet and watch `Log`.
4. **Deploy when asked.** Commit, push, then update the Pi (see [DEPLOYMENT.md](DEPLOYMENT.md)).

## There is no automated test suite

`pytest` is listed in the dev extras but no tests exist. Do not scaffold a test framework unasked. Verification means: unit-call pure functions, run `py_compile`/ruff, and when authorised, run the script against the sheet. State clearly which of these you did and which you could not do.

## Changing scope

- Prefer adding a script over modifying the runner or `ControlPanel`.
- Changes to the items under "Ask before changing" in [CLAUDE.md](CLAUDE.md) get a short proposal first.
- A change that touches the sheet layout, status enum or script contract also affects the live sheet and every script: list what else must change.

## Versioning

The version is `pyproject.toml` `version`; history is `CHANGELOG.md`; the rules and steps are in `docs/scripts.md#versioning`. The user wants it incremented whenever a change is going to be pushed to the Pi.

- When finishing a change that is meant to be committed or pushed (anything beyond a trivial docs typo), propose the bump level (patch: fix/tweak; minor: new script, new runner or sheet behaviour, or anything needing a restart) and apply it together with a `CHANGELOG.md` entry.
- Always run `uv lock` after changing `version`. `uv.lock` records the project version, and `git_pull_update.py` runs `uv sync --locked`, so a stale lock makes the Pi update fail.
- The README header also states the version; update it in the same commit.
- Commit and push only when asked; the bump itself is part of the change, not a separate step.

## Git

- Branch is `main`; the Pi pulls `origin main`, so a push is effectively a deploy. Only commit or push when asked.
- Commit messages: plain imperative text, no emojis (matches existing history, e.g. "Refactor setup scripts and remove PowerShell helper").
- Never stage `credentials.json`, `.raspi-config` changes, `.env*`, `logs/`, `.history/`.
