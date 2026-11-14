---
name: docs-capture
description: Sync documentation (docs/, README, .claude/) with code changes made in the session. Proposes edits and asks before applying.
---

# Docs capture

Bring documentation in line with what was actually implemented. Only update what the change warrants.

## Steps

1. Run `git status` and `git diff --name-only`; recall the session goal.
2. Map changes to docs:

| Change | Update |
|--------|--------|
| New or changed task script | `docs/scripts/<NAME>_README.md` if setup is non-obvious; `.claude/REPOSITORY_STRUCTURE.md` file list |
| Script contract, status values, sheet columns | `.claude/SCRIPT_CONTRACT.md`, `.claude/ARCHITECTURE.md`, README status table |
| `setup_*.sh`, systemd, `raspi-helper.sh` | `.claude/DEPLOYMENT.md`, `docs/scripts/SETUP_SH_README.md`, `SERVICE_README.md`, `RASPI_HELPER_SH.md` |
| New dependency | `.claude/CODING_STANDARDS.md`, `.claude/CLAUDE.md` environment section |
| Fixed a "Known inconsistency" | Remove it from `.claude/CLAUDE.md` and `DOCUMENTATION.md` |
| Idea only, not built | `docs/script_ideas.md` marked as planned |

3. Show proposed edits (file, what changes, why) and wait for approval before applying.

## Rules

- Docs reflect the implementation, not intentions; mark planned work as planned
- Mermaid for diagrams, no emojis, sentence-case headings
- No secrets or private details (credentials, key IDs, Pi IP)
- Do not edit `.claude/CLAUDE.md` without approval, since it is the instruction file
- Flag stale README / `project-overview.md` links rather than silently rewriting them
- Use absolute dates, not "today"

## Output

```
DOCS CAPTURE
Proposed: [file - change - reason]
Stale but untouched: [file - issue]
Apply? (yes/no)
```
