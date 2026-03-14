# Raspberry Pi Setup & Remote Management Guide

This guide walks you through connecting to your Raspberry Pi via SSH, installing the Remote Worker repository, and managing updates remotely.

---

## Prerequisites

- Raspberry Pi (any model) with Raspberry Pi OS installed
- Raspberry Pi connected to your network (WiFi or Ethernet)
- Your primary machine (Windows, Mac, or Linux) on the same network
- SSH client installed (built-in on Mac/Linux; use PowerShell or PuTTY on Windows)
- Google Cloud credentials (`credentials.json`) ready to deploy

---

## Part 1: Finding Your Raspberry Pi's IP Address

### On the Raspberry Pi (First Time Setup)

1. Connect a monitor and keyboard to your Pi
2. Boot up and log in with default credentials:
   - **Username:** `pi`
   - **Password:** `raspberry` (or your custom password)
3. Open a terminal and run:
   ```bash
   hostname -I
   ```
4. Note the IP address (e.g., `192.168.1.100`)

### Alternatively (Without Monitor)

1. Check your router's DHCP client list to find the Pi's IP
2. Or use a network scanner tool (e.g., `nmap` on Linux/Mac):
   ```bash
   nmap -sn 192.168.1.0/24 | grep -i "raspberry\|pi"
   ```

---

## Part 2: Enabling SSH on Raspberry Pi

### If You Have Console Access

1. Run the Raspberry Pi configuration utility:
   ```bash
   sudo raspi-config
   ```
2. Navigate to **Interface Options** → **SSH** → **Enable**
3. Select **Yes** and exit

### If SSH is Already Enabled

Skip to Part 3.

---

## Part 3: Connecting via SSH from Your Primary Machine

### On Windows (PowerShell)

```powershell
# Connect to your Pi (replace with your Pi's IP)
ssh pi@192.168.1.100

# First time: You'll be asked to accept the host key. Type 'yes'
# Then enter the password (default: 'raspberry')
```

### On Mac/Linux (Terminal)

```bash
ssh pi@192.168.1.100
```

### Using PuTTY (Windows GUI Alternative)

1. Download PuTTY from https://www.putty.org/
2. Enter the IP address (e.g., `192.168.1.100`) in the Host Name field
3. Set Port to `22` and Connection Type to `SSH`
4. Click **Open** and log in with username `pi` and password

---

## Part 4: Initial Raspberry Pi Environment Setup

Once connected via SSH, run these commands:

### 1. Update System Packages

```bash
sudo apt update
sudo apt upgrade -y
```

### 2. Install Python 3.10+ and Essential Tools

```bash
sudo apt install -y python3 python3-pip python3-venv git
```

### 3. Install UV (Fast Python Package Manager)

```bash
pip3 install uv
```

---

## Part 5: Clone and Install the Repository

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
# Or if using requirements.txt:
pip install -r requirements.txt
```

### 4. Deploy Credentials

**Important:** The `credentials.json` file is sensitive and must be kept secure.

```bash
# On your primary machine, copy the file to the Pi:
scp credentials.json pi@192.168.1.100:~/RaspPi-Remote-Worker/

# Or manually:
# 1. SSH into the Pi
# 2. Create/paste the credentials.json file in ~/RaspPi-Remote-Worker/
# 3. Verify permissions:
chmod 600 credentials.json
```

### 5. Verify Installation

```bash
python3 runner.py --help
# Or run a quick test connection:
python3 test_connection.py
```

---

## Part 6: Setting Up the Systemd Service

To run the worker automatically on Pi boot, set up a systemd service.

### 1. Create Service File

```bash
sudo nano /etc/systemd/system/remote-worker.service
```

### 2. Paste This Configuration

```ini
[Unit]
Description=Remote Worker - Google Sheets Task Runner
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/RaspPi-Remote-Worker
Environment="PATH=/home/pi/RaspPi-Remote-Worker/.venv/bin"
ExecStart=/home/pi/RaspPi-Remote-Worker/.venv/bin/python3 runner.py
Restart=always
RestartSec=10

# Log output
StandardOutput=append:/home/pi/RaspPi-Remote-Worker/logs/service.log
StandardError=append:/home/pi/RaspPi-Remote-Worker/logs/service.log

[Install]
WantedBy=multi-user.target
```

### 3. Create Logs Directory

```bash
mkdir -p /home/pi/RaspPi-Remote-Worker/logs
```

### 4. Enable and Start the Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable remote-worker.service
sudo systemctl start remote-worker.service

# Check status:
sudo systemctl status remote-worker.service

# View logs:
tail -f /home/pi/RaspPi-Remote-Worker/logs/service.log
```

