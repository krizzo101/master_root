"""Pytest configuration and shared fixtures for unified context system tests."""

import asyncio
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Generator
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest

# Test configuration constants
TEST_CONFIG = {
    "database": {
        "test_db_url": "postgresql://test_user:test_password@localhost:5432/test_context_db",
        "timeout": 30,
        "pool_size": 5,
    },
    "performance": {
        "small_load_items": 100,
        "medium_load_items": 1000,
        "large_load_items": 5000,
        "timeout_multiplier": 2.0,
    },
    "integration": {
        "enable_real_db": os.getenv("TEST_REAL_DB", "false").lower() == "true",
        "enable_network": os.getenv("TEST_NETWORK", "false").lower() == "true",
    },
}


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "stress: Stress tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "database: Database tests")
    config.addinivalue_line("markers", "schema: Schema validation tests")
    config.addinivalue_line("markers", "git_adapter: Git adapter tests")
    config.addinivalue_line("markers", "error_adapter: Error adapter tests")
    config.addinivalue_line("markers", "cicd_adapter: CI/CD adapter tests")
    config.addinivalue_line("markers", "adapter_correlation: Adapter correlation tests")
    config.addinivalue_line("markers", "pipeline: Pipeline tests")
    config.addinivalue_line("markers", "real_db: Tests requiring real database")
    config.addinivalue_line("markers", "network: Tests requiring network access")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers and skip conditions."""
    for item in items:
        # Add unit marker to tests without other markers
        if not any(
            mark.name in ["integration", "e2e", "performance", "stress"]
            for mark in item.iter_markers()
        ):
            item.add_marker(pytest.mark.unit)

        # Skip network tests if network access not enabled
        if "network" in [mark.name for mark in item.iter_markers()]:
            if not TEST_CONFIG["integration"]["enable_network"]:
                item.add_marker(pytest.mark.skip(reason="Network tests disabled"))

        # Skip real database tests if not enabled
        if "real_db" in [mark.name for mark in item.iter_markers()]:
            if not TEST_CONFIG["integration"]["enable_real_db"]:
                item.add_marker(pytest.mark.skip(reason="Real database tests disabled"))


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_database():
    """Mock database connection for testing."""
    db_mock = AsyncMock()

    # Mock basic operations
    db_mock.execute.return_value = None
    db_mock.fetch.return_value = []
    db_mock.fetchrow.return_value = None
    db_mock.fetchval.return_value = None

    # Mock transaction
    transaction_mock = AsyncMock()
    transaction_mock.__aenter__.return_value = transaction_mock
    transaction_mock.__aexit__.return_value = None
    db_mock.transaction.return_value = transaction_mock

    # Mock connection pool
    pool_mock = AsyncMock()
    pool_mock.acquire.return_value.__aenter__.return_value = db_mock
    pool_mock.close = AsyncMock()

    return db_mock


@pytest.fixture
def test_workspace(tmp_path):
    """Create temporary workspace for tests."""
    workspace = {
        "root": tmp_path,
        "repo": tmp_path / "test_repo",
        "logs": tmp_path / "logs",
        "config": tmp_path / "config",
        "output": tmp_path / "output",
    }

    # Create directories
    for path in workspace.values():
        if isinstance(path, Path):
            path.mkdir(exist_ok=True)

    return workspace


@pytest.fixture
def sample_git_data():
    """Sample git data for testing."""
    return {
        "commits": [
            {
                "hash": "abc123def456",
                "author": "John Developer",
                "author_email": "john@example.com",
                "commit_date": "2024-01-15 10:00:00 +0000",
                "subject": "feat: Add user authentication",
                "body": "Implement JWT-based authentication system",
                "changed_files": [
                    {"type": "A", "file": "src/auth.py"},
                    {"type": "M", "file": "src/models/user.py"},
                ],
            },
            {
                "hash": "def456abc789",
                "author": "Jane Developer",
                "author_email": "jane@example.com",
                "commit_date": "2024-01-14 15:30:00 +0000",
                "subject": "fix: Resolve database connection issue",
                "body": "Fix connection pooling and timeout handling",
                "changed_files": [{"type": "M", "file": "src/database.py"}],
            },
        ],
        "branches": [
            {"name": "main", "commit_hash": "abc123def456"},
            {"name": "feature/auth", "commit_hash": "def456abc789"},
        ],
    }


@pytest.fixture
def sample_error_data():
    """Sample error data for testing."""
    return {
        "errors": [
            {
                "error_id": "error_001",
                "message": "Authentication failed for user@example.com",
                "severity": "error",
                "timestamp": datetime(2024, 1, 15, 10, 15, tzinfo=timezone.utc),
                "file_path": "src/auth.py",
                "line_number": 45,
                "error_type": "AuthenticationError",
                "stack_trace": "at auth.validateToken(auth.py:45)\nat middleware.authenticate(middleware.py:12)",
            },
            {
                "error_id": "error_002",
                "message": "Database connection timeout",
                "severity": "error",
                "timestamp": datetime(2024, 1, 15, 10, 20, tzinfo=timezone.utc),
                "file_path": "src/database.py",
                "line_number": 123,
                "error_type": "ConnectionTimeoutError",
            },
        ]
    }


@pytest.fixture
def sample_cicd_data():
    """Sample CI/CD data for testing."""
    return {
        "github_workflows": [
            {
                "id": 123456789,
                "name": "CI",
                "head_branch": "main",
                "head_sha": "abc123def456",
                "status": "completed",
                "conclusion": "success",
                "created_at": "2024-01-15T10:05:00Z",
                "updated_at": "2024-01-15T10:10:00Z",
                "actor": {"login": "john-developer"},
            },
            {
                "id": 987654321,
                "name": "Deploy",
                "head_branch": "main",
                "head_sha": "abc123def456",
                "status": "completed",
                "conclusion": "failure",
                "created_at": "2024-01-15T10:15:00Z",
                "updated_at": "2024-01-15T10:20:00Z",
                "actor": {"login": "deployment-bot"},
            },
        ],
        "gitlab_pipelines": [
            {
                "id": 456789,
                "status": "success",
                "ref": "main",
                "sha": "abc123def456",
                "created_at": "2024-01-15T10:25:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
                "user": {"username": "developer1"},
            }
        ],
    }


@pytest.fixture
def performance_config():
    """Performance test configuration."""
    return TEST_CONFIG["performance"]


@pytest.fixture
def integration_config():
    """Integration test configuration."""
    return TEST_CONFIG["integration"]


@pytest.fixture
def mock_http_session():
    """Mock HTTP session for API tests."""
    session_mock = AsyncMock()
    response_mock = AsyncMock()

    # Configure response mock
    response_mock.status = 200
    response_mock.json = AsyncMock()
    response_mock.text = AsyncMock()
    response_mock.raise_for_status = Mock()

    # Configure session mock
    session_mock.get.return_value.__aenter__.return_value = response_mock
    session_mock.post.return_value.__aenter__.return_value = response_mock
    session_mock.close = AsyncMock()

    return session_mock, response_mock


@pytest.fixture
def mock_file_system(test_workspace):
    """Mock file system operations."""

    def create_test_file(relative_path: str, content: str):
        """Create a test file with content."""
        file_path = test_workspace["root"] / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
        return file_path

    def create_log_file(filename: str, log_entries: list):
        """Create a log file with entries."""
        log_path = test_workspace["logs"] / filename
        log_content = "\n".join(log_entries)
        log_path.write_text(log_content)
        return log_path

    return {
        "create_file": create_test_file,
        "create_log": create_log_file,
        "workspace": test_workspace,
    }


@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Cleanup after each test."""
    yield  # Run the test

    # Cleanup any lingering async tasks
    try:
        loop = asyncio.get_running_loop()
        tasks = [task for task in asyncio.all_tasks(loop) if not task.done()]
        for task in tasks:
            task.cancel()
    except RuntimeError:
        pass  # No running loop


