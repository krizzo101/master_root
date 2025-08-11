import logging
from typing import List
from fastapi import FastAPI, HTTPException, Path, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from app.models import TaskCreate, TaskUpdate, Task, ErrorResponse
from app.storage import TaskStorage

logger = logging.getLogger("task_api")
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="FastAPI Task Management Web API",
    version="1.0.0",
    description="A simple, in-memory RESTful API to manage tasks",
)

# Allow cross-origin requests (for Swagger UI, development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware for logging requests
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logger.info(f"Request: {request.method} {request.url}")
        response = await call_next(request)
        logger.info(f"Response status: {response.status_code}")
        return response


app.add_middleware(LoggingMiddleware)

# Global in-memory storage instance
storage = TaskStorage()


@app.get("/health", summary="Health Check", tags=["Utility"], response_model=dict)
async def health_check() -> dict:
    """Health check endpoint to verify the API is up and running."""
    return {"status": "ok"}


@app.post(
    "/tasks",
    response_model=Task,
    status_code=status.HTTP_201_CREATED,
    summary="Create a New Task",
    responses={
        201: {"description": "Task created successfully"},
        400: {"model": ErrorResponse},
    },
    tags=["Tasks"],
)
async def create_task(task_data: TaskCreate) -> Task:
    """Create a new task with the provided information."""
    created_task = storage.create_task(task_data)
    logger.info(f"Task created: {created_task}")
    return created_task


@app.get(
    "/tasks",
    response_model=List[Task],
    summary="List All Tasks",
    responses={200: {"description": "List of all tasks."}},
    tags=["Tasks"],
)
async def get_all_tasks() -> List[Task]:
    """Retrieve a list of all tasks in the system."""
    tasks = storage.list_tasks()
    logger.info(f"Retrieved {len(tasks)} tasks")
    return tasks


@app.get(
    "/tasks/{task_id}",
    response_model=Task,
    summary="Get Task Details by ID",
    responses={
        200: {"description": "Task retrieved successfully."},
        404: {"model": ErrorResponse},
    },
    tags=["Tasks"],
)
async def get_task(
    task_id: int = Path(..., description="The unique identifier of the task", gt=0)
) -> Task:
    """Retrieve details of a specific task by its ID."""
    task = storage.get_task(task_id)
    if task is None:
        logger.warning(f"Task not found: ID {task_id}")
        raise HTTPException(status_code=404, detail="Task not found.")
    logger.info(f"Retrieved task: {task}")
    return task


@app.put(
    "/tasks/{task_id}",
    response_model=Task,
    summary="Update an Existing Task",
    responses={
        200: {"description": "Task updated successfully."},
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
    tags=["Tasks"],
)
async def update_task(
    task_id: int = Path(
        ..., description="The unique identifier of the task to update", gt=0
    ),
    task_update: TaskUpdate = ...,
) -> Task:
    """Update the details of an existing task (partial or full update)."""
    updated_task = storage.update_task(task_id, task_update)
    if updated_task is None:
        logger.warning(f"Task not found for update: ID {task_id}")
        raise HTTPException(status_code=404, detail="Task not found.")
    logger.info(f"Task updated: {updated_task}")
    return updated_task


@app.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a Task",
    responses={
        204: {"description": "Task deleted successfully."},
        404: {"model": ErrorResponse},
    },
    tags=["Tasks"],
)
async def delete_task(
    task_id: int = Path(
        ..., description="The unique identifier of the task to delete", gt=0
    )
) -> None:
    """Delete a task from the system by its ID."""
    result = storage.delete_task(task_id)
    if not result:
        logger.warning(f"Task not found for deletion: ID {task_id}")
        raise HTTPException(status_code=404, detail="Task not found.")
    logger.info(f"Task deleted: ID {task_id}")
    return


@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTPException: {exc.detail}")
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


@app.exception_handler(Exception)
async def internal_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {repr(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal server error."},
    )
