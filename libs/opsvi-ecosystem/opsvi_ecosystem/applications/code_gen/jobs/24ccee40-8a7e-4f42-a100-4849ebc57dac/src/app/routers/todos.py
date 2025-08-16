"""
FastAPI router for todo CRUD endpoints.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.todo import TodoDAL
from app.db.session import get_session
from app.schemas.todo import TodoCreate, TodoResponse, TodoUpdate

logger = logging.getLogger(__name__)

router = APIRouter()


async def get_todo_dal(db_session: AsyncSession = Depends(get_session)) -> TodoDAL:
    return TodoDAL(db_session)


@router.post(
    "/",
    response_model=TodoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new todo item",
)
async def create_todo(todo_create: TodoCreate, dal: TodoDAL = Depends(get_todo_dal)):
    """Create a new todo item."""
    try:
        todo = await dal.create_todo(todo_create)
        return todo
    except Exception as exc:
        logger.error(f"Error creating todo: {exc}")
        raise HTTPException(status_code=500, detail="Failed to create todo item.")


@router.get(
    "/",
    response_model=list[TodoResponse],
    status_code=status.HTTP_200_OK,
    summary="List all todo items",
)
async def list_todos(dal: TodoDAL = Depends(get_todo_dal)):
    """Retrieve all todo items."""
    try:
        todos = await dal.get_all_todos()
        return todos
    except Exception as exc:
        logger.error(f"Error retrieving todos: {exc}")
        raise HTTPException(status_code=500, detail="Failed to retrieve todo items.")


@router.get(
    "/{todo_id}",
    response_model=TodoResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a todo item by ID",
)
async def get_todo(todo_id: int, dal: TodoDAL = Depends(get_todo_dal)):
    """Get details for a specific todo item by its ID."""
    todo = await dal.get_todo(todo_id)
    if not todo:
        logger.info(f"Todo not found (id={todo_id})")
        raise HTTPException(status_code=404, detail="Todo item not found.")
    return todo


@router.put(
    "/{todo_id}",
    response_model=TodoResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a todo item",
)
async def update_todo(
    todo_id: int, todo_update: TodoUpdate, dal: TodoDAL = Depends(get_todo_dal)
):
    """
    Update fields of a todo item by ID.
    """
    todo = await dal.update_todo(todo_id, todo_update)
    if not todo:
        logger.info(f"Todo not found for update (id={todo_id})")
        raise HTTPException(status_code=404, detail="Todo item not found.")
    return todo


@router.delete(
    "/{todo_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a todo item"
)
async def delete_todo(todo_id: int, dal: TodoDAL = Depends(get_todo_dal)):
    """
    Delete a todo item by ID.
    """
    success = await dal.delete_todo(todo_id)
    if not success:
        logger.info(f"Todo not found for deletion (id={todo_id})")
        raise HTTPException(status_code=404, detail="Todo item not found.")
    return
