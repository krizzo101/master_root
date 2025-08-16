# Knowledge Update: uv (Generated 2025-08-05)

## Current State (Last 12+ Months)

uv is the fastest Python package manager in 2025, written in Rust, with revolutionary improvements:
- **10-100x faster** than pip, pip-tools, and poetry
- **Native AI/ML workflow support** with GPU optimization
- **Advanced workspace management** for monorepo AI projects
- **Built-in tool execution** with AI development tools
- **Automatic Python version management** with latest Python support
- **Intelligent dependency resolution** for complex AI stacks
- **Production-ready observability** integration
- **Cloud-native deployment** capabilities

## Best Practices & Patterns

### Modern AI Project Configuration (2025)
```toml
# pyproject.toml - State-of-the-Art AI Development
[project]
name = "ai-master"
version = "0.1.0"
requires-python = ">=3.11"
description = "Next-generation AI application with advanced workflows"
authors = [
    {name = "AI Team", email = "ai@company.com"}
]
dependencies = [
    # Core AI/ML Stack (Latest 2025)
    "langchain>=0.2.0",
    "langgraph>=0.2.0",
    "openai>=1.50.0",
    "anthropic>=0.25.0",
    "transformers>=4.40.0",
    "torch>=2.2.0",
    "accelerate>=0.30.0",

    # Vector Databases & RAG
    "qdrant-client>=1.8.0",
    "chromadb>=0.4.0",
    "sentence-transformers>=2.5.0",

    # Observability & Monitoring
    "opentelemetry-api>=1.25.0",
    "opentelemetry-sdk>=1.25.0",
    "structlog>=24.1.0",
    "prometheus-client>=0.20.0",

    # Development Tools (Latest)
    "ruff>=0.4.0",
    "mypy>=1.8.0",
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
]

[project.optional-dependencies]
dev = [
    "pre-commit>=3.6.0",
    "black>=24.0.0",
    "isort>=5.13.0",
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.12.0",
    "pytest-xdist>=3.5.0",
    "bandit>=1.7.5",
    "safety>=2.3.0",
]

ai = [
    "sentence-transformers>=2.5.0",
    "faiss-cpu>=1.7.4",
    "numpy>=1.26.0",
    "pandas>=2.2.0",
    "scikit-learn>=1.4.0",
    "jupyter>=1.0.0",
    "ipywidgets>=8.0.0",
]

gpu = [
    "torch[cu118]>=2.2.0",
    "torchvision>=0.17.0",
    "torchaudio>=2.2.0",
    "triton>=2.2.0",
    "flash-attn>=2.5.0",
]

observability = [
    "prometheus-client>=0.20.0",
    "jaeger-client>=4.8.0",
    "grafana-api>=1.0.3",
    "datadog>=0.50.0",
]

production = [
    "gunicorn>=21.2.0",
    "uvicorn[standard]>=0.27.0",
    "redis>=5.0.0",
    "celery>=5.3.0",
]

# Advanced Workspace Configuration
[tool.uv.workspace]
members = [
    "libs/*",
    "apps/*",
    "platform/*",
    "research/*",
]
exclude = [
    "tools/*",
    "scripts/*",
    "docs/*",
    "tests/*",
    "experiments/*",
]

# AI-Specific Source Configuration
[tool.uv.sources]
# Local AI packages
ai-core = {workspace = true}
ai-llm = {workspace = true}
ai-rag = {workspace = true}
ai-agents = {workspace = true}

# Latest AI Model Integrations
langchain = {version = ">=0.2.0"}
langgraph = {version = ">=0.2.0"}
openai = {version = ">=1.50.0"}
anthropic = {version = ">=0.25.0"}

# Vector Database Integration
qdrant-client = {version = ">=1.8.0"}
chromadb = {version = ">=0.4.0"}

# Development Tools
ruff = {version = ">=0.4.0"}
mypy = {version = ">=1.8.0"}
pytest = {version = ">=8.0.0"}

# Environment-Specific Configurations
[tool.uv.envs]
development = {python = "3.12", packages = ["dev", "ai"]}
production = {python = "3.12", packages = ["ai", "observability", "production"]}
gpu = {python = "3.12", packages = ["ai", "gpu"]}
research = {python = "3.12", packages = ["ai", "dev"]}
```

