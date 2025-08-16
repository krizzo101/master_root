"""Unit tests for the file discovery module."""

import os
import pytest
import tempfile
from pathlib import Path

from proj_mapper.core.file_discovery import FileDiscovery
from proj_mapper.models.file import FileType, DiscoveredFile


@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory structure for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a simple project structure
        project_root = Path(temp_dir)
        
        # Create src directory with Python files
        src_dir = project_root / "src"
        src_dir.mkdir()
        
        py_file1 = src_dir / "main.py"
        py_file1.write_text("print('Hello, world!')")
        
        py_file2 = src_dir / "utils.py"
        py_file2.write_text("def get_greeting(): return 'Hello'")
        
        # Create tests directory
        tests_dir = project_root / "tests"
        tests_dir.mkdir()
        
        test_file = tests_dir / "test_main.py"
        test_file.write_text("def test_main(): assert True")
        
        # Create docs directory with markdown
        docs_dir = project_root / "docs"
        docs_dir.mkdir()
        
        md_file = docs_dir / "readme.md"
        md_file.write_text("# Project Documentation")
        
        # Create .git directory (should be excluded)
        git_dir = project_root / ".git"
        git_dir.mkdir()
        
        git_file = git_dir / "HEAD"
        git_file.write_text("ref: refs/heads/main")
        
        # Create node_modules directory (should be excluded)
        node_dir = project_root / "node_modules"
        node_dir.mkdir()
        
        node_file = node_dir / "package.json"
        node_file.write_text("{}")
        
        yield project_root


def test_file_discovery_init():
    """Test FileDiscovery initialization with default and custom values."""
    # Default values
    discovery = FileDiscovery()
    assert discovery.include_patterns == ["**/*"]
    assert discovery.exclude_patterns == []
    assert discovery.max_file_size == 1048576  # 1MB
    
    # Custom values
    custom_discovery = FileDiscovery(
        include_patterns=["**/*.py"],
        exclude_patterns=["**/test_*.py"],
        max_file_size=2048
    )
    assert custom_discovery.include_patterns == ["**/*.py"]
    assert custom_discovery.exclude_patterns == ["**/test_*.py"]
    assert custom_discovery.max_file_size == 2048


def test_discover_files(temp_project_dir):
    """Test discovering files in a project directory."""
    discovery = FileDiscovery(
        include_patterns=["**/*"],
        exclude_patterns=["**/.git/**", "**/node_modules/**"]
    )
    
    files = discovery.discover_files(temp_project_dir)
    
    # Check that we found the expected files
    assert len(files) >= 4  # At least our 4 explicit files
    
    # Verify all returned objects are DiscoveredFile instances
    for file in files:
        assert isinstance(file, DiscoveredFile)
    
    # Check that excluded directories were not included
    for file in files:
        assert ".git" not in str(file.path)
        assert "node_modules" not in str(file.path)


def test_categorize_files(temp_project_dir):
    """Test categorizing files by type."""
    discovery = FileDiscovery(
        include_patterns=["**/*"],
        exclude_patterns=["**/.git/**", "**/node_modules/**"]
    )
    
    files = discovery.discover_files(temp_project_dir)
    categorized = discovery.categorize_files(files)
    
    # Check that we have Python and Markdown categories
    assert FileType.PYTHON in categorized
    assert FileType.MARKDOWN in categorized
    
    # Verify Python files are correctly categorized
    python_files = categorized[FileType.PYTHON]
    assert len(python_files) >= 3  # main.py, utils.py, test_main.py
    
    # Verify Markdown files are correctly categorized
    markdown_files = categorized[FileType.MARKDOWN]
    assert len(markdown_files) >= 1  # readme.md


def test_filter_files_by_type(temp_project_dir):
    """Test filtering files by type."""
    discovery = FileDiscovery()
    
    files = discovery.discover_files(temp_project_dir)
    python_files = discovery.filter_files_by_type(files, FileType.PYTHON)
    
    # Check that we only have Python files
    assert len(python_files) >= 3  # main.py, utils.py, test_main.py
    for file in python_files:
        assert file.file_type == FileType.PYTHON


def test_filter_files_by_pattern(temp_project_dir):
    """Test filtering files by pattern."""
    discovery = FileDiscovery()
    
    files = discovery.discover_files(temp_project_dir)
    
    # Filter for test files
    test_files = discovery.filter_files_by_pattern(files, "**/test_*.py")
    assert len(test_files) == 1  # test_main.py
    
    # Filter for markdown files
    md_files = discovery.filter_files_by_pattern(files, "**/*.md")
    assert len(md_files) == 1  # readme.md


def test_discover_with_max_file_size(temp_project_dir):
    """Test discovering files with max file size restriction."""
    # Set a very small max file size to exclude all files
    discovery = FileDiscovery(max_file_size=10)  # 10 bytes
    
    files = discovery.discover_files(temp_project_dir)
    
    # Most files should be excluded due to size restriction
    for file in files:
        assert file.metadata.size <= 10


def test_discover_empty_directory():
    """Test discovering files in an empty directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        discovery = FileDiscovery()
        files = discovery.discover_files(temp_dir)
        
        # Should be an empty list
        assert len(files) == 0


def test_discover_non_existent_directory():
    """Test discovering files in a non-existent directory."""
    discovery = FileDiscovery()
    
    with pytest.raises(ValueError):
        discovery.discover_files("/path/does/not/exist")


def test_discover_file_not_directory():
    """Test discovering files with a file path instead of directory."""
    # Create a temporary file
    with tempfile.NamedTemporaryFile() as temp_file:
        discovery = FileDiscovery()
        
        with pytest.raises(ValueError):
            discovery.discover_files(temp_file.name) 