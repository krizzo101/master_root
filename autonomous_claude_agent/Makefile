# Autonomous Claude Agent - Build Automation
# Generated: 2025-08-15
# Version: 1.0.0

# Variables
SHELL := /bin/bash
.DEFAULT_GOAL := help
.PHONY: help build test clean deploy

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

# Project variables
PROJECT_NAME := autonomous-claude-agent
VERSION := $(shell grep version pyproject.toml | head -1 | cut -d'"' -f2)
PYTHON := python3.11
VENV := venv
PIP := $(VENV)/bin/pip
PYTHON_EXEC := $(VENV)/bin/python
PYTEST := $(VENV)/bin/pytest
BLACK := $(VENV)/bin/black
RUFF := $(VENV)/bin/ruff
MYPY := $(VENV)/bin/mypy

# Docker variables
DOCKER_IMAGE := $(PROJECT_NAME):$(VERSION)
DOCKER_REGISTRY := registry.opsvi.ai
DOCKER_TAG := $(DOCKER_REGISTRY)/$(DOCKER_IMAGE)

# Environment
ENV_FILE := .env
ENV_EXAMPLE := .env.example

##@ General

help: ## Display this help message
	@awk 'BEGIN {FS = ":.*##"; printf "\n$(BLUE)Usage:$(NC)\n  make $(GREEN)<target>$(NC)\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2 } /^##@/ { printf "\n$(BLUE)%s$(NC)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

version: ## Show version
	@echo "$(PROJECT_NAME) version: $(VERSION)"

##@ Development

init: ## Initialize development environment
	@echo "$(BLUE)Initializing development environment...$(NC)"
	@if [ ! -f $(ENV_FILE) ]; then \
		cp $(ENV_EXAMPLE) $(ENV_FILE); \
		echo "$(GREEN)Created .env file from template$(NC)"; \
	fi
	@$(PYTHON) -m venv $(VENV)
	@$(PIP) install --upgrade pip setuptools wheel
	@$(PIP) install -r requirements.txt
	@$(PIP) install -e .[dev]
	@echo "$(GREEN)Development environment ready!$(NC)"

install: ## Install dependencies
	@echo "$(BLUE)Installing dependencies...$(NC)"
	@$(PIP) install -r requirements.txt
	@echo "$(GREEN)Dependencies installed!$(NC)"

install-dev: ## Install development dependencies
	@echo "$(BLUE)Installing development dependencies...$(NC)"
	@$(PIP) install -e .[dev]
	@echo "$(GREEN)Development dependencies installed!$(NC)"

install-all: ## Install all dependencies (including optional)
	@echo "$(BLUE)Installing all dependencies...$(NC)"
	@$(PIP) install -e .[all]
	@echo "$(GREEN)All dependencies installed!$(NC)"

update: ## Update dependencies
	@echo "$(BLUE)Updating dependencies...$(NC)"
	@$(PIP) install --upgrade -r requirements.txt
	@echo "$(GREEN)Dependencies updated!$(NC)"

##@ Code Quality

format: ## Format code with black
	@echo "$(BLUE)Formatting code...$(NC)"
	@$(BLACK) src/ tests/ scripts/
	@echo "$(GREEN)Code formatted!$(NC)"

lint: ## Lint code with ruff
	@echo "$(BLUE)Linting code...$(NC)"
	@$(RUFF) check src/ tests/ scripts/ --fix
	@echo "$(GREEN)Code linted!$(NC)"

type-check: ## Type check with mypy
	@echo "$(BLUE)Type checking...$(NC)"
	@$(MYPY) src/
	@echo "$(GREEN)Type check complete!$(NC)"

quality: format lint type-check ## Run all code quality checks

##@ Testing

test: ## Run unit tests
	@echo "$(BLUE)Running unit tests...$(NC)"
	@$(PYTEST) tests/unit -v --cov=autonomous_claude_agent
	@echo "$(GREEN)Unit tests complete!$(NC)"

test-integration: ## Run integration tests
	@echo "$(BLUE)Running integration tests...$(NC)"
	@$(PYTEST) tests/integration -v -m integration
	@echo "$(GREEN)Integration tests complete!$(NC)"

