"""Configuration file for pytest."""

import os
import sys
from pathlib import Path

import pytest

# Add the src directory to the path to make imports work
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def project_root():
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def src_dir(project_root):
    """Return the src directory."""
    return project_root / "src"


@pytest.fixture
def temp_dir(tmp_path):
    """Return a temporary directory for tests."""
    return tmp_path 