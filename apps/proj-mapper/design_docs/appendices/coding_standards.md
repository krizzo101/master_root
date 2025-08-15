# Coding Standards

**Version:** 1.0.0  
**Last Updated:** 2023-11-05  
**Status:** Draft

## Purpose

This document defines the coding standards for the Project Mapper system. These standards are designed to create code that is optimized for AI agent development and maintenance, ensuring consistency, readability, and maintainability across the codebase.

## Python Style Guidelines

### Code Formatting

- Use [Black](https://github.com/psf/black) with default settings for automatic code formatting
- Maximum line length of 88 characters (Black default)
- Use 4 spaces for indentation (no tabs)
- Follow PEP 8 conventions for naming:
  - `snake_case` for functions, methods, and variables
  - `PascalCase` for classes
  - `UPPER_CASE` for constants
- Remove trailing whitespace
- End files with a newline

### Imports

- Group imports in the following order, separated by a blank line:
  1. Standard library imports
  2. Related third-party imports
  3. Local application/library specific imports
- Within each group, sort imports alphabetically
- Prefer explicit imports over wildcard imports
- Use absolute imports for clarity and to avoid circular dependencies

Example:

```python
import os
import sys
from typing import Dict, List, Optional

import yaml
from pydantic import BaseModel

from proj_mapper.analyzers import FileAnalyzer
from proj_mapper.models import ProjectMap
```

### Documentation

- All modules, classes, methods, and functions must have docstrings
- Use [Google style docstrings](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)
- Include type hints in all function signatures
- Document parameters, return types, and exceptions raised
- Use explicit, detailed docstrings that describe behavior precisely

Example:

```python
def parse_file(file_path: str, max_depth: Optional[int] = None) -> Dict[str, Any]:
    """
    Parse a file and extract its structure.

    This function analyzes the content of the file and returns a dictionary
    representing its structure including classes, functions, and relationships.

    Args:
        file_path: Path to the file to parse
        max_depth: Maximum depth to analyze (None for unlimited)

    Returns:
        Dictionary containing the file structure

    Raises:
        FileNotFoundError: If the file doesn't exist
        ParserError: If the file cannot be parsed
    """
```

### Comments

- Write comments that explain "why" not "what"
- Keep comments up-to-date with code changes
- Use TODO, FIXME, and NOTE comments with consistent formatting for future improvements
- Prefer descriptive naming and clear code over excessive comments

### Logging

- Use the built-in logging module
- Define appropriate log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Include contextual information in log messages
- Structure log messages for easy parsing
- Avoid logging sensitive information

Example:

```python
import logging

logger = logging.getLogger(__name__)

def process_file(file_path):
    logger.debug("Processing file: %s", file_path)
    try:
        result = parse_file(file_path)
        logger.info("Successfully processed file: %s", file_path)
        return result
    except Exception as e:
        logger.error("Error processing file %s: %s", file_path, str(e))
        raise
```

## Code Structure

### File Structure

- Keep files focused on a single responsibility
- Limit file size to 250 lines of code (excluding comments and docstrings)
- Use meaningful file names that reflect their contents
- Organize files in a logical directory structure

### Function and Method Design

- Functions should do one thing and do it well
- Limit function length to 50 lines
- Use descriptive parameter names
- Implement default parameter values where appropriate
- Return early to avoid deep nesting
- Use type hints consistently

Example:

```python
def extract_imports(content: str, file_type: str = "python") -> List[Dict[str, str]]:
    """
    Extract import statements from file content.

    Args:
        content: File content as string
        file_type: Type of file (python, javascript, etc.)

    Returns:
        List of dictionaries containing import information
    """
    if not content:
        return []

    if file_type != "python":
        raise NotImplementedError(f"Import extraction for {file_type} not supported")

    # Implementation
    result = []
    # ...
    return result
```

### Class Design

- Follow the Single Responsibility Principle
- Keep classes focused and cohesive
- Implement proper encapsulation
- Design for extension but closed for modification
- Use appropriate class and instance methods
- Consider composition over inheritance
- Implement proper `__init__` methods

Example:

```python
class FileAnalyzer:
    """Analyzes files to extract structure and elements."""

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the file analyzer.

        Args:
            config: Configuration options for the analyzer
        """
        self.config = config or {}
        self.parsers = self._init_parsers()

    def _init_parsers(self) -> Dict[str, Parser]:
        """Initialize file type specific parsers."""
        return {
            "python": PythonParser(self.config.get("python", {})),
            "markdown": MarkdownParser(self.config.get("markdown", {}))
        }

    def analyze(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze a file and return its structure.

        Args:
            file_path: Path to the file to analyze

        Returns:
            Dictionary containing the file structure

        Raises:
            FileNotFoundError: If the file doesn't exist
            UnsupportedFileTypeError: If the file type is not supported
        """
        # Implementation
```

## Testing Standards

### Test Structure

- Use pytest as the testing framework
- Organize tests to mirror the package structure
- Name test files with `test_` prefix
- Name test functions with `test_` prefix and descriptive names
- Group tests by functionality

### Test Coverage

- Aim for minimum 80% code coverage
- Test edge cases and error conditions
- Use parameterized tests for multiple similar test cases
- Include integration tests for component interactions

### Test Fixtures

- Use fixtures for setup and teardown
- Create reusable fixtures for common test dependencies
- Use appropriate scope for fixtures (function, class, module, session)

Example:

```python
import pytest
from proj_mapper.analyzers import PythonAnalyzer

@pytest.fixture
def python_file_content():
    """Sample Python file content for testing."""
    return """
    def hello_world():
        \"\"\"Say hello.\"\"\"
        print("Hello, World!")

    class Example:
        \"\"\"Example class.\"\"\"
        def method(self):
            pass
    """

def test_python_analyzer_extracts_functions(python_file_content):
    """Test that PythonAnalyzer extracts functions correctly."""
    analyzer = PythonAnalyzer()
    result = analyzer.analyze_content(python_file_content)

    assert len(result["functions"]) == 1
    assert result["functions"][0]["name"] == "hello_world"
```

## AI Optimization Guidelines

### Code Structure for AI Readability

- Use consistent patterns and idioms to help AI agents recognize code patterns
- Break complex operations into smaller, well-named functions
- Use explicit variable names that clearly indicate purpose
- Favor explicit code over clever/implicit solutions
- Structure code with clear progression and minimal state changes

### AI Agent Maintenance Optimizations

- Include explicit pattern markers to help AI agents identify code sections
- Use consistent nomenclature across the codebase to aid AI comprehension
- Add semantic grouping with clear section comments where appropriate
- Ensure one concept per line for better AI parsing
- Keep complex expressions simple and decomposed

Example:

```python
# AI-SECTION-BEGIN: Relationship Detection
def detect_relationships(elements: List[Element]) -> List[Relationship]:
    """
    Detect relationships between elements.

    This function analyzes a list of elements and identifies relationships
    between them, such as inheritance, usage, and calls.

    Args:
        elements: List of elements to analyze

    Returns:
        List of detected relationships
    """
    # First, index elements for efficient lookup
    element_index = build_element_index(elements)

    # Then detect each relationship type
    inheritance_relations = detect_inheritance_relationships(elements, element_index)
    usage_relations = detect_usage_relationships(elements, element_index)
    call_relations = detect_call_relationships(elements, element_index)

    # Combine all relationships
    all_relationships = []
    all_relationships.extend(inheritance_relations)
    all_relationships.extend(usage_relations)
    all_relationships.extend(call_relations)

    return all_relationships
# AI-SECTION-END: Relationship Detection
```

### Documentation for AI Agents

- Provide explicit function signatures with full type annotations
- Use clear, structured docstrings that explain behavior precisely
- Include example usage in docstrings for complex functions
- Document relationships between components explicitly
- Use consistent terminology throughout documentation

Example:

```python
# AI-DOC: This class handles the analysis of Python modules
class PythonAnalyzer(FileAnalyzer):
    """
    Analyzer for Python files.

    This analyzer parses Python source files and extracts information about:
    - Imports
    - Classes and their methods
    - Functions
    - Variables and constants
    - Docstrings

    Example usage:
        analyzer = PythonAnalyzer()
        result = analyzer.analyze('my_module.py')
        classes = result.get_classes()

    Related components:
    - Used by: ProjectAnalyzer
    - Depends on: ast (standard library)
    - Creates: PythonFileModel
    """
```

### Error Handling for AI Maintainability

- Use explicit error types with descriptive names
- Provide detailed error messages that explain the issue and suggest solutions
- Handle exceptions at appropriate levels of abstraction
- Log errors with context information for debugging
- Use typed exceptions for better AI error handling recognition

Example:

```python
class AnalyzerError(Exception):
    """Base class for all analyzer errors."""
    pass

class UnsupportedFileTypeError(AnalyzerError):
    """Raised when attempting to analyze an unsupported file type."""
    pass

class ParsingError(AnalyzerError):
    """Raised when a file cannot be parsed."""
    def __init__(self, file_path: str, line_number: Optional[int] = None, message: str = ""):
        self.file_path = file_path
        self.line_number = line_number
        self.message = message
        super().__init__(f"Error parsing {file_path}" +
                         (f" at line {line_number}" if line_number else "") +
                         (f": {message}" if message else ""))
```

## Pipeline Architecture Patterns

The Project Mapper follows a pipeline architecture, and code should adhere to these pipeline-specific patterns:

### Pipeline Stage Interface

- All pipeline stages must implement the `PipelineStage` interface
- Stages should be focused on a single transformation
- Stages should be stateless when possible
- Input and output interfaces must be explicitly defined
- Each stage should validate its input and output

Example:

```python
from abc import ABC, abstractmethod
from typing import Any, Dict

class PipelineStage(ABC):
    """Interface for all pipeline stages."""

    @abstractmethod
    def process(self, context: Dict[str, Any], input_data: Any) -> Any:
        """
        Process the input data and return the result.

        Args:
            context: Pipeline execution context
            input_data: Data to process

        Returns:
            Processed data for the next stage
        """
        pass

    def validate_input(self, input_data: Any) -> bool:
        """
        Validate that the input data meets this stage's requirements.

        Args:
            input_data: Data to validate

        Returns:
            True if valid, False otherwise
        """
        return True
```

### Data Flow

- Use immutable data structures where possible
- Clearly document the expected input and output formats
- Use typed dictionaries or data classes for complex data structures
- Implement conversion utilities when necessary
- Maintain backward compatibility when changing data structures

## Version Control Practices

### Commit Guidelines

- Write clear, concise commit messages
- Use present tense for commit messages
- Reference issue numbers in commit messages where applicable
- Keep commits focused on a single change
- Commit working code that passes tests

### Versioning

- Follow semantic versioning (MAJOR.MINOR.PATCH)
- Update version numbers according to changes made
- Maintain a changelog with all notable changes

## Related Documents

- [Functional Requirements](../requirements/functional_requirements.md)
- [Non-Functional Requirements](../requirements/non_functional_requirements.md)
- [Testing Strategy](testing_strategy.md)
- [Release Process](release_process.md)

---

_End of Coding Standards Document_
