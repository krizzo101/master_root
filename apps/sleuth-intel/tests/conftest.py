"""Global pytest configuration and fixtures."""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Generator, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from aiohttp import ClientSession

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.models import Business, IntelligenceReport, Person, Query
from tests.fixtures.mock_data import MockDataGenerator
from tests.utils.test_helpers import TestAPIClient, create_test_config


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_config():
    """Provide test configuration."""
    return create_test_config()


@pytest.fixture
def mock_data_generator():
    """Provide mock data generator."""
    return MockDataGenerator()


@pytest.fixture
def sample_person(mock_data_generator):
    """Create a sample person object."""
    return mock_data_generator.create_person()


@pytest.fixture
def sample_business(mock_data_generator):
    """Create a sample business object."""
    return mock_data_generator.create_business()


@pytest.fixture
def sample_query():
    """Create a sample query object."""
    return Query(
        query_type="person_search",
        parameters={
            "first_name": "John",
            "last_name": "Doe",
            "city": "New York",
            "state": "NY",
        },
        metadata={"request_id": "test-123", "timestamp": datetime.now().isoformat()},
    )


@pytest_asyncio.fixture
async def mock_http_session():
    """Create a mock HTTP session."""
    async with ClientSession() as session:
        yield session


@pytest.fixture
def mock_api_client():
    """Create a mock API client."""
    client = MagicMock()
    client.search_person = AsyncMock(return_value=[])
    client.search_business = AsyncMock(return_value=[])
    client.search_email = AsyncMock(return_value=[])
    client.search_phone = AsyncMock(return_value=[])
    client.search_address = AsyncMock(return_value=[])
    return client


@pytest.fixture
def mock_redis_client():
    """Create a mock Redis client."""
    client = MagicMock()
    client.get = AsyncMock(return_value=None)
    client.set = AsyncMock(return_value=True)
    client.delete = AsyncMock(return_value=True)
    client.exists = AsyncMock(return_value=False)
    client.expire = AsyncMock(return_value=True)
    return client


@pytest.fixture
def mock_message_bus():
    """Create a mock message bus."""
    bus = MagicMock()
    bus.publish = AsyncMock(return_value=True)
    bus.subscribe = AsyncMock()
    bus.unsubscribe = AsyncMock()
    return bus


@pytest.fixture
def mock_orchestrator(mock_api_client, mock_redis_client, mock_message_bus):
    """Create a mock orchestrator."""
    orchestrator = MagicMock()
    orchestrator.api_client = mock_api_client
    orchestrator.redis_client = mock_redis_client
    orchestrator.message_bus = mock_message_bus
    orchestrator.execute = AsyncMock()
    return orchestrator


@pytest.fixture
def mock_agent():
    """Create a mock agent."""
    agent = MagicMock()
    agent.execute = AsyncMock()
    agent.validate = AsyncMock(return_value=True)
    agent.name = "test_agent"
    agent.capabilities = ["search", "analyze"]
    return agent


@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment variables for each test."""
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def capture_logs():
    """Capture log output for testing."""
    logs = []

    def log_capture(message, level="INFO", **kwargs):
        logs.append(
            {
                "message": message,
                "level": level,
                "timestamp": datetime.now().isoformat(),
                **kwargs,
            }
        )

    return logs, log_capture


@pytest.fixture
def performance_timer():
    """Provide a performance timer for tests."""
    import time

    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
            self.elapsed = None

        def start(self):
            self.start_time = time.perf_counter()

        def stop(self):
            self.end_time = time.perf_counter()
            self.elapsed = self.end_time - self.start_time
            return self.elapsed

        def __enter__(self):
            self.start()
            return self

        def __exit__(self, *args):
            self.stop()

    return Timer


@pytest.fixture
def test_api_client(test_config):
    """Create a test API client."""
    return TestAPIClient(test_config)


@pytest.fixture
def mock_openai_client():
    """Create a mock OpenAI client."""
    client = MagicMock()
    client.chat.completions.create = AsyncMock(
        return_value=MagicMock(
            choices=[MagicMock(message=MagicMock(content="Mock AI response"))]
        )
    )
    return client


@pytest.fixture
def temp_directory(tmp_path):
    """Create a temporary directory for test files."""
    test_dir = tmp_path / "test_data"
    test_dir.mkdir()
    return test_dir


@pytest.fixture
def sample_intelligence_report():
    """Create a sample intelligence report."""
    return IntelligenceReport(
        subject="John Doe",
        summary="Test intelligence report",
        findings=[
            {
                "category": "personal",
                "confidence": 0.95,
                "data": {"name": "John Doe", "age": 35},
            }
        ],
        risk_assessment={"level": "low", "factors": []},
        recommendations=["No action required"],
        metadata={"generated_at": datetime.now().isoformat(), "version": "1.0"},
    )
