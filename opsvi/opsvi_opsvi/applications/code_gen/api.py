"""FastAPI interface for the code generation utility."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Dict, Any

import logging
from fastapi import FastAPI, HTTPException, Body, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

import time
from config import config
from logging_config import setup_logging
from rate_limiting import rate_limit_middleware, rate_limiter
from validation import validator, validate_job_id, ValidationError
from schemas import RequirementsSpec
from pipeline import build_pipeline
from database import create_job, update_job, get_job_data, init_db
from task_queue import run_pipeline

from local_shared.openai_interfaces.responses_interface import OpenAIResponsesInterface  # type: ignore
from threading import Thread
import os
from ws_router import ws_router
from fastapi.responses import JSONResponse
from datetime import datetime

# Application start time for uptime tracking
_start_time = datetime.now()
from ai_agents import analyze_request_security_with_ai

# Initialize interfaces
_openai_interface = OpenAIResponsesInterface()

# Build pipeline placeholder (no tools yet)
_pipeline = build_pipeline([])

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Initialize database
init_db()

# In-memory job store placeholder; replace with persistent DB in production
_jobs: Dict[str, Path] = {}

# Application metrics
_metrics = {
    "start_time": time.time(),
    "total_requests": 0,
    "active_jobs": 0,
    "completed_jobs": 0,
    "failed_jobs": 0,
    "validation_errors": 0,
}

app = FastAPI(
    title="Code Generation Utility",
    description="Automated Python code generation with SDLC pipeline",
    version="1.0.0",
)

# Include WebSocket router
app.include_router(ws_router)


# ---------------------------------------------------------------------------
# Request/response logging middleware
# ---------------------------------------------------------------------------


@app.middleware("http")
async def log_requests(request: Request, call_next):  # type: ignore[override]
    logger.info(f"HTTP {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(
        "Completed %s %s -> %s", request.method, request.url.path, response.status_code
    )
    return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # Allow Tailwind & DaisyUI CDN for styles/scripts
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-hashes' https://cdn.tailwindcss.com https://cdn.jsdelivr.net; "
            "style-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
            "img-src 'self' data:; font-src 'self' data:;"
        )

        # Add rate limit headers if available
        if hasattr(request.state, "rate_limit_info"):
            info = request.state.rate_limit_info
            response.headers["X-RateLimit-Limit"] = str(info["limit"])
            response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
            response.headers["X-RateLimit-Reset"] = str(int(info["reset_at"]))

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware."""

    async def dispatch(self, request: Request, call_next):
        await rate_limit_middleware(request)
        return await call_next(request)


# Add middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)

# Compute absolute path to the static directory (same folder as this file)
_static_dir = Path(__file__).resolve().parent / "static"
if not _static_dir.exists():
    raise RuntimeError(f"Static directory not found at {_static_dir}")

app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")


@app.get("/")
async def root():
    """Serve the default web UI."""
    return FileResponse(_static_dir / "index.html")


@app.get("/favicon.ico")
async def favicon():
    """Serve favicon."""
    return FileResponse(_static_dir / "favicon.ico")


@app.get("/original")
async def original_ui():
    """Serve the original web UI."""
    return FileResponse(_static_dir / "index_v2.html")


@app.get("/cyberpunk")
async def cyberpunk_ui():
    """Serve the Cyberpunk-themed web UI."""
    return FileResponse(_static_dir / "index_cyberpunk.html")


@app.get("/holographic")
async def holographic_ui():
    """Serve the Holographic-themed web UI."""
    return FileResponse(_static_dir / "index_holographic.html")


@app.get("/quantum")
async def quantum_ui():
    """Serve the Quantum-themed web UI."""
    return FileResponse(_static_dir / "index_quantum.html")


@app.get("/industrial")
async def industrial_ui():
    """Serve the industrial masculine web UI."""
    return FileResponse(_static_dir / "index_industrial.html")


@app.get("/steampunk")
async def steampunk_ui():
    """Serve the steampunk industrial web UI."""
    return FileResponse(_static_dir / "index_steampunk.html")


@app.get("/ai")
async def ai_ui():
    """Serve the AI-themed web UI."""
    return FileResponse(_static_dir / "index_ai.html")


