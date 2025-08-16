# WSL2 Memory Manager for Windows
# Run this script in PowerShell on Windows to manage WSL2 memory

param(
    [Parameter(Position=0)]
    [ValidateSet("Status", "Monitor", "Cleanup", "Restart", "Config", "Install")]
    [string]$Action = "Status",
    
    [int]$WarningThreshold = 70,
    [int]$CriticalThreshold = 85,
    [int]$MonitorInterval = 60,
    [switch]$AutoCleanup
)

# Check if running as Administrator
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# Get WSL2 memory usage
function Get-WSLMemoryUsage {
    $vmmem = Get-Process -Name "vmmem" -ErrorAction SilentlyContinue
    if ($vmmem) {
        $memoryGB = [math]::Round($vmmem.WorkingSet64 / 1GB, 2)
        $totalMemory = (Get-WmiObject Win32_ComputerSystem).TotalPhysicalMemory / 1GB
        $percentUsed = [math]::Round(($memoryGB / $totalMemory) * 100, 1)
        
        return @{
            ProcessId = $vmmem.Id
            MemoryGB = $memoryGB
            TotalSystemGB = [math]::Round($totalMemory, 2)
            PercentUsed = $percentUsed
            Status = if ($percentUsed -ge $CriticalThreshold) { "Critical" } 
                    elseif ($percentUsed -ge $WarningThreshold) { "Warning" } 
                    else { "Normal" }
        }
    } else {
        return @{
            ProcessId = 0
            MemoryGB = 0
            TotalSystemGB = [math]::Round((Get-WmiObject Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 2)
            PercentUsed = 0
            Status = "WSL2 Not Running"
        }
    }
}

# Display memory status
function Show-WSLStatus {
    Clear-Host
    Write-Host "================================" -ForegroundColor Cyan
    Write-Host "    WSL2 Memory Status" -ForegroundColor Cyan
    Write-Host "================================" -ForegroundColor Cyan
    
    $usage = Get-WSLMemoryUsage
    
    $statusColor = switch ($usage.Status) {
        "Critical" { "Red" }
        "Warning" { "Yellow" }
        "Normal" { "Green" }
        default { "Gray" }
    }
    
    Write-Host "`nMemory Usage:" -ForegroundColor White
    Write-Host "  WSL2 Memory: $($usage.MemoryGB) GB / $($usage.TotalSystemGB) GB" -ForegroundColor $statusColor
    Write-Host "  Percentage:  $($usage.PercentUsed)%" -ForegroundColor $statusColor
    Write-Host "  Status:      $($usage.Status)" -ForegroundColor $statusColor
    
    if ($usage.ProcessId -gt 0) {
        Write-Host "  Process ID:  $($usage.ProcessId)" -ForegroundColor Gray
    }
    
    # Get WSL distributions
    Write-Host "`nWSL Distributions:" -ForegroundColor White
    $distros = wsl.exe --list --verbose 2>$null | Select-Object -Skip 1 | Where-Object { $_ -match '\S' }
    if ($distros) {
        $distros | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
    } else {
        Write-Host "  No distributions found" -ForegroundColor Gray
    }
    
    # Show Cursor/VS Code processes if any
    $cursorProcesses = Get-Process -Name "Cursor", "Code" -ErrorAction SilentlyContinue
    if ($cursorProcesses) {
        Write-Host "`nCursor/VS Code Processes:" -ForegroundColor White
        $cursorProcesses | ForEach-Object {
            $memMB = [math]::Round($_.WorkingSet64 / 1MB, 0)
            Write-Host "  $($_.Name) (PID: $($_.Id)): $memMB MB" -ForegroundColor Gray
        }
    }
    
    Write-Host "`n================================" -ForegroundColor Cyan
}

# Monitor memory continuously
function Start-WSLMonitor {
    Write-Host "Starting WSL2 Memory Monitor..." -ForegroundColor Green
    Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
    Write-Host ""
    
    $lastCleanup = Get-Date
    $cleanupInterval = New-TimeSpan -Minutes 5
    
    while ($true) {
        $usage = Get-WSLMemoryUsage
        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        
        $statusColor = switch ($usage.Status) {
            "Critical" { "Red" }
            "Warning" { "Yellow" }
            "Normal" { "Green" }
            default { "Gray" }
        }
        
        Write-Host "[$timestamp] Memory: $($usage.MemoryGB)GB ($($usage.PercentUsed)%) - $($usage.Status)" -ForegroundColor $statusColor
        
        # Auto cleanup if enabled and threshold exceeded
        if ($AutoCleanup -and $usage.Status -eq "Critical") {
            $timeSinceLastCleanup = (Get-Date) - $lastCleanup
            if ($timeSinceLastCleanup -ge $cleanupInterval) {
                Write-Host "  Triggering automatic cleanup..." -ForegroundColor Yellow
                Invoke-WSLCleanup
                $lastCleanup = Get-Date
            }
        }
        
        # Send notification if critical
        if ($usage.Status -eq "Critical") {
            Send-WSLNotification -Title "WSL2 Memory Critical" -Message "Memory usage is at $($usage.PercentUsed)%"
        }
        
        Start-Sleep -Seconds $MonitorInterval
    }
}

# Perform memory cleanup
function Invoke-WSLCleanup {
    Write-Host "`nPerforming WSL2 memory cleanup..." -ForegroundColor Yellow
    
    # Get memory before
    $before = Get-WSLMemoryUsage
    Write-Host "Before cleanup: $($before.MemoryGB) GB ($($before.PercentUsed)%)" -ForegroundColor Gray
    
    # Run cleanup command in WSL
    Write-Host "Running cleanup in WSL..." -ForegroundColor Yellow
    wsl.exe -e bash -c "echo 3 | sudo tee /proc/sys/vm/drop_caches > /dev/null 2>&1; echo 1 | sudo tee /proc/sys/vm/compact_memory > /dev/null 2>&1"
    
    # Wait for cleanup to take effect
    Start-Sleep -Seconds 3
    
    # Get memory after
    $after = Get-WSLMemoryUsage
    $freed = [math]::Round($before.MemoryGB - $after.MemoryGB, 2)
    
    if ($freed -gt 0) {
        Write-Host "After cleanup: $($after.MemoryGB) GB ($($after.PercentUsed)%)" -ForegroundColor Green
        Write-Host "Freed: $freed GB" -ForegroundColor Green
    } else {
        Write-Host "No significant memory freed" -ForegroundColor Yellow
    }
}

# Restart WSL2
function Restart-WSL {
    Write-Host "Restarting WSL2..." -ForegroundColor Yellow
    Write-Host "This will terminate all WSL instances and running processes!" -ForegroundColor Red
    Write-Host "Continue? (Y/N): " -NoNewline
    $response = Read-Host
    
    if ($response -eq 'Y' -or $response -eq 'y') {
        Write-Host "Shutting down WSL2..." -ForegroundColor Yellow
        wsl.exe --shutdown
        
        Start-Sleep -Seconds 2
        
        Write-Host "WSL2 has been shut down. It will restart automatically when needed." -ForegroundColor Green
        
        # Optionally restart default distribution
        Write-Host "Start default WSL distribution? (Y/N): " -NoNewline
        $response = Read-Host
        if ($response -eq 'Y' -or $response -eq 'y') {
            Write-Host "Starting WSL..." -ForegroundColor Yellow
            wsl.exe echo "WSL Started"
        }
    } else {
        Write-Host "Restart cancelled" -ForegroundColor Yellow
    }
}

# Send Windows notification
function Send-WSLNotification {
    param(
        [string]$Title,
        [string]$Message
    )
    
    Add-Type -AssemblyName System.Windows.Forms
    $notification = New-Object System.Windows.Forms.NotifyIcon
    $notification.Icon = [System.Drawing.SystemIcons]::Warning
    $notification.BalloonTipTitle = $Title
    $notification.BalloonTipText = $Message
    $notification.Visible = $true
    $notification.ShowBalloonTip(5000)
    Start-Sleep -Seconds 5
    $notification.Dispose()
}

# Create or update .wslconfig
function Set-WSLConfig {
    $wslConfigPath = "$env:USERPROFILE\.wslconfig"
    
    Write-Host "WSL2 Configuration Setup" -ForegroundColor Cyan
    Write-Host "========================" -ForegroundColor Cyan
    
    # Get current system memory
    $totalMemoryGB = [math]::Round((Get-WmiObject Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 0)
    $recommendedMemory = [math]::Min([math]::Round($totalMemoryGB * 0.5, 0), 16)
    
    Write-Host "`nSystem Memory: $totalMemoryGB GB" -ForegroundColor White
    Write-Host "Recommended WSL2 Memory: $recommendedMemory GB" -ForegroundColor Green
    
    Write-Host "`nEnter WSL2 memory limit in GB (or press Enter for recommended): " -NoNewline
    $memoryInput = Read-Host
    $memory = if ($memoryInput) { $memoryInput } else { $recommendedMemory }
    
    Write-Host "Enter WSL2 swap size in GB (default 4): " -NoNewline
    $swapInput = Read-Host
    $swap = if ($swapInput) { $swapInput } else { 4 }
    
    $config = @"
[wsl2]
# Memory limit for WSL2
memory=${memory}GB

# Swap size
swap=${swap}GB

# Number of processors (leave commented to use all)
# processors=4

# Disable page reporting to save memory
pageReporting=false

# Disable idle memory trimming
# idleThreshold=1

# Compact memory automatically
# compactMemory=true

# Nested virtualization (for Docker)
nestedVirtualization=true

# Localhost forwarding
localhostForwarding=true
"@

    # Backup existing config if it exists
    if (Test-Path $wslConfigPath) {
        $backupPath = "$wslConfigPath.backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
        Copy-Item $wslConfigPath $backupPath
        Write-Host "`nBacked up existing config to: $backupPath" -ForegroundColor Yellow
    }
    
    # Write new config
    Set-Content -Path $wslConfigPath -Value $config -Encoding UTF8
    Write-Host "`nConfiguration saved to: $wslConfigPath" -ForegroundColor Green
    
    Write-Host "`nConfiguration:" -ForegroundColor White
    Write-Host $config -ForegroundColor Gray
    
    Write-Host "`n⚠️  WSL2 must be restarted for changes to take effect." -ForegroundColor Yellow
    Write-Host "Restart WSL2 now? (Y/N): " -NoNewline
    $response = Read-Host
    if ($response -eq 'Y' -or $response -eq 'y') {
        wsl.exe --shutdown
        Write-Host "WSL2 has been shut down. Changes will take effect on next start." -ForegroundColor Green
    }
}

# Install scheduled task for monitoring
function Install-WSLMonitor {
    if (!(Test-Administrator)) {
        Write-Host "This action requires Administrator privileges." -ForegroundColor Red
        Write-Host "Please run PowerShell as Administrator and try again." -ForegroundColor Yellow
        return
    }
    
    Write-Host "Installing WSL Memory Monitor as scheduled task..." -ForegroundColor Yellow
    
    $taskName = "WSL2MemoryMonitor"
    $scriptPath = $MyInvocation.MyCommand.Path
    
    # Create the scheduled task action
    $action = New-ScheduledTaskAction -Execute "PowerShell.exe" `
        -Argument "-WindowStyle Hidden -ExecutionPolicy Bypass -File `"$scriptPath`" Monitor -AutoCleanup"
    
    # Create the trigger (at system startup)
    $trigger = New-ScheduledTaskTrigger -AtStartup
    
    # Create the principal (run with highest privileges)
    $principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" `
        -LogonType Interactive -RunLevel Highest
    
    # Create the settings
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries -StartWhenAvailable
    
    # Register the task
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger `
        -Principal $principal -Settings $settings -Force
    
    Write-Host "Scheduled task installed successfully!" -ForegroundColor Green
    Write-Host "The monitor will start automatically at system startup." -ForegroundColor Gray
}

# Main execution
switch ($Action) {
    "Status" {
        Show-WSLStatus
    }
    "Monitor" {
        Start-WSLMonitor
    }
    "Cleanup" {
        Invoke-WSLCleanup
    }
    "Restart" {
        Restart-WSL
    }
    "Config" {
        Set-WSLConfig
    }
    "Install" {
        Install-WSLMonitor
    }
}

# Add helper text if no action specified
if ($Action -eq "Status") {
    Write-Host "`nAvailable actions:" -ForegroundColor White
    Write-Host "  .\WSL-Memory-Manager.ps1 Status   - Show current status (default)" -ForegroundColor Gray
    Write-Host "  .\WSL-Memory-Manager.ps1 Monitor  - Start continuous monitoring" -ForegroundColor Gray
    Write-Host "  .\WSL-Memory-Manager.ps1 Cleanup  - Perform memory cleanup" -ForegroundColor Gray
    Write-Host "  .\WSL-Memory-Manager.ps1 Restart  - Restart WSL2" -ForegroundColor Gray
    Write-Host "  .\WSL-Memory-Manager.ps1 Config   - Configure WSL2 memory limits" -ForegroundColor Gray
    Write-Host "  .\WSL-Memory-Manager.ps1 Install  - Install as scheduled task" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Options:" -ForegroundColor White
    Write-Host "  -AutoCleanup           - Enable automatic cleanup during monitoring" -ForegroundColor Gray
    Write-Host "  -WarningThreshold N    - Set warning threshold (default: 70%)" -ForegroundColor Gray
    Write-Host "  -CriticalThreshold N   - Set critical threshold (default: 85%)" -ForegroundColor Gray
    Write-Host "  -MonitorInterval N     - Set monitor interval in seconds (default: 60)" -ForegroundColor Gray
}