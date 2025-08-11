"""
FastAPI application for the Auto-Forge factory.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from ..core.orchestrator import AutoForgeOrchestrator
from ..models.schemas import (
    DevelopmentRequest,
    DevelopmentResponse,
    JobProgress,
    JobResult,
    HealthCheck,
    FactoryConfig,
    AgentConfig,
    AgentType,
    Language,
    Framework,
    CloudProvider,
)


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Global orchestrator instance
orchestrator: AutoForgeOrchestrator = None


def create_default_config() -> FactoryConfig:
    """Create default factory configuration."""

    # Default agent configurations
    agent_configs = {}

    for agent_type in AgentType:
        agent_configs[agent_type] = AgentConfig(
            agent_type=agent_type,
            model=(
                "gpt-4"
                if agent_type
                in [AgentType.PLANNER, AgentType.ARCHITECT, AgentType.CRITIC]
                else "gpt-4"
            ),
            temperature=0.1,
            max_tokens=4000,
            timeout_seconds=300,
            retry_attempts=3,
            quality_threshold=0.8,
            enabled=True,
        )

    return FactoryConfig(
        max_concurrent_jobs=10,
        max_agents_per_job=8,
        default_timeout_seconds=3600,
        agent_configs=agent_configs,
        supported_languages=[
            Language.PYTHON,
            Language.JAVASCRIPT,
            Language.TYPESCRIPT,
            Language.GO,
            Language.RUST,
            Language.JAVA,
            Language.C_SHARP,
            Language.CPP,
            Language.PHP,
            Language.RUBY,
        ],
        supported_frameworks=[
            Framework.FASTAPI,
            Framework.DJANGO,
            Framework.FLASK,
            Framework.REACT,
            Framework.VUE,
            Framework.ANGULAR,
            Framework.EXPRESS,
            Framework.GIN,
            Framework.ECHO,
            Framework.ACTIX,
            Framework.ROCKET,
            Framework.SPRING,
            Framework.ASPNET,
            Framework.LARAVEL,
            Framework.RAILS,
        ],
        supported_cloud_providers=[
            CloudProvider.AWS,
            CloudProvider.GCP,
            CloudProvider.AZURE,
            CloudProvider.DIGITALOCEAN,
            CloudProvider.HEROKU,
            CloudProvider.VERCEL,
            CloudProvider.NETLIFY,
        ],
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global orchestrator

    # Startup
    logger.info("Starting Auto-Forge Factory...")

    # Initialize orchestrator
    config = create_default_config()
    orchestrator = AutoForgeOrchestrator(config)

    logger.info("Auto-Forge Factory started successfully")

    yield

    # Shutdown
    logger.info("Shutting down Auto-Forge Factory...")

    # Clean up any active jobs
    if orchestrator:
        for job_id in list(orchestrator.active_jobs.keys()):
            orchestrator.cancel_job(job_id)

    logger.info("Auto-Forge Factory shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Auto-Forge Factory",
    description="Production-ready autonomous software development factory",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# WebSocket connection manager
class ConnectionManager:
    """Manage WebSocket connections for real-time updates."""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, job_id: str):
        """Connect a WebSocket for a specific job."""
        await websocket.accept()
        self.active_connections[job_id] = websocket
        logger.info(f"WebSocket connected for job {job_id}")

    def disconnect(self, job_id: str):
        """Disconnect a WebSocket for a specific job."""
        if job_id in self.active_connections:
            del self.active_connections[job_id]
            logger.info(f"WebSocket disconnected for job {job_id}")

    async def send_progress_update(self, job_id: str, data: Dict[str, Any]):
        """Send progress update to a specific job's WebSocket."""
        if job_id in self.active_connections:
            try:
                await self.active_connections[job_id].send_json(
                    {
                        "type": "progress",
                        "job_id": job_id,
                        "data": data,
                        "timestamp": data.get("updated_at"),
                    }
                )
            except Exception as e:
                logger.error(f"Error sending WebSocket update for job {job_id}: {e}")
                self.disconnect(job_id)


manager = ConnectionManager()


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Auto-Forge Factory API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    factory_status = orchestrator.get_factory_status()

    return HealthCheck(
        status="healthy",
        timestamp=orchestrator.job_progress.get("timestamp", "unknown"),
        version="1.0.0",
        services={"orchestrator": "healthy", "agent_registry": "healthy"},
        agents=factory_status.get("agent_registry_status", {}).get(
            "agent_statuses", {}
        ),
        queue_size=0,  # TODO: Implement queue
        active_jobs=factory_status.get("active_jobs", 0),
    )


