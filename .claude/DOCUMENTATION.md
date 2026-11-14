# Documentation Policy

Docs reflect the implementation, stay concise, and say each thing once.

## Where to document

| Location | Contents (one home each) |
|----------|--------------------------|
| `README.md` | Overview, how it works, status table, quick start, layout, doc index |
| `docs/setup.md` | Google Cloud, Pi setup, install, service commands, helper script, troubleshooting |
| `docs/scripts.md` | Runner behaviour, sheet layout, status lifecycle, `ControlPanel` API, script template, included scripts |
| `docs/script_ideas.md` | Backlog of scripts, marked as ideas |
| `docs/improvements.md` | Review findings and proposed changes, marked as proposed |
| `docs/knowledge/` | General reference notes unrelated to the code path |
| Code comments | Non-obvious WHY only |
| `.claude/` | Rules and gotchas for Claude; link to the docs above instead of copying them |

## Rules

- Do not write documentation unless the change warrants it. A new script gets a short paragraph in `docs/scripts.md`, not a new file.
- Before adding text, check whether it already exists elsewhere; link instead of repeating.
- Mark planned work as planned. `pulse_monitor.py` and `other-ideas.py` are notes, not features.
- Mermaid for diagrams; no emojis; sentence-case headings.
- No secrets or private details: no credentials, key IDs, passwords, Wi-Fi names, account emails, or the Pi's IP or login name. Use `<pi-ip>` and `<pi-user>`.
- `docs/notes.md` is gitignored scratch and may hold private details; never copy from it.