test-all: ## Run all tests
	@echo "$(BLUE)Running all tests...$(NC)"
	@$(PYTEST) tests/ -v --cov=autonomous_claude_agent --cov-report=html
	@echo "$(GREEN)All tests complete! Coverage report: htmlcov/index.html$(NC)"

test-watch: ## Run tests in watch mode
	@echo "$(BLUE)Running tests in watch mode...$(NC)"
	@$(PYTEST) tests/ -v --watch

coverage: ## Generate coverage report
	@echo "$(BLUE)Generating coverage report...$(NC)"
	@$(PYTEST) tests/ --cov=autonomous_claude_agent --cov-report=html --cov-report=term
	@echo "$(GREEN)Coverage report generated: htmlcov/index.html$(NC)"

##@ Docker

docker-build: ## Build Docker image
	@echo "$(BLUE)Building Docker image...$(NC)"
	@docker build -t $(DOCKER_IMAGE) .
	@echo "$(GREEN)Docker image built: $(DOCKER_IMAGE)$(NC)"

docker-push: ## Push Docker image to registry
	@echo "$(BLUE)Pushing Docker image to registry...$(NC)"
	@docker tag $(DOCKER_IMAGE) $(DOCKER_TAG)
	@docker push $(DOCKER_TAG)
	@echo "$(GREEN)Docker image pushed: $(DOCKER_TAG)$(NC)"

docker-run: ## Run Docker container
	@echo "$(BLUE)Running Docker container...$(NC)"
	@docker run -it --rm \
		--env-file $(ENV_FILE) \
		-p 8000:8000 \
		-v $(PWD)/data:/data \
		-v $(PWD)/logs:/logs \
		$(DOCKER_IMAGE)

docker-compose-up: ## Start services with docker-compose
	@echo "$(BLUE)Starting services...$(NC)"
	@docker-compose up -d
	@echo "$(GREEN)Services started!$(NC)"

docker-compose-down: ## Stop services with docker-compose
	@echo "$(BLUE)Stopping services...$(NC)"
	@docker-compose down
	@echo "$(GREEN)Services stopped!$(NC)"

docker-compose-logs: ## Show docker-compose logs
	@docker-compose logs -f

docker-clean: ## Clean Docker resources
	@echo "$(BLUE)Cleaning Docker resources...$(NC)"
	@docker-compose down -v
	@docker system prune -f
	@echo "$(GREEN)Docker resources cleaned!$(NC)"

##@ Deployment

deploy-dev: ## Deploy to development environment
	@echo "$(BLUE)Deploying to development...$(NC)"
	@./scripts/deploy.sh dev
	@echo "$(GREEN)Deployed to development!$(NC)"

deploy-staging: ## Deploy to staging environment
	@echo "$(BLUE)Deploying to staging...$(NC)"
	@./scripts/deploy.sh staging
	@echo "$(GREEN)Deployed to staging!$(NC)"

deploy-prod: ## Deploy to production environment
	@echo "$(YELLOW)WARNING: Deploying to production!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo "$(BLUE)Deploying to production...$(NC)"; \
		./scripts/deploy.sh prod; \
		echo "$(GREEN)Deployed to production!$(NC)"; \
	else \
		echo "$(RED)Deployment cancelled$(NC)"; \
	fi

rollback: ## Rollback deployment
	@echo "$(BLUE)Rolling back deployment...$(NC)"
	@./scripts/rollback.sh
	@echo "$(GREEN)Rollback complete!$(NC)"

##@ Database

db-migrate: ## Run database migrations
	@echo "$(BLUE)Running database migrations...$(NC)"
	@$(PYTHON_EXEC) -m alembic upgrade head
	@echo "$(GREEN)Migrations complete!$(NC)"

db-rollback: ## Rollback database migration
	@echo "$(BLUE)Rolling back database migration...$(NC)"
	@$(PYTHON_EXEC) -m alembic downgrade -1
	@echo "$(GREEN)Rollback complete!$(NC)"

