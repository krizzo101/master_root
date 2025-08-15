#!/bin/bash
# Script to run all tests and generate coverage reports

set -e  # Exit on error

# Define colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Running tests for Project Mapper${NC}"

# Ensure we're in the project root
cd "$(dirname "$0")/.."

# Create directory for reports
mkdir -p reports

# Check if running in CI environment
if [ -n "$CI" ]; then
    PYTEST_ARGS="--no-header -v"
else
    PYTEST_ARGS=""
fi

echo -e "${YELLOW}Running linting checks...${NC}"
flake8 src tests || { echo -e "${RED}Linting failed${NC}"; exit 1; }
isort --check src tests || { echo -e "${RED}Import sorting check failed${NC}"; exit 1; }
black --check src tests || { echo -e "${RED}Code formatting check failed${NC}"; exit 1; }
mypy src || { echo -e "${RED}Type checking failed${NC}"; exit 1; }

echo -e "${YELLOW}Running unit tests...${NC}"
python -m pytest tests/unit -v || { echo -e "${RED}Unit tests failed${NC}"; exit 1; }

echo -e "${YELLOW}Running integration tests...${NC}"
python -m pytest tests/integration -v || { echo -e "${RED}Integration tests failed${NC}"; exit 1; }

echo -e "${YELLOW}Running end-to-end tests...${NC}"
python -m pytest tests/e2e -v || { echo -e "${RED}End-to-end tests failed${NC}"; exit 1; }

echo -e "${YELLOW}Generating coverage report...${NC}"
python -m pytest --cov=src/proj_mapper \
                 --cov-report=xml:reports/coverage.xml \
                 --cov-report=html:reports/htmlcov \
                 --cov-report=term \
                 tests/ || { echo -e "${RED}Coverage report generation failed${NC}"; exit 1; }

# Make the script executable
chmod +x "$0"

echo -e "${GREEN}All tests passed successfully!${NC}"
echo -e "${GREEN}Coverage report available at reports/htmlcov/index.html${NC}" 