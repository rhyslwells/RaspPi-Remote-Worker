#!/bin/bash

# RaspPi Remote Worker - Systemd Service Setup Script
# This script sets up the systemd service for RaspPi-Remote-Worker
# Run after setup_initial.sh has completed
# Run with: bash setup_systemd.sh

set -e  # Exit on any error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}RaspPi Remote Worker - Systemd Setup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if running as pi user (or allow any non-root)
if [ "$EUID" -eq 0 ]; then
   echo -e "${YELLOW}Please don't run this script as root. Run as 'pi' user:${NC}"
   echo "  exit  # (if logged in as root)"
   echo "  su pi"
   echo "  bash setup_systemd.sh"
   exit 1
fi

# Confirm before proceeding
echo -e "${BLUE}This script will:${NC}"
echo "  1. Set up systemd service for auto-start"
echo ""
echo -e "${YELLOW}You will need to enter your password for sudo commands.${NC}"
echo ""
read -p "Proceed? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Setup cancelled."
    exit 1
fi

# Step 1: Set up systemd service
echo ""
echo -e "${BLUE}Step 1/1: Setting up systemd service...${NC}"

# Create logs directory
mkdir -p logs

# Create service file
sudo tee /etc/systemd/system/remote-worker.service > /dev/null <<EOF
[Unit]
Description=Remote Worker - Google Sheets Task Runner
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=rhyslwells
WorkingDirectory=/home/rhyslwells/Desktop/RaspPi-Remote-Worker
Environment="PATH=/home/rhyslwells/Desktop/RaspPi-Remote-Worker/.venv/bin"
ExecStart=/home/rhyslwells/Desktop/RaspPi-Remote-Worker/.venv/bin/python3 scripts/runner.py
Restart=always
RestartSec=10

# Log output
StandardOutput=append:/home/rhyslwells/Desktop/RaspPi-Remote-Worker/logs/service.log
StandardError=append:/home/rhyslwells/Desktop/RaspPi-Remote-Worker/logs/service.log

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable remote-worker.service

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Systemd Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo ""
echo "1. Deploy credentials:"
echo "   From your main machine, run:"
echo "   scp credentials.json rhyslwells@$(hostname -I | awk '{print $1}'):~/Desktop/RaspPi-Remote-Worker/"
echo ""
echo "2. Verify credentials were copied:"
echo "   ls -la ~/Desktop/RaspPi-Remote-Worker/credentials.json"
echo ""
echo "3. Start the service:"
echo "   sudo systemctl start remote-worker.service"
echo ""
echo "4. Check status:"
echo "   sudo systemctl status remote-worker.service"
echo ""
echo "5. View logs:"
echo "   journalctl -u remote-worker.service -f"
echo ""
echo -e "${BLUE}For more information, see:${NC}"
echo "  - docs/scripts/SERVICE_README.md (systemd service management)"
echo ""


# sudo systemctl restart remote-worker.service
