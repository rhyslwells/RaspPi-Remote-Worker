activate venv:
source .venv/bin/activate

python3 scripts/runner.py 


---
To run on startup, you need to set up the systemd service. The `setup_systemd.sh` script configures a service that runs `python3 scripts/runner.py` on boot and restarts it if it crashes.
docs/scripts/SETUP_SH_README.md

# Start the service
sudo systemctl start remote-worker.service

# Stop the service
sudo systemctl stop remote-worker.service
