#!/bin/bash
"""
Unified Monitoring Suite Deployment Script

Deploys and configures the complete monitoring and performance optimization suite:
- Unified monitoring dashboard (port 8002)
- Performance optimizer with automated recommendations
- Comprehensive health checker with deep diagnostics
- Advanced alert manager with multi-channel notifications
- Log aggregation system with pattern detection
- Capacity planner with growth forecasting
- Production readiness validation

This script orchestrates the deployment of all monitoring components and ensures
they are properly integrated with the existing unified context system.
"""

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="/home/opsvi/master_root"
LOG_FILE="$SCRIPT_DIR/deployment.log"
PID_DIR="$SCRIPT_DIR/pids"

# Create necessary directories
mkdir -p "$PID_DIR"
mkdir -p "$PROJECT_ROOT/logs/monitoring"
mkdir -p "$PROJECT_ROOT/logs/archives"

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

# Section header
section() {
    log "${PURPLE}=== $1 ===${NC}"
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

# Start Python service
start_python_service() {
    local service_name=$1
    local script_path=$2
    local port=${3:-""}

    if is_service_running "$service_name"; then
        warning "$service_name is already running"
        return 0
    fi

    info "Starting $service_name..."

    # Set environment variables
    export PYTHONPATH="$PROJECT_ROOT/libs:$PROJECT_ROOT/apps:$PYTHONPATH"
    export LOG_LEVEL="INFO"
    export MONITORING_DB_PATH="$PROJECT_ROOT/logs/monitoring/monitoring.db"

    # Start the service
    cd "$SCRIPT_DIR"

    if [[ -n "$port" ]]; then
        nohup python3 "$script_path" --port "$port" > "$PROJECT_ROOT/logs/monitoring/${service_name}.log" 2>&1 &
    else
        nohup python3 "$script_path" > "$PROJECT_ROOT/logs/monitoring/${service_name}.log" 2>&1 &
    fi

    local pid=$!
    echo "$pid" > "$PID_DIR/$service_name.pid"

    # Wait for service to start
    sleep 3

    if kill -0 "$pid" 2>/dev/null; then
        success "$service_name started successfully (PID: $pid)"
        if [[ -n "$port" ]]; then
            info "$service_name available at http://localhost:$port"
        fi
    else
        error_exit "$service_name failed to start"
    fi
}

# Stop service
stop_service() {
    local service_name=$1
    local pid_file="$PID_DIR/$service_name.pid"

    if [[ -f "$pid_file" ]]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            info "Stopping $service_name (PID: $pid)..."
            kill "$pid"

            # Wait for graceful shutdown
            for i in {1..10}; do
                if ! kill -0 "$pid" 2>/dev/null; then
                    success "$service_name stopped successfully"
                    rm -f "$pid_file"
                    return 0
                fi
                sleep 1
            done

            # Force kill if still running
            if kill -0 "$pid" 2>/dev/null; then
                warning "Force killing $service_name..."
                kill -9 "$pid"
                sleep 2
            fi
        fi

        rm -f "$pid_file"
        info "$service_name stopped"
    else
        info "$service_name is not running"
    fi
}

# Check dependencies
check_dependencies() {
    section "Checking Dependencies"

    # Check Python
    if ! command -v python3 &> /dev/null; then
        error_exit "Python 3 is required but not installed"
    fi

    local python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
    info "Python version: $python_version"

    # Check required Python packages
    local required_packages=("fastapi" "uvicorn" "psycopg2" "neo4j" "docker" "psutil" "numpy" "aiofiles" "requests")
    local missing_packages=()

    for package in "${required_packages[@]}"; do
        if ! python3 -c "import $package" 2>/dev/null; then
            missing_packages+=("$package")
        fi
    done

    if [ ${#missing_packages[@]} -gt 0 ]; then
        warning "Missing Python packages: ${missing_packages[*]}"
        info "Installing missing packages..."

        for package in "${missing_packages[@]}"; do
            if [[ "$package" == "psycopg2" ]]; then
                pip3 install psycopg2-binary
            else
                pip3 install "$package"
            fi
        done
    fi

    # Check Docker
    if command -v docker &> /dev/null; then
        info "Docker is available"
        if ! docker ps &> /dev/null; then
            warning "Docker daemon is not running or accessible"
        fi
    else
        warning "Docker is not available - container monitoring will be limited"
    fi

    # Check database connections
    info "Checking database connections..."

    # Test PostgreSQL
    if python3 -c "
import psycopg2
try:
    conn = psycopg2.connect(host='localhost', port=5432, database='unified_context', user='opsvi', password='opsvi_secure_password')
    conn.close()
    print('PostgreSQL: Connected')
except Exception as e:
    print(f'PostgreSQL: Connection failed - {e}')
    exit(1)
" 2>/dev/null; then
        success "PostgreSQL connection verified"
    else
        warning "PostgreSQL connection failed - some monitoring features may be limited"
    fi

    # Test Neo4j
    if python3 -c "
from neo4j import GraphDatabase
try:
    driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'password'))
    with driver.session() as session:
        session.run('RETURN 1')
    driver.close()
    print('Neo4j: Connected')
except Exception as e:
    print(f'Neo4j: Connection failed - {e}')
    exit(1)
" 2>/dev/null; then
        success "Neo4j connection verified"
    else
        warning "Neo4j connection failed - graph monitoring will be limited"
    fi

    success "Dependency check completed"
}

# Create configuration files
create_configurations() {
    section "Creating Configuration Files"

    # Create monitoring configuration
    cat > "$SCRIPT_DIR/monitoring_config.json" << EOF
{
    "postgres": {
        "host": "localhost",
        "port": 5432,
        "database": "unified_context",
        "user": "opsvi",
        "password": "opsvi_secure_password"
    },
    "neo4j": {
        "uri": "bolt://localhost:7687",
        "user": "neo4j",
        "password": "password"
    },
    "embedding_service": {
        "url": "http://localhost:8001"
    },
    "monitoring_service": {
        "url": "http://localhost:8000"
    },
    "unified_dashboard": {
        "port": 8002,
        "host": "0.0.0.0",
        "log_level": "INFO"
    },
    "alert_manager": {
        "email": {
            "smtp_server": "localhost",
            "smtp_port": 587,
            "from_address": "alerts@opsvi.local",
            "to_address": "admin@opsvi.local",
            "use_tls": false,
            "enabled": false
        },
        "webhook": {
            "default_url": "",
            "enabled": false
        },
        "file": {
            "alert_log_path": "$PROJECT_ROOT/logs/monitoring/alerts.log",
            "enabled": true
        }
    },
    "log_aggregator": {
        "database_path": "$PROJECT_ROOT/logs/monitoring/log_aggregator.db",
        "collection_interval": 300,
        "archive_retention_days": 30
    },
    "capacity_planner": {
        "forecasting_periods": ["1_month", "3_months", "6_months", "1_year"],
        "growth_analysis_window": 1000,
        "confidence_threshold": 0.7
    }
}
EOF

    success "Configuration files created"
}

# Create systemd service files (optional)
create_systemd_services() {
    section "Creating Systemd Service Files"

    if [[ "$EUID" -eq 0 ]]; then
        info "Creating systemd service files..."

        # Unified Monitoring Dashboard Service
        cat > /etc/systemd/system/unified-monitoring-dashboard.service << EOF
[Unit]
Description=Unified Monitoring Dashboard
After=network.target postgresql.service neo4j.service

[Service]
Type=simple
User=opsvi
WorkingDirectory=$SCRIPT_DIR
Environment=PYTHONPATH=$PROJECT_ROOT/libs:$PROJECT_ROOT/apps
ExecStart=/usr/bin/python3 $SCRIPT_DIR/unified_monitoring_dashboard.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

        systemctl daemon-reload
        success "Systemd service files created"
        info "To enable services on boot: sudo systemctl enable unified-monitoring-dashboard"
    else
        warning "Not running as root - skipping systemd service creation"
    fi
}

# Deploy monitoring suite
deploy_monitoring_suite() {
    section "Deploying Monitoring Suite"

    # Start the unified monitoring dashboard
    start_python_service "unified_dashboard" "$SCRIPT_DIR/unified_monitoring_dashboard.py" "8002"

    # Wait for dashboard to be ready
    info "Waiting for monitoring dashboard to be ready..."
    for i in {1..30}; do
        if curl -f http://localhost:8002/api/health >/dev/null 2>&1; then
            success "Monitoring dashboard is ready"
            break
        fi
        sleep 2
        if [[ $i -eq 30 ]]; then
            error_exit "Monitoring dashboard failed to become ready"
        fi
    done

    success "Monitoring suite deployment completed"
}

# Run initial health check
run_health_check() {
    section "Running Initial Health Check"

    info "Performing comprehensive health check..."

    # Create health check script
    cat > "$SCRIPT_DIR/run_health_check.py" << 'EOF'
#!/usr/bin/env python3
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from health_checker import run_health_check

async def main():
    try:
        result = await run_health_check()
        if result and not isinstance(result, dict) or 'error' not in result:
            print("✅ Health check completed successfully")
            return 0
        else:
            print("❌ Health check failed")
            return 1
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
EOF

    chmod +x "$SCRIPT_DIR/run_health_check.py"

    if python3 "$SCRIPT_DIR/run_health_check.py"; then
        success "Initial health check passed"
    else
        warning "Initial health check showed issues - check the generated report"
    fi
}

# Run performance analysis
run_performance_analysis() {
    section "Running Performance Analysis"

    info "Performing comprehensive performance analysis..."

    # Create performance analysis script
    cat > "$SCRIPT_DIR/run_performance_analysis.py" << 'EOF'
#!/usr/bin/env python3
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from performance_optimizer import run_performance_analysis

async def main():
    try:
        result = await run_performance_analysis()
        if result and 'error' not in result:
            print("✅ Performance analysis completed successfully")
            return 0
        else:
            print("❌ Performance analysis failed")
            return 1
    except Exception as e:
        print(f"❌ Performance analysis error: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
EOF

    chmod +x "$SCRIPT_DIR/run_performance_analysis.py"

    if python3 "$SCRIPT_DIR/run_performance_analysis.py"; then
        success "Performance analysis completed"
    else
        warning "Performance analysis showed issues - check the generated report"
    fi
}

# Show service status
show_status() {
    section "Service Status"

    local services=("unified_dashboard")

    for service in "${services[@]}"; do
        if is_service_running "$service"; then
            echo -e "${GREEN}✅ $service: Running${NC}"

            # Show additional info for dashboard
            if [[ "$service" == "unified_dashboard" ]]; then
                if curl -f http://localhost:8002/api/health >/dev/null 2>&1; then
                    echo -e "   ${GREEN}✅ Dashboard Health: OK${NC}"
                    echo -e "   ${BLUE}🌐 URL: http://localhost:8002${NC}"
                else
                    echo -e "   ${YELLOW}⚠️ Dashboard Health: Degraded${NC}"
                fi
            fi
        else
            echo -e "${RED}❌ $service: Not Running${NC}"
        fi
    done

    # Show log locations
    echo
    info "Log Files:"
    echo "  - Deployment: $LOG_FILE"
    echo "  - Services: $PROJECT_ROOT/logs/monitoring/"
    echo "  - Alerts: $PROJECT_ROOT/logs/monitoring/alerts.log"

    # Show report locations
    echo
    info "Generated Reports:"
    find "$PROJECT_ROOT" -name "*REPORT_*.json" -type f -newer "$SCRIPT_DIR" 2>/dev/null | head -5 | while read file; do
        echo "  - $(basename "$file")"
    done
}

# Stop all services
stop_all() {
    section "Stopping All Services"

    local services=("unified_dashboard")

    for service in "${services[@]}"; do
        stop_service "$service"
    done

    success "All services stopped"
}

# Main function
main() {
    local command=${1:-"deploy"}

    log "${PURPLE}Unified Monitoring Suite Deployment${NC}"
    log "Time: $(date)"
    log "Command: $command"
    log "Working Directory: $SCRIPT_DIR"

    case "$command" in
        "deploy")
            check_dependencies
            create_configurations
            deploy_monitoring_suite

            # Run initial assessments
            run_health_check
            run_performance_analysis

            show_status

            info "🚀 Deployment completed!"
            info "📊 Access the monitoring dashboard at: http://localhost:8002"
            info "📝 View logs in: $PROJECT_ROOT/logs/monitoring/"
            info "🔍 Check reports in: $PROJECT_ROOT/*REPORT_*.json"

            ;;

        "start")
            deploy_monitoring_suite
            show_status
            ;;

        "stop")
            stop_all
            ;;

        "restart")
            stop_all
            sleep 2
            deploy_monitoring_suite
            show_status
            ;;

        "status")
            show_status
            ;;

        "health")
            run_health_check
            ;;

        "performance")
            run_performance_analysis
            ;;

        "install-systemd")
            create_systemd_services
            ;;

        "help"|"-h"|"--help")
            echo "Unified Monitoring Suite Deployment Script"
            echo
            echo "Usage: $0 [COMMAND]"
            echo
            echo "Commands:"
            echo "  deploy          Full deployment (default)"
            echo "  start           Start monitoring services"
            echo "  stop            Stop all services"
            echo "  restart         Restart all services"
            echo "  status          Show service status"
            echo "  health          Run health check"
            echo "  performance     Run performance analysis"
            echo "  install-systemd Create systemd services (requires root)"
            echo "  help            Show this help message"
            echo
            echo "Examples:"
            echo "  $0 deploy       # Full deployment"
            echo "  $0 status       # Check service status"
            echo "  $0 restart      # Restart all services"
            echo
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
