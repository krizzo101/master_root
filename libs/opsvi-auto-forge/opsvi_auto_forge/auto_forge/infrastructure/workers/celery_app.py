"""Celery application configuration for the autonomous software factory."""

import logging
import time
from celery import Celery
from celery.signals import (
    task_prerun,
    task_postrun,
    task_failure,
    worker_init,
    task_received,
    task_revoked,
)
from prometheus_client import Counter, Histogram, Gauge
from opsvi_auto_forge.config.settings import Settings
from opsvi_auto_forge.infrastructure.monitoring.logging_config import (
    get_logger,
    log_task_start,
    log_task_end,
    log_error,
    set_pipeline_context,
)

# Initialize settings
settings = Settings()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Prometheus metrics
TASKS_RUN = Counter(
    "celery_tasks_run_total", "Total number of tasks run", ["queue", "task_name"]
)
TASKS_FAILED = Counter(
    "celery_tasks_failed_total", "Total number of failed tasks", ["queue", "task_name"]
)
TASK_DURATION = Histogram(
    "celery_task_duration_seconds", "Task duration in seconds", ["queue", "task_name"]
)
ACTIVE_TASKS = Gauge(
    "celery_active_tasks", "Number of currently active tasks", ["queue"]
)

# Create Celery application
app = Celery(
    "software_factory",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "auto_forge.infrastructure.workers.tasks",
        "auto_forge.infrastructure.workers.agent_tasks",
    ],
)

# Celery configuration
app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Task routing
    task_routes={
        "auto_forge.infrastructure.workers.tasks.heavy.*": {"queue": "heavy"},
        "auto_forge.infrastructure.workers.tasks.io.*": {"queue": "io"},
        "auto_forge.infrastructure.workers.tasks.test.*": {"queue": "test"},
        "auto_forge.infrastructure.workers.agent_tasks.*": {"queue": "default"},
    },
    # Task execution
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_always_eager=False,
    # Retry configuration
    task_autoretry_for=(Exception,),
    task_autoretry_backoff=True,
    task_autoretry_jitter=True,
    task_autoretry_max_retries=3,
    # Result backend
    result_expires=3600,  # 1 hour
    # Worker configuration
    worker_max_tasks_per_child=1000,
    worker_max_memory_per_child=200000,  # 200MB
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
)

# Enhanced logging setup
structlog_logger = get_logger("celery.app")


@worker_init.connect
def worker_init_handler(sender=None, **kwargs):
    """Log worker initialization."""
    structlog_logger.info(
        "Celery worker initialized",
        worker_name=getattr(sender, "hostname", "unknown"),
        worker_pid=getattr(sender, "pid", "unknown"),
        worker_queues=(
            list(getattr(sender.app, "conf", {}).get("task_routes", {}).values())
            if hasattr(sender, "app")
            else []
        ),
        **kwargs,
    )


@task_received.connect
def task_received_handler(sender=None, request=None, **kwargs):
    """Log when a task is received by a worker."""
    structlog_logger.info(
        "Task received by worker",
        task_id=request.id,
        task_name=request.name,
        worker_name=getattr(sender, "hostname", "unknown"),
        queue=request.delivery_info.get("routing_key", "unknown"),
        **kwargs,
    )


@task_prerun.connect
def task_prerun_handler(
    sender=None, task_id=None, task=None, args=None, kwargs=None, **kwargs_extra
):
    """Log before task execution starts."""
    start_time = time.time()

    # Extract pipeline context from kwargs if available
    pipeline_context = kwargs.get("pipeline_context", {})
    phase = pipeline_context.get("phase", "unknown")
    agent_type = pipeline_context.get("agent_type", "unknown")

    # Set pipeline context for logging
    set_pipeline_context(phase, str(task_id), agent_type)

    # Log task start
    log_task_start(
        task_id=task_id,
        task_type=task.name,
        agent_type=agent_type,
        phase=phase,
        args=args,
        kwargs=kwargs,
        worker_name=getattr(sender, "hostname", "unknown"),
    )

    # Update metrics
    ACTIVE_TASKS.labels(queue=kwargs_extra.get("queue", "default")).inc()

    structlog_logger.debug(
        "Task execution starting",
        task_id=task_id,
        task_name=task.name,
        phase=phase,
        agent_type=agent_type,
        worker_name=getattr(sender, "hostname", "unknown"),
        **kwargs_extra,
    )


