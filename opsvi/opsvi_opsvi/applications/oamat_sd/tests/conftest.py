"""
Pytest configuration and shared fixtures for Smart Decomposition tests

This module provides common fixtures and test configuration for the entire test suite.
"""

import asyncio
from collections.abc import Generator
from pathlib import Path

# Add project root to path for imports
import sys
import tempfile
from typing import Any, Dict
from unittest.mock import AsyncMock

import pytest

project_root = Path(__file__).parents[4]
sys.path.insert(0, str(project_root))

# Add current project to path for relative imports
current_project = Path(__file__).parents[1]
sys.path.insert(0, str(current_project))


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create temporary directory for test files"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def sample_test_requests() -> Dict[str, str]:
    """Provide sample test requests for various complexity levels"""
    return {
        "simple": "What is Python?",
        "medium": "Create a REST API for user management with authentication",
        "complex": "Build a complete e-commerce platform with microservices architecture",
    }


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing"""
    mock_client = AsyncMock()
    mock_client.chat.completions.create.return_value = AsyncMock(
        choices=[
            AsyncMock(
                message=AsyncMock(content="Mock response from OpenAI", tool_calls=None)
            )
        ]
    )
    return mock_client


@pytest.fixture
def mock_complexity_analysis() -> Dict[str, Any]:
    """Provide mock complexity analysis for testing"""
    return {
        "complexity_score": 5.5,
        "execution_strategy": "multi_agent",
        "factors": {
            "scope": 7,
            "technical_depth": 6,
            "domain_knowledge": 5,
            "dependencies": 4,
            "timeline": 3,
            "risk": 2,
        },
        "recommended_agents": ["researcher", "analyst", "synthesizer"],
    }


@pytest.fixture
def mock_agent_output() -> Dict[str, Any]:
    """Provide mock agent output for testing"""
    return {
        "success": True,
        "agent_role": "researcher",
        "content": "Mock research findings about Python web frameworks",
        "metadata": {
            "execution_time": 2.5,
            "tools_used": ["brave_search", "arxiv_research"],
            "confidence": 0.85,
        },
    }


@pytest.fixture
def mock_solution_artifact() -> Dict[str, Any]:
    """Provide mock solution artifact for testing"""
    return {
        "artifact_type": "research_report",
        "content": "Comprehensive analysis of Python web frameworks including Django, FastAPI, and Flask...",
        "metadata": {
            "word_count": 1500,
            "sections": [
                "executive_summary",
                "framework_comparison",
                "recommendations",
            ],
            "confidence": 0.9,
        },
    }


# Pytest collection configuration
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test location"""
    for item in items:
        # Add markers based on test file location
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)

        # Add slow marker for tests that might take longer
        if "performance" in str(item.fspath) or "benchmark" in item.name:
            item.add_marker(pytest.mark.slow)


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom settings"""
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests (deselect with '-m \"not unit\"')"
    )
    config.addinivalue_line(
        "markers",
        "integration: marks tests as integration tests (deselect with '-m \"not integration\"')",
    )
    config.addinivalue_line(
        "markers",
        "e2e: marks tests as end-to-end tests (deselect with '-m \"not e2e\"')",
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
