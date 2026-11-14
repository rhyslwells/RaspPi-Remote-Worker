# Script Contract (rules for Claude)

The contract, template and registration steps are in [docs/scripts.md](../docs/scripts.md#writing-a-script). Reference implementations: `scripts/prime_hunter.py` (parameters), `scripts/test_connection.py` (minimal). Rules to apply on top:

1. `main()` returns exactly `(bool, str, str)` on every path, including error paths. `None` produces the Log error "cannot unpack non-iterable NoneType object".
2. Return `(False, message, details)` for expected failures; do not raise.
3. Parameters arrive as strings and may be missing or blank: convert and validate at the top of `main()`.
4. Keep runtime short and bounded. The runner is single-threaded and has no timeout.
5. No `sys.exit()`, no `os.chdir()`.
6. Keep the `sys.path.insert(0, str(Path(__file__).parent))` + `from utils.control_panel import ControlPanel` pattern.
7. Do not put secrets in `message` or `details`; both are written to a shared sheet. Keep `details` well under 50,000 characters.
8. New scripts use `main()`; the `test_sheet_connection` special case in `runner.py` is legacy.
9. Constructing `ControlPanel` hits the live sheet. Do not do it while verifying unless the user asked.
10. New dependency: add to `pyproject.toml` and tell the user the Pi must `uv sync`.
11. Persist script data with `utils.script_db.connect("<script>")` (stdlib SQLite, `data/<script>.db`), not ad hoc files. A database error must not fail the run: catch it and carry on (see `store_primes` in `prime_hunter.py`). The runner already records each run's parameters and result in the `runs` table; do not duplicate that.
12. Anything that stops or restarts the service or the Pi must schedule it and return first (see `restart_pi.py`); never do it inline.
13. The service PATH is the venv `bin` only: call system tools by absolute path (`/usr/bin/sudo`) or search fallback dirs, as `git_pull_update.py` does. Use `sudo -n` so a missing password fails instead of hanging.
14. Do not name another script in a Config `Description` or `Details` cell: rows are found by searching the whole sheet.
15. Document a new script in `docs/scripts.md` (one short paragraph under "Included scripts"), not in a new file.
