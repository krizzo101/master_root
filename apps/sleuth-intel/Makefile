# Sleuth Intel Makefile

.PHONY: help install test test-unit test-integration test-e2e test-performance test-all \
        lint format clean coverage security docker-build docker-run

PYTHON := python3
PIP := $(PYTHON) -m pip
PYTEST := $(PYTHON) -m pytest
BLACK := $(PYTHON) -m black
ISORT := $(PYTHON) -m isort
FLAKE8 := $(PYTHON) -m flake8
MYPY := $(PYTHON) -m mypy
COVERAGE := $(PYTHON) -m coverage
BANDIT := $(PYTHON) -m bandit

# Colors
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m

help: ## Show this help message
	@echo "Sleuth Intel - Test Suite Commands"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

install: ## Install dependencies
	@echo "$(GREEN)Installing dependencies...$(NC)"
	$(PIP) install -r requirements.txt
	$(PIP) install -r requirements-dev.txt 2>/dev/null || true

test: ## Run all tests with coverage
	@echo "$(GREEN)Running all tests...$(NC)"
	$(PYTEST) tests/ -v --cov=src --cov-report=term-missing

test-unit: ## Run unit tests
	@echo "$(GREEN)Running unit tests...$(NC)"
	$(PYTEST) tests/unit -v --cov=src --cov-report=term-missing -m "not integration and not e2e and not performance"

test-integration: ## Run integration tests
	@echo "$(GREEN)Running integration tests...$(NC)"
	$(PYTEST) tests/integration -v --cov=src --cov-report=term-missing -m "integration"

test-e2e: ## Run end-to-end tests
	@echo "$(GREEN)Running end-to-end tests...$(NC)"
	$(PYTEST) tests/e2e -v -m "e2e"

test-performance: ## Run performance tests
	@echo "$(GREEN)Running performance tests...$(NC)"
	$(PYTEST) tests/performance -v -m "performance" --benchmark-only

test-all: test-unit test-integration test-e2e test-performance ## Run all test suites

test-parallel: ## Run tests in parallel
	@echo "$(GREEN)Running tests in parallel...$(NC)"
	$(PYTEST) tests/ -v --cov=src -n auto

test-watch: ## Run tests in watch mode
	@echo "$(GREEN)Running tests in watch mode...$(NC)"
	$(PYTEST) tests/ -v --watch

lint: ## Run linting checks
	@echo "$(GREEN)Running linting checks...$(NC)"
	$(BLACK) --check src tests
	$(ISORT) --check-only src tests
	$(FLAKE8) src tests
	$(MYPY) src

format: ## Format code
	@echo "$(GREEN)Formatting code...$(NC)"
	$(BLACK) src tests
	$(ISORT) src tests

clean: ## Clean test artifacts
	@echo "$(GREEN)Cleaning test artifacts...$(NC)"
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf test-results
	rm -f .coverage
	rm -f coverage.xml
	rm -f coverage.json
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

coverage: ## Generate coverage report
	@echo "$(GREEN)Generating coverage report...$(NC)"
	$(COVERAGE) run -m pytest tests/
	$(COVERAGE) report
	$(COVERAGE) html
	@echo "Coverage report available at htmlcov/index.html"

coverage-open: coverage ## Generate and open coverage report
	@echo "$(GREEN)Opening coverage report...$(NC)"
	@command -v xdg-open >/dev/null 2>&1 && xdg-open htmlcov/index.html || \
	command -v open >/dev/null 2>&1 && open htmlcov/index.html || \
	echo "Please open htmlcov/index.html manually"

security: ## Run security checks
	@echo "$(GREEN)Running security checks...$(NC)"
	$(BANDIT) -r src -f json -o test-results/bandit.json
	@echo "Security report saved to test-results/bandit.json"

benchmark: ## Run performance benchmarks
	@echo "$(GREEN)Running benchmarks...$(NC)"
	$(PYTEST) tests/performance -v --benchmark-only --benchmark-json=test-results/benchmark.json
	@echo "Benchmark results saved to test-results/benchmark.json"

ci: ## Run CI pipeline locally
	@echo "$(GREEN)Running CI pipeline...$(NC)"
	$(PYTHON) scripts/test_ci.py

ci-unit: ## Run CI pipeline for unit tests only
	@echo "$(GREEN)Running CI pipeline for unit tests...$(NC)"
	$(PYTHON) scripts/test_ci.py --suite unit

docker-build: ## Build Docker image
	@echo "$(GREEN)Building Docker image...$(NC)"
	docker build -t sleuth-intel:latest .

docker-test: ## Run tests in Docker
	@echo "$(GREEN)Running tests in Docker...$(NC)"
	docker run --rm sleuth-intel:latest make test

docker-shell: ## Open shell in Docker container
	@echo "$(GREEN)Opening Docker shell...$(NC)"
	docker run --rm -it -v $(PWD):/app sleuth-intel:latest /bin/bash

pre-commit: lint test-unit ## Run pre-commit checks
	@echo "$(GREEN)Pre-commit checks passed!$(NC)"

setup-hooks: ## Setup git hooks
	@echo "$(GREEN)Setting up git hooks...$(NC)"
	echo "#!/bin/bash\nmake pre-commit" > .git/hooks/pre-commit
	chmod +x .git/hooks/pre-commit
	@echo "Git hooks installed!"

report: ## Generate test report
	@echo "$(GREEN)Generating test report...$(NC)"
	@mkdir -p test-results
	$(PYTEST) tests/ --junit-xml=test-results/junit.xml --cov=src --cov-report=xml:test-results/coverage.xml --cov-report=html:test-results/htmlcov
	@echo "Reports generated in test-results/"

load-test: ## Run load tests with Locust
	@echo "$(GREEN)Starting load tests...$(NC)"
	locust -f tests/performance/test_load_testing.py --host=http://localhost:8000 --users=100 --spawn-rate=10 --time=60s --headless

stress-test: ## Run stress tests
	@echo "$(GREEN)Running stress tests...$(NC)"
	$(PYTEST) tests/performance -v -m "stress" -k "stress"

validate: lint test coverage security ## Run all validation checks
	@echo "$(GREEN)All validation checks passed!$(NC)"

.DEFAULT_GOAL := help
