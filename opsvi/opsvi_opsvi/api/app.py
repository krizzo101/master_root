"""FastAPI application for the software factory API."""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from fastapi import (
    BackgroundTasks,
    FastAPI,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from ..memory.graph.neo4j_client import get_neo4j_client
from ..orchestrator.meta_orchestrator import execute_software_factory_pipeline
from ..workers.celery_app import get_queue_stats, get_worker_status

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Software Factory API",
    description="API for autonomous software factory pipeline execution",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for API requests/responses
class PipelineRequest(BaseModel):
    """Request to start a pipeline execution."""

    request: str
    project_name: str
    project_description: str = ""
    pipeline_name: str = "software_factory_v1"
    config: dict[str, Any] | None = None


class PipelineResponse(BaseModel):
    """Response from pipeline execution."""

    success: bool
    project_id: str | None = None
    run_id: str | None = None
    error: str | None = None
    completed_tasks: list[str] = []
    failed_tasks: list[str] = []
    total_loops: int = 0
    task_results: dict[str, Any] = {}


class RunStatus(BaseModel):
    """Status of a pipeline run."""

    run_id: str
    project_id: str
    status: str
    current_task: str | None = None
    completed_tasks: int = 0
    failed_tasks: int = 0
    total_tasks: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    started_at: str
    completed_at: str | None = None


class TaskStatus(BaseModel):
    """Status of a specific task."""

    task_id: str
    name: str
    status: str
    task_type: str
    started_at: str | None = None
    completed_at: str | None = None
    tokens_used: int = 0
    cost_usd: float = 0.0
    error_message: str | None = None


class ArtifactInfo(BaseModel):
    """Information about an artifact."""

    artifact_id: str
    name: str
    artifact_type: str
    file_path: str
    size_bytes: int
    created_at: str


class CritiqueInfo(BaseModel):
    """Information about a critique."""

    critique_id: str
    overall_score: float
    pass_threshold: bool
    policy_scores: dict[str, float]
    reasons: list[str]
    created_at: str


# Background task storage
background_tasks: dict[str, asyncio.Task] = {}


async def execute_pipeline_background(request: PipelineRequest, task_id: str) -> None:
    """Execute pipeline in background."""
    try:
        result = await execute_software_factory_pipeline(
            request=request.request,
            project_name=request.project_name,
            project_description=request.project_description,
            pipeline_name=request.pipeline_name,
            config=request.config,
        )

        # Store result for later retrieval
        background_tasks[task_id] = result

    except Exception as e:
        logger.error(f"Background pipeline execution failed: {e}")
        background_tasks[task_id] = {"success": False, "error": str(e)}


@app.post("/api/pipeline/start", response_model=PipelineResponse)
async def start_pipeline(
    request: PipelineRequest, background_tasks: BackgroundTasks
) -> PipelineResponse:
    """Start a pipeline execution."""
    try:
        # Generate task ID
        task_id = str(UUID.uuid4())

        # Start background execution
        background_tasks.add_task(execute_pipeline_background, request, task_id)

        return PipelineResponse(
            success=True,
            project_id=None,  # Will be available after execution
            run_id=None,  # Will be available after execution
            task_id=task_id,
        )

    except Exception as e:
        logger.error(f"Failed to start pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/pipeline/status/{task_id}", response_model=PipelineResponse)
async def get_pipeline_status(task_id: str) -> PipelineResponse:
    """Get the status of a pipeline execution."""
    if task_id not in background_tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    result = background_tasks[task_id]

    if isinstance(result, dict):
        return PipelineResponse(**result)
    else:
        # Task is still running
        return PipelineResponse(
            success=False, error="Task is still running", task_id=task_id
        )


@app.get("/api/runs/{run_id}/status", response_model=RunStatus)
async def get_run_status(run_id: str) -> RunStatus:
    """Get the status of a specific run."""
    try:
        neo4j = get_neo4j_client()
        status = neo4j.get_run_status(run_id)

        if not status:
            raise HTTPException(status_code=404, detail="Run not found")

        return RunStatus(**status)

    except Exception as e:
        logger.error(f"Failed to get run status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/runs/{run_id}/tasks", response_model=list[TaskStatus])
async def get_run_tasks(run_id: str) -> list[TaskStatus]:
    """Get all tasks for a specific run."""
    try:
        neo4j = get_neo4j_client()

        # Query for tasks in the run
        query = """
        MATCH (r:Run {id: $run_id})-[:CONTAINS_TASK]->(t:Task)
        RETURN t
        ORDER BY t.created_at
        """

        result = neo4j._execute_query(query, {"run_id": run_id})

        tasks = []
        for record in result:
            task_data = record.get("t", {})
            tasks.append(
                TaskStatus(
                    task_id=task_data.get("id"),
                    name=task_data.get("name"),
                    status=task_data.get("status"),
                    task_type=task_data.get("task_type"),
                    started_at=task_data.get("started_at"),
                    completed_at=task_data.get("completed_at"),
                    tokens_used=task_data.get("tokens_used", 0),
                    cost_usd=task_data.get("cost_usd", 0.0),
                    error_message=task_data.get("error_message"),
                )
            )

        return tasks

    except Exception as e:
        logger.error(f"Failed to get run tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/runs/{run_id}/artifacts", response_model=list[ArtifactInfo])
async def get_run_artifacts(run_id: str) -> list[ArtifactInfo]:
    """Get all artifacts for a specific run."""
    try:
        neo4j = get_neo4j_client()

        # Query for artifacts in the run
        query = """
        MATCH (r:Run {id: $run_id})-[:CONTAINS_TASK]->(t:Task)-[:PRODUCED]->(a:Artifact)
        RETURN a
        ORDER BY a.created_at
        """

        result = neo4j._execute_query(query, {"run_id": run_id})

        artifacts = []
        for record in result:
            artifact_data = record.get("a", {})
            artifacts.append(
                ArtifactInfo(
                    artifact_id=artifact_data.get("id"),
                    name=artifact_data.get("name"),
                    artifact_type=artifact_data.get("artifact_type"),
                    file_path=artifact_data.get("file_path"),
                    size_bytes=artifact_data.get("size_bytes", 0),
                    created_at=artifact_data.get("created_at"),
                )
            )

        return artifacts

    except Exception as e:
        logger.error(f"Failed to get run artifacts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/runs/{run_id}/critiques", response_model=list[CritiqueInfo])
async def get_run_critiques(run_id: str) -> list[CritiqueInfo]:
    """Get all critiques for a specific run."""
    try:
        neo4j = get_neo4j_client()

        # Query for critiques in the run
        query = """
        MATCH (r:Run {id: $run_id})-[:CONTAINS_TASK]->(t:Task)-[:EMITTED]->(c:Critique)
        RETURN c
        ORDER BY c.created_at
        """

        result = neo4j._execute_query(query, {"run_id": run_id})

        critiques = []
        for record in result:
            critique_data = record.get("c", {})
            critiques.append(
                CritiqueInfo(
                    critique_id=critique_data.get("id"),
                    overall_score=critique_data.get("overall_score", 0.0),
                    pass_threshold=critique_data.get("pass_threshold", False),
                    policy_scores=critique_data.get("policy_scores", {}),
                    reasons=critique_data.get("reasons", []),
                    created_at=critique_data.get("created_at"),
                )
            )

        return critiques

    except Exception as e:
        logger.error(f"Failed to get run critiques: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/artifacts/{artifact_id}/download")
async def download_artifact(artifact_id: str):
    """Download an artifact file."""
    try:
        neo4j = get_neo4j_client()

        # Query for artifact
        query = """
        MATCH (a:Artifact {id: $artifact_id})
        RETURN a
        """

        result = neo4j._execute_query(query, {"artifact_id": artifact_id})

        if not result:
            raise HTTPException(status_code=404, detail="Artifact not found")

        artifact_data = result[0].get("a", {})
        file_path = artifact_data.get("file_path")

        if not file_path or not Path(file_path).exists():
            raise HTTPException(status_code=404, detail="Artifact file not found")

        return FileResponse(
            path=file_path,
            filename=artifact_data.get("name", "artifact"),
            media_type=artifact_data.get("mime_type", "application/octet-stream"),
        )

    except Exception as e:
        logger.error(f"Failed to download artifact: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/projects/{project_id}/lineage")
async def get_project_lineage(project_id: str) -> dict[str, Any]:
    """Get the complete lineage for a project."""
    try:
        neo4j = get_neo4j_client()
        lineage = neo4j.get_project_lineage(project_id)
        return lineage

    except Exception as e:
        logger.error(f"Failed to get project lineage: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/queue/stats")
async def get_queue_stats() -> dict[str, Any]:
    """Get queue statistics."""
    try:
        stats = get_queue_stats()
        return stats

    except Exception as e:
        logger.error(f"Failed to get queue stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/workers/status")
async def get_workers_status() -> dict[str, Any]:
    """Get worker status information."""
    try:
        status = get_worker_status()
        return status

    except Exception as e:
        logger.error(f"Failed to get worker status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/pipelines")
async def list_pipelines() -> list[str]:
    """List available pipelines."""
    try:
        from ..orchestrator.dag_loader import dag_loader

        pipelines = dag_loader.list_pipelines()
        return pipelines

    except Exception as e:
        logger.error(f"Failed to list pipelines: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health_check() -> dict[str, Any]:
    """Health check endpoint."""
    try:
        # Check Neo4j connection
        neo4j = get_neo4j_client()
        neo4j._execute_query("RETURN 1", {})

        # Check Celery workers
        worker_status = get_worker_status()

        return {
            "status": "healthy",
            "neo4j_connected": True,
            "workers_available": len(worker_status.get("workers", [])),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }


# WebSocket endpoint for real-time updates
@app.websocket("/ws/runs/{run_id}")
async def websocket_run_updates(websocket: WebSocket, run_id: str):
    """WebSocket endpoint for real-time run updates."""
    await websocket.accept()

    try:
        neo4j = get_neo4j_client()

        while True:
            # Get current run status
            status = neo4j.get_run_status(run_id)

            if status:
                await websocket.send_json(status)

            # Wait before next update
            await asyncio.sleep(5)

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for run {run_id}")
    except Exception as e:
        logger.error(f"WebSocket error for run {run_id}: {e}")
        try:
            await websocket.send_json({"error": str(e)})
        except:
            pass


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
