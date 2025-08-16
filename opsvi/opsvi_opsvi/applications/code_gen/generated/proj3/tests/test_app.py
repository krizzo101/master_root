import os
import sys

# Add src directory to path
CURRENT_DIR = os.path.dirname(__file__)
SRC_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "src"))
sys.path.insert(0, SRC_DIR)

import pytest
from app import app
import json


@pytest.fixture
def client():
    """Create test client."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_home_page(client):
    """Test home page loads."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"Items List" in response.data


def test_add_item_page(client):
    """Test add item page loads."""
    response = client.get("/add")
    assert response.status_code == 200
    assert b"Add New Item" in response.data


def test_api_items(client):
    """Test API items endpoint."""
    response = client.get("/api/items")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)
    assert len(data) >= 2  # Sample items


def test_api_add_item(client):
    """Test API add item."""
    item_data = {"name": "Test Item", "description": "Test Description"}
    response = client.post(
        "/api/items", data=json.dumps(item_data), content_type="application/json"
    )
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data["name"] == "Test Item"
    assert "id" in data


def test_health_endpoint(client):
    """Test health check."""
    response = client.get("/health")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["status"] == "healthy"
    assert "items_count" in data


def test_add_item_form(client):
    """Test adding item via form."""
    response = client.post(
        "/add",
        data={"name": "Form Test Item", "description": "Added via form"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Form Test Item" in response.data
