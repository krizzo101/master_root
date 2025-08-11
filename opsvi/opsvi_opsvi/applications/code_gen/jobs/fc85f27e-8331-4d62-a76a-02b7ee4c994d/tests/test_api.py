import os
import sys

# Add src directory to path
CURRENT_DIR = os.path.dirname(__file__)
SRC_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "src"))
sys.path.insert(0, SRC_DIR)

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_root():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Web API is running"}


def test_create_and_get_item():
    """Test creating and retrieving an item."""
    # Create item
    item_data = {"name": "Test Item", "description": "A test item"}
    response = client.post("/items", json=item_data)
    assert response.status_code == 200
    created_item = response.json()
    assert created_item["name"] == "Test Item"
    assert created_item["id"] == 1

    # Get item
    response = client.get(f"/items/{created_item['id']}")
    assert response.status_code == 200
    assert response.json() == created_item


def test_get_nonexistent_item():
    """Test getting non-existent item."""
    response = client.get("/items/999")
    assert response.status_code == 404
