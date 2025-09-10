# DPO System Makefile
# Provides convenient commands for installation, testing, and maintenance

.PHONY: help install test clean deploy integrate validate docs server

# Default target
help:
	@echo "DPO System Management Commands"
	@echo "=============================="
	@echo ""
	@echo "Installation:"
	@echo "  make install      - Install DPO system"
	@echo "  make integrate    - Integrate with orchestrator"
	@echo "  make deploy       - Full deployment (install + integrate)"
	@echo ""
	@echo "Testing:"
	@echo "  make test         - Run all tests"
	@echo "  make validate     - Validate deployment"
	@echo "  make test-integration - Test ecosystem integration"
	@echo ""
	@echo "Development:"
	@echo "  make dev          - Install in development mode"
	@echo "  make lint         - Run code linting"
	@echo "  make format       - Format code with black"
	@echo ""
	@echo "Operations:"
	@echo "  make server       - Start DPO server"
	@echo "  make dashboard    - Open dashboard"
	@echo "  make logs         - View logs"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean        - Clean build artifacts"
	@echo "  make update       - Update dependencies"
	@echo "  make docs         - Generate documentation"

# Installation targets
install:
	@echo "Installing DPO system..."
	@bash install.sh

integrate:
	@echo "Integrating with orchestrator..."
	@python3 scripts/integrate_orchestrator.py

deploy: install integrate validate
	@echo "✅ DPO deployment complete!"

dev:
	@echo "Installing in development mode..."
	@pip install -e .
	@pip install -r requirements.txt

# Testing targets
test:
	@echo "Running test suite..."
	@python3 -m pytest tests/ -v

validate:
	@echo "Validating deployment..."
	@python3 tests/test_deployment.py

test-integration:
	@echo "Testing ecosystem integration..."
	@python3 tests/test_integration.py

test-templates:
	@echo "Validating templates..."
	@for template in templates/*.json; do \
		echo "Checking $$template..."; \
		python3 -c "import json; json.load(open('$$template'))" || exit 1; \
	done
	@echo "✅ All templates valid"

# Development targets
lint:
	@echo "Running linters..."
	@flake8 src/ tests/ --max-line-length=100 --ignore=E203,W503

format:
	@echo "Formatting code..."
	@black src/ tests/ --line-length=100

type-check:
	@echo "Running type checks..."
	@mypy src/ --ignore-missing-imports

# Operations targets
server:
	@echo "Starting DPO server..."
	@dpo server

dashboard:
	@echo "Opening dashboard..."
	@dpo dashboard

logs:
	@echo "Viewing logs..."
	@tail -f ~/.dpo/logs/dpo.log

monitor:
	@echo "Starting monitoring..."
	@watch -n 5 "dpo status --all"

# Maintenance targets
clean:
	@echo "Cleaning build artifacts..."
	@rm -rf build/ dist/ *.egg-info
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete

update:
	@echo "Updating dependencies..."
	@pip install --upgrade -r requirements.txt

docs:
	@echo "Generating documentation..."
	@cd docs && sphinx-build -b html . _build/html

backup:
	@echo "Creating backup..."
	@tar czf dpo_backup_$(shell date +%Y%m%d_%H%M%S).tar.gz \
		--exclude='*.pyc' \
		--exclude='__pycache__' \
		--exclude='output/*' \
		.

# Utility targets
version:
	@python3 -c "from src import __version__; print(f'DPO Version: {__version__}')"

status:
	@echo "System Status:"
	@echo "--------------"
	@python3 -c "import os; print(f'Installation: {"✓" if os.path.exists("~/.dpo") else "✗"}')"
	@python3 -c "import subprocess; r=subprocess.run(['dpo', '--version'], capture_output=True); print(f'CLI: {"✓" if r.returncode==0 else "✗"}')" 2>/dev/null || echo "CLI: ✗"
	@echo ""
	@dpo status 2>/dev/null || echo "No active workflows"

config:
	@dpo configure --show

# Docker targets
docker-build:
	@echo "Building Docker image..."
	@docker build -t dpo:latest .

docker-run:
	@echo "Running in Docker..."
	@docker run -it --rm \
		-v $(PWD):/app \
		-v ~/.dpo:/root/.dpo \
		-p 8765:8765 \
		-p 8080:8080 \
		dpo:latest

# Quick commands
quick-test:
	@echo "Running quick test..."
	@dpo build "Create a hello world script" --dry-run

demo:
	@echo "Running demo..."
	@dpo build "Create a simple REST API for managing tasks"

# Installation verification
verify: validate
	@echo "Verification Results:"
	@echo "===================="
	@cat ~/.dpo/deployment_test_report.json 2>/dev/null || echo "No test report found"

.DEFAULT_GOAL := help
