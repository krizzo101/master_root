import threading
from typing import Dict, List, Optional
from app.models import Task, TaskCreate, TaskUpdate


class TaskStorage:
    """In-memory storage backend for tasks."""

    def __init__(self):
        self._tasks: Dict[int, Task] = {}
        self._counter = 1
        self._lock = threading.Lock()

    def create_task(self, task_data: TaskCreate) -> Task:
        with self._lock:
            task = Task(id=self._counter, **task_data.dict())
            self._tasks[self._counter] = task
            self._counter += 1
            return task

    def list_tasks(self) -> List[Task]:
        with self._lock:
            return list(self._tasks.values())

    def get_task(self, task_id: int) -> Optional[Task]:
        with self._lock:
            return self._tasks.get(task_id)

    def update_task(self, task_id: int, updates: TaskUpdate) -> Optional[Task]:
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return None
            update_data = updates.dict(exclude_unset=True)
            updated_fields = task.dict()
            updated_fields.update(update_data)
            updated_task = Task(**updated_fields)
            self._tasks[task_id] = updated_task
            return updated_task

    def delete_task(self, task_id: int) -> bool:
        with self._lock:
            if task_id in self._tasks:
                del self._tasks[task_id]
                return True
            return False
