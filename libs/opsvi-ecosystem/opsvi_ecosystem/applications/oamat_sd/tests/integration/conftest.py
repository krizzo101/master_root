"""
Integration Test Configuration for Real MCP Client Testing

Provides fixtures and setup for testing real MCP implementations with
proper environment variable handling and path resolution.
"""

import logging
import os
import sys
from pathlib import Path

import pytest


# Ensure proper import path for shared MCP tools
def ensure_project_path():
    """Ensure project root is in sys.path for shared tool imports"""
    current = Path(__file__).resolve()
    # From tests/integration/conftest.py, go up to project root
    # conftest.py -> integration -> tests -> oama_sd -> applications -> src -> agent_world
    project_root = current.parents[5]  # Go up 6 levels (parents[5])

    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
        logging.info(f"Added project root to sys.path: {project_root}")

    return project_root


# Ensure path is available during import
ensure_project_path()

from src.applications.oamat_sd.src.tools.mcp_tool_registry import MCPToolRegistry


@pytest.fixture(scope="session", autouse=True)
def integration_test_setup():
    """Session-wide setup for integration tests"""
    # Ensure project root is in path
    project_root = ensure_project_path()

    # Verify shared tools are accessible
    shared_mcp = project_root / "src" / "shared" / "mcp"
    if not shared_mcp.exists():
        pytest.skip(f"Shared MCP tools not found at {shared_mcp}")

    logging.info(f"Integration test setup complete. Project root: {project_root}")


@pytest.fixture
def real_client_registry():
    """Create MCPToolRegistry with real clients enabled"""
    # Force real clients regardless of test environment
    os.environ["SMART_DECOMP_USE_REAL_MCP"] = "true"

    # Create registry with explicit real client mode
    registry = MCPToolRegistry(use_real_clients=True)

    yield registry

    # Cleanup
    if "SMART_DECOMP_USE_REAL_MCP" in os.environ:
        del os.environ["SMART_DECOMP_USE_REAL_MCP"]


@pytest.fixture
def mock_client_registry():
    """Create MCPToolRegistry with mock clients for comparison"""
    # Explicitly force mock clients
    registry = MCPToolRegistry(use_real_clients=False)
    return registry


@pytest.fixture
def performance_tracker():
    """Track execution times for performance analysis"""
    tracker = {"execution_times": [], "start_time": None, "results": [], "errors": []}
    return tracker


@pytest.fixture(scope="session")
def api_keys_available():
    """Check if required API keys are available for real API testing"""
    required_keys = {
        "BRAVE_API_KEY": "Brave Search API",
        "FIRECRAWL_API_KEY": "Firecrawl API",
        "CONTEXT7_API_KEY": "Context7 API",
    }

    available_keys = {}
    missing_keys = []

    for key, service in required_keys.items():
        if os.getenv(key):
            available_keys[key] = service
        else:
            missing_keys.append(f"{key} ({service})")

    if missing_keys:
        logging.warning(f"Missing API keys: {', '.join(missing_keys)}")
        logging.info("Some real API tests may be skipped")

    return {
        "available": available_keys,
        "missing": missing_keys,
        "has_any": len(available_keys) > 0,
    }


@pytest.fixture
def integration_test_markers():
    """Provide test markers for conditional execution"""
    return {
        "real_api_enabled": os.getenv("REAL_MCP_TESTS", "").lower()
        in ("1", "true", "yes"),
        "network_available": True,  # Can be enhanced with actual network check
        "slow_tests_enabled": os.getenv("SLOW_TESTS", "1").lower()
        in ("1", "true", "yes"),
    }


def pytest_configure(config):
    """Configure pytest markers for integration tests"""
    config.addinivalue_line(
        "markers",
        "real_api: Tests that make actual API calls (requires REAL_MCP_TESTS=1)",
    )
    config.addinivalue_line("markers", "performance: Performance benchmark tests")
    config.addinivalue_line("markers", "network: Tests requiring network connectivity")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to handle conditional execution"""

    # Skip real API tests if not enabled
    real_api_enabled = os.getenv("REAL_MCP_TESTS", "").lower() in ("1", "true", "yes")

    if not real_api_enabled:
        skip_real_api = pytest.mark.skip(
            reason="Real MCP tests disabled. Set REAL_MCP_TESTS=1 to enable"
        )
        for item in items:
            if "real_api" in item.keywords:
                item.add_marker(skip_real_api)

    # Skip slow tests if disabled
    slow_tests_enabled = os.getenv("SLOW_TESTS", "1").lower() in ("1", "true", "yes")
    if not slow_tests_enabled:
        skip_slow = pytest.mark.skip(
            reason="Slow tests disabled. Set SLOW_TESTS=1 to enable"
        )
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)
