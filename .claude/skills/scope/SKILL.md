---
name: scope
description: Lock the scope of a change to the Pi remote worker (new task script, fix, runner or sheet change) before implementing. Use at the start of any non-trivial change.
---

# Scope

Define one change precisely so implementation stays small. Max a few minutes.

## Steps

1. **Goal** - one or two sentences. If it needs more, split it.
2. **Classify the change**, because the class sets the risk:
   - Task script (new or edited) in `scripts/` - low risk
   - `ControlPanel` / `utils` - medium (every script depends on it)
   - `runner.py`, sheet layout, `ScriptStatus`, script contract, systemd unit, `setup_*.sh` - high, "ask before changing" (see CLAUDE.md)
   - Docs only
3. **Contract**
   - Sheet inputs: which `Parameter-N` values, their meaning and validation
   - Result: the `(success, message, details)` for the success and each failure case
   - Side effects: sheet writes, files, network, anything on the Pi
4. **Acceptance criteria** - 3 to 5 testable statements, e.g. "returns `(False, 'Missing parameters', ...)` when fewer than 2 parameters are set".
5. **Constraints** - new dependencies? runtime length (runner is single-threaded)? needs live sheet or Pi to verify?
6. **Effort** - tiny / small / medium / large (split if large).

## Output

```
SCOPE LOCKED
Goal:
Class: [script | utils | high-risk | docs]
Contract: params -> result tuple; side effects
Acceptance criteria:
  1.
  2.
  3.
Constraints:
Verification plan: [what can be checked locally vs needs live sheet / Pi]
Effort:
```

Then ask whether to proceed. High-risk classes need explicit approval.

## Red flags - split or stop

- "While we are here, also refactor X" - separate scope
- Touches sheet column layout and scripts and runner at once
- Adds a dependency for a one-off task
- No way to verify short of running on the live system and the user has not agreed to that