@task_postrun.connect
def task_postrun_handler(
    sender=None,
    task_id=None,
    task=None,
    args=None,
    kwargs=None,
    retval=None,
    state=None,
    **kwargs_extra,
):
    """Log after task execution completes."""
    end_time = time.time()
    start_time = kwargs_extra.get("start_time", end_time)
    duration = end_time - start_time

    # Extract pipeline context
    pipeline_context = kwargs.get("pipeline_context", {})
    phase = pipeline_context.get("phase", "unknown")
    agent_type = pipeline_context.get("agent_type", "unknown")

    # Determine success
    success = state == "SUCCESS"

    # Log task completion
    log_task_end(
        task_id=task_id,
        task_type=task.name,
        success=success,
        agent_type=agent_type,
        phase=phase,
        duration_ms=duration * 1000,
        state=state,
        result_size=len(str(retval)) if retval else 0,
        worker_name="unknown",  # sender doesn't have hostname in postrun
    )

    # Update metrics
    queue = kwargs_extra.get("queue", "default")
    TASKS_RUN.labels(queue=queue, task_name=task.name).inc()
    TASK_DURATION.labels(queue=queue, task_name=task.name).observe(duration)
    ACTIVE_TASKS.labels(queue=queue).dec()

    if not success:
        TASKS_FAILED.labels(queue=queue, task_name=task.name).inc()

    structlog_logger.info(
        f"Task execution {'completed' if success else 'failed'}",
        task_id=task_id,
        task_name=task.name,
        phase=phase,
        agent_type=agent_type,
        state=state,
        duration_ms=duration * 1000,
        worker_name="unknown",  # sender doesn't have hostname in postrun
        success=success,
    )


@task_failure.connect
def task_failure_handler(
    sender=None,
    task_id=None,
    exception=None,
    args=None,
    kwargs=None,
    traceback=None,
    einfo=None,
    **kwargs_extra,
):
    """Log when a task fails."""
    # Extract pipeline context
    pipeline_context = kwargs.get("pipeline_context", {})
    phase = pipeline_context.get("phase", "unknown")
    agent_type = pipeline_context.get("agent_type", "unknown")

    # Log error with full context
    log_error(
        f"Task execution failed: {exception}",
        error=exception,
        task_id=task_id,
        task_name=sender.name,
        phase=phase,
        agent_type=agent_type,
        args=args,
        kwargs=kwargs,
        traceback=traceback,
        **kwargs_extra,
    )

    structlog_logger.error(
        "Task execution failed",
        task_id=task_id,
        task_name=sender.name,
        phase=phase,
        agent_type=agent_type,
        exception=str(exception),
        exception_type=type(exception).__name__,
        traceback=traceback,
        **kwargs_extra,
    )


@task_revoked.connect
def task_revoked_handler(
    sender=None, request=None, terminated=None, signum=None, expired=None, **kwargs
):
    """Log when a task is revoked."""
    structlog_logger.warning(
        "Task revoked",
        task_id=request.id,
        task_name=request.name,
        terminated=terminated,
        signum=signum,
        expired=expired,
        **kwargs,
    )


# Test task with enhanced logging
@app.task(name="workers.celery_app.test_task")
def test_task():
    """Simple test task to verify task registration."""
    structlog_logger.info("Test task executed successfully")
    return {"status": "success", "message": "Test task executed"}


