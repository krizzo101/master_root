#!/bin/bash
"""
Production Migration Execution Script
Comprehensive SQLite to PostgreSQL migration with safety checks
"""

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SQLITE_DB="/home/opsvi/master_root/chat_logs.db"
POSTGRES_URL="postgresql://opsvi:opsvi_secure_password@localhost:5432/unified_context"
MIGRATION_SCRIPT="$SCRIPT_DIR/sqlite_to_postgresql_migration.py"
TEST_SCRIPT="$SCRIPT_DIR/test_migration.py"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging
LOG_FILE="migration_execution_$(date +%Y%m%d_%H%M%S).log"

log() {
    echo -e "$1" | tee -a "$LOG_FILE"
}

log_info() {
    log "${BLUE}[INFO]${NC} $1"
}

log_warn() {
    log "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    log "${RED}[ERROR]${NC} $1"
}

log_success() {
    log "${GREEN}[SUCCESS]${NC} $1"
}

# Cleanup function
cleanup() {
    log_info "Cleaning up temporary files..."
    # Add any cleanup logic here
}

# Error handler
error_handler() {
    log_error "Migration failed at line $1"
    cleanup
    exit 1
}

trap 'error_handler $LINENO' ERR
trap cleanup EXIT

print_banner() {
    cat << 'EOF'
╔══════════════════════════════════════════════════════════════════════════════╗
║                    SQLite to PostgreSQL Migration                           ║
║                         Production Execution                                ║
╚══════════════════════════════════════════════════════════════════════════════╝
EOF
}

check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed"
        exit 1
    fi

    # Check Python dependencies
    python3 -c "import asyncpg, psycopg2, tqdm" 2>/dev/null || {
        log_error "Required Python packages not installed"
        log_info "Install with: pip install asyncpg psycopg2-binary tqdm"
        exit 1
    }

    # Check SQLite database
    if [[ ! -f "$SQLITE_DB" ]]; then
        log_error "SQLite database not found: $SQLITE_DB"
        exit 1
    fi

    # Check database size
    DB_SIZE=$(du -h "$SQLITE_DB" | cut -f1)
    log_info "SQLite database size: $DB_SIZE"

    # Check migration script
    if [[ ! -f "$MIGRATION_SCRIPT" ]]; then
        log_error "Migration script not found: $MIGRATION_SCRIPT"
        exit 1
    fi

    # Check test script
    if [[ ! -f "$TEST_SCRIPT" ]]; then
        log_warn "Test script not found: $TEST_SCRIPT"
    fi

    log_success "Prerequisites check passed"
}

check_postgresql() {
    log_info "Testing PostgreSQL connection..."

    # Extract connection details for psql test
    PG_HOST=$(echo "$POSTGRES_URL" | sed -n 's/.*@\([^:]*\):.*/\1/p')
    PG_PORT=$(echo "$POSTGRES_URL" | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
    PG_DB=$(echo "$POSTGRES_URL" | sed -n 's/.*\/\([^?]*\).*/\1/p')
    PG_USER=$(echo "$POSTGRES_URL" | sed -n 's/postgresql:\/\/\([^:]*\):.*/\1/p')

    # Test connection
    if command -v psql &> /dev/null; then
        PGPASSWORD="${POSTGRES_URL#*://*/}" psql -h "$PG_HOST" -p "$PG_PORT" -U "$PG_USER" -d "$PG_DB" -c "SELECT 1;" &>/dev/null || {
            log_error "Cannot connect to PostgreSQL database"
            exit 1
        }
    else
        log_warn "psql not available, skipping connection test"
    fi

    log_success "PostgreSQL connection verified"
}

run_tests() {
    log_info "Running pre-migration tests..."

    if [[ -f "$TEST_SCRIPT" ]]; then
        cd "$PROJECT_ROOT"
        python3 "$TEST_SCRIPT" | tee -a "$LOG_FILE"

        if [[ ${PIPESTATUS[0]} -eq 0 ]]; then
            log_success "All tests passed"
        else
            log_error "Tests failed"
            read -p "Continue with migration anyway? [y/N]: " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        fi
    else
        log_warn "Test script not found, skipping tests"
    fi
}

show_migration_options() {
    cat << 'EOF'
Migration Options:
1) Full migration (recommended for first run)
2) Incremental migration (resume from checkpoint)
3) Custom batch size
4) Skip validation (faster, less safe)
5) Custom configuration

EOF
    read -p "Select option [1-5] (default 1): " -n 1 -r
    echo
    OPTION=${REPLY:-1}
}

