# Agent-Orchestrator Cleanup Script

## Overview
Safe cleanup utility for maintaining the agent-orchestrator directory. Creates backups, archives old outputs, and removes obsolete files.

## Usage

### Preview Changes (Recommended First Step)
```bash
python cleanup.py --dry-run
```

### Basic Cleanup
```bash
python cleanup.py
```

### Advanced Options
```bash
# Skip backup creation (not recommended)
python cleanup.py --skip-backup

# Archive outputs older than 14 days (default is 7)
python cleanup.py --archive-days 14

# Also reorganize files into appropriate directories
python cleanup.py --reorganize

# Skip confirmation prompts
python cleanup.py --force

# Clean a different directory
python cleanup.py --base-dir /path/to/agent-orchestrator
```

## What It Does

### 1. Creates Backup
- Creates tar.gz archive of current state
- Stored in `backups/` directory
- Named with timestamp for easy identification

### 2. Deletes Old Logs
- Removes orchestrator log files from previous runs
- Removes temporary mcp-shell.log files
- Frees up disk space

### 3. Removes Temporary Files
- Deletes test reports
- Removes broken/original file backups
- Cleans up temporary markdown files

### 4. Archives Old Outputs
- Compresses workflow outputs older than X days
- Moves to `output/archive/` directory
- Preserves data while saving space

### 5. Reorganizes Files (Optional)
- Moves demo files to `demos/`
- Moves task definitions to `task_definitions/`
- Moves run scripts to `scripts/`
- Helps maintain organized structure

## Safety Features

### Backup System
- Automatic backup before any deletions
- Timestamped archives for rollback capability
- Can be skipped with `--skip-backup` (not recommended)

### Dry Run Mode
- Preview all changes without making them
- Shows exactly what will be deleted/moved
- Always recommended as first step

### Confirmation Prompts
- Requires explicit confirmation before changes
- Can be bypassed with `--force` flag
- Shows summary of planned actions

### Detailed Logging
- All actions logged to `cleanup.log`
- Console output shows progress
- JSON report generated after completion

## Files Affected

### Deleted Files
- Old orchestrator logs (orchestrator_*.log)
- Temporary files (temp_*.md, test_report.html)
- Broken/original file backups (*.broken.json, *.original)

### Archived (After 7 Days)
- Workflow output directories in `output/`
- Compressed to tar.gz format
- Moved to `output/archive/`

### Preserved Files
- Core application files (*.py in root)
- Source code (`src/` directory)
- Documentation (`docs/` directory)
- Configuration files (.env, requirements.txt, etc.)
- Recent workflow outputs

## Rollback Procedure

If you need to restore after cleanup:

1. Locate backup in `backups/` directory
2. Extract backup to temporary location:
   ```bash
   tar -xzf backups/agent_orchestrator_backup_TIMESTAMP.tar.gz -C /tmp/restore
   ```
3. Review and selectively restore needed files
4. Or fully restore:
   ```bash
   tar -xzf backups/agent_orchestrator_backup_TIMESTAMP.tar.gz
   ```

## Cleanup Report

After each run, a JSON report is generated:
- `cleanup_report_TIMESTAMP.json`
- Contains all actions taken
- Shows space freed
- Lists affected files

## Recommendations

1. **Always run with `--dry-run` first** to preview changes
2. **Keep backups** for at least 7 days before deleting
3. **Review the cleanup report** after each run
4. **Schedule regular cleanups** (weekly recommended)
5. **Monitor `output/` directory** size over time

## Troubleshooting

### Permission Errors
- Ensure you have write permissions in the directory
- Run with appropriate user privileges

### Large Backups
- Consider archiving old backups to external storage
- Implement rotation policy for backup files

### Script Fails
- Check `cleanup.log` for detailed error messages
- Ensure Python 3.6+ is installed
- Verify all required modules are available

## Future Enhancements

Planned improvements:
- Automatic scheduling via cron
- Configurable retention policies
- Remote backup support
- Size-based cleanup triggers
- Integration with monitoring systems
