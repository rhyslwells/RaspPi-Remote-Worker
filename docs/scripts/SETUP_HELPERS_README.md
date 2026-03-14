# Raspberry Pi Setup Assistant Files

This directory contains helper files to simplify setting up and managing your Raspberry Pi remote worker. Choose the approach that matches your setup.

---

## 📋 File Overview

| File | Purpose | For | Learn |
|------|---------|-----|-------|
| **SETUP_QUICKSTART.md** | High-level overview of setup process | Everyone | Best starting point |
| **NETWORK_RECONNECTION.md** | Reconnect Pi after moving house or WiFi change | When moving/changing WiFi | Network config |
| **setup.sh** | Automated installation script | On the Pi | Bash scripting |
| **raspi-helper.ps1** | Windows PowerShell helper commands | Windows users | PowerShell functions |
| **raspi-helper.sh** | WSL/Linux Bash helper commands | WSL users | Bash scripting |

---

## 🚀 Quick Start (5 minutes)

### ⚡ Just Moved House?
If you've moved and need to reconnect to a new WiFi network, see [NETWORK_RECONNECTION.md](./NETWORK_RECONNECTION.md) instead. Takes 5-10 minutes.

### 1. **Read This First**
Start with [SETUP_QUICKSTART.md](./SETUP_QUICKSTART.md) for the big picture.

### 2. **Choose Your Connection Method**

**Windows + PuTTY (Visual)**
- Open PuTTY
- IP: `192.168.1.100` | Port: `22`
- Login: `pi` / Password: `raspberry`

**Windows + PowerShell**
```powershell
ssh pi@192.168.1.100
```

**Windows + WSL Bash**
```bash
ssh pi@192.168.1.100
```

### 3. **Run Automated Setup on Pi**

Once connected to your Pi via SSH:
```bash
curl -sSL https://raw.githubusercontent.com/rhyslwells/RaspPi-Remote-Worker/main/setup.sh | bash
```

This runs `setup.sh` which automates all installation steps.

### 4. **Deploy Credentials & Start Service**

From your Windows machine (PowerShell or WSL):

```bash
# Copy credentials
scp credentials.json pi@192.168.1.100:~/RaspPi-Remote-Worker/

# SSH in and start service
ssh pi@192.168.1.100
sudo systemctl start remote-worker.service
```

---

## 🔧 Setup Files in Detail

### setup.sh (Automated Installation)

**What it does:**
- Updates system packages
- Installs Python 3.10+, git, build tools
- Installs UV package manager
- Clones the repository
- Creates virtual environment
- Installs Python dependencies
- Sets up systemd service for auto-start

**How to run:**
```bash
# On the Raspberry Pi (via SSH)
curl -sSL https://raw.githubusercontent.com/rhyslwells/RaspPi-Remote-Worker/main/setup.sh | bash

# Or manually:
cd ~ && bash ~/RaspPi-Remote-Worker/setup.sh
```

**Duration:** ~10 minutes (depending on system speed and internet)

**Benefits of this approach:**
- ✅ No manual typing = fewer errors
- ✅ Reproducible setup
- ✅ Good for learning what each step does (read the script!)

---

### raspi-helper.ps1 (Windows PowerShell)

**What it provides:**
- SSH connections
- File transfer (credentials.json, logs)
- Service management (start/stop/restart)
- Live log viewing
- Repository updates
- Connection testing
- System diagnostics

**How to use:**

**First time setup:**
```powershell
# Navigate to your project directory
cd c:\Users\YourName\Desktop\RaspPi-Remote-Worker

# Load the helper
. .\raspi-helper.ps1 -PiIP "192.168.1.100"

# Save for future sessions
Save-RaspPiConfig -IP "192.168.1.100"
```

**Future sessions (after saving config):**
```powershell
cd c:\Users\YourName\Desktop\RaspPi-Remote-Worker
. .\raspi-helper.ps1
```

