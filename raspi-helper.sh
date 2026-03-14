#!/bin/bash

# RaspPi Remote Worker - WSL/Bash Helper Script
#
# Usage: source ./raspi-helper.sh
# Then use the functions defined below
#
# This script provides convenient functions for managing your Raspberry Pi
# from WSL Bash or any Linux terminal
#
# For Windows PowerShell equivalent, see raspi-helper.ps1

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Load configuration if it exists
CONFIG_FILE="$(dirname "$0")/.raspi-config"
if [ -f "$CONFIG_FILE" ]; then
    PI_IP=$(cat "$CONFIG_FILE")
    echo -e "${GREEN}Loaded Pi IP from config: $PI_IP${NC}"
fi

# ============================================================================
# SSH CONNECTION
# ============================================================================

connect_raspi() {
    # Connect to Raspberry Pi via SSH
    if [ -z "$PI_IP" ]; then
        echo -e "${RED}Error: Pi IP not configured.${NC}"
        echo "Usage: source ./raspi-helper.sh 192.168.1.100"
        return 1
    fi
    
    echo -e "${GREEN}Connecting to Pi at $PI_IP...${NC}"
    ssh pi@"$PI_IP"
}

# ============================================================================
# FILE TRANSFER
# ============================================================================

copy_credentials_to_raspi() {
    # Copy credentials.json to Raspberry Pi
    local cred_path="${1:-.}"
    
    if [ -z "$PI_IP" ]; then
        echo -e "${RED}Error: Pi IP not configured.${NC}"
        return 1
    fi
    
    if [ ! -f "$cred_path" ]; then
        echo -e "${RED}Error: Credentials file not found: $cred_path${NC}"
        return 1
    fi
    
    echo -e "${GREEN}Copying $cred_path to Pi...${NC}"
    scp "$cred_path" "pi@${PI_IP}:~/RaspPi-Remote-Worker/"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Success! Credentials copied.${NC}"
        echo ""
        echo -e "${CYAN}Next: Verify on Pi with:${NC}"
        echo "  ssh pi@$PI_IP 'ls -la ~/RaspPi-Remote-Worker/credentials.json'"
    fi
}

get_raspi_logs() {
    # Download logs from Raspberry Pi
    local local_path="${1:-.}"
    
    if [ -z "$PI_IP" ]; then
        echo -e "${RED}Error: Pi IP not configured.${NC}"
        return 1
    fi
    
    mkdir -p "$local_path"
    
    echo -e "${GREEN}Downloading logs from Pi...${NC}"
    scp -r "pi@${PI_IP}:~/RaspPi-Remote-Worker/logs/*" "$local_path/"
    
    echo -e "${GREEN}Logs downloaded to: $local_path${NC}"
}

# ============================================================================
# SERVICE MANAGEMENT (via SSH)
# ============================================================================

get_raspi_service_status() {
    # Check service status on Raspberry Pi
    if [ -z "$PI_IP" ]; then
        echo -e "${RED}Error: Pi IP not configured.${NC}"
        return 1
    fi
    
    echo -e "${GREEN}Checking service status on Pi...${NC}"
    ssh pi@"$PI_IP" "sudo systemctl status remote-worker.service"
}

start_raspi_service() {
    # Start the Remote Worker service
    if [ -z "$PI_IP" ]; then
        echo -e "${RED}Error: Pi IP not configured.${NC}"
        return 1
    fi
    
    echo -e "${GREEN}Starting Remote Worker service on Pi...${NC}"
    ssh pi@"$PI_IP" "sudo systemctl start remote-worker.service"
    
    sleep 2
    get_raspi_service_status
}

stop_raspi_service() {
    # Stop the Remote Worker service
    if [ -z "$PI_IP" ]; then
        echo -e "${RED}Error: Pi IP not configured.${NC}"
        return 1
    fi
    
    echo -e "${GREEN}Stopping Remote Worker service on Pi...${NC}"
    ssh pi@"$PI_IP" "sudo systemctl stop remote-worker.service"
    
    sleep 2
    get_raspi_service_status
}

restart_raspi_service() {
    # Restart the Remote Worker service
    if [ -z "$PI_IP" ]; then
        echo -e "${RED}Error: Pi IP not configured.${NC}"
        return 1
    fi
    
    echo -e "${GREEN}Restarting Remote Worker service on Pi...${NC}"
    ssh pi@"$PI_IP" "sudo systemctl restart remote-worker.service"
    
    sleep 2
    get_raspi_service_status
}

watch_raspi_logs() {
    # Watch live service logs (Ctrl+C to exit)
    if [ -z "$PI_IP" ]; then
        echo -e "${RED}Error: Pi IP not configured.${NC}"
        return 1
    fi
    
    echo -e "${GREEN}Connecting to live logs (Ctrl+C to exit)...${NC}"
    ssh pi@"$PI_IP" "sudo journalctl -u remote-worker.service -f"
}

# ============================================================================
# REPOSITORY UPDATES
# ============================================================================

update_raspi_repo() {
    # Pull latest code and restart service
    if [ -z "$PI_IP" ]; then
        echo -e "${RED}Error: Pi IP not configured.${NC}"
        return 1
    fi
    
    echo -e "${GREEN}Updating repository on Pi...${NC}"
    ssh pi@"$PI_IP" "cd ~/RaspPi-Remote-Worker && git pull origin main && source .venv/bin/activate && uv sync && sudo systemctl restart remote-worker.service"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Update complete! Service restarted.${NC}"
    else
        echo -e "${RED}Update failed. Check logs with: watch_raspi_logs${NC}"
    fi
}

# ============================================================================
# DIAGNOSTICS
# ============================================================================

