"""
Todo API router for CRUD operations.
"""

from fastapi import APIRouter, Depends, Path, status

from app.models.todo import (
    MessageResponse,
    TodoItemCreate,
    TodoItemModel,
    TodoItemResponse,
    TodoItemUpdate,
)
from app.services.todo_service import TodoService, get_todo_service

router = APIRouter()


@router.post(
    "",
    response_model=TodoItemResponse,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": MessageResponse, "description": "Validation Error"}},
)
async def create_todo(
    item: TodoItemCreate, service: TodoService = Depends(get_todo_service)
) -> TodoItemResponse:
    """Create a new todo item."""
    todo = await service.create_item(item)
    return TodoItemResponse(data=todo)


@router.get("", response_model=list[TodoItemModel], status_code=status.HTTP_200_OK)
async def list_todos(
    service: TodoService = Depends(get_todo_service),
) -> list[TodoItemModel]:
    """Retrieve all todo items."""
    return await service.list_items()


@router.get(
    "/{item_id}",
    response_model=TodoItemModel,
    status_code=status.HTTP_200_OK,
    responses={404: {"model": MessageResponse, "description": "Item not found"}},
)
async def get_todo(
    item_id: int = Path(..., gt=0, description="The ID of the todo item for retrieval"),
    service: TodoService = Depends(get_todo_service),
) -> TodoItemModel:
    """Retrieve a todo item by its ID."""
    return await service.get_item(item_id)


@router.put(
    "/{item_id}",
    response_model=TodoItemModel,
    status_code=status.HTTP_200_OK,
    responses={404: {"model": MessageResponse, "description": "Item not found"}},
)
async def update_todo(
    item_id: int = Path(..., gt=0, description="The ID of the todo item for update"),
    item: TodoItemUpdate = ...,  # Validates input
    service: TodoService = Depends(get_todo_service),
) -> TodoItemModel:
    """Update an existing todo item."""
    return await service.update_item(item_id, item)


@router.patch(
    "/{item_id}",
    response_model=TodoItemModel,
    status_code=status.HTTP_200_OK,
    responses={404: {"model": MessageResponse, "description": "Item not found"}},
)
async def patch_todo(
    item_id: int = Path(..., gt=0),
    item: TodoItemUpdate = ...,  # Validates input, allows partial updates
    service: TodoService = Depends(get_todo_service),
) -> TodoItemModel:
    """Partially update a todo item."""
    return await service.patch_item(item_id, item)


@router.delete(
    "/{item_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    responses={404: {"model": MessageResponse, "description": "Item not found"}},
)
async def delete_todo(
    item_id: int = Path(..., gt=0, description="The ID of the todo item to delete"),
    service: TodoService = Depends(get_todo_service),
) -> MessageResponse:
    """Delete a todo item."""
    await service.delete_item(item_id)
    return MessageResponse(message=f"Item {item_id} deleted successfully.")
