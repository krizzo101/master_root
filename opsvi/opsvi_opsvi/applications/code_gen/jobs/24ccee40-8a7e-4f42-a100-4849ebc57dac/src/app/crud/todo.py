"""
CRUD operations for Todo items (DAL/repository layer)
"""
from typing import List, Optional
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.todo import Todo
from app.schemas.todo import TodoCreate, TodoUpdate
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class TodoDAL:
    """
    Data Access Layer for Todo CRUD operations.
    """

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_todo(self, todo_create: TodoCreate) -> Todo:
        new_todo = Todo(
            description=todo_create.description,
            is_completed=todo_create.is_completed,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        try:
            self.db_session.add(new_todo)
            await self.db_session.commit()
            await self.db_session.refresh(new_todo)
            logger.info("Todo created with id %s", new_todo.id)
            return new_todo
        except SQLAlchemyError as e:
            await self.db_session.rollback()
            logger.error("Failed to create todo: %s", e)
            raise

    async def get_todo(self, todo_id: int) -> Optional[Todo]:
        result = await self.db_session.execute(select(Todo).where(Todo.id == todo_id))
        todo = result.scalar_one_or_none()
        return todo

    async def get_all_todos(self) -> List[Todo]:
        result = await self.db_session.execute(select(Todo).order_by(Todo.id.asc()))
        return result.scalars().all()

    async def update_todo(
        self, todo_id: int, todo_update: TodoUpdate
    ) -> Optional[Todo]:
        todo = await self.get_todo(todo_id)
        if not todo:
            return None
        updated = False
        if todo_update.description is not None:
            todo.description = todo_update.description
            updated = True
        if todo_update.is_completed is not None:
            todo.is_completed = todo_update.is_completed
            updated = True
        if updated:
            todo.updated_at = datetime.utcnow()
            try:
                self.db_session.add(todo)
                await self.db_session.commit()
                await self.db_session.refresh(todo)
                logger.info(f"Todo updated (id={todo_id})")
            except SQLAlchemyError as e:
                await self.db_session.rollback()
                logger.error("Failed to update todo: %s", e)
                raise
        return todo

    async def delete_todo(self, todo_id: int) -> bool:
        todo = await self.get_todo(todo_id)
        if not todo:
            return False
        try:
            await self.db_session.delete(todo)
            await self.db_session.commit()
            logger.info(f"Todo deleted (id={todo_id})")
            return True
        except SQLAlchemyError as e:
            await self.db_session.rollback()
            logger.error("Failed to delete todo: %s", e)
            raise
