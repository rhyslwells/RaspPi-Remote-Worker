---
name: test
description: Verify a change to the Pi remote worker against its acceptance criteria and the script contract, using safe local checks first. There is no pytest suite in this repo.
---

# Test

Verify against the acceptance criteria. There are no committed tests, so verification is targeted checks.

## Levels (stop at the highest one the user has authorised)

1. **Static** - always
   - `python -m py_compile` on changed files
   - `ruff check` on changed files if available
   - Confirm `main()` exists and every return path is a 3-tuple of `(bool, str, str)`
2. **Local logic** - always, no network
   - Import the module and call pure helper functions directly (for example `prime_hunter.find_primes(1, 30)`)
   - Edge inputs: empty/blank parameter, non-numeric string, start > end, very large range (does it finish in reasonable time on a Pi?)
   - Importing a script must not execute work or touch the network at import time
3. **Live sheet** - only if the user asked
   - Run from the repo root so `credentials.json` resolves
   - `python scripts/test_connection.py`, or set the row to `START` and watch `Config` and `Log`
   - Confirm transitions IDLE/START -> RUNNING -> SUCCESS or FAILED and the Log row content
4. **Pi** - only if the user asked: pull, `uv sync`, restart service, check `logs/service.log`

## Contract checks

- Return type is exactly `(success, message, details)`
- Failure cases return `False` with an informative message instead of raising
- Missing / extra parameters handled
- No secrets in `message` or `details` (they are written to a shared sheet)

## Output

```
TEST COMPLETE
Criterion 1: PASS / FAIL / NOT RUN (how)
Criterion 2: ...
Levels run: static | local | live sheet | Pi
Not run: [and why]
Result: PASS / FAIL
```

Report failures with the actual output. Do not move to `/review` on a FAIL.