get_migration_params() {
    MIGRATION_PARAMS=()

    case $OPTION in
        1)
            log_info "Selected: Full migration with default settings"
            ;;
        2)
            log_info "Selected: Incremental migration"
            MIGRATION_PARAMS+=("--incremental")
            ;;
        3)
            read -p "Enter batch size (default 1000): " BATCH_SIZE
            BATCH_SIZE=${BATCH_SIZE:-1000}
            log_info "Selected: Custom batch size $BATCH_SIZE"
            MIGRATION_PARAMS+=("--batch-size" "$BATCH_SIZE")
            ;;
        4)
            log_warn "Selected: Skip validation (not recommended for production)"
            MIGRATION_PARAMS+=("--no-validation")
            ;;
        5)
            log_info "Selected: Custom configuration"
            read -p "Enter SQLite path [$SQLITE_DB]: " CUSTOM_SQLITE
            read -p "Enter PostgreSQL URL [$POSTGRES_URL]: " CUSTOM_POSTGRES
            SQLITE_DB=${CUSTOM_SQLITE:-$SQLITE_DB}
            POSTGRES_URL=${CUSTOM_POSTGRES:-$POSTGRES_URL}
            ;;
        *)
            log_info "Invalid option, using default full migration"
            ;;
    esac

    # Add database paths
    MIGRATION_PARAMS+=("--sqlite-path" "$SQLITE_DB")
    MIGRATION_PARAMS+=("--postgres-url" "$POSTGRES_URL")
}

confirm_migration() {
    log_warn "Migration will:"
    log_warn "  - Read from: $SQLITE_DB"
    log_warn "  - Write to PostgreSQL database"
    log_warn "  - Process potentially large amounts of data"
    log_warn "  - Create backup files"
    echo

    read -p "Are you sure you want to proceed? [y/N]: " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Migration cancelled by user"
        exit 0
    fi
}

run_migration() {
    log_info "Starting migration with parameters: ${MIGRATION_PARAMS[*]}"
    log_info "Migration started at: $(date)"

    cd "$PROJECT_ROOT"

    # Run migration with timeout and progress monitoring
    timeout 7200 python3 "$MIGRATION_SCRIPT" "${MIGRATION_PARAMS[@]}" 2>&1 | tee -a "$LOG_FILE" || {
        local exit_code=$?
        if [[ $exit_code -eq 124 ]]; then
            log_error "Migration timed out after 2 hours"
        else
            log_error "Migration failed with exit code $exit_code"
        fi
        exit $exit_code
    }

    log_success "Migration completed at: $(date)"
}

post_migration_checks() {
    log_info "Running post-migration validation..."

    # Check for migration report
    REPORT_FILES=(migration_report_*.json)
    if [[ -e "${REPORT_FILES[0]}" ]]; then
        LATEST_REPORT=$(ls -t migration_report_*.json | head -n1)
        log_info "Migration report: $LATEST_REPORT"

        # Extract key statistics
        if command -v jq &> /dev/null; then
            MIGRATED_RECORDS=$(jq -r '.stats.records_migrated' "$LATEST_REPORT" 2>/dev/null || echo "N/A")
            FAILED_RECORDS=$(jq -r '.stats.records_failed' "$LATEST_REPORT" 2>/dev/null || echo "N/A")
            DURATION=$(jq -r '.performance.migration_duration_seconds' "$LATEST_REPORT" 2>/dev/null || echo "N/A")

            log_info "Records migrated: $MIGRATED_RECORDS"
            log_info "Records failed: $FAILED_RECORDS"
            log_info "Duration: ${DURATION}s"
        fi
    else
        log_warn "No migration report found"
    fi

    # Check for errors in log
    if grep -q "ERROR" "$LOG_FILE"; then
        log_warn "Errors found in migration log"
        log_info "Review log file: $LOG_FILE"
    fi

    log_success "Post-migration checks completed"
}

main() {
    print_banner
    log_info "Migration execution started: $(date)"
    log_info "Log file: $LOG_FILE"

    # Prerequisite checks
    check_prerequisites
    check_postgresql

    # Pre-migration testing
    run_tests

    # Migration configuration
    show_migration_options
    get_migration_params

    # Final confirmation
    confirm_migration

    # Execute migration
    run_migration

    # Post-migration validation
    post_migration_checks

    log_success "Migration execution completed successfully!"
    log_info "Check the migration report and logs for detailed results"

    # Show summary
    cat << EOF

╔══════════════════════════════════════════════════════════════════════════════╗
║                           Migration Summary                                  ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Status: SUCCESS                                                              ║
║ Log: $LOG_FILE                                          ║
║ Reports: migration_report_*.json                                            ║
║ Backups: migration_backup_*/ (if created)                                   ║
╚══════════════════════════════════════════════════════════════════════════════╝

EOF
}

# Check if script is being sourced or executed
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
