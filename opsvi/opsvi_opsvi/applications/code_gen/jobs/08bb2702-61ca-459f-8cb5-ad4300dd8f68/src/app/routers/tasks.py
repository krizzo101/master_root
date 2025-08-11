"""
Task management API routes.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import logging

from app.schemas import (
    TaskCreate,
    TaskResponse,
    TaskUpdate,
    TaskListResponse,
    MessageResponse,
)
from app.database import get_session
from app import crud

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task_endpoint(
    task: TaskCreate, session: AsyncSession = Depends(get_session)
):
    """
    Create a new task.
    """
    new_task = await crud.create_task(session, task)
    return new_task


@router.get("/", response_model=TaskListResponse)
async def list_tasks_endpoint(session: AsyncSession = Depends(get_session)):
    """
    Retrieve all tasks.
    """
    tasks = await crud.get_tasks(session)
    return {"tasks": tasks}


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task_endpoint(task_id: int, session: AsyncSession = Depends(get_session)):
    """
    Retrieve a task by ID.
    """
    task = await crud.get_task_by_id(session, task_id)
    if not task:
        logger.info(f"Task not found: {task_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found."
        )
    return task


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task_endpoint(
    task_id: int, task_update: TaskUpdate, session: AsyncSession = Depends(get_session)
):
    """
    Replace a task by ID with the provided fields.
    """
    task = await crud.update_task(session, task_id, task_update)
    if not task:
        logger.info(f"Attempt to update non-existent task: {task_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found."
        )
    return task


@router.patch("/{task_id}", response_model=TaskResponse)
async def patch_task_endpoint(
    task_id: int, task_update: TaskUpdate, session: AsyncSession = Depends(get_session)
):
    """
    Partially update a task by ID.
    """
    # Same logic as PUT since partial updates are accepted
    task = await crud.update_task(session, task_id, task_update)
    if not task:
        logger.info(f"Attempt to update non-existent task: {task_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found."
        )
    return task


@router.delete(
    "/{task_id}", response_model=MessageResponse, status_code=status.HTTP_200_OK
)
async def delete_task_endpoint(
    task_id: int, session: AsyncSession = Depends(get_session)
):
    """
    Delete a task by ID.
    """
    deleted = await crud.delete_task(session, task_id)
    if not deleted:
        logger.info(f"Attempt to delete non-existent task: {task_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found."
        )
    return MessageResponse(message="Task deleted successfully.")