# Parametrized fixtures for different test scenarios
@pytest.fixture(params=["small", "medium", "large"])
def load_size(request, performance_config):
    """Parametrized fixture for different load sizes."""
    sizes = {
        "small": performance_config["small_load_items"],
        "medium": performance_config["medium_load_items"],
        "large": performance_config["large_load_items"],
    }
    return sizes[request.param]


@pytest.fixture(params=["git", "error", "cicd"])
def adapter_type(request):
    """Parametrized fixture for different adapter types."""
    return request.param


# Test data generators
class TestDataGenerator:
    """Generate test data for various scenarios."""

    @staticmethod
    def generate_commits(count: int) -> list:
        """Generate test commit data."""
        commits = []
        for i in range(count):
            commit = {
                "hash": f"commit_{i:08x}",
                "author": f"Developer {i % 10}",
                "author_email": f"dev{i % 10}@example.com",
                "commit_date": f"2024-01-{15 + (i % 15):02d} {10 + (i % 12):02d}:00:00 +0000",
                "subject": f"Commit {i}: Feature implementation",
                "body": f"Detailed description of commit {i}",
                "changed_files": [
                    {"type": "M", "file": f"src/module_{i % 20}.py"},
                    {
                        "type": "A" if i % 5 == 0 else "M",
                        "file": f"tests/test_{i % 15}.py",
                    },
                ],
            }
            commits.append(commit)
        return commits

    @staticmethod
    def generate_errors(count: int) -> list:
        """Generate test error data."""
        errors = []
        severities = ["error", "warning", "info"]
        error_types = ["AuthError", "NetworkError", "ValidationError", "DatabaseError"]

        for i in range(count):
            error = {
                "error_id": f"error_{i:06d}",
                "message": f"Error {i}: Something went wrong",
                "severity": severities[i % len(severities)],
                "timestamp": datetime(2024, 1, 15, 10, i % 60, tzinfo=timezone.utc),
                "file_path": f"src/module_{i % 25}.py",
                "line_number": (i % 1000) + 1,
                "error_type": error_types[i % len(error_types)],
                "source": "logs",
            }
            errors.append(error)
        return errors

    @staticmethod
    def generate_workflows(count: int) -> list:
        """Generate test workflow data."""
        workflows = []
        statuses = ["completed", "in_progress", "queued"]
        conclusions = ["success", "failure", "cancelled"]

        for i in range(count):
            workflow = {
                "id": 1000000 + i,
                "name": f"Workflow {i}",
                "head_branch": f"branch_{i % 10}",
                "head_sha": f"sha_{i:08x}",
                "status": statuses[i % len(statuses)],
                "conclusion": conclusions[i % len(conclusions)],
                "created_at": f"2024-01-15T{10 + (i % 12):02d}:00:00Z",
                "updated_at": f"2024-01-15T{10 + (i % 12):02d}:05:00Z",
                "actor": {"login": f"user_{i % 20}"},
            }
            workflows.append(workflow)
        return workflows


