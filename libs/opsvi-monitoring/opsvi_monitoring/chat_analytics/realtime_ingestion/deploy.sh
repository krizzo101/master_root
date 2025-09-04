#!/bin/bash

# Deployment script for real-time chat log ingestion service
# This script sets up the service for production deployment

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="/home/opsvi/master_root"
SERVICE_NAME="realtime-chat-ingestion"
SERVICE_USER="${SERVICE_USER:-opsvi}"
LOG_DIR="${LOG_DIR:-/var/log/${SERVICE_NAME}}"
RUN_DIR="${RUN_DIR:-/var/run/${SERVICE_NAME}}"
CONFIG_DIR="${CONFIG_DIR:-/etc/${SERVICE_NAME}}"

echo "🚀 Deploying Real-time Chat Log Ingestion Service"
echo "=============================================="

# Check if running as root for system-wide installation
if [[ $EUID -eq 0 ]]; then
    SYSTEM_INSTALL=true
    echo "📋 Installing system-wide service"
else
    SYSTEM_INSTALL=false
    echo "📋 Installing user service"
    LOG_DIR="${HOME}/.local/var/log/${SERVICE_NAME}"
    RUN_DIR="${HOME}/.local/var/run/${SERVICE_NAME}"
    CONFIG_DIR="${HOME}/.config/${SERVICE_NAME}"
fi

# Function to create directories
create_directories() {
    echo "📁 Creating directories..."

    mkdir -p "${LOG_DIR}"
    mkdir -p "${RUN_DIR}"
    mkdir -p "${CONFIG_DIR}"

    if [[ $SYSTEM_INSTALL == true ]]; then
        chown -R ${SERVICE_USER}:${SERVICE_USER} "${LOG_DIR}" "${RUN_DIR}" "${CONFIG_DIR}"
        chmod 755 "${LOG_DIR}" "${RUN_DIR}" "${CONFIG_DIR}"
    fi

    echo "   ✓ Directories created"
}

# Function to install Python dependencies
install_dependencies() {
    echo "📦 Installing Python dependencies..."

    # Check if in virtual environment
    if [[ -z "${VIRTUAL_ENV}" ]]; then
        echo "   ⚠️  Warning: Not in a virtual environment"
        echo "   ⚠️  Consider using: python -m venv .venv && source .venv/bin/activate"
    fi

    # Install required packages
    python -m pip install --upgrade pip
    python -m pip install \
        asyncio \
        asyncpg \
        psycopg2-binary \
        watchdog \
        psutil \
        pyyaml \
        uvloop \
        aiofiles

    # Install optional packages for monitoring
    python -m pip install prometheus_client || echo "   ⚠️  prometheus_client not installed (optional)"

    echo "   ✓ Dependencies installed"
}

# Function to copy configuration files
setup_configuration() {
    echo "⚙️  Setting up configuration..."

    # Copy default config
    cp "${SCRIPT_DIR}/config/default_config.yml" "${CONFIG_DIR}/config.yml"

    # Update paths in config for this installation
    if [[ $SYSTEM_INSTALL == true ]]; then
        sed -i "s|/tmp/realtime_chat_ingestion.log|${LOG_DIR}/service.log|g" "${CONFIG_DIR}/config.yml"
        sed -i "s|/tmp/realtime_chat_ingestion.pid|${RUN_DIR}/service.pid|g" "${CONFIG_DIR}/config.yml"
    else
        sed -i "s|/tmp/realtime_chat_ingestion.log|${LOG_DIR}/service.log|g" "${CONFIG_DIR}/config.yml"
        sed -i "s|/tmp/realtime_chat_ingestion.pid|${RUN_DIR}/service.pid|g" "${CONFIG_DIR}/config.yml"
    fi

    if [[ $SYSTEM_INSTALL == true ]]; then
        chown ${SERVICE_USER}:${SERVICE_USER} "${CONFIG_DIR}/config.yml"
        chmod 644 "${CONFIG_DIR}/config.yml"
    fi

    echo "   ✓ Configuration files setup"
    echo "   📝 Edit ${CONFIG_DIR}/config.yml to customize settings"
}

