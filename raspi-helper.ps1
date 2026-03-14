# RaspPi Remote Worker - Windows PowerShell Helper Script
# 
# Usage: . .\raspi-helper.ps1
# Then use the functions defined below
#
# This script provides convenient functions for managing your Raspberry Pi
# from Windows PowerShell or Windows Terminal
#
# For WSL Bash equivalent, see raspi-helper.sh

param(
    [Parameter(Mandatory=$false)]
    [string]$PiIP = $null
)

# Try to read Pi IP from a config file if it exists
$ConfigFile = "$PSScriptRoot\.raspi-config"
if (Test-Path $ConfigFile) {
    $PiIP = Get-Content $ConfigFile
    Write-Host "Loaded Pi IP from config: $PiIP" -ForegroundColor Green
}

if (-not $PiIP) {
    Write-Host "Usage: . .\raspi-helper.ps1 -PiIP '192.168.1.100'" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Or configure permanently by creating .raspi-config file with your Pi's IP" -ForegroundColor Cyan
    Write-Host "  (in the same directory as this script)"
}

# ============================================================================
# SSH CONNECTION
# ============================================================================

function Connect-RaspPi {
    <#
    .SYNOPSIS
    Connect to Raspberry Pi via SSH
    #>
    if (-not $PiIP) {
        Write-Host "Error: Pi IP not configured. Set with: . .\raspi-helper.ps1 -PiIP '192.168.1.100'" -ForegroundColor Red
        return
    }
    
    Write-Host "Connecting to Pi at $PiIP..." -ForegroundColor Green
    ssh pi@$PiIP
}

# ============================================================================
# FILE TRANSFER
# ============================================================================

function Copy-CredentialsToRaspPi {
    <#
    .SYNOPSIS
    Copy credentials.json to Raspberry Pi
    #>
    param(
        [Parameter(Mandatory=$false)]
        [string]$CredentialsPath = "credentials.json"
    )
    
    if (-not $PiIP) {
        Write-Host "Error: Pi IP not configured." -ForegroundColor Red
        return
    }
    
    if (-not (Test-Path $CredentialsPath)) {
        Write-Host "Error: Credentials file not found: $CredentialsPath" -ForegroundColor Red
        return
    }
    
    Write-Host "Copying $CredentialsPath to Pi..." -ForegroundColor Green
    scp $CredentialsPath "pi@${PiIP}:~/RaspPi-Remote-Worker/"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Success! Credentials copied." -ForegroundColor Green
        Write-Host ""
        Write-Host "Next: Verify on Pi with:" -ForegroundColor Cyan
        Write-Host "  ssh pi@$PiIP 'ls -la ~/RaspPi-Remote-Worker/credentials.json'" -ForegroundColor Cyan
    }
}

function Get-RaspPiLogs {
    <#
    .SYNOPSIS
    Download latest logs from Raspberry Pi
    #>
    param(
        [Parameter(Mandatory=$false)]
        [string]$LocalPath = "./pi-logs"
    )
    
    if (-not $PiIP) {
        Write-Host "Error: Pi IP not configured." -ForegroundColor Red
        return
    }
    
    if (-not (Test-Path $LocalPath)) {
        New-Item -ItemType Directory -Path $LocalPath | Out-Null
    }
    
    Write-Host "Downloading logs from Pi..." -ForegroundColor Green
    scp -r "pi@${PiIP}:~/RaspPi-Remote-Worker/logs/*" "$LocalPath/"
    
    Write-Host "Logs downloaded to: $LocalPath" -ForegroundColor Green
}

# ============================================================================
# SERVICE MANAGEMENT (via SSH)
# ============================================================================

function Get-RaspPiServiceStatus {
    <#
    .SYNOPSIS
    Check service status on Raspberry Pi
    #>
    if (-not $PiIP) {
        Write-Host "Error: Pi IP not configured." -ForegroundColor Red
        return
    }
    
    Write-Host "Checking service status on Pi..." -ForegroundColor Green
    ssh pi@$PiIP "sudo systemctl status remote-worker.service"
}

function Start-RaspPiService {
    <#
    .SYNOPSIS
    Start the Remote Worker service on Raspberry Pi
    #>
    if (-not $PiIP) {
        Write-Host "Error: Pi IP not configured." -ForegroundColor Red
        return
    }
    
    Write-Host "Starting Remote Worker service on Pi..." -ForegroundColor Green
    ssh pi@$PiIP "sudo systemctl start remote-worker.service"
    
    Start-Sleep -Seconds 2
    Get-RaspPiServiceStatus
}

