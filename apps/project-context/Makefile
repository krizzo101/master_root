# Makefile for Unified Context System Testing

.PHONY: help install test test-unit test-integration test-e2e test-performance test-all
.PHONY: test-adapters test-database test-correlation test-pipeline
.PHONY: coverage lint format type-check security-scan clean setup-dev
.PHONY: test-watch test-debug test-specific test-ci

# Default target
help: ## Show this help message
	@echo "Unified Context System - Test Commands"
	@echo "======================================"
	@echo ""
	@echo "Setup Commands:"
	@echo "  install          Install all dependencies"
	@echo "  setup-dev        Setup development environment"
	@echo ""
	@echo "Test Commands:"
	@echo "  test            Run all standard tests (unit + integration + adapters)"
	@echo "  test-all        Run all tests including e2e and performance"
	@echo "  test-unit       Run unit tests only (fast)"
	@echo "  test-integration Run integration tests"
	@echo "  test-e2e        Run end-to-end tests"
	@echo "  test-performance Run performance tests"
	@echo "  test-adapters   Run all adapter tests"
	@echo "  test-database   Run database schema tests"
	@echo "  test-correlation Run cross-adapter correlation tests"
	@echo "  test-pipeline   Run pipeline integration tests"
	@echo ""
	@echo "Development Commands:"
	@echo "  test-watch      Run tests in watch mode"
	@echo "  test-debug      Run tests with debug output"
	@echo "  coverage        Generate coverage report"
	@echo "  lint            Run code linting"
	@echo "  format          Format code"
	@echo "  type-check      Run type checking"
	@echo "  security-scan   Run security scanning"
	@echo "  clean           Clean test artifacts"
	@echo ""
	@echo "CI/CD Commands:"
	@echo "  test-ci         Run CI test suite"
	@echo ""
	@echo "Variables:"
	@echo "  TEST_CATEGORY   Specific test category to run"
	@echo "  TEST_FILE       Specific test file to run"
	@echo "  TEST_PATTERN    Test pattern to match"
	@echo "  VERBOSE         Enable verbose output (1 for yes)"
	@echo ""
	@echo "Examples:"
	@echo "  make test-unit VERBOSE=1"
	@echo "  make test-specific TEST_FILE=tests/test_git_adapter_unit.py"
	@echo "  make test TEST_PATTERN='test_commit*'"

# Variables
PYTHON := python3
PIP := pip3
TEST_RUNNER := $(PYTHON) scripts/run_tests.py
PYTEST := $(PYTHON) -m pytest
PROJECT_ROOT := $(shell pwd)
TEST_REPORTS_DIR := test_reports

# Conditional variables
ifdef VERBOSE
    VERBOSE_FLAG := --verbose
endif

ifdef TEST_PATTERN
    PATTERN_FLAG := -k $(TEST_PATTERN)
endif

# Installation and setup
install: ## Install all dependencies
	@echo "📦 Installing dependencies..."
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PIP) install -r requirements-test.txt
	$(PIP) install -e .
	@echo "✅ Dependencies installed"

setup-dev: install ## Setup development environment
	@echo "🔧 Setting up development environment..."
	$(PIP) install pre-commit black isort flake8 mypy bandit safety
	pre-commit install || echo "pre-commit not available"
	mkdir -p $(TEST_REPORTS_DIR)
	@echo "✅ Development environment ready"

# Core test commands
test: test-unit test-adapters test-integration ## Run standard test suite (unit + adapters + integration)

test-all: ## Run all tests including e2e and performance
	@echo "🚀 Running all test categories..."
	$(TEST_RUNNER) --all --coverage $(VERBOSE_FLAG)

test-unit: ## Run unit tests
	@echo "⚡ Running unit tests..."
	$(TEST_RUNNER) --category unit --coverage $(VERBOSE_FLAG)

test-integration: ## Run integration tests
	@echo "🔗 Running integration tests..."
	$(TEST_RUNNER) --category integration --coverage $(VERBOSE_FLAG)

