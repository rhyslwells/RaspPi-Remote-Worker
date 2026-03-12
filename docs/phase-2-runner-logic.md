# Phase 2: Runner Logic

## Overview

This phase involves implementing the core `runner.py` script that will continuously poll your Google Sheet and execute scripts based on commands.

## Core Loop

The runner performs these operations in a loop:

1. **Authenticate** with Google Sheets API using `credentials.json`
2. **Read** the control Sheet for any "START" flags
3. **Execute** the corresponding script from `/scripts` folder
4. **Log** the output and results
5. **Update** the Sheet cell to "SUCCESS", "FAILED", or "IDLE"
6. **Wait** before polling again (e.g., every 30 seconds)

## Key Components

### Authentication
- Use `oauth2client` and `gspread` libraries
- Load credentials from `credentials.json`
- Create authorized connection to Google Sheets

### Polling Mechanism
- Efficient polling without overwhelming API quota
- Configurable poll interval
- Handle API rate limits and transient failures

### Script Execution
- Dynamically import and run scripts from `/scripts`
- Capture stdout and stderr
- Handle timeouts for long-running tasks
- Implement proper error handling and logging

### Logging
- Log all operations to a file (rotated to prevent disk bloat)
- Include timestamps and status information
- Output can optionally be stored in Google Sheet for visibility

## systemd Service Setup

Create a service file to run runner.py on boot and keep it running:

```ini
[Unit]
Description=Raspberry Pi Task Runner
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/path/to/repo
ExecStart=/usr/bin/python3 runner.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## Error Handling

- Implement retry logic for transient API failures
- Graceful degradation if Google Sheets is unreachable
- Clear error messages in logs and Sheet status
- Automatic recovery and resumption

## Next Steps

- Implement basic polling and execution engine
- Create test scripts to verify functionality
- Test with each of the implementation ideas