---

## Part 7: Remote Updates & Maintenance

### Pulling Latest Changes

```bash
# SSH into the Pi
ssh pi@192.168.1.100

# Navigate to repo
cd ~/RaspPi-Remote-Worker

# Pull latest code
git pull origin main

# Rebuild dependencies if pyproject.toml changed
source .venv/bin/activate
uv sync

# Restart the service
sudo systemctl restart remote-worker.service
```

### Automating Updates (Optional)

Create a cron job to pull updates nightly:

```bash
# Edit crontab
crontab -e

# Add this line (runs at 2 AM daily):
0 2 * * * cd ~/RaspPi-Remote-Worker && git pull origin main && source .venv/bin/activate && uv sync && sudo systemctl restart remote-worker.service > /tmp/update.log 2>&1
```

### Monitoring Service Health

```bash
# Check if service is running
sudo systemctl status remote-worker.service

# View recent logs
sudo journalctl -u remote-worker.service -n 50

# View application logs
tail -100 ~/RaspPi-Remote-Worker/logs/service.log

# Check disk space
df -h
```

---

## Part 8: SSH Key-Based Authentication (Recommended)

To avoid entering passwords every time, set up SSH keys:

### On Your Primary Machine

```powershell
# Windows PowerShell
ssh-keygen -t rsa -b 4096 -f "$HOME\.ssh\id_rsa"

# Mac/Linux
ssh-keygen -t rsa -b 4096
```

### Copy Public Key to Raspberry Pi

```powershell
# Windows
$pubKey = Get-Content "$HOME\.ssh\id_rsa.pub"
ssh pi@192.168.1.100 "mkdir -p ~/.ssh && echo '$pubKey' >> ~/.ssh/authorized_keys"

# Mac/Linux
ssh-copy-id pi@192.168.1.100
```

Now you can SSH without entering a password:
```bash
ssh pi@192.168.1.100
```

---

## Troubleshooting

### Can't Connect to Raspberry Pi

- **Issue:** SSH connection refused
- **Solution:** 
  - Verify SSH is enabled: `sudo raspi-config` → Interface Options → SSH
  - Check IP address: `hostname -I` on the Pi
  - Verify firewall isn't blocking port 22

### Service Won't Start

- **Issue:** `sudo systemctl start remote-worker.service` fails
- **Solution:**
  - Check status: `sudo systemctl status remote-worker.service`
  - View error logs: `sudo journalctl -u remote-worker.service -n 50`
  - Verify Python path: `which python3`
  - Verify working directory exists: `ls -la ~/RaspPi-Remote-Worker`

### Git Pull Fails

- **Issue:** Permission denied on git pull
- **Solution:**
  - Set up SSH keys for GitHub (or use HTTPS with personal access token)
  - Verify repo URL: `git remote -v`

### Out of Disk Space

- **Issue:** Service crashes due to full disk
- **Solution:**
  ```bash
  df -h
  # Clear old logs:
  rm ~/.config/logs/*.log
  # Check what's using space:
  du -sh ~/*
  ```

### Credentials Not Found

- **Issue:** `FileNotFoundError: credentials.json not found`
- **Solution:**
  - Verify file exists: `ls -la ~/RaspPi-Remote-Worker/credentials.json`
  - Check permissions: `chmod 600 ~/RaspPi-Remote-Worker/credentials.json`
  - Redeploy if missing: `scp credentials.json pi@192.168.1.100:~/RaspPi-Remote-Worker/`

---

## Quick Reference: Common Commands

```bash
# Connect
ssh pi@192.168.1.100

# Navigate to repo
cd ~/RaspPi-Remote-Worker

# Activate virtualenv
source .venv/bin/activate

# Pull and update
git pull origin main && uv sync

# Restart service
sudo systemctl restart remote-worker.service

# View logs
tail -f logs/service.log

# Check service status
sudo systemctl status remote-worker.service

# Deactivate virtualenv
deactivate
```

---

## Next Steps

Once the service is running:

1. Verify it's polling correctly by checking logs regularly
2. Test with a simple script (see [RUNNER_README.md](./RUNNER_README.md))
3. Set up your first task in the Google Sheet
4. Monitor the Control Panel (Google Sheets) for "SUCCESS" or "FAILED" status
5. See [CONTROL_PANEL_README.md](./CONTROL_PANEL_README.md) for panel configuration
