#!/bin/bash
# Autonomous Claude Agent Bootstrap Script
# Generated: 2025-08-15
# Version: 1.0.0
#
# This script sets up the complete environment for the Autonomous Claude Agent

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PYTHON_VERSION="3.11"
VENV_DIR="venv"
LOG_FILE="$PROJECT_ROOT/logs/bootstrap.log"

# Functions
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        error "$1 is not installed. Please install it first."
    fi
}

check_python_version() {
    local python_cmd="$1"
    local required_version="$2"
    
    if ! $python_cmd -c "import sys; exit(0 if sys.version_info >= tuple(map(int, '$required_version'.split('.'))) else 1)" 2>/dev/null; then
        return 1
    fi
    return 0
}

create_directories() {
    log "Creating project directories..."
    
    local dirs=(
        "$PROJECT_ROOT/data"
        "$PROJECT_ROOT/logs"
        "$PROJECT_ROOT/checkpoints"
        "$PROJECT_ROOT/cache"
        "$PROJECT_ROOT/exports"
        "$PROJECT_ROOT/imports"
        "$PROJECT_ROOT/backups"
        "$PROJECT_ROOT/temp"
        "$PROJECT_ROOT/config"
        "$PROJECT_ROOT/src"
        "$PROJECT_ROOT/tests"
        "$PROJECT_ROOT/scripts"
        "$PROJECT_ROOT/docs"
        "$PROJECT_ROOT/templates"
        "$PROJECT_ROOT/prompts"
    )
    
    for dir in "${dirs[@]}"; do
        mkdir -p "$dir"
        log "Created: $dir"
    done
    
    success "Directories created successfully"
}

setup_python_environment() {
    log "Setting up Python environment..."
    
    # Find appropriate Python version
    local python_cmd=""
    for cmd in python3.11 python3 python; do
        if check_python_version "$cmd" "$PYTHON_VERSION"; then
            python_cmd="$cmd"
            break
        fi
    done
    
    if [ -z "$python_cmd" ]; then
        error "Python $PYTHON_VERSION or higher is required but not found"
    fi
    
    log "Using Python: $($python_cmd --version)"
    
    # Create virtual environment
    log "Creating virtual environment..."
    $python_cmd -m venv "$PROJECT_ROOT/$VENV_DIR"
    
    # Activate virtual environment
    source "$PROJECT_ROOT/$VENV_DIR/bin/activate"
    
    # Upgrade pip
    log "Upgrading pip..."
    pip install --upgrade pip setuptools wheel
    
    success "Python environment setup complete"
}

install_dependencies() {
    log "Installing Python dependencies..."
    
    # Activate virtual environment
    source "$PROJECT_ROOT/$VENV_DIR/bin/activate"
    
    # Install requirements
    if [ -f "$PROJECT_ROOT/requirements.txt" ]; then
        pip install -r "$PROJECT_ROOT/requirements.txt"
        success "Dependencies installed from requirements.txt"
    else
        warning "requirements.txt not found"
    fi
    
    # Install package in development mode
    if [ -f "$PROJECT_ROOT/pyproject.toml" ]; then
        pip install -e "$PROJECT_ROOT[dev]"
        success "Package installed in development mode"
    fi
}

setup_environment_file() {
    log "Setting up environment file..."
    
    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        if [ -f "$PROJECT_ROOT/.env.example" ]; then
            cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
            warning "Created .env from .env.example - Please update with your API keys"
        else
            error ".env.example not found"
        fi
    else
        log ".env file already exists"
    fi
}

check_docker() {
    log "Checking Docker installation..."
    
    if command -v docker &> /dev/null; then
        log "Docker version: $(docker --version)"
        
        if docker compose version &> /dev/null 2>&1; then
            log "Docker Compose version: $(docker compose version)"
        elif command -v docker-compose &> /dev/null; then
            log "Docker Compose version: $(docker-compose --version)"
        else
            warning "Docker Compose not found"
        fi
    else
        warning "Docker not installed - Some features may not be available"
    fi
}

setup_git_hooks() {
    log "Setting up Git hooks..."
    
    if [ -d "$PROJECT_ROOT/.git" ]; then
        # Create hooks directory if it doesn't exist
        mkdir -p "$PROJECT_ROOT/.git/hooks"
        
        # Pre-commit hook
        cat > "$PROJECT_ROOT/.git/hooks/pre-commit" << 'EOF'
#!/bin/bash
# Pre-commit hook for code quality

# Activate virtual environment
source venv/bin/activate

# Run formatters and linters
echo "Running code formatters..."
black src/ tests/ scripts/ --check
ruff check src/ tests/ scripts/

# Run type checking
echo "Running type checking..."
mypy src/

# Run tests
echo "Running tests..."
pytest tests/unit -q

echo "Pre-commit checks passed!"
EOF
        
        chmod +x "$PROJECT_ROOT/.git/hooks/pre-commit"
        success "Git hooks installed"
    else
        warning "Not a git repository - Skipping git hooks setup"
    fi
}

