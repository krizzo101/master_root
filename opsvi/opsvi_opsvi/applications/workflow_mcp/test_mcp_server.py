from fastapi.testclient import TestClient
import pytest

from src.applications.workflow_mcp.mcp_server import app

client = TestClient(app)


@pytest.fixture(scope="module")
def workflow_data():
    return {
        "name": "Test Workflow",
        "type": "test",
        "spec": {"steps": ["a", "b"]},
    }


@pytest.fixture(scope="module")
def run_input():
    return {"input": {"param": "value"}}


workflow_id = None
run_id = None


def test_create_workflow(workflow_data):
    response = client.post("/workflows", json=workflow_data)
    assert response.status_code == 200
    data = response.json()
    global workflow_id
    workflow_id = data["_key"]
    assert data["name"] == workflow_data["name"]


def test_get_workflow():
    global workflow_id
    response = client.get(f"/workflows/{workflow_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["_key"] == workflow_id


def test_list_workflows():
    response = client.get("/workflows")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_update_workflow():
    global workflow_id
    response = client.put(f"/workflows/{workflow_id}", json={"name": "Updated Name"})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"


def test_run_workflow(run_input):
    global workflow_id, run_id
    response = client.post(f"/workflows/{workflow_id}/run", json=run_input)
    assert response.status_code == 200
    data = response.json()
    run_id = data["_key"]
    assert data["workflow_id"] == workflow_id


def test_list_runs():
    response = client.get("/runs")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_run():
    global run_id
    response = client.get(f"/runs/{run_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["_key"] == run_id


def test_update_run():
    global run_id
    response = client.put(f"/runs/{run_id}", json={"status": "complete"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "complete"


def test_delete_run():
    global run_id
    response = client.delete(f"/runs/{run_id}")
    assert response.status_code == 200
    assert response.json()["deleted"] == run_id


def test_delete_workflow():
    global workflow_id
    response = client.delete(f"/workflows/{workflow_id}")
    assert response.status_code == 200
    assert response.json()["deleted"] == workflow_id
