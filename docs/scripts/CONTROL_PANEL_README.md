# Control Panel Class Documentation

## Overview

The **Control Panel** is a centralized Python class for managing script execution through a Google Sheet. It provides a clean interface for:

- **Reading script commands** from a Config sheet
- **Updating script status** (IDLE, START, RUNNING, SUCCESS, FAILED)
- **Logging execution history** to a Log sheet
- **Managing the complete script lifecycle** from START to completion
- **Supporting future multi-processing** operations

This class eliminates the need for individual scripts to handle their own Google Sheets authentication and logging, creating a consistent, maintainable system.

---

## Architecture

### Google Sheets Structure

The Control Panel expects your spreadsheet to have two sheets:

#### **Config Sheet**
Contains script definitions and current status.

| Column | Name | Purpose |
|--------|------|---------|
| A | Script Name | Name of the script to manage |
| B | Status | Current status (IDLE, START, RUNNING, SUCCESS, FAILED) |
| C | Last Used | Timestamp of last status change |
| D | Details | Additional information or error messages |
| E | Priority | Execution priority (1-10) |

**Example:**
```
Script Name       | Status  | Last Used           | Details         | Priority
test_connection   | IDLE    | 2025-03-13 10:30:00 | Ready           | 5
prime_hunter      | START   | 2025-03-13 10:29:00 | Queued          | 3
pulse_monitor     | SUCCESS | 2025-03-13 10:15:00 | Completed       | 5
```

#### **Log Sheet**
Complete execution history for auditing and debugging.

| Column | Name | Purpose |
|--------|------|---------|
| A | Timestamp | When the event occurred |
| B | Script Name | Which script this event is for |
| C | Status | Status at this point (IDLE, START, RUNNING, SUCCESS, FAILED) |
| D | Message | Human-readable status description |
| E | Details | Technical details or error trace |

**Example:**
```
Timestamp               | Script Name    | Status  | Message                    | Details
2025-03-13 10:30:00    | test_connection | RUNNING | Script execution started   | 
2025-03-13 10:30:15    | test_connection | SUCCESS | Execution completed...     | Connection verified
2025-03-13 10:31:00    | prime_hunter    | START   | Waiting for execution      | 
```

---

## Status Lifecycle

Scripts follow this status flow:

```
IDLE → START (triggered manually in sheet)
     ↓
  RUNNING (script begins execution)
     ↓
  SUCCESS or FAILED (execution completes)
     ↓
  IDLE (ready for next START)
```

### Status Reference

| Status | Meaning | Who Sets It |
|--------|---------|------------|
| `IDLE` | Script is ready to execute (default state) | Manual reset, or START→SUCCESS/FAILED→IDLE |
| `START` | Trigger signal; script should begin execution | Manual in spreadsheet |
| `RUNNING` | Script is actively executing | Control Panel (auto) |
| `SUCCESS` | Last execution completed without errors | Control Panel (auto) |
| `FAILED` | Last execution encountered an error | Control Panel (auto) |

---

## Installation & Setup

### 1. Credentials

Ensure you have `credentials.json` in your project root (created during Phase 1: Environment Setup).

### 2. Python Version

Requires Python 3.10+

### 3. Dependencies

The required packages are listed in `pyproject.toml`:
```toml
dependencies = [
    "gspread>=6.0.0",
    "oauth2client>=4.1.3",
    ...
]
```

Install with:
```bash
pip install -e .
```

---

## Usage

### Basic Initialization

```python
from utils.control_panel import ControlPanel, ScriptStatus

# Create a Control Panel instance
panel = ControlPanel(
    spreadsheet_name="RaspPI-Remote-Worker",
    credentials_path="credentials.json",
    config_sheet_name="Config",
    log_sheet_name="Log"
)
```

### Check Script Status

```python
status = panel.get_script_status("test_connection")

if status == ScriptStatus.START:
    print("Script has been triggered!")
elif status == ScriptStatus.RUNNING:
    print("Script is already running")
else:
    print(f"Current status: {status.value}")
```

### Update Script Status

Update status and log the change to the Log sheet:

```python
# Simple status update
panel.set_script_status(
    script_name="test_connection",
    status=ScriptStatus.RUNNING,
    message="Starting execution"
)

# With additional details
panel.set_script_status(
    script_name="prime_hunter",
    status=ScriptStatus.SUCCESS,
    message="Hunt completed",
    details="Found 15 primes between 100-200"
)
```