function Stop-RaspPiService {
    <#
    .SYNOPSIS
    Stop the Remote Worker service on Raspberry Pi
    #>
    if (-not $PiIP) {
        Write-Host "Error: Pi IP not configured." -ForegroundColor Red
        return
    }
    
    Write-Host "Stopping Remote Worker service on Pi..." -ForegroundColor Green
    ssh pi@$PiIP "sudo systemctl stop remote-worker.service"
    
    Start-Sleep -Seconds 2
    Get-RaspPiServiceStatus
}

function Restart-RaspPiService {
    <#
    .SYNOPSIS
    Restart the Remote Worker service on Raspberry Pi
    #>
    if (-not $PiIP) {
        Write-Host "Error: Pi IP not configured." -ForegroundColor Red
        return
    }
    
    Write-Host "Restarting Remote Worker service on Pi..." -ForegroundColor Green
    ssh pi@$PiIP "sudo systemctl restart remote-worker.service"
    
    Start-Sleep -Seconds 2
    Get-RaspPiServiceStatus
}

function Watch-RaspPiLogs {
    <#
    .SYNOPSIS
    Watch live service logs on Raspberry Pi (press Ctrl+C to exit)
    #>
    if (-not $PiIP) {
        Write-Host "Error: Pi IP not configured." -ForegroundColor Red
        return
    }
    
    Write-Host "Connecting to live logs (Ctrl+C to exit)..." -ForegroundColor Green
    ssh pi@$PiIP "sudo journalctl -u remote-worker.service -f"
}

# ============================================================================
# REPOSITORY UPDATES
# ============================================================================

function Update-RaspPiRepo {
    <#
    .SYNOPSIS
    Pull latest code and restart service on Raspberry Pi
    #>
    if (-not $PiIP) {
        Write-Host "Error: Pi IP not configured." -ForegroundColor Red
        return
    }
    
    Write-Host "Updating repository on Pi..." -ForegroundColor Green
    ssh pi@$PiIP @'
        cd ~/RaspPi-Remote-Worker && \
        git pull origin main && \
        source .venv/bin/activate && \
        uv sync && \
        sudo systemctl restart remote-worker.service
'@
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Update complete! Service restarted." -ForegroundColor Green
    } else {
        Write-Host "Update failed. Check logs with: Watch-RaspPiLogs" -ForegroundColor Red
    }
}

# ============================================================================
# DIAGNOSTICS
# ============================================================================

function Test-RaspPiConnection {
    <#
    .SYNOPSIS
    Test connectivity to Raspberry Pi
    #>
    if (-not $PiIP) {
        Write-Host "Error: Pi IP not configured." -ForegroundColor Red
        return
    }
    
    Write-Host "Testing connection to Pi at $PiIP..." -ForegroundColor Green
    
    # Ping
    Write-Host ""
    Write-Host "1. Testing network ping..." -ForegroundColor Cyan
    if (Test-Connection -ComputerName $PiIP -Count 1 -Quiet) {
        Write-Host "   ✓ Network ping successful" -ForegroundColor Green
    } else {
        Write-Host "   ✗ Network ping failed" -ForegroundColor Red
        return
    }
    
    # SSH connection
    Write-Host ""
    Write-Host "2. Testing SSH connection..." -ForegroundColor Cyan
    ssh pi@$PiIP "echo OK" 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✓ SSH connection successful" -ForegroundColor Green
    } else {
        Write-Host "   ✗ SSH connection failed" -ForegroundColor Red
        return
    }
    
    # Repository
    Write-Host ""
    Write-Host "3. Checking repository..." -ForegroundColor Cyan
    ssh pi@$PiIP "test -d ~/RaspPi-Remote-Worker && echo OK" 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✓ Repository found" -ForegroundColor Green
    } else {
        Write-Host "   ✗ Repository not found" -ForegroundColor Red
        return
    }
    
    # Credentials
    Write-Host ""
    Write-Host "4. Checking credentials.json..." -ForegroundColor Cyan
    ssh pi@$PiIP "test -f ~/RaspPi-Remote-Worker/credentials.json && echo OK" 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✓ Credentials found" -ForegroundColor Green
    } else {
        Write-Host "   ✗ Credentials not found (copy with: Copy-CredentialsToRaspPi)" -ForegroundColor Red
    }
    
    # Service
    Write-Host ""
    Write-Host "5. Checking service status..." -ForegroundColor Cyan
    ssh pi@$PiIP "sudo systemctl is-active remote-worker.service" 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✓ Service is running" -ForegroundColor Green
    } else {
        Write-Host "   ✗ Service is not running" -ForegroundColor Yellow
        Write-Host "      Start with: Start-RaspPiService" -ForegroundColor Cyan
    }
    
    Write-Host ""
    Write-Host "✓ All tests passed!" -ForegroundColor Green
}

