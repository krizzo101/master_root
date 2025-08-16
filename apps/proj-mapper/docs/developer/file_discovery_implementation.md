# File Discovery Implementation Guide

## Overview

The File Discovery component is responsible for identifying and categorizing files within a project directory. It serves as the foundation for the entire analysis pipeline by providing a structured representation of the project's file system.

## Core Functionality

The File Discovery module will:

1. Scan directory structures recursively
2. Filter files based on include/exclude patterns
3. Categorize files by type (Python, Markdown, etc.)
4. Create file metadata objects with relevant information
5. Provide an API for other components to access file information

## Implementation Details

### 1. File Discovery Class

```python
from pathlib import Path
import fnmatch
import os
from typing import List, Dict, Set, Optional
from dataclasses import dataclass

@dataclass
class FileMetadata:
    """Metadata for a discovered file."""
    path: Path
    relative_path: Path
    file_type: str
    size: int
    last_modified: float

    @property
    def is_python(self) -> bool:
        return self.path.suffix == '.py'

    @property
    def is_markdown(self) -> bool:
        return self.path.suffix == '.md'

    @property
    def is_documentation(self) -> bool:
        return self.is_markdown or self.path.suffix in ('.rst', '.txt')

    @property
    def name(self) -> str:
        return self.path.name


class FileDiscovery:
    """Discovers and categorizes files in a project."""

    def __init__(self,
                 root_dir: Path,
                 include_patterns: Optional[List[str]] = None,
                 exclude_patterns: Optional[List[str]] = None):
        """Initialize with root directory and optional filters.

        Args:
            root_dir: The root directory to scan
            include_patterns: Glob patterns to include (e.g. ['*.py', '*.md'])
            exclude_patterns: Glob patterns to exclude (e.g. ['**/venv/**', '**/__pycache__/**'])
        """
        self.root_dir = Path(root_dir).absolute()
        self.include_patterns = include_patterns or ['**/*']
        self.exclude_patterns = exclude_patterns or ['**/venv/**', '**/__pycache__/**',
                                                     '**/.git/**', '**/.mypy_cache/**']
        self._discovered_files: Dict[Path, FileMetadata] = {}

    def discover(self) -> Dict[Path, FileMetadata]:
        """Scan the root directory and discover files based on patterns.

        Returns:
            Dict[Path, FileMetadata]: Dictionary of discovered files with relative paths as keys
        """
        self._discovered_files = {}

        for path in self.root_dir.glob('**/*'):
            if not path.is_file():
                continue

            relative_path = path.relative_to(self.root_dir)
            rel_path_str = str(relative_path)

            # Check if file should be excluded
            if any(fnmatch.fnmatch(rel_path_str, pattern) for pattern in self.exclude_patterns):
                continue

            # Check if file should be included
            if not any(fnmatch.fnmatch(rel_path_str, pattern) for pattern in self.include_patterns):
                continue

            # Create metadata
            stat = path.stat()
            file_type = path.suffix[1:] if path.suffix else ''

            metadata = FileMetadata(
                path=path,
                relative_path=relative_path,
                file_type=file_type,
                size=stat.st_size,
                last_modified=stat.st_mtime
            )

            self._discovered_files[relative_path] = metadata

        return self._discovered_files

    def get_python_files(self) -> Dict[Path, FileMetadata]:
        """Get all discovered Python files.

        Returns:
            Dict[Path, FileMetadata]: Dictionary of Python files
        """
        return {path: metadata for path, metadata in self._discovered_files.items()
                if metadata.is_python}

    def get_documentation_files(self) -> Dict[Path, FileMetadata]:
        """Get all discovered documentation files.

        Returns:
            Dict[Path, FileMetadata]: Dictionary of documentation files
        """
        return {path: metadata for path, metadata in self._discovered_files.items()
                if metadata.is_documentation}

    def get_files_by_type(self, file_type: str) -> Dict[Path, FileMetadata]:
        """Get all discovered files of a specific type.

        Args:
            file_type: The file type extension without the dot (e.g. 'py', 'md')

        Returns:
            Dict[Path, FileMetadata]: Dictionary of files of the specified type
        """
        return {path: metadata for path, metadata in self._discovered_files.items()
                if metadata.file_type == file_type}
```

### 2. Integration with Pipeline

Create a pipeline stage for file discovery:

```python
from project_mapper.pipeline import PipelineStage, PipelineContext
from pathlib import Path
from typing import Dict, Any

class FileDiscoveryStage(PipelineStage):
    """Pipeline stage for file discovery."""

    def __init__(self,
                 include_patterns=None,
                 exclude_patterns=None,
                 name="file_discovery"):
        """Initialize the file discovery stage.

        Args:
            include_patterns: Optional list of glob patterns to include
            exclude_patterns: Optional list of glob patterns to exclude
            name: Stage name
        """
        super().__init__(name=name)
        self.include_patterns = include_patterns
        self.exclude_patterns = exclude_patterns

    def process(self, context: PipelineContext) -> Dict[str, Any]:
        """Process the stage.

        Args:
            context: Pipeline context

        Returns:
            Dict[str, Any]: Updated context with discovered files
        """
        project_root = context.get('project_root')
        if not project_root:
            raise ValueError("Project root not set in pipeline context")

        discoverer = FileDiscovery(
            root_dir=project_root,
            include_patterns=self.include_patterns,
            exclude_patterns=self.exclude_patterns
        )

        files = discoverer.discover()

        # Add to context
        context.update({
            'files': files,
            'python_files': discoverer.get_python_files(),
            'documentation_files': discoverer.get_documentation_files()
        })

        return context
```

## Test Cases

### Unit Tests

Create unit tests for the FileDiscovery class:

