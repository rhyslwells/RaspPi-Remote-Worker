# Repository Structure

```
RaspPi-Remote-Worker/
├── scripts/
│   ├── runner.py              # Polling loop, dynamic script loader (service entry point)
│   ├── test_connection.py     # Sheet connectivity check (special-cased in runner)
│   ├── prime_hunter.py        # Example parameterised task
│   ├── git_pull_update.py     # Pi self-update (pull, uv sync, restart-needed report); no ControlPanel
│   ├── pulse_monitor.py       # Notes for a future health-check script (not runnable)
│   ├── other-ideas.py         # Notes for future scripts (not runnable)
│   └── utils/
│       ├── control_panel.py   # ControlPanel + ScriptStatus (all Sheets I/O)
│       └── list_sheets.py     # Diagnostic: list sheets the credentials can see
├── docs/
│   ├── setup.md               # Setup, service, helper script, troubleshooting
│   ├── scripts.md             # Runner, sheet layout, ControlPanel API, writing scripts
│   ├── script_ideas.md        # Script backlog (ideas)
│   ├── improvements.md        # Review findings (proposed)
│   ├── knowledge/             # Symbolic_Regression, SD_CARD_FORMAT
│   └── notes.md               # gitignored scratch (private; do not read or copy)
├── setup_initial.sh           # Pi first-time setup
├── setup_systemd.sh           # Pi service install
├── raspi-helper.sh            # SSH helper functions (source it)
├── pyproject.toml, uv.lock    # Dependencies (uv) and the project version; lock must match the version
├── CHANGELOG.md               # One entry per version
├── README.md
├── credentials.json           # SECRET, gitignored
├── .raspi-config              # Pi IP for the helper script; currently tracked in git (private-ish, do not edit unasked)
├── logs/                      # Runtime logs (gitignored *.log)
└── .claude/                   # This directory
```

## Where new things go

| Adding | Location |
|--------|----------|
| A task the Pi should run | `scripts/<name>.py` following [SCRIPT_CONTRACT.md](SCRIPT_CONTRACT.md) |
| Shared Sheets or helper code | `scripts/utils/` |
| Documentation for a script | a short paragraph in `docs/scripts.md` |
| Setup or ops reference | `docs/setup.md` |
| General learning notes | `docs/knowledge/` |
| A half-formed script idea | `docs/script_ideas.md` |
| A proposed change to the runner or sheet | `docs/improvements.md` |
| Pi-side automation | root-level `*.sh`, matching existing setup scripts |

## Surface area policy

- Keep the runner and `ControlPanel` small; new behavior belongs in scripts first.
- Do not create new top-level directories, packages (`src/`), test frameworks or CI config unless requested. `pyproject.toml` mentions a `src/remote_worker` package that does not exist; leave it unless asked.
- Do not create supplementary examples or scaffolding unrequested.
- Scripts use relative `from utils.control_panel import ...` after a `sys.path.insert` of their own directory. Keep that pattern.