**Available commands:**
```powershell
Connect-RaspPi                          # SSH into Pi
Copy-CredentialsToRaspPi                # Deploy credentials.json
Get-RaspPiLogs                          # Download logs
Get-RaspPiServiceStatus                 # Check service
Start-RaspPiService                     # Start service
Stop-RaspPiService                      # Stop service
Restart-RaspPiService                   # Restart service
Watch-RaspPiLogs                        # Live logs (Ctrl+C to exit)
Update-RaspPiRepo                       # Pull changes & restart
Test-RaspPiConnection                   # Run diagnostics
Get-RaspPiInfo                          # System info
Save-RaspPiConfig -IP "192.168.1.100"  # Save IP permanently
Show-Help                               # Show all commands
```

**Example workflow:**
```powershell
# Connect and manage
Connect-RaspPi

# In another PowerShell window:
. .\raspi-helper.ps1

# Copy credentials
Copy-CredentialsToRaspPi credentials.json

# Check status
Get-RaspPiServiceStatus

# View logs in real time
Watch-RaspPiLogs

# Update code and restart
Update-RaspPiRepo

# Run diagnostics
Test-RaspPiConnection
```

---

### raspi-helper.sh (WSL/Bash)

**What it provides:**
Same as PowerShell version but for Bash/WSL:
- SSH connections
- File transfer
- Service management
- Log viewing
- Repository updates
- Connection testing
- Diagnostics

**How to use (WSL Terminal):**

**First time:**
```bash
cd ~/RaspPi-Remote-Worker

# Load helper
source raspi-helper.sh

# Save IP for future
save_raspi_config 192.168.1.100
```

**Future sessions:**
```bash
cd ~/RaspPi-Remote-Worker
source raspi-helper.sh
```

**Available commands:**
```bash
connect_raspi                           # SSH into Pi
copy_credentials_to_raspi              # Deploy credentials.json
get_raspi_logs [path]                  # Download logs
get_raspi_service_status               # Check service
start_raspi_service                    # Start service
stop_raspi_service                     # Stop service
restart_raspi_service                  # Restart service
watch_raspi_logs                       # Live logs (Ctrl+C to exit)
update_raspi_repo                      # Pull changes & restart
test_raspi_connection                  # Run diagnostics
get_raspi_info                         # System info
save_raspi_config 192.168.1.100       # Save IP permanently
show_help                              # Show all commands
```

**Example workflow:**
```bash
# Setup
source raspi-helper.sh
save_raspi_config 192.168.1.100

# Connect
connect_raspi

# In another terminal:
source raspi-helper.sh
copy_credentials_to_raspi credentials.json

# Check and manage
get_raspi_service_status
watch_raspi_logs
update_raspi_repo
test_raspi_connection
```

---

## 📚 Learning Bash & PowerShell

### If you want to learn more bash, explore:

1. **setup.sh** - See these concepts:
   - Shebang: `#!/bin/bash`
   - Variables: `$PI_IP`, `${variable}`
   - Conditionals: `if [ condition ]; then`
   - Loops: `for`, `while`
   - Functions: `function_name() {}`
   - Command substitution: `$(command)`
   - Redirects: `>`, `>>`, `2>&1`

2. **raspi-helper.sh** - See these concepts:
   - Function definitions and exports
   - Color codes (ANSI escape sequences)
   - Command piping: `|`
   - SSH with command execution
   - Error checking: `$?`
   - Configuration files
   - Heredocs: `<< 'EOF'`

### If you want to learn more PowerShell, explore:

1. **raspi-helper.ps1** - See these concepts:
   - Functions with parameters
   - Error handling: `$LASTEXITCODE`
   - String interpolation
   - File operations: `Test-Path`, `Get-Content`
   - Process invocation: `ssh`, `scp`
   - Cmdlets vs traditional commands
   - Parameter documentation
   - Aliases and full cmdlet names

---

## 🔍 Troubleshooting

### Can't find Pi IP

```bash
# Check your router or use nmap on WSL:
nmap -sn 192.168.1.0/24 | grep -i "raspberry\|pi"

# Once found:
save_raspi_config 192.168.1.100    # (or PowerShell equivalent)
```

### SSH connection fails

```bash
# Test network connectivity:
ping 192.168.1.100

# Check if SSH is enabled on Pi:
ssh pi@192.168.1.100 "sudo raspi-config"
# Navigate to: Interface Options → SSH → Enable

# Verify no firewall blocks port 22
```

### Service won't start