test-e2e: ## Run end-to-end tests
	@echo "🎯 Running end-to-end tests..."
	$(TEST_RUNNER) --category e2e $(VERBOSE_FLAG)

test-performance: ## Run performance tests
	@echo "📈 Running performance tests..."
	$(TEST_RUNNER) --category performance $(VERBOSE_FLAG)

test-adapters: ## Run all adapter tests
	@echo "🔌 Running adapter tests..."
	$(TEST_RUNNER) --category adapters --coverage $(VERBOSE_FLAG)

test-database: ## Run database schema tests
	@echo "🗄️  Running database tests..."
	$(TEST_RUNNER) --category database $(VERBOSE_FLAG)

test-correlation: ## Run cross-adapter correlation tests
	@echo "🔀 Running correlation tests..."
	$(TEST_RUNNER) --category correlation $(VERBOSE_FLAG)

test-pipeline: ## Run pipeline integration tests
	@echo "🏗️  Running pipeline tests..."
	$(TEST_RUNNER) --category pipeline $(VERBOSE_FLAG)

# Specific adapter tests
test-git: ## Run Git adapter tests
	@echo "📝 Running Git adapter tests..."
	$(PYTEST) tests/ -m git_adapter $(VERBOSE_FLAG) $(PATTERN_FLAG)

test-error: ## Run Error adapter tests
	@echo "⚠️  Running Error adapter tests..."
	$(PYTEST) tests/ -m error_adapter $(VERBOSE_FLAG) $(PATTERN_FLAG)

test-cicd: ## Run CI/CD adapter tests
	@echo "🏃 Running CI/CD adapter tests..."
	$(PYTEST) tests/ -m cicd_adapter $(VERBOSE_FLAG) $(PATTERN_FLAG)

# Development and debugging
test-watch: ## Run tests in watch mode
	@echo "👀 Running tests in watch mode..."
	$(PYTEST) tests/ --looponfail $(VERBOSE_FLAG) $(PATTERN_FLAG)

test-debug: ## Run tests with debug output
	@echo "🐛 Running tests with debug output..."
	$(PYTEST) tests/ -s -vv --tb=long --capture=no $(PATTERN_FLAG)

test-specific: ## Run specific test file or pattern
	@if [ -n "$(TEST_FILE)" ]; then \
		echo "🎯 Running specific test file: $(TEST_FILE)"; \
		$(TEST_RUNNER) --test $(TEST_FILE) $(VERBOSE_FLAG); \
	elif [ -n "$(TEST_CATEGORY)" ]; then \
		echo "🎯 Running test category: $(TEST_CATEGORY)"; \
		$(TEST_RUNNER) --category $(TEST_CATEGORY) $(VERBOSE_FLAG); \
	else \
		echo "❌ Please specify TEST_FILE or TEST_CATEGORY"; \
		echo "   Example: make test-specific TEST_FILE=tests/test_git_adapter_unit.py"; \
		echo "   Example: make test-specific TEST_CATEGORY=unit"; \
		exit 1; \
	fi

# Coverage and reporting
coverage: ## Generate detailed coverage report
	@echo "📊 Generating coverage report..."
	$(PYTEST) tests/ --cov=src/project_context --cov-report=html --cov-report=term-missing --cov-report=xml
	@echo "📋 Coverage report generated in htmlcov/"

coverage-unit: ## Generate coverage for unit tests only
	@echo "📊 Generating unit test coverage..."
	$(PYTEST) tests/ -m unit --cov=src/project_context --cov-report=html:htmlcov-unit --cov-report=term-missing

# Code quality
lint: ## Run code linting
	@echo "🔍 Running code linting..."
	flake8 src/ tests/ --max-line-length=100 --extend-ignore=E203,W503
	@echo "✅ Linting completed"

format: ## Format code
	@echo "✨ Formatting code..."
	black src/ tests/ scripts/
	isort src/ tests/ scripts/
	@echo "✅ Code formatted"

format-check: ## Check code formatting
	@echo "🔍 Checking code formatting..."
	black --check src/ tests/ scripts/
	isort --check-only src/ tests/ scripts/
	@echo "✅ Format check completed"