# Pipeline execution task with enhanced logging
@app.task(
    bind=True, name="auto_forge.infrastructure.workers.celery_app.execute_pipeline"
)
def execute_pipeline(
    self, run_id: str, project_id: str, pipeline_name: str = "software_factory_v1"
):
    """Execute a pipeline using the MetaOrchestrator."""
    import asyncio
    import logging

    logger = logging.getLogger(__name__)
    structlog_logger = get_logger("pipeline.execution")

    structlog_logger.info(
        "Pipeline execution started",
        run_id=run_id,
        project_id=project_id,
        pipeline_name=pipeline_name,
        task_id=self.request.id,
        worker_name=self.request.hostname,
    )

    try:
        # Import MetaOrchestrator
        from opsvi_auto_forge.application.orchestrator.meta_orchestrator import (
            MetaOrchestrator,
        )
        from opsvi_auto_forge.infrastructure.memory.graph.client import Neo4jClient

        structlog_logger.info(
            "Initializing Neo4j client", run_id=run_id, step="neo4j_init"
        )

        # Initialize Neo4j client
        neo4j_client = Neo4jClient()

        structlog_logger.info(
            "Initializing orchestrator", run_id=run_id, step="orchestrator_init"
        )

        # Initialize orchestrator
        orchestrator = MetaOrchestrator(neo4j_client)

        # Use a single event loop for all async operations
        async def run_pipeline():
            # Initialize the orchestrator (loads task registry)
            await orchestrator.initialize()

            structlog_logger.info(
                "Starting pipeline",
                run_id=run_id,
                project_id=project_id,
                pipeline_name=pipeline_name,
                step="pipeline_start",
            )

            # Start pipeline using MetaOrchestrator
            context = await orchestrator.start_pipeline(
                project_id=project_id,
                run_id=run_id,
                pipeline_name=pipeline_name,
            )

            structlog_logger.info(
                "Pipeline started successfully",
                run_id=run_id,
                dag_id=context.dag_id,
                step="pipeline_created",
            )

            structlog_logger.info(
                "Executing pipeline", run_id=run_id, step="pipeline_execute"
            )

            # Execute pipeline
            result = await orchestrator.execute_pipeline(context)
            return result

        # Run everything in a single event loop
        result = asyncio.run(run_pipeline())

        structlog_logger.info(
            "Pipeline execution completed",
            run_id=run_id,
            result_success=result.get("success", False),
            result_summary=(
                str(result)[:200] + "..." if len(str(result)) > 200 else str(result)
            ),
            step="pipeline_complete",
        )

        if result.get("success", False):
            structlog_logger.info(
                "Pipeline execution SUCCESS", run_id=run_id, success=True
            )
            return {
                "status": "success",
                "run_id": run_id,
                "result": result,
            }
        else:
            structlog_logger.error(
                "Pipeline execution FAILED",
                run_id=run_id,
                success=False,
                error=result.get("error", "Unknown error"),
            )
            return {
                "status": "failed",
                "run_id": run_id,
                "error": result.get("error", "Unknown error"),
                "result": result,
            }

    except Exception as e:
        structlog_logger.error(
            "Pipeline execution exception",
            run_id=run_id,
            exception=str(e),
            exception_type=type(e).__name__,
            exc_info=True,
        )

        logger.error(f"🔴 Pipeline execution FAILED for run {run_id}: {e}")
        return {
            "status": "failed",
            "run_id": run_id,
            "error": str(e),
        }


# Health check task
@app.task(bind=True, name="workers.tasks.health_check")
def health_check(self):
    """Health check task to verify Celery is working."""
    import time

    logger.info(f"Health check task {self.request.id} executed")
    return {
        "status": "healthy",
        "task_id": self.request.id,
        "timestamp": time.time(),
    }


# Test task
@app.task(bind=True, name="workers.tasks.test_task")
def test_task(self):
    """Test task to verify task registration."""
    import time

    logger.info(f"Test task {self.request.id} executed")
    return {
        "status": "success",
        "task_id": self.request.id,
        "timestamp": time.time(),
        "message": "Test task executed",
    }


# Export the Celery app
__all__ = ["app"]
