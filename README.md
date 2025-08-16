# OPSVI Master Workspace

[![CI](https://github.com/opsvi/master-workspace/actions/workflows/ci.yml/badge.svg)](https://github.com/opsvi/master-workspace/actions/workflows/ci.yml)

A comprehensive monorepo for AI/ML Operations with built-in observability, RAG capabilities, and MCP integration.

## 🎯 Workspace Optimization Status

This workspace has been optimized with:
- ✅ **Phase 1**: Linting & Type Checking (ruff, black, mypy)
- ✅ **Phase 2**: Testing Infrastructure (pytest, coverage)
- ✅ **Phase 3**: Integration Refactor (editable installs)
- ✅ **Phase 4**: Workflow Automation (pre-commit hooks)
- ✅ **Phase 5**: Documentation & README Updates

## 🚀 Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd master_root

# Setup the workspace
uv sync

# Initialize RAG system
uv run project-intel init-rag

# Start observability stack
cd platform/observability
docker-compose up -d

# Start RAG stack
cd ../rag
docker-compose up -d
```

## 📁 Project Structure

```
master_root/
├── apps/                    # External applications (symlinked)
│   ├── ACCF/               # AI/ML capabilities framework
│   ├── genFileMap/         # File mapping and analysis
│   └── project-intelligence/ # Project intelligence system
├── libs/                    # Shared libraries (editable installs)
│   ├── opsvi-core/         # Core utilities
│   ├── opsvi-rag/          # RAG utilities
│   ├── opsvi-llm/          # LLM integration
│   └── opsvi-agents/       # Agent framework
├── platform/               # Platform services
│   ├── observability/      # Grafana, Tempo, OTEL
│   ├── rag/               # Qdrant vector DB
│   └── mcp/               # MCP registry
├── tools/                  # Development tools
├── scripts/                # Utility scripts
├── systemd/                # Systemd services
├── docs/                   # Documentation
├── intake/                 # Incoming projects (excluded from tooling)
└── .archive/               # Archived content (excluded from tooling)
```

## 🛠️ Development

### Git Workflow

- **MAIN**: Protected branch for stable releases
- **AUTOSAVE**: Automatic commits every 10 minutes
- **Worktrees**: Use `scripts/new_agent_worktree.sh` for feature development

### Commands

```bash
# Create new agent worktree
./scripts/new_agent_worktree.sh my-agent

# Run tests
uv run pytest

# Format code
uv run ruff format
uv run black .

# Lint code
uv run ruff check
uv run mypy .

# Build packages
uv build

# Run pre-commit hooks manually
just hooks

# Quick development workflow (format, lint, test)
just dev
```

### Systemd Services

```bash
# Enable autosave (every 10 minutes)
systemctl --user enable autosave@opsvi.timer

# Enable snapshots (every 12 hours)
systemctl --user enable snapshot@opsvi.timer

# Start services
systemctl --user start autosave@opsvi.timer snapshot@opsvi.timer
```

## 🛠️ Quality & Development Tools

### Pre-commit Hooks

This workspace uses pre-commit hooks to ensure code quality:

```bash
# Install pre-commit hooks (done automatically)
pre-commit install

# Run hooks manually
pre-commit run --all-files

# Run via justfile
just hooks
```

**Hooks included:**
- **ruff**: Fast Python linter and formatter
- **black**: Code formatting
- **mypy**: Static type checking

### Justfile Commands

The workspace includes a comprehensive `justfile` with development commands:

```bash
# Show all available commands
just

# Quick development workflow
just dev

# Run pre-commit hooks
just hooks

# Platform management
just up          # Start all services
just down        # Stop all services
just status      # Show system status

# Testing and quality
just test        # Run tests
just test-cov    # Run tests with coverage
just lint        # Run linting
just fmt         # Run formatting
```

## 🔧 Configuration

Create a `.env` file in the root directory:

```bash
OPSVI_APP_NAME=opsvi-master
OPSVI_ENVIRONMENT=development
OPSVI_DEBUG=true
OPSVI_LOG_LEVEL=INFO
```

### MCP Registry

Configure MCP registry in `platform/mcp/registry.json`:

```json
{
  "name": "opsvi-mcp",
  "url": "${MCP_REGISTRY_URL}",
  "auth": {
    "username": "${MCP_USERNAME}",
    "password": "${MCP_PASSWORD}"
  }
}
```

## 📊 Observability

Access the observability stack at:
- **Grafana**: http://localhost:3000
- **Tempo**: http://localhost:3200
- **OTEL Collector**: http://localhost:4318

## 🔍 RAG System

The RAG system uses Qdrant for vector storage and provides:
- Document ingestion and embedding
- Semantic search capabilities
- Collection management

## 🔄 Workspace Optimization Details

### Phase 1: Linting & Type Checking
- **ruff**: Fast Python linter with auto-fix capabilities
- **black**: Consistent code formatting
- **mypy**: Static type checking with strict configuration
- **Configuration**: `.ruff.toml`, `mypy.ini` with proper exclusions

### Phase 2: Testing Infrastructure
- **pytest**: Comprehensive test framework
- **Coverage**: HTML coverage reports
- **Configuration**: `pytest.ini` with proper test discovery
- **CI/CD**: GitHub Actions workflow for automated testing

### Phase 3: Integration Refactor
- **Editable Installs**: All `libs/` packages installed in editable mode
- **Clean Imports**: Proper import paths without symlink dependencies
- **Package Structure**: Standardized Python package layout

### Phase 4: Workflow Automation
- **Pre-commit Hooks**: Automatic quality checks on commit
- **Justfile Integration**: `just hooks` command for manual execution
- **Exclusion Patterns**: Proper handling of external/archive directories

### Phase 5: Documentation Updates
- **README Updates**: Comprehensive documentation of new tools and processes
- **Workflow Documentation**: Clear development workflow instructions

## 🤝 Contributing

1. Create a worktree for your feature
2. Make changes and commit to your branch
3. Pre-commit hooks will run automatically
4. Run tests: `just test`
5. Create a PR to merge into MAIN

## 📄 License

MIT License - see LICENSE file for details.