type-check: ## Run type checking
	@echo "🔍 Running type checking..."
	mypy src/ --ignore-missing-imports || echo "⚠️  Type checking completed with warnings"

security-scan: ## Run security scanning
	@echo "🔒 Running security scan..."
	bandit -r src/ -f json -o bandit-report.json || echo "⚠️  Security scan completed with warnings"
	safety check --json --output safety-report.json || echo "⚠️  Safety check completed with warnings"
	@echo "✅ Security scan completed"

# CI/CD commands
test-ci: ## Run CI test suite
	@echo "🤖 Running CI test suite..."
	$(TEST_RUNNER) --all --coverage --fail-fast

test-pr: test-unit test-adapters test-integration ## Run PR validation tests

# Utility commands
clean: ## Clean test artifacts and cache
	@echo "🧹 Cleaning test artifacts..."
	rm -rf $(TEST_REPORTS_DIR)/
	rm -rf htmlcov/
	rm -rf htmlcov-*/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf src/project_context/__pycache__/
	rm -rf tests/__pycache__/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage.*" -delete
	rm -f bandit-report.json safety-report.json
	@echo "✅ Cleanup completed"

list-tests: ## List all available tests
	@echo "📋 Available tests:"
	$(PYTEST) --collect-only -q tests/

check-deps: ## Check test dependencies
	@echo "🔍 Checking test dependencies..."
	$(PYTHON) -c "import pytest; print('✅ pytest:', pytest.__version__)"
	$(PYTHON) -c "import pytest_asyncio; print('✅ pytest-asyncio installed')"
	$(PYTHON) -c "import pytest_cov; print('✅ pytest-cov installed')"
	$(PYTHON) -c "import pytest_html; print('✅ pytest-html installed')"
	@echo "✅ All test dependencies available"

# Performance benchmarking
benchmark: ## Run performance benchmarks
	@echo "🏃 Running performance benchmarks..."
	$(PYTEST) tests/test_performance_load.py -m performance --benchmark-only $(VERBOSE_FLAG)

benchmark-compare: ## Compare performance benchmarks
	@echo "📊 Comparing performance benchmarks..."
	$(PYTEST) tests/test_performance_load.py -m performance --benchmark-compare $(VERBOSE_FLAG)

# Database specific commands
test-db-schema: ## Test database schema validation
	@echo "🗄️  Testing database schema..."
	$(PYTEST) tests/test_database_schema.py $(VERBOSE_FLAG)

test-db-real: ## Run tests with real database (requires TEST_REAL_DB=true)
	@echo "🗄️  Running tests with real database..."
	TEST_REAL_DB=true $(PYTEST) tests/ -m real_db $(VERBOSE_FLAG)

# Docker-based testing
test-docker: ## Run tests in Docker container
	@echo "🐳 Running tests in Docker..."
	docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit

# Stress testing
stress-test: ## Run stress tests
	@echo "💪 Running stress tests..."
	$(PYTEST) tests/ -m stress --timeout=3600 $(VERBOSE_FLAG)

# Generate test documentation
test-docs: ## Generate test documentation
	@echo "📚 Generating test documentation..."
	$(PYTHON) scripts/generate_test_docs.py
	@echo "✅ Test documentation generated"

# Parallel testing
test-parallel: ## Run tests in parallel
	@echo "⚡ Running tests in parallel..."
	$(PYTEST) tests/ -n auto --dist worksteal $(VERBOSE_FLAG)

# Test data management
setup-test-data: ## Setup test data
	@echo "📊 Setting up test data..."
	$(PYTHON) scripts/setup_test_data.py
	@echo "✅ Test data ready"

clean-test-data: ## Clean test data
	@echo "🧹 Cleaning test data..."
	$(PYTHON) scripts/clean_test_data.py
	@echo "✅ Test data cleaned"

# Quick shortcuts
quick: test-unit ## Quick test run (unit tests only)
full: test-all ## Full test run (all categories)
ci: test-ci ## CI test run
dev: test-unit test-adapters ## Development test run
