#!/usr/bin/env python3
"""
PyTest Configuration and Fixtures for DPO Testing

Provides shared fixtures, configuration, and utilities for all DPO tests.
"""

import asyncio
import json
import logging
import sys
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest
import yaml

sys.path.append(str(Path(__file__).parent.parent))

from src.dpo_main_controller import DevelopmentProcessOrchestrator, DPOConfiguration
from tests.fixtures.mock_orchestrator import (
    MockOrchestratorClient,
    MockOrchestratorServer,
)
from tests.fixtures.sample_data import SampleRequestGenerator, SampleWorkflowData

# Configure logging for tests
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Pytest configuration
pytest_plugins = ["pytest_asyncio"]


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace for testing."""
    temp_dir = tempfile.mkdtemp(prefix="dpo_test_")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_config():
    """Provide mock configuration for testing."""
    return {
        "ai_provider": "mock",
        "max_parallel_agents": 3,
        "orchestrator_path": "/mock/orchestrator",
        "output_directory": "/tmp/dpo_test_output",
        "enable_monitoring": False,
        "enable_performance_tracking": True,
        "request_timeout": 30,
        "workflow_timeout": 300,
        "retry_attempts": 2,
        "quality_gates": {
            "enabled": True,
            "thresholds": {
                "code_coverage": 80,
                "test_pass_rate": 95,
                "performance_score": 85,
            },
        },
    }


@pytest.fixture
def sample_requests():
    """Provide sample request data for testing."""
    return {
        "simple_api": {
            "type": "api_development",
            "description": "Create a REST API for user management",
            "requirements": [
                "CRUD operations for users",
                "Authentication with JWT",
                "Input validation",
            ],
            "technology_stack": ["Python", "FastAPI", "PostgreSQL"],
        },
        "complex_fullstack": {
            "type": "fullstack_application",
            "description": "Build a complete e-commerce platform",
            "requirements": [
                "Product catalog with search",
                "Shopping cart and checkout",
                "User accounts and orders",
                "Admin dashboard",
                "Payment integration",
            ],
            "technology_stack": ["React", "Node.js", "MongoDB", "Stripe"],
        },
        "cli_tool": {
            "type": "cli_development",
            "description": "Develop a CLI tool for file synchronization",
            "requirements": [
                "Bidirectional sync",
                "Conflict resolution",
                "Progress reporting",
                "Configuration management",
            ],
            "technology_stack": ["Python", "Click"],
        },
        "integration": {
            "type": "integration_connector",
            "description": "Create Salesforce to HubSpot integration",
            "requirements": [
                "Contact synchronization",
                "Deal pipeline mapping",
                "Custom field mapping",
                "Error handling and retry",
            ],
            "technology_stack": ["Python", "REST APIs", "Webhooks"],
        },
        "malformed": {
            "type": "unknown",
            "description": "This is a malformed request",
            "requirements": None,
            "technology_stack": [],
        },
    }


@pytest.fixture
def mock_orchestrator_response():
    """Provide mock orchestrator response for testing."""
    return {
        "workflow_id": "test_workflow_123",
        "status": "submitted",
        "agents": [
            {"id": "agent_1", "type": "architect", "status": "pending"},
            {"id": "agent_2", "type": "developer", "status": "pending"},
        ],
        "estimated_completion": "2024-09-09T00:00:00Z",
        "output_directory": "/tmp/test_output",
    }


@pytest.fixture
def mock_ai_client():
    """Mock AI client for testing without actual API calls."""

    class MockAIClient:
        def __init__(self):
            self.call_count = 0
            self.responses = []

        async def generate(self, prompt, model="gpt-4"):
            self.call_count += 1
            # Return predefined responses based on prompt content
            if "classify" in prompt.lower():
                return json.dumps(
                    {
                        "type": "api_development",
                        "confidence": 0.95,
                        "complexity": "medium",
                    }
                )
            elif "enhance" in prompt.lower():
                return json.dumps(
                    {
                        "enhancements": [
                            {
                                "type": "performance",
                                "suggestion": "Implement caching strategy",
                                "priority": "high",
                            }
                        ]
                    }
                )
            elif "template" in prompt.lower():
                return json.dumps(
                    {
                        "workflow": {
                            "phases": ["planning", "development", "testing"],
                            "agents": ["architect", "developer", "tester"],
                        }
                    }
                )
            else:
                return json.dumps({"status": "success", "data": {}})

        def reset(self):
            self.call_count = 0
            self.responses = []

    return MockAIClient()


@pytest.fixture
def performance_tracker():
    """Track performance metrics during tests."""

    class PerformanceTracker:
        def __init__(self):
            self.metrics = {}
            self.start_times = {}

        def start(self, operation: str):
            self.start_times[operation] = datetime.now()

        def end(self, operation: str):
            if operation in self.start_times:
                duration = (
                    datetime.now() - self.start_times[operation]
                ).total_seconds()
                if operation not in self.metrics:
                    self.metrics[operation] = []
                self.metrics[operation].append(duration)
                del self.start_times[operation]
                return duration
            return None

        def get_stats(self, operation: str = None):
            if operation:
                if operation in self.metrics:
                    values = self.metrics[operation]
                    return {
                        "count": len(values),
                        "total": sum(values),
                        "average": sum(values) / len(values),
                        "min": min(values),
                        "max": max(values),
                    }
                return None
            return self.metrics

        def reset(self):
            self.metrics = {}
            self.start_times = {}

    return PerformanceTracker()


@pytest.fixture
def test_database():
    """Provide test database connection for integration tests."""

    # This would be replaced with actual test database setup
    class TestDatabase:
        def __init__(self):
            self.data = {}

        def save(self, key: str, value: Any):
            self.data[key] = value

        def get(self, key: str):
            return self.data.get(key)

        def delete(self, key: str):
            if key in self.data:
                del self.data[key]

        def clear(self):
            self.data = {}

        def list_keys(self):
            return list(self.data.keys())

    db = TestDatabase()
    yield db
    db.clear()


@pytest.fixture
def capture_logs():
    """Capture and analyze logs during tests."""
    import logging
    from io import StringIO

    class LogCapture:
        def __init__(self):
            self.stream = StringIO()
            self.handler = logging.StreamHandler(self.stream)
            self.handler.setLevel(logging.DEBUG)
            self.logger = logging.getLogger()
            self.original_level = self.logger.level

        def start(self):
            self.logger.setLevel(logging.DEBUG)
            self.logger.addHandler(self.handler)

        def stop(self):
            self.logger.removeHandler(self.handler)
            self.logger.setLevel(self.original_level)

        def get_logs(self):
            return self.stream.getvalue()

        def clear(self):
            self.stream = StringIO()
            self.handler.stream = self.stream

        def contains(self, text: str):
            return text in self.get_logs()

        def count_level(self, level: str):
            logs = self.get_logs()
            return logs.count(f"[{level.upper()}]")

    capture = LogCapture()
    capture.start()
    yield capture
    capture.stop()


@pytest.fixture
def validation_helper():
    """Helper for validating test results."""

    class ValidationHelper:
        @staticmethod
        def validate_workflow_json(workflow: Dict[str, Any]) -> bool:
            """Validate workflow JSON structure."""
            required_fields = ["task_type", "agents", "config"]
            return all(field in workflow for field in required_fields)

        @staticmethod
        def validate_enhancement(enhancement: Dict[str, Any]) -> bool:
            """Validate enhancement structure."""
            required_fields = ["type", "suggestion", "priority"]
            return all(field in enhancement for field in required_fields)

        @staticmethod
        def validate_classification(classification: Dict[str, Any]) -> bool:
            """Validate request classification."""
            required_fields = ["type", "confidence"]
            return all(field in classification for field in required_fields)

        @staticmethod
        def validate_performance_metrics(metrics: Dict[str, Any]) -> bool:
            """Validate performance metrics."""
            return all(
                metric in metrics
                for metric in ["execution_time", "memory_usage", "success_rate"]
            )

    return ValidationHelper()


# Test environment setup
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "system: System tests")
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "critical: Critical functionality tests")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on location."""
    for item in items:
        # Add markers based on test file location
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "system" in str(item.fspath):
            item.add_marker(pytest.mark.system)
        elif "benchmarks" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