@app.get("/matrix")
async def matrix_ui():
    """Serve the Matrix-themed web UI."""
    return FileResponse(_static_dir / "index_matrix.html")


@app.get("/davinci")
async def davinci_ui():
    """Serve the Da Vinci-themed web UI."""
    return FileResponse(_static_dir / "index_davinci.html")


@app.get("/space")
async def space_ui():
    """Serve the Space-themed web UI."""
    return FileResponse(_static_dir / "index_space.html")


@app.get("/psychedelic")
async def psychedelic_ui():
    """Serve the Psychedelic-themed web UI."""
    return FileResponse(_static_dir / "index_psychedelic.html")


@app.get("/neural")
async def neural_ui():
    """Serve the Neural Network-themed web UI."""
    return FileResponse(_static_dir / "index_neural.html")


@app.get("/health")
async def health_check() -> dict[str, Any]:
    """Health check endpoint with dependency status."""
    from dependency_manager import health_check_dependencies

    dependencies = health_check_dependencies()
    overall_status = "healthy" if all(dependencies.values()) else "degraded"

    return {
        "status": overall_status,
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "dependencies": dependencies,
        "uptime_seconds": (datetime.now() - _start_time).total_seconds(),
    }


@app.get("/metrics")
async def metrics() -> dict[str, Any]:
    """Prometheus-style metrics endpoint."""
    uptime = time.time() - _metrics["start_time"]

    # Count job statuses
    active_jobs = 0
    completed_jobs = 0
    failed_jobs = 0

    for job_dir in _jobs.values():
        if (job_dir / "DONE").exists():
            completed_jobs += 1
        elif (job_dir / "error.log").exists():
            failed_jobs += 1
        else:
            active_jobs += 1

    return {
        "codegen_uptime_seconds": uptime,
        "codegen_requests_total": _metrics["total_requests"],
        "codegen_jobs_active": active_jobs,
        "codegen_jobs_completed_total": completed_jobs,
        "codegen_jobs_failed_total": failed_jobs,
        "codegen_validation_errors_total": _metrics["validation_errors"],
        "codegen_jobs_total": len(_jobs),
    }


@app.get("/info")
async def info() -> dict[str, Any]:
    """Application information endpoint."""
    return {
        "name": "Code Generation Utility",
        "version": "1.0.0",
        "description": "Automated Python code generation with SDLC pipeline",
        "features": [
            "Project template generation",
            "Automated testing",
            "Documentation generation",
            "Artifact packaging",
            "Multiple project types (CLI, Web API, Data Processor, Web App)",
        ],
        "supported_models": [
            config.openai_model_o4_mini,
            config.openai_model_gpt41,
            config.openai_model_gpt41_mini,
        ],
        "project_types": [
            "CLI_TOOL",
            "WEB_API",
            "DATA_PROCESSOR",
            "WEB_APP",
            "SIMPLE_SCRIPT",
        ],
        "endpoints": {
            "POST /chat": "Create new generation job",
            "GET /status/{job_id}": "Check job status",
            "GET /artifacts/{job_id}": "Download project artifacts",
            "GET /health": "Health check",
            "GET /metrics": "Application metrics",
            "GET /info": "Application information",
        },
    }


@app.get("/rate-limit-status")
async def rate_limit_status() -> dict[str, Any]:
    """Get rate limiting status (admin endpoint)."""
    return rate_limiter.get_status()


