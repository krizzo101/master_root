import pytest
from app.crud import (
    get_todos,
    get_todo as crud_get_todo,
    create_todo as crud_create_todo,
    update_todo as crud_update_todo,
    replace_todo as crud_replace_todo,
    delete_todo as crud_delete_todo,
)
from app.database import Base, engine, SessionLocal
from app.models import Todo
from sqlalchemy.orm import Session

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)


def create_test_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_crud_create_and_get_todo_success():
    db = next(create_test_db_session())

    todo_in = {"title": "Crud Test", "description": "CRUD operations test"}
    todo = crud_create_todo(db, todo_in)
    assert todo.id is not None
    assert todo.title == todo_in["title"]

    retrieved = crud_get_todo(db, todo.id)
    assert retrieved.id == todo.id
    assert retrieved.title == todo_in["title"]


def test_crud_get_todos_respects_skip_and_limit():
    db = next(create_test_db_session())
    # Clear existing
    db.query(Todo).delete()
    db.commit()

    # Create 10 todos
    for i in range(10):
        crud_create_todo(db, {"title": f"Task {i}", "description": "desc"})

    todos = get_todos(db, skip=0, limit=5)
    assert len(todos) == 5
    todos_skip_5 = get_todos(db, skip=5, limit=5)
    assert len(todos_skip_5) == 5


def test_crud_update_todo_partial_update():
    db = next(create_test_db_session())
    todo = crud_create_todo(
        db, {"title": "Original Title", "description": "Original Desc"}
    )

    update_data = {"description": "Updated Desc"}
    updated = crud_update_todo(db, todo.id, update_data)

    assert updated.description == "Updated Desc"
    assert updated.title == "Original Title"


def test_crud_replace_todo_fully_replaces_fields():
    db = next(create_test_db_session())
    todo = crud_create_todo(
        db, {"title": "Title Old", "description": "Desc Old", "completed": False}
    )

    new_data = {"title": "Title New", "description": "Desc New", "completed": True}
    replaced = crud_replace_todo(db, todo.id, new_data)

    assert replaced.title == new_data["title"]
    assert replaced.description == new_data["description"]
    assert replaced.completed == new_data["completed"]


def test_crud_delete_todo_successfully_removes():
    db = next(create_test_db_session())
    todo = crud_create_todo(db, {"title": "ToDelete", "description": "ToDelete Desc"})
    deleted = crud_delete_todo(db, todo.id)
    assert deleted.id == todo.id
    assert crud_get_todo(db, todo.id) is None


def test_crud_get_todo_with_nonexistent_id_returns_none():
    db = next(create_test_db_session())
    todo = crud_get_todo(db, 9999999)
    assert todo is None
