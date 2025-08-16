# Project Mapper Analysis Subsystem

This directory contains the analysis subsystem for the Project Mapper application. The analysis subsystem is responsible for extracting structured information from code and documentation files in a project.

## Architecture

The analysis subsystem consists of the following components:

- **Base Analyzer Interface** (`base.py`): Defines the interface for all analyzers.
- **Analyzer Factory** (`factory.py`): Creates and registers analyzers for different file types.
- **Analysis Pipeline** (`pipeline.py`): Coordinates the analysis of project files.
- **Code Analyzers** (`code/`): Contains analyzers for different programming languages.
- **Documentation Analyzers** (`documentation/`): Contains analyzers for different documentation formats.

## Usage

Here's a basic example of how to use the analysis subsystem:

```python
from proj_mapper.core.discovery import ProjectDiscovery
from proj_mapper.analyzers.pipeline import AnalysisPipeline

# Discover project files
discovery = ProjectDiscovery()
project = discovery.discover_project("/path/to/project")

# Analyze project files
pipeline = AnalysisPipeline()
results = pipeline.analyze_project(project)

# Generate a summary
summary = pipeline.generate_summary()
print(f"Analyzed {summary['total_files_analyzed']} files")

# Get related files
related_files = pipeline.get_related_files("/path/to/file.py", "import")
print(f"Found {len(related_files)} related files")

# Get code references to a file
references = pipeline.get_code_references_to_file("/path/to/file.py")
print(f"Found references in {len(references)} files")

# Get documentation for code
doc_references = pipeline.get_documentation_for_code("/path/to/file.py")
print(f"Found documentation in {len(doc_references)} files")
```

## Adding New Analyzers

To add a new analyzer:

1. Create a new class that extends `Analyzer` from `base.py`.
2. Implement the required methods: `can_analyze()` and `analyze()`.
3. Register the analyzer in `factory.py`.

Example for a new language analyzer:

```python
from proj_mapper.analyzers.base import Analyzer
from proj_mapper.models.analysis import CodeAnalysisResult
from proj_mapper.models.file import DiscoveredFile, FileType

class JavaAnalyzer(Analyzer):
    """Analyzer for Java code files."""

    supported_extensions = {'.java'}

    def can_analyze(self, file: DiscoveredFile) -> bool:
        """Check if this analyzer can analyze the given file."""
        return file.file_type == FileType.SOURCE or file.get_extension() in self.supported_extensions

    def analyze(self, file: DiscoveredFile, content=None) -> CodeAnalysisResult:
        """Analyze a Java file."""
        # Implementation...
```

## Understanding Analysis Results

Analysis results are structured as follows:

- **CodeAnalysisResult**: Contains code elements, imports, and docstrings.

  - **Elements**: Classes, methods, functions, variables, etc.
  - **Imports**: Dependencies on other modules.
  - **References**: References to other files or code elements.

- **DocumentationAnalysisResult**: Contains documentation elements.
  - **Elements**: Sections, paragraphs, code blocks, lists, etc.
  - **References**: References to code or other files.

## Testing

The analysis subsystem has comprehensive unit tests in the `tests/analyzers/` directory. Run the tests with:

```bash
pytest tests/analyzers/
```