@app.post("/chat")
async def chat(request: Request) -> JSONResponse:
    """Handle chat/generation requests."""
    try:
        data = await request.json()
        if isinstance(data, str):
            user_request = data.strip()
            options = {}
        elif isinstance(data, dict):
            user_request = data.get("request", "").strip()
            options = data.get("options", {})
        else:
            return JSONResponse(
                status_code=400, content={"error": "Invalid request format"}
            )

        logger.info(
            "New chat request received",
            extra={
                "request_length": len(user_request),
                "has_rate_limit": hasattr(request.state, "rate_limited"),
            },
        )

        if not user_request:
            return JSONResponse(
                status_code=400, content={"error": "Request cannot be empty"}
            )

        # Security analysis
        # security_analysis = analyze_request_security_with_ai(user_request)

        # if not security_analysis.is_safe:
        #     logger.warning(
        #         f"Request blocked due to security concerns: {security_analysis.concerns}"
        #     )
        #     return JSONResponse(
        #         status_code=403,
        #         content={
        #             "error": "Request blocked for security reasons",
        #             "concerns": security_analysis.concerns,
        #             "recommendations": security_analysis.recommendations,
        #         },
        #     )

        logger.info("Request validated successfully (security check bypassed)")

        # Create job entry in database
        job_id = str(uuid.uuid4())
        logger.info(f"Generated job ID: {job_id}")

        try:
            create_job(job_id, user_request)
            logger.info(f"Job {job_id} created in database successfully")
        except Exception as db_error:
            logger.error(f"Failed to create job in database: {db_error}")
            return JSONResponse(status_code=500, content={"error": "Database error"})

        try:
            # Enqueue job with Celery (dependencies ensure this works)
            task_result = run_pipeline.delay(job_id, options)
            logger.info(
                f"Job {job_id} enqueued successfully with task ID: {task_result.id}, options: {options}"
            )
        except Exception as celery_error:
            logger.error(f"Failed to enqueue job {job_id}: {celery_error}")
            return JSONResponse(status_code=500, content={"error": "Queue error"})

        return JSONResponse(content={"job_id": job_id})

    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        return JSONResponse(status_code=500, content={"error": "Internal server error"})


@app.get("/status/{job_id}")
async def status(job_id: str) -> dict[str, Any]:
    # Validate job_id format
    if not validate_job_id(job_id):
        logger.warning(f"Invalid job ID format: {job_id}")
        raise HTTPException(status_code=400, detail="Invalid job_id format")

    db_job_dict = get_job_data(job_id)
    if not db_job_dict:
        logger.warning(f"Status requested for unknown job: {job_id}")
        raise HTTPException(status_code=404, detail="Unknown job_id")

    job_dir = config.job_output_dir / job_id

    # Enhanced status checking
    status_info: dict[str, Any] = {
        "job_id": job_id,
        "status": db_job_dict["status"],
        "phase": db_job_dict.get("phase"),
        "progress": db_job_dict.get("progress"),
    }

    # If DB says completed and artifacts ready, add flag
    if db_job_dict["status"] == "completed":
        status_info["artifacts_ready"] = bool(db_job_dict.get("artifacts_path"))

    if (job_dir / "DONE").exists():
        status_info["status"] = "completed"
        # Add completion details
        if (job_dir / "test_output.log").exists():
            test_output = (job_dir / "test_output.log").read_text()
            if "passed" in test_output:
                status_info["tests_passed"] = True
        if (job_dir / "artifacts.zip").exists():
            status_info["artifacts_ready"] = True

        # Add full job results for completed jobs
        try:
            # Look for results in architecture and docs directories
            if (job_dir / "architecture" / "0001-project-architecture.md").exists():
                status_info["architecture"] = {
                    "adr_generated": True,
                    "components": "Available in ADR",
                }

            # Add basic requirements info
            status_info["requirements"] = {
                "extracted": True,
                "title": "Project requirements extracted",
            }

            # Add test report info
            if (job_dir / "test_output.log").exists():
                test_content = (job_dir / "test_output.log").read_text()
                status_info["test_report"] = {"completed": True, "log_available": True}
        except Exception as e:
            logger.warning(f"Failed to read job completion details: {e}")
    elif (job_dir / "error.log").exists():
        status_info["status"] = "failed"
        error_content = (job_dir / "error.log").read_text()
        status_info["error"] = error_content[:500]  # Truncate long errors
    else:
        # fallback detailed phase detection
        if status_info["phase"] is None:
            if (job_dir / "architecture").exists():
                status_info["phase"] = "architecture_complete"
            elif (job_dir / "src").exists():
                status_info["phase"] = "code_generated"
            elif (job_dir / "requirements.txt").exists():
                status_info["phase"] = "requirements_generated"

    return status_info