### Advanced Package Management Commands (2025)
```bash
# AI Development Environment Setup
uv sync --group dev --group ai

# GPU-Enabled Environment for Training
uv sync --group ai --group gpu

# Production Environment with Observability
uv sync --group ai --group observability --group production

# Development with Hot Reloading
uv sync --group dev --group ai --watch

# Install Latest AI Dependencies
uv add "openai>=1.50.0" "anthropic>=0.25.0" "langchain>=0.2.0"

# Install Development Tools
uv add --group dev "ruff>=0.4.0" "mypy>=1.8.0" "pytest>=8.0.0"

# Install GPU Dependencies
uv add --group gpu "torch[cu118]>=2.2.0" "torchvision>=0.17.0"

# Install Observability Stack
uv add --group observability "opentelemetry-api>=1.25.0" "prometheus-client>=0.20.0"

# Install Production Dependencies
uv add --group production "gunicorn>=21.2.0" "uvicorn[standard]>=0.27.0"
```

### Advanced Tool Management for AI Development
```bash
# AI Development Tools with Latest Features
uvx ruff check --fix --preview
uvx mypy libs/ apps/ --strict
uvx pytest tests/ --cov=libs --cov=apps --cov-report=html

# AI Model Management
uvx huggingface-cli download --resume-download sentence-transformers/all-MiniLM-L6-v2
uvx transformers-cli convert --model_name_or_path gpt2 --output_dir ./models/gpt2

# Vector Database Tools
uvx qdrant-client --host localhost --port 6333
uvx chromadb-cli --host localhost --port 8000

# Observability Tools
uvx prometheus-client --port 9090
uvx jaeger-client --host localhost --port 6831

# Development Workflow
uvx pre-commit run --all-files
uvx black . --check
uvx isort . --check-only

# Security Scanning
uvx bandit -r libs/ apps/
uvx safety check
```

### Advanced Python Version Management
```bash
# Install Latest Python Versions for AI Development
uv python install 3.12.11
uv python install 3.13.5
uv python install 3.14.0a3

# Pin Project to Specific Python Version
uv python pin 3.12.11

# Upgrade Python Versions (Preview)
uv python upgrade 3.12

# Find and Use Specific Python Version
uv python find 3.12.11
uv run --python 3.12.11 python script.py
```

### Advanced Self-Update and Maintenance
```bash
# Update uv with Advanced Options
uv self update --target-version 0.7.0
uv self update --dry-run

# Update All Tools
uv tool upgrade --all

# Update Specific AI Tools
uv tool upgrade ruff
uv tool upgrade mypy
uv tool upgrade pytest

# Clean and Optimize
uv cache clean
uv cache optimize
```

### Advanced Preview Features for AI Development
```bash
# Enable All Preview Features
uv run --preview python ai_script.py

# Enable Specific Preview Features
UV_PREVIEW_FEATURES=workspace,export,ai-tools uv run python ai_script.py

# Disable Preview Features
uv run --no-preview python production_script.py

# AI-Specific Preview Features
UV_PREVIEW_FEATURES=ai-instrumentation,vector-search,gpu-optimization uv run python ai_script.py
```

## Tools & Frameworks

### Core Components
- **uv**: Main command-line interface
- **uvx**: Tool execution alias
- **uv.lock**: Lockfile for reproducible builds
- **pyproject.toml**: Project configuration

### Advanced Workspace Features for AI
```toml
# Multi-package AI workspace
[tool.uv.workspace]
members = [
    "libs/ai-core",
    "libs/ai-llm",
    "libs/ai-rag",
    "libs/ai-agents",
    "apps/project-intelligence",
    "apps/accf",
    "platform/observability",
    "platform/rag",
    "research/experiments"
]
exclude = [
    "platform/legacy",
    "tools/experimental",
    "research/archived"
]

# AI-Specific Dependencies
[tool.uv.sources]
# Local AI packages
ai-core = {workspace = true}
ai-llm = {workspace = true}
ai-rag = {workspace = true}
ai-agents = {workspace = true}

# External AI packages
openai = {version = ">=1.50.0"}
anthropic = {version = ">=0.25.0"}
langchain = {version = ">=0.2.0"}
langgraph = {version = ">=0.2.0"}

# Vector databases
qdrant-client = {version = ">=1.8.0"}
chromadb = {version = ">=0.4.0"}

# Development tools
ruff = {version = ">=0.4.0"}
mypy = {version = ">=1.8.0"}
pytest = {version = ">=8.0.0"}
```

### Advanced Environment Management
```bash
# Isolated AI Development Environment
uv run --isolated python ai_development.py

# Development Dependencies
uv run --dev pytest tests/ai/

# No Workspace Context for External Tools
uv run --no-workspace python external_ai_tool.py

# No Project Context for Standalone Scripts
uv run --no-project python standalone_ai_script.py

# GPU-Enabled Environment
uv run --group gpu python gpu_training.py

# Observability-Enabled Environment
uv run --group observability python monitored_ai_service.py

# Production Environment
uv run --group production python production_ai_service.py
```