# Function to create systemd service file
create_systemd_service() {
    echo "🔧 Creating systemd service..."

    if [[ $SYSTEM_INSTALL == true ]]; then
        SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
        EXEC_USER="${SERVICE_USER}"
    else
        SERVICE_FILE="${HOME}/.config/systemd/user/${SERVICE_NAME}.service"
        mkdir -p "$(dirname "${SERVICE_FILE}")"
        EXEC_USER="$(whoami)"
    fi

    cat > "${SERVICE_FILE}" << EOF
[Unit]
Description=Real-time Chat Log Ingestion Service
Documentation=https://github.com/opsvi/master_root/libs/opsvi-monitoring
After=network.target postgresql.service

[Service]
Type=simple
User=${EXEC_USER}
Group=${EXEC_USER}
WorkingDirectory=${PROJECT_ROOT}
Environment=PYTHONPATH=${PROJECT_ROOT}
ExecStart=/usr/bin/python3 -m opsvi_monitoring.chat_analytics.realtime_ingestion.service_runner start --config ${CONFIG_DIR}/config.yml
ExecStop=/usr/bin/python3 -m opsvi_monitoring.chat_analytics.realtime_ingestion.service_runner stop --config ${CONFIG_DIR}/config.yml
ExecReload=/usr/bin/python3 -m opsvi_monitoring.chat_analytics.realtime_ingestion.service_runner restart --config ${CONFIG_DIR}/config.yml
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=${SERVICE_NAME}
PIDFile=${RUN_DIR}/service.pid

# Security settings
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=${LOG_DIR} ${RUN_DIR} ${PROJECT_ROOT} ${CONFIG_DIR}

# Resource limits
LimitNOFILE=65536
MemoryMax=1G

[Install]
WantedBy=multi-user.target
EOF

    if [[ $SYSTEM_INSTALL == true ]]; then
        systemctl daemon-reload
        echo "   ✓ System service created: ${SERVICE_FILE}"
        echo "   🔧 Enable with: sudo systemctl enable ${SERVICE_NAME}"
        echo "   ▶️  Start with: sudo systemctl start ${SERVICE_NAME}"
    else
        systemctl --user daemon-reload
        echo "   ✓ User service created: ${SERVICE_FILE}"
        echo "   🔧 Enable with: systemctl --user enable ${SERVICE_NAME}"
        echo "   ▶️  Start with: systemctl --user start ${SERVICE_NAME}"
    fi
}

# Function to create startup script
create_startup_script() {
    echo "📜 Creating startup script..."

    SCRIPT_PATH="${CONFIG_DIR}/start_service.sh"

    cat > "${SCRIPT_PATH}" << 'EOF'
#!/bin/bash

# Startup script for real-time chat log ingestion service

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/config.yml"
PROJECT_ROOT="/home/opsvi/master_root"

# Set Python path
export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH}"

# Change to project directory
cd "${PROJECT_ROOT}"

# Start the service
python3 -m opsvi_monitoring.chat_analytics.realtime_ingestion.service_runner start \
    --config "${CONFIG_FILE}" \
    "$@"
EOF

    chmod +x "${SCRIPT_PATH}"

    if [[ $SYSTEM_INSTALL == true ]]; then
        chown ${SERVICE_USER}:${SERVICE_USER} "${SCRIPT_PATH}"
    fi

    echo "   ✓ Startup script created: ${SCRIPT_PATH}"
}

# Function to create monitoring script
create_monitoring_script() {
    echo "📊 Creating monitoring script..."

    SCRIPT_PATH="${CONFIG_DIR}/monitor_service.sh"

    cat > "${SCRIPT_PATH}" << 'EOF'
#!/bin/bash

# Monitoring script for real-time chat log ingestion service

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/config.yml"
PROJECT_ROOT="/home/opsvi/master_root"

export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH}"
cd "${PROJECT_ROOT}"

case "${1:-status}" in
    status)
        echo "🔍 Service Status:"
        python3 -m opsvi_monitoring.chat_analytics.realtime_ingestion.service_runner status --config "${CONFIG_FILE}"
        ;;
    logs)
        echo "📋 Recent Logs:"
        tail -n 50 "$(dirname "${SCRIPT_DIR}")/log/service.log" 2>/dev/null || echo "No logs found"
        ;;
    metrics)
        echo "📊 Current Metrics:"
        python3 -c "
import sys
sys.path.insert(0, '${PROJECT_ROOT}')
from opsvi_monitoring.chat_analytics.realtime_ingestion.monitoring import create_prometheus_metrics
# Implementation would require running service instance
print('Service must be running to collect metrics')
"
        ;;
    health)
        echo "❤️  Health Check:"
        python3 -c "