@app.get("/progress/{job_id}")
async def get_job_progress(job_id: str) -> dict[str, Any]:
    """Get real-time job progress with fallback support."""
    try:
        # Validate job_id format
        if not validate_job_id(job_id):
            logger.warning(f"Invalid job ID format: {job_id}")
            raise HTTPException(status_code=400, detail="Invalid job_id format")

        # First, try to get from database
        job_data = get_job_data(job_id)
        if not job_data:
            raise HTTPException(status_code=404, detail="Job not found")

        # Check for real-time progress updates in fallback cache
        from ws_router import get_progress_fallback

        real_time_progress = get_progress_fallback(job_id)

        # Check for artifacts file to set artifacts_ready flag
        job_dir = config.job_output_dir / job_id
        artifacts_ready = False

        if job_data.get("status") == "completed":
            # Check both database path and physical file
            artifacts_ready = (
                bool(job_data.get("artifacts_path"))
                or (job_dir / "artifacts.zip").exists()
            )

        if real_time_progress:
            # Merge real-time data with database data
            return {
                "job_id": job_id,
                "status": real_time_progress.get("status", job_data["status"]),
                "phase": real_time_progress.get("phase", job_data.get("phase")),
                "progress": real_time_progress.get("progress", job_data["progress"]),
                "message": real_time_progress.get("message", ""),
                "error": real_time_progress.get("error", job_data.get("error")),
                "artifacts_path": job_data.get("artifacts_path"),
                "artifacts_ready": artifacts_ready,
                "real_time": True,
                "timestamp": datetime.now().isoformat(),
            }
        else:
            # Return database data only
            return {
                "job_id": job_id,
                "status": job_data["status"],
                "phase": job_data.get("phase"),
                "progress": job_data["progress"],
                "message": "",
                "error": job_data.get("error"),
                "artifacts_path": job_data.get("artifacts_path"),
                "artifacts_ready": artifacts_ready,
                "real_time": False,
                "timestamp": datetime.now().isoformat(),
            }

    except Exception as e:
        logger.error(f"Error getting job progress: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/artifacts/{job_id}")
async def artifacts(job_id: str) -> FileResponse:
    """Download artifacts ZIP for completed job."""
    # Validate job_id format
    if not validate_job_id(job_id):
        logger.warning(f"Invalid job ID format for artifacts: {job_id}")
        raise HTTPException(status_code=400, detail="Invalid job_id format")

    db_job_dict = get_job_data(job_id)
    if not db_job_dict:
        raise HTTPException(status_code=404, detail="Unknown job_id")

    # Try multiple possible locations for the artifacts file
    possible_paths = []

    # 1. Use the path from database if it exists
    if db_job_dict.get("artifacts_path"):
        possible_paths.append(Path(db_job_dict.get("artifacts_path")))

    # 2. Look in config.job_output_dir relative to current working directory
    possible_paths.append(config.job_output_dir / job_id / "artifacts.zip")

    # 3. Look in src/applications/code_gen/jobs (where Celery worker creates files)
    possible_paths.append(
        Path("src/applications/code_gen/jobs") / job_id / "artifacts.zip"
    )

    # 4. Look relative to the API file location
    api_dir = Path(__file__).parent
    possible_paths.append(api_dir / "jobs" / job_id / "artifacts.zip")

    # Find the first path that exists
    artifact_path = None
    for path in possible_paths:
        if path.exists():
            artifact_path = path
            break

    if not artifact_path:
        logger.error(
            f"Artifacts ZIP not found for job {job_id}. Tried paths: {[str(p) for p in possible_paths]}"
        )
        raise HTTPException(status_code=404, detail="Artifacts not found")

    # Check for DONE file in the same directory as the artifacts
    done_file = artifact_path.parent / "DONE"
    if not done_file.exists():
        logger.warning(f"Artifacts requested for incomplete job: {job_id}")
        raise HTTPException(status_code=409, detail="Job not yet completed")

    # Look for artifacts.zip created by the pipeline
    if not artifact_path.exists():
        logger.error(f"Artifacts ZIP not found for job: {job_id}")
        raise HTTPException(status_code=404, detail="Artifacts not found")

    logger.info(f"Serving artifacts for job: {job_id}")
    return FileResponse(
        path=artifact_path,
        filename=f"project_{job_id[:8]}.zip",
        media_type="application/zip",
    )
