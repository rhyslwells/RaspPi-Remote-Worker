#!/bin/bash

# RaspPi Remote Worker - Automated Setup Script
# This script automates the installation of RaspPi-Remote-Worker on a Raspberry Pi
# Run with: curl -sSL https://raw.githubusercontent.com/rhyslwells/RaspPi-Remote-Worker/main/setup.sh | bash

set -e  # Exit on any error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}RaspPi Remote Worker Setup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if running on Raspberry Pi
if ! grep -q "Raspberry" /proc/device-tree/model 2>/dev/null; then
    echo -e "${YELLOW}Warning: This doesn't appear to be a Raspberry Pi.${NC}"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if running as pi user (or allow any non-root)
if [ "$EUID" -eq 0 ]; then
   echo -e "${YELLOW}Please don't run this script as root. Run as 'pi' user:${NC}"
   echo "  exit  # (if logged in as root)"
   echo "  su pi"
   echo "  bash setup.sh"
   exit 1
fi

# Confirm before proceeding
echo -e "${BLUE}This script will:${NC}"
echo "  1. Update system packages (apt update, apt upgrade)"
echo "  2. Install Python 3.10+, git, and build tools"
echo "  3. Install UV (fast package manager)"
echo "  4. Clone the RaspPi-Remote-Worker repository"
echo "  5. Create and activate virtual environment"
echo "  6. Install Python dependencies from pyproject.toml"
echo "  7. Set up systemd service for auto-start"
echo ""
echo -e "${YELLOW}You will need to enter your password for sudo commands.${NC}"
echo ""
read -p "Proceed? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Setup cancelled."
    exit 1
fi

# Step 1: Update system
echo ""
echo -e "${BLUE}Step 1/7: Updating system packages...${NC}"
sudo apt update
sudo apt upgrade -y

# Step 2: Install Python and dependencies
echo ""
echo -e "${BLUE}Step 2/7: Installing Python, git, and build tools...${NC}"
sudo apt install -y python3 python3-pip python3-venv python3-dev git build-essential

# Step 3: Install UV
echo ""
echo -e "${BLUE}Step 3/7: Installing UV package manager...${NC}"
pip3 install --upgrade pip
pip3 install uv

# Step 4: Clone repository
echo ""
echo -e "${BLUE}Step 4/7: Cloning RaspPi-Remote-Worker repository...${NC}"
cd ~
if [ -d "RaspPi-Remote-Worker" ]; then
    echo -e "${YELLOW}Repository already exists. Updating...${NC}"
    cd RaspPi-Remote-Worker
    git pull origin main
else
    git clone https://github.com/rhyslwells/RaspPi-Remote-Worker.git
    cd RaspPi-Remote-Worker
fi

# Step 5: Create virtual environment
echo ""
echo -e "${BLUE}Step 5/7: Creating virtual environment...${NC}"
uv venv .venv

# Step 6: Install dependencies
echo ""
echo -e "${BLUE}Step 6/7: Installing Python dependencies...${NC}"
source .venv/bin/activate
uv sync
deactivate

# Step 7: Set up systemd service
echo ""
echo -e "${BLUE}Step 7/7: Setting up systemd service...${NC}"

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
EOF

sudo systemctl daemon-reload
sudo systemctl enable remote-worker.service

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo ""
echo "1. Deploy credentials:"
echo "   From your main machine, run:"
echo "   scp credentials.json pi@$(hostname -I | awk '{print $1}'):~/RaspPi-Remote-Worker/"
echo ""
echo "2. Verify credentials were copied:"
echo "   ls -la ~/RaspPi-Remote-Worker/credentials.json"
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
echo "  - docs/scripts/SETUP_QUICKSTART.md (this process)"
echo "  - docs/scripts/RASP_PI_README.md (detailed reference)"
echo "  - docs/scripts/SERVICE_README.md (systemd service management)"
echo ""
