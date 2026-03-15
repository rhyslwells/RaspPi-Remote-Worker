## raspi-helper.sh (Bash/WSL)

Bash/WSL helper script for managing your Raspberry Pi remotely without entering your password multiple times. Handles SSH connections, service management, log retrieval, and diagnostics.

### Configuration

The script uses:
- **PI_USER**: Username for SSH (set to `rhyslwells` by default)
- **PI_IP**: Stored in `.raspi-config` file (project root)

### Quick Start

**First time setup:**
```bash
cd ~/RaspPi-Remote-Worker
source raspi-helper.sh
save_raspi_config 192.168.1.215
```

**Future sessions:**
```bash
cd ~/RaspPi-Remote-Worker
source raspi-helper.sh
```

The script loads your saved IP automatically and shows which one is configured.

### Available Commands

| Command | Purpose |
|---------|---------|
| `connect_raspi` | SSH into the Pi |
| `copy_credentials_to_raspi credentials.json` | Deploy credentials file |
| `get_raspi_logs [path]` | Download logs from Pi |
| `get_raspi_service_status` | Check service status |
| `start_raspi_service` | Start service & show status (single SSH) |
| `stop_raspi_service` | Stop service & show status (single SSH) |
| `restart_raspi_service` | Restart service & show status (single SSH) |
| `watch_raspi_logs` | View live logs (Ctrl+C to exit) |
| `update_raspi_repo` | Git pull & restart service |
| `test_raspi_connection` | Run 5-point diagnostic check |
| `get_raspi_info` | System info (OS, Python, disk, memory, IP, service) |
| `save_raspi_config <IP>` | Save Pi IP for future sessions |
| `show_help` | Show all available commands |

### Example Workflow

```bash
# Initial setup
source raspi-helper.sh
save_raspi_config 192.168.1.215

# Check everything works
test_raspi_connection

# Deploy credentials
copy_credentials_to_raspi credentials.json

# Manage service (single password prompt each)
start_raspi_service
stop_raspi_service
restart_raspi_service

# Monitor and update
watch_raspi_logs        # View live logs
update_raspi_repo       # Pull latest code
get_raspi_info          # System details
```

### Notes

- Service commands (`start/stop/restart`) combine operations into a single SSH call to minimize password prompts
- Requires key-based SSH authentication or will prompt for password once per command
- For direct file editing on the Pi, consider VSCode Remote SSH in addition to this script