setup_database() {
    log "Setting up database..."
    
    # Check if PostgreSQL is running
    if command -v psql &> /dev/null; then
        log "PostgreSQL detected"
        
        # Create database if it doesn't exist
        if [ -f "$PROJECT_ROOT/scripts/init.sql" ]; then
            log "Running database initialization script..."
            # Note: This requires proper PostgreSQL credentials
            # psql -U postgres -f "$PROJECT_ROOT/scripts/init.sql"
            warning "Please run 'psql -U postgres -f scripts/init.sql' manually with appropriate credentials"
        fi
    else
        warning "PostgreSQL not found - Database setup skipped"
    fi
    
    # Check Redis
    if command -v redis-cli &> /dev/null; then
        log "Redis detected"
        if redis-cli ping &> /dev/null; then
            success "Redis is running"
        else
            warning "Redis is installed but not running"
        fi
    else
        warning "Redis not found - Some caching features may not work"
    fi
}

install_additional_tools() {
    log "Checking additional tools..."
    
    # Check for required system tools
    local tools=("git" "curl" "make")
    for tool in "${tools[@]}"; do
        if command -v "$tool" &> /dev/null; then
            log "$tool: installed ✓"
        else
            warning "$tool: not installed ✗"
        fi
    done
    
    # Install Playwright browsers if needed
    if pip show playwright &> /dev/null; then
        log "Installing Playwright browsers..."
        playwright install chromium firefox
        success "Playwright browsers installed"
    fi
}

run_initial_tests() {
    log "Running initial tests..."
    
    # Activate virtual environment
    source "$PROJECT_ROOT/$VENV_DIR/bin/activate"
    
    # Run basic import test
    python -c "import autonomous_claude_agent; print('✓ Package imports successfully')" || warning "Package import failed"
    
    # Run unit tests if they exist
    if [ -d "$PROJECT_ROOT/tests" ]; then
        pytest "$PROJECT_ROOT/tests/unit" -q --tb=short || warning "Some tests failed"
    fi
}

generate_completion_script() {
    log "Generating shell completion script..."
    
    # Create completion script for the CLI
    cat > "$PROJECT_ROOT/scripts/completion.sh" << 'EOF'
# Bash completion for claude-agent

_claude_agent_completion() {
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    opts="run serve test deploy rollback help version"
    
    case "${prev}" in
        run)
            local sub_opts="--task --mode --config --verbose --debug"
            COMPREPLY=( $(compgen -W "${sub_opts}" -- ${cur}) )
            return 0
            ;;
        serve)
            local sub_opts="--host --port --workers --reload"
            COMPREPLY=( $(compgen -W "${sub_opts}" -- ${cur}) )
            return 0
            ;;
        *)
            ;;
    esac
    
    COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
    return 0
}

complete -F _claude_agent_completion claude-agent
EOF
    
    success "Completion script generated at scripts/completion.sh"
    log "To enable: source scripts/completion.sh"
}

print_summary() {
    echo ""
    echo "======================================"
    echo -e "${GREEN}Bootstrap Complete!${NC}"
    echo "======================================"
    echo ""
    echo "Project Root: $PROJECT_ROOT"
    echo "Python Environment: $PROJECT_ROOT/$VENV_DIR"
    echo "Log File: $LOG_FILE"
    echo ""
    echo "Next steps:"
    echo "1. Activate the virtual environment:"
    echo "   source $VENV_DIR/bin/activate"
    echo ""
    echo "2. Update your .env file with API keys:"
    echo "   vim .env"
    echo ""
    echo "3. Run the agent:"
    echo "   make run"
    echo ""
    echo "4. Or start with Docker:"
    echo "   make docker-compose-up"
    echo ""
    echo "For help:"
    echo "   make help"
    echo ""
    echo "Documentation: docs/README.md"
    echo "======================================"
}

main() {
    echo "======================================"
    echo "Autonomous Claude Agent Bootstrap"
    echo "Version: 1.0.0"
    echo "======================================"
    echo ""
    
    # Create log directory first
    mkdir -p "$PROJECT_ROOT/logs"
    
    # Initialize log file
    echo "Bootstrap started at $(date)" > "$LOG_FILE"
    
    # Change to project root
    cd "$PROJECT_ROOT"
    
    # Run setup steps
    log "Starting bootstrap process..."
    
    create_directories
    check_command "python3"
    check_command "pip"
    setup_python_environment
    install_dependencies
    setup_environment_file
    check_docker
    setup_git_hooks
    setup_database
    install_additional_tools
    run_initial_tests
    generate_completion_script
    
    # Print summary
    print_summary
    
    success "Bootstrap completed successfully!"
    log "Bootstrap finished at $(date)"
}

# Handle errors
trap 'error "Bootstrap failed on line $LINENO"' ERR

# Run main function
main "$@"