# Runner.py Documentation

## Overview

**Runner.py** is the central orchestration service that powers your Raspberry Pi Remote Worker system. It continuously polls your Google Sheet's Config worksheet and executes scripts based on their status, managing the complete lifecycle from START to SUCCESS/FAILED.

Think of it as a "daemon" that sits on your Raspberry Pi, waiting for you to set a script's status to `START` in the Google Sheet, then automatically executes it and reports results back.

---

## How It Works

### Polling Loop Architecture

Runner.py follows a simple but powerful polling pattern:

```
┌─────────────────────────────────────────────┐
│  Runner.py Polling Loop                     │
└─────────────────────────────────────────────┘
           ↓
   ┌───────────────────┐
   │  Initialize       │
   │  Control Panel    │
   └─────────┬─────────┘
           ↓
   ┌───────────────────────────────────────┐
   │  Loop (every 10 seconds):             │
   │                                       │
   │  1. Read Config sheet                 │
   │  2. Find scripts with Status=START    │
   │  3. For each script:                  │
   │     - Execute it                      │
   │     - Update Status → RUNNING         │
   │     - Run script logic                │
   │     - Update Status → SUCCESS/FAILED  │
   │     - Log to Log sheet                │
   │  4. Sleep 10 seconds                  │
   │  5. Repeat                            │
   └─────────────────────────────────────┘
           ↓
   ┌───────────────────┐
   │ Update Google     │
   │ Sheet on each     │
   │ status change     │
   └───────────────────┘
```

### Timeline Example

```
Time    │ Google Sheet                │ Runner.py                    │ Log Sheet
        │ Status Column               │ Action                       │ Record
─────────────────────────────────────────────────────────────────────────────
10:00   │ test_connection: IDLE       │ Polling...                   │
10:05   │ test_connection: START      │ User sets to START           │
10:10   │ test_connection: START      │ Detected! Set → RUNNING      │ RUNNING entry
        │ test_connection: RUNNING    │ Executing script...          │
10:15   │ test_connection: RUNNING    │ Script completes             │
        │ test_connection: SUCCESS    │ Set → SUCCESS                │ SUCCESS entry
        │ Last Used: 10:15            │ (Last Used timestamp added)  │
10:20   │ test_connection: SUCCESS    │ Polling... (idle)            │
```

---

## System Components

### 1. Runner.py (The Service)
- Runs continuously on your Raspberry Pi
- Polls the Config sheet every 10 seconds
- Detects scripts with `START` status
- Manages script execution lifecycle
- Updates Config and Log sheets

### 2. Control Panel (Shared Library)
- Handles all Google Sheets authentication
- Manages status updates consistently
- Logs execution history
- Available to both Runner and individual scripts

### 3. Config Sheet (Your Control Interface)
- Manual trigger interface (you set Status to START)
- Current status visibility
- Last Used timestamp tracking

### 4. Log Sheet (Audit Trail)
- Complete history of all executions
- Timestamps, statuses, messages
- Useful for debugging and monitoring

### 5. Your Scripts (The Work)
- Individual Python modules in `/scripts` folder
- Execute when Runner detects START status
- Return (success, message, details) tuple
- Can be as simple or complex as needed

---

## Setup & Installation

### Prerequisites

1. **Python 3.10+** installed on your Raspberry Pi
2. **credentials.json** in project root (service account credentials)
3. **Google spreadsheet** created (see Phase 1: Environment Setup docs)
4. **Dependencies installed**: `pip install -e .`

### Initial Setup

#### 1. Verify Control Panel Works

```bash
cd scripts
python test_connection.py
```

Expected output:
```
============================================================
🧪 Remote Worker - Connection Test
============================================================

📝 Initializing Control Panel...
✅ Connection test SUCCESSFUL!
```

#### 2. Register Scripts in Config Sheet

Add your scripts to the Config sheet. Example:

| Script Name | Status | Last Used | Details | Priority |
|---|---|---|---|---|
| test_connection | IDLE | | | 5 |
| prime_hunter | IDLE | | | 5 |
| pulse_monitor | IDLE | | | 5 |

#### 3. Test Runner Locally

```bash
# From the project root
python scripts/runner.py
```

You should see:
```
📝 Initializing Control Panel...
🔗 Successfully authenticated with Google Sheets API
📊 Opened spreadsheet: RaspPI-Remote-Worker
📋 Accessed existing worksheet: Config
📋 Accessed existing worksheet: Log
✅ Control Panel initialized for spreadsheet: RaspPI-Remote-Worker

[Polling... waiting for START triggers]
```

