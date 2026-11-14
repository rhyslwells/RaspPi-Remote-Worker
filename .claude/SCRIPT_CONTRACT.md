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
11. Document a new script in `docs/scripts.md` (one short paragraph under "Included scripts"), not in a new file.
