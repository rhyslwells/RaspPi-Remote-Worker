# systemd Service Setup

This guide covers setting up Runner.py as a systemd service so it automatically starts on Raspberry Pi boot and runs continuously in the background.

## Why systemd?

Running runner.py as a systemd service provides:
- **Auto-start on boot**: Runner starts automatically when Pi powers on
- **Auto-restart**: If runner crashes, systemd automatically restarts it
- **System integration**: Logs captured in journalctl for easy monitoring
- **Process management**: Stop, start, or check status easily with systemctl
- **Recommended approach**: Industry standard for background services on Linux

## Step-by-Step Setup

### Step 1: Create the Service File

SSH into your Raspberry Pi and create the service file:

```bash
sudo nano /etc/systemd/system/remote-worker.service
```

### Step 2: Add Service Configuration

Copy and paste this configuration:

```ini
[Unit]
Description=RaspPi Remote Worker Runner
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/RaspPi-Remote-Worker
ExecStart=/usr/bin/python3 /home/pi/RaspPi-Remote-Worker/scripts/runner.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Important**: Replace `/home/pi/RaspPi-Remote-Worker` with your actual project directory path.

Save the file: **Ctrl+O**, **Enter**, **Ctrl+X**

### Step 3: Enable and Start the Service

```bash
# Reload systemd daemon to recognize new service
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable remote-worker

# Start the service immediately
sudo systemctl start remote-worker
```

## Verifying the Service

### Check Status

```bash
sudo systemctl status remote-worker
```

Expected output:
```
● remote-worker.service - RaspPi Remote Worker Runner
   Loaded: loaded (/etc/systemd/system/remote-worker.service; enabled; vendor preset: enabled)
   Active: active (running) since Thu 2025-03-13 10:45:32 UTC; 5min ago
 Main PID: 1234 (python3)
    Tasks: 1 (limit: 400)
   Memory: 45.2M
   CGroup: /system.slice/remote-worker.service
           └─1234 /usr/bin/python3 /home/pi/RaspPi-Remote-Worker/scripts/runner.py
```

### View Live Logs

```bash
# Follow logs in real-time
journalctl -u remote-worker -f

# View last 50 log lines
journalctl -u remote-worker -n 50

# View logs from a specific date
journalctl -u remote-worker --since "2025-03-13"
```

## Service Management Commands

```bash
# Start the service
sudo systemctl start remote-worker

# Stop the service
sudo systemctl stop remote-worker

# Restart the service
sudo systemctl restart remote-worker

# Check service status
sudo systemctl status remote-worker

# Enable/disable auto-start on boot
sudo systemctl enable remote-worker    # Enable
sudo systemctl disable remote-worker   # Disable

# View service logs
journalctl -u remote-worker -f
```

## Configuration Options Explained

| Option | Value | Explanation |
|--------|-------|-------------|
| `Description` | RaspPi Remote Worker Runner | Human-readable service name |
| `After=network.target` | - | Wait for network before starting |
| `Type=simple` | - | Service runs as a normal process |
| `User=pi` | - | Run as 'pi' user (not root) |
| `WorkingDirectory` | `/home/pi/RaspPi-Remote-Worker` | Project root directory |
| `ExecStart` | `/usr/bin/python3 /home/pi/...` | Command to run |
| `Restart=always` | - | Always restart if process dies |
| `RestartSec=10` | - | Wait 10 seconds before restart |
| `WantedBy=multi-user.target` | - | Start in multi-user mode |

## Troubleshooting

### Service won't start

```bash
# Check exact error
sudo systemctl status remote-worker
journalctl -u remote-worker -n 20

# Common issues:
# 1. Wrong path: Check WorkingDirectory and ExecStart match your setup
# 2. Missing credentials.json: Verify credentials.json exists in project root
# 3. Permission denied: Ensure 'pi' user can access project directory
```

### Service keeps restarting

```bash
# View detailed logs
journalctl -u remote-worker -f

# Check for:
# - Google Sheets API errors
# - Missing dependencies
# - Python version issues
```

### To stop the service

```bash
sudo systemctl stop remote-worker

# Verify it stopped
sudo systemctl status remote-worker
```

## Next Steps

1. Create the systemd service file (Step 1-3 above)
2. Verify it's running: `sudo systemctl status remote-worker`
3. Monitor logs: `journalctl -u remote-worker -f`
4. Set up your scripts in the Config sheet
5. Trigger a script to test the full system

## Related Documentation

- [Runner.py Documentation](RUNNER_README.md) - Complete runner.py guide
- [Control Panel Documentation](CONTROL_PANEL_README.md) - Google Sheets integration details


