#!/bin/bash

# Database backup script for Sleuth Intel

set -euo pipefail

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/var/backups/sleuth-intel}"
DATABASE_URL="${DATABASE_URL}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
S3_BUCKET="${S3_BUCKET:-sleuth-intel-backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="sleuth_intel_backup_${TIMESTAMP}.sql"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

create_backup_dir() {
    if [ ! -d "${BACKUP_DIR}" ]; then
        log_info "Creating backup directory: ${BACKUP_DIR}"
        mkdir -p "${BACKUP_DIR}"
    fi
}

perform_backup() {
    log_info "Starting database backup..."

    # Parse database URL
    DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
    DB_PORT=$(echo $DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
    DB_NAME=$(echo $DATABASE_URL | sed -n 's/.*\/\(.*\)/\1/p')
    DB_USER=$(echo $DATABASE_URL | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')

    # Perform backup
    PGPASSWORD=$(echo $DATABASE_URL | sed -n 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/p') \
        pg_dump -h ${DB_HOST} -p ${DB_PORT} -U ${DB_USER} -d ${DB_NAME} \
        --verbose --no-owner --no-acl \
        -f "${BACKUP_DIR}/${BACKUP_FILE}"

    if [ $? -eq 0 ]; then
        log_info "Database backup completed: ${BACKUP_FILE}"

        # Compress backup
        gzip "${BACKUP_DIR}/${BACKUP_FILE}"
        BACKUP_FILE="${BACKUP_FILE}.gz"
        log_info "Backup compressed: ${BACKUP_FILE}"
    else
        log_error "Database backup failed"
        exit 1
    fi
}

verify_backup() {
    log_info "Verifying backup..."

    if [ -f "${BACKUP_DIR}/${BACKUP_FILE}" ]; then
        SIZE=$(du -h "${BACKUP_DIR}/${BACKUP_FILE}" | cut -f1)
        log_info "Backup file size: ${SIZE}"

        # Test integrity
        if gunzip -t "${BACKUP_DIR}/${BACKUP_FILE}" 2>/dev/null; then
            log_info "Backup integrity verified"
        else
            log_error "Backup file is corrupted"
            exit 1
        fi
    else
        log_error "Backup file not found"
        exit 1
    fi
}

upload_to_s3() {
    if command -v aws &> /dev/null; then
        log_info "Uploading backup to S3..."

        aws s3 cp "${BACKUP_DIR}/${BACKUP_FILE}" \
            "s3://${S3_BUCKET}/database/${BACKUP_FILE}" \
            --storage-class STANDARD_IA

        if [ $? -eq 0 ]; then
            log_info "Backup uploaded to S3: s3://${S3_BUCKET}/database/${BACKUP_FILE}"
        else
            log_warn "Failed to upload backup to S3"
        fi
    else
        log_warn "AWS CLI not installed, skipping S3 upload"
    fi
}

cleanup_old_backups() {
    log_info "Cleaning up old backups..."

    # Local cleanup
    find "${BACKUP_DIR}" -name "sleuth_intel_backup_*.sql.gz" \
        -mtime +${RETENTION_DAYS} -delete

    log_info "Removed local backups older than ${RETENTION_DAYS} days"

    # S3 cleanup
    if command -v aws &> /dev/null; then
        aws s3 ls "s3://${S3_BUCKET}/database/" | \
            while read -r line; do
                CREATE_DATE=$(echo $line | awk '{print $1" "$2}')
                CREATE_DATE_EPOCH=$(date -d "$CREATE_DATE" +%s)
                CURRENT_EPOCH=$(date +%s)
                AGE_DAYS=$(( ($CURRENT_EPOCH - $CREATE_DATE_EPOCH) / 86400 ))

                if [ $AGE_DAYS -gt $RETENTION_DAYS ]; then
                    FILE_NAME=$(echo $line | awk '{print $4}')
                    aws s3 rm "s3://${S3_BUCKET}/database/${FILE_NAME}"
                    log_info "Removed S3 backup: ${FILE_NAME}"
                fi
            done
    fi
}

send_notification() {
    local status=$1
    local message=$2

    # Send to monitoring system
    if [ ! -z "${MONITORING_WEBHOOK}" ]; then
        curl -X POST ${MONITORING_WEBHOOK} \
            -H "Content-Type: application/json" \
            -d "{\"status\": \"${status}\", \"message\": \"${message}\", \"timestamp\": \"$(date -Iseconds)\"}"
    fi

    # Log to syslog
    logger -t sleuth-intel-backup "${status}: ${message}"
}

# Main execution
main() {
    log_info "Starting Sleuth Intel database backup process"

    # Check prerequisites
    if [ -z "${DATABASE_URL}" ]; then
        log_error "DATABASE_URL is not set"
        exit 1
    fi

    # Create backup directory
    create_backup_dir

    # Perform backup
    perform_backup

    # Verify backup
    verify_backup

    # Upload to S3
    upload_to_s3

    # Cleanup old backups
    cleanup_old_backups

    # Send success notification
    send_notification "SUCCESS" "Database backup completed: ${BACKUP_FILE}"

    log_info "Backup process completed successfully"
}

# Error handling
trap 'log_error "Backup failed on line $LINENO"; send_notification "FAILURE" "Database backup failed"' ERR

# Run main function
main
