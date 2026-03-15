Explain this script



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
