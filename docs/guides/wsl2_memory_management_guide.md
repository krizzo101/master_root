# WSL2 Memory Management Guide for Cursor/VS Code

## Overview

This guide provides a comprehensive solution for managing WSL2 memory consumption issues, particularly when using Cursor IDE or VS Code with multiple sessions. The solution includes monitoring tools, automatic cleanup scripts, and preventive measures.

## The Problem

WSL2 memory consumption issues manifest as:
- **Memory Leak**: WSL2 doesn't properly release cached memory back to Windows
- **Cursor/VS Code Memory Growth**: Each session spawns new server processes that persist
- **Orphaned Processes**: Old extension hosts and language servers continue consuming memory
- **Cache Accumulation**: Linux file system cache grows without bounds
- **Eventually**: System runs out of memory, swap fills up, and sessions crash

## Solution Components

### 1. Python Memory Monitor (`wsl_memory_monitor.py`)
A comprehensive monitoring and management tool that:
- Continuously monitors memory usage
- Sends alerts when thresholds are exceeded
- Performs automatic cleanup operations
- Tracks Cursor/VS Code specific processes
- Maintains logs and state

### 2. Quick Cleanup Script (`wsl_quick_cleanup.sh`)
A bash script for immediate memory relief:
- Drops Linux caches
- Compacts memory
- Kills orphaned Cursor processes
- Cleans various caches (apt, pip, npm)
- Provides before/after statistics

### 3. Windows PowerShell Manager (`WSL-Memory-Manager.ps1`)
Windows-side management tool:
- Monitors Vmmem process
- Can restart WSL2 completely
- Configures .wslconfig settings
- Provides Windows notifications
- Can be installed as scheduled task

### 4. Setup Script (`setup_wsl_memory_management.sh`)
Automated setup that:
- Installs dependencies
- Configures sudo permissions
- Sets up systemd service
- Creates cron jobs
- Adds convenient aliases

## Installation

### Prerequisites
```bash
# Install Python package
pip install --user psutil
```

### Quick Setup
```bash
# Clone or download the scripts to ~/master_root/scripts/
cd ~/master_root/scripts/

# Run the setup script
./setup_wsl_memory_management.sh

# Source aliases
source ~/.bash_aliases
```

### Manual Setup

1. **Configure sudo permissions** (required for cache dropping):
```bash
sudo visudo
# Add these lines (replace 'opsvi' with your username):
opsvi ALL=(ALL) NOPASSWD: /usr/bin/tee /proc/sys/vm/drop_caches
opsvi ALL=(ALL) NOPASSWD: /usr/bin/tee /proc/sys/vm/compact_memory
```

2. **Set up configuration**:
```bash
python3 ~/master_root/scripts/wsl_memory_monitor.py config
# Edit ~/.config/wsl_memory_monitor.json as needed
```

3. **Create aliases** (add to ~/.bashrc or ~/.bash_aliases):
```bash
alias wsl-mem-status='python3 ~/master_root/scripts/wsl_memory_monitor.py status'
alias wsl-mem-cleanup='~/master_root/scripts/wsl_quick_cleanup.sh'
alias wsl-mem-monitor='python3 ~/master_root/scripts/wsl_memory_monitor.py monitor'
```

## Usage

### Check Current Status
```bash
wsl-mem-status
# or
python3 ~/master_root/scripts/wsl_memory_monitor.py status
```

### Perform Quick Cleanup
```bash
wsl-mem-cleanup
# or
./wsl_quick_cleanup.sh
```

### Start Continuous Monitoring
```bash
# Foreground
wsl-mem-monitor

# Background/daemon
python3 ~/master_root/scripts/wsl_memory_monitor.py monitor --daemon
```

### Windows-side Management
```powershell
# In PowerShell on Windows
.\WSL-Memory-Manager.ps1 Status
.\WSL-Memory-Manager.ps1 Monitor -AutoCleanup
.\WSL-Memory-Manager.ps1 Cleanup
.\WSL-Memory-Manager.ps1 Config  # Create/update .wslconfig
```

## Configuration

### Memory Monitor Configuration
Edit `~/.config/wsl_memory_monitor.json`:

```json
{
    "thresholds": {
        "warning_percent": 70,        # Alert when memory > 70%
        "critical_percent": 85,        # Critical alert & auto-cleanup
        "swap_warning_percent": 50    # Alert when swap > 50%
    },
    "cleanup": {
        "auto_cleanup": true,          # Enable automatic cleanup
        "cleanup_threshold_percent": 80,
        "min_cleanup_interval_seconds": 300,  # Min 5 minutes between cleanups
        "drop_caches": true,
        "kill_orphaned_processes": true,
        "compact_memory": true
    },
    "cursor_specific": {
        "monitor_cursor_processes": true,
        "max_cursor_servers": 3,       # Keep only 3 most recent servers
        "max_extension_memory_mb": 1024  # Kill extensions using > 1GB
    }
}
```

