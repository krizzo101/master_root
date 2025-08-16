import pytest
from app.services.todo_service import InMemoryTodoStore, TodoService


@pytest.fixture
def todo_store():
    return InMemoryTodoStore()


@pytest.fixture
def todo_service(todo_store):
    return TodoService(store=todo_store)


@pytest.fixture
def sample_item():
    return {
        "title": "Sample Todo",
        "description": "Sample description",
        "completed": False,
    }


def test_in_memory_todo_store_initialization_is_empty(todo_store):
    items = todo_store.list()
    assert isinstance(items, list)
    assert len(items) == 0


def test_create_todo_item_adds_and_returns_item_with_id(todo_store, sample_item):
    result = todo_store.create(sample_item)
    assert isinstance(result, dict)
    assert "id" in result
    assert result["title"] == sample_item["title"]

    # Item list should contain the created item
    all_items = todo_store.list()
    assert any(item["id"] == result["id"] for item in all_items)


def test_get_existing_and_nonexisting_item(todo_store, sample_item):
    created = todo_store.create(sample_item)
    item_id = created["id"]
    fetched = todo_store.get(item_id)
    assert fetched["id"] == item_id
    assert fetched["title"] == sample_item["title"]

    # Test not found
    with pytest.raises(KeyError):
        todo_store.get(999999)


def test_update_existing_item_and_partial_update(todo_store, sample_item):
    created = todo_store.create(sample_item)
    item_id = created["id"]

    # Full update
    updates = {
        "title": "Updated Title",
        "description": "Updated description",
        "completed": True,
    }
    updated_item = todo_store.update(item_id, updates, partial=False)
    assert updated_item["title"] == "Updated Title"
    assert updated_item["completed"] is True

    # Partial update
    partial_updates = {"completed": False}
    updated_partial = todo_store.update(item_id, partial_updates, partial=True)
    assert updated_partial["completed"] is False

    # Updating non-existent item raises error
    with pytest.raises(KeyError):
        todo_store.update(999999, partial_updates, partial=True)


def test_delete_existing_and_nonexisting_item(todo_store, sample_item):
    created = todo_store.create(sample_item)
    item_id = created["id"]
    result = todo_store.delete(item_id)
    assert result == True

    # Ensure item no longer exists
    with pytest.raises(KeyError):
        todo_store.get(item_id)

    # Deleting non-existing item raises
    with pytest.raises(KeyError):
        todo_store.delete(999999)


def test_todo_service_methods_integration(todo_service, sample_item):
    # Create
    created = todo_service.create(sample_item)
    item_id = created["id"]
    assert created["title"] == sample_item["title"]

    # List
    items = todo_service.list()
    assert any(item["id"] == item_id for item in items)

    # Get
    fetched = todo_service.get(item_id)
    assert fetched["id"] == item_id

    # Update
    updates = {"completed": True}
    updated = todo_service.update(item_id, updates, partial=True)
    assert updated["completed"] is True

    # Delete
    delete_result = todo_service.delete(item_id)
    assert delete_result is True

    # Confirm deletion
    with pytest.raises(KeyError):
        todo_service.get(item_id)
