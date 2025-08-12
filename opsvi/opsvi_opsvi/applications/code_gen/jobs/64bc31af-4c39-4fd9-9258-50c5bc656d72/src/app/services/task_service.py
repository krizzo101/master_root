import logging

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.models import Task
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate

logger = logging.getLogger("uvicorn.error")


class TaskService:
    """Service layer for task business logic."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_task(self, task_create: TaskCreate) -> TaskResponse:
        """Create a new task."""
        new_task = Task(title=task_create.title, description=task_create.description)
        try:
            self.session.add(new_task)
            await self.session.commit()
            await self.session.refresh(new_task)
            logger.info(f"Created task: {new_task.id}")
            return TaskResponse.from_orm(new_task)
        except SQLAlchemyError as exc:
            await self.session.rollback()
            logger.error(f"Error creating task: {exc}")
            raise

    async def list_tasks(self) -> list[TaskResponse]:
        """Return a list of all tasks."""
        stmt = select(Task)
        tasks = (await self.session.execute(stmt)).scalars().all()
        logger.info(f"Listed {len(tasks)} tasks")
        return [TaskResponse.from_orm(task) for task in tasks]

    async def get_task(self, task_id: int) -> TaskResponse | None:
        """Get a task by its ID."""
        task = await self.session.get(Task, task_id)
        if not task:
            logger.info(f"Task {task_id} not found")
            return None
        return TaskResponse.from_orm(task)

    async def update_task(
        self, task_id: int, task_update: TaskUpdate
    ) -> TaskResponse | None:
        """Update an existing task by ID."""
        task = await self.session.get(Task, task_id)
        if not task:
            logger.info(f"Task {task_id} not found for update")
            return None
        if task_update.title is not None:
            task.title = task_update.title
        if task_update.description is not None:
            task.description = task_update.description
        try:
            await self.session.commit()
            await self.session.refresh(task)
            logger.info(f"Updated task: {task.id}")
            return TaskResponse.from_orm(task)
        except SQLAlchemyError as exc:
            await self.session.rollback()
            logger.error(f"Error updating task {task_id}: {exc}")
            raise

    async def delete_task(self, task_id: int) -> bool:
        """Delete a task by ID."""
        task = await self.session.get(Task, task_id)
        if not task:
            logger.info(f"Task {task_id} not found for deletion")
            return False
        try:
            await self.session.delete(task)
            await self.session.commit()
            logger.info(f"Deleted task: {task_id}")
            return True
        except SQLAlchemyError as exc:
            await self.session.rollback()
            logger.error(f"Error deleting task {task_id}: {exc}")
            raise
