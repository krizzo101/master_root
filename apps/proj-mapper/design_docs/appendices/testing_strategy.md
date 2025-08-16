# Testing Strategy

**Version:** 1.0.0  
**Last Updated:** 2023-11-05  
**Status:** Draft

## Document Purpose

This document outlines the testing strategy for the Project Mapper system. It defines the testing approach, methodologies, levels, and standards to ensure the quality, reliability, and correctness of the system.

## Testing Approach

The Project Mapper system follows a test-driven development (TDD) approach, where tests are written before or alongside the implementation code. The testing strategy is designed to:

1. Verify that the system meets its functional and non-functional requirements
2. Ensure that the system behaves correctly under various conditions
3. Detect defects early in the development process
4. Provide confidence in code changes and refactoring
5. Serve as documentation for system behavior

## Testing Levels

### Unit Testing

Unit tests verify the correctness of individual components in isolation.

**Scope:**

- Individual functions and methods
- Classes and modules
- Small, focused behaviors

**Characteristics:**

- Fast execution (milliseconds)
- No external dependencies (databases, files, network)
- High code coverage (minimum 80%)
- Isolated from other components through mocking and stubbing

**Tools:**

- pytest as the primary testing framework
- pytest-mock for mocking dependencies
- pytest-cov for coverage reporting

**Example:**

```python
def test_parse_module():
    """Test the parse_module function with a simple module."""
    # Setup
    content = "def test_function(): pass\n"

    # Execute
    result = parse_module(content)

    # Verify
    assert len(result.functions) == 1
    assert result.functions[0].name == "test_function"
    assert len(result.classes) == 0
```

### Integration Testing

Integration tests verify that multiple components work together correctly.

**Scope:**

- Interactions between modules
- API boundaries
- External dependency interfaces

**Characteristics:**

- Medium execution speed
- Limited external dependencies
- Focus on interaction points
- Verification of correct data flow

**Tools:**

- pytest with specific fixtures for integration testing
- Controlled test environments for external dependencies

**Example:**

```python
def test_analyze_project_with_code_and_docs():
    """Test analyzing a project with both code and documentation."""
    # Setup test project structure
    with TestProjectFixture() as project:
        project.add_python_file("module.py", "def function(): pass")
        project.add_markdown_file("readme.md", "# Project\n\nDescription.")

        # Execute
        config = MapperConfig(include_docs=True)
        mapper = ProjectMapper(config)
        result = mapper.analyze_project(project.path)

        # Verify
        assert len(result.code_structure.modules) == 1
        assert len(result.doc_structure.documents) == 1
        assert result.code_structure.modules[0].name == "module"
        assert "function" in result.code_structure.modules[0].functions[0].name
```

### System Testing

System tests verify that the entire system works correctly end-to-end.

**Scope:**

- Complete workflow scenarios
- Command-line interface
- Output generation
- Error handling

**Characteristics:**

- Slower execution
- May include actual file I/O
- Focus on user-facing behaviors
- Verification of system outputs

**Tools:**

- pytest with system test fixtures
- Temporary directories for file operations
- Shell command execution utilities

**Example:**

```python
def test_cli_with_real_project():
    """Test the CLI with a real project structure."""
    # Setup test project
    with TestProjectFixture.from_template("small_project") as project:
        # Execute CLI command
        result = run_cli_command([
            "proj_mapper",
            project.path,
            "--format", "json",
            "--output-dir", project.temp_dir
        ])

        # Verify
        assert result.exit_code == 0
        assert os.path.exists(os.path.join(project.temp_dir, "project_map.json"))

        # Verify contents
        with open(os.path.join(project.temp_dir, "project_map.json")) as f:
            data = json.load(f)
            assert "project" in data
            assert "structure" in data["project"]
```

### Performance Testing

Performance tests verify that the system meets its performance requirements.

**Scope:**

- Execution time for typical projects
- Memory usage
- CPU utilization
- Scalability with project size

**Characteristics:**

- Benchmarking against reference projects
- Resource monitoring
- Comparative analysis

**Tools:**

- pytest-benchmark for performance testing
- Memory profilers
- Sample projects of various sizes

**Example:**

```python
@pytest.mark.benchmark
def test_performance_medium_project(benchmark):
    """Benchmark analysis of a medium-sized project."""
    with TestProjectFixture.from_template("medium_project") as project:
        # Execute benchmark
        result = benchmark(
            lambda: ProjectMapper().analyze_project(project.path)
        )

        # Verify performance meets requirements
        assert result.stats.mean < 2.0  # Mean execution time < 2 seconds
```

## Test Organization

### Directory Structure

