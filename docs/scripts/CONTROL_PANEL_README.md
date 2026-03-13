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
Contains script definitions, current status, and runtime parameters.

| Column | Name | Purpose |
|--------|------|---------|
| A | Script Name | Name of the script to manage |
| B | Status | Current status (IDLE, START, RUNNING, SUCCESS, FAILED) |
| C | Last Used | Timestamp of last status change |
| D | Details | Additional information or error messages |
| E | Priority | Execution priority (1-10) |
| F+ | Parameter-1, Parameter-2, ... | Script-specific input parameters (dynamic, extensible) |

**Example:**
```
Script Name       | Status  | Last Used           | Details         | Priority | Parameter-1 | Parameter-2
test_connection   | IDLE    | 2025-03-13 10:30:00 | Ready           | 5        |             |
prime_hunter      | START   | 2025-03-13 10:29:00 | Queued          | 3        | 100         | 200
pulse_monitor     | SUCCESS | 2025-03-13 10:15:00 | Completed       | 5        |             |
```

**Parameter Columns:**
- You can add as many `Parameter-X` columns as needed
- Parameter naming should follow the pattern `Parameter-1`, `Parameter-2`, `Parameter-3`, etc.
- Parameters are optional and can be left empty for scripts that don't need them
- The Control Panel automatically discovers and reads all Parameter-X columns

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

### Get Script Parameters

Retrieve parameters for a specific script:

```python
# Get parameters as a dictionary
params = panel.get_script_parameters("prime_hunter")
# Returns: {'Parameter-1': '100', 'Parameter-2': '200'}

# Get parameters as an ordered list
params_list = panel.get_script_parameters_list("prime_hunter")
# Returns: ['100', '200']

# Get all available parameter column headers
headers = panel.get_parameter_headers()
# Returns: ['Parameter-1', 'Parameter-2', 'Parameter-3']
```

**Flexible Parameter Support:**
- The Control Panel automatically discovers all `Parameter-X` columns
- You can add new parameter columns to the Config sheet without modifying code
- Parameters are retrieved in sorted order (Parameter-1, Parameter-2, etc.)
- Empty parameter cells are skipped

**Example usage in a script:**
```python
def execution_func():
    params = panel.get_script_parameters("my_script")
    start = int(params.get('Parameter-1', 0))
    end = int(params.get('Parameter-2', 100))
    
    result = process_range(start, end)
    return (True, "Processing complete", f"Processed {result} items")
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
    
    # Parameter operations (dynamic, supports any number of parameters)
    get_script_parameters(script_name) -> Dict[str, str]
    get_script_parameters_list(script_name) -> List[str]
    get_parameter_headers() -> List[str]
    
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

## Questions & Support

For issues or questions:
1. Check the Log sheet for error details
2. Review the console output when running scripts
3. Verify Config sheet contains your script entries
4. Check that credentials.json has proper permissions