---

## Configuration

### Polling Interval

By default, Runner polls every **10 seconds**. To change this:

**In runner.py**, line ~28:
```python
time.sleep(10)  # ← Change this number (in seconds)
```

- **5 seconds**: More responsive, higher API quota usage
- **10 seconds**: (default) Good balance of responsiveness and efficiency
- **30 seconds**: Slower response, but lower quota usage

### Spreadsheet Name

Runner defaults to:
```python
panel = ControlPanel(spreadsheet_name="RaspPI-Remote-Worker")
```

Change this to match your actual spreadsheet name.

### Adding New Sheets

If you rename your Config or Log sheets, update:
```python
panel = ControlPanel(
    spreadsheet_name="RaspPI-Remote-Worker",
    config_sheet_name="Config",      # ← Change if renamed
    log_sheet_name="Log"              # ← Change if renamed
)
```

---

## Registering Scripts

### What Runner Needs

Runner executes scripts by their **filename**. For Runner to find and run a script:

1. **Script file** must be in `/scripts` folder
2. **Script name** must be in Config sheet column A
3. Script must define an execution function that returns `(success: bool, message: str, details: str)`

### Step-by-Step: Register a New Script

#### Step 1: Create Script File

Create `/scripts/my_script.py`:
```python
#!/usr/bin/env python3
"""
My Custom Script
Does something useful on your Raspberry Pi.
"""

def main():
    """Main script execution."""
    try:
        # Your actual work here
        result = do_something_useful()
        
        return (
            True,
            "Execution successful",
            f"Result: {result}"
        )
    except Exception as e:
        return (
            False,
            "Execution failed",
            str(e)
        )

if __name__ == "__main__":
    success, message, details = main()
    exit(0 if success else 1)
```

#### Step 2: Add to Config Sheet

Add entry to Config worksheet:
| Script Name | Status | Last Used | Details | Priority |
|---|---|---|---|---|
| my_script.py | IDLE | | | 5 |

#### Step 3: Trigger via Google Sheet

- Open your spreadsheet in browser
- Set `my_script.py` Status to `START`
- Runner polls and finds the START trigger within 10 seconds
- Script executes automatically
- Status updates to SUCCESS or FAILED

---

## Creating Custom Scripts

### Full Example: Prime Finder Script

Here's a complete script that Runner can execute:

```python
#!/usr/bin/env python3
"""
Prime Finder Script
Finds all prime numbers in a given range.
Demonstrates how to create a Runner-compatible script.
"""

import sys
import time
from pathlib import Path

# Add parent directory to import utils
sys.path.insert(0, str(Path(__file__).parent))
from utils.control_panel import ControlPanel, ScriptStatus


def find_primes(start: int, end: int) -> list:
    """
    Find all prime numbers between start and end (inclusive).
    
    Args:
        start: Starting number
        end: Ending number
        
    Returns:
        List of prime numbers found
    """
    primes = []
    for num in range(max(2, start), end + 1):
        # Simple primality test
        is_prime = all(num % i != 0 for i in range(2, int(num ** 0.5) + 1))
        if is_prime:
            primes.append(num)
        
        # Log progress occasionally
        if num % 100 == 0:
            print(f"  Checking... {num}")
    
    return primes


def main():
    """
    Main execution function.
    
    Returns:
        Tuple of (success: bool, message: str, details: str)
        This is what Runner expects from your script!
    """
    try:
        print("🔍 Starting prime finder...")
        
        start_time = time.time()
        
        # Your script work here
        primes = find_primes(100, 1000)
        
        elapsed = time.time() - start_time
        
        # Prepare results
        message = f"Found {len(primes)} primes"
        details = f"Range: 100-1000 | Time: {elapsed:.2f}s | Primes: {primes[:5]}..."
        
        print(f"✅ {message}")
        print(f"   {details}")
        
        # Return tuple: (success, message, details)
        return (True, message, details)
        
    except Exception as e:
        error_msg = f"Error finding primes: {str(e)}"
        print(f"❌ {error_msg}")
        return (False, "Execution failed", str(e))


if __name__ == "__main__":
    success, message, details = main()
    exit(0 if success else 1)
```

### Script Requirements

Your script must:

1. **Return a tuple** from main():
   ```python
   return (success: bool, message: str, details: str)
   ```

2. **Handle errors gracefully**:
   ```python
   try:
       # your work
       return (True, "Success message", "Details")
   except Exception as e:
       return (False, "Error message", str(e))
   ```