test_raspi_connection() {
    # Test connectivity to Raspberry Pi
    if [ -z "$PI_IP" ]; then
        echo -e "${RED}Error: Pi IP not configured.${NC}"
        return 1
    fi
    
    echo -e "${GREEN}Testing connection to Pi at $PI_IP...${NC}"
    
    # Ping
    echo ""
    echo -e "${CYAN}1. Testing network ping...${NC}"
    if ping -c 1 -W 2 "$PI_IP" &> /dev/null; then
        echo -e "   ${GREEN}✓ Network ping successful${NC}"
    else
        echo -e "   ${RED}✗ Network ping failed${NC}"
        return 1
    fi
    
    # SSH connection
    echo ""
    echo -e "${CYAN}2. Testing SSH connection...${NC}"
    if ssh pi@"$PI_IP" "echo OK" &> /dev/null; then
        echo -e "   ${GREEN}✓ SSH connection successful${NC}"
    else
        echo -e "   ${RED}✗ SSH connection failed${NC}"
        return 1
    fi
    
    # Repository
    echo ""
    echo -e "${CYAN}3. Checking repository...${NC}"
    if ssh pi@"$PI_IP" "test -d ~/RaspPi-Remote-Worker" 2>/dev/null; then
        echo -e "   ${GREEN}✓ Repository found${NC}"
    else
        echo -e "   ${RED}✗ Repository not found${NC}"
        return 1
    fi
    
    # Credentials
    echo ""
    echo -e "${CYAN}4. Checking credentials.json...${NC}"
    if ssh pi@"$PI_IP" "test -f ~/RaspPi-Remote-Worker/credentials.json" 2>/dev/null; then
        echo -e "   ${GREEN}✓ Credentials found${NC}"
    else
        echo -e "   ${RED}✗ Credentials not found (copy with: copy_credentials_to_raspi)${NC}"
    fi
    
    # Service
    echo ""
    echo -e "${CYAN}5. Checking service status...${NC}"
    if ssh pi@"$PI_IP" "sudo systemctl is-active remote-worker.service" &> /dev/null; then
        echo -e "   ${GREEN}✓ Service is running${NC}"
    else
        echo -e "   ${YELLOW}✗ Service is not running${NC}"
        echo -e "      ${CYAN}Start with: start_raspi_service${NC}"
    fi
    
    echo ""
    echo -e "${GREEN}✓ All tests passed!${NC}"
}

get_raspi_info() {
    # Get system information from Raspberry Pi
    if [ -z "$PI_IP" ]; then
        echo -e "${RED}Error: Pi IP not configured.${NC}"
        return 1
    fi
    
    echo -e "${GREEN}Getting system info from Pi...${NC}"
    echo ""
    
    ssh pi@"$PI_IP" << 'EOF'
echo "=== SYSTEM INFO ==="
uname -a
echo ""
echo "=== PYTHON INFO ==="
python3 --version
echo ""
echo "=== DISK USAGE ==="
df -h | head -4
echo ""
echo "=== MEMORY USAGE ==="
free -h | head -2
echo ""
echo "=== IPv4 ADDRESS ==="
hostname -I
echo ""
echo "=== SERVICE STATUS ==="
sudo systemctl status remote-worker.service --no-pager | head -10
EOF
}

# ============================================================================
# CONFIGURATION HELPERS
# ============================================================================

save_raspi_config() {
    # Save Pi IP address to config file
    local ip="$1"
    
    if [ -z "$ip" ]; then
        echo -e "${RED}Usage: save_raspi_config 192.168.1.100${NC}"
        return 1
    fi
    
    echo "$ip" > "$CONFIG_FILE"
    echo -e "${GREEN}Saved Pi IP to $CONFIG_FILE${NC}"
    echo -e "${GREEN}Run this script again with: source ./raspi-helper.sh${NC}"
}

show_help() {
    # Show available commands
    cat << 'EOF'
RaspPi Remote Worker - Bash Helper Script

Available functions:

CONNECTION:
  connect_raspi                      - SSH into the Pi

FILE TRANSFER:
  copy_credentials_to_raspi          - Deploy credentials.json
  get_raspi_logs [path]              - Download logs from Pi

SERVICE MANAGEMENT:
  get_raspi_service_status           - Check service status
  start_raspi_service                - Start the service
  stop_raspi_service                 - Stop the service
  restart_raspi_service              - Restart the service
  watch_raspi_logs                   - View live logs (Ctrl+C to exit)

REPOSITORY:
  update_raspi_repo                  - Pull and restart

DIAGNOSTICS:
  test_raspi_connection              - Run connection tests
  get_raspi_info                     - Show system info

CONFIGURATION:
  save_raspi_config 192.168.1.100    - Save Pi IP for future sessions
  show_help                          - Show this help message

Examples:
  connect_raspi
  copy_credentials_to_raspi credentials.json
  get_raspi_service_status
  watch_raspi_logs
  save_raspi_config 192.168.1.100
  test_raspi_connection
  update_raspi_repo

EOF
}

# Export functions so they're available in the shell
export -f connect_raspi
export -f copy_credentials_to_raspi
export -f get_raspi_logs
export -f get_raspi_service_status
export -f start_raspi_service
export -f stop_raspi_service
export -f restart_raspi_service
export -f watch_raspi_logs
export -f update_raspi_repo
export -f test_raspi_connection
export -f get_raspi_info
export -f save_raspi_config
export -f show_help

# Initial message
if [ -z "$PI_IP" ]; then
    echo -e "${YELLOW}RaspPi Helper loaded.${NC}"
    echo -e "${YELLOW}Configure Pi IP with: save_raspi_config 192.168.1.100${NC}"
    echo ""
    show_help
else
    echo -e "${GREEN}RaspPi Helper loaded. Pi IP: $PI_IP${NC}"
    echo "Type 'show_help' for available commands"
fi