### WSL2 Configuration (.wslconfig)
Create `C:\Users\<YourUsername>\.wslconfig`:

```ini
[wsl2]
memory=16GB          # Limit WSL2 to 16GB (adjust based on your system)
swap=8GB            # Swap size
pageReporting=false  # Disable page reporting to save memory
nestedVirtualization=true
localhostForwarding=true
```

## Automation

### Systemd Service (if systemd is available)
```bash
# Install service
sudo cp wsl-memory-monitor.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable wsl-memory-monitor
sudo systemctl start wsl-memory-monitor

# Check status
sudo systemctl status wsl-memory-monitor
```

### Cron Job for Periodic Cleanup
```bash
# Add to crontab
crontab -e

# Add this line for hourly cleanup
0 * * * * /home/opsvi/master_root/scripts/wsl_quick_cleanup.sh > /dev/null 2>&1
```

### Windows Scheduled Task
```powershell
# Run PowerShell as Administrator
.\WSL-Memory-Manager.ps1 Install
```

## Troubleshooting

### Issue: Cleanup doesn't free memory
**Solution**: This often happens when processes are actively using memory. Try:
```bash
# More aggressive cleanup
sudo sync
echo 3 | sudo tee /proc/sys/vm/drop_caches
echo 1 | sudo tee /proc/sys/vm/compact_memory

# If still not working, restart WSL2 from Windows
wsl.exe --shutdown
```

### Issue: Monitor script fails with permission errors
**Solution**: Ensure sudo permissions are configured correctly:
```bash
# Test permissions
echo 3 | sudo tee /proc/sys/vm/drop_caches
# Should not ask for password
```

### Issue: Cursor keeps creating new processes
**Solution**: Limit the number of Cursor windows open simultaneously. Consider:
- Using workspace features instead of multiple windows
- Closing unused terminals and panels
- Disabling unnecessary extensions

### Issue: Memory fills up quickly after cleanup
**Solution**: This indicates active memory usage. Check for:
- Large files being processed
- Memory-intensive extensions
- Background tasks or builds running
- Consider increasing WSL2 memory limit in .wslconfig

## Best Practices

### Preventive Measures
1. **Limit concurrent Cursor/VS Code sessions** to 2-3 maximum
2. **Close unused terminals** and output panels
3. **Disable unnecessary extensions**, especially memory-intensive ones
4. **Use Remote-SSH** instead of WSL extension when possible
5. **Regularly restart Cursor** (at least daily) to clear accumulated processes

### Memory Management Strategy
1. **Set appropriate limits** in .wslconfig based on your system
2. **Enable automatic monitoring** with reasonable thresholds
3. **Schedule regular cleanups** during low-activity periods
4. **Monitor trends** to identify problematic patterns
5. **Keep logs** for troubleshooting recurring issues

### Performance Optimization
1. **Disable Windows Defender** real-time scanning for WSL2 directories
2. **Use native Windows tools** when possible (git, node, etc.)
3. **Avoid large file operations** between Windows and WSL2
4. **Consider using Docker Desktop** memory limits if using containers
5. **Regularly update** WSL2, Windows, and Cursor to get latest fixes

## Monitoring and Alerts

### Log Files
- **Monitor log**: `~/.local/log/wsl_memory_monitor.log`
- **State file**: `~/.local/state/wsl_memory_state.json`

### Setting up Email Alerts
Edit the configuration file to enable email notifications:
```json
"notifications": {
    "enabled": true,
    "email_notifications": true,
    "email_config": {
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "from_email": "your-email@gmail.com",
        "to_email": "recipient@gmail.com",
        "password": "app-specific-password"
    }
}
```

### Desktop Notifications
Desktop notifications work if you have a GUI environment in WSL2 or are using Windows Terminal with notification support.

## Advanced Features

### Custom Cleanup Actions
Add custom cleanup commands to the script:
```bash
# Edit wsl_quick_cleanup.sh and add:
# Custom cleanup for your development environment
rm -rf /tmp/build-cache/*
docker system prune -f
```

### Integration with CI/CD
The monitor can be integrated with build systems to:
- Perform cleanup before large builds
- Alert when memory is insufficient
- Automatically manage resources

### API Integration
The Python monitor can be extended to:
- Send metrics to monitoring systems (Prometheus, Grafana)
- Integrate with Slack/Teams for alerts
- Provide REST API for remote monitoring

## Conclusion

This comprehensive solution addresses WSL2 memory issues through:
- **Proactive monitoring** to catch issues early
- **Automatic cleanup** to prevent crashes
- **Multiple tools** for different scenarios
- **Flexible configuration** for various workflows

Regular use of these tools should prevent memory-related crashes and improve your development experience with Cursor/VS Code in WSL2.

## Support and Updates

- Check logs regularly for patterns
- Adjust thresholds based on your workflow
- Update scripts as new WSL2 versions are released
- Consider contributing improvements back to the community

Remember: The goal is to maintain a stable development environment while maximizing available resources. Adjust the configuration to match your specific needs and hardware capabilities.