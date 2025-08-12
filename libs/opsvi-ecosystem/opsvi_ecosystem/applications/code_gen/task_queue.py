from __future__ import annotations

"""Celery application used for asynchronous pipeline execution."""

from celery import Celery
from logging import getLogger
from applications.code_gen.config import config
from applications.code_gen.pipeline import build_pipeline
from applications.code_gen.database import update_job, get_job_data
from applications.code_gen.ws_router import publish_progress_update
from pathlib import Path
import traceback

logger = getLogger(__name__)

celery = Celery(
    "code_gen",
    broker=config.redis_url,
    backend=config.redis_url,
)


@celery.task(name="code_gen.run_pipeline")
def run_pipeline(job_id: str, options: dict = None) -> None:  # noqa: D401
    """Celery task to execute the generation pipeline for a job."""
    import os
    import sys
    from pathlib import Path

    logger.info(f"[celery] Task starting - Working directory: {os.getcwd()}")
    logger.info(f"[celery] Job ID: {job_id}")

    # Debug database path
    from applications.code_gen.database import _db_path

    logger.info(f"[celery] Database path: {_db_path}")
    logger.info(f"[celery] Database exists: {_db_path.exists()}")

    job = get_job_data(job_id)
    logger.info(f"[celery] Retrieved job data: {job}")
    if not job:
        logger.error("Job %s not found in DB", job_id)
        return

    out_dir = Path(config.job_output_dir) / job_id
    out_dir.mkdir(parents=True, exist_ok=True)
    state = {
        "request": job["request_text"],
        "output_dir": out_dir,
        "job_id": job_id,
        "options": options or {},
    }

    try:
        logger.info("[celery] Running pipeline for %s", job_id)
        update_job(job_id, status="in_progress", phase="parse_input", progress=0.05)

        # Publish initial progress update via WebSocket
        publish_progress_update(
            job_id,
            {
                "status": "in_progress",
                "phase": "parse_input",
                "progress": 0.05,
                "message": "Starting pipeline execution",
            },
        )

        pipeline = build_pipeline([])

        # Handle async pipeline
        import asyncio

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(pipeline.invoke(state))
        finally:
            loop.close()

        update_job(
            job_id,
            status="completed",
            phase="done",
            progress=1.0,
            artifacts_path=str(out_dir / "artifacts.zip"),
        )

        # Publish completion update via WebSocket
        publish_progress_update(
            job_id,
            {
                "status": "completed",
                "phase": "done",
                "progress": 1.0,
                "message": "Pipeline execution completed successfully",
                "artifacts_path": str(out_dir / "artifacts.zip"),
                "artifacts_ready": True,
            },
        )

    except Exception as exc:  # noqa: BLE001
        logger.error("Pipeline failed for %s: %s", job_id, exc)
        traceback.print_exc()
        update_job(job_id, status="failed", error=str(exc))

        # Publish failure update via WebSocket
        publish_progress_update(
            job_id,
            {
                "status": "failed",
                "phase": "error",
                "progress": 0.0,
                "message": f"Pipeline execution failed: {exc}",
                "error": str(exc),
            },
        )
