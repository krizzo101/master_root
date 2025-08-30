# Intelligent Project Backup System

## Overview
A hybrid backup solution that combines full backups with incremental diffs, smart retention policies, and automated scheduling.

## Key Features

### 1. **Hybrid Backup Strategy**
- **Weekly Full Backups**: Complete project snapshot every Sunday
- **Daily Incremental Backups**: Only changed files since last full backup
- **Hourly Snapshots** (optional): For active development periods
- **Smart Deduplication**: Content-based hashing to identify changes

### 2. **Intelligent Exclusions**
Automatically excludes:
- Virtual environments (`venv/`, `.venv/`, `env/`)
- Node modules (`node_modules/`)
- Build artifacts (`dist/`, `build/`, `target/`)
- Cache directories (`__pycache__/`, `.cache/`)
- Version control (`.git/`, `.svn/`)
- IDE files (`.vscode/`, `.idea/`)
- Large generated files (`*.log`, `*.db`)
- Temporary files and directories

### 3. **Retention Policies**
- **2 Full Backups** (14 days coverage)
- **7 Days of Incrementals** (daily changes)
- **48 Hours of Snapshots** (hourly during development)
- **3 Monthly Archives** (optional, for milestones)

### 4. **Advanced Features**
- Git integration (tracks commit/branch with each backup)
- File integrity verification (SHA-256 hashing)
- Compression (configurable gzip/bz2/xz)
- Restore to any point in time
- Backup verification and integrity checking

## Quick Start

### Initial Setup
```bash
# Make scripts executable
chmod +x scripts/backup_manager.py
chmod +x scripts/backup_automation.sh

# Run initial setup (creates first full backup)
./scripts/backup_automation.sh setup
```

### Manual Backups
```bash
# Create backup (auto-detects type needed)
python scripts/backup_manager.py /home/opsvi/master_root backup

# Force specific backup type
python scripts/backup_manager.py /home/opsvi/master_root backup --type full
python scripts/backup_manager.py /home/opsvi/master_root backup --type incremental
python scripts/backup_manager.py /home/opsvi/master_root backup --type snapshot
```

### Automated Backups

#### Option 1: Cron (Recommended for most users)
```bash
# Install cron jobs
./scripts/backup_automation.sh install-cron

# Verify installation
crontab -l
```

#### Option 2: Systemd Timers (For system-wide backups)
```bash
# Generate systemd timer files
./scripts/backup_automation.sh install-systemd

# Install with sudo (follow printed instructions)
```

### Restore Operations
```bash
# List available backups
python scripts/backup_manager.py /home/opsvi/master_root --backup-dir ./backups list

# Restore specific backup
python scripts/backup_manager.py /home/opsvi/master_root --backup-dir ./backups restore full_20250830_143000

# Restore to specific location
python scripts/backup_manager.py /home/opsvi/master_root --backup-dir ./backups restore full_20250830_143000 --to /path/to/restore
```

## Configuration

Edit `backups/master_root/backup_config.json`:

```json
{
  "exclude_patterns": [...],  // Files/dirs to exclude
  "retention": {
    "full_backups_keep": 2,           // Number of full backups to retain
    "full_backup_interval_days": 7,   // Days between full backups
    "incremental_keep_days": 7,       // Keep incrementals for N days
    "snapshot_keep_hours": 48,        // Keep snapshots for N hours
    "monthly_archives_keep": 3        // Keep N monthly archives
  },
  "compression": {
    "algorithm": "gzip",  // gzip, bz2, or xz
    "level": 6           // 1-9 (higher = better compression)
  }
}
```

## Backup Schedule

### Default Schedule
- **Full Backup**: Every Sunday at 3:00 AM
- **Incremental Backup**: Daily at 2:00 AM
- **Cleanup**: Every Monday at 4:00 AM
- **Snapshots**: Optional, hourly during work hours

### Customizing Schedule

For cron:
```bash
crontab -e
# Modify the schedule as needed
```

For systemd:
```bash
sudo systemctl edit project-backup-daily.timer
```

## Storage Optimization

