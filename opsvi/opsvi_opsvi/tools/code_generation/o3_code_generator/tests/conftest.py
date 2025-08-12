#!/usr/bin/env python3
"""
Pytest configuration and fixtures for O3 Code Generator tests.

This module provides shared fixtures and test configuration for all tests
in the O3 Code Generator application.
"""

import shutil
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest

from src.tools.code_generation.o3_code_generator.config.core.config_manager import (
    ConfigManager,
)
from src.tools.code_generation.o3_code_generator.o3_logger.logger import get_logger


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_config_manager():
    """Create a mock ConfigManager for testing."""
    config = Mock(spec=ConfigManager)
    config.get.return_value = "test_value"
    config.get_openai_api_key.return_value = "test_api_key"
    config.get_model_name.return_value = "gpt-4"
    config.get_temperature.return_value = 0.1
    config.get_max_tokens.return_value = 2000
    return config


@pytest.fixture
def mock_logger():
    """Create a mock logger for testing."""
    logger = Mock(spec=get_logger())
    logger.info = Mock()
    logger.error = Mock()
    logger.debug = Mock()
    logger.warning = Mock()
    return logger


@pytest.fixture
def mock_openai_client():
    """Create a mock OpenAI client for testing."""
    client = Mock()
    client.chat.completions.create.return_value = Mock(
        choices=[
            Mock(message=Mock(content='{"result": "test_output", "status": "success"}'))
        ]
    )
    return client


@pytest.fixture
def sample_input_data() -> dict[str, Any]:
    """Provide sample input data for testing."""
    return {
        "prompt": "Generate a simple Python function",
        "context_files": ["test_file.py"],
        "output_format": "python",
        "model_name": "gpt-4",
        "temperature": 0.1,
        "max_tokens": 1000,
    }


@pytest.fixture
def sample_output_data() -> dict[str, Any]:
    """Provide sample output data for testing."""
    return {
        "generated_code": "def test_function():\n    return 'Hello, World!'",
        "status": "success",
        "model_used": "gpt-4",
        "tokens_used": 150,
        "processing_time": 2.5,
    }


@pytest.fixture
def sample_file_content() -> str:
    """Provide sample file content for testing."""
    return '''#!/usr/bin/env python3
"""
Sample test file for testing utilities.
"""

import os
from typing import Dict, Any

def sample_function(data: Dict[str, Any]) -> str:
    """Sample function for testing."""
    return f"Processed: {data.get('key', 'default')}"

class SampleClass:
    """Sample class for testing."""

    def __init__(self, name: str):
        self.name = name

    def get_name(self) -> str:
        """Get the name."""
        return self.name
'''


@pytest.fixture
def sample_json_data() -> dict[str, Any]:
    """Provide sample JSON data for testing."""
    return {
        "project_name": "test_project",
        "description": "A test project",
        "requirements": ["pytest", "requests"],
        "files": [{"name": "main.py", "content": "print('Hello, World!')"}],
        "config": {"version": "1.0.0", "author": "Test Author"},
    }