import sys, json
sys.path.insert(0, '${PROJECT_ROOT}')
# Health check implementation
print('Health check requires running service')
"
        ;;
    *)
        echo "Usage: $0 {status|logs|metrics|health}"
        exit 1
        ;;
esac
EOF

    chmod +x "${SCRIPT_PATH}"

    if [[ $SYSTEM_INSTALL == true ]]; then
        chown ${SERVICE_USER}:${SERVICE_USER} "${SCRIPT_PATH}"
    fi

    echo "   ✓ Monitoring script created: ${SCRIPT_PATH}"
}

# Function to run tests
run_tests() {
    echo "🧪 Running tests..."

    cd "${PROJECT_ROOT}"
    export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH}"

    # Run unit tests
    echo "   Running unit tests..."
    python3 "${SCRIPT_DIR}/tests/test_realtime_ingestion.py" --suite unit

    echo "   ✓ Tests completed"
}

# Function to validate installation
validate_installation() {
    echo "✅ Validating installation..."

    # Check if Python can import the module
    cd "${PROJECT_ROOT}"
    export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH}"

    python3 -c "
import sys
sys.path.insert(0, '${PROJECT_ROOT}')
from opsvi_monitoring.chat_analytics.realtime_ingestion import RealTimeChatLogService
print('✓ Module imports successfully')
"

    # Check configuration
    if [[ -f "${CONFIG_DIR}/config.yml" ]]; then
        echo "   ✓ Configuration file exists"
    else
        echo "   ❌ Configuration file missing"
        exit 1
    fi

    # Check directories
    for dir in "${LOG_DIR}" "${RUN_DIR}" "${CONFIG_DIR}"; do
        if [[ -d "$dir" ]]; then
            echo "   ✓ Directory exists: $dir"
        else
            echo "   ❌ Directory missing: $dir"
            exit 1
        fi
    done

    echo "   ✅ Installation validated"
}

# Function to print deployment summary
print_summary() {
    echo ""
    echo "🎉 Deployment Complete!"
    echo "======================"
    echo ""
    echo "📁 Installation paths:"
    echo "   Config:     ${CONFIG_DIR}"
    echo "   Logs:       ${LOG_DIR}"
    echo "   Runtime:    ${RUN_DIR}"
    echo ""
    echo "🚀 Quick start:"
    echo "   Start service:   ${CONFIG_DIR}/start_service.sh"
    echo "   Monitor:         ${CONFIG_DIR}/monitor_service.sh"
    echo "   Edit config:     ${CONFIG_DIR}/config.yml"
    echo ""

    if [[ $SYSTEM_INSTALL == true ]]; then
        echo "🔧 Systemd commands:"
        echo "   Enable:     sudo systemctl enable ${SERVICE_NAME}"
        echo "   Start:      sudo systemctl start ${SERVICE_NAME}"
        echo "   Status:     sudo systemctl status ${SERVICE_NAME}"
        echo "   Logs:       sudo journalctl -u ${SERVICE_NAME} -f"
    else
        echo "🔧 Systemd commands:"
        echo "   Enable:     systemctl --user enable ${SERVICE_NAME}"
        echo "   Start:      systemctl --user start ${SERVICE_NAME}"
        echo "   Status:     systemctl --user status ${SERVICE_NAME}"
        echo "   Logs:       journalctl --user -u ${SERVICE_NAME} -f"
    fi

    echo ""
    echo "📚 Next steps:"
    echo "   1. Review and customize ${CONFIG_DIR}/config.yml"
    echo "   2. Ensure PostgreSQL is running and accessible"
    echo "   3. Start the service"
    echo "   4. Monitor logs for successful startup"
    echo ""
}

# Main deployment process
main() {
    echo "Starting deployment process..."

    create_directories
    install_dependencies
    setup_configuration
    create_systemd_service
    create_startup_script
    create_monitoring_script

    # Optional steps
    if [[ "${RUN_TESTS:-true}" == "true" ]]; then
        run_tests
    fi

    validate_installation
    print_summary
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --no-tests)
            export RUN_TESTS=false
            shift
            ;;
        --service-user)
            export SERVICE_USER="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --no-tests       Skip running tests"
            echo "  --service-user   Specify service user (default: opsvi)"
            echo "  --help           Show this help"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Run main deployment
main
