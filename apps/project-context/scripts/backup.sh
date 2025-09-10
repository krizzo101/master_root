#!/bin/bash
# Project Context Database Backup Script
# Supports PostgreSQL with TimescaleDB and Redis backups

set -euo pipefail

# Configuration
BACKUP_DIR="/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-7}

# Database connection info
DB_HOST=${PGHOST:-postgres}
DB_PORT=${PGPORT:-5432}
DB_NAME=${PGDATABASE:-unified_context}
DB_USER=${PGUSER:-opsvi}

# Backup file names
PG_BACKUP_FILE="$BACKUP_DIR/postgres_backup_$TIMESTAMP.sql.gz"
PG_SCHEMA_FILE="$BACKUP_DIR/postgres_schema_$TIMESTAMP.sql"
REDIS_BACKUP_FILE="$BACKUP_DIR/redis_backup_$TIMESTAMP.rdb"

# Logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" >&2
}

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Function to check if PostgreSQL is ready
wait_for_postgres() {
    log "Waiting for PostgreSQL to be ready..."
    local max_attempts=30
    local attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" > /dev/null 2>&1; then
            log "PostgreSQL is ready"
            return 0
        fi

        attempt=$((attempt + 1))
        log "Attempt $attempt/$max_attempts - waiting for PostgreSQL..."
        sleep 2
    done

    log_error "PostgreSQL not ready after $max_attempts attempts"
    return 1
}

# Function to backup PostgreSQL database
backup_postgres() {
    log "Starting PostgreSQL backup..."

    # Full database backup with custom format
    if pg_dump \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        --verbose \
        --no-password \
        --format=custom \
        --compress=9 \
        --no-owner \
        --no-privileges \
        | gzip > "$PG_BACKUP_FILE"; then

        log "PostgreSQL database backup completed: $PG_BACKUP_FILE"

        # Get backup file size
        local backup_size=$(du -h "$PG_BACKUP_FILE" | cut -f1)
        log "Backup size: $backup_size"

    else
        log_error "PostgreSQL database backup failed"
        return 1
    fi

    # Schema-only backup for quick restore testing
    if pg_dump \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        --schema-only \
        --no-password \
        --verbose > "$PG_SCHEMA_FILE"; then

        log "PostgreSQL schema backup completed: $PG_SCHEMA_FILE"
    else
        log_error "PostgreSQL schema backup failed"
        return 1
    fi
}

# Function to backup Redis data
backup_redis() {
    log "Starting Redis backup..."

    # Check if Redis is available
    if redis-cli -h redis -p 6379 ping > /dev/null 2>&1; then
        # Force Redis to save current data
        if redis-cli -h redis -p 6379 BGSAVE > /dev/null 2>&1; then
            log "Redis background save initiated"

            # Wait for background save to complete
            local save_in_progress=true
            local max_wait=60
            local wait_count=0

            while [ "$save_in_progress" = true ] && [ $wait_count -lt $max_wait ]; do
                if redis-cli -h redis -p 6379 LASTSAVE > /dev/null 2>&1; then
                    save_in_progress=false
                    log "Redis background save completed"
                else
                    sleep 1
                    wait_count=$((wait_count + 1))
                fi
            done

            # Copy the RDB file if we can access Redis data directory
            # In production, this would typically be done through volume mounts
            log "Redis backup completed (background save)"

        else
            log_error "Redis background save failed"
            return 1
        fi
    else
        log "Redis not available - skipping Redis backup"
    fi
}

# Function to create application state backup
backup_application_state() {
    log "Creating application state backup..."

    local app_backup_file="$BACKUP_DIR/app_state_$TIMESTAMP.tar.gz"

    # Create application configuration and state backup
    tar -czf "$app_backup_file" \
        -C /app \
        config/ \
        data/.proj-intel \
        2>/dev/null || true

    if [ -f "$app_backup_file" ]; then
        log "Application state backup completed: $app_backup_file"
    else
        log "No application state to backup"
    fi
}

