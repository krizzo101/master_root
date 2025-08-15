# Project Mapper Implementation Testing Guide

## Overview

This document outlines a comprehensive testing approach for validating the Project Mapper implementation. It provides structured test cases, validation steps, and success criteria to ensure the system functions correctly and meets all requirements.

## Testing Approach

The testing strategy follows a multi-layered approach:

1. **Unit Testing**: Testing individual components in isolation
2. **Integration Testing**: Testing components working together
3. **System Testing**: Testing the entire pipeline
4. **Validation Testing**: Testing against real-world projects

## Test Environments

Testing should be performed in these environments:

1. **Development Environment**: Local testing during development
2. **CI Environment**: Automated testing in continuous integration
3. **Production-like Environment**: Testing with real-world projects

## Test Data

For consistent and thorough testing, use the following test data:

1. **Simple Project**: A minimal project with few files and simple structures
2. **Medium Project**: A moderately complex project with various file types and structures
3. **Complex Project**: A large-scale project with complex dependencies and relationships
4. **Edge Cases**: Projects with unusual structures or patterns

## File Discovery Testing

### Unit Tests

| Test ID | Description               | Input                          | Expected Output             | Validation Criteria      |
| ------- | ------------------------- | ------------------------------ | --------------------------- | ------------------------ |
| FD-U-01 | Basic File Discovery      | Project with Python files      | List of discovered files    | All Python files found   |
| FD-U-02 | Include Pattern Filtering | Include pattern `**/*.py`      | Only Python files           | No non-Python files      |
| FD-U-03 | Exclude Pattern Filtering | Exclude pattern `**/test_*.py` | No test files               | No test files in results |
| FD-U-04 | Empty Directory           | Empty project directory        | Empty result                | No errors thrown         |
| FD-U-05 | File Categorization       | Mixed file types               | Correctly categorized files | Files grouped by type    |

### Integration Tests

| Test ID | Description          | Input                  | Expected Output             | Validation Criteria          |
| ------- | -------------------- | ---------------------- | --------------------------- | ---------------------------- |
| FD-I-01 | Pipeline Integration | Project directory      | Pipeline context with files | Context contains files       |
| FD-I-02 | Pipeline Data Flow   | Discovery stage output | Input for next stage        | Correct file metadata format |
| FD-I-03 | Error Handling       | Invalid directory      | Proper error in context     | Error message in context     |

## Python Analyzer Testing

### Unit Tests

| Test ID | Description          | Input                    | Expected Output        | Validation Criteria                 |
| ------- | -------------------- | ------------------------ | ---------------------- | ----------------------------------- |
| PA-U-01 | Module Analysis      | Python module file       | Module structure       | Correct imports, functions, classes |
| PA-U-02 | Class Detection      | File with classes        | Class structures       | All classes with correct attributes |
| PA-U-03 | Function Analysis    | File with functions      | Function structures    | All functions with parameters       |
| PA-U-04 | Import Analysis      | File with imports        | Import structures      | All imports correctly identified    |
| PA-U-05 | Type Hint Processing | Type-annotated file      | Type information       | All type hints extracted            |
| PA-U-06 | Nested Structures    | Nested classes/functions | Hierarchical structure | Correct nesting relationships       |
| PA-U-07 | Decorator Handling   | Decorated functions      | Decorator information  | All decorators identified           |

### Integration Tests

| Test ID | Description          | Input                  | Expected Output   | Validation Criteria       |
| ------- | -------------------- | ---------------------- | ----------------- | ------------------------- |
| PA-I-01 | Pipeline Integration | Discovery stage output | Analyzed modules  | All Python files analyzed |
| PA-I-02 | Error Handling       | Invalid Python file    | Error in context  | Error message in context  |
| PA-I-03 | Large File Handling  | Very large Python file | Complete analysis | No performance issues     |

## Relationship Mapping Testing

### Unit Tests