```
tests/
  ├── unit/                  # Unit tests
  │    ├── analyzers/        # Tests for analyzers
  │    ├── formatters/       # Tests for formatters
  │    ├── models/           # Tests for data models
  │    └── utils/            # Tests for utilities
  ├── integration/           # Integration tests
  │    ├── test_analyzer_formatter.py
  │    ├── test_code_doc_integration.py
  │    └── test_pipeline.py
  ├── system/                # System tests
  │    ├── test_cli.py       # Command-line interface tests
  │    ├── test_output.py    # Output validation tests
  │    └── test_scenarios.py # End-to-end scenario tests
  ├── performance/           # Performance tests
  │    ├── test_benchmarks.py
  │    └── projects/         # Test projects for benchmarking
  └── conftest.py            # Shared fixtures and configuration
```

### Naming Conventions

- Test files: `test_*.py`
- Test functions: `test_<function_name>_<scenario>`
- Test classes: `Test<ComponentName>`
- Fixtures: `<purpose>_fixture`

### Fixtures

Reusable test fixtures are defined in `conftest.py` files at appropriate levels:

```python
@pytest.fixture
def sample_module_content():
    """Sample Python module content for testing."""
    return """
    def function_one():
        \"\"\"This is function one.\"\"\"
        return True

    class SampleClass:
        \"\"\"A sample class.\"\"\"

        def method_one(self):
            \"\"\"Sample method.\"\"\"
            return function_one()
    """

@pytest.fixture
def test_project(tmp_path):
    """Create a test project structure."""
    project = TestProject(tmp_path)
    project.create()
    return project
```

## Test Coverage

### Coverage Goals

- **Unit Tests**: Minimum 80% line coverage, with focus on branch coverage
- **Integration Tests**: Coverage of all major component interactions
- **System Tests**: Coverage of all user-facing features and workflows

### Coverage Reporting

Code coverage is measured and reported using pytest-cov, with reports generated in HTML and XML formats.

```bash
pytest --cov=proj_mapper --cov-report=html --cov-report=xml
```

### Uncovered Code

Any code that cannot be reasonably tested should be explicitly marked with coverage exclusion comments and documented with the reason:

```python
def system_dependent_function():
    if sys.platform == 'win32':  # pragma: no cover
        # Windows-specific code that can't be tested in all environments
        return win32_implementation()
    else:
        return posix_implementation()
```

## Test Data Management

### Test Data Sources

1. **Generated Test Data**: Programmatically generated during test execution
2. **Static Test Files**: Stored in the repository under `tests/data/`
3. **Test Fixtures**: Python objects created by fixture functions
4. **Template Projects**: Sample projects for system and performance testing

### Test Project Fixture

A key fixture for system testing is the `TestProject` class that creates and manages test project structures:

```python
class TestProject:
    """Helper class for creating test project structures."""

    def __init__(self, root_path):
        self.root_path = root_path

    def add_python_file(self, relative_path, content):
        """Add a Python file to the test project."""
        path = self.root_path / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return path

    def add_markdown_file(self, relative_path, content):
        """Add a Markdown file to the test project."""
        path = self.root_path / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return path

    @classmethod
    def from_template(cls, template_name, tmp_path):
        """Create a test project from a template."""
        template_path = Path(__file__).parent / "projects" / template_name
        project = cls(tmp_path)
        shutil.copytree(template_path, tmp_path, dirs_exist_ok=True)
        return project
```

## Test Execution

### Local Development

During local development, tests can be run using:

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/system/

# Run with specific markers
pytest -m "not slow"
```

### Continuous Integration

In CI environments, tests are run on each pull request and merge to main:

```yaml
# Example GitHub Actions workflow
test:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    - name: Install dependencies
      run: pip install -e ".[dev]"
    - name: Run tests
      run: pytest --cov=proj_mapper --cov-report=xml
    - name: Upload coverage report
      uses: codecov/codecov-action@v1
```

## Test Categories

Tests are categorized using pytest markers to allow selective execution:

```python
# In conftest.py
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "system: marks tests as system tests")
    config.addinivalue_line("markers", "performance: marks tests as performance tests")

# In test files
@pytest.mark.slow
def test_large_project_analysis():
    """Test analysis of a large project (slow test)."""
```

## Mocking Strategy

### Principles

- Mock external dependencies (filesystem, network, etc.)
- Use consistent mocking patterns
- Prefer explicit mocks over monkey patching
- Document mock behavior and expectations

### Mocking Examples

```python
def test_file_analyzer_with_mock(mocker):
    """Test FileAnalyzer with mocked file operations."""
    # Mock open function
    mock_open = mocker.patch("builtins.open", mocker.mock_open(read_data="file content"))

    # Mock os.path.exists
    mocker.patch("os.path.exists", return_value=True)

    # Execute with mock
    analyzer = FileAnalyzer()
    result = analyzer.analyze("fake_file.py")

    # Verify
    assert result.content == "file content"
    mock_open.assert_called_once_with("fake_file.py", "r", encoding="utf-8")