@app.post("/develop", response_model=DevelopmentResponse)
async def start_development(request: DevelopmentRequest):
    """Start a new development job."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    try:
        # Check if we can accept more jobs
        factory_status = orchestrator.get_factory_status()
        if factory_status["active_jobs"] >= orchestrator.config.max_concurrent_jobs:
            raise HTTPException(
                status_code=429,
                detail=f"Maximum concurrent jobs ({orchestrator.config.max_concurrent_jobs}) reached",
            )

        # Start the development job
        job_id = await orchestrator.start_development_job(request)

        logger.info(f"Started development job {job_id} for project: {request.name}")

        return DevelopmentResponse(
            job_id=job_id,
            status="pending",
            message=f"Development job started successfully. Job ID: {job_id}",
            progress_url=f"/status/{job_id}",
            websocket_url=f"/ws/{job_id}",
        )

    except Exception as e:
        logger.error(f"Error starting development job: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to start development job: {e}"
        )


@app.get("/status/{job_id}", response_model=JobProgress)
async def get_job_status(job_id: str):
    """Get the status of a development job."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    try:
        job_uuid = job_id
        progress = orchestrator.get_job_progress(job_uuid)

        if not progress:
            raise HTTPException(status_code=404, detail="Job not found")

        return progress

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")
    except Exception as e:
        logger.error(f"Error getting job status for {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get job status: {e}")


@app.get("/artifacts/{job_id}", response_model=JobResult)
async def get_job_artifacts(job_id: str):
    """Get the artifacts and results of a completed development job."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    try:
        job_uuid = job_id
        result = orchestrator.get_job_result(job_uuid)

        if not result:
            # Check if job is still running
            progress = orchestrator.get_job_progress(job_uuid)
            if progress and progress.status.value in ["pending", "running"]:
                raise HTTPException(
                    status_code=202,
                    detail="Job is still running. Use /status/{job_id} to check progress.",
                )
            else:
                raise HTTPException(
                    status_code=404, detail="Job not found or not completed"
                )

        return result

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job artifacts for {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get job artifacts: {e}")


@app.delete("/jobs/{job_id}")
async def cancel_job(job_id: str):
    """Cancel a running development job."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    try:
        job_uuid = job_id
        cancelled = orchestrator.cancel_job(job_uuid)

        if not cancelled:
            raise HTTPException(
                status_code=404, detail="Job not found or already completed"
            )

        logger.info(f"Cancelled job {job_id}")

        return {"message": f"Job {job_id} cancelled successfully"}

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel job: {e}")


@app.get("/jobs")
async def list_jobs():
    """List all jobs (active and completed)."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    try:
        active_jobs = []
        for job_id, job_info in orchestrator.active_jobs.items():
            active_jobs.append(
                {
                    "job_id": str(job_id),
                    "project_name": job_info["request"].name,
                    "status": "active",
                    "started_at": job_info["started_at"].isoformat(),
                    "current_phase": job_info["current_phase"],
                }
            )

        completed_jobs = []
        for job_id, result in orchestrator.job_results.items():
            completed_jobs.append(
                {
                    "job_id": str(job_id),
                    "project_name": (
                        result.summary.split("'")[1]
                        if "'" in result.summary
                        else "Unknown"
                    ),
                    "status": result.status.value,
                    "completed_at": (
                        result.completed_at.isoformat() if result.completed_at else None
                    ),
                    "quality_score": result.quality_score,
                    "total_cost": result.total_cost,
                }
            )

        return {
            "active_jobs": active_jobs,
            "completed_jobs": completed_jobs,
            "total_active": len(active_jobs),
            "total_completed": len(completed_jobs),
        }

    except Exception as e:
        logger.error(f"Error listing jobs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list jobs: {e}")


@app.get("/factory/status")
async def get_factory_status():
    """Get overall factory status."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    try:
        return orchestrator.get_factory_status()

    except Exception as e:
        logger.error(f"Error getting factory status: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get factory status: {e}"
        )


@app.get("/factory/config")
async def get_factory_config():
    """Get factory configuration."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    return orchestrator.config


@app.websocket("/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    """WebSocket endpoint for real-time job updates."""
    await manager.connect(websocket, job_id)

    try:
        while True:
            # Keep connection alive and wait for client disconnect
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(job_id)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


if __name__ == "__main__":
    uvicorn.run(
        "auto_forge_factory.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
