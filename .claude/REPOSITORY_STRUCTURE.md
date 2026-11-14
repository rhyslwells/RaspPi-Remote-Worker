# Repository Structure

```
RaspPi-Remote-Worker/
├── scripts/
│   ├── runner.py              # Polling loop, dynamic script loader (service entry point)
│   ├── test_connection.py     # Sheet connectivity check (special-cased in runner)
│   ├── prime_hunter.py        # Example parameterised task
│   ├── pulse_monitor.py       # Notes for a future health-check script (not runnable)
│   ├── other-ideas.py         # Notes for future scripts (not runnable)
│   └── utils/
│       ├── control_panel.py   # ControlPanel + ScriptStatus (all Sheets I/O)
│       └── list_sheets.py     # Diagnostic: list sheets the credentials can see
├── docs/
│   ├── Raspberry Pi Remote Worker - Setup & Management.md
│   ├── scripts/               # One README per script / tool
│   ├── knowledge/             # Reference notes (BASH, POWERSHELL, Symbolic_Regression)
│   ├── other/                 # Pi setup, SD card, VS Code SSH, env setup
│   ├── handy.md, later.md, script_ideas.md
│   └── notes.md               # gitignored scratch
├── setup_initial.sh           # Pi first-time setup
├── setup_systemd.sh           # Pi service install
├── raspi-helper.sh            # SSH helper functions (source it)
├── pyproject.toml, uv.lock    # Dependencies (uv)
├── project-overview.md        # Architecture overview (partly TODO)
├── README.md
├── credentials.json           # SECRET, gitignored
├── .raspi-config              # Pi IP, gitignored in practice (do not commit changes)
├── logs/                      # Runtime logs (gitignored *.log)
└── .claude/                   # This directory
```

## Where new things go

| Adding | Location |
|--------|----------|
| A task the Pi should run | `scripts/<name>.py` following [SCRIPT_CONTRACT.md](SCRIPT_CONTRACT.md) |
| Shared Sheets or helper code | `scripts/utils/` |
| Documentation for a script | `docs/scripts/<NAME>_README.md` |
| Setup or ops reference | `docs/other/` or the Setup & Management doc |
| General learning notes | `docs/knowledge/` |
| A half-formed script idea | `docs/script_ideas.md` |
| Pi-side automation | root-level `*.sh`, matching existing setup scripts |

## Surface area policy

- Keep the runner and `ControlPanel` small; new behavior belongs in scripts first.
- Do not create new top-level directories, packages (`src/`), test frameworks or CI config unless requested. `pyproject.toml` mentions a `src/remote_worker` package that does not exist; leave it unless asked.
- Do not create supplementary examples or scaffolding unrequested.
- Scripts use relative `from utils.control_panel import ...` after a `sys.path.insert` of their own directory. Keep that pattern.
