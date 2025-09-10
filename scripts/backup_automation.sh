#!/bin/bash
# Backup automation script with systemd/cron integration

PROJECT_PATH="/home/opsvi/master_root"
BACKUP_DIR="/home/opsvi/backups/master_root"
SCRIPT_PATH="/home/opsvi/master_root/scripts/backup_manager.py"

# Setup function for first-time configuration
setup_backup_system() {
    echo "Setting up backup system..."

    # Create backup directory
    mkdir -p "$BACKUP_DIR"

    # Make scripts executable
    chmod +x "$SCRIPT_PATH"
    chmod +x "$0"

    # Create initial full backup
    python3 "$SCRIPT_PATH" "$PROJECT_PATH" --backup-dir "$BACKUP_DIR" backup --type full

    echo "Backup system setup complete!"
}

# Install systemd timers (requires sudo)
install_systemd_timers() {
    echo "Installing systemd timers..."

    # Create service file for backups
    cat > /tmp/project-backup.service << EOF
[Unit]
Description=Project Backup Service
After=network.target

[Service]
Type=oneshot
User=$USER
ExecStart=/usr/bin/python3 $SCRIPT_PATH $PROJECT_PATH --backup-dir $BACKUP_DIR backup --type auto
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

    # Create timer for daily incremental backups
    cat > /tmp/project-backup-daily.timer << EOF
[Unit]
Description=Daily Project Incremental Backup
Requires=project-backup.service

[Timer]
OnCalendar=daily
OnCalendar=*-*-* 02:00:00
Persistent=true

[Install]
WantedBy=timers.target
EOF

    # Create timer for weekly full backups
    cat > /tmp/project-backup-weekly.timer << EOF
[Unit]
Description=Weekly Project Full Backup
Requires=project-backup.service

[Timer]
OnCalendar=weekly
OnCalendar=Sun *-*-* 03:00:00
Persistent=true

[Install]
WantedBy=timers.target
EOF

    # Create timer for hourly snapshots (optional, disabled by default)
    cat > /tmp/project-backup-snapshot.timer << EOF
[Unit]
Description=Hourly Project Snapshot
Requires=project-backup.service

[Timer]
OnCalendar=hourly
Persistent=false

[Install]
WantedBy=timers.target
EOF

    echo "Systemd timer files created in /tmp/"
    echo "To install, run:"
    echo "  sudo cp /tmp/project-backup.service /etc/systemd/system/"
    echo "  sudo cp /tmp/project-backup-*.timer /etc/systemd/system/"
    echo "  sudo systemctl daemon-reload"
    echo "  sudo systemctl enable project-backup-daily.timer"
    echo "  sudo systemctl enable project-backup-weekly.timer"
    echo "  sudo systemctl start project-backup-daily.timer"
    echo "  sudo systemctl start project-backup-weekly.timer"
}

# Install cron jobs (alternative to systemd)
install_cron_jobs() {
    echo "Installing cron jobs..."

    # Create cron entries
    CRON_ENTRIES=$(cat << EOF
# Project Backup Schedule
# Daily incremental backup at 2 AM
0 2 * * * /usr/bin/python3 $SCRIPT_PATH $PROJECT_PATH --backup-dir $BACKUP_DIR backup --type incremental >> $BACKUP_DIR/cron.log 2>&1

# Weekly full backup on Sunday at 3 AM
0 3 * * 0 /usr/bin/python3 $SCRIPT_PATH $PROJECT_PATH --backup-dir $BACKUP_DIR backup --type full >> $BACKUP_DIR/cron.log 2>&1

# Hourly snapshot during work hours (9 AM - 6 PM on weekdays) - Optional, commented out by default
# 0 9-18 * * 1-5 /usr/bin/python3 $SCRIPT_PATH $PROJECT_PATH --backup-dir $BACKUP_DIR backup --type snapshot >> $BACKUP_DIR/cron.log 2>&1

# Cleanup old backups every Monday at 4 AM
0 4 * * 1 /usr/bin/python3 $SCRIPT_PATH $PROJECT_PATH --backup-dir $BACKUP_DIR clean >> $BACKUP_DIR/cron.log 2>&1
EOF
)

    # Add to crontab
    (crontab -l 2>/dev/null; echo "$CRON_ENTRIES") | crontab -

    echo "Cron jobs installed successfully!"
    echo "View with: crontab -l"
    echo "Edit with: crontab -e"
}

# Quick backup function
quick_backup() {
    python3 "$SCRIPT_PATH" "$PROJECT_PATH" --backup-dir "$BACKUP_DIR" backup --type "${1:-auto}"
}

# Status function
backup_status() {
    echo "=== Backup System Status ==="
    echo
    echo "Project Path: $PROJECT_PATH"
    echo "Backup Directory: $BACKUP_DIR"
    echo

    if [ -d "$BACKUP_DIR" ]; then
        echo "Backup Statistics:"
        echo -n "  Full backups: "
        find "$BACKUP_DIR/full" -name "*.tar.gz" 2>/dev/null | wc -l
        echo -n "  Incremental backups: "
        find "$BACKUP_DIR/incremental" -name "*.tar.gz" 2>/dev/null | wc -l
        echo -n "  Snapshots: "
        find "$BACKUP_DIR/snapshots" -name "*.tar.gz" 2>/dev/null | wc -l
        echo
        echo "  Total backup size: $(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1)"
        echo
        echo "Latest backups:"
        python3 "$SCRIPT_PATH" "$PROJECT_PATH" --backup-dir "$BACKUP_DIR" list | head -5
    else
        echo "Backup directory not found. Run './backup_automation.sh setup' first."
    fi

    echo
    echo "Cron jobs:"
    crontab -l 2>/dev/null | grep -E "(backup|$SCRIPT_PATH)" || echo "  No cron jobs found"

    echo
    echo "Systemd timers:"
    systemctl list-timers --all 2>/dev/null | grep -E "project-backup" || echo "  No systemd timers found"
}

# Main menu
case "${1:-}" in
    setup)
        setup_backup_system
        ;;
    install-systemd)
        install_systemd_timers
        ;;
    install-cron)
        install_cron_jobs
        ;;
    backup)
        quick_backup "${2:-auto}"
        ;;
    status)
        backup_status
        ;;
    *)
        echo "Project Backup Automation"
        echo "Usage: $0 {setup|install-systemd|install-cron|backup [type]|status}"
        echo
        echo "Commands:"
        echo "  setup           - Initial setup and first full backup"
        echo "  install-systemd - Create systemd timer files (requires sudo to install)"
        echo "  install-cron    - Install cron jobs for automated backups"
        echo "  backup [type]   - Run backup now (type: auto|full|incremental|snapshot)"
        echo "  status          - Show backup system status"
        echo
        echo "Examples:"
        echo "  $0 setup                    # First time setup"
        echo "  $0 install-cron             # Setup automatic backups with cron"
        echo "  $0 backup full              # Create full backup now"
        echo "  $0 backup incremental       # Create incremental backup now"
        echo "  $0 status                   # Check backup status"
        ;;
esac
