# Knowledge Update: pytest (Generated 2025-08-05)

## Current State (Last 12+ Months)

pytest is a powerful Python testing framework with significant recent improvements:
- **Performance**: Enhanced test discovery and execution speed
- **Async Support**: Improved async/await testing capabilities
- **Type Checking**: Better integration with type checkers
- **Plugin Ecosystem**: Extensive plugin support for various testing scenarios
- **Modern Python**: Full support for Python 3.8+ features
- **Configuration**: Enhanced configuration management with pyproject.toml
- **Reporting**: Improved test reporting and output formats

## Best Practices & Patterns

### Basic Test Structure
```python
# test_example.py
import pytest

def test_basic_function():
    """Basic test function"""
    assert 1 + 1 == 2

def test_string_operations():
    """Test string operations"""
    text = "hello world"
    assert text.upper() == "HELLO WORLD"
    assert len(text) == 11

class TestClass:
    """Test class example"""

    def test_method(self):
        """Test method within class"""
        assert "test" in "this is a test"

    def test_another_method(self):
        """Another test method"""
        assert 2 * 3 == 6
```

### Fixtures
```python
import pytest

@pytest.fixture
def sample_data():
    """Provide sample data for tests"""
    return {"name": "test", "value": 42}

@pytest.fixture(scope="session")
def database_connection():
    """Session-scoped database connection"""
    # Setup
    connection = create_database_connection()
    yield connection
    # Teardown
    connection.close()

@pytest.fixture
def temp_file(tmp_path):
    """Create temporary file"""
    file_path = tmp_path / "test_file.txt"
    file_path.write_text("test content")
    return file_path

def test_with_fixtures(sample_data, temp_file):
    """Test using multiple fixtures"""
    assert sample_data["name"] == "test"
    assert temp_file.read_text() == "test content"
```

### Parameterized Tests
```python
import pytest

@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
])
def test_multiply_by_two(input, expected):
    """Test multiplication by 2"""
    assert input * 2 == expected

@pytest.mark.parametrize("a,b,expected", [
    pytest.param(1, 2, 3, id="positive_numbers"),
    pytest.param(-1, -2, -3, id="negative_numbers"),
    pytest.param(0, 0, 0, id="zeros"),
])
def test_addition(a, b, expected):
    """Test addition with different scenarios"""
    assert a + b == expected
```

### Async Testing
```python
import pytest
import asyncio

@pytest.mark.asyncio
async def test_async_function():
    """Test async function"""
    result = await async_function()
    assert result == "expected"

@pytest.fixture
async def async_fixture():
    """Async fixture"""
    data = await fetch_data()
    yield data
    await cleanup()

@pytest.mark.asyncio
async def test_with_async_fixture(async_fixture):
    """Test using async fixture"""
    assert async_fixture is not None
```

### Configuration
```toml
# pyproject.toml
[tool.pytest.ini_options]
testpaths = ["tests", "libs", "apps"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--strict-markers",
    "--strict-config",
    "--cov=libs",
    "--cov=apps",
    "--cov-report=term-missing",
    "--cov-report=html",
    "--cov-report=xml",
]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
    "unit: marks tests as unit tests",
]
```

## Tools & Frameworks

### Core Components
- **pytest**: Main test runner
- **pytest-cov**: Coverage reporting
- **pytest-asyncio**: Async testing support
- **pytest-mock**: Mocking utilities
- **pytest-xdist**: Parallel test execution

### Command Line Usage
```bash
# Basic test execution
pytest

# Run specific test file
pytest test_example.py

# Run specific test function
pytest test_example.py::test_basic_function

# Run tests with markers
pytest -m "not slow"
pytest -m integration

# Run tests in parallel
pytest -n auto

# Generate coverage report
pytest --cov=myapp --cov-report=html

# Verbose output
pytest -v

# Stop on first failure
pytest -x

# Show local variables on failure
pytest -l
```

### Plugins and Extensions
```python
# pytest-mock
def test_with_mock(mocker):
    """Test using mocks"""
    mock_func = mocker.patch('module.function')
    mock_func.return_value = 'mocked'

    result = call_function()
    assert result == 'mocked'
    mock_func.assert_called_once()

# pytest-cov
def test_with_coverage():
    """Test that will be included in coverage"""
    result = complex_function()
    assert result is not None

# pytest-html
def test_with_html_report():
    """Test that will appear in HTML report"""
    assert True
```

## Implementation Guidance

### Project Structure
```
myproject/
├── src/
│   └── myapp/
│       ├── __init__.py
│       └── module.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_module.py
│   └── integration/
│       └── test_integration.py
├── pyproject.toml
└── pytest.ini
```

### Test Organization
```python
# conftest.py - Shared fixtures
import pytest

@pytest.fixture(scope="session")
def app():
    """Application fixture"""
    from myapp import create_app
    app = create_app()
    return app

@pytest.fixture
def client(app):
    """Test client fixture"""
    return app.test_client()

# test_module.py - Unit tests
def test_unit_function():
    """Unit test"""
    assert unit_function() == expected

# test_integration.py - Integration tests
@pytest.mark.integration
def test_integration(client):
    """Integration test"""
    response = client.get('/api/endpoint')
    assert response.status_code == 200
```

### CI/CD Integration
```yaml
# GitHub Actions
- name: Run tests
  run: |
    pip install pytest pytest-cov pytest-asyncio
    pytest --cov=src --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

## Limitations & Considerations

### Current Limitations
- **Async Support**: Some async patterns may require specific plugins
- **Performance**: Large test suites may require optimization
- **Plugin Compatibility**: Some plugins may not work with latest versions
- **Configuration**: Complex configurations may be challenging

### Best Practices
- **Test Organization**: Use clear test file and function names
- **Fixtures**: Use appropriate fixture scopes (function, class, module, session)
- **Markers**: Use markers to categorize and filter tests
- **Coverage**: Maintain good test coverage
- **Isolation**: Ensure tests are independent and isolated

### Migration Considerations
- **From unittest**: pytest is compatible with unittest tests
- **From nose**: Most nose features have pytest equivalents
- **Configuration**: Migrate configuration files gradually
- **Plugins**: Identify and migrate necessary plugins

## Recent Updates (2024-2025)

### Performance Improvements
- **Faster Discovery**: Improved test discovery algorithms
- **Parallel Execution**: Enhanced parallel test execution
- **Memory Optimization**: Reduced memory usage for large test suites
- **Caching**: Better caching of test results

### New Features (2024-2025)
- **Enhanced Async Support**: Better async/await testing capabilities
- **Improved Type Checking**: Better integration with type checkers
- **Configuration Enhancements**: More flexible configuration options
- **Reporting Improvements**: Enhanced test reporting formats

### Breaking Changes (2024-2025)
- **Python Version Support**: Dropped support for Python 3.7
- **Plugin API**: Some plugin APIs may have changed
- **Configuration**: Some configuration options may have changed
- **Deprecations**: Some deprecated features removed

### Plugin Updates
- **pytest-asyncio**: Enhanced async testing support
- **pytest-cov**: Improved coverage reporting
- **pytest-mock**: Better mocking capabilities
- **pytest-xdist**: Enhanced parallel execution

### Ecosystem Integration
- **IDE Support**: Better integration with popular IDEs
- **CI/CD**: Enhanced CI/CD pipeline integration
- **Documentation**: Improved documentation and examples
- **Community**: Active community and plugin ecosystem