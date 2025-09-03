#!/bin/bash
#
# Claude Monitor Launch Script
# Provides convenient shortcuts and environment setup for the Claude monitoring system
#

set -e  # Exit on any error

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_NAME="Claude Monitor"
PYTHON_PATH="/home/opsvi/miniconda/bin/python"
MAIN_SCRIPT="$SCRIPT_DIR/main.py"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_header() {
    echo -e "${PURPLE}=== $1 ===${NC}"
}

# Check if Python exists
check_python() {
    if [[ ! -f "$PYTHON_PATH" ]]; then
        log_error "Python not found at $PYTHON_PATH"
        log_info "Please update PYTHON_PATH in this script or install Python"
        exit 1
    fi

    # Check Python version
    local python_version=$("$PYTHON_PATH" --version 2>&1)
    log_info "Using $python_version from $PYTHON_PATH"
}

# Check if main script exists
check_main_script() {
    if [[ ! -f "$MAIN_SCRIPT" ]]; then
        log_error "Main script not found at $MAIN_SCRIPT"
        exit 1
    fi
}

# Install/check dependencies
check_dependencies() {
    log_info "Checking dependencies..."

    local missing_deps=()

    # Check for required Python packages
    local required_packages=(
        "fastapi"
        "uvicorn"
        "rich"
        "psutil"
        "docker"
        "websockets"
        "pydantic"
    )

    for package in "${required_packages[@]}"; do
        if ! "$PYTHON_PATH" -c "import $package" 2>/dev/null; then
            missing_deps+=("$package")
        fi
    done

    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log_warning "Missing dependencies: ${missing_deps[*]}"
        log_info "Install with: pip install ${missing_deps[*]}"

        read -p "Would you like to install them now? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log_info "Installing dependencies..."
            "$PYTHON_PATH" -m pip install "${missing_deps[@]}"
            log_success "Dependencies installed"
        else
            log_warning "Some features may not work without dependencies"
        fi
    else
        log_success "All dependencies are available"
    fi
}

# Show usage information
show_usage() {
    cat << EOF
${PURPLE}$APP_NAME Launch Script${NC}

${CYAN}Usage:${NC}
    $0 [MODE] [OPTIONS]

${CYAN}Modes:${NC}
    console     Run with console UI (default)
    web         Run with web UI (future)
    backend     Run backend service only

${CYAN}Quick Commands:${NC}
    start       Start with console UI
    web         Start with web UI
    api         Start backend API only

${CYAN}Management:${NC}
    status      Check if services are running
    stop        Stop running services
    restart     Restart services
    logs        Show recent logs

${CYAN}Development:${NC}
    dev         Start in development mode with auto-reload
    debug       Start with debug logging
    test        Run tests (if available)

${CYAN}Utilities:${NC}
    deps        Check/install dependencies
    health      Check system health
    help        Show this help message

${CYAN}Examples:${NC}
    $0              # Start with console UI
    $0 console      # Start with console UI
    $0 web          # Start with web UI
    $0 backend      # Start backend only
    $0 dev          # Development mode
    $0 --port 8080  # Use custom port
    $0 --host 0.0.0.0 --port 8080  # Bind to all interfaces

${CYAN}Options:${NC}
    --host HOST     Host to bind service (default: localhost)
    --port PORT     Port for service (default: 8000)
    --log-level LVL Logging level: DEBUG, INFO, WARNING, ERROR
    --debug         Enable debug mode
    --help          Show detailed help

EOF
}

# Check if any services are running
check_service_status() {
    local pids=$(pgrep -f "claude-monitor" 2>/dev/null || true)
    if [[ -n "$pids" ]]; then
        log_info "Claude Monitor services running (PIDs: $pids)"
        return 0
    else
        log_info "No Claude Monitor services running"
        return 1
    fi
}

# Stop running services
stop_services() {
    log_info "Stopping Claude Monitor services..."

    local pids=$(pgrep -f "claude-monitor" 2>/dev/null || true)
    if [[ -n "$pids" ]]; then
        echo "$pids" | xargs kill -TERM 2>/dev/null || true
        sleep 2

        # Force kill if still running
        local remaining=$(pgrep -f "claude-monitor" 2>/dev/null || true)
        if [[ -n "$remaining" ]]; then
            log_warning "Force killing remaining processes..."
            echo "$remaining" | xargs kill -KILL 2>/dev/null || true
        fi

        log_success "Services stopped"
    else
        log_info "No services were running"
    fi
}

# Show recent logs
show_logs() {
    local log_file="/tmp/claude-monitor.log"
    if [[ -f "$log_file" ]]; then
        log_info "Recent logs from $log_file:"
        tail -n 50 "$log_file"
    else
        log_info "No log file found at $log_file"
    fi
}

# Run health check
run_health_check() {
    log_header "System Health Check"

    # Check Python
    check_python

    # Check main script
    check_main_script

    # Check dependencies
    check_dependencies

    # Check database
    local db_path="/home/opsvi/master_root/chat_logs.db"
    if [[ -f "$db_path" ]]; then
        log_success "Database found: $db_path"
        local db_size=$(du -h "$db_path" | cut -f1)
        log_info "Database size: $db_size"
    else
        log_warning "Database not found: $db_path"
    fi

    # Check Docker
    if command -v docker &> /dev/null; then
        if docker info &> /dev/null; then
            log_success "Docker is running"
        else
            log_warning "Docker is installed but not running"
        fi
    else
        log_warning "Docker not found"
    fi

    log_success "Health check completed"
}

# Run the application with given arguments
run_application() {
    local mode="$1"
    shift

    log_header "Starting $APP_NAME"

    # Basic checks
    check_python
    check_main_script

    # Build command
    local cmd=("$PYTHON_PATH" "$MAIN_SCRIPT")

    # Add mode if specified
    case "$mode" in
        console|"")
            cmd+=("--console")
            ;;
        web)
            cmd+=("--web")
            ;;
        backend|api)
            cmd+=("--backend")
            ;;
        dev)
            cmd+=("--console" "--reload" "--debug")
            ;;
        debug)
            cmd+=("--console" "--debug")
            ;;
        *)
            cmd+=("--$mode")
            ;;
    esac

    # Add remaining arguments
    cmd+=("$@")

    log_info "Starting: ${cmd[*]}"
    log_info "Press Ctrl+C to stop"
    echo

    # Execute command
    exec "${cmd[@]}"
}

# Main script logic
main() {
    cd "$SCRIPT_DIR"

    # Handle special commands first
    case "${1:-}" in
        help|--help|-h)
            show_usage
            exit 0
            ;;
        status)
            check_service_status
            exit $?
            ;;
        stop)
            stop_services
            exit 0
            ;;
        restart)
            stop_services
            sleep 1
            run_application console "${@:2}"
            ;;
        logs)
            show_logs
            exit 0
            ;;
        deps)
            check_dependencies
            exit 0
            ;;
        health)
            run_health_check
            exit 0
            ;;
        test)
            log_info "Running tests..."
            if [[ -f "test_*.py" ]] || [[ -d "tests" ]]; then
                "$PYTHON_PATH" -m pytest . -v
            else
                log_warning "No tests found"
            fi
            exit 0
            ;;
        start)
            run_application console "${@:2}"
            ;;
        ""|console|web|backend|api|dev|debug)
            run_application "$@"
            ;;
        *)
            # Check if it's a flag
            if [[ "$1" =~ ^-- ]]; then
                run_application console "$@"
            else
                log_error "Unknown command: $1"
                log_info "Use '$0 help' for usage information"
                exit 1
            fi
            ;;
    esac
}

# Run main function with all arguments
main "$@"
