# Setup and operations

Placeholders: `<pi-user>` is the Pi login name, `<pi-ip>` its address. The repo lives at `~/Desktop/RaspPi-Remote-Worker` on the Pi (this is the path `setup_systemd.sh` writes into the service file).

## 1. Google Cloud and the sheet

1. In Google Cloud Console enable the **Google Sheets API** and **Google Drive API**.
2. Create a **service account** and download its key as `credentials.json`.
3. Create the spreadsheet `RaspPI-Remote-Worker` and share it with the service account's email (Editor).
4. The `Config` and `Log` tabs are created with headers on first run if missing. Column layout: [scripts.md](scripts.md#sheet-layout).

`credentials.json` is gitignored. Never commit or paste it.

## 2. Flash and connect to the Pi

1. Flash **Raspberry Pi OS (64-bit)** with [Raspberry Pi Imager](https://www.raspberrypi.com/software/). In the Imager settings set the hostname, user, password, Wi-Fi and enable SSH.
2. Find the Pi's IP from your router's device list (or use [Raspberry Pi Connect](https://connect.raspberrypi.com/devices) for browser access).
3. Connect: `ssh <pi-user>@<pi-ip>`.

Card will not format on Windows: [knowledge/SD_CARD_FORMAT.md](knowledge/SD_CARD_FORMAT.md).

### VS Code Remote SSH (optional)

Install the "Remote - SSH" extension, run **Remote-SSH: Add New SSH Host** with `ssh <pi-user>@<pi-ip>`, connect, then open `~/Desktop/RaspPi-Remote-Worker`. For password-free logins: `ssh-keygen -t ed25519` then `ssh-copy-id <pi-user>@<pi-ip>`.

## 3. Install on the Pi

```bash
cd ~/Desktop
git clone https://github.com/rhyslwells/RaspPi-Remote-Worker.git
cd RaspPi-Remote-Worker
bash setup_initial.sh     # apt packages, venv, uv, uv sync (about 5-10 minutes)
bash setup_systemd.sh     # writes and enables remote-worker.service
```

Run both as the normal user (not root); they ask for `sudo` when needed.

Manual dependency install, if you skip the script: `uv venv .venv && source .venv/bin/activate && uv sync`.

`setup_systemd.sh` writes this unit (user and paths are fixed in the script):

- runs `.venv/bin/python3 scripts/runner.py` from the repo root (so `credentials.json` resolves)
- `Restart=always`, `RestartSec=10`
- stdout and stderr appended to `logs/service.log`

## 4. Deploy credentials

From your main machine:

```bash
scp credentials.json <pi-user>@<pi-ip>:~/Desktop/RaspPi-Remote-Worker/
```

## 5. Run and manage the service

```bash
sudo systemctl start remote-worker.service
sudo systemctl status remote-worker.service
sudo systemctl restart remote-worker.service
sudo systemctl stop remote-worker.service
journalctl -u remote-worker.service -f      # live logs
tail -n 50 ~/Desktop/RaspPi-Remote-Worker/logs/service.log
```

Run in the foreground for debugging (stop the service first):

```bash
cd ~/Desktop/RaspPi-Remote-Worker
source .venv/bin/activate
python3 scripts/runner.py
```

## 6. Updating

The Pi does not update itself: push to GitHub first, then use any one of these.

| Method | How | Restarts the service? |
|--------|-----|-----------------------|
| From the sheet | Set `git_pull_update.py` to `START` in `Config` (add the row once) | No; the result says "restart needed" when `runner.py` or `utils/` changed |
| From your PC | `update_raspi_repo` (helper script, below) | Yes |
| On the Pi | the commands below | Yes |

Manual commands:

```bash
cd ~/Desktop/RaspPi-Remote-Worker
git pull origin main
source .venv/bin/activate && uv sync
sudo systemctl restart remote-worker.service
```

`update_raspi_repo` in the helper script does the same over SSH. If `git pull` is denied, set up SSH keys for GitHub or use HTTPS with a personal access token (`git remote -v` shows the current URL).

## 7. Helper script (`raspi-helper.sh`)

Run from the repo root in Git Bash, WSL or any bash shell:

```bash
source raspi-helper.sh
save_raspi_config <pi-ip>     # once; stored in .raspi-config (tracked in git)
```

| Command | Purpose |
|---------|---------|
| `connect_raspi` | SSH into the Pi |
| `test_raspi_connection` | Ping, SSH, repo, credentials and service checks |
| `copy_credentials_to_raspi <file>` | Deploy `credentials.json` |
| `start_raspi_service`, `stop_raspi_service`, `restart_raspi_service`, `get_raspi_service_status` | Service control |
| `watch_raspi_logs` | Live journal (Ctrl+C to exit) |
| `get_raspi_logs [dir]` | Download `logs/` |
| `update_raspi_repo` | Pull, `uv sync`, restart |
| `get_raspi_info` | OS, Python, disk, memory, IP, service state |
| `show_help` | List commands |

The SSH user is set by `PI_USER` at the top of the script. All remote paths are `~/Desktop/RaspPi-Remote-Worker`.

## Troubleshooting

| Symptom | Check |
|---------|-------|
| Service will not start | `journalctl -u remote-worker.service -n 50`; `credentials.json` present in the repo root; paths in the unit match the real location |
| `Credentials file not found` | The service must run from the repo root; copy the file there |
| `Could not find spreadsheet` | Name must match `RaspPI-Remote-Worker`; sheet must be shared with the service account |
| Service restarts repeatedly | Look for Sheets API errors or missing dependencies in `logs/service.log` |
| Row stuck on `RUNNING` | The Pi restarted mid-script. Set the cell back to `IDLE` by hand (automatic recovery is proposed in [improvements.md](improvements.md)) |
| `Please don't run this script as root` | Run the setup scripts without `sudo` |
