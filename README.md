# OPSVI Master Workspace

[![CI](https://github.com/opsvi/master-workspace/actions/workflows/ci.yml/badge.svg)](https://github.com/opsvi/master-workspace/actions/workflows/ci.yml)

A comprehensive monorepo for AI/ML Operations with built-in observability, RAG capabilities, and MCP integration.

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
├── apps/                    # Applications
│   └── project-intel/       # Project intelligence app
├── libs/                    # Shared libraries
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
└── docs/                   # Documentation
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

## 🔧 Configuration

### Environment Variables

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

## 🤝 Contributing

1. Create a worktree for your feature
2. Make changes and commit to your branch
3. Run tests and linting
4. Create a PR to merge into MAIN

## 📄 License

MIT License - see LICENSE file for details.