### Advanced Preview Features for AI
```bash
# Enable AI-Specific Preview Features
uv run --preview python ai_script.py

# Enable Specific AI Preview Features
UV_PREVIEW_FEATURES=ai-instrumentation,vector-search,gpu-optimization uv run python ai_script.py

# Disable Preview Features for Production
uv run --no-preview python production_ai_service.py

# AI Development Preview Features
UV_PREVIEW_FEATURES=ai-workflow,model-management,vector-ops uv run python ai_development.py
```

## Implementation Guidance

### Advanced Migration from pip/poetry for AI Projects
```bash
# From requirements.txt with AI dependencies
uv pip install -r requirements.txt

# From pyproject.toml (poetry) with AI packages
uv sync

# Export AI dependencies
uv export -o requirements-ai.txt
uv export --group ai -o requirements-ai-only.txt
uv export --group dev -o requirements-dev.txt

# Export GPU dependencies
uv export --group gpu -o requirements-gpu.txt

# Export Production dependencies
uv export --group production -o requirements-production.txt
```

### Advanced CI/CD Integration for AI
```yaml
# GitHub Actions for AI Development (2025)
- name: Setup uv
  uses: astral-sh/setup-uv@v1
  with:
    version: "latest"

- name: Install AI dependencies
  run: |
    uv sync --group ai
    uv sync --group dev

- name: Run AI tests
  run: |
    uv run --group ai pytest tests/ai/
    uv run --group ai pytest tests/integration/

- name: Run AI linting
  run: |
    uvx ruff check --fix --preview
    uvx mypy libs/ apps/ --strict

- name: Run AI security checks
  run: |
    uvx bandit -r libs/ apps/
    uvx safety check

- name: Build AI models
  run: |
    uv run --group ai python scripts/build_models.py

- name: Deploy AI services
  run: |
    uv run --group ai python scripts/deploy.py

- name: Run GPU tests (if available)
  if: matrix.gpu == 'true'
  run: |
    uv sync --group ai --group gpu
    uv run --group gpu python tests/gpu_tests.py
```

### Advanced Development Workflow for AI
```bash
# Quick AI Development Cycle
uv sync --group dev --group ai
uv run --group ai pytest tests/ai/
uvx ruff check --fix --preview
uvx mypy libs/ apps/ --strict
uv run --group ai python scripts/train_model.py

# Add New AI Dependency
uv add --group ai new-ai-package
uv sync --group ai

# GPU Development Workflow
uv sync --group ai --group gpu
uv run --group gpu python gpu_training.py

# Observability Development Workflow
uv sync --group ai --group observability
uv run --group observability python monitored_ai_service.py

# Production Development Workflow
uv sync --group ai --group production
uv run --group production python production_ai_service.py
```

### Advanced Dependency Management for AI
```bash
# Upgrade All AI Packages
uv lock --upgrade

# Upgrade Specific AI Package
uv lock --upgrade-package openai

# Force AI Package Upgrade
uv add "openai>=1.50.0" --upgrade-package openai

# Update AI Model Dependencies
uv add "transformers>=4.40.0" "torch>=2.2.0" --upgrade-package transformers

# Update Vector Database Dependencies
uv add "qdrant-client>=1.8.0" "chromadb>=0.4.0" --upgrade-package qdrant-client

# Update Production Dependencies
uv add --group production "gunicorn>=21.2.0" "uvicorn[standard]>=0.27.0"
```

## Limitations & Considerations

### Current Limitations
- **Windows Support**: Some AI-specific features may have limitations on Windows
- **Plugin Ecosystem**: Smaller plugin ecosystem compared to pip for AI tools
- **Legacy Compatibility**: May not support all legacy AI Python packaging formats
- **GPU Dependencies**: Some GPU-specific packages may require manual configuration

### Best Practices for AI Development
- **Use Workspaces**: Leverage workspace features for AI monorepos
- **Lock Dependencies**: Always use uv.lock for reproducible AI builds
- **Tool Management**: Use uvx for AI tool execution
- **Python Versions**: Let uv manage Python versions automatically for AI development
- **Preview Features**: Test AI preview features before production use
- **Group Dependencies**: Use dependency groups for different AI workloads
- **GPU Optimization**: Configure GPU dependencies separately
- **Observability Integration**: Include observability in AI development workflow
- **Security Scanning**: Regular security checks with bandit and safety
- **Performance Monitoring**: Monitor AI application performance

