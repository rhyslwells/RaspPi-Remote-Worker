We will put all tasks here: under a respective descriptive header.

## Quick Start Checklist

- [x] Phase 1: Complete Google Cloud setup and generate `credentials.json`
- [x] Phase 1: Initialize GitHub repository with proper structure
- [ ] Phase 2: Install Python dependencies on Raspberry Pi
- [ ] Phase 2: Create and enable systemd service
- [ ] Phase 3: Implement first script (Test Connection)
- [x] Test: Create connection test script and verify logging works

---

## Control Panel: Next Steps
- [ ] **Update existing scripts** - Migrate `prime_hunter.py`, `pulse_monitor.py`, etc. to use Control Panel
- [ ] **Implement runner.py** - Use Control Panel in the main polling loop (Phase 2)
- [ ] **Add systemd service** - Configure Control Panel to run on Pi boot
- [ ] **Monitor & log** - Archive old logs monthly; set up alerts for FAILED status
- [ ] **Multiprocessing** - Explore using multiprocessing to run multiple scripts concurrently without blocking the main loop.

---