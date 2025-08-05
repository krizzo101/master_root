# Development Workflow

This document outlines the development workflow for the OPSVI Master Workspace.

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- `uv` package manager
- Docker and Docker Compose
- Git

### Initial Setup

```bash
# Clone the repository
git clone <repository-url>
cd master_root

# Install dependencies
uv sync

# Install pre-commit hooks
pre-commit install
```

## 🛠️ Development Workflow

### 1. Create a Worktree

Always use worktrees for feature development:

```bash
# Create a new worktree
./scripts/new_agent_worktree.sh my-feature

# Switch to the worktree
cd /home/opsvi/_worktrees/my-feature
```

### 2. Make Changes

Follow the coding standards:

- Use type hints for all functions
- Follow PEP 8 style guidelines
- Write docstrings for all public functions
- Keep functions small and focused

### 3. Quality Checks

The workspace has automated quality checks:

```bash
# Run all quality checks
just dev

# Or run individually:
just fmt    # Format code
just lint   # Lint code
just test   # Run tests
just hooks  # Run pre-commit hooks
```

### 4. Commit Changes

Pre-commit hooks run automatically:

```bash
git add .
git commit -m "feat: add new feature"
# Pre-commit hooks run automatically
```

### 5. Push and Create PR

```bash
git push origin my-feature
# Create PR to merge into MAIN
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
just test

# Run with coverage
just test-cov

# Run specific test file
uv run pytest tests/opsvi_core/test_logging.py

# Run with verbose output
uv run pytest -v
```

### Test Structure

- `tests/`: Test files
- `tests/opsvi_core/`: Tests for opsvi-core library
- `tests/opsvi_rag/`: Tests for opsvi-rag library
- `tests/opsvi_llm/`: Tests for opsvi-llm library
- `tests/opsvi_agents/`: Tests for opsvi-agents library

## 🔍 Code Quality Tools

### Ruff (Linter)

Fast Python linter with auto-fix capabilities:

```bash
# Check for issues
uv run ruff check .

# Fix auto-fixable issues
uv run ruff check --fix .

# Format code
uv run ruff format .
```

### Black (Formatter)

Consistent code formatting:

```bash
# Format code
uv run black .

# Check formatting without changes
uv run black --check .
```

### MyPy (Type Checker)

Static type checking:

```bash
# Run type checking
uv run mypy .

# Check specific file
uv run mypy libs/opsvi-core/src/opsvi_core/
```

## 📦 Package Management

### Library Structure

The workspace uses editable installs for development:

```bash
# Install all libraries in editable mode
uv pip install -e libs/opsvi-core/
uv pip install -e libs/opsvi-rag/
uv pip install -e libs/opsvi-llm/
uv pip install -e libs/opsvi-agents/
```

### Adding Dependencies

```bash
# Add to pyproject.toml
uv add package-name

# Add development dependency
uv add --dev package-name
```

## 🔧 Configuration Files

### Pre-commit Configuration

`.pre-commit-config.yaml`:
- ruff: Linting and formatting
- black: Code formatting
- mypy: Type checking
- Excludes external/archive directories

### Ruff Configuration

`.ruff.toml`:
- Line length: 88 characters
- Target Python: 3.12
- Strict linting rules

### MyPy Configuration

`mypy.ini`:
- Strict type checking
- Excludes external directories
- Ignores missing imports for external dependencies

### Pytest Configuration

`pytest.ini`:
- Test discovery in `tests/` and `libs/`
- Excludes external directories
- Coverage reporting

## 🚀 Platform Services

### Starting Services

```bash
# Start all services
just up

# Start individual services
just up-obs  # Observability stack
just up-rag  # RAG system

# Check status
just status
```

### Development Environment

```bash
# Setup demo environment
just demo

# This will:
# 1. Sync dependencies
# 2. Start all services
# 3. Initialize RAG system
# 4. Display access URLs
```

## 🔄 Git Workflow

### Branch Protection

- **MAIN**: Protected branch, requires PR review
- **AUTOSAVE**: Automatic commits every 10 minutes
- **Feature branches**: Use worktrees for development

### Commit Messages

Use conventional commit messages:

```
feat: add new feature
fix: fix bug in existing feature
docs: update documentation
style: format code
refactor: refactor existing code
test: add or update tests
chore: maintenance tasks
```

### Worktree Management

```bash
# List worktrees
git worktree list

# Remove worktree when done
git worktree remove /path/to/worktree
```

## 🐛 Troubleshooting

### Common Issues

1. **Pre-commit hooks failing**:
   ```bash
   # Run hooks manually to see errors
   pre-commit run --all-files

   # Fix issues and try again
   just fmt
   just lint
   ```

2. **Import errors**:
   ```bash
   # Reinstall libraries in editable mode
   uv pip install -e libs/opsvi-core/
   ```

3. **Test failures**:
   ```bash
   # Run tests with verbose output
   uv run pytest -v

   # Run specific failing test
   uv run pytest tests/path/to/test.py::test_function
   ```

### Getting Help

- Check the logs in `docs/status/` for recent workspace status
- Review the justfile for available commands: `just --list`
- Check pre-commit hook output for specific errors

## 📚 Additional Resources

- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [Black Documentation](https://black.readthedocs.io/)
- [MyPy Documentation](https://mypy.readthedocs.io/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Pre-commit Documentation](https://pre-commit.com/)