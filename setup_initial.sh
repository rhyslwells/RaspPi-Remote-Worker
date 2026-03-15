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
echo "  3. Create virtual environment"
echo "  4. Install UV and Python dependencies"
echo ""
echo -e "${YELLOW}You will need to enter your password for sudo commands.${NC}"
echo ""
read -p "Proceed? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Setup cancelled."
    exit 1
fi

# Step 1: Update system
echo ""
echo -e "${BLUE}Step 1/6: Updating system packages...${NC}"
sudo apt update
sudo apt upgrade -y

# Step 2: Install Python and dependencies
echo ""
echo -e "${BLUE}Step 2/6: Installing Python, git, and build tools...${NC}"
sudo apt install -y python3 python3-pip python3-venv python3-dev git build-essential

# Step 3: Create virtual environment
echo ""
echo -e "${BLUE}Step 3/6: Creating virtual environment...${NC}"
python3 -m venv .venv
source .venv/bin/activate

# Step 4: Install UV and dependencies
echo ""
echo -e "${BLUE}Step 4/6: Installing UV and Python dependencies...${NC}"
pip install --upgrade pip
pip install uv
uv sync

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Initial Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo ""
echo "1. Run setup_systemd.sh to set up the systemd service:"
echo "   bash setup_systemd.sh"
echo ""
echo "2. Deploy credentials when ready:"
echo "   From your main machine, run:"
echo "   scp credentials.json pi@$(hostname -I | awk '{print $1}'):~/RaspPi-Remote-Worker/"
echo ""
echo ""
