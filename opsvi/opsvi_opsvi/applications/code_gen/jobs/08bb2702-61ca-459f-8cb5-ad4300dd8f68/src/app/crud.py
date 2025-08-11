"""
CRUD operations for Task Management API.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import update, delete
from fastapi import HTTPException, status
from app.models import Task
from app.schemas import TaskCreate, TaskUpdate
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


async def get_tasks(session: AsyncSession) -> List[Task]:
    """
    Retrieve all tasks.
    """
    try:
        result = await session.execute(select(Task))
        tasks = result.scalars().all()
        return tasks
    except SQLAlchemyError as exc:
        logger.error(f"Error retrieving tasks: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving tasks.",
        )


async def get_task_by_id(session: AsyncSession, task_id: int) -> Optional[Task]:
    """
    Retrieve a task by ID.
    """
    try:
        result = await session.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()
        return task
    except SQLAlchemyError as exc:
        logger.error(f"Error retrieving task {task_id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving task.",
        )


async def create_task(session: AsyncSession, task_create: TaskCreate) -> Task:
    """
    Create a new task.
    """
    task = Task(
        title=task_create.title,
        description=task_create.description,
        is_completed=task_create.is_completed
        if task_create.is_completed is not None
        else False,
    )
    try:
        session.add(task)
        await session.commit()
        await session.refresh(task)
        logger.info(f"Created task with id {task.id}")
        return task
    except SQLAlchemyError as exc:
        await session.rollback()
        logger.error(f"Error creating task: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating task.",
        )


async def update_task(
    session: AsyncSession, task_id: int, task_update: TaskUpdate
) -> Optional[Task]:
    """
    Update an existing task by ID.
    """
    task = await get_task_by_id(session, task_id)
    if not task:
        logger.warning(f"Attempting to update non-existent task id {task_id}")
        return None
    for var, value in vars(task_update).items():
        if value is not None:
            setattr(task, var, value)
    try:
        await session.commit()
        await session.refresh(task)
        logger.info(f"Updated task {task_id}")
        return task
    except SQLAlchemyError as exc:
        await session.rollback()
        logger.error(f"Error updating task {task_id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating task.",
        )


async def delete_task(session: AsyncSession, task_id: int) -> bool:
    """
    Delete a task by ID.
    """
    task = await get_task_by_id(session, task_id)
    if not task:
        logger.warning(f"Attempting to delete non-existent task id {task_id}")
        return False
    try:
        await session.delete(task)
        await session.commit()
        logger.info(f"Deleted task {task_id}")
        return True
    except SQLAlchemyError as exc:
        await session.rollback()
        logger.error(f"Error deleting task {task_id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting task.",
        )
