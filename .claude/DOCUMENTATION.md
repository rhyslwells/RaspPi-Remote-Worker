# Documentation Policy

Docs should reflect the implementation, stay concise, and avoid repeating each other.

## Where to document

| Location | Purpose |
|----------|---------|
| `README.md` | Overview, quick start, status reference |
| `docs/Raspberry Pi Remote Worker - Setup & Management.md` | End-to-end setup and day-to-day management |
| `docs/scripts/<NAME>_README.md` | One page per script or shell tool (existing pattern) |
| `docs/other/` | Pi, SD card, SSH and environment setup |
| `docs/knowledge/` | General reference notes (bash, PowerShell, theory) |
| `docs/script_ideas.md`, `docs/later.md` | Backlog ideas; clearly not implemented |
| Code comments | Non-obvious WHY only |
| `.claude/` | Assistant guidance; keep it in sync with code, not aspirational |

## Rules

- Do not write documentation unless the change warrants it. A new script needs a README only if setup is non-obvious.
- Mark planned work as planned. `pulse_monitor.py` and `other-ideas.py` are notes, not features.
- Use Mermaid for diagrams, not ASCII art.
- No emojis, no secrets: never include credential contents, service-account emails, spreadsheet IDs beyond what is already in README, or the Pi IP.
- Sentence-case headings.

## Known stale docs

README and `project-overview.md` link to `docs/0-project-overview.md` and `docs/phase-*.md`, which do not exist, and show `runner.py` at the repo root. Fix these only when asked or when a task touches those sections; `/docs-capture` should flag them rather than rewrite silently.
