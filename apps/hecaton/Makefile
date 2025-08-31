# HECATON Enhanced Patterns Makefile
# Automation for development, testing, and deployment

.PHONY: help install test benchmark deploy clean

PYTHON := python3
PIP := pip3
PROJECT_DIR := $(shell pwd)
VENV := .venv
ACTIVATE := source $(VENV)/bin/activate

# Colors for output
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(GREEN)HECATON Enhanced Patterns - Development Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'

install: ## Install dependencies and set up development environment
	@echo "$(GREEN)Setting up development environment...$(NC)"
	$(PYTHON) -m venv $(VENV)
	$(ACTIVATE) && $(PIP) install --upgrade pip
	$(ACTIVATE) && $(PIP) install -r requirements.txt
	$(ACTIVATE) && $(PIP) install -e .
	@echo "$(GREEN)Environment ready! Activate with: source $(VENV)/bin/activate$(NC)"

requirements: ## Generate requirements.txt from current environment
	$(ACTIVATE) && $(PIP) freeze > requirements.txt

test: ## Run all tests
	@echo "$(GREEN)Running tests...$(NC)"
	$(ACTIVATE) && pytest tests/ -v --cov=src/hecaton --cov-report=html --cov-report=term

test-unit: ## Run unit tests only
	$(ACTIVATE) && pytest tests/unit/ -v

test-integration: ## Run integration tests only
	$(ACTIVATE) && pytest tests/integration/ -v

test-pattern: ## Test specific pattern (usage: make test-pattern PATTERN=checkpoint)
	$(ACTIVATE) && pytest tests/ -k $(PATTERN) -v

benchmark: ## Run performance benchmarks
	@echo "$(GREEN)Running benchmarks...$(NC)"
	$(ACTIVATE) && python benchmarks/enhanced_patterns_benchmark.py
	@echo "$(GREEN)Benchmark results saved to benchmarks/results/$(NC)"

benchmark-compare: ## Compare benchmark results with baseline
	$(ACTIVATE) && python benchmarks/compare_results.py

lint: ## Run code linting
	@echo "$(GREEN)Linting code...$(NC)"
	$(ACTIVATE) && black src/ tests/ --check
	$(ACTIVATE) && flake8 src/ tests/
	$(ACTIVATE) && mypy src/

format: ## Format code
	@echo "$(GREEN)Formatting code...$(NC)"
	$(ACTIVATE) && black src/ tests/
	$(ACTIVATE) && isort src/ tests/

validate-inputs: ## Validate input sets
	@echo "$(GREEN)Validating input sets...$(NC)"
	$(ACTIVATE) && python scripts/validate_inputs.py INPUT_SETS.yaml

run-input: ## Run specific input set (usage: make run-input INPUT=checkpoint_recovery_task)
	$(ACTIVATE) && python src/hecaton/cli_enhanced.py INPUT_SETS.yaml --task-id $(INPUT) -v

run-all-inputs: ## Run all input sets sequentially
	@echo "$(GREEN)Running all input sets...$(NC)"
	$(ACTIVATE) && python scripts/run_all_inputs.py

monitor: ## Start monitoring dashboard
	@echo "$(GREEN)Starting monitoring dashboard on http://localhost:8080$(NC)"
	$(ACTIVATE) && python monitoring/dashboard.py

profile: ## Profile code execution
	$(ACTIVATE) && python -m cProfile -o profile.stats src/hecaton/cli_enhanced.py INPUT_SETS.yaml --task-id checkpoint_recovery_task
	$(ACTIVATE) && python scripts/analyze_profile.py profile.stats

security-scan: ## Run security vulnerability scan
	@echo "$(GREEN)Running security scan...$(NC)"
	$(ACTIVATE) && bandit -r src/
	$(ACTIVATE) && safety check

docs: ## Generate documentation
	@echo "$(GREEN)Generating documentation...$(NC)"
	$(ACTIVATE) && sphinx-build -b html docs/ docs/_build/html
	@echo "$(GREEN)Documentation available at docs/_build/html/index.html$(NC)"

docker-build: ## Build Docker image
	docker build -t hecaton-enhanced:latest .

docker-run: ## Run in Docker container
	docker run -it --rm -v $(PROJECT_DIR):/app hecaton-enhanced:latest

deploy-staging: ## Deploy to staging environment
	@echo "$(YELLOW)Deploying to staging...$(NC)"
	./scripts/deploy.sh staging

deploy-production: ## Deploy to production (requires confirmation)
	@echo "$(RED)WARNING: Deploying to production!$(NC)"
	@read -p "Are you sure? [y/N] " confirm && [ "$$confirm" = "y" ] || exit 1
	./scripts/deploy.sh production

rollback: ## Rollback last deployment
	@echo "$(YELLOW)Rolling back deployment...$(NC)"
	./scripts/rollback.sh

clean: ## Clean build artifacts and cache
	@echo "$(GREEN)Cleaning up...$(NC)"
	rm -rf $(VENV)
	rm -rf __pycache__ .pytest_cache .coverage htmlcov
	rm -rf *.egg-info build dist
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

status: ## Show project status
	@echo "$(GREEN)Project Status:$(NC)"
	@echo "Branch: $$(git branch --show-current)"
	@echo "Last commit: $$(git log -1 --oneline)"
	@echo "Modified files: $$(git status --porcelain | wc -l)"
	@echo ""
	@echo "$(GREEN)Pattern Implementation Status:$(NC)"
	@python scripts/check_implementation_status.py

migrate: ## Run migration from old to new patterns
	@echo "$(GREEN)Running migration...$(NC)"
	$(ACTIVATE) && python scripts/migrate.py

backup: ## Backup current state before changes
	@echo "$(GREEN)Creating backup...$(NC)"
	tar -czf backups/hecaton-backup-$$(date +%Y%m%d-%H%M%S).tar.gz src/ tests/ INPUT_SETS.yaml

.DEFAULT_GOAL := help
