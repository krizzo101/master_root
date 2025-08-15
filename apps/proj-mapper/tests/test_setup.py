"""
Test file to validate that the development environment is set up correctly.
"""
import sys
from importlib.util import find_spec


def test_python_version() -> None:
    """Test that Python version is 3.8 or higher."""
    major, minor = sys.version_info[:2]
    assert major == 3 and minor >= 8, f"Python version should be 3.8+, got {major}.{minor}"


def test_dependencies_installed() -> None:
    """Test that required dependencies are installed."""
    dependencies = [
        "markdown_it",  # from markdown-it-py
        "yaml",  # from pyyaml
        "pytest",
        "black",
        "isort",
        "flake8",
        "mypy",
    ]

    for dependency in dependencies:
        spec = find_spec(dependency)
        assert spec is not None, f"Dependency {dependency} is not installed"


def test_project_importable() -> None:
    """Test that the proj_mapper package is importable."""
    spec = find_spec("proj_mapper")
    assert spec is not None, "proj_mapper is not importable" 