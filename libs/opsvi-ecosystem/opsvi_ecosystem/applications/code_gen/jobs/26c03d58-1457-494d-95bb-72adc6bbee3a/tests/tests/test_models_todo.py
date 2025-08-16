import pytest
from app.models import todo
from pydantic import ValidationError


@pytest.fixture
def valid_todo_data():
    return {
        "title": "Test Todo",
        "description": "A simple test todo item",
        "completed": False,
    }


def test_title_must_not_be_blank_valid():
    valid_title = "Valid Title"
    # title_must_not_be_blank is a validator, called with cls and value
    # Should return the same value if valid
    result = todo.TodoItemBase.title_must_not_be_blank(todo.TodoItemBase, valid_title)
    assert result == valid_title


import pytest


def test_title_must_not_be_blank_blank_string():
    blank_titles = ["", "   ", "\t\n"]
    for blank_title in blank_titles:
        with pytest.raises(ValueError) as exc_info:
            todo.TodoItemBase.title_must_not_be_blank(todo.TodoItemBase, blank_title)
        assert "title must not be blank" in str(exc_info.value)


import pytest


def test_todoitemcreate_rejects_blank_title():
    with pytest.raises(ValidationError) as exc_info:
        todo.TodoItemCreate(title="  ", description="desc")
    errors = exc_info.value.errors()
    assert any(
        e["loc"] == ("title",) and e["msg"].startswith("title must not be blank")
        for e in errors
    )


import pytest


def test_todoitemupdate_allows_partial_and_validates_title():
    # Valid update with title
    update = todo.TodoItemUpdate(title="New Title")
    assert update.title == "New Title"

    # Valid update without title
    update = todo.TodoItemUpdate(description="desc")
    assert update.description == "desc"

    # Invalid blank title should raise ValidationError
    with pytest.raises(ValidationError) as exc_info:
        todo.TodoItemUpdate(title="   ")
    errors = exc_info.value.errors()
    assert any(
        e["loc"] == ("title",) and e["msg"].startswith("title must not be blank")
        for e in errors
    )


def test_todoitemmodel_and_response_models(valid_todo_data):
    # Create TodoItemModel with id
    todo_item = todo.TodoItemModel(id=1, **valid_todo_data)
    assert todo_item.id == 1
    assert todo_item.title == valid_todo_data["title"]
    assert todo_item.description == valid_todo_data["description"]
    assert todo_item.completed == valid_todo_data["completed"]

    # Create TodoItemResponse with same data
    response = todo.TodoItemResponse(id=1, **valid_todo_data)
    assert response.id == 1


def test_messageresponse_model():
    msg = todo.MessageResponse(message="Success")
    assert msg.message == "Success"


def test_config_class_settings():
    # Assuming Config has standard pydantic config attributes
    config = todo.Config
    # Check if allow_population_by_field_name attribute exists
    assert hasattr(config, "allow_population_by_field_name")
