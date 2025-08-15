"""Unit tests for file model classes."""

import pytest
from pathlib import Path
from datetime import datetime

from proj_mapper.models.file import FileType, DiscoveredFile


def test_file_type_enum():
    """Test the FileType enumeration."""
    assert FileType.PYTHON.value == "python"
    assert FileType.JAVA.value == "java"
    assert FileType.JAVASCRIPT.value == "javascript"
    assert FileType.TYPESCRIPT.value == "typescript"
    assert FileType.HTML.value == "html"
    assert FileType.CSS.value == "css"
    assert FileType.JSON.value == "json"
    assert FileType.YAML.value == "yaml"
    assert FileType.MARKDOWN.value == "markdown"
    assert FileType.TEXT.value == "text"
    assert FileType.BINARY.value == "binary"
    assert FileType.OTHER.value == "other"


def test_file_type_from_extension():
    """Test determining file type from extension."""
    assert FileType.from_extension(".py") == FileType.PYTHON
    assert FileType.from_extension(".java") == FileType.JAVA
    assert FileType.from_extension(".js") == FileType.JAVASCRIPT
    assert FileType.from_extension(".ts") == FileType.TYPESCRIPT
    assert FileType.from_extension(".html") == FileType.HTML
    assert FileType.from_extension(".css") == FileType.CSS
    assert FileType.from_extension(".json") == FileType.JSON
    assert FileType.from_extension(".yml") == FileType.YAML
    assert FileType.from_extension(".md") == FileType.MARKDOWN
    assert FileType.from_extension(".txt") == FileType.TEXT
    assert FileType.from_extension(".bin") == FileType.BINARY
    assert FileType.from_extension(".unknown") == FileType.UNKNOWN


def test_discovered_file_creation():
    """Test creation of DiscoveredFile objects."""
    file_path = Path("/test/file.py")
    now = datetime.now()
    file = DiscoveredFile(
        path=file_path,
        relative_path="file.py",
        file_type=FileType.PYTHON,
        size=1024,
        modified_time=now,
        created_time=now,
        is_binary=False,
        is_directory=False,
        is_symlink=False
    )
    
    assert file.path == file_path
    assert file.relative_path == "file.py"
    assert file.file_type == FileType.PYTHON
    assert file.size == 1024


def test_discovered_file_create_mock():
    """Test creating a mock DiscoveredFile."""
    file_path = Path("/test/file.py")
    file = DiscoveredFile.create_mock(
        path=file_path,
        relative_path="file.py",
        file_type=FileType.PYTHON
    )
    
    assert file.path == file_path
    assert file.relative_path == "file.py"
    assert file.file_type == FileType.PYTHON
    assert file.size == 1024
    assert isinstance(file.modified_time, datetime)
    assert isinstance(file.created_time, datetime)


def test_discovered_file_to_dict():
    """Test converting DiscoveredFile to dictionary."""
    file_path = Path("/test/file.py")
    now = datetime.now()
    file = DiscoveredFile(
        path=file_path,
        relative_path="file.py",
        file_type=FileType.PYTHON,
        size=1024,
        modified_time=now,
        created_time=now,
        is_binary=False,
        is_directory=False,
        is_symlink=False
    )
    
    data = file.to_dict()
    assert data["path"] == str(file_path)
    assert data["relative_path"] == "file.py"
    assert data["file_type"] == "python"
    assert data["size"] == 1024 