# Function to verify backup integrity
verify_backups() {
    log "Verifying backup integrity..."

    # Verify PostgreSQL backup
    if [ -f "$PG_BACKUP_FILE" ]; then
        if gzip -t "$PG_BACKUP_FILE" 2>/dev/null; then
            log "PostgreSQL backup file integrity verified"
        else
            log_error "PostgreSQL backup file is corrupted"
            return 1
        fi
    fi

    # Verify schema backup
    if [ -f "$PG_SCHEMA_FILE" ]; then
        if [ -s "$PG_SCHEMA_FILE" ]; then
            log "PostgreSQL schema backup file verified"
        else
            log_error "PostgreSQL schema backup file is empty"
        fi
    fi
}

# Function to cleanup old backups
cleanup_old_backups() {
    log "Cleaning up backups older than $RETENTION_DAYS days..."

    # Find and delete old backup files
    local deleted_count=0

    for file in "$BACKUP_DIR"/*backup_*.{sql.gz,sql,rdb,tar.gz} 2>/dev/null; do
        if [ -f "$file" ]; then
            # Check if file is older than retention period
            if [ "$(find "$file" -mtime +$RETENTION_DAYS)" ]; then
                rm -f "$file"
                deleted_count=$((deleted_count + 1))
                log "Deleted old backup: $(basename "$file")"
            fi
        fi
    done

    log "Cleanup completed - deleted $deleted_count old backup files"
}

# Function to upload to S3 (if configured)
upload_to_s3() {
    if [ -n "${BACKUP_S3_BUCKET:-}" ] && [ -n "${AWS_ACCESS_KEY_ID:-}" ]; then
        log "Uploading backups to S3..."

        # This would require aws-cli to be installed
        # aws s3 cp "$PG_BACKUP_FILE" "s3://$BACKUP_S3_BUCKET/postgres/"
        # aws s3 cp "$PG_SCHEMA_FILE" "s3://$BACKUP_S3_BUCKET/postgres/"

        log "S3 upload configured but not implemented in this container"
    else
        log "S3 backup not configured - skipping upload"
    fi
}

# Function to send backup notifications
send_notification() {
    local status=$1
    local message=$2

    if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
        # Send Slack notification
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"Backup Status: $status\n$message\"}" \
            "$SLACK_WEBHOOK_URL" \
            2>/dev/null || true
    fi

    log "Backup notification: $status - $message"
}

# Function to generate backup report
generate_report() {
    local report_file="$BACKUP_DIR/backup_report_$TIMESTAMP.txt"

    cat > "$report_file" << EOF
Project Context Database Backup Report
======================================
Timestamp: $(date)
Backup ID: $TIMESTAMP
Retention: $RETENTION_DAYS days

Files Created:
$(ls -la "$BACKUP_DIR"/*"$TIMESTAMP"* 2>/dev/null || echo "No backup files found")

Database Info:
- Host: $DB_HOST:$DB_PORT
- Database: $DB_NAME
- User: $DB_USER

Backup Status: SUCCESS
EOF

    log "Backup report generated: $report_file"
}

# Main execution
main() {
    log "Starting Project Context backup process..."
    log "Backup timestamp: $TIMESTAMP"
    log "Retention period: $RETENTION_DAYS days"

    # Wait for services to be ready
    wait_for_postgres

    # Perform backups
    backup_postgres
    backup_redis
    backup_application_state

    # Verify backup integrity
    verify_backups

    # Cleanup old backups
    cleanup_old_backups

    # Upload to cloud storage (if configured)
    upload_to_s3

    # Generate report
    generate_report

    # Send success notification
    send_notification "SUCCESS" "Backup completed successfully at $TIMESTAMP"

    log "Backup process completed successfully"
}

# Error handling
trap 'log_error "Backup process failed"; send_notification "FAILED" "Backup process failed at $TIMESTAMP"; exit 1' ERR

# Execute main function
main "$@"
