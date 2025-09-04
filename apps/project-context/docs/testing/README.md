# Unified Context System - Testing Documentation

## Overview

This document provides comprehensive information about the testing strategy, framework, and practices for the Unified Context System Phase 2 implementation.

## Table of Contents

- [Testing Strategy](#testing-strategy)
- [Test Categories](#test-categories)
- [Quick Start](#quick-start)
- [Test Structure](#test-structure)
- [Running Tests](#running-tests)
- [Writing Tests](#writing-tests)
- [CI/CD Integration](#cicd-integration)
- [Performance Testing](#performance-testing)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Testing Strategy

Our testing approach follows a comprehensive pyramid strategy with multiple layers:

```
                    E2E Tests (Slow, High-Level)
                 /                               \
        Integration Tests (Medium Speed)
      /                                         \
Unit Tests (Fast, Low-Level, High Coverage)
```

### Testing Principles

1. **Fast Feedback**: Unit tests provide immediate feedback during development
2. **Comprehensive Coverage**: >95% code coverage target for critical components
3. **Real-World Scenarios**: Integration tests use realistic data and scenarios
4. **Performance Validation**: Regular performance testing prevents regressions
5. **Cross-System Correlation**: Tests validate relationships between different adapters

## Test Categories

### 1. Unit Tests (`unit`)
- **Purpose**: Test individual components in isolation
- **Speed**: Very fast (< 5 seconds total)
- **Coverage**: Individual functions, classes, and methods
- **Dependencies**: Mocked/stubbed external dependencies

**Files:**
- `test_git_adapter_unit.py` - Git adapter unit tests
- `test_error_adapter_unit.py` - Error adapter unit tests
- `test_cicd_adapter_unit.py` - CI/CD adapter unit tests

### 2. Integration Tests (`integration`)
- **Purpose**: Test component interactions and adapter correlations
- **Speed**: Medium (30-60 seconds)
- **Coverage**: Cross-adapter relationships, data flow
- **Dependencies**: Mock external services, use real internal components

**Files:**
- `test_adapter_integration.py` - Cross-adapter correlation tests

### 3. End-to-End Tests (`e2e`)
- **Purpose**: Test complete workflows and system behavior
- **Speed**: Slow (2-5 minutes)
- **Coverage**: Full pipeline execution, realistic scenarios
- **Dependencies**: May use real external services (with caution)

**Files:**
- `test_pipeline_end_to_end.py` - Complete pipeline tests

### 4. Performance Tests (`performance`)
- **Purpose**: Validate performance requirements and prevent regressions
- **Speed**: Very slow (5-30 minutes)
- **Coverage**: Throughput, memory usage, concurrent processing
- **Dependencies**: Large datasets, performance monitoring

**Files:**
- `test_performance_load.py` - Performance and load tests

### 5. Database Tests (`database`)
- **Purpose**: Validate database schema, constraints, and operations
- **Speed**: Medium (30-60 seconds)
- **Coverage**: Schema validation, data integrity, migrations
- **Dependencies**: Test database instance

**Files:**
- `test_database_schema.py` - Database schema validation

## Quick Start

### Prerequisites

```bash
# Install dependencies
make install

# Setup development environment
make setup-dev
```

### Running Tests

```bash
# Run all standard tests (recommended for development)
make test

# Run specific test category
make test-unit
make test-integration
make test-performance

# Run with coverage
make coverage

# Run specific test file
make test-specific TEST_FILE=tests/test_git_adapter_unit.py

# Run with verbose output
make test-unit VERBOSE=1
```

### Using the Test Runner Script

```bash
# Run all tests with detailed reporting
python scripts/run_tests.py --all --coverage

# Run specific category
python scripts/run_tests.py --category unit

# Run with performance tests
python scripts/run_tests.py --all --include-performance

# Get help
python scripts/run_tests.py --help
```

## Test Structure

### Directory Layout

```
tests/
├── conftest.py                     # Shared fixtures and configuration
├── pytest.ini                     # Pytest configuration
│
├── test_git_adapter_unit.py        # Git adapter unit tests
├── test_error_adapter_unit.py      # Error adapter unit tests
├── test_cicd_adapter_unit.py       # CI/CD adapter unit tests
├── test_adapter_integration.py     # Cross-adapter integration tests
├── test_pipeline_end_to_end.py     # End-to-end pipeline tests
├── test_performance_load.py        # Performance and load tests
├── test_database_schema.py         # Database schema validation tests
│
└── fixtures/                       # Test data and fixtures
    ├── sample_git_data.json
    ├── sample_error_logs.txt
    └── sample_cicd_workflows.json
```

### Test Naming Conventions

- **Files**: `test_[component]_[type].py`
- **Classes**: `Test[ComponentName][TestType]`
- **Methods**: `test_[specific_behavior]`

### Test Markers

Tests are categorized using pytest markers:

```python
@pytest.mark.unit
@pytest.mark.integration
@pytest.mark.e2e
@pytest.mark.performance
@pytest.mark.slow
@pytest.mark.database
@pytest.mark.git_adapter
@pytest.mark.error_adapter
@pytest.mark.cicd_adapter
```

## Running Tests

### Command Line Options

#### Make Targets
```bash
# Core test commands
make test                    # Run standard test suite
make test-all               # Run all tests including performance
make test-unit              # Unit tests only
make test-integration       # Integration tests
make test-e2e              # End-to-end tests
make test-performance      # Performance tests

# Adapter-specific tests
make test-git              # Git adapter tests
make test-error            # Error adapter tests
make test-cicd             # CI/CD adapter tests

# Development commands
make test-watch            # Watch mode
make test-debug            # Debug output
make coverage              # Coverage report
make test-parallel         # Parallel execution
```

#### Test Runner Script
```bash
# Basic usage
python scripts/run_tests.py --all                    # All tests
python scripts/run_tests.py --category unit          # Specific category
python scripts/run_tests.py --test path/to/test.py   # Specific test

# Configuration options
--coverage                 # Generate coverage reports
--verbose                  # Verbose output
--fail-fast               # Stop on first failure
--parallel                # Run tests in parallel
--workers N               # Number of parallel workers

# Special options
--include-performance     # Include performance tests in --all
--dry-run                 # Show what would be run
--list-categories         # List available categories
```

#### Direct Pytest
```bash
# Run specific test patterns
pytest tests/ -k "test_commit"                       # Pattern matching
pytest tests/ -m "unit and git_adapter"             # Multiple markers
pytest tests/test_git_adapter_unit.py::TestGitAdapter::test_initialization

# With options
pytest tests/ -v --tb=short --maxfail=3             # Verbose, short traceback, stop after 3 failures
pytest tests/ -s                                    # Don't capture output (for debugging)
pytest tests/ -x                                    # Stop on first failure
pytest tests/ --lf                                  # Run last failed tests only
```

### Environment Variables

```bash
# Database testing
TEST_REAL_DB=true          # Enable real database tests
TEST_DB_URL=postgresql://... # Custom database URL

# Network testing
TEST_NETWORK=true          # Enable tests requiring network access

# Performance testing
PERFORMANCE_MULTIPLIER=2.0 # Multiply timeouts by this factor

# Debugging
PYTHONPATH=/path/to/project # Ensure project is in path
TEST_MODE=true             # Enable test mode
```

## Writing Tests

### Test Structure Template

```python
"""Test module for [Component] [Type] tests."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone

from src.project_context.ingestion.adapters.your_adapter import YourAdapter
from src.project_context.models.common import ContextItem


@pytest.fixture
def adapter_config():
    """Create test configuration."""
    return AdapterConfig(
        adapter_id="test_adapter",
        source_type="test",
        # ... configuration
    )


@pytest.fixture
def sample_data():
    """Sample test data."""
    return {
        "items": [
            # ... test data
        ]
    }


class TestYourAdapter:
    """Test class for YourAdapter."""

    @pytest.mark.asyncio
    async def test_initialization(self, adapter_config):
        """Test adapter initialization."""
        adapter = YourAdapter(adapter_config)
        assert adapter.config == adapter_config
        # ... assertions

    @pytest.mark.asyncio
    async def test_fetch_items(self, adapter_config, sample_data):
        """Test fetching items."""
        with patch('external_dependency') as mock_dep:
            mock_dep.return_value = sample_data["items"]

            adapter = YourAdapter(adapter_config)
            items = []
            async for item in adapter.fetch_items():
                items.append(item)

            assert len(items) == len(sample_data["items"])

    @pytest.mark.asyncio
    async def test_error_handling(self, adapter_config):
        """Test error handling."""
        with patch('external_dependency') as mock_dep:
            mock_dep.side_effect = Exception("Test error")

            adapter = YourAdapter(adapter_config)

            with pytest.raises(Exception, match="Test error"):
                async for item in adapter.fetch_items():
                    pass
```

### Async Test Guidelines

```python
# Always mark async tests
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result is not None

# Use AsyncMock for async dependencies
mock_client = AsyncMock()
mock_client.fetch.return_value = test_data

# Proper async context manager mocking
with patch('aiohttp.ClientSession') as mock_session:
    session_instance = AsyncMock()
    response_mock = AsyncMock()
    response_mock.json.return_value = test_data
    session_instance.get.return_value.__aenter__.return_value = response_mock
    mock_session.return_value = session_instance
```

### Performance Test Guidelines

```python
@pytest.mark.performance
@pytest.mark.asyncio
async def test_throughput_performance(performance_monitor):
    """Test throughput performance."""
    await performance_monitor.start_monitoring()

    # Run performance test
    processed_count = 0
    async for item in adapter.fetch_items():
        processed_count += 1
        if processed_count >= 1000:
            break

    await performance_monitor.stop_monitoring()

    metrics = performance_monitor.get_metrics()
    assert metrics["total_time_seconds"] < 30
    assert processed_count >= 1000
    assert metrics["peak_memory_mb"] < 200
```

### Database Test Guidelines

```python
@pytest.mark.database
@pytest.mark.asyncio
async def test_schema_validation(mock_connection):
    """Test database schema."""
    # Mock database query results
    mock_connection.fetch.return_value = [
        {"table_name": "context_items"},
        {"table_name": "context_relationships"}
    ]

    # Test query
    tables = await mock_connection.fetch("SELECT table_name FROM information_schema.tables")
    table_names = {row["table_name"] for row in tables}

    assert "context_items" in table_names
    assert "context_relationships" in table_names
```

## CI/CD Integration

### GitHub Actions Workflow

Our CI/CD pipeline includes multiple jobs:

1. **Unit Tests** - Fast feedback on basic functionality
2. **Database Tests** - Schema validation with real PostgreSQL
3. **Integration Tests** - Cross-component testing
4. **Adapter Tests** - Individual adapter validation
5. **E2E Tests** - Complete system testing
6. **Performance Tests** - Nightly performance validation
7. **Code Quality** - Linting, formatting, security scans

### Workflow Triggers

- **Push/PR**: Unit, integration, adapter tests
- **Schedule** (nightly): Performance tests
- **Manual**: All tests with configurable options

### Test Reports

All tests generate standardized reports:

- **JUnit XML**: For CI/CD integration
- **HTML Reports**: Human-readable detailed results
- **Coverage Reports**: Code coverage analysis
- **Performance Reports**: Performance metrics and trends

## Performance Testing

### Performance Test Categories

1. **Throughput Tests**: Items processed per second
2. **Memory Tests**: Memory usage under load
3. **Concurrent Tests**: Multiple adapters running simultaneously
4. **Stress Tests**: System limits and recovery
5. **Regression Tests**: Performance comparison over time

### Performance Targets

- **Unit Tests**: < 10ms per test
- **Git Adapter**: > 50 items/second processing
- **Error Adapter**: > 100 items/second processing
- **CI/CD Adapter**: > 25 items/second processing
- **Memory Usage**: < 500MB for large datasets
- **Relationship Detection**: < 100ms for 100-item context window

### Running Performance Tests

```bash
# Run all performance tests
make test-performance

# Run with custom multiplier for slower systems
PERFORMANCE_MULTIPLIER=2.0 make test-performance

# Benchmark comparison
make benchmark-compare

# Stress testing
make stress-test
```

## Best Practices

### Test Design

1. **Test Independence**: Each test should be isolated and not depend on others
2. **Clear Naming**: Test names should clearly describe what is being tested
3. **Single Responsibility**: Each test should verify one specific behavior
4. **Realistic Data**: Use realistic test data that represents real-world scenarios
5. **Error Cases**: Test both success and failure scenarios

### Mock Strategy

1. **Mock External Dependencies**: Always mock external services, APIs, file system
2. **Use Real Internal Logic**: Don't mock the code you're testing
3. **Verify Interactions**: Ensure mocks are called correctly
4. **Reset Mocks**: Clean up mocks between tests

### Performance Considerations

1. **Test Data Size**: Use appropriate data sizes for different test types
2. **Resource Monitoring**: Monitor memory and CPU usage during tests
3. **Timeout Management**: Set appropriate timeouts for different test categories
4. **Parallel Execution**: Enable parallel execution for faster feedback

### Documentation

1. **Docstrings**: All test functions should have clear docstrings
2. **Comments**: Explain complex test setup or assertions
3. **README**: Keep testing documentation up to date
4. **Examples**: Provide examples for common testing patterns

## Troubleshooting

### Common Issues

#### 1. Test Timeouts
```bash
# Increase timeout for specific tests
pytest tests/ --timeout=600

# Or use environment variable
PERFORMANCE_MULTIPLIER=2.0 make test
```

#### 2. Database Connection Issues
```bash
# Check database is running
docker-compose up -d postgres

# Verify connection
TEST_REAL_DB=true TEST_DB_URL=postgresql://... make test-database
```

#### 3. Memory Issues
```bash
# Run tests sequentially
pytest tests/ -n 1

# Monitor memory usage
python scripts/run_tests.py --category performance --verbose
```

#### 4. Import Errors
```bash
# Ensure project is installed in development mode
pip install -e .

# Check Python path
export PYTHONPATH=$(pwd):$PYTHONPATH
```

### Debugging Tests

#### Debug Output
```bash
# Run with debug output
make test-debug

# Run specific test with output
pytest tests/test_specific.py -s -vv
```

#### IDE Integration
Most IDEs support pytest integration:

- **VSCode**: Python extension with pytest support
- **PyCharm**: Built-in pytest runner
- **Vim/Neovim**: vim-test plugin

#### Log Analysis
```bash
# View test logs
tail -f test_reports/*.log

# Check specific test output
cat test_reports/unit_report.html
```

### Getting Help

1. **Check Documentation**: Review this README and inline code documentation
2. **Run Help Commands**: `python scripts/run_tests.py --help`
3. **Check Examples**: Look at existing tests for patterns
4. **Debug Output**: Use verbose and debug modes to understand failures

## Contributing

When contributing new tests:

1. Follow the established patterns and conventions
2. Add appropriate test markers
3. Update documentation if adding new test categories
4. Ensure tests are deterministic and reliable
5. Add performance considerations for resource-intensive tests

## Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [Coverage.py](https://coverage.readthedocs.io/)
- [Performance Testing Best Practices](https://docs.python.org/3/library/profile.html)