```

## Continuous Testing

### Developer Workflow

Tests are integrated into the developer workflow:

1. Write tests before or alongside implementation code
2. Run relevant tests during development
3. Run full test suite before committing
4. Maintain test coverage as code evolves

### Pre-commit Hooks

Pre-commit hooks run tests and coverage checks:

```yaml
# .pre-commit-config.yaml
- repo: local
  hooks:
    - id: pytest
      name: pytest
      entry: pytest tests/unit/
      language: system
      pass_filenames: false
      always_run: true
```

## Test Documentation

### Test Documentation in Code

Tests serve as executable documentation and should be clearly written:

```python
def test_module_analyzer_extracts_docstrings():
    """
    Verify that ModuleAnalyzer extracts docstrings from functions and classes.

    Given a Python module with docstrings in functions and classes
    When the ModuleAnalyzer processes the module
    Then the resulting model should contain the docstrings
    And the docstrings should be correctly associated with their elements
    """
    # Test implementation
```

### Test Reports

Test results are reported in multiple formats:

1. Console output during test execution
2. JUnit XML for CI integration
3. HTML reports for human review
4. Coverage reports showing code coverage

## AI Agent Testing

The Project Mapper system is designed specifically for AI agent consumption, requiring specialized testing approaches to ensure AI compatibility.

### AI Consumption Tests

Specialized tests that verify the system produces output optimized for AI consumption:

```python
def test_ai_json_structure():
    """Test that JSON output meets AI parsing requirements."""
    with TestProjectFixture() as project:
        # Generate output
        mapper = ProjectMapper()
        result = mapper.analyze_project(project.path)
        output = JSONFormatter().format(result)

        # Verify AI-specific requirements
        assert "schema_version" in output
        assert "sections" in output
        assert "relationships" in output
        assert all(isinstance(key, str) for key in output.keys())  # All keys must be strings
        assert all(type(output[key]) in (dict, list, str, int, bool, None) for key in output)  # Simple data types
```

### Schema Validation Tests

Tests that validate output against defined schemas for AI consumption:

```python
def test_file_map_schema_validity():
    """Test that file maps conform to the defined schema for AI parsing."""
    with TestProjectFixture() as project:
        # Generate file maps
        mapper = ProjectMapper(file_maps=True)
        mapper.analyze_project(project.path)

        # Load file and extract map
        file_path = project.path / "some_file.py"
        content = file_path.read_text()
        file_map = extract_file_map(content)

        # Validate against schema
        schema_validator = SchemaValidator("file_map_schema.json")
        validation_result = schema_validator.validate(file_map)
        assert validation_result.is_valid
        assert validation_result.errors == []
```

### AI Agent Simulation Tests

Tests that simulate AI agent consumption patterns:

```python
def test_ai_agent_usage_patterns():
    """Test that output supports common AI agent processing patterns."""
    with TestProjectFixture() as project:
        # Generate maps
        mapper = ProjectMapper()
        result = mapper.analyze_project(project.path)
        output = JSONFormatter().format(result)

        # Simulate AI tokenization and processing
        ai_simulator = AIAgentSimulator()
        processing_result = ai_simulator.process_map(output)

        # Verify efficiency metrics
        assert processing_result.token_efficiency > 0.8  # 80% of tokens are meaningful for AI
        assert processing_result.context_retrieval_accuracy > 0.9  # 90% accuracy in retrieving relevant context
        assert processing_result.relationship_inference_success > 0.85  # 85% success in inferring relationships
```

### Map Update Tests

Tests that verify map consistency during real-time updates:

```python
def test_map_updates_for_ai_consumption():
    """Test that map updates maintain consistency for AI agents."""
    with TestProjectFixture() as project:
        # Initial mapping
        mapper = ProjectMapper()
        initial_result = mapper.analyze_project(project.path)

        # Modify a file
        modified_file = project.path / "module.py"
        original_content = modified_file.read_text()
        new_content = original_content + "\n\nclass NewClass:\n    pass\n"
        modified_file.write_text(new_content)

        # Update mapping
        update_result = mapper.update_project(project.path)

        # Verify update consistency for AI consumption
        assert update_result.has_consistent_references
        assert update_result.relationship_integrity_maintained
        assert len(update_result.broken_references) == 0
```

## Related Documents

- [Coding Standards](coding_standards.md)
- [Release Process](release_process.md)
- [System Architecture](../architecture/system_architecture.md)
- [Functional Requirements](../requirements/functional_requirements.md) - See section FR-7 for AI Development and Maintenance Support
- [Non-Functional Requirements](../requirements/non_functional_requirements.md) - See sections AI-1 through AI-5 for AI Consumption Requirements

---

_End of Testing Strategy Document_
