# Quick Start: Complete Raspberry Pi Setup (15-20 minutes)

This is a high-level overview that ties together **RASP_PI_README.md** and **SERVICE_README.md** into a simple 4-step process.

---

## Overview: What You're Setting Up

You have **two main tasks**:
1. **Connect to your Raspberry Pi via SSH** (from your Windows machine)
2. **Install the Remote Worker and set it to auto-start** (on the Pi)

This document provides the fastest path through both steps.

---

## Step 1: Find Your Raspberry Pi's IP Address (5 minutes)

### Option A: With Monitor/Keyboard Connected

```bash
# On the Raspberry Pi terminal:
hostname -I
```

Write down the IP (e.g., `192.168.1.100`)

### Option B: Without Monitor (Check Router)

Look in your WiFi router's settings → Connected Devices → Find "Raspberry Pi"

---

## Step 2: Connect via SSH from Windows (1 minute)

### Using PuTTY (Easiest Visual Approach)

1. Open **PuTTY**
2. Hostname: `192.168.1.100` (use your Pi's IP)
3. Port: `22`
4. Connection type: `SSH`
5. Click **Open**
6. Login: `pi` / Password: `raspberry` (or your custom password)

### Using Windows PowerShell (Command Line)

```powershell
ssh pi@192.168.1.100
```

Accept the host key when prompted, then enter password.

### Using WSL (If you prefer Bash)

```bash
ssh pi@192.168.1.100
```

---

## Step 3: Automated Setup on the Pi (10 minutes)

Once connected via SSH, run this **one-line command** that automates everything:

```bash
curl -sSL https://raw.githubusercontent.com/rhyslwells/RaspPi-Remote-Worker/main/setup.sh | bash -s -- 192.168.1.100
```

This script will:
- ✅ Update system packages
- ✅ Install Python 3.10+ and git
- ✅ Install UV (package manager)
- ✅ Clone the repository
- ✅ Create virtual environment and install dependencies
- ✅ Set up systemd service for auto-start

**Note:** The script will ask you to confirm and may prompt for your password (for `sudo` commands).

### Manual Setup (If you prefer step-by-step)

If you'd rather do it manually to learn bash commands, see [Part 4-5 of RASP_PI_README.md](./RASP_PI_README.md#part-4-initial-raspberry-pi-environment-setup)

---

## Step 4: Add Credentials and Start Service (2 minutes)

### Copy credentials.json to the Pi

From your Windows machine, in **PowerShell or WSL**:

```bash
# Replace 192.168.1.100 with your Pi's IP, and adjust path if needed
scp credentials.json pi@192.168.1.100:~/RaspPi-Remote-Worker/

# Verify it was copied:
ssh pi@192.168.1.100 "ls -la ~/RaspPi-Remote-Worker/credentials.json"
```

### Start the Service

```bash
# SSH into Pi (if not already connected)
ssh pi@192.168.1.100

# Enable and start the service
sudo systemctl enable remote-worker.service
sudo systemctl start remote-worker.service

# Verify it's running
sudo systemctl status remote-worker.service
```

**Success!** Your service should show `active (running)` in green.

---

## Verify Everything Works

### Check Service Status

```bash
ssh pi@192.168.1.100
sudo systemctl status remote-worker.service
```

Should show:
```
● remote-worker.service - Remote Worker - Google Sheets Task Runner
   Loaded: loaded (...; enabled; ...)
   Active: active (running)
```

### View Logs

```bash
sudo journalctl -u remote-worker.service -n 20
```

You should see logs showing the service is polling the Google Sheet.

---

## Useful WSL Bash Commands to Learn

Since you're on Windows with WSL, here are key bash commands used in setup:

```bash
# File and directory operations
pwd                          # Show current directory
cd ~/RaspPi-Remote-Worker   # Change directory
ls -la                       # List files with details (-a shows hidden, -l shows details)
mkdir -p logs                # Create directory (even if parent doesn't exist)
cp file.txt copy.txt         # Copy file
mv old.txt new.txt           # Move/rename file
rm file.txt                  # Delete file
chmod 600 credentials.json   # Change file permissions

# Text editing (no GUI)
nano filename.txt            # User-friendly editor (Ctrl+O save, Ctrl+X exit)
cat filename.txt             # Display file contents
echo "text" > file.txt       # Write text to file
grep "search_term" file.txt  # Search within file

# Git operations (version control)
git clone https://...        # Download repository
git pull origin main         # Download latest changes
git status                   # Check what changed

# Package management
pip install package_name     # Install Python packages
uv sync                      # Install dependencies from pyproject.toml

# System operations
sudo command                 # Run command with admin privileges
sudo systemctl status name   # Check service status
sudo systemctl restart name  # Restart service
sudo apt update              # Update package list
sudo apt install -y package  # Install system package
```

### Bash Script Basics (What the setup.sh does)

```bash
#!/bin/bash                    # Tells system this is a bash script

set -e                         # Exit if any command fails
cd ~/RaspPi-Remote-Worker      # Navigate to directory

# Run commands sequentially
echo "Installing packages..."  # Print message
sudo apt update                # Execute command
sudo apt install -y python3    # -y means "yes to all prompts"

# Check if file exists
if [ -f "credentials.json" ]; then
    echo "Found credentials"
fi
```

---

## Troubleshooting Quick Reference

| Problem | Command to Debug |
|---------|-----------------|
| Can't SSH to Pi | `ping 192.168.1.100` (check if reachable) |
| Service won't start | `sudo systemctl status remote-worker.service` |
| See what's in repo | `ls -la ~/RaspPi-Remote-Worker` |
| See recent logs | `sudo journalctl -u remote-worker.service -n 50` |
| Stop service | `sudo systemctl stop remote-worker.service` |
| View file contents | `cat ~/RaspPi-Remote-Worker/credentials.json` |

---

## What Happens Next

Once the service is running:

1. **Check Control Panel**: Open your Google Sheet and verify it's being polled
2. **Test a Script**: Set a script to "START" in the sheet and watch it execute
3. **Monitor**: Use `sudo journalctl -u remote-worker.service -f` to watch in real-time

For more details, see:
- **[RASP_PI_README.md](./RASP_PI_README.md)** — Full setup guide with all options
- **[SERVICE_README.md](./SERVICE_README.md)** — Systemd service management
- **[RUNNER_README.md](./RUNNER_README.md)** — How the polling/execution works

---

## Summary

```
┌─ Windows Machine (Your Computer) ──────────────────────────┐
│                                                             │
│  1. Open PuTTY or PowerShell                               │
│     ssh pi@192.168.1.100                                   │
│                                                             │
│  2. Copy credentials.json via scp                          │
│     scp credentials.json pi@192.168.1.100:~/...            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                              ↓
                          SSH Connection
                              ↓
┌─ Raspberry Pi ─────────────────────────────────────────────┐
│                                                             │
│  3. Automated Setup (or do it manually)                    │
│     curl ... | bash                                         │
│     - Install Python, git, UV                              │
│     - Clone repo                                           │
│     - Create virtualenv                                    │
│                                                             │
│  4. Deploy credentials & start service                     │
│     sudo systemctl start remote-worker.service             │
│                                                             │
│  5. Service runs continuously, polls Google Sheet          │
│     Automatically restarts on reboot                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```
