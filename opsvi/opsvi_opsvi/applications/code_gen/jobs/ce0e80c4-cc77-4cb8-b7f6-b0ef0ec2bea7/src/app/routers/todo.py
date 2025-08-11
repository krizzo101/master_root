import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas import TodoCreate, TodoRead, TodoUpdate
from app.services.todo_service import TodoService
from app.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=TodoRead, status_code=status.HTTP_201_CREATED)
def create_todo(todo_in: TodoCreate, db: Session = Depends(get_db)) -> TodoRead:
    """Create a new todo item."""
    try:
        todo_service = TodoService(db)
        new_todo = todo_service.create_todo(todo_in)
        return new_todo
    except Exception as ex:
        logger.error(f"Error creating todo: {ex}")
        raise HTTPException(status_code=500, detail="Failed to create todo item.")


@router.get("/", response_model=List[TodoRead])
def get_all_todos(db: Session = Depends(get_db)) -> List[TodoRead]:
    """Retrieve all todo items."""
    try:
        todo_service = TodoService(db)
        return todo_service.get_all_todos()
    except Exception as ex:
        logger.error(f"Error retrieving todos: {ex}")
        raise HTTPException(status_code=500, detail="Failed to retrieve todo items.")


@router.get("/{todo_id}", response_model=TodoRead)
def get_todo_by_id(todo_id: int, db: Session = Depends(get_db)) -> TodoRead:
    """Retrieve a todo item by ID."""
    todo_service = TodoService(db)
    todo = todo_service.get_todo_by_id(todo_id)
    if not todo:
        logger.info(f"Todo item not found: {todo_id}")
        raise HTTPException(status_code=404, detail="Todo item not found.")
    return todo


@router.put("/{todo_id}", response_model=TodoRead)
def update_todo(
    todo_id: int, todo_in: TodoUpdate, db: Session = Depends(get_db)
) -> TodoRead:
    """Update an existing todo item by ID."""
    todo_service = TodoService(db)
    todo = todo_service.update_todo(todo_id, todo_in)
    if not todo:
        logger.info(f"Todo item to update not found: {todo_id}")
        raise HTTPException(status_code=404, detail="Todo item not found.")
    return todo


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(todo_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a todo item by ID."""
    todo_service = TodoService(db)
    success = todo_service.delete_todo(todo_id)
    if not success:
        logger.info(f"Todo item to delete not found: {todo_id}")
        raise HTTPException(status_code=404, detail="Todo item not found.")
