# Sleuth Intel Test Suite Documentation

## Overview

The Sleuth Intel system includes a comprehensive test suite covering unit tests, integration tests, end-to-end scenarios, and performance testing. This document provides guidance on running tests, understanding the test structure, and contributing new tests.

## Test Structure

```
tests/
├── conftest.py           # Global pytest configuration and fixtures
├── fixtures/
│   └── mock_data.py      # Mock data generators
├── utils/
│   └── test_helpers.py   # Test utility functions
├── unit/                # Unit tests
│   ├── test_agents.py
│   ├── test_models.py
│   └── test_api_clients.py
├── integration/         # Integration tests
│   ├── test_agent_communication.py
│   └── test_orchestrator_workflows.py
├── e2e/                 # End-to-end tests
│   └── test_complete_investigations.py
└── performance/         # Performance tests
    └── test_load_testing.py
```

## Quick Start

### Install Dependencies

```bash
pip install -r requirements.txt
pip install pytest pytest-cov pytest-asyncio pytest-benchmark
```

### Run All Tests

```bash
# Using pytest directly
pytest tests/

# Using the Makefile
make test

# Using the test runner script
./scripts/run_tests.sh
```

### Run Specific Test Suites

```bash
# Unit tests only
make test-unit
pytest tests/unit -v

# Integration tests
make test-integration
pytest tests/integration -v -m integration

# End-to-end tests
make test-e2e
pytest tests/e2e -v -m e2e

# Performance tests
make test-performance
pytest tests/performance -v -m performance
```

## Test Categories

### Unit Tests

Unit tests verify individual components in isolation:

- **Agent Tests** (`test_agents.py`): Test individual agent functionality
- **Model Tests** (`test_models.py`): Test data model validation and serialization
- **API Client Tests** (`test_api_clients.py`): Test API client methods with mocked responses

Example:
```python
pytest tests/unit/test_agents.py::TestPersonSearchAgent::test_search_basic -v
```

### Integration Tests

Integration tests verify component interactions:

- **Agent Communication** (`test_agent_communication.py`): Test message bus and agent coordination
- **Orchestrator Workflows** (`test_orchestrator_workflows.py`): Test workflow execution and error handling

Example:
```python
pytest tests/integration -v -m integration
```

### End-to-End Tests

E2E tests simulate complete investigation scenarios:

- Person background checks
- Business due diligence
- Fraud investigations
- Relationship mapping
- Real-time monitoring

Example:
```python
pytest tests/e2e/test_complete_investigations.py::TestCompleteInvestigations::test_person_background_check -v
```

### Performance Tests

Performance tests measure system behavior under load:

- Baseline performance metrics
- Concurrent request handling
- Sustained load testing
- Burst load scenarios
- Memory usage profiling
- Cache performance

Example:
```python
pytest tests/performance -v -m performance --benchmark-only
```

## Test Markers

Tests are organized with markers for selective execution:

```python
@pytest.mark.unit           # Unit tests
@pytest.mark.integration    # Integration tests
@pytest.mark.e2e           # End-to-end tests
@pytest.mark.performance    # Performance tests
@pytest.mark.slow          # Slow-running tests
@pytest.mark.critical      # Critical path tests
```

Run tests by marker:
```bash
pytest -m "unit and not slow"
pytest -m "critical"
```

## Coverage Reports

### Generate Coverage Report

```bash
# Terminal report
pytest --cov=src --cov-report=term-missing

# HTML report
pytest --cov=src --cov-report=html
open htmlcov/index.html

# XML report for CI
pytest --cov=src --cov-report=xml
```

### Coverage Goals

- Overall coverage: **≥80%**
- Critical modules: **≥90%**
- New code: **100%**

## CI/CD Integration

### GitHub Actions Workflow

The project includes a comprehensive GitHub Actions workflow (`.github/workflows/test.yml`) that:

1. Runs linting and code quality checks
2. Executes unit tests across Python versions
3. Runs integration tests with Redis
4. Performs E2E testing
5. Executes performance benchmarks
6. Generates coverage reports
7. Performs security scanning

### Local CI Simulation

Run the complete CI pipeline locally:

```bash
# Full CI pipeline
make ci

# Specific suite
python scripts/test_ci.py --suite unit
```

## Load Testing

### Using Locust