### Log Execution Events

Record events to the Log sheet (independent of Config sheet updates):

```python
panel.log_execution(
    script_name="pulse_monitor",
    status=ScriptStatus.RUNNING,
    message="Reading sensor data",
    details="Sampling at 100Hz for 10 seconds"
)
```

### Execute Complete Script Lifecycle

Automatically handle START → RUNNING → SUCCESS/FAILED transitions:

```python
def my_script_logic():
    """The actual work of your script."""
    try:
        # Your script logic here
        result = expensive_computation()
        return (True, "Computation successful", f"Result: {result}")
    except Exception as e:
        return (False, "Computation failed", str(e))

# Execute with full lifecycle management
success = panel.execute_script_lifecycle(
    script_name="my_script",
    execution_func=my_script_logic
)

# The Control Panel will:
# 1. Set status to RUNNING
# 2. Execute my_script_logic()
# 3. Set status to SUCCESS or FAILED based on result
# 4. Log everything to the Log sheet
```

### Get Scripts Ready to Run

Retrieve all scripts with START status:

```python
scripts_to_run = panel.get_scripts_to_run()
# Returns: ["test_connection", "prime_hunter"]

for script_name in scripts_to_run:
    panel.execute_script_lifecycle(
        script_name=script_name,
        execution_func=lambda: run_my_script(script_name)
    )
```

### Add New Script to Config

Programmatically register a new script:

```python
panel.add_script_to_config(
    script_name="my_new_script",
    priority=3
)
```

### Get All Scripts

Retrieve complete script list:

```python
all_scripts = panel.get_all_scripts()
for script in all_scripts:
    print(f"{script['Script Name']}: {script['Status']}")
```

### Reset to IDLE

Reset all scripts to IDLE (useful for system recovery):

```python
panel.reset_all_to_idle()
```

---

## Real-World Example

Here's an example script using Control Panel:

```python
#!/usr/bin/env python3
"""
Prime Hunter Script
Finds prime numbers and logs results.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from utils.control_panel import ControlPanel, ScriptStatus


def find_primes(start: int, end: int) -> list:
    """Find all primes between start and end."""
    primes = []
    for num in range(max(2, start), end + 1):
        is_prime = all(num % i != 0 for i in range(2, int(num ** 0.5) + 1))
        if is_prime:
            primes.append(num)
    return primes


def main():
    # Initialize Control Panel
    panel = ControlPanel(spreadsheet_name="RaspPI-Remote-Worker")
    
    # Define the actual script logic
    def execution_func():
        try:
            # Your script work
            primes = find_primes(100, 200)
            
            message = f"Found {len(primes)} primes"
            details = f"Primes: {primes[:5]}..." if len(primes) > 5 else f"Primes: {primes}"
            
            return (True, message, details)
        except Exception as e:
            return (False, "Error finding primes", str(e))
    
    # Execute with full lifecycle management
    success = panel.execute_script_lifecycle(
        script_name="prime_hunter",
        execution_func=execution_func
    )
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
```

---

## Advanced Features

### Custom Logging

Access the Control Panel's logger:

```python
panel.logger.info("This is an info message")
panel.logger.error("This is an error message")
panel.logger.warning("This is a warning")
```

### Multi-Processing Considerations

For future multi-processing support, keep these principles in mind:

1. **Always use `set_script_status()` or `execute_script_lifecycle()`** - These handle sheet updates atomically
2. **Status polling interval** - In runner.py, add a small delay between checks
3. **Lock on config sheet updates** - When implementing multi-process workers, add a lock mechanism
4. **Log sheet is append-only** - Multiple processes can safely append to the Log sheet simultaneously

Example runner pattern for future multi-processing:

```python
from concurrent.futures import ThreadPoolExecutor
import time

panel = ControlPanel(spreadsheet_name="RaspPI-Remote-Worker")
executor = ThreadPoolExecutor(max_workers=4)

while True:
    scripts_to_run = panel.get_scripts_to_run()
    
    for script_name in scripts_to_run:
        # Submit to thread pool
        executor.submit(
            panel.execute_script_lifecycle,
            script_name=script_name,
            execution_func=lambda: run_script(script_name)
        )
    
    time.sleep(10)  # Poll every 10 seconds
```

