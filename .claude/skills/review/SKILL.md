---
name: review
description: Review a change to the Pi remote worker for contract, safety, secrets and fit with existing patterns before committing.
---

# Review

Check the current diff (`git diff`, `git status`) against project standards.

## Checklist

**Safety and secrets (highest priority)**
- [ ] No `credentials.json`, key material, Pi IP or `.raspi-config` content in the diff, docs or log messages
- [ ] Nothing untracked and sensitive about to be staged
- [ ] No command injection: sheet values (script name, parameters) are untrusted input. Script names must not be used to build paths or shell commands without validation; no `shell=True` with sheet data
- [ ] No destructive operations added to `*.sh` without a prompt

**Contract**
- [ ] Task scripts return `(bool, str, str)` on every path
- [ ] Status enum, sheet columns, runner loop and systemd unit unchanged, or the change was approved and its knock-on effects listed

**Fit**
- [ ] Follows existing patterns (`sys.path.insert`, `ControlPanel` for all Sheets I/O, logging style)
- [ ] Style per `.claude/CODING_STANDARDS.md`; no emojis in new docs/comments/commit text; no debug leftovers
- [ ] No unrequested dependencies, scaffolding or refactors
- [ ] Shell scripts still LF endings and executable

**Runtime on the Pi**
- [ ] Bounded runtime and memory; will not stall the 10 s poll loop for long
- [ ] Works when started from the repo root under systemd

**Docs**
- [ ] Note anything in `docs/` or `.claude/` that is now stale (for `/docs-capture`)

## Output

```
REVIEW
Safety: ok / issues
Contract: ok / issues
Fit: ok / issues
Runtime: ok / issues
Stale docs: [list]
Result: APPROVE / REQUEST CHANGES
```

Findings should cite `file:line` and say what breaks, ranked by severity. Do not commit or push as part of review.