function Get-RaspPiInfo {
    <#
    .SYNOPSIS
    Get system information from Raspberry Pi
    #>
    if (-not $PiIP) {
        Write-Host "Error: Pi IP not configured." -ForegroundColor Red
        return
    }
    
    Write-Host "Getting system info from Pi..." -ForegroundColor Green
    Write-Host ""
    
    ssh pi@$PiIP @'
        echo "=== SYSTEM INFO ==="
        uname -a
        echo ""
        echo "=== PYTHON INFO ==="
        python3 --version
        echo ""
        echo "=== DISK USAGE ==="
        df -h | head -4
        echo ""
        echo "=== MEMORY USAGE ==="
        free -h | head -2
        echo ""
        echo "=== IPv4 ADDRESS ==="
        hostname -I
        echo ""
        echo "=== SERVICE STATUS ==="
        sudo systemctl status remote-worker.service --no-pager | head -10
'@
}

# ============================================================================
# SETUP HELPERS
# ============================================================================

function Save-RaspPiConfig {
    <#
    .SYNOPSIS
    Save Pi IP address to config file for future sessions
    #>
    param(
        [Parameter(Mandatory=$true)]
        [string]$IP
    )
    
    $ConfigFile = "$PSScriptRoot\.raspi-config"
    Set-Content -Path $ConfigFile -Value $IP
    Write-Host "Saved Pi IP to $ConfigFile" -ForegroundColor Green
    Write-Host "Run this script again with: . .\raspi-helper.ps1" -ForegroundColor Green
}

function Show-Help {
    <#
    .SYNOPSIS
    Show available commands
    #>
    Write-Host "RaspPi Remote Worker - PowerShell Helper Script" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Available functions:" -ForegroundColor Green
    Write-Host ""
    Write-Host "CONNECTION:" -ForegroundColor Yellow
    Write-Host "  Connect-RaspPi                    - SSH into the Pi" -ForegroundColor White
    Write-Host ""
    Write-Host "FILE TRANSFER:" -ForegroundColor Yellow
    Write-Host "  Copy-CredentialsToRaspPi          - Deploy credentials.json" -ForegroundColor White
    Write-Host "  Get-RaspPiLogs                    - Download logs from Pi" -ForegroundColor White
    Write-Host ""
    Write-Host "SERVICE MANAGEMENT:" -ForegroundColor Yellow
    Write-Host "  Get-RaspPiServiceStatus           - Check service status" -ForegroundColor White
    Write-Host "  Start-RaspPiService               - Start the service" -ForegroundColor White
    Write-Host "  Stop-RaspPiService                - Stop the service" -ForegroundColor White
    Write-Host "  Restart-RaspPiService             - Restart the service" -ForegroundColor White
    Write-Host "  Watch-RaspPiLogs                  - View live logs (Ctrl+C to exit)" -ForegroundColor White
    Write-Host ""
    Write-Host "REPOSITORY:" -ForegroundColor Yellow
    Write-Host "  Update-RaspPiRepo                 - Pull and restart" -ForegroundColor White
    Write-Host ""
    Write-Host "DIAGNOSTICS:" -ForegroundColor Yellow
    Write-Host "  Test-RaspPiConnection             - Run connection tests" -ForegroundColor White
    Write-Host "  Get-RaspPiInfo                    - Show system info" -ForegroundColor White
    Write-Host ""
    Write-Host "CONFIGURATION:" -ForegroundColor Yellow
    Write-Host "  Save-RaspPiConfig -IP '192.168.1.100'  - Save Pi IP for future sessions" -ForegroundColor White
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Cyan
    Write-Host "  Connect-RaspPi" -ForegroundColor White
    Write-Host "  Copy-CredentialsToRaspPi" -ForegroundColor White
    Write-Host "  Get-RaspPiServiceStatus" -ForegroundColor White
    Write-Host "  Watch-RaspPiLogs" -ForegroundColor White
    Write-Host "  Save-RaspPiConfig -IP '192.168.1.100'" -ForegroundColor White
    Write-Host ""
}

# Auto-show help if no Pi IP configured
if (-not $PiIP) {
    Show-Help
} else {
    Write-Host "Pi IP: $PiIP" -ForegroundColor Green
    Write-Host "Type 'Show-Help' for available commands" -ForegroundColor Green
}
