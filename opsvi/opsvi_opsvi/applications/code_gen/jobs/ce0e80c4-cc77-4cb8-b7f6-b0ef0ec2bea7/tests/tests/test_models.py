import pytest
from app.models import Todo


def test_todo_model_attributes_and_str():
    todo = Todo(
        id=1, title="Test Task", description="Test Description", completed=False
    )
    assert todo.id == 1
    assert todo.title == "Test Task"
    assert todo.description == "Test Description"
    assert todo.completed is False
    # Test __repr__ or __str__ if defined
    representation = str(todo)
    assert isinstance(representation, str)
    assert "Test Task" in representation
    assert "completed" in representation or "Test Task" in representation