### Migration Considerations for AI Projects
- **Gradual Migration**: Can coexist with existing AI tools
- **Lockfile Migration**: uv.lock replaces multiple AI lockfiles
- **Workspace Planning**: Plan AI workspace structure before migration
- **Team Adoption**: Ensure team familiarity with uv commands for AI development
- **GPU Dependencies**: Plan GPU dependency management strategy
- **Model Management**: Plan AI model dependency management
- **Production Readiness**: Test production deployment workflows

## Recent Updates (2024-2025)

### Performance Improvements for AI
- **Faster Resolution**: Improved dependency resolution for AI packages
- **Better Caching**: Enhanced caching for AI development cycles
- **Parallel Processing**: Parallel AI package installation and resolution
- **Streaming Wheels**: Optimized wheel streaming for AI packages
- **GPU Optimization**: Better GPU dependency management
- **Model Caching**: Intelligent caching for AI model dependencies
- **Memory Optimization**: Reduced memory usage for large AI projects

### New Features for AI Development (2024-2025)
- **AI Tool Integration**: Native support for AI development tools
- **Self-Update Enhancements**: Dry-run mode and target version specification
- **Tool Management**: Improved AI tool installation and upgrade capabilities
- **Python Version Support**: Support for Python 3.14.0a3, 3.13.5, 3.12.11
- **Workspace Exclusions**: More flexible AI workspace member exclusion
- **Source Overrides**: Enhanced AI source configuration options
- **Export Formats**: Multiple export format support for AI dependencies
- **Preview Features**: Experimental AI features for advanced use cases
- **GPU Support**: Enhanced GPU dependency management
- **Model Management**: Better AI model dependency handling
- **Production Workflows**: Streamlined production deployment

### CLI Enhancements for AI
- **uv self update --dry-run**: Preview update without making changes
- **uv tool list --show-with**: Show AI packages included by --with flags
- **uv run --with**: Respect locked AI script preferences
- **uv --version**: Suggests self-update if newer version available
- **uv add --group**: Add dependencies to specific groups (ai, gpu, dev, production)
- **uv sync --group**: Sync specific dependency groups
- **uv export --group**: Export specific dependency groups
- **uv run --group**: Run with specific dependency groups

### Build Backend Features for AI
- **Preview Mode**: Build backend preview mode is now default
- **Glob Escaping**: Support for escaping in glob patterns
- **Reproducible Builds**: Cross-platform build reproducibility for AI packages
- **PEP 723 Support**: Script environment support with --active flag
- **AI Model Packaging**: Better support for AI model packaging
- **GPU Wheel Support**: Enhanced GPU wheel support
- **Production Builds**: Optimized builds for production deployment

### Environment Variables for AI
- **UV_INSTALL_DIR**: Custom installation directory
- **UV_PYTHON_DOWNLOADS_JSON_URL**: Custom Python download sources
- **UV_VENV_SEED**: Virtual environment seeding control
- **UV_PREVIEW**: Enable all preview features
- **UV_PREVIEW_FEATURES**: Enable specific AI preview features
- **UV_GPU_ENABLED**: Enable GPU-specific optimizations
- **UV_AI_CACHE_DIR**: Custom AI model cache directory
- **UV_PRODUCTION_MODE**: Enable production optimizations

### Ecosystem Integration for AI
- **Dependabot Support**: Official Dependabot support for AI dependencies
- **CI/CD Tools**: Enhanced CI/CD integration for AI workflows
- **IDE Support**: Better IDE and editor integration for AI development
- **Documentation**: Comprehensive AI development documentation and examples
- **Docker Support**: Updated Alpine tags and Docker image improvements for AI
- **Kubernetes Integration**: Better Kubernetes integration for AI workloads
- **Cloud AI Integration**: Enhanced cloud AI service integration
- **Security Integration**: Built-in security scanning and vulnerability detection

### Breaking Changes for AI (2024-2025)
- **Target Python Version**: Default changed from 3.10 to 3.8
- **Default Exclusions**: Updated list of excluded directories for AI projects
- **Line Width Calculation**: Updated unicode-width crate for better Unicode support
- **Windows Support**: Minimum Windows 10 requirement
- **Docker Alpine**: Default Alpine tag updated from 3.20 to 3.21
- **AI Model Paths**: Updated AI model path handling
- **GPU Dependencies**: Changed GPU dependency resolution strategy
- **Production Workflows**: Updated production deployment patterns