| Test ID | Description                    | Input                    | Expected Output           | Validation Criteria           |
| ------- | ------------------------------ | ------------------------ | ------------------------- | ----------------------------- |
| RM-U-01 | Import Relationships           | Modules with imports     | Import relationships      | All imports mapped            |
| RM-U-02 | Inheritance Relationships      | Classes with inheritance | Inheritance relationships | All base classes identified   |
| RM-U-03 | Function Call Relationships    | Functions calling others | Call relationships        | Function calls identified     |
| RM-U-04 | Attribute Access Relationships | Attribute access         | Access relationships      | Attribute access mapped       |
| RM-U-05 | Relationship Confidence        | Ambiguous relationships  | Confidence scores         | Appropriate confidence levels |

### Integration Tests

| Test ID | Description                | Input                 | Expected Output            | Validation Criteria           |
| ------- | -------------------------- | --------------------- | -------------------------- | ----------------------------- |
| RM-I-01 | Pipeline Integration       | Analysis stage output | Relationship graph         | Complete relationship network |
| RM-I-02 | Cross-Module Relationships | Multi-module project  | Inter-module relationships | Connections between modules   |
| RM-I-03 | Large Project Performance  | Large project         | Complete relationship map  | Reasonable performance        |

## Map Generation Testing

### Unit Tests

| Test ID | Description         | Input                 | Expected Output   | Validation Criteria          |
| ------- | ------------------- | --------------------- | ----------------- | ---------------------------- |
| MG-U-01 | Basic Map Structure | Relationship data     | Map structure     | Correct map hierarchy        |
| MG-U-02 | Map Metadata        | Project with metadata | Map with metadata | All metadata included        |
| MG-U-03 | Map Serialization   | Map object            | Serialized map    | Correct JSON format          |
| MG-U-04 | Large Map Handling  | Large project data    | Complete map      | No memory/performance issues |

### Integration Tests

| Test ID | Description          | Input                     | Expected Output | Validation Criteria     |
| ------- | -------------------- | ------------------------- | --------------- | ----------------------- |
| MG-I-01 | Pipeline Integration | Relationship stage output | Generated map   | Complete project map    |
| MG-I-02 | Map Storage          | Generated map             | Stored map      | Map correctly persisted |
| MG-I-03 | Map Versioning       | Multiple map generations  | Version history | Correct versioning      |

## End-to-End Testing

### System Tests

| Test ID | Description              | Input            | Expected Output  | Validation Criteria                 |
| ------- | ------------------------ | ---------------- | ---------------- | ----------------------------------- |
| E2E-01  | Simple Project Analysis  | Simple project   | Complete map     | All components correctly mapped     |
| E2E-02  | Medium Project Analysis  | Medium project   | Complete map     | Correct relationships and structure |
| E2E-03  | Complex Project Analysis | Complex project  | Complete map     | Complete analysis without errors    |
| E2E-04  | Incremental Analysis     | Modified project | Updated map      | Only changed parts updated          |
| E2E-05  | CLI Interface            | CLI commands     | Expected output  | Correct CLI behavior                |
| E2E-06  | Performance Benchmarking | Large project    | Analysis metrics | Meets performance targets           |

## Validation Test Cases

Use these real-world projects for validation:

1. **Small Library Project**:

   - Example: A simple utility library
   - Goals: Verify basic analysis and relationship mapping

2. **Medium Web Application**:

   - Example: A Flask or Django application
   - Goals: Test framework-specific analysis and complex relationships

3. **Large Complex Project**:
   - Example: An open-source project with multiple modules
   - Goals: Validate scalability and performance

## Test Implementation

### Unit Tests Structure

Create a comprehensive unit test suite with the following structure:

```
tests/
  unit/
    discovery/
      test_file_discovery.py
    analysis/
      test_python_analyzer.py
    relationships/
      test_relationship_mapper.py
    maps/
      test_map_generator.py
  integration/
    test_discovery_analysis.py
    test_analysis_relationships.py
    test_relationships_maps.py
  system/
    test_end_to_end.py
    test_cli.py
    test_performance.py
```

### Sample Unit Test

Here's a sample unit test for file discovery:

