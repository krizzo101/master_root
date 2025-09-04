#!/bin/bash
"""
Startup Script for pgvector Semantic Search System

Orchestrates the complete pgvector integration for unified context system:
1. Starts PostgreSQL with pgvector extension
2. Starts embedding service on localhost:8001
3. Runs initialization and validation tests
4. Provides system status and monitoring
"""

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$SCRIPT_DIR/pgvector_startup.log"
PID_DIR="$SCRIPT_DIR/pids"

# Create PID directory
mkdir -p "$PID_DIR"

# Logging function
log() {
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Error handling
error_exit() {
    log "${RED}ERROR: $1${NC}"
    exit 1
}

# Success message
success() {
    log "${GREEN}SUCCESS: $1${NC}"
}

# Warning message
warning() {
    log "${YELLOW}WARNING: $1${NC}"
}

# Info message
info() {
    log "${BLUE}INFO: $1${NC}"
}

# Check if service is running
is_service_running() {
    local service_name=$1
    local pid_file="$PID_DIR/$service_name.pid"

    if [[ -f "$pid_file" ]]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            return 0  # Running
        else
            rm -f "$pid_file"  # Clean up stale PID file
            return 1  # Not running
        fi
    else
        return 1  # Not running
    fi
}

# Wait for service to be ready
wait_for_service() {
    local service_name=$1
    local check_command=$2
    local max_attempts=${3:-30}
    local attempt=0

    info "Waiting for $service_name to be ready..."

    while [[ $attempt -lt $max_attempts ]]; do
        if eval "$check_command" >/dev/null 2>&1; then
            success "$service_name is ready"
            return 0
        fi

        attempt=$((attempt + 1))
        info "Attempt $attempt/$max_attempts - waiting for $service_name..."
        sleep 2
    done

    error_exit "$service_name failed to become ready within timeout"
}

# Start PostgreSQL with pgvector
start_postgres() {
    info "Starting PostgreSQL with pgvector extension..."

    if is_service_running "postgres"; then
        warning "PostgreSQL is already running"
        return 0
    fi

    # Check if Docker is available
    if ! command -v docker &> /dev/null; then
        error_exit "Docker is required but not installed"
    fi

    # Start PostgreSQL container
    cd "$SCRIPT_DIR"
    docker-compose -f docker-compose.postgres.yml up -d postgres

    if [[ $? -ne 0 ]]; then
        error_exit "Failed to start PostgreSQL container"
    fi

    # Save container ID as PID
    docker-compose -f docker-compose.postgres.yml ps -q postgres > "$PID_DIR/postgres.pid"

    # Wait for PostgreSQL to be ready
    wait_for_service "PostgreSQL" "docker-compose -f docker-compose.postgres.yml exec -T postgres pg_isready -U opsvi -d unified_context"

    success "PostgreSQL with pgvector is running"
}

# Start embedding service
start_embedding_service() {
    info "Starting embedding service on localhost:8001..."

    if is_service_running "embedding_service"; then
        warning "Embedding service is already running"
        return 0
    fi

    # Check if the embedding service directory exists
    if [[ ! -d "$SCRIPT_DIR/apps/embedding-service" ]]; then
        error_exit "Embedding service directory not found: $SCRIPT_DIR/apps/embedding-service"
    fi

    # Start embedding service container
    cd "$SCRIPT_DIR"
    docker-compose -f docker-compose.embedding.yml up -d embedding-service

    if [[ $? -ne 0 ]]; then
        error_exit "Failed to start embedding service container"
    fi

    # Save container ID as PID
    docker-compose -f docker-compose.embedding.yml ps -q embedding-service > "$PID_DIR/embedding_service.pid"

    # Wait for embedding service to be ready
    wait_for_service "Embedding Service" "curl -f http://localhost:8001/health"

    success "Embedding service is running on localhost:8001"
}

# Run database migrations
run_migrations() {
    info "Running database migrations and pgvector setup..."

    # Check if PostgreSQL is running
    if ! is_service_running "postgres"; then
        error_exit "PostgreSQL must be running before migrations"
    fi

    # Run pgvector setup script
    cd "$SCRIPT_DIR"
    docker-compose -f docker-compose.postgres.yml exec -T postgres psql -U opsvi -d unified_context -f /docker-entrypoint-initdb.d/02-setup-pgvector.sql

    if [[ $? -eq 0 ]]; then
        success "Database migrations completed successfully"
    else
        error_exit "Database migrations failed"
    fi
}

# Test system functionality
test_system() {
    info "Running system functionality tests..."

    # Check if Python is available
    if ! command -v python3 &> /dev/null; then
        warning "Python3 not found, skipping integration tests"
        return 0
    fi

    # Run integration tests
    cd "$SCRIPT_DIR"
    python3 test_pgvector_integration.py

    if [[ $? -eq 0 ]]; then
        success "System integration tests passed"
    else
        warning "Some integration tests failed - check logs for details"
    fi
}

# Show system status
show_status() {
    echo
    info "=== PGVECTOR SYSTEM STATUS ==="

    # PostgreSQL status
    if is_service_running "postgres"; then
        echo -e "${GREEN}✅ PostgreSQL: Running${NC}"

        # Check pgvector extension
        if docker-compose -f docker-compose.postgres.yml exec -T postgres psql -U opsvi -d unified_context -c "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector');" | grep -q "t"; then
            echo -e "${GREEN}✅ pgvector extension: Installed${NC}"
        else
            echo -e "${RED}❌ pgvector extension: Not installed${NC}"
        fi
    else
        echo -e "${RED}❌ PostgreSQL: Not running${NC}"
    fi

    # Embedding service status
    if is_service_running "embedding_service"; then
        echo -e "${GREEN}✅ Embedding Service: Running${NC}"

        # Check service health
        if curl -f http://localhost:8001/health >/dev/null 2>&1; then
            echo -e "${GREEN}✅ Embedding Service Health: OK${NC}"
        else
            echo -e "${YELLOW}⚠️ Embedding Service Health: Degraded${NC}"
        fi
    else
        echo -e "${RED}❌ Embedding Service: Not running${NC}"
    fi

    # Show listening ports
    echo
    info "Active Services:"
    ss -tlnp | grep -E "(5432|8001)" | while read line; do
        echo "  $line"
    done

    echo
    info "Log file: $LOG_FILE"
    info "PID directory: $PID_DIR"
}

# Stop all services
stop_services() {
    info "Stopping pgvector services..."

    # Stop embedding service
    if is_service_running "embedding_service"; then
        info "Stopping embedding service..."
        cd "$SCRIPT_DIR"
        docker-compose -f docker-compose.embedding.yml down
        rm -f "$PID_DIR/embedding_service.pid"
    fi

    # Stop PostgreSQL
    if is_service_running "postgres"; then
        info "Stopping PostgreSQL..."
        cd "$SCRIPT_DIR"
        docker-compose -f docker-compose.postgres.yml down
        rm -f "$PID_DIR/postgres.pid"
    fi

    success "All services stopped"
}

# Show help
show_help() {
    echo "pgvector Semantic Search System Startup Script"
    echo
    echo "Usage: $0 [OPTION]"
    echo
    echo "Options:"
    echo "  start       Start all services (PostgreSQL + Embedding Service)"
    echo "  stop        Stop all services"
    echo "  restart     Restart all services"
    echo "  status      Show system status"
    echo "  test        Run integration tests"
    echo "  migrate     Run database migrations"
    echo "  logs        Show recent logs"
    echo "  help        Show this help message"
    echo
    echo "Examples:"
    echo "  $0 start     # Start the complete system"
    echo "  $0 status    # Check if services are running"
    echo "  $0 test      # Validate system functionality"
    echo
}

# Show logs
show_logs() {
    if [[ -f "$LOG_FILE" ]]; then
        info "Recent logs from $LOG_FILE:"
        tail -n 50 "$LOG_FILE"
    else
        warning "No log file found"
    fi
}

# Main execution
main() {
    local command=${1:-"help"}

    case "$command" in
        "start")
            info "Starting pgvector semantic search system..."
            start_postgres
            start_embedding_service
            run_migrations
            show_status
            info "System startup complete!"
            ;;
        "stop")
            stop_services
            ;;
        "restart")
            stop_services
            sleep 2
            main "start"
            ;;
        "status")
            show_status
            ;;
        "test")
            test_system
            ;;
        "migrate")
            run_migrations
            ;;
        "logs")
            show_logs
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            error_exit "Unknown command: $command. Use 'help' to see available options."
            ;;
    esac
}

# Trap signals for clean shutdown
trap 'error_exit "Interrupted by user"' INT TERM

# Run main function
main "$@"
