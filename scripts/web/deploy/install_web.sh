#!/bin/bash

# Remote Worker web UI (Pi Control) - install or remove it on the Pi in one go.
# Run from the repo on the Pi, as the normal user (it asks for sudo):
#   bash scripts/web/deploy/install_web.sh                       # install / repair
#   bash scripts/web/deploy/install_web.sh --stop-sheet-runner   # ...and stop Sheet polling
#   bash scripts/web/deploy/install_web.sh --uninstall           # remove the web service
#
# Safe to run again: every step checks first. It does:
#   1. installs the Python dependencies (.venv/bin/uv sync --locked)
#   2. installs and enables remote-worker-web.service (localhost:8051, starts at boot)
#      and pulse-sample.timer (a Pi health sample every 5 minutes, also from boot)
#   3. installs Tailscale if missing and signs the Pi in (prints a login link: open it
#      on your phone or laptop, same account as your phone's Tailscale app)
#   4. publishes the page to your tailnet only with `tailscale serve` (never Funnel)
# The unit file uses __USER__ and __REPO__ placeholders, filled in from this checkout.

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../../.." && pwd)"
RUN_USER="$(id -un)"
UNIT=remote-worker-web.service
UNIT_DIR=/etc/systemd/system
UNIT_PATH=$UNIT_DIR/$UNIT
PORT=8051

if [ "$EUID" -eq 0 ]; then
    echo -e "${YELLOW}Run as the normal user, not root (the script uses sudo itself).${NC}"
    exit 1
fi

if [ "$1" = "--uninstall" ]; then
    echo -e "${BLUE}Removing the web UI service...${NC}"
    sudo tailscale serve reset 2>/dev/null || true
    sudo systemctl disable --now "$UNIT" 2>/dev/null || true
    sudo rm -f "$UNIT_PATH"
    sudo systemctl disable --now pulse-sample.timer 2>/dev/null || true
    sudo rm -f "$UNIT_DIR/pulse-sample.timer" "$UNIT_DIR/pulse-sample.service"
    sudo systemctl daemon-reload
    echo -e "${GREEN}Removed. Tailscale itself, data/ and logs/ are left in place.${NC}"
    exit 0
fi

if [ ! -x "$REPO/.venv/bin/python3" ]; then
    echo -e "${YELLOW}No virtualenv at $REPO/.venv. Run setup_initial.sh first.${NC}"
    exit 1
fi

echo -e "${BLUE}Step 1/4: Python dependencies${NC}"
# uv lives inside the venv (setup_initial.sh pip-installs it there), not on PATH.
if [ ! -x "$REPO/.venv/bin/uv" ]; then
    "$REPO/.venv/bin/pip" install uv
fi
(cd "$REPO" && .venv/bin/uv sync --locked)

echo -e "${BLUE}Step 2/4: web UI service${NC}"
mkdir -p "$REPO/logs"
sed -e "s|__USER__|$RUN_USER|g" -e "s|__REPO__|$REPO|g" \
    "$HERE/remote-worker-web.service" | sudo tee "$UNIT_PATH" > /dev/null
for f in pulse-sample.service pulse-sample.timer; do
    sed -e "s|__USER__|$RUN_USER|g" -e "s|__REPO__|$REPO|g"         "$HERE/$f" | sudo tee "$UNIT_DIR/$f" > /dev/null
done
# The old Pulse Monitor schedule (a temporary timer started from the page) is replaced
sudo systemctl stop pulse-monitor.timer pulse-monitor.service 2>/dev/null || true
sudo systemctl daemon-reload
sudo systemctl enable --now pulse-sample.timer
sudo systemctl enable "$UNIT"
sudo systemctl restart "$UNIT"
sleep 3
if ! systemctl is-active --quiet "$UNIT"; then
    echo -e "${YELLOW}$UNIT is not running. Last log lines:${NC}"
    tail -n 20 "$REPO/logs/web-service.log" || true
    exit 1
fi
if ! curl -fsS "http://127.0.0.1:$PORT/api/scripts" > /dev/null; then
    echo -e "${YELLOW}Service is up but http://127.0.0.1:$PORT did not answer.${NC}"
    exit 1
fi
echo "  running, answering on 127.0.0.1:$PORT"

echo -e "${BLUE}Step 3/4: Tailscale${NC}"
if ! command -v tailscale > /dev/null; then
    curl -fsSL https://tailscale.com/install.sh | sh
fi
if ! tailscale status > /dev/null 2>&1; then
    echo -e "${YELLOW}Open the login link below on your phone or laptop and sign in.${NC}"
    sudo tailscale up
fi

echo -e "${BLUE}Step 4/4: publish to the tailnet only${NC}"
# Fails the first time if Serve is not enabled on the tailnet; the message carries a
# link to enable it. Open it, then run this script again.
if ! sudo tailscale serve --bg "$PORT"; then
    echo -e "${YELLOW}If the message above has a link, open it to enable Serve, then re-run this script.${NC}"
    exit 1
fi
tailscale serve status

if [ "$1" = "--stop-sheet-runner" ]; then
    echo -e "${BLUE}Stopping the Sheet runner (no more polling of the Sheet)...${NC}"
    sudo systemctl disable --now remote-worker.service
    echo "  Bring it back with: sudo systemctl enable --now remote-worker.service"
fi

echo ""
echo -e "${GREEN}Done. Open the https://...ts.net address above on a device with Tailscale on.${NC}"
echo "Survives a reboot: the web service and Tailscale both start by themselves."