db-reset: ## Reset database
	@echo "$(YELLOW)WARNING: This will reset the database!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo "$(BLUE)Resetting database...$(NC)"; \
		$(PYTHON_EXEC) -m alembic downgrade base; \
		$(PYTHON_EXEC) -m alembic upgrade head; \
		echo "$(GREEN)Database reset complete!$(NC)"; \
	else \
		echo "$(RED)Reset cancelled$(NC)"; \
	fi

##@ Server

run: ## Run the agent server
	@echo "$(BLUE)Starting agent server...$(NC)"
	@$(PYTHON_EXEC) -m autonomous_claude_agent.server

run-dev: ## Run the agent server in development mode
	@echo "$(BLUE)Starting agent server (development)...$(NC)"
	@$(PYTHON_EXEC) -m autonomous_claude_agent.server --dev --reload

run-worker: ## Run background worker
	@echo "$(BLUE)Starting background worker...$(NC)"
	@$(PYTHON_EXEC) -m autonomous_claude_agent.worker

run-cli: ## Run CLI interface
	@echo "$(BLUE)Starting CLI interface...$(NC)"
	@$(PYTHON_EXEC) -m autonomous_claude_agent.cli

##@ Monitoring

logs: ## Show application logs
	@tail -f logs/agent.log

metrics: ## Show metrics dashboard
	@echo "$(BLUE)Opening metrics dashboard...$(NC)"
	@open http://localhost:9090

grafana: ## Open Grafana dashboard
	@echo "$(BLUE)Opening Grafana dashboard...$(NC)"
	@open http://localhost:3000

health: ## Check service health
	@echo "$(BLUE)Checking service health...$(NC)"
	@curl -s http://localhost:8000/health | jq
	@echo "$(GREEN)Health check complete!$(NC)"

##@ Maintenance

clean: ## Clean build artifacts
	@echo "$(BLUE)Cleaning build artifacts...$(NC)"
	@rm -rf build/ dist/ *.egg-info .pytest_cache .coverage htmlcov/
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@echo "$(GREEN)Clean complete!$(NC)"

clean-all: clean docker-clean ## Clean everything
	@echo "$(BLUE)Cleaning everything...$(NC)"
	@rm -rf $(VENV) data/ logs/ checkpoints/ cache/
	@echo "$(GREEN)Full clean complete!$(NC)"

backup: ## Backup data and configuration
	@echo "$(BLUE)Creating backup...$(NC)"
	@./scripts/backup.sh
	@echo "$(GREEN)Backup complete!$(NC)"

restore: ## Restore from backup
	@echo "$(BLUE)Restoring from backup...$(NC)"
	@./scripts/restore.sh
	@echo "$(GREEN)Restore complete!$(NC)"

##@ Utilities

shell: ## Open Python shell with project context
	@$(PYTHON_EXEC) -i -c "from autonomous_claude_agent import *; print('Agent shell ready')"

docs: ## Generate documentation
	@echo "$(BLUE)Generating documentation...$(NC)"
	@$(PYTHON_EXEC) -m mkdocs build
	@echo "$(GREEN)Documentation generated: site/index.html$(NC)"

docs-serve: ## Serve documentation locally
	@echo "$(BLUE)Serving documentation...$(NC)"
	@$(PYTHON_EXEC) -m mkdocs serve

benchmark: ## Run performance benchmarks
	@echo "$(BLUE)Running benchmarks...$(NC)"
	@$(PYTHON_EXEC) scripts/benchmark.py
	@echo "$(GREEN)Benchmarks complete!$(NC)"

validate: ## Validate configuration
	@echo "$(BLUE)Validating configuration...$(NC)"
	@$(PYTHON_EXEC) scripts/validate_config.py
	@echo "$(GREEN)Configuration valid!$(NC)"

bootstrap: ## Bootstrap the entire system
	@echo "$(BLUE)Bootstrapping system...$(NC)"
	@./scripts/bootstrap.sh
	@echo "$(GREEN)Bootstrap complete!$(NC)"

# Performance targets
.NOTPARALLEL: test-all
.SILENT: version