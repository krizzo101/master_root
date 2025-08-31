# Hecaton Build Specification
## Complete Build, Test, and Deployment Guide

---

## 📦 Project Configuration

### Current Build Files
```
apps/hecaton/
├── pyproject.toml         # Python project configuration
├── requirements.txt       # Direct dependencies
├── setup.py              # Package setup (if needed)
└── .env.example          # Environment variables template
```

---

## 🔧 Build Requirements

### Python Version
- **Required**: Python 3.9+
- **Recommended**: Python 3.11
- **Tested With**: Python 3.9, 3.10, 3.11

### Core Dependencies
```toml
# From pyproject.toml
[tool.poetry.dependencies]
python = "^3.9"
anthropic = "^0.18.0"
langchain = "^0.1.0"
langgraph = "^0.0.20"
asyncio = "^3.4.3"
pydantic = "^2.0.0"
aiofiles = "^23.0.0"
httpx = "^0.25.0"
```

### Development Dependencies
```toml
[tool.poetry.group.dev.dependencies]
pytest = "^7.4.0"
pytest-asyncio = "^0.21.0"
black = "^23.0.0"
isort = "^5.12.0"
flake8 = "^6.0.0"
mypy = "^1.5.0"
coverage = "^7.3.0"
```

---

## 🏗️ Build Process

### 1. Environment Setup
```bash
# Clone repository
git clone <repository-url>
cd apps/hecaton

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Or using poetry
poetry install
```

### 2. Configuration
```bash
# Copy environment template
cp .env.example .env

# Configure required variables
cat >> .env << EOF
# Claude API Configuration
CLAUDE_API_KEY=your-api-key-here
CLAUDE_API_URL=https://api.anthropic.com/v1

# Token Pool (for parallel execution)
CLAUDE_TOKEN_1=token-1
CLAUDE_TOKEN_2=token-2
CLAUDE_TOKEN_3=token-3

# Orchestration Settings
MAX_CONCURRENT_AGENTS=5
DEFAULT_TIMEOUT=300
RETRY_ATTEMPTS=3

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/hecaton.log
EOF
```

### 3. Build Commands
```bash
# Development build
make dev

# Production build
make build

# Clean build artifacts
make clean

# Full rebuild
make clean build
```

### 4. Makefile (Recommended)
```makefile
# Create this as apps/hecaton/Makefile
.PHONY: help dev build test clean install lint format

help:
	@echo "Available commands:"
	@echo "  make install  - Install dependencies"
	@echo "  make dev     - Development build"
	@echo "  make build   - Production build"
	@echo "  make test    - Run tests"
	@echo "  make lint    - Run linters"
	@echo "  make format  - Format code"
	@echo "  make clean   - Clean build artifacts"

install:
	pip install -r requirements.txt
	pip install -e .

dev: install
	pip install -r requirements-dev.txt
	pre-commit install

build:
	python -m build
	pip wheel . -w dist/

test:
	pytest tests/ -v --cov=hecaton --cov-report=html

lint:
	flake8 src/hecaton tests/
	mypy src/hecaton
	black --check src/hecaton tests/
	isort --check-only src/hecaton tests/

format:
	black src/hecaton tests/
	isort src/hecaton tests/

clean:
	rm -rf build/ dist/ *.egg-info
	find . -type d -name __pycache__ -rm -rf
	find . -type f -name "*.pyc" -delete
```

---

## 🧪 Testing Strategy

### Test Structure
```
tests/
├── unit/                  # Unit tests
│   ├── test_agents.py
│   ├── test_orchestrators.py
│   └── test_messages.py
├── integration/          # Integration tests
│   ├── test_agent_communication.py
│   └── test_end_to_end.py
├── performance/          # Performance tests
│   ├── test_throughput.py
│   └── test_latency.py
└── fixtures/            # Test fixtures
    └── mock_agents.py
```

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=hecaton --cov-report=html

# Run specific test file
pytest tests/unit/test_agents.py

# Run with verbose output
pytest -v

# Run performance tests only
pytest tests/performance/ -v

# Parallel test execution
pytest -n auto
```

### Test Configuration (`pytest.ini`)
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
markers =
    unit: Unit tests
    integration: Integration tests
    performance: Performance tests
    slow: Slow running tests
```

---

## 🚀 Deployment

### Docker Build
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src/ ./src/
COPY config/ ./config/

# Set environment variables
ENV PYTHONPATH=/app/src
ENV HECATON_ENV=production

# Run application
CMD ["python", "-m", "hecaton.main"]
```

### Build Docker Image
```bash
# Build image
docker build -t hecaton:latest .

# Run container
docker run -d \
  --name hecaton \
  -e CLAUDE_API_KEY=$CLAUDE_API_KEY \
  -v $(pwd)/logs:/app/logs \
  hecaton:latest

# Docker Compose (docker-compose.yml)
version: '3.8'
services:
  hecaton:
    build: .
    environment:
      - CLAUDE_API_KEY=${CLAUDE_API_KEY}
      - LOG_LEVEL=INFO
    volumes:
      - ./logs:/app/logs
      - ./config:/app/config
    restart: unless-stopped
```

---

## 📊 Performance Build Optimization

### Compile Python (Optional)
```bash
# Using Nuitka for compilation
pip install nuitka

# Compile main module
python -m nuitka --follow-imports --standalone src/hecaton/main.py

# Using Cython for critical paths
pip install cython
python setup.py build_ext --inplace
```

### Production Optimizations
```python
# In pyproject.toml
[tool.poetry.build]
generate-setup-file = true

[build-system]
requires = ["poetry-core>=1.0.0", "cython>=0.29"]
build-backend = "poetry.core.masonry.api"

# Enable optimizations
[tool.black]
line-length = 100
target-version = ['py311']

[tool.isort]
profile = "black"
line_length = 100
```

---

## 🔍 Quality Checks

### Pre-commit Hooks (`.pre-commit-config.yaml`)
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.0.0
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: ['--max-line-length=100']

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.5.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

### Security Scanning
```bash
# Install security tools
pip install safety bandit

# Check for vulnerable dependencies
safety check

# Scan for security issues
bandit -r src/hecaton/

# Check secrets
pip install detect-secrets
detect-secrets scan --all-files
```

---

## 📈 Performance Benchmarks

### Build Performance Targets
- **Build Time**: < 30 seconds
- **Test Suite**: < 2 minutes
- **Docker Image Size**: < 500MB
- **Startup Time**: < 5 seconds
- **Memory Usage**: < 512MB baseline

### Monitoring Build Health
```bash
# Check build size
du -sh dist/

# Profile import time
python -X importtime -c "import hecaton"

# Memory profiling
pip install memory-profiler
python -m memory_profiler src/hecaton/main.py
```

---

## 🔄 Continuous Integration

### GitHub Actions (`.github/workflows/build.yml`)
```yaml
name: Build and Test

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11]

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt

    - name: Lint
      run: |
        flake8 src/ tests/
        black --check src/ tests/

    - name: Test
      run: |
        pytest --cov=hecaton --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

---

## 📝 Release Process

### Version Management
```bash
# Using semantic versioning
# Update version in pyproject.toml
[tool.poetry]
version = "1.2.3"

# Tag release
git tag -a v1.2.3 -m "Release version 1.2.3"
git push origin v1.2.3

# Build release
python -m build
twine upload dist/*
```

---

*This build specification provides a complete guide for building, testing, and deploying the Hecaton multi-agent system.*
