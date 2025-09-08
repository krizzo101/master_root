#!/bin/bash
#
# Production Dashboard Startup Script
# Handles environment setup, dependency checks, and service management
#

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
LOG_DIR="$PROJECT_ROOT/logs"
CONFIG_FILE="$PROJECT_ROOT/production_config.json"
PID_FILE="$LOG_DIR/dashboard.pid"
PYTHON_PATH="/home/opsvi/miniconda/bin/python"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

# Check if running as correct user
check_user() {
    if [[ "$USER" != "opsvi" ]]; then
        warn "Script should be run as user 'opsvi', current user: $USER"
    fi
}

# Create necessary directories
setup_directories() {
    log "Setting up directories..."
    mkdir -p "$LOG_DIR"
    mkdir -p "$PROJECT_ROOT/outputs"
    chmod 755 "$LOG_DIR" "$PROJECT_ROOT/outputs"
}

# Check Python environment and dependencies
check_dependencies() {
    log "Checking dependencies..."

    if [[ ! -f "$PYTHON_PATH" ]]; then
        error "Python not found at: $PYTHON_PATH"
        exit 1
    fi

    # Check required Python packages
    local required_packages=(
        "aiohttp"
        "asyncio"
        "websockets"
        "pathlib"
    )

    for package in "${required_packages[@]}"; do
        if ! "$PYTHON_PATH" -c "import $package" 2>/dev/null; then
            error "Required package '$package' not installed"
            exit 1
        fi
    done

    log "✅ All dependencies satisfied"
}

# Check for existing process
check_existing_process() {
    if [[ -f "$PID_FILE" ]]; then
        local pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            warn "Dashboard already running with PID: $pid"
            return 0
        else
            log "Removing stale PID file"
            rm -f "$PID_FILE"
        fi
    fi
    return 1
}

# Start dashboard server
start_dashboard() {
    log "Starting production dashboard server..."

    # Set environment variables
    export PYTHONPATH="$PROJECT_ROOT/src:$PYTHONPATH"
    export DASHBOARD_HOST="${DASHBOARD_HOST:-0.0.0.0}"
    export DASHBOARD_PORT="${DASHBOARD_PORT:-8765}"
    export DASHBOARD_LOG_LEVEL="${DASHBOARD_LOG_LEVEL:-INFO}"

    # Start the dashboard
    cd "$PROJECT_ROOT"

    if [[ "${DAEMON:-false}" == "true" ]]; then
        # Run as daemon
        nohup "$PYTHON_PATH" production_dashboard.py --config "$CONFIG_FILE" \
            > "$LOG_DIR/dashboard_startup.log" 2>&1 &

        local pid=$!
        echo "$pid" > "$PID_FILE"

        log "Dashboard started as daemon with PID: $pid"
        log "Monitor logs: tail -f $LOG_DIR/dashboard_production.log"

        # Wait a moment to check if process is still running
        sleep 2
        if kill -0 "$pid" 2>/dev/null; then
            log "✅ Dashboard successfully started"
            log "🌐 Web UI: http://${DASHBOARD_HOST:-localhost}:${DASHBOARD_PORT:-8765}"
            log "🩺 Health: http://${DASHBOARD_HOST:-localhost}:8766/health"
        else
            error "Dashboard failed to start - check logs"
            exit 1
        fi
    else
        # Run in foreground
        exec "$PYTHON_PATH" production_dashboard.py --config "$CONFIG_FILE"
    fi
}

# Stop dashboard server
stop_dashboard() {
    if [[ -f "$PID_FILE" ]]; then
        local pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            log "Stopping dashboard server (PID: $pid)..."
            kill -TERM "$pid"

            # Wait for graceful shutdown
            local count=0
            while kill -0 "$pid" 2>/dev/null && [[ $count -lt 30 ]]; do
                sleep 1
                ((count++))
            done

            if kill -0 "$pid" 2>/dev/null; then
                warn "Forcefully killing dashboard process"
                kill -KILL "$pid"
            fi

            rm -f "$PID_FILE"
            log "✅ Dashboard stopped"
        else
            log "Dashboard not running"
            rm -f "$PID_FILE"
        fi
    else
        log "No PID file found - dashboard not running"
    fi
}

# Check dashboard status
status_dashboard() {
    if [[ -f "$PID_FILE" ]]; then
        local pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            log "Dashboard running with PID: $pid"

            # Check health endpoint
            if command -v curl >/dev/null; then
                local health_url="http://localhost:8766/health"
                if curl -s "$health_url" >/dev/null; then
                    log "✅ Health check passed"
                else
                    warn "❌ Health check failed"
                fi
            fi
        else
            warn "PID file exists but process not running"
            rm -f "$PID_FILE"
        fi
    else
        log "Dashboard not running"
    fi
}

# Restart dashboard
restart_dashboard() {
    log "Restarting dashboard..."
    stop_dashboard
    sleep 2
    start_dashboard
}

# Install as systemd service
install_service() {
    log "Installing systemd service..."

    if [[ $EUID -ne 0 ]]; then
        error "Service installation requires root privileges"
        exit 1
    fi

    local service_file="/etc/systemd/system/agent-orchestrator-dashboard.service"

    cp "$PROJECT_ROOT/dashboard.service" "$service_file"
    systemctl daemon-reload
    systemctl enable agent-orchestrator-dashboard.service

    log "✅ Service installed successfully"
    log "Start with: sudo systemctl start agent-orchestrator-dashboard"
    log "Check status: sudo systemctl status agent-orchestrator-dashboard"
}

# Show usage information
usage() {
    cat << EOF
Usage: $0 {start|stop|restart|status|install-service|check}

Commands:
  start          Start the dashboard server
  stop           Stop the dashboard server
  restart        Restart the dashboard server
  status         Show dashboard status
  install-service Install as systemd service (requires root)
  check          Check dependencies and configuration

Environment Variables:
  DASHBOARD_HOST     Host to bind to (default: 0.0.0.0)
  DASHBOARD_PORT     Port to bind to (default: 8765)
  DASHBOARD_LOG_LEVEL Log level (default: INFO)
  DAEMON             Run as daemon (default: false)

Examples:
  # Start in foreground
  $0 start

  # Start as daemon
  DAEMON=true $0 start

  # Start on custom port
  DASHBOARD_PORT=9000 $0 start

  # Install as system service
  sudo $0 install-service
EOF
}

# Main execution
main() {
    check_user
    setup_directories

    case "${1:-}" in
        start)
            if check_existing_process; then
                exit 0
            fi
            check_dependencies
            start_dashboard
            ;;
        stop)
            stop_dashboard
            ;;
        restart)
            restart_dashboard
            ;;
        status)
            status_dashboard
            ;;
        install-service)
            install_service
            ;;
        check)
            check_dependencies
            log "✅ All checks passed"
            ;;
        *)
            usage
            exit 1
            ;;
    esac
}

# Handle signals for graceful shutdown
trap 'log "Received signal, shutting down..."; stop_dashboard; exit 0' SIGTERM SIGINT

# Run main function
main "$@"
