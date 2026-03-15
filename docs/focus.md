# Raspberry Pi Remote Worker - Setup & Management

## Table of Contents
1. [Connection Methods](#connection-methods)
2. [Initial Setup (Automated)](#initial-setup-automated)
3. [Manual Setup Steps](#manual-setup-steps)
4. [Managing Credentials](#managing-credentials)
5. [Repository & Service Management](#repository--service-management)
6. [Helper Scripts](#helper-scripts)
7. [Troubleshooting](#troubleshooting)

---

## Connection Methods

Two options are available for connecting to your Raspberry Pi:
- **SSH**: Terminal-based access for command-line operations
- **Raspberry Pi Connect**: Browser-based remote management interface

> **Note:** When using Raspberry Pi Connect, the system runs Linux commands.

---

## Initial Setup (Automated)

The fastest way to get started is with the automated one-line setup:

```bash
curl -sSL https://raw.githubusercontent.com/rhyslwells/RaspPi-Remote-Worker/main/setup.sh | bash -s -- 192.168.1.100
```

This command handles everything:
- ✅ Update system packages
- ✅ Install Python 3.10+ and git
- ✅ Install UV (package manager)
- ✅ Clone the repository
- ✅ Create virtual environment
- ✅ Install all Python dependencies
- ✅ Configure systemd service for auto-start

**What is systemd?** It's a Linux system and service manager that enables scripts to run as background services that automatically start on boot. Your Remote Worker will launch whenever the Raspberry Pi powers on.

> **Note:** The script will ask for confirmation and may prompt for your password (for `sudo` commands).

---

## Manual Setup Steps

If you prefer to set up manually or troubleshoot:

### 1. Clone the Repository

```bash
cd ~
git clone https://github.com/rhyslwells/RaspPi-Remote-Worker.git
cd RaspPi-Remote-Worker
```

### 2. Create and Activate Virtual Environment

```bash
uv venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies

```bash
uv sync
```

### 4. Verify Installation

```bash
python3 runner.py --help
```

---

## Managing Credentials

### Strategy
Store sensitive credentials locally on the Raspberry Pi in a gitignored folder, then reference them from the codebase.

### Setup Process
1. Create a dedicated local folder on the Raspberry Pi for sensitive files
2. Copy/paste the contents of `credentials.json` into a new file in that folder
3. Update your code to reference these local files instead of committing them to git

This keeps secrets safe from version control while allowing the code to access them at runtime.

---

## Repository & Service Management

### Repository Syncing
Use git commands when SSH'd into the Pi to pull the latest changes:

```bash
git pull origin main
```

### Setting Up Auto-Start Service

Once the automated setup completes, the systemd service is configured automatically. To manually manage it:

```bash
# SSH into Pi
ssh pi@192.168.1.100

# Enable and start the service
sudo systemctl enable remote-worker.service
sudo systemctl start remote-worker.service

# Check service status
sudo systemctl status remote-worker.service
```

---

## Helper Scripts

Use the helper script for ongoing management of your Remote Worker:

- **Linux/Mac:** `raspi-helper.sh`
- **Windows:** `raspi-helper.ps1`

> TODO: Add detailed explanations of helper script functionality

---

## Troubleshooting

### Git Pull Fails with Permission Denied

**Problem:** Permission denied when running `git pull`

**Solution:**
- Set up SSH keys for GitHub (recommended) or use HTTPS with a personal access token
- Verify your remote URL: `git remote -v`

---

## Upcoming Tasks

- [ ] Phase 2: Install Python dependencies on Raspberry Pi
- [ ] Phase 2: Create and enable systemd service (if not using automated setup)
- [ ] Document helper scripts (`raspi-helper.sh` and `raspi-helper.ps1`)





