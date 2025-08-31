#!/bin/bash
# HECATON Automation Script
# Single entry point for all operations

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

PYTHON_VERSION="3.11"
VENV_DIR=".venv"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${BLUE}[HECATON]${NC} $1"; }
success() { echo -e "${GREEN}✅ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠️ $1${NC}"; }
error() { echo -e "${RED}❌ $1${NC}"; exit 1; }

# Check Python version
check_python() {
    if command -v python$PYTHON_VERSION >/dev/null 2>&1; then
        PYTHON_CMD="python$PYTHON_VERSION"
    elif command -v python3 >/dev/null 2>&1; then
        PYTHON_CMD="python3"
    else
        error "Python 3.11+ not found"
    fi
    log "Using Python: $($PYTHON_CMD --version)"
}

# Setup virtual environment
setup_venv() {
    if [ ! -d "$VENV_DIR" ]; then
        log "Creating virtual environment..."
        $PYTHON_CMD -m venv "$VENV_DIR"
        success "Virtual environment created"
    fi
    source "$VENV_DIR/bin/activate"
    pip install --upgrade pip
}

# Install dependencies
install_deps() {
    log "Installing dependencies..."
    pip install -e ".[dev]"
    success "Dependencies installed"
}

# Run tests
run_tests() {
    log "Running tests..."
    pytest tests/ -v
    success "Tests completed"
}

# Test parallel execution (Phase 0)
test_parallel() {
    log "Testing 2-agent parallel execution..."
    python -m hecaton.core.orchestrator --test-parallel
    success "Parallel execution test completed"
}

# Bootstrap Phase 1
bootstrap() {
    log "Starting Phase 1 bootstrap (2→5 agents)..."
    python -m hecaton.bootstrap.phase1
    success "Phase 1 bootstrap initiated"
}

# Run quality checks
run_quality() {
    log "Running quality checks..."
    black src/ tests/ --check
    isort src/ tests/ --check
    flake8 src/ tests/
    mypy src/
    success "Quality checks passed"
}

# Main command processing
case "${1:-help}" in
    "setup")
        check_python
        setup_venv
        install_deps
        ;;
    "test")
        setup_venv
        run_tests
        ;;
    "test-parallel")
        setup_venv
        test_parallel
        ;;
    "bootstrap")
        setup_venv
        bootstrap
        ;;
    "quality")
        setup_venv
        run_quality
        ;;
    "scaffold")
        ./scripts/scaffold.sh
        ;;
    "help"|*)
        echo "HECATON - Multi-Agent Orchestration Framework"
        echo ""
        echo "Usage: ./scripts/run.sh [command]"
        echo ""
        echo "Commands:"
        echo "  setup         - Setup environment and install dependencies"
        echo "  test          - Run all tests"
        echo "  test-parallel - Test 2-agent parallel execution (Phase 0)"
        echo "  bootstrap     - Start Phase 1 bootstrap (2→5 agents)"
        echo "  quality       - Run code quality checks"
        echo "  scaffold      - Create project structure"
        echo ""
        echo "Current Phase: 0 (Manual Core - 2 agents)"
        ;;
esac
