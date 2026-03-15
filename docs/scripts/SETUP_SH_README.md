# Setup Scripts Overview

This document explains the two setup scripts used to deploy RaspPi Remote Worker:
1. **setup_initial.sh** - Initial system setup and dependencies
2. **setup_systemd.sh** - Systemd service configuration for auto-start

---

## setup_initial.sh (Initial Setup)

**What it does:**
- Verifies the script is running on a Raspberry Pi
- Updates system packages (`apt update`, `apt upgrade`)
- Installs Python 3, git, and build tools
- Creates a Python virtual environment (`.venv`)
- Installs UV package manager
- Installs all Python dependencies via `uv sync`

**How to run:**
```bash
bash setup_initial.sh
```

**Duration:** ~5-10 minutes (depending on internet speed and Raspberry Pi model)

**Requirements:**
- Running as non-root user (e.g., `pi` or `rhyslwells`)
- Internet connection
- Sudo access (you'll be prompted for your password)

**What happens:**
1. Script verifies it's running on a Raspberry Pi (with override option)
2. Confirms you want to proceed
3. Updates system packages (~2-3 minutes)
4. Installs required tools
5. Creates isolated Python environment
6. Installs project dependencies

---

## setup_systemd.sh (Service Configuration)

**What it does:**
- Creates a `logs/` directory for service output
- Creates systemd service file (`/etc/systemd/system/remote-worker.service`)
- Registers the service to auto-start on boot
- Enables automatic restarts if the service crashes

**Service configuration:**
- **Service name:** Remote Worker - Google Sheets Task Runner
- **User:** rhyslwells
- **Working directory:** `/home/rhyslwells/Desktop/RaspPi-Remote-Worker`
- **Startup command:** Runs `scripts/runner.py` via the virtual environment
- **Auto-restart:** Yes (restarts after 10 seconds if it crashes)
- **Logging:** Saves output to `logs/service.log`

**How to run:**
```bash
bash setup_systemd.sh
```

**Requirements:**
- `setup_initial.sh` must have completed successfully
- Running as non-root user
- Sudo access (you'll be prompted for your password)

---

## Setup Workflow

**First time setup:**
```bash
# Step 1: Initial setup
bash setup_initial.sh

# Step 2: Configure systemd service
bash setup_systemd.sh

# Step 3: Deploy credentials
scp credentials.json rhyslwells@<pi-ip>:~/Desktop/RaspPi-Remote-Worker/

# Step 4: Start the service
sudo systemctl start remote-worker.service
```

---

## Managing the Service

Once `setup_systemd.sh` has run, use these commands:

```bash
# Check service status
sudo systemctl status remote-worker.service

# Start the service
sudo systemctl start remote-worker.service

# Stop the service
sudo systemctl stop remote-worker.service

# Restart the service
sudo systemctl restart remote-worker.service

# View logs in real-time
sudo journalctl -u remote-worker.service -f

# View last 50 lines of logs
sudo journalctl -u remote-worker.service -n 50

# View service file
cat /etc/systemd/system/remote-worker.service
```

---

## Troubleshooting

**Command not found errors in setup_initial.sh:**
- Ensure you're in the correct directory: `~/Desktop/RaspPi-Remote-Worker/`
- Check that the script has execute permissions: `chmod +x setup_initial.sh`

**"Please don't run this script as root":**
- Don't use `sudo` when running these scripts
- Run as the regular user (e.g., `pi` or `rhyslwells`)
- The scripts will prompt for sudo when needed

**Service won't start:**
- Check credentials are deployed: `ls -la ~/Desktop/RaspPi-Remote-Worker/credentials.json`
- Check logs: `sudo journalctl -u remote-worker.service -n 50`
- Verify service file: `sudo systemctl status remote-worker.service`





