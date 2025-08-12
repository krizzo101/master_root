from sqlalchemy.orm import Session

from app import models, schemas
from app.exceptions import ValidationException


def get_todos(db: Session, skip: int = 0, limit: int = 100) -> list[models.Todo]:
    """Retrieve a list of todos."""
    return db.query(models.Todo).offset(skip).limit(limit).all()


def get_todo(db: Session, todo_id: int) -> models.Todo | None:
    """Retrieve a todo by ID."""
    return db.query(models.Todo).filter(models.Todo.id == todo_id).first()


def create_todo(db: Session, todo_in: schemas.TodoCreate) -> models.Todo:
    """Create a new todo."""
    if not todo_in.title.strip() or not todo_in.description.strip():
        raise ValidationException("Title and description are required.")
    new_todo = models.Todo(
        title=todo_in.title.strip(), description=todo_in.description.strip()
    )
    db.add(new_todo)
    db.commit()
    db.refresh(new_todo)
    return new_todo


def update_todo(
    db: Session, todo_id: int, todo_in: schemas.TodoUpdate
) -> models.Todo | None:
    """Update fields on a todo by ID."""
    todo = get_todo(db, todo_id)
    if not todo:
        return None
    if todo_in.title is not None:
        if not todo_in.title.strip():
            raise ValidationException("Title cannot be empty.")
        todo.title = todo_in.title.strip()
    if todo_in.description is not None:
        if not todo_in.description.strip():
            raise ValidationException("Description cannot be empty.")
        todo.description = todo_in.description.strip()
    db.commit()
    db.refresh(todo)
    return todo


def replace_todo(
    db: Session, todo_id: int, todo_in: schemas.TodoCreate
) -> models.Todo | None:
    """Replace a todo with new title and description."""
    todo = get_todo(db, todo_id)
    if not todo:
        return None
    if not todo_in.title.strip() or not todo_in.description.strip():
        raise ValidationException("Title and description are required.")
    todo.title = todo_in.title.strip()
    todo.description = todo_in.description.strip()
    db.commit()
    db.refresh(todo)
    return todo


def delete_todo(db: Session, todo_id: int) -> bool:
    """Delete a todo by ID. Returns True if deleted."""
    todo = get_todo(db, todo_id)
    if not todo:
        return False
    db.delete(todo)
    db.commit()
    return True