3. **Be in `/scripts` folder** with `.py` extension

4. **Have script name in Config sheet** exactly as file name

### Optional: Direct Control Panel Usage

Scripts can optionally use Control Panel for logging progress:

```python
from utils.control_panel import ControlPanel, ScriptStatus

panel = ControlPanel(spreadsheet_name="RaspPI-Remote-Worker")

# Log progress to Log sheet
panel.log_execution(
    script_name="prime_hunter.py",
    status=ScriptStatus.RUNNING,
    message="Searching: 100-500",
    details="Current progress"
)

# Or use full lifecycle (Control Panel manages status automatically)
def my_logic():
    # ... do work ...
    return (True, "Done", "Details")

success = panel.execute_script_lifecycle(
    script_name="my_script.py",
    execution_func=my_logic
)
```

---

## Running on Raspberry Pi

### Option 1: Manual Start

```bash
# SSH into your Pi
ssh pi@raspberrypi.local

# Navigate to project
cd /home/pi/RaspPi-Remote-Worker

# Start runner
python3 scripts/runner.py
```

### Option 2: Background Process (Screen)

```bash
# Start in detachable session
screen -S runner python3 scripts/runner.py

# Detach: Ctrl+A, then D
# Reattach: screen -r runner
```

### Option 3: systemd Service (Recommended)

Create `/etc/systemd/system/remote-worker.service`:

```ini
[Unit]
Description=RaspPi Remote Worker Runner
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/RaspPi-Remote-Worker
ExecStart=/usr/bin/python3 /home/pi/RaspPi-Remote-Worker/scripts/runner.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable remote-worker
sudo systemctl start remote-worker

# Check status
sudo systemctl status remote-worker

# View logs
journalctl -u remote-worker -f
```

---

## Triggering Scripts

### From Google Sheet

1. Open your spreadsheet in browser
2. Find the script in Config sheet
3. Set Status column to `START`
4. Runner detects this within 10 seconds
5. Script executes and status updates

### From Command Line (Testing)

Manually set Status before running:
```bash
# Set test_connection to START in your Config sheet
# Then run runner:
python3 scripts/runner.py

# Runner will execute it and update status
```

---

## Monitoring & Logs

### Console Output

While runner is running, you'll see:

```
✅ Control Panel initialized for spreadsheet: RaspPI-Remote-Worker
Executing: test_connection
✅ Updated test_connection status to RUNNING - Script execution started
✅ Executed test_connection - Execution completed successfully
Executing: prime_hunter
✅ Updated prime_hunter status to RUNNING - Script execution started
✅ Executed prime_hunter - Execution completed successfully
```

### Google Sheet Log Sheet

The Log sheet contains:
- **Timestamp**: When the event occurred
- **Script Name**: Which script
- **Status**: IDLE, START, RUNNING, SUCCESS, FAILED
- **Message**: Human-readable description
- **Details**: Technical details or error trace

### systemd Logs

```bash
# View recent logs
journalctl -u remote-worker -n 50

# Follow live logs
journalctl -u remote-worker -f

# Logs from specific date
journalctl -u remote-worker --since "2025-03-13"
```

---

## Troubleshooting

### "Script not found in Config sheet"

**Problem**: Runner says script doesn't exist in Config sheet.

**Solution**:
1. Verify script name in Config sheet matches exactly (including .py extension)
2. Check spelling and capitalization
3. Ensure row has the script name in Column A

### "Connection failed"

**Problem**: Runner can't reach Google Sheets API.

**Solutions**:
1. Verify `credentials.json` exists in project root
2. Check internet connection on Raspberry Pi
3. Verify service account has access to spreadsheet
4. Check API quotas haven't been exceeded

### "Script timed out"

**Problem**: Script takes too long and doesn't return in time.

**Solutions**:
1. Scripts should ideally complete in under 5 minutes
2. For long-running tasks, break into smaller scripts
3. Log progress to Log sheet so you can see it's working
4. Consider running once per day instead of on-demand

### "Status stuck on RUNNING"

**Problem**: Script crashed and status didn't update.

**Solutions**:
1. Check the Log sheet for error messages
2. Manually reset Status to IDLE or re-run
3. Check script error handling (must catch exceptions!)
4. Verify script returns (success, message, details) tuple

### "Runner keeps restarting"

**Problem**: systemd service restarts every 10 seconds.

