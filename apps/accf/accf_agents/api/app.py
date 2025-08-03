"""
FastAPI application for the ACCF Research Agent.

This module provides the main FastAPI application with health checks,
task execution endpoints, and agent management.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from ..core.settings import get_settings
from ..core.orchestrator import AgentOrchestrator
from ..utils.logging import setup_logging

# Global orchestrator instance
_orchestrator: AgentOrchestrator = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global _orchestrator

    # Startup
    settings = get_settings()
    setup_logging(settings)

    logger = logging.getLogger("api")
    logger.info("Starting ACCF Research Agent API")

    # Initialize orchestrator
    _orchestrator = AgentOrchestrator(settings)
    await _orchestrator.initialize()

    logger.info("ACCF Research Agent API started successfully")

    yield

    # Shutdown
    if _orchestrator:
        await _orchestrator.shutdown()
    logger.info("ACCF Research Agent API shutdown complete")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(
        title="ACCF Research Agent",
        description="Production-ready research agent system with Neo4j GraphRAG integration",
        version="0.5.0",
        lifespan=lifespan,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    from .endpoints import health, tasks, agents

    app.include_router(health.router, prefix="/health", tags=["health"])
    app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
    app.include_router(agents.router, prefix="/agents", tags=["agents"])

    return app


def get_app() -> FastAPI:
    """Get the FastAPI application instance."""
    return create_app()


def get_orchestrator() -> AgentOrchestrator:
    """Get the global orchestrator instance."""
    if _orchestrator is None:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    return _orchestrator


# Create the app instance
app = create_app()