```bash
# Start Locust web UI
locust -f tests/performance/test_load_testing.py --host=http://localhost:8000

# Headless mode
locust -f tests/performance/test_load_testing.py \
    --host=http://localhost:8000 \
    --users=100 \
    --spawn-rate=10 \
    --time=60s \
    --headless
```

### Stress Testing

```bash
# Run stress tests
pytest tests/performance -v -k "stress"

# Custom stress scenario
python scripts/stress_test.py --duration=300 --users=500
```

## Test Utilities

### Mock Data Generator

```python
from tests.fixtures.mock_data import MockDataGenerator

generator = MockDataGenerator()
person = generator.create_person()
business = generator.create_business()
people = generator.create_bulk_persons(100)
```

### Test Helpers

```python
from tests.utils.test_helpers import (
    TestAPIClient,
    MockCache,
    PerformanceProfiler,
    wait_for_condition
)

# Mock API client
client = TestAPIClient(config)
client.set_response("/endpoint", {"data": "value"})

# Performance profiling
profiler = PerformanceProfiler()
measurement = profiler.start("operation")
# ... operation ...
profiler.stop(measurement)
```

## Writing Tests

### Test Structure Template

```python
import pytest
from unittest.mock import AsyncMock, MagicMock

class TestMyComponent:
    """Test suite for MyComponent."""

    @pytest.fixture
    def component(self):
        """Create component instance."""
        return MyComponent()

    @pytest.mark.asyncio
    async def test_basic_functionality(self, component):
        """Test basic component functionality."""
        # Arrange
        expected = "result"

        # Act
        result = await component.do_something()

        # Assert
        assert result == expected

    @pytest.mark.asyncio
    async def test_error_handling(self, component):
        """Test error handling."""
        with pytest.raises(ValueError):
            await component.invalid_operation()
```

### Best Practices

1. **Use descriptive test names** that explain what is being tested
2. **Follow AAA pattern**: Arrange, Act, Assert
3. **Use fixtures** for setup and teardown
4. **Mock external dependencies** to ensure isolation
5. **Test edge cases** and error conditions
6. **Keep tests independent** - no shared state
7. **Use parametrization** for similar test cases

## Debugging Tests

### Verbose Output

```bash
# Maximum verbosity
pytest -vvv tests/unit/test_agents.py

# Show print statements
pytest -s tests/unit/test_agents.py

# Stop on first failure
pytest -x tests/
```

### Debugging with pdb

```python
import pdb

def test_something():
    result = function_under_test()
    pdb.set_trace()  # Debugger breakpoint
    assert result == expected
```

### Test Isolation

```bash
# Run single test
pytest tests/unit/test_agents.py::TestPersonSearchAgent::test_search_basic

# Run tests matching pattern
pytest -k "search" tests/
```

## Performance Benchmarking

### Using pytest-benchmark

```python
@pytest.mark.benchmark
def test_performance(benchmark):
    result = benchmark(function_to_benchmark, arg1, arg2)
    assert result == expected
```

### Benchmark Comparison

```bash
# Save benchmark
pytest --benchmark-save=baseline

# Compare with baseline
pytest --benchmark-compare=baseline

# Generate JSON report
pytest --benchmark-json=benchmark.json
```

## Continuous Improvement

### Test Metrics

Monitor and improve:
- Test coverage percentage
- Test execution time
- Test flakiness rate
- Performance regression
- Security vulnerability count

### Adding New Tests

1. Identify untested code paths
2. Write test following templates
3. Ensure test passes locally
4. Verify coverage improvement
5. Submit PR with tests

## Troubleshooting

### Common Issues

1. **Async test failures**
   ```bash
   # Ensure pytest-asyncio is installed
   pip install pytest-asyncio
   ```

2. **Import errors**
   ```bash
   # Add src to Python path
   export PYTHONPATH="${PYTHONPATH}:${PWD}/src"
   ```

3. **Flaky tests**
   ```bash
   # Rerun failed tests
   pytest --reruns 3 --reruns-delay 1
   ```

4. **Slow tests**
   ```bash
   # Run tests in parallel
   pytest -n auto
   ```

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [Locust Documentation](https://docs.locust.io/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

## Contact

For questions or issues related to testing:
- Create an issue in the repository
- Contact the development team
- Review the CI/CD logs for automated test results