```bash
# Check details:
ssh pi@192.168.1.100
sudo systemctl status remote-worker.service
sudo journalctl -u remote-worker.service -n 50

# Common issues:
# - Missing credentials.json (copy with helper)
# - Wrong path in service file
# - Permission issues on directory
```

### Wrong script format for your system

- Windows + PowerShell → Use `raspi-helper.ps1`
- Windows + WSL → Use `raspi-helper.sh`
- Mac/Linux → Use `raspi-helper.sh`

---

## 📖 Next Steps

Once setup completes:

1. ✅ Read [SETUP_QUICKSTART.md](./SETUP_QUICKSTART.md) to understand the process
2. ✅ Run `setup.sh` on the Pi (or follow steps in [RASP_PI_README.md](./RASP_PI_README.md))
3. ✅ Use helper script (`raspi-helper.sh` or `raspi-helper.ps1`) for ongoing management
4. ✅ Copy credentials.json to the Pi
5. ✅ Start the service: `sudo systemctl start remote-worker.service`
6. ✅ Monitor with `watch_raspi_logs` or `Watch-RaspPiLogs`
7. ✅ Set up your first task in the Google Sheet
8. ✅ See [RUNNER_README.md](./RUNNER_README.md) for scripting details

---

## 📝 Helper Scripts Summary

| Task | PowerShell | Bash (WSL) | Manual |
|------|-----------|-----------|--------|
| Connect | `Connect-RaspPi` | `connect_raspi` | `ssh pi@IP` |
| Check status | `Get-RaspPiServiceStatus` | `get_raspi_service_status` | `ssh pi@IP sudo systemctl status...` |
| View logs | `Watch-RaspPiLogs` | `watch_raspi_logs` | `ssh pi@IP sudo journalctl...` |
| Copy file | `Copy-CredentialsToRaspPi` | `copy_credentials_to_raspi` | `scp file pi@IP:path` |
| Update repo | `Update-RaspPiRepo` | `update_raspi_repo` | `ssh pi@IP cd ... && git pull...` |
| Diagnose | `Test-RaspPiConnection` | `test_raspi_connection` | Run multiple ssh commands |

---

## � Just Moved Houses?

If you need to reconnect your Pi to a new WiFi network:
→ See [NETWORK_RECONNECTION.md](./NETWORK_RECONNECTION.md)

Quick summary:
1. **With monitor:** Click WiFi icon → Select new network → Get new IP
2. **Without monitor:** Use **Raspberry Pi Imager** to pre-configure WiFi before booting
3. **Find IP:** Check router → Connected Devices or use `nmap`
4. **SSH in:** `ssh pi@NEW_IP_ADDRESS`
5. **Verify service:** `sudo systemctl status remote-worker.service`

---

## 📝 All Files Summary

Since you have **Windows, WSL, and PuTTY**:

1. **Start:** Use PuTTY to SSH (visual, no command line anxiety)
2. **Setup:** Run `curl ... | bash` (automated, follows setup.sh)
3. **Ongoing:** Use `raspi-helper.sh` in WSL (learn bash in context)

This gives you:
- Visual comfort (PuTTY for initial connection)
- Automation (no manual typing)
- Bash learning (helper functions + setup.sh to read)

---

## 💡 Pro Tips

**Save your Pi IP:**
```bash
# PowerShell:
Save-RaspPiConfig -IP "192.168.1.100"

# Bash:
save_raspi_config 192.168.1.100
```

**Automate credentials deployment:**
```bash
# From Windows, run both in one line:
scp credentials.json pi@192.168.1.100:~/RaspPi-Remote-Worker/ && ssh pi@192.168.1.100 "chmod 600 ~/RaspPi-Remote-Worker/credentials.json"
```

**Watch logs while testing:**
```bash
# Terminal 1: Watch logs
watch_raspi_logs

# Terminal 2: Trigger actions / run updates
update_raspi_repo
```

---

For detailed reference, see:
- [SETUP_QUICKSTART.md](./SETUP_QUICKSTART.md) - High-level overview
- [RASP_PI_README.md](./RASP_PI_README.md) - Detailed setup guide
- [SERVICE_README.md](./SERVICE_README.md) - Systemd service management
- [RUNNER_README.md](./RUNNER_README.md) - How the polling system works