@pytest.fixture
def test_data_generator():
    """Test data generator fixture."""
    return TestDataGenerator()


# Performance monitoring fixtures
@pytest.fixture
def performance_monitor():
    """Performance monitoring fixture."""
    try:
        import psutil

        class PerformanceMonitor:
            def __init__(self):
                self.start_time = None
                self.end_time = None
                self.start_memory = None
                self.peak_memory = None
                self.measurements = []

            def start(self):
                self.start_time = psutil.time.time()
                self.start_memory = psutil.Process().memory_info().rss / 1024 / 1024
                self.peak_memory = self.start_memory

            def stop(self):
                self.end_time = psutil.time.time()
                current_memory = psutil.Process().memory_info().rss / 1024 / 1024
                if current_memory > self.peak_memory:
                    self.peak_memory = current_memory

            def record(self, label: str, value: float):
                self.measurements.append((label, value))

            def get_metrics(self):
                return {
                    "duration": self.end_time - self.start_time
                    if self.end_time
                    else None,
                    "memory_used": self.peak_memory - self.start_memory
                    if self.peak_memory
                    else None,
                    "peak_memory": self.peak_memory,
                    "measurements": dict(self.measurements),
                }

        return PerformanceMonitor()

    except ImportError:
        # Fallback if psutil not available
        class MockPerformanceMonitor:
            def start(self):
                pass

            def stop(self):
                pass

            def record(self, label: str, value: float):
                pass

            def get_metrics(self):
                return {}

        return MockPerformanceMonitor()


# Skip conditions for different test types
def pytest_runtest_setup(item):
    """Setup function to handle test skipping."""
    # Skip performance tests in regular runs unless explicitly requested
    if "performance" in [mark.name for mark in item.iter_markers()]:
        if not item.config.getoption(
            "-m"
        ) or "performance" not in item.config.getoption("-m"):
            pytest.skip("Performance tests require -m performance flag")

    # Skip slow tests unless explicitly requested
    if "slow" in [mark.name for mark in item.iter_markers()]:
        if not item.config.getoption("--run-slow"):
            pytest.skip("Slow tests require --run-slow flag")


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--run-slow", action="store_true", default=False, help="Run slow tests"
    )
    parser.addoption(
        "--test-db-url",
        action="store",
        default=TEST_CONFIG["database"]["test_db_url"],
        help="Test database URL",
    )
    parser.addoption(
        "--performance-multiplier",
        action="store",
        type=float,
        default=1.0,
        help="Performance test timeout multiplier",
    )


# Test utilities
class TestUtilities:
    """Utility functions for tests."""

    @staticmethod
    def assert_context_item_valid(item):
        """Assert that a context item is valid."""
        assert item.id is not None
        assert item.source_type is not None
        assert item.source_id is not None
        assert len(item.source_id) > 0

        if item.timestamp:
            assert isinstance(item.timestamp, datetime)

        if item.metrics:
            assert isinstance(item.metrics, dict)

        if item.tags:
            assert isinstance(item.tags, list)
            assert all(isinstance(tag, str) for tag in item.tags)

    @staticmethod
    def assert_relationship_valid(relationship_tuple):
        """Assert that a relationship tuple is valid."""
        assert len(relationship_tuple) == 3
        rel_type, target_id, confidence = relationship_tuple

        assert isinstance(rel_type, str)
        assert len(rel_type) > 0
        assert target_id is not None
        assert isinstance(confidence, (int, float))
        assert 0.0 <= confidence <= 1.0

    @staticmethod
    def create_mock_adapter(adapter_type: str, item_count: int = 10):
        """Create a mock adapter for testing."""
        adapter_mock = AsyncMock()

        # Generate test data based on adapter type
        if adapter_type == "git":
            test_items = TestDataGenerator.generate_commits(item_count)
        elif adapter_type == "error":
            test_items = TestDataGenerator.generate_errors(item_count)
        elif adapter_type == "cicd":
            test_items = TestDataGenerator.generate_workflows(item_count)
        else:
            test_items = [{"id": i, "data": f"item_{i}"} for i in range(item_count)]

        async def mock_fetch_items(*args, **kwargs):
            for item in test_items:
                yield item

        adapter_mock.fetch_items.return_value = mock_fetch_items()
        return adapter_mock, test_items


@pytest.fixture
def test_utils():
    """Test utilities fixture."""
    return TestUtilities()
