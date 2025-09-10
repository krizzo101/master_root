#!/bin/bash
# Test runner for OPSVI libraries

set -e

echo "Setting up test environment..."

# Install test dependencies
pip install -q pytest pytest-cov pytest-asyncio pytest-mock

echo "Running OPSVI library tests..."

# Run tests for each library
echo "Testing opsvi-llm..."
python -m pytest libs/opsvi-llm/tests -v --tb=short

echo "Testing opsvi-interfaces..."
python -m pytest libs/opsvi-interfaces/tests -v --tb=short

echo "Testing opsvi-assistant..."
python -m pytest apps/opsvi-assistant/tests -v --tb=short

echo "Generating coverage report..."
python -m pytest libs/opsvi-llm/tests libs/opsvi-interfaces/tests apps/opsvi-assistant/tests \
    --cov=libs/opsvi-llm/opsvi_llm \
    --cov=libs/opsvi-interfaces/opsvi_interfaces \
    --cov=apps/opsvi-assistant/opsvi_assistant \
    --cov-report=term-missing \
    --cov-report=html:htmlcov \
    --tb=short

echo "Test run complete! Coverage report available in htmlcov/index.html"
