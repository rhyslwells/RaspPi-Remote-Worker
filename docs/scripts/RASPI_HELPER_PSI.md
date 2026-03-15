
Explain this script


### raspi-helper.ps1 (Windows PowerShell)

**What it provides:**
- SSH connections
- File transfer (credentials.json, logs)
- Service management (start/stop/restart)
- Live log viewing
- Repository updates
- Connection testing
- System diagnostics

**How to use:**

**First time setup:**
```powershell
# Navigate to your project directory
cd c:\Users\YourName\Desktop\RaspPi-Remote-Worker

# Load the helper
. .\raspi-helper.ps1 -PiIP "192.168.1.100"

# Save for future sessions
Save-RaspPiConfig -IP "192.168.1.100"
```

**Future sessions (after saving config):**
```powershell
cd c:\Users\YourName\Desktop\RaspPi-Remote-Worker
. .\raspi-helper.ps1
```

**Available commands:**
```powershell
Connect-RaspPi                          # SSH into Pi
Copy-CredentialsToRaspPi                # Deploy credentials.json
Get-RaspPiLogs                          # Download logs
Get-RaspPiServiceStatus                 # Check service
Start-RaspPiService                     # Start service
Stop-RaspPiService                      # Stop service
Restart-RaspPiService                   # Restart service
Watch-RaspPiLogs                        # Live logs (Ctrl+C to exit)
Update-RaspPiRepo                       # Pull changes & restart
Test-RaspPiConnection                   # Run diagnostics
Get-RaspPiInfo                          # System info
Save-RaspPiConfig -IP "192.168.1.100"  # Save IP permanently
Show-Help                               # Show all commands
```

**Example workflow:**
```powershell
# Connect and manage
Connect-RaspPi

# In another PowerShell window:
. .\raspi-helper.ps1

# Copy credentials
Copy-CredentialsToRaspPi credentials.json

# Check status
Get-RaspPiServiceStatus

# View logs in real time
Watch-RaspPiLogs

# Update code and restart
Update-RaspPiRepo

# Run diagnostics
Test-RaspPiConnection
```

---
