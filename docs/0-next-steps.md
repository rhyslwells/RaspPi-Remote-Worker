3. ✅ Use helper script (`raspi-helper.sh` or `raspi-helper.ps1`) for ongoing management
explain these


---

Because we can remote access it i can just copy/past cred and secrets onto the rasppi and store them in a local folder that is gitignored. Then the codebase can reference these files without them being in the repo.
---

active cooler for rasppi
buy

---
remote ssh to rasp pi

here: use 
Remote shh connect 

will need to get the connection working though.

docs\setup\rasp-pi.md

Connecting via terminal shh to rasppi is not working, will use raspberry remote connect instead: https://connect.raspberrypi.com/devices

permision is denied: 

use:ssh rhyslwells@192.168.1.215

when using remote connect the system is in Linux.
---
setup folder needs cleaned to remove duplication.

Sensitive Data Management: Create a dedicated local folder on the Raspberry Pi for configuration.json and other sensitive credentials to be handled via manual transfer.

Repository Refactoring: Update the codebase to reference these external sensitive files while ensuring they are excluded from version control (e.g., via .gitignore).

Repository Syncing: Implement a workflow to sync the GitHub repository to the Raspberry Pi using the existing configuration sheet.

Documentation Archive: Create a /setup folder to store and archive completed documentation for future reference.

---
We will need to conside the enviorment set up of the repo on the raspberry pi.
Will we use UV?
How will I connect to the raspberry pi to set up the repo, and how will I manage the copy of the repo on the raspberry pi going forward. Ie git pull, then uv sync any new dependancies, the repo moving forward? Probablly doing this throguh the terminal.

---
We will need to understand the documentation for controlpanel and runner.

---
Build out these:
C:\Users\RhysL\Desktop\RaspPi-Remote-Worker\scripts\other-ideas.py

---

We will put all tasks here: under a respective descriptive header.

Quick Start Checklist

- [x] Phase 1: Complete Google Cloud setup and generate `credentials.json`
- [x] Phase 1: Initialize GitHub repository with proper structure
- [ ] Phase 2: Install Python dependencies on Raspberry Pi
- [ ] Phase 2: Create and enable systemd service
- [ ] Phase 3: Implement first script (Test Connection)
- [x] Test: Create connection test script and verify logging works

---

Control Panel: Next Steps
- [x] **Update existing scripts** - Migrate `prime_hunter.py`, `pulse_monitor.py`, etc. to use Control Panel
- [x] **Implement runner.py** - Use Control Panel in the main polling loop (Phase 2)
- [ ] **Add systemd service** - Configure Control Panel to run on Pi boot
- [ ] **Multiprocessing** - Explore using multiprocessing to run multiple scripts concurrently without blocking the main loop.

---
README.md and 0-project-overview.md need to be updated to references correclty.




# Mannually copy over creds to the raspberry pi. 

Just copy and paste the contents of the credentials file into a new file on the raspberry pi.

# How to git install on Remote Worker 

### Git Pull Fails

- **Issue:** Permission denied on git pull
- **Solution:**
  - Set up SSH keys for GitHub (or use HTTPS with personal access token)
  - Verify repo URL: `git remote -v`

### 1. Clone the Repository

```bash
cd ~
git clone https://github.com/rhyslwells/RaspPi-Remote-Worker.git
cd RaspPi-Remote-Worker
```

### 2. Create and Activate Virtual Environment

```bash
uv venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies

```bash
uv sync

Once connected via SSH, run this **one-line command** that automates everything:

```bash
curl -sSL https://raw.githubusercontent.com/rhyslwells/RaspPi-Remote-Worker/main/setup.sh | bash -s -- 192.168.1.100
```

This script will:
- ✅ Update system packages
- ✅ Install Python 3.10+ and git
- ✅ Install UV (package manager)
- ✅ Clone the repository
- ✅ Create virtual environment and install dependencies
- ✅ Set up systemd service for auto-start

**Note:** The script will ask you to confirm and may prompt for your password (for `sudo` commands).

What is systemd? It's a Linux system and service manager that allows you to run scripts as background services that start on boot. This means your Remote Worker will automatically start whenever the Raspberry Pi is powered on.


### 5. Verify Installation

```bash
python3 runner.py --help




# How to manually start it:

```bash
# SSH into Pi (if not already connected)
ssh pi@192.168.1.100

# Enable and start the service
sudo systemctl enable remote-worker.service
sudo systemctl start remote-worker.service

# Verify it's running
sudo systemctl status remote-worker.service
```

# 2. and set it to auto-start** (on the Pi)

how do we get it to auto start (this will be needs otherwise will not see Control Panel)

# Script in Control panel to git pull

so it can be run on the rasp pi to pull latest changes and update dependencies. This will be useful for maintenance and updates going forward.

----------





