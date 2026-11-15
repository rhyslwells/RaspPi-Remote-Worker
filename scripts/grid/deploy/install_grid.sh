#!/bin/bash

# GB grid collector - install or remove the systemd timers on the Pi.
# Run from the repo on the Pi, as the normal user (it asks for sudo):
#   bash scripts/grid/deploy/install_grid.sh              # install and enable
#   bash scripts/grid/deploy/install_grid.sh --uninstall  # stop and remove
#
# The unit files in this folder use __USER__ and __REPO__ placeholders; they are
# filled in from the current user and the location of this checkout.

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../../.." && pwd)"
RUN_USER="$(id -un)"
UNIT_DIR=/etc/systemd/system
TIMERS="grid-elexon grid-agile grid-summary grid-backup grid-gsp grid-prune"

if [ "$EUID" -eq 0 ]; then
    echo -e "${YELLOW}Run as the normal user, not root (the script uses sudo itself).${NC}"
    exit 1
fi

if [ "$1" = "--uninstall" ]; then
    echo -e "${BLUE}Removing GB grid timers...${NC}"
    for t in $TIMERS; do
        sudo systemctl disable --now "$t.timer" 2>/dev/null || true
        sudo rm -f "$UNIT_DIR/$t.timer"
    done
    sudo rm -f "$UNIT_DIR/grid-collector@.service"
    sudo systemctl daemon-reload
    echo -e "${GREEN}Removed. data/grid.db and logs are left in place.${NC}"
    exit 0
fi

if [ ! -x "$REPO/.venv/bin/python3" ]; then
    echo -e "${YELLOW}No virtualenv at $REPO/.venv. Run 'uv sync' first.${NC}"
    exit 1
fi

TZ_NOW="$(timedatectl show -p Timezone --value 2>/dev/null || true)"
if [ "$TZ_NOW" != "Europe/London" ]; then
    echo -e "${YELLOW}Pi timezone is '${TZ_NOW:-unknown}', not Europe/London.${NC}"
    echo "The Agile timer follows the system timezone. Fix with:"
    echo "  sudo timedatectl set-timezone Europe/London"
    exit 1
fi

echo -e "${BLUE}This will install the grid collector timers for user '$RUN_USER'${NC}"
echo "  repo: $REPO"
echo "  timers: $TIMERS"
read -p "Proceed? (y/n) " -n 1 -r
echo ""
[[ $REPLY =~ ^[Yy]$ ]] || { echo "Cancelled."; exit 1; }

# Check the OnCalendar expressions parse before touching /etc.
grep -h "^OnCalendar=" "$HERE"/*.timer 2>/dev/null | cut -d= -f2- | while read -r expr; do
    systemd-analyze calendar "$expr" > /dev/null || { echo "Bad OnCalendar: $expr"; exit 1; }
done

mkdir -p "$REPO/data" "$REPO/logs"

render() {  # render <file> -> stdout
    sed -e "s#__USER__#$RUN_USER#g" -e "s#__REPO__#$REPO#g" "$HERE/$1"
}

render "grid-collector@.service" | sudo tee "$UNIT_DIR/grid-collector@.service" > /dev/null
for t in $TIMERS; do
    render "$t.timer" | sudo tee "$UNIT_DIR/$t.timer" > /dev/null
done

sudo systemctl daemon-reload
for t in $TIMERS; do
    sudo systemctl enable --now "$t.timer"
done

echo ""
echo -e "${GREEN}Installed.${NC} Next runs:"
systemctl list-timers 'grid-*' --no-pager
echo ""
echo "Fill the database now (optional, 7 days; the gsp timer fills regional data itself from 04:00):"
echo "  $REPO/.venv/bin/python3 scripts/grid/collect.py backfill --from \$(date -d '7 days ago' +%F) --to \$(date +%F)"
echo "Logs: journalctl -u 'grid-collector@*' -n 50   and   $REPO/logs/grid_collector.log"
echo "Optional heartbeat: put GRID_HEARTBEAT_URL=... in /etc/default/grid-collector"