```python
import pytest
import tempfile
from pathlib import Path
from project_mapper.discovery.file_discovery import FileDiscovery

class TestFileDiscovery:

    @pytest.fixture
    def sample_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            project_root = Path(tmpdir)
            (project_root / "main.py").touch()
            (project_root / "utils").mkdir()
            (project_root / "utils" / "helpers.py").touch()
            (project_root / "docs").mkdir()
            (project_root / "docs" / "readme.md").touch()
            (project_root / "venv").mkdir()
            (project_root / "venv" / "lib").mkdir(parents=True)
            (project_root / "venv" / "lib" / "python.exe").touch()

            yield project_root

    def test_basic_discovery(self, sample_project):
        """Test basic file discovery with default patterns."""
        discovery = FileDiscovery(sample_project)
        files = discovery.discover()

        # Should find 3 files excluding venv
        assert len(files) == 3

        # Check specific files
        assert sample_project.joinpath("main.py").relative_to(sample_project) in files
        assert sample_project.joinpath("utils/helpers.py").relative_to(sample_project) in files
        assert sample_project.joinpath("docs/readme.md").relative_to(sample_project) in files
```

### Sample Integration Test

Here's a sample integration test:

```python
import pytest
import tempfile
from pathlib import Path
from project_mapper.pipeline import PipelineContext
from project_mapper.discovery.file_discovery import FileDiscoveryStage
from project_mapper.analysis.python_analyzer import PythonAnalysisStage

class TestDiscoveryAnalysisIntegration:

    @pytest.fixture
    def sample_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            project_root = Path(tmpdir)
            (project_root / "main.py").write_text("def main(): pass")
            (project_root / "utils").mkdir()
            (project_root / "utils" / "helpers.py").write_text("def helper(): return True")

            yield project_root

    def test_discovery_analysis_integration(self, sample_project):
        """Test integration between file discovery and Python analysis."""
        # Create pipeline context
        context = PipelineContext({'project_root': sample_project})

        # Create and run file discovery stage
        discovery_stage = FileDiscoveryStage()
        context = discovery_stage.process(context)

        # Check files were discovered
        assert 'python_files' in context
        assert len(context['python_files']) == 2

        # Create and run Python analysis stage
        analysis_stage = PythonAnalysisStage()
        context = analysis_stage.process(context)

        # Check modules were analyzed
        assert 'analyzed_modules' in context
        assert len(context['analyzed_modules']) == 2

        # Check module contents
        main_module = context['analyzed_modules'][Path("main.py")]
        helpers_module = context['analyzed_modules'][Path("utils/helpers.py")]

        assert "main" in main_module.functions
        assert "helper" in helpers_module.functions
```

## Test Execution Plan

1. **Development Testing**:

   - Run unit tests during development
   - Verify each component individually

2. **Integration Testing**:

   - Run integration tests after unit tests pass
   - Verify component interactions

3. **System Testing**:

   - Run end-to-end tests on representative projects
   - Verify complete pipeline functionality

4. **Performance Testing**:
   - Run benchmarks on large projects
   - Verify performance meets requirements

## Test Success Criteria

A successful implementation must:

1. **Pass All Tests**: All unit, integration, and system tests must pass
2. **Meet Performance Targets**: Analysis must complete within acceptable time frames
3. **Handle Edge Cases**: Properly handle unusual code patterns and structures
4. **Scale Appropriately**: Work with projects of various sizes
5. **Produce Accurate Maps**: Generate maps that correctly represent the project structure

## Test Metrics

Track these metrics during testing:

1. **Test Coverage**: Aim for >90% code coverage
2. **Analysis Time**: Measure time to analyze projects of different sizes
3. **Memory Usage**: Monitor memory consumption during analysis
4. **Accuracy Rate**: Compare detected structures to actual project structures
5. **Error Rate**: Track errors and exceptions during analysis

## Test Reporting

Generate test reports with:

1. **Test Results**: Pass/fail status for all tests
2. **Coverage Report**: Code coverage metrics
3. **Performance Metrics**: Time and memory usage
4. **Error Log**: Any errors or warnings encountered

## Conclusion

Following this testing guide will ensure a robust and reliable implementation of the Project Mapper. The test cases cover all aspects of the system, from individual components to the complete pipeline, ensuring comprehensive validation of the implementation.

The test cases are designed to be automated, allowing for continuous validation during development and before releases. By using both simple test cases and real-world projects, the testing approach ensures both theoretical correctness and practical usability.