**Solutions**:
1. Check logs: `journalctl -u remote-worker -f`
2. Run manually to see error: `python3 scripts/runner.py`
3. Verify credentials.json path is correct
4. Check Google Sheets API is enabled

---

## Multi-Script Execution

### Running Scripts in Parallel

By default, scripts run sequentially. For parallel execution with multi-processing:

```python
from concurrent.futures import ThreadPoolExecutor
import time

def main():
    panel = ControlPanel(spreadsheet_name="RaspPI-Remote-Worker")
    executor = ThreadPoolExecutor(max_workers=3)  # 3 scripts at once
    
    while True:
        try:
            scripts_to_run = panel.get_scripts_to_run()
            
            for script_name in scripts_to_run:
                # Submit to thread pool instead of blocking wait
                executor.submit(
                    execute_single_script,
                    panel,
                    script_name
                )
            
            time.sleep(10)
        except Exception as e:
            panel.logger.error(f"Runner error: {e}")
            time.sleep(30)

def execute_single_script(panel, script_name):
    """Execute a single script in a thread."""
    def execution_func():
        return run_my_script(script_name)
    
    panel.execute_script_lifecycle(
        script_name=script_name,
        execution_func=execution_func
    )
```

### Priority-Based Execution

Modify runner to respect Priority column:

```python
scripts_to_run = panel.get_scripts_to_run()

# Sort by priority (lower number = higher priority)
all_scripts = panel.get_all_scripts()
priority_map = {s["Script Name"]: int(s.get("Priority", 5)) 
                for s in all_scripts}

scripts_to_run_sorted = sorted(scripts_to_run, 
                               key=lambda s: priority_map.get(s, 5))

for script_name in scripts_to_run_sorted:
    panel.execute_script_lifecycle(...)
```

---

## Performance Tips

### 1. Optimize Polling Interval

- Scripts that finish < 5 seconds: 10 second interval is fine
- Scripts taking 5-30 seconds: increase to 30-60 seconds
- Long-running scripts: run on schedule instead of on-demand

### 2. Batch Scripts By Time

Instead of constantly checking, schedule specific times:

```python
from datetime import datetime, time

def should_run_now():
    now = datetime.now().time()
    # Only check between 6am and 10pm
    start = time(6, 0)
    end = time(22, 0)
    return start <= now <= end

while True:
    if should_run_now():
        scripts_to_run = panel.get_scripts_to_run()
        # ... execute ...
    
    time.sleep(300)  # Check every 5 minutes
```

### 3. Limit Log Sheet Growth

Archive old logs monthly:

```python
def archive_old_logs():
    """Move logs older than 30 days to Archive sheet."""
    from datetime import datetime, timedelta
    
    logs = panel.log_sheet.get_all_records()
    cutoff = datetime.now() - timedelta(days=30)
    
    # Archive logic here
    pass
```

### 4. Error Recovery

Add circuit breaker for repeated failures:

```python
failed_count = {}

for script_name in scripts_to_run:
    if failed_count.get(script_name, 0) > 3:
        panel.logger.warning(f"Skipping {script_name} - too many failures")
        continue
    
    success = panel.execute_script_lifecycle(...)
    
    if not success:
        failed_count[script_name] = failed_count.get(script_name, 0) + 1
    else:
        failed_count[script_name] = 0
```

---

## Next Steps

1. **Test runner locally**: `python scripts/runner.py`
2. **Register your scripts**: Add to Config sheet
3. **Set up systemd service**: For auto-start on Pi boot
4. **Monitor logs**: Check Log sheet and systemd logs
5. **Optimize**: Adjust polling interval and parallel execution

---

## API Quick Reference

```python
# Initialize
panel = ControlPanel(spreadsheet_name="RaspPI-Remote-Worker")

# Get scripts to run
scripts = panel.get_scripts_to_run()  # Returns list of START scripts

# Execute a script
success = panel.execute_script_lifecycle(
    script_name="my_script.py",
    execution_func=lambda: (True, "Success", "Details")
)

# Direct status update
panel.set_script_status(
    script_name="my_script.py",
    status=ScriptStatus.RUNNING,
    message="In progress"
)

# Log an event
panel.log_execution(
    script_name="my_script.py",
    status=ScriptStatus.SUCCESS,
    message="Completed",
    details="All systems operational"
)
```

---

## Questions?

- See [CONTROL_PANEL_README.md](CONTROL_PANEL_README.md) for Control Panel details
- Check Google Sheet Log for execution history
- Review systemd logs: `journalctl -u remote-worker -f`
