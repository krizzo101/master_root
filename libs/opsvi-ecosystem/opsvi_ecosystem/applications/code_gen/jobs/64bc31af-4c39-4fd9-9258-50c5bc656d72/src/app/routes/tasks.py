from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas import task as task_schema
from app.services.task_service import TaskService

router = APIRouter()


@router.post(
    "/", response_model=task_schema.TaskResponse, status_code=status.HTTP_201_CREATED
)
async def create_task(
    task_create: task_schema.TaskCreate, session: AsyncSession = Depends(get_session)
):
    """Create a new task."""
    service = TaskService(session)
    return await service.create_task(task_create)


@router.get("/", response_model=list[task_schema.TaskResponse])
async def list_tasks(session: AsyncSession = Depends(get_session)):
    """Get a list of all tasks."""
    service = TaskService(session)
    return await service.list_tasks()


@router.get("/{task_id}", response_model=task_schema.TaskResponse)
async def get_task(task_id: int, session: AsyncSession = Depends(get_session)):
    """Get details of a task by its ID."""
    service = TaskService(session)
    task = await service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.put("/{task_id}", response_model=task_schema.TaskResponse)
async def update_task(
    task_id: int,
    task_update: task_schema.TaskUpdate,
    session: AsyncSession = Depends(get_session),
):
    """Update an existing task by its ID."""
    service = TaskService(session)
    updated_task = await service.update_task(task_id, task_update)
    if not updated_task:
        raise HTTPException(status_code=404, detail="Task not found")
    return updated_task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int, session: AsyncSession = Depends(get_session)):
    """Delete a task by its ID."""
    service = TaskService(session)
    deleted = await service.delete_task(task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Task not found")
    return None
