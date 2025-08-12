"""
Main entrypoint for the Task Management API.
"""
import logging
import sys

import uvicorn
from fastapi import FastAPI
from fastapi.exception_handlers import RequestValidationError
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.requests import Request
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

from app.database import init_db
from app.middleware import setup_middleware
from app.routers import health, tasks

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Task Management API",
    description="A simple FastAPI-powered RESTful web API for task management.",
    version="1.0.0",
    contact={"name": "Task Management API Team", "email": "dev@example.com"},
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Register middleware
setup_middleware(app)

# Include routers
app.include_router(health.router)
app.include_router(tasks.router)


@app.on_event("startup")
async def on_startup():
    # Ensure database tables are created
    await init_db()
    logger.info("Application startup complete.")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": exc.body},
    )


@app.get("/", tags=["root"])
async def root():
    return {"message": "Welcome to the Task Management API! See /docs for usage."}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
