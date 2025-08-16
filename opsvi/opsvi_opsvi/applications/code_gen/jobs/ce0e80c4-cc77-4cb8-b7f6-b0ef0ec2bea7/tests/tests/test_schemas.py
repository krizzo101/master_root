import pytest
from pydantic import ValidationError
from app.schemas import TodoBase, TodoCreate, TodoUpdate, TodoRead, Config


def test_todobase_validation_and_fields():
    valid_data = {"title": "Sample", "description": "Desc", "completed": True}
    todo = TodoBase(**valid_data)
    assert todo.title == "Sample"
    assert todo.description == "Desc"
    assert todo.completed is True

    # Title required
    with pytest.raises(ValidationError):
        TodoBase(description="Desc")

    # completed defaults to False if omitted
    data = {"title": "Sample2", "description": "Desc2"}
    todo2 = TodoBase(**data)
    assert todo2.completed is False


def test_todocreate_accepts_required_fields():
    data = {"title": "Create Task", "description": "Create Desc"}
    todo_create = TodoCreate(**data)
    assert todo_create.title == "Create Task"
    assert todo_create.description == "Create Desc"

    # Title is required
    with pytest.raises(ValidationError):
        TodoCreate(description="No Title")


def test_todoupdate_all_fields_optional():
    # Empty update
    todo_update = TodoUpdate()
    assert todo_update.title is None
    assert todo_update.description is None
    assert todo_update.completed is None

    # Partial update
    data = {"title": "Updated Title"}
    todo_update2 = TodoUpdate(**data)
    assert todo_update2.title == "Updated Title"


def test_todoread_includes_id_and_fields():
    data = {"id": 1, "title": "Read Task", "description": "Desc", "completed": True}
    todo_read = TodoRead(**data)
    assert todo_read.id == 1
    assert todo_read.title == "Read Task"
    assert todo_read.completed is True


def test_config_schema_basic_validation():
    config = Config()
    # Assume Config has some default fields
    assert config is not None
    # If Config has required fields, test them here
