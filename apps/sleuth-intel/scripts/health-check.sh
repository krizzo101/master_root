#!/bin/bash

# Health check script for Sleuth Intel application

set -euo pipefail

# Configuration
HEALTH_ENDPOINT="${HEALTH_ENDPOINT:-http://localhost:8000/health}"
READY_ENDPOINT="${READY_ENDPOINT:-http://localhost:8000/ready}"
METRICS_ENDPOINT="${METRICS_ENDPOINT:-http://localhost:9090/metrics}"
TIMEOUT=10

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Functions
check_endpoint() {
    local endpoint=$1
    local name=$2

    if curl -f -s --max-time ${TIMEOUT} ${endpoint} > /dev/null; then
        echo -e "${GREEN}✓${NC} ${name} check passed"
        return 0
    else
        echo -e "${RED}✗${NC} ${name} check failed"
        return 1
    fi
}

check_database() {
    echo -n "Checking database connection... "

    if psql ${DATABASE_URL} -c "SELECT 1" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Connected"
        return 0
    else
        echo -e "${RED}✗${NC} Failed"
        return 1
    fi
}

check_redis() {
    echo -n "Checking Redis connection... "

    if redis-cli ping > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Connected"
        return 0
    else
        echo -e "${RED}✗${NC} Failed"
        return 1
    fi
}

check_disk_space() {
    echo "Checking disk space..."

    local usage=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')

    if [ ${usage} -gt 90 ]; then
        echo -e "${RED}✗${NC} Disk usage critical: ${usage}%"
        return 1
    elif [ ${usage} -gt 80 ]; then
        echo -e "${YELLOW}⚠${NC} Disk usage warning: ${usage}%"
        return 0
    else
        echo -e "${GREEN}✓${NC} Disk usage normal: ${usage}%"
        return 0
    fi
}

check_memory() {
    echo "Checking memory usage..."

    local usage=$(free | grep Mem | awk '{print int($3/$2 * 100)}')

    if [ ${usage} -gt 90 ]; then
        echo -e "${RED}✗${NC} Memory usage critical: ${usage}%"
        return 1
    elif [ ${usage} -gt 80 ]; then
        echo -e "${YELLOW}⚠${NC} Memory usage warning: ${usage}%"
        return 0
    else
        echo -e "${GREEN}✓${NC} Memory usage normal: ${usage}%"
        return 0
    fi
}

check_processes() {
    echo "Checking application processes..."

    if pgrep -f "gunicorn" > /dev/null; then
        echo -e "${GREEN}✓${NC} Gunicorn is running"
    else
        echo -e "${RED}✗${NC} Gunicorn is not running"
        return 1
    fi

    return 0
}

# Main execution
echo "========================================="
echo "Sleuth Intel Health Check"
echo "========================================="
echo ""

FAILED=0

# Check endpoints
check_endpoint ${HEALTH_ENDPOINT} "Health" || FAILED=$((FAILED + 1))
check_endpoint ${READY_ENDPOINT} "Readiness" || FAILED=$((FAILED + 1))
check_endpoint ${METRICS_ENDPOINT} "Metrics" || FAILED=$((FAILED + 1))

echo ""

# Check services
check_database || FAILED=$((FAILED + 1))
check_redis || FAILED=$((FAILED + 1))

echo ""

# Check system resources
check_disk_space || FAILED=$((FAILED + 1))
check_memory || FAILED=$((FAILED + 1))
check_processes || FAILED=$((FAILED + 1))

echo ""
echo "========================================="

if [ ${FAILED} -eq 0 ]; then
    echo -e "${GREEN}All health checks passed!${NC}"
    exit 0
else
    echo -e "${RED}${FAILED} health check(s) failed${NC}"
    exit 1
fi