### Space Requirements
- Full backup: ~50-70% of project size (after compression)
- Incremental: ~1-10% of project size (only changes)
- Total for 2-week retention: ~1.5-2x project size

### Example Storage Calculation
For a 1GB project:
- 2 full backups: ~1.4GB
- 7 daily incrementals: ~0.2GB
- 48 hourly snapshots: ~0.1GB
- **Total: ~1.7GB**

## Recovery Strategies

### Point-in-Time Recovery
```bash
# Restore to specific date
python scripts/backup_manager.py /home/opsvi/master_root --backup-dir ./backups restore incr_20250830_020000
```

### Disaster Recovery
1. Keep offsite copies of full backups
2. Sync backup directory to cloud storage:
   ```bash
   rsync -av backups/ remote-server:/backups/
   # or
   aws s3 sync backups/ s3://my-bucket/backups/
   ```

### Verification
```bash
# Verify backup integrity
python scripts/backup_manager.py /home/opsvi/master_root --backup-dir ./backups verify full_20250830_143000

# Verify all backups
for backup in $(ls backups/master_root/metadata/*.json | xargs -n1 basename | sed 's/_metadata.json//'); do
    python scripts/backup_manager.py /home/opsvi/master_root verify $backup
done
```

## Best Practices

1. **Test Restores Regularly**: Verify backups work by doing test restores monthly
2. **Monitor Backup Logs**: Check `backups/master_root/backup.log` for issues
3. **Offsite Copies**: Keep copies of full backups in cloud storage
4. **Document Changes**: Major refactors should trigger a full backup
5. **Version Control**: Use this alongside Git, not as a replacement

## Improvements Over Original Concept

### Your Concept vs Implementation

| Your Concept | Our Implementation | Benefit |
|---|---|---|
| Only incremental diffs | Hybrid full + incremental | Faster restores, better reliability |
| 2-week rolling window | Configurable retention policies | Flexible for different needs |
| Need all diffs to restore | Each incremental references base | Can restore from any point |
| Basic exclusions | Smart pattern-based exclusions | Automatically skips generated files |
| Manual process | Automated with cron/systemd | Set and forget |

### Additional Enhancements
1. **Content-based deduplication**: Only backs up files that actually changed (not just timestamp)
2. **Git integration**: Tracks code state with backups
3. **Compression options**: Balance speed vs size
4. **Verification system**: Ensure backups are valid
5. **Parallel backup chains**: Can maintain multiple backup strategies simultaneously

## Troubleshooting

### Common Issues

**Backup takes too long**:
- Add more patterns to exclude_patterns
- Reduce compression level
- Use snapshots instead of incrementals during development

**Running out of space**:
- Reduce retention periods
- Increase compression level
- Exclude more generated files

**Restore fails**:
- Verify backup integrity first
- Check base backup exists for incrementals
- Ensure sufficient space in restore location

### Monitoring
```bash
# Check backup status
./scripts/backup_automation.sh status

# View recent backup activity
tail -f backups/master_root/backup.log

# Check disk usage
du -sh backups/master_root/
```

## Advanced Usage

### Custom Exclude Patterns
Add project-specific exclusions:
```python
# In backup_config.json
"exclude_patterns": [
    "*.mp4",  # Large video files
    "datasets/",  # Large data directories
    "*.weights",  # ML model files
    "scratch/",  # Temporary work
]
```

### Multiple Backup Strategies
Run different backup strategies in parallel:
```bash
# Development snapshots
python scripts/backup_manager.py . --backup-dir ./backups/dev backup --type snapshot

# Production backups
python scripts/backup_manager.py . --backup-dir ./backups/prod backup --type full
```

### Integration with CI/CD
```yaml
# .github/workflows/backup.yml
on:
  push:
    branches: [main]
jobs:
  backup:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - run: python scripts/backup_manager.py . backup --type incremental
      - uses: actions/upload-artifact@v2
        with:
          name: backup
          path: backups/
```

## Summary

This backup system provides enterprise-grade protection for your project with minimal overhead. The hybrid approach ensures you can quickly recover from any point while maintaining reasonable storage requirements. The automation ensures backups happen consistently without manual intervention.