---

## Error Handling

The Control Panel provides robust error handling:

### File Not Found
```python
try:
    panel = ControlPanel(credentials_path="invalid_path.json")
except FileNotFoundError as e:
    print(f"Credentials not found: {e}")
```

### Spreadsheet Not Found
```python
try:
    panel = ControlPanel(spreadsheet_name="Non-existent-Sheet")
except gspread.exceptions.SpreadsheetNotFound as e:
    print(f"Spreadsheet not found: {e}")
```

### Script Not Found in Config
```python
success = panel.set_script_status(
    script_name="unknown_script",
    status=ScriptStatus.RUNNING
)
if not success:
    print("Script not found in Config sheet")
```

All methods return meaningful error messages logged to the console and the Log sheet.

---

## Testing

### Connection Test

Use the updated `test_connection.py` to verify everything works:

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
🔗 Successfully authenticated with Google Sheets API
📊 Opened spreadsheet: RaspPI-Remote-Worker
📋 Accessed existing worksheet: Config
📋 Accessed existing worksheet: Log

✅ Connection test SUCCESSFUL!
   Script: test_connection.py
   Spreadsheet: RaspPI-Remote-Worker
   Status logged to Log worksheet

============================================================
```

---

## Troubleshooting

### "credentials.json not found"
- Ensure `credentials.json` is in the project root
- Check that service account has access to your spreadsheet

### "Could not find spreadsheet"
- Verify the spreadsheet name matches exactly in the Control Panel initialization
- Check that the service account email (from credentials.json) has Editor access to the sheet

### Status not updating
- Verify you're calling `set_script_status()` or `execute_script_lifecycle()`
- Check the Log sheet to view error messages
- Ensure the script name exists in the Config sheet

### Performance issues with large logs
- The Log sheet is append-only; old logs can be archived to another sheet if it grows too large
- Consider adding a cleanup task to archive logs older than 30 days

---

## API Reference

### ControlPanel Class

```python
class ControlPanel:
    # Initialization
    __init__(spreadsheet_name, credentials_path="credentials.json", 
             config_sheet_name="Config", log_sheet_name="Log")
    
    # Read operations
    get_script_status(script_name) -> Optional[ScriptStatus]
    get_scripts_to_run() -> List[str]
    get_all_scripts() -> List[Dict[str, str]]
    
    # Write operations
    set_script_status(script_name, status, message="", details="") -> bool
    add_script_to_config(script_name, priority=5) -> bool
    log_execution(script_name, status, message="", details="") -> bool
    
    # Lifecycle management
    execute_script_lifecycle(script_name, execution_func) -> bool
    reset_all_to_idle() -> bool
    
    # Attributes
    workbook: gspread.Spreadsheet
    config_sheet: gspread.Worksheet
    log_sheet: gspread.Worksheet
    logger: logging.Logger
```

### ScriptStatus Enum

```python
class ScriptStatus(Enum):
    IDLE = "IDLE"
    START = "START"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
```

---

## Next Steps

1. **Update existing scripts** - Migrate `prime_hunter.py`, `pulse_monitor.py`, etc. to use Control Panel
2. **Implement runner.py** - Use Control Panel in the main polling loop (Phase 2)
3. **Add systemd service** - Configure Control Panel to run on Pi boot
4. **Monitor & log** - Archive old logs monthly; set up alerts for FAILED status

---

## Questions & Support

For issues or questions:
1. Check the Log sheet for error details
2. Review the console output when running scripts
3. Verify Config sheet contains your script entries
4. Check that credentials.json has proper permissions


## Initial Notes

Config Class
- for the google sheet actiing as a config 
   we will need a python class here, that can be imported into respective scripts, so that they know when to run, ect.
   - Later we will need to consider multi processing.
   - if a script complete i would like the config sheet status to change respectively. 
   - Current options are "IDLE", "START", "RUNNING", "SUCCESS", "FAILED"
   - scripts\test_connection.py will need to be updated with respect to the new class, removing any uncessary code.
   - Part of the class should be to log the the status's like in scripts\test_connection.py to the Log sheet. So that this tracks any scripts that get run. 
   - We will need a readme file in C:\Users\RhysL\Desktop\RaspPi-Remote-Worker\docs\scripts to be generated.
