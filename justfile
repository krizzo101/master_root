# OPSVI Master Workspace Justfile
# Usage: just <task>

# Default task
default:
    @just --list

# Sync dependencies
sync:
    uv sync

# Format code
fmt:
    uv run ruff format .
    uv run black .

# Lint code
lint:
    uv run ruff check .
    uv run mypy .

# Run tests
test:
    uv run pytest

# Run tests with coverage
test-cov:
    uv run pytest --cov=libs --cov=apps --cov-report=html

# Start observability stack
up-obs:
    cd platform/observability && docker-compose up -d

# Stop observability stack
down-obs:
    cd platform/observability && docker-compose down

# Start RAG stack
up-rag:
    cd platform/rag && docker-compose up -d

# Stop RAG stack
down-rag:
    cd platform/rag && docker-compose down

# Start all platform services
up:
    just up-obs
    just up-rag

# Stop all platform services
down:
    just down-obs
    just down-rag

# Initialize RAG system
init-rag:
    uv run python tools/rag_init.py

# Create new agent worktree
worktree name:
    ./scripts/new_agent_worktree.sh {{name}}

# Run autosave
autosave:
    ./tools/autosave.sh

# Run snapshot
snapshot:
    ./tools/snapshot.sh

# Build all packages
build:
    uv build

# Clean build artifacts
clean:
    rm -rf dist/
    rm -rf build/
    rm -rf *.egg-info/
    find . -type d -name __pycache__ -delete
    find . -type f -name "*.pyc" -delete

# Install systemd services
install-systemd:
    cp systemd/*.service ~/.config/systemd/user/
    cp systemd/*.timer ~/.config/systemd/user/
    systemctl --user daemon-reload

# Enable systemd services
enable-systemd:
    systemctl --user enable autosave@opsvi.timer
    systemctl --user enable snapshot@opsvi.timer

# Start systemd services
start-systemd:
    systemctl --user start autosave@opsvi.timer
    systemctl --user start snapshot@opsvi.timer

# Demo setup
demo:
    @echo "🚀 Setting up OPSVI demo environment..."
    just sync
    just up
    sleep 10
    just init-rag
    @echo "✅ Demo environment ready!"
    @echo "📊 Grafana: http://localhost:3000 (admin/admin)"
    @echo "🔍 Qdrant UI: http://localhost:8080"
    @echo "📈 Tempo: http://localhost:3200"

# Show status
status:
    @echo "📊 Platform Services:"
    docker-compose -f platform/observability/docker-compose.yml ps
    docker-compose -f platform/rag/docker-compose.yml ps
    @echo ""
    @echo "🔄 Systemd Services:"
    systemctl --user status autosave@opsvi.timer snapshot@opsvi.timer --no-pager -l
    @echo ""
    @echo "📁 Git Status:"
    git status --short
    @echo ""
    @echo "🌿 Current Branch:"
    git branch --show-current

# Quick development workflow
dev:
    just fmt
    just lint
    just test

# Run pre-commit hooks
hooks:
    pre-commit run --all-files

# Check for security issues
security:
    uv run bandit -r libs/ apps/

# Update dependencies
update:
    uv lock --upgrade
    uv sync

# Show dependency tree
deps:
    uv tree

# Check for outdated packages
outdated:
    uv pip list --outdated

# Help
help:
    @echo "OPSVI Master Workspace Commands:"
    @echo ""
    @echo "Development:"
    @echo "  just sync      - Sync dependencies"
    @echo "  just fmt       - Format code"
    @echo "  just lint      - Lint code"
    @echo "  just test      - Run tests"
    @echo "  just dev       - Format, lint, and test"
    @echo "  just build     - Build packages"
    @echo "  just security  - Security audit"
    @echo "  just update    - Update dependencies"
    @echo "  just deps      - Show dependency tree"
    @echo "  just outdated  - Check outdated packages"
    @echo ""
    @echo "Platform:"
    @echo "  just up        - Start all services"
    @echo "  just down      - Stop all services"
    @echo "  just up-obs    - Start observability"
    @echo "  just up-rag    - Start RAG system"
    @echo "  just init-rag  - Initialize RAG"
    @echo ""
    @echo "Git & Automation:"
    @echo "  just worktree <name> - Create worktree"
    @echo "  just autosave  - Run autosave"
    @echo "  just snapshot  - Run snapshot"
    @echo ""
    @echo "Systemd:"
    @echo "  just install-systemd - Install services"
    @echo "  just enable-systemd  - Enable services"
    @echo "  just start-systemd   - Start services"
    @echo ""
    @echo "Demo:"
    @echo "  just demo      - Setup demo environment"
    @echo "  just status    - Show system status"