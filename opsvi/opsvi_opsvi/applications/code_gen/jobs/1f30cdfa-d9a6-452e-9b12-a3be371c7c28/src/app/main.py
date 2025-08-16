import logging
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware
from app import crud, models, schemas, database
from app.exceptions import NotFoundException, ValidationException

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="FastAPI Todo List Web Service",
    description="A RESTful API for managing todos.",
    version="1.0.0",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logger.info(f"Incoming request: {request.method} {request.url}")
        response = await call_next(request)
        logger.info(f"Response status: {response.status_code}")
        return response


app.add_middleware(LoggingMiddleware)


# Create tables
@app.on_event("startup")
def on_startup():
    logger.info("Initializing database.")
    database.Base.metadata.create_all(bind=database.engine)


# Health check endpoint
@app.get("/health", tags=["Health"], response_model=schemas.HealthCheckResponse)
def health_check():
    """Healthcheck endpoint for monitoring."""
    return {"status": "ok"}


# Exception handlers
@app.exception_handler(NotFoundException)
def not_found_handler(request: Request, exc: NotFoundException):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": exc.detail},
    )


@app.exception_handler(ValidationException)
def validation_handler(request: Request, exc: ValidationException):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.detail},
    )


@app.exception_handler(Exception)
def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal Server Error"},
    )


def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post(
    "/todos",
    response_model=schemas.Todo,
    status_code=status.HTTP_201_CREATED,
    tags=["Todos"],
)
def create_todo(todo_in: schemas.TodoCreate, db: Session = Depends(get_db)):
    """Create a new todo item."""
    todo = crud.create_todo(db, todo_in)
    logger.info(f"Created todo with id={todo.id}")
    return todo


@app.get("/todos", response_model=list[schemas.Todo], tags=["Todos"])
def list_todos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all todo items."""
    todos = crud.get_todos(db, skip=skip, limit=limit)
    return todos


@app.get("/todos/{todo_id}", response_model=schemas.Todo, tags=["Todos"])
def get_todo(todo_id: int, db: Session = Depends(get_db)):
    """Retrieve a specific todo by ID."""
    todo = crud.get_todo(db, todo_id)
    if not todo:
        raise NotFoundException("Todo not found")
    return todo


@app.patch("/todos/{todo_id}", response_model=schemas.Todo, tags=["Todos"])
def update_todo(
    todo_id: int, todo_in: schemas.TodoUpdate, db: Session = Depends(get_db)
):
    """Partially update an existing todo by ID."""
    todo = crud.update_todo(db, todo_id, todo_in)
    if not todo:
        raise NotFoundException("Todo not found")
    logger.info(f"Updated todo id={todo_id}")
    return todo


@app.put("/todos/{todo_id}", response_model=schemas.Todo, tags=["Todos"])
def replace_todo(
    todo_id: int, todo_in: schemas.TodoCreate, db: Session = Depends(get_db)
):
    """Fully replace an existing todo by ID."""
    todo = crud.replace_todo(db, todo_id, todo_in)
    if not todo:
        raise NotFoundException("Todo not found")
    logger.info(f"Replaced todo id={todo_id}")
    return todo


@app.delete("/todos/{todo_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Todos"])
def delete_todo(todo_id: int, db: Session = Depends(get_db)):
    """Delete a todo item by ID."""
    success = crud.delete_todo(db, todo_id)
    if not success:
        raise NotFoundException("Todo not found")
    logger.info(f"Deleted todo id={todo_id}")
    return None
