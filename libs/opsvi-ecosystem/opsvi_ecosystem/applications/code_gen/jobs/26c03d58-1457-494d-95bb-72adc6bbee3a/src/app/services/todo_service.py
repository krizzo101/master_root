"""
Business logic and in-memory data operations for todo items.
Thread-safe for concurrency.
"""
import logging
from datetime import datetime
from threading import Lock

from fastapi import HTTPException, status

from app.models.todo import TodoItemCreate, TodoItemModel, TodoItemUpdate


class InMemoryTodoStore:
    """
    Thread-safe in-memory store for todo items.
    """

    def __init__(self):
        self._store: dict[int, TodoItemModel] = {}
        self._id_counter: int = 1
        self._lock: Lock = Lock()

    def create(self, item: TodoItemCreate) -> TodoItemModel:
        with self._lock:
            now = datetime.utcnow()
            item_obj = TodoItemModel(
                id=self._id_counter,
                title=item.title,
                description=item.description,
                completed=item.completed,
                created_at=now,
                updated_at=now,
            )
            self._store[self._id_counter] = item_obj
            logging.info(f"Created new todo item: {item_obj}")
            self._id_counter += 1
            return item_obj

    def list(self) -> list[TodoItemModel]:
        with self._lock:
            # Return sorted by creation time, recently added last
            return sorted(self._store.values(), key=lambda x: x.created_at)

    def get(self, item_id: int) -> TodoItemModel | None:
        with self._lock:
            return self._store.get(item_id)

    def update(
        self, item_id: int, update: TodoItemUpdate, partial: bool = False
    ) -> TodoItemModel:
        with self._lock:
            current = self._store.get(item_id)
            if current is None:
                raise KeyError(f"Todo item with id {item_id} not found.")
            data = current.dict()
            updated = False
            for field in ["title", "description", "completed"]:
                val = getattr(update, field)
                if val is not None or (not partial and val is not None):
                    data[field] = val if val is not None else data[field]
                    updated = True if val is not None else updated
            if updated:
                now = datetime.utcnow()
                data["updated_at"] = now
            updated_obj = TodoItemModel(**data)
            self._store[item_id] = updated_obj
            logging.info(f"Updated todo item {item_id}: {updated_obj}")
            return updated_obj

    def delete(self, item_id: int) -> None:
        with self._lock:
            if item_id not in self._store:
                raise KeyError(f"Todo item with id {item_id} not found.")
            del self._store[item_id]
            logging.info(f"Deleted todo item {item_id}.")


# Singleton store for application lifetime
_TODO_STORE = InMemoryTodoStore()


class TodoService:
    """
    Encapsulates business logic for todo item CRUD operations.
    """

    def __init__(self, store: InMemoryTodoStore):
        self.store = store

    async def create_item(self, item: TodoItemCreate) -> TodoItemModel:
        return self.store.create(item)

    async def list_items(self) -> list[TodoItemModel]:
        return self.store.list()

    async def get_item(self, item_id: int) -> TodoItemModel:
        result = self.store.get(item_id)
        if result is None:
            logging.warning(f"Tried to get non-existent todo item {item_id}.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Todo item {item_id} not found.",
            )
        return result

    async def update_item(self, item_id: int, item: TodoItemUpdate) -> TodoItemModel:
        try:
            return self.store.update(item_id, item, partial=False)
        except KeyError:
            logging.warning(f"Tried to update non-existent todo item {item_id}.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Todo item {item_id} not found.",
            )

    async def patch_item(self, item_id: int, item: TodoItemUpdate) -> TodoItemModel:
        try:
            return self.store.update(item_id, item, partial=True)
        except KeyError:
            logging.warning(f"Tried to patch non-existent todo item {item_id}.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Todo item {item_id} not found.",
            )

    async def delete_item(self, item_id: int) -> None:
        try:
            self.store.delete(item_id)
        except KeyError:
            logging.warning(f"Tried to delete non-existent todo item {item_id}.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Todo item {item_id} not found.",
            )


# Dependency for FastAPI injection
def get_todo_service() -> TodoService:
    return TodoService(_TODO_STORE)
