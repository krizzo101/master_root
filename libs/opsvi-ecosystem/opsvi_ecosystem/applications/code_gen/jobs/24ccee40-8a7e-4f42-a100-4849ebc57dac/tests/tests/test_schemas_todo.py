import pytest
from pydantic import ValidationError
from app.schemas.todo import TodoBase, TodoCreate, TodoUpdate, TodoInDB, TodoResponse


def test_todobase_and_todocreate_schema_validation():
    # Valid TodoBase
    todo_base = TodoBase(description="Task", completed=True)
    assert todo_base.description == "Task"
    assert todo_base.completed is True

    # Valid TodoCreate requires description
    todo_create = TodoCreate(description="New task")
    assert todo_create.description == "New task"

    # Missing description triggers validation error
    with pytest.raises(ValidationError):
        TodoCreate(completed=False)  # missing required


def test_todoupdate_description_validation():
    # Valid description
    update = TodoUpdate(description="Valid desc")
    assert update.description == "Valid desc"

    # None description is acceptable
    update_none = TodoUpdate(description=None)
    assert update_none.description is None

    # Empty string is invalid
    with pytest.raises(ValidationError):
        TodoUpdate(description="")


def test_todoin_db_and_response_models():
    todo_data = {"id": 123, "description": "desc", "completed": False}
    todo_in_db = TodoInDB(**todo_data)
    assert todo_in_db.id == 123
    assert todo_in_db.description == "desc"
    assert todo_in_db.completed is False

    todo_resp = TodoResponse(**todo_data)
    assert todo_resp.id == 123
    assert todo_resp.description == "desc"
    assert todo_resp.completed is False
