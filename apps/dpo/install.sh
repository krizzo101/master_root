#!/bin/bash
#
# DPO System Installation Script
# Installs the Development Process Orchestrator and its dependencies
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Installation directories
DPO_HOME="${DPO_HOME:-$HOME/.dpo}"
VENV_DIR="${DPO_HOME}/venv"
CONFIG_DIR="${DPO_HOME}/config"
TEMPLATES_DIR="${DPO_HOME}/templates"
LOGS_DIR="${DPO_HOME}/logs"

# Print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Header
echo "==========================================="
echo "   DPO System Installation"
echo "==========================================="
echo ""

# Check Python version
print_info "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.8 or higher."
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    print_error "Python $REQUIRED_VERSION or higher is required. Found: $PYTHON_VERSION"
fi
print_success "Python $PYTHON_VERSION found"

# Create installation directories
print_info "Creating installation directories..."
mkdir -p "$DPO_HOME"
mkdir -p "$CONFIG_DIR"
mkdir -p "$TEMPLATES_DIR"
mkdir -p "$LOGS_DIR"
print_success "Directories created"

# Create virtual environment
print_info "Creating virtual environment..."
if [ -d "$VENV_DIR" ]; then
    print_warning "Virtual environment already exists. Skipping..."
else
    python3 -m venv "$VENV_DIR"
    print_success "Virtual environment created"
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Upgrade pip
print_info "Upgrading pip..."
pip install --upgrade pip wheel setuptools > /dev/null 2>&1
print_success "Pip upgraded"

# Install DPO package
print_info "Installing DPO system..."
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Install in development mode for easy updates
pip install -e . > /dev/null 2>&1
print_success "DPO system installed"

# Install additional dependencies
print_info "Installing additional dependencies..."
pip install -r requirements.txt > /dev/null 2>&1
print_success "Dependencies installed"

# Copy default configuration
print_info "Setting up configuration..."
if [ ! -f "$CONFIG_DIR/dpo_config.json" ]; then
    cp "$SCRIPT_DIR/config/default_config.json" "$CONFIG_DIR/dpo_config.json" 2>/dev/null || {
        # Create default config if template doesn't exist
        cat > "$CONFIG_DIR/dpo_config.json" << EOF
{
    "output_base_dir": "$HOME/dpo_output",
    "max_parallel_agents": 10,
    "enable_websocket": true,
    "websocket_port": 8765,
    "enable_dashboard": true,
    "enable_intelligence": true,
    "enable_context_injection": true,
    "auto_recovery": true,
    "checkpoint_interval": 300,
    "log_level": "INFO",
    "template_library_path": "$TEMPLATES_DIR",
    "knowledge_base_path": "$DPO_HOME/knowledge",
    "metrics_enabled": true
}
EOF
    }
    print_success "Configuration created"
else
    print_warning "Configuration already exists. Keeping existing settings."
fi

# Copy templates
print_info "Installing templates..."
if [ -d "$SCRIPT_DIR/templates" ]; then
    cp -r "$SCRIPT_DIR/templates/"* "$TEMPLATES_DIR/" 2>/dev/null || true
    print_success "Templates installed"
else
    print_warning "No templates found to install"
fi

# Create command line symlink
print_info "Setting up command line interface..."
INSTALL_DIR="/usr/local/bin"
if [ -w "$INSTALL_DIR" ]; then
    ln -sf "$VENV_DIR/bin/dpo" "$INSTALL_DIR/dpo"
    print_success "Command 'dpo' installed to $INSTALL_DIR"
else
    print_warning "Cannot write to $INSTALL_DIR. Adding to PATH instead."

    # Add to user's PATH
    SHELL_RC=""
    if [ -n "$BASH_VERSION" ]; then
        SHELL_RC="$HOME/.bashrc"
    elif [ -n "$ZSH_VERSION" ]; then
        SHELL_RC="$HOME/.zshrc"
    fi

    if [ -n "$SHELL_RC" ]; then
        echo "" >> "$SHELL_RC"
        echo "# DPO System" >> "$SHELL_RC"
        echo "export PATH=\"$VENV_DIR/bin:\$PATH\"" >> "$SHELL_RC"
        print_success "Added to PATH in $SHELL_RC"
        print_info "Please run: source $SHELL_RC"
    fi
fi

# Create bash completion
print_info "Setting up bash completion..."
cat > "$CONFIG_DIR/dpo_completion.bash" << 'EOF'
_dpo_completion() {
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"

    # Main commands
    opts="build status templates configure server dashboard metrics cancel results version --help"

    # Sub-commands for templates
    if [ "${COMP_WORDS[1]}" = "templates" ]; then
        opts="list show validate"
    fi

    # Options for build command
    if [ "${prev}" = "build" ]; then
        opts="--project-type --tech-stack --priority --output-dir --template --no-intelligence --dry-run --async-mode"
    fi

    COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
    return 0
}

complete -F _dpo_completion dpo
EOF

if [ -f "$HOME/.bashrc" ]; then
    echo "source $CONFIG_DIR/dpo_completion.bash" >> "$HOME/.bashrc"
    print_success "Bash completion installed"
fi

# Verify installation
print_info "Verifying installation..."
if "$VENV_DIR/bin/python" -c "import dpo" 2>/dev/null; then
    print_success "DPO modules verified"
else
    print_warning "DPO modules not fully installed"
fi

# Test CLI
if "$VENV_DIR/bin/dpo" --version > /dev/null 2>&1; then
    print_success "CLI verified"
else
    print_warning "CLI not fully functional"
fi

# Integration with master_root ecosystem
print_info "Checking master_root integration..."
if [ -d "/home/opsvi/master_root/apps/agent-orchestrator" ]; then
    print_success "Agent orchestrator found"

    # Create integration symlink
    ln -sf "/home/opsvi/master_root/apps/agent-orchestrator" "$DPO_HOME/orchestrator" 2>/dev/null || true
else
    print_warning "Agent orchestrator not found. Some features may be limited."
fi

# Check for MCP tools
if command -v mcp &> /dev/null; then
    print_success "MCP tools available"
else
    print_warning "MCP tools not found. Knowledge base features may be limited."
fi

# Summary
echo ""
echo "==========================================="
echo "   Installation Complete!"
echo "==========================================="
echo ""
echo "DPO has been installed to: $DPO_HOME"
echo ""
echo "To get started:"
echo "  1. Activate the environment: source $VENV_DIR/bin/activate"
echo "  2. Run a test: dpo build \"Create a simple web app\""
echo "  3. Check status: dpo status"
echo "  4. View help: dpo --help"
echo ""
echo "Configuration file: $CONFIG_DIR/dpo_config.json"
echo "Templates directory: $TEMPLATES_DIR"
echo "Logs directory: $LOGS_DIR"
echo ""

# Optional: Start server
read -p "Would you like to start the DPO server now? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_info "Starting DPO server..."
    "$VENV_DIR/bin/dpo" server &
    print_success "Server started in background (PID: $!)"
fi

print_success "Installation complete!"
