# RaspPi Remote Worker

## Overview

**RaspPi Remote Worker** is a Raspberry Pi-based task execution system that enables remote, scheduled, and on-demand task management through a simple Google Sheets control panel.

The system uses a classic "Remote Worker" architecture: a persistent service runs on a Raspberry Pi, polling a Google Sheet for task commands, executing local Python scripts, and reporting execution status back to the sheet. No complex web UI or SSH access needed—just update a spreadsheet cell to trigger tasks.

**Control Panel:** [Google Sheets Dashboard](https://docs.google.com/spreadsheets/d/1d9QU9st_j2gY4Qp7gkhNu5PB016w58sfkjGkW4JydD8/edit?gid=0#gid=0)

## Documentation

Complete setup and implementation guides are in the `docs/` folder:

* [Project Overview](./docs/0-project-overview.md) — Architecture and system design
* [Phase 1: Environment Setup](./docs/phase-1-environment-setup.md) — Google Cloud API, repository setup
* [Phase 2: Runner Logic](./docs/phase-2-runner-logic.md) — Core polling loop and systemd service
* [Phase 3: Implementation Ideas](./docs/phase-3-implementation-ideas.md) — Example scripts to get started

## System Components

### 1. The Controller (Google Sheets)
A spreadsheet with columns for `Script Name` and `Status`, acting as a centralized control panel.

### 2. The Worker (Raspberry Pi)
A systemd service running a Python loop that:
* Polls the Google Sheet API for task commands
* Detects "START" flags and executes corresponding scripts
* Logs execution and updates status back to the sheet
* Ensures persistence across reboots

### 3. The Scripts (`/scripts` folder)
Modular Python scripts that perform specific tasks. Examples included to get you started.

## Project Structure

```
/
├── runner.py                # Main polling and execution loop
├── pyproject.toml          # Python dependencies (gspread, oauth2client)
├── credentials.json        # ⚠️ Service account credentials (NEVER commit)
├── .gitignore             # Excludes credentials.json
├── /scripts/              # Task script modules
├── /docs/                 # Complete documentation
└── /logs/                 # Service logs (generated at runtime)
```

## How It Works

1. **Setup:** Google Cloud credentials and Raspberry Pi environment configured
2. **Service:** Systemd service starts on Pi boot, beginning the polling loop
3. **Command:** User updates a cell in the Google Sheet to "START"
4. **Execution:** Worker detects the command, runs the corresponding script from `/scripts`
5. **Feedback:** Execution log and status ("SUCCESS" or "FAILED") written back to the sheet

## Control Panel Status Reference

| Status | Meaning |
|--------|---------|
| `IDLE` | Ready to execute (default) |
| `START` | Trigger script execution |
| `RUNNING` | Script currently executing |
| `SUCCESS` | Last execution completed successfully |
| `FAILED` | Last execution encountered an error |

## Getting Started

### Prerequisites

* Raspberry Pi (any model) with Raspberry Pi OS
* Python 3.10+
* Google Cloud project with service account credentials
* Internet access (both Pi and primary machine)

### Installation

See [Phase 1: Environment Setup](./docs/phase-1-environment-setup.md) for detailed instructions on:
* Setting up Google Cloud API credentials
* Configuring the Raspberry Pi
* Installing dependencies using `uv`

## Features

* **On-demand execution** — Trigger tasks anytime from the Google Sheet
* **Persistent service** — Automatic restart on Pi reboot via systemd
* **Simple control** — No SSH or complex CLI needed; update a spreadsheet cell
* **Modular scripts** — Easy to write and add your own task scripts
* **Execution logging** — Full logs stored locally and status tracked in the sheet
* **Multi-tasking ready** — Architecture supports future multiprocessing expansion

## Contributing

Contributions are welcome via issues or pull requests. Keep changes aligned with the modular architecture and documentation standards.

## License

This project is open source and intended for personal and educational use.
