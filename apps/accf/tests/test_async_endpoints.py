"""
Async Testing Setup for ACCF Research Agent API.

This module provides comprehensive async testing for the FastAPI endpoints
as specified in the technical workstream.
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from accf_agents.api.app import app
from accf_agents.agents.base import Task
from accf_agents import Settings


def test_health_endpoint():
    """Test the basic health check endpoint."""
    with TestClient(app) as client:
        response = client.get("/health/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "service" in data


def test_detailed_health_endpoint():
    """Test the detailed health check endpoint."""
    with TestClient(app) as client:
        response = client.get("/health/detailed")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "metrics" in data
        assert "agents" in data


def test_readiness_endpoint():
    """Test the readiness check endpoint."""
    with TestClient(app) as client:
        response = client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert "agents_available" in data


def test_knowledge_search_endpoint():
    """Test the knowledge search endpoint."""
    with TestClient(app) as client:
        response = client.post(
            "/tasks/execute",
            json={
                "task_id": "test-search-1",
                "type": "knowledge_search",
                "parameters": {"query": "test query", "top_k": 5},
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
        assert "status" in data


def test_consult_endpoint():
    """Test the consult endpoint."""
    with TestClient(app) as client:
        response = client.post(
            "/tasks/execute",
            json={
                "task_id": "test-consult-1",
                "type": "consult",
                "parameters": {
                    "prompt": "What is the capital of France?",
                    "session_id": "test-session",
                },
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
        assert "status" in data


def test_batch_execution_endpoint():
    """Test the batch execution endpoint."""
    with TestClient(app) as client:
        response = client.post(
            "/tasks/execute-batch",
            json=[
                {
                    "task_id": "batch-1",
                    "type": "knowledge_search",
                    "parameters": {"query": "test query 1"},
                },
                {
                    "task_id": "batch-2",
                    "type": "consult",
                    "parameters": {"prompt": "test prompt", "session_id": "test"},
                },
            ],
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) == 2


def test_agent_status_endpoint():
    """Test the agent status endpoint."""
    with TestClient(app) as client:
        response = client.get("/agents/status/overview")
        assert response.status_code == 200
        data = response.json()
        assert "total_agents" in data
        assert "agents" in data


def test_agent_capabilities_endpoint():
    """Test the agent capabilities endpoint."""
    with TestClient(app) as client:
        response = client.get("/agents/consult/capabilities")
        assert response.status_code == 200
        data = response.json()
        assert "agent_name" in data
        assert "capabilities" in data


def test_agent_test_endpoint():
    """Test the agent test endpoint."""
    with TestClient(app) as client:
        response = client.post(
            "/agents/consult/test",
            json={
                "test_parameters": {
                    "prompt": "test prompt",
                    "session_id": "test-session",
                }
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "test_result" in data


def test_task_status_endpoint():
    """Test the task status endpoint."""
    with TestClient(app) as client:
        # First create a task
        create_response = client.post(
            "/tasks/execute",
            json={
                "task_id": "status-test-1",
                "type": "consult",
                "parameters": {"prompt": "test", "session_id": "test"},
            },
        )
        assert create_response.status_code == 200

        # Then check its status
        task_id = create_response.json()["task_id"]
        status_response = client.get(f"/tasks/status/{task_id}")
        assert status_response.status_code == 200
        data = status_response.json()
        assert "task_id" in data
        assert "status" in data


def test_invalid_task_type():
    """Test handling of invalid task type."""
    with TestClient(app) as client:
        response = client.post(
            "/tasks/execute",
            json={
                "task_id": "invalid-test",
                "type": "invalid_agent_type",
                "parameters": {},
            },
        )
        assert response.status_code == 400
        data = response.json()
        assert "error" in data


def test_missing_parameters():
    """Test handling of missing required parameters."""
    with TestClient(app) as client:
        response = client.post(
            "/tasks/execute",
            json={
                "task_id": "missing-params-test",
                "type": "consult",
                "parameters": {},  # Missing required parameters
            },
        )
        assert response.status_code == 400
        data = response.json()
        assert "error" in data


def test_large_batch_execution():
    """Test handling of large batch execution."""
    with TestClient(app) as client:
        # Create a large batch of tasks
        batch_tasks = []
        for i in range(10):
            batch_tasks.append(
                {
                    "task_id": f"batch-large-{i}",
                    "type": "knowledge_search",
                    "parameters": {"query": f"test query {i}"},
                }
            )

        response = client.post("/tasks/execute-batch", json=batch_tasks)
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