```python
import os
import tempfile
from pathlib import Path
import pytest
from project_mapper.discovery.file_discovery import FileDiscovery, FileMetadata

class TestFileDiscovery:

    @pytest.fixture
    def test_project(self):
        """Create a temporary project structure for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create directory structure
            project_root = Path(temp_dir)

            # Create Python files
            (project_root / "main.py").touch()
            (project_root / "utils").mkdir()
            (project_root / "utils" / "helpers.py").touch()

            # Create documentation
            (project_root / "docs").mkdir()
            (project_root / "docs" / "readme.md").touch()

            # Create excluded directories
            venv_dir = project_root / "venv"
            venv_dir.mkdir()
            (venv_dir / "bin").mkdir()
            (venv_dir / "bin" / "python").touch()

            yield project_root

    def test_basic_discovery(self, test_project):
        """Test basic file discovery with default patterns."""
        discovery = FileDiscovery(test_project)
        files = discovery.discover()

        # Should find 3 files (excluding venv)
        assert len(files) == 3

        # Check specific files
        assert test_project.joinpath("main.py").relative_to(test_project) in files
        assert test_project.joinpath("utils/helpers.py").relative_to(test_project) in files
        assert test_project.joinpath("docs/readme.md").relative_to(test_project) in files

        # Check venv exclusion
        venv_file = test_project.joinpath("venv/bin/python").relative_to(test_project)
        assert venv_file not in files

    def test_custom_include_pattern(self, test_project):
        """Test discovery with custom include pattern."""
        discovery = FileDiscovery(
            test_project,
            include_patterns=["**/*.py"]
        )
        files = discovery.discover()

        # Should only find Python files
        assert len(files) == 2

        # Check specific files
        assert test_project.joinpath("main.py").relative_to(test_project) in files
        assert test_project.joinpath("utils/helpers.py").relative_to(test_project) in files

        # MD file should be excluded
        assert test_project.joinpath("docs/readme.md").relative_to(test_project) not in files

    def test_custom_exclude_pattern(self, test_project):
        """Test discovery with custom exclude pattern."""
        discovery = FileDiscovery(
            test_project,
            exclude_patterns=["**/venv/**", "**/utils/**"]
        )
        files = discovery.discover()

        # Should exclude utils directory
        assert len(files) == 2

        # Check specific files
        assert test_project.joinpath("main.py").relative_to(test_project) in files
        assert test_project.joinpath("docs/readme.md").relative_to(test_project) in files

        # Utils file should be excluded
        assert test_project.joinpath("utils/helpers.py").relative_to(test_project) not in files

    def test_get_python_files(self, test_project):
        """Test getting Python files."""
        discovery = FileDiscovery(test_project)
        discovery.discover()

        python_files = discovery.get_python_files()

        # Should find 2 Python files
        assert len(python_files) == 2

        # Check specific files
        assert test_project.joinpath("main.py").relative_to(test_project) in python_files
        assert test_project.joinpath("utils/helpers.py").relative_to(test_project) in python_files

    def test_get_documentation_files(self, test_project):
        """Test getting documentation files."""
        discovery = FileDiscovery(test_project)
        discovery.discover()

        doc_files = discovery.get_documentation_files()

        # Should find 1 documentation file
        assert len(doc_files) == 1

        # Check specific files
        assert test_project.joinpath("docs/readme.md").relative_to(test_project) in doc_files
```

### Integration Tests

Create integration tests for the FileDiscoveryStage:

```python
import os
import tempfile
from pathlib import Path
import pytest
from project_mapper.pipeline import PipelineContext
from project_mapper.discovery.file_discovery import FileDiscoveryStage

class TestFileDiscoveryStage:

    @pytest.fixture
    def test_project(self):
        """Create a temporary project structure for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create directory structure
            project_root = Path(temp_dir)

            # Create Python files
            (project_root / "main.py").touch()
            (project_root / "utils").mkdir()
            (project_root / "utils" / "helpers.py").touch()

            # Create documentation
            (project_root / "docs").mkdir()
            (project_root / "docs" / "readme.md").touch()

            yield project_root

    def test_file_discovery_stage(self, test_project):
        """Test the file discovery pipeline stage."""
        # Create context with project root
        context = PipelineContext({'project_root': test_project})

        # Create and run stage
        stage = FileDiscoveryStage()
        result_context = stage.process(context)

        # Check files were discovered
        assert 'files' in result_context
        assert 'python_files' in result_context
        assert 'documentation_files' in result_context

        # Check counts
        assert len(result_context['files']) == 3
        assert len(result_context['python_files']) == 2
        assert len(result_context['documentation_files']) == 1
```

## Implementation Steps

1. **Create Base Classes**:

   - Implement `FileMetadata` dataclass
   - Implement `FileDiscovery` class with core functionality

2. **Add Pipeline Integration**:

   - Create `FileDiscoveryStage` class
   - Ensure it integrates with pipeline context

3. **Write Tests**:

   - Implement unit tests for core functionality
   - Implement integration tests with pipeline

4. **Documentation**:
   - Add docstrings to all classes and methods
   - Create usage examples

## Validation Criteria

The File Discovery implementation must:

1. **Correctly Identify** all files in the project
2. **Properly Filter** based on include/exclude patterns
3. **Accurately Categorize** files by type
4. **Integrate Seamlessly** with the pipeline
5. **Provide Accessible API** for other components

## Related Components

The File Discovery component interacts with:

1. **Pipeline Context**: Stores discovered files for later stages
2. **Code Analysis**: Uses discovered Python files for analysis
3. **Documentation Analysis**: Uses discovered documentation files

## Conclusion

The File Discovery component provides the foundation for the entire analysis pipeline. Its implementation should prioritize accuracy, performance, and ease of integration with other components. By following this guide, you can create a robust file discovery mechanism that meets all requirements of the Project Mapper system.
