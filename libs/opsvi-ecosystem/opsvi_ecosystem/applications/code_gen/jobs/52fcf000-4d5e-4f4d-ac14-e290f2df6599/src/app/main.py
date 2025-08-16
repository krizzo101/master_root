"""
Main FastAPI application entry point for Automated Python Code Review Web Application.
Handles API routing, initialization, lifespan events, and middleware.
"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from app.api import router as api_router
from app.auth import router as auth_router
from app.config import settings
from app.db import Base, engine
from app.github import router as github_router
from app.views import router as view_router

# Initialize database
Base.metadata.create_all(bind=engine)

# Set up logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Automated Python Code Review API", docs_url="/docs", redoc_url="/redoc"
)

# Session, CORS, static/media serving
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve template static and uploaded code (for download links)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Routers
app.include_router(view_router)
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(api_router, prefix="/api", tags=["api"])
app.include_router(github_router, prefix="/github", tags=["github"])


@app.get("/health", tags=["health"])
def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "ok"}


@app.on_event("startup")
def startup_event():
    logger.info("App startup: Verifying database and initializing services.")


@app.on_event("shutdown")
def shutdown_event():
    logger.info("App shutdown: Cleaning up resources.")
