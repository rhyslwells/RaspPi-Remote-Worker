Because we can remote access it i can just copy/past cred and secrets onto the rasppi and store them in a local folder that is gitignored. Then the codebase can reference these files without them being in the repo.
---

active cooler for rasppi
buy

---
remote ssh to rasp pi

here: use 
Remote shh connect 

will need to get the connection working though.
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
Connecting via terminal shh to rasppi is not working, will use raspberry remote connect instead: https://connect.raspberrypi.com/devices

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