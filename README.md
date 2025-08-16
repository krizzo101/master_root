# OPSVI Master Workspace

[![CI](https://github.com/opsvi/master-workspace/actions/workflows/ci.yml/badge.svg)](https://github.com/opsvi/master-workspace/actions/workflows/ci.yml)

A comprehensive monorepo for AI/ML Operations with built-in observability, RAG capabilities, and MCP integration. **Now featuring a complete foundational library ecosystem for production AI applications.**

## 🎯 Development Status

### ✅ Infrastructure Optimization (Complete)
- ✅ **Phase 1**: Linting & Type Checking (ruff, black, mypy)
- ✅ **Phase 2**: Testing Infrastructure (pytest, coverage)
- ✅ **Phase 3**: Integration Refactor (editable installs)
- ✅ **Phase 4**: Workflow Automation (pre-commit hooks)
- ✅ **Phase 5**: Documentation & README Updates

### 🚀 Library Ecosystem (Major Progress)
- ✅ **opsvi-core**: Complete foundation library with configuration, logging, exceptions, and base patterns
- ✅ **opsvi-llm**: Complete LLM integration with multi-provider support, function calling, and rate limiting
- 🔄 **opsvi-rag**: Vector storage foundation with Qdrant integration (providers and retrieval pending)
- ⏳ **opsvi-agents**: Multi-agent orchestration framework (planned)

### 📚 Knowledge Management (New)
- ✅ **2025 Technology Updates**: Comprehensive knowledge base with latest patterns for LangChain, OpenAI, Qdrant, etc.
- ✅ **Architecture Intelligence**: Project analysis and mapping for informed development decisions

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
│   ├── opsvi-core/         # ✅ Core utilities (config, logging, patterns, exceptions)
│   ├── opsvi-llm/          # ✅ LLM integration (OpenAI, Anthropic, rate limiting, function calling)
│   ├── opsvi-rag/          # 🔄 RAG utilities (Qdrant vector store, embedding providers, retrieval)
│   └── opsvi-agents/       # ⏳ Agent framework (multi-agent orchestration)
├── knowledge/               # 📚 Technology knowledge base (2025 updates)
├── intake/                  # Incoming projects (reference implementations)
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

## 🔍 Library Ecosystem

### opsvi-core (Production Ready)
- **Configuration**: Type-safe config with Pydantic V2 and environment variables
- **Logging**: Structured logging with Structlog and OpenTelemetry integration
- **Patterns**: BaseActor and BaseAgent with async lifecycle management
- **Exceptions**: Comprehensive error hierarchy for robust error handling
- **Testing**: 28 tests with 84% coverage

### opsvi-llm (Production Ready)
- **Multi-Provider**: Unified interface for OpenAI and Anthropic APIs
- **Function Calling**: Structured function calling with type safety
- **Rate Limiting**: Token bucket and sliding window rate limiters
- **Retry Logic**: Exponential backoff with configurable parameters
- **Streaming**: Real-time response streaming support
- **Testing**: 20 tests with 46% coverage

### opsvi-rag (Foundation Complete)
- **Vector Storage**: Async Qdrant client with collection management
- **Next Phase**: Embedding providers (OpenAI, Sentence Transformers)
- **Planned**: Document processors and retrieval engines

## 📚 Knowledge Base

The `/knowledge/` directory contains 2025 technology updates including:
- **LangChain**: Latest patterns and best practices
- **LangGraph**: State management and agent workflows
- **OpenAI**: Function calling and structured outputs
- **Qdrant**: Vector database optimization
- **Modern Python**: UV, Ruff, Pydantic V2, async patterns

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

## 🛣️ Roadmap

### Immediate (Current Sprint)
- **opsvi-rag completion**: Embedding providers and document processors
- **opsvi-rag retrieval**: Semantic search and RAG pipeline implementation

### Next Phase
- **opsvi-agents**: Multi-agent orchestration framework leveraging agent_world patterns
- **Integration testing**: Cross-library integration and performance testing
- **Documentation**: Comprehensive API docs and usage guides

### Future
- **Advanced RAG**: Multi-modal document processing and hybrid search
- **Agent Workflows**: LangGraph integration for complex agent orchestration
- **Observability**: Enhanced monitoring and debugging tools

## 🤝 Contributing

1. Create a worktree for your feature: `./scripts/new_agent_worktree.sh feature-name`
2. Review project intelligence: Analyze `.proj-intel/` and `knowledge/` directories
3. Make changes following modern Python patterns (async, type hints, Pydantic V2)
4. Pre-commit hooks will run automatically (ruff, black, mypy)
5. Run tests: `just test` or `uv run pytest`
6. Create a PR to merge into MAIN

## 📄 License

MIT License - see LICENSE file for details.