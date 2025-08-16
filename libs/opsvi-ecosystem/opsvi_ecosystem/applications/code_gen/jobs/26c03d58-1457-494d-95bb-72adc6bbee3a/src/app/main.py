"""
Main FastAPI application for Todo List REST API.
Handles all routing, dependency injection, and startup configuration.
"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_api_settings
from app.middleware.error_handling import add_exception_handlers
from app.routers import todo

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app with settings
description = """
A simple Todo List REST API built with FastAPI.
Supports CRUD operations on todo items in an in-memory store.
"""
settings = get_api_settings()

app = FastAPI(
    title="Todo List REST API",
    version="1.0.0",
    description=description,
    contact={"name": "API Support", "email": "support@example.com"},
    docs_url="/docs",
    redoc_url="/redoc",
)

# Middleware: CORS (allow everything for demo purposes)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom error handling middleware
add_exception_handlers(app)

# Routers
app.include_router(todo.router, prefix="/todos", tags=["todos"])


# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check() -> dict:
    """Simple health check."""
    logger.debug("Health check endpoint called.")
    return {"status": "ok"}


# Root endpoint
@app.get("/", include_in_schema=False)
async def root() -> dict:
    return {"message": "Welcome to the Todo List REST API."}
