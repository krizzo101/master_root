#!/bin/bash
# Project Context MCP Server Entrypoint Script

set -euo pipefail

# Default values
INTEL_DIR=${INTEL_DIR:-/app/data/.proj-intel}
LOG_LEVEL=${LOG_LEVEL:-INFO}
WORKERS=${WORKERS:-auto}

# Logging functions
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" >&2
}

# Health check function
health_check() {
    log "Starting health checks..."

    # Check if required directories exist
    if [ ! -d "$INTEL_DIR" ]; then
        log "Creating intelligence directory: $INTEL_DIR"
        mkdir -p "$INTEL_DIR"
    fi

    # Check database connectivity
    if [ -n "${DB_HOST:-}" ]; then
        log "Checking database connectivity..."
        while ! pg_isready -h "$DB_HOST" -p "${DB_PORT:-5432}" -U "${DB_USER:-opsvi}" 2>/dev/null; do
            log "Waiting for database to be ready..."
            sleep 2
        done
        log "Database is ready"
    fi

    # Check Redis connectivity
    if [ -n "${REDIS_HOST:-}" ]; then
        log "Checking Redis connectivity..."
        while ! redis-cli -h "$REDIS_HOST" -p "${REDIS_PORT:-6379}" ping 2>/dev/null | grep -q PONG; do
            log "Waiting for Redis to be ready..."
            sleep 2
        done
        log "Redis is ready"
    fi

    log "Health checks completed"
}

# Setup logging
setup_logging() {
    log "Setting up logging configuration..."

    # Create log directory
    mkdir -p /app/logs

    # Export environment variables for the application
    export PYTHONUNBUFFERED=1
    export LOG_LEVEL="$LOG_LEVEL"

    log "Logging configured with level: $LOG_LEVEL"
}

# Initialize application
init_application() {
    log "Initializing Project Context MCP Server..."

    # Set Python path
    export PYTHONPATH=/app/src:$PYTHONPATH

    # Setup cache if Redis is available
    if [ "${CACHE_ENABLED:-true}" = "true" ]; then
        log "Cache enabled"
        export ENABLE_REDIS_CACHE=true
    else
        log "Cache disabled"
        export ENABLE_REDIS_CACHE=false
    fi

    # Setup file watching if enabled
    if [ "${WATCH_ENABLED:-true}" = "true" ]; then
        log "File watching enabled"
        export ENABLE_FILE_WATCHING=true
    else
        log "File watching disabled"
        export ENABLE_FILE_WATCHING=false
    fi

    log "Application initialization completed"
}

# Start metrics collection
start_metrics() {
    if [ "${PROMETHEUS_ENABLED:-true}" = "true" ]; then
        log "Starting Prometheus metrics endpoint on port ${PROMETHEUS_PORT:-8080}"
        # The application itself will handle metrics endpoint
    else
        log "Prometheus metrics disabled"
    fi
}

# Cleanup function
cleanup() {
    log "Shutting down Project Context MCP Server..."

    # Kill background processes
    jobs -p | xargs -r kill 2>/dev/null || true

    # Cleanup cache connections
    if pgrep -f "project-context" > /dev/null; then
        pkill -TERM -f "project-context" || true
        sleep 5
        pkill -KILL -f "project-context" 2>/dev/null || true
    fi

    log "Shutdown completed"
}

# Signal handlers
trap cleanup SIGTERM SIGINT

# Determine number of workers
get_workers() {
    if [ "$WORKERS" = "auto" ]; then
        # Use number of CPU cores
        WORKERS=$(nproc)
        log "Auto-detected $WORKERS CPU cores"
    fi
    echo "$WORKERS"
}

# Production server startup
start_production_server() {
    local workers=$(get_workers)

    log "Starting production server with $workers workers..."

    exec gunicorn \
        --bind 0.0.0.0:3000 \
        --workers "$workers" \
        --worker-class "${WORKER_CLASS:-uvicorn.workers.UvicornWorker}" \
        --worker-connections "${WORKER_CONNECTIONS:-1000}" \
        --max-requests 1000 \
        --max-requests-jitter 100 \
        --timeout "${WORKER_TIMEOUT:-30}" \
        --keepalive "${KEEPALIVE:-5}" \
        --preload \
        --access-logfile /app/logs/access.log \
        --error-logfile /app/logs/error.log \
        --log-level "$LOG_LEVEL" \
        --capture-output \
        project_context.server.main:app
}

# Development server startup
start_dev_server() {
    log "Starting development server..."

    exec python -m uvicorn \
        project_context.server.main:app \
        --host 0.0.0.0 \
        --port 3000 \
        --log-level "${LOG_LEVEL,,}" \
        --reload \
        --reload-dir /app/src
}

# Main execution
main() {
    log "Project Context MCP Server starting up..."
    log "Version: ${VERSION:-development}"
    log "Environment: ${ENVIRONMENT:-production}"

    # Setup logging
    setup_logging

    # Run health checks
    health_check

    # Initialize application
    init_application

    # Start metrics collection
    start_metrics

    # Determine server type and start
    if [ "${DEVELOPMENT_MODE:-false}" = "true" ]; then
        start_dev_server
    else
        start_production_server
    fi
}

# Execute main function with all arguments
main "$@"
