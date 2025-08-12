import logging
from datetime import datetime

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models import Todo
from app.schemas import TodoCreate, TodoRead, TodoUpdate

logger = logging.getLogger(__name__)


class TodoService:
    """
    Service layer for managing todo items: CRUD operations, validation, business logic.
    """

    def __init__(self, db: Session):
        self.db = db

    def create_todo(self, todo_in: TodoCreate) -> TodoRead:
        try:
            todo = Todo(
                title=todo_in.title,
                description=todo_in.description,
                completed=todo_in.completed,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            self.db.add(todo)
            self.db.commit()
            self.db.refresh(todo)
            return TodoRead.from_orm(todo)
        except SQLAlchemyError as ex:
            self.db.rollback()
            logger.error(f"Error creating todo: {ex}")
            raise

    def get_all_todos(self) -> list[TodoRead]:
        todos = self.db.query(Todo).all()
        return [TodoRead.from_orm(todo) for todo in todos]

    def get_todo_by_id(self, todo_id: int) -> TodoRead | None:
        todo = self.db.query(Todo).filter(Todo.id == todo_id).first()
        if todo:
            return TodoRead.from_orm(todo)
        return None

    def update_todo(self, todo_id: int, todo_in: TodoUpdate) -> TodoRead | None:
        todo = self.db.query(Todo).filter(Todo.id == todo_id).first()
        if not todo:
            return None
        try:
            updated = False
            if todo_in.title is not None:
                todo.title = todo_in.title
                updated = True
            if todo_in.description is not None:
                todo.description = todo_in.description
                updated = True
            if todo_in.completed is not None:
                todo.completed = todo_in.completed
                updated = True
            if updated:
                todo.updated_at = datetime.utcnow()
                self.db.add(todo)
                self.db.commit()
                self.db.refresh(todo)
            return TodoRead.from_orm(todo)
        except SQLAlchemyError as ex:
            self.db.rollback()
            logger.error(f"Error updating todo {todo_id}: {ex}")
            raise

    def delete_todo(self, todo_id: int) -> bool:
        todo = self.db.query(Todo).filter(Todo.id == todo_id).first()
        if not todo:
            return False
        try:
            self.db.delete(todo)
            self.db.commit()
            return True
        except SQLAlchemyError as ex:
            self.db.rollback()
            logger.error(f"Error deleting todo {todo_id}: {ex}")
            raise
