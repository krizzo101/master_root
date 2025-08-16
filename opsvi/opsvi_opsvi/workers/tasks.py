"""Celery tasks for the software factory."""

import logging
import time
from datetime import datetime
from typing import Any
from uuid import uuid4

from celery import current_task

from ..memory.graph.neo4j_client import get_neo4j_client
from ..orchestrator.registry import registry
from ..orchestrator.task_models import Metrics, Result, TaskRecord, TaskStatus

logger = logging.getLogger(__name__)


def _create_task_record(
    task_name: str,
    task_type: str,
    project_id: str,
    run_id: str,
    input_data: dict[str, Any],
    agent_path: str,
    agent_config: dict[str, Any],
) -> TaskRecord:
    """Create a task record for tracking."""
    return TaskRecord(
        id=str(uuid4()),
        name=task_name,
        task_type=task_type,
        status=TaskStatus.PENDING,
        project_id=project_id,
        run_id=run_id,
        input_data=input_data,
        agent_path=agent_path,
        agent_config=agent_config,
        created_at=datetime.utcnow(),
    )


def _log_task_start(task_record: TaskRecord) -> None:
    """Log task start to Neo4j."""
    try:
        neo4j = get_neo4j_client()

        # Create task node
        task_data = task_record.dict()
        task_data["started_at"] = datetime.utcnow().isoformat()
        task_data["status"] = TaskStatus.RUNNING.value

        neo4j.create_task(task_data)

        # Link to project and run
        neo4j.link_task_to_project(task_record.id, task_record.project_id)
        neo4j.link_task_to_run(task_record.id, task_record.run_id)

        # Link agent
        agent_name = task_record.agent_path.split(".")[-1]
        neo4j.link_agent_performs_task(agent_name, task_record.id)

        logger.info(f"Task {task_record.name} started: {task_record.id}")

    except Exception as e:
        logger.error(f"Failed to log task start: {e}")


def _log_task_completion(
    task_record: TaskRecord,
    result: Any,
    success: bool,
    error: str | None = None,
    metrics: Metrics | None = None,
) -> None:
    """Log task completion to Neo4j."""
    try:
        neo4j = get_neo4j_client()

        # Update task status
        task_data = {
            "task_id": task_record.id,
            "status": TaskStatus.SUCCESS.value if success else TaskStatus.FAILED.value,
            "output_data": result if success else None,
            "error_message": error if not success else None,
            "completed_at": datetime.utcnow().isoformat(),
            "tokens_used": metrics.tokens_used if metrics else 0,
            "latency_ms": metrics.latency_ms if metrics else 0,
            "cost_usd": metrics.cost_usd if metrics else 0.0,
            "retry_count": (
                current_task.request.retries
                if hasattr(current_task.request, "retries")
                else 0
            ),
        }

        # Create result node
        result_record = Result(
            id=str(uuid4()),
            task_id=task_record.id,
            success=success,
            data=result if success else {},
            error=error if not success else None,
            metrics=metrics or Metrics(),
            created_at=datetime.utcnow(),
            execution_time_ms=metrics.latency_ms if metrics else 0,
        )

        neo4j.create_result(result_record.dict())
        neo4j.link_task_result(task_record.id, result_record.id)

        logger.info(f"Task {task_record.name} completed: {task_record.id}")

    except Exception as e:
        logger.error(f"Failed to log task completion: {e}")


def _execute_agent_with_metrics(
    agent_name: str, input_data: dict[str, Any], agent_config: dict[str, Any]
) -> tuple[Any, Metrics]:
    """Execute an agent and collect metrics."""
    start_time = time.time()

    try:
        # Execute the agent
        result = registry.execute_agent(agent_name, input_data, agent_config)

        # Calculate metrics
        execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds

        # Estimate tokens (this is a simplified estimation)
        estimated_tokens = len(str(input_data)) // 4 + len(str(result)) // 4

        # Estimate cost (simplified - would need actual API costs)
        estimated_cost = estimated_tokens * 0.000002  # Rough estimate

        metrics = Metrics(
            tokens_used=estimated_tokens,
            latency_ms=int(execution_time),
            cost_usd=estimated_cost,
            memory_mb=0.0,  # Would need actual measurement
            cpu_percent=0.0,  # Would need actual measurement
            mocked=False,
            retry_count=0,
        )

        return result, metrics

    except Exception as e:
        execution_time = (time.time() - start_time) * 1000
        metrics = Metrics(
            tokens_used=0,
            latency_ms=int(execution_time),
            cost_usd=0.0,
            memory_mb=0.0,
            cpu_percent=0.0,
            mocked=False,
            retry_count=(
                current_task.request.retries
                if hasattr(current_task.request, "retries")
                else 0
            ),
        )
        raise e


@current_task.task(bind=True)
def execute_plan_task(self, task_data: dict[str, Any]) -> dict[str, Any]:
    """Execute a planning task."""
    task_record = _create_task_record(
        task_name=task_data.get("name", "plan_task"),
        task_type="plan",
        project_id=task_data["project_id"],
        run_id=task_data["run_id"],
        input_data=task_data.get("input_data", {}),
        agent_path=task_data.get("agent_path", "plan_agent"),
        agent_config=task_data.get("agent_config", {}),
    )

    _log_task_start(task_record)

    try:
        result, metrics = _execute_agent_with_metrics(
            task_record.agent_path, task_record.input_data, task_record.agent_config
        )

        _log_task_completion(task_record, result, True, metrics=metrics)

        return {
            "task_id": task_record.id,
            "success": True,
            "result": result,
            "metrics": metrics.dict(),
        }

    except Exception as e:
        logger.error(f"Plan task failed: {e}")
        _log_task_completion(task_record, None, False, str(e))

        # Retry logic is handled by Celery configuration
        raise


@current_task.task(bind=True)
def execute_spec_task(self, task_data: dict[str, Any]) -> dict[str, Any]:
    """Execute a specification task."""
    task_record = _create_task_record(
        task_name=task_data.get("name", "spec_task"),
        task_type="spec",
        project_id=task_data["project_id"],
        run_id=task_data["run_id"],
        input_data=task_data.get("input_data", {}),
        agent_path=task_data.get("agent_path", "spec_agent"),
        agent_config=task_data.get("agent_config", {}),
    )

    _log_task_start(task_record)

    try:
        result, metrics = _execute_agent_with_metrics(
            task_record.agent_path, task_record.input_data, task_record.agent_config
        )

        _log_task_completion(task_record, result, True, metrics=metrics)

        return {
            "task_id": task_record.id,
            "success": True,
            "result": result,
            "metrics": metrics.dict(),
        }

    except Exception as e:
        logger.error(f"Spec task failed: {e}")
        _log_task_completion(task_record, None, False, str(e))
        raise


@current_task.task(bind=True)
def execute_research_task(self, task_data: dict[str, Any]) -> dict[str, Any]:
    """Execute a research task."""
    task_record = _create_task_record(
        task_name=task_data.get("name", "research_task"),
        task_type="research",
        project_id=task_data["project_id"],
        run_id=task_data["run_id"],
        input_data=task_data.get("input_data", {}),
        agent_path=task_data.get("agent_path", "research_agent"),
        agent_config=task_data.get("agent_config", {}),
    )

    _log_task_start(task_record)

    try:
        result, metrics = _execute_agent_with_metrics(
            task_record.agent_path, task_record.input_data, task_record.agent_config
        )

        _log_task_completion(task_record, result, True, metrics=metrics)

        return {
            "task_id": task_record.id,
            "success": True,
            "result": result,
            "metrics": metrics.dict(),
        }

    except Exception as e:
        logger.error(f"Research task failed: {e}")
        _log_task_completion(task_record, None, False, str(e))
        raise


@current_task.task(bind=True)
def execute_code_task(self, task_data: dict[str, Any]) -> dict[str, Any]:
    """Execute a code generation task."""
    task_record = _create_task_record(
        task_name=task_data.get("name", "code_task"),
        task_type="code",
        project_id=task_data["project_id"],
        run_id=task_data["run_id"],
        input_data=task_data.get("input_data", {}),
        agent_path=task_data.get("agent_path", "code_agent"),
        agent_config=task_data.get("agent_config", {}),
    )

    _log_task_start(task_record)

    try:
        result, metrics = _execute_agent_with_metrics(
            task_record.agent_path, task_record.input_data, task_record.agent_config
        )

        _log_task_completion(task_record, result, True, metrics=metrics)

        return {
            "task_id": task_record.id,
            "success": True,
            "result": result,
            "metrics": metrics.dict(),
        }

    except Exception as e:
        logger.error(f"Code task failed: {e}")
        _log_task_completion(task_record, None, False, str(e))
        raise


@current_task.task(bind=True)
def execute_test_task(self, task_data: dict[str, Any]) -> dict[str, Any]:
    """Execute a test generation task."""
    task_record = _create_task_record(
        task_name=task_data.get("name", "test_task"),
        task_type="test",
        project_id=task_data["project_id"],
        run_id=task_data["run_id"],
        input_data=task_data.get("input_data", {}),
        agent_path=task_data.get("agent_path", "test_agent"),
        agent_config=task_data.get("agent_config", {}),
    )

    _log_task_start(task_record)

    try:
        result, metrics = _execute_agent_with_metrics(
            task_record.agent_path, task_record.input_data, task_record.agent_config
        )

        _log_task_completion(task_record, result, True, metrics=metrics)

        return {
            "task_id": task_record.id,
            "success": True,
            "result": result,
            "metrics": metrics.dict(),
        }

    except Exception as e:
        logger.error(f"Test task failed: {e}")
        _log_task_completion(task_record, None, False, str(e))
        raise


@current_task.task(bind=True)
def execute_validate_task(self, task_data: dict[str, Any]) -> dict[str, Any]:
    """Execute a validation task."""
    task_record = _create_task_record(
        task_name=task_data.get("name", "validate_task"),
        task_type="validate",
        project_id=task_data["project_id"],
        run_id=task_data["run_id"],
        input_data=task_data.get("input_data", {}),
        agent_path=task_data.get("agent_path", "validate_agent"),
        agent_config=task_data.get("agent_config", {}),
    )

    _log_task_start(task_record)

    try:
        result, metrics = _execute_agent_with_metrics(
            task_record.agent_path, task_record.input_data, task_record.agent_config
        )

        _log_task_completion(task_record, result, True, metrics=metrics)

        return {
            "task_id": task_record.id,
            "success": True,
            "result": result,
            "metrics": metrics.dict(),
        }

    except Exception as e:
        logger.error(f"Validate task failed: {e}")
        _log_task_completion(task_record, None, False, str(e))
        raise


@current_task.task(bind=True)
def execute_document_task(self, task_data: dict[str, Any]) -> dict[str, Any]:
    """Execute a documentation task."""
    task_record = _create_task_record(
        task_name=task_data.get("name", "document_task"),
        task_type="document",
        project_id=task_data["project_id"],
        run_id=task_data["run_id"],
        input_data=task_data.get("input_data", {}),
        agent_path=task_data.get("agent_path", "doc_agent"),
        agent_config=task_data.get("agent_config", {}),
    )

    _log_task_start(task_record)

    try:
        result, metrics = _execute_agent_with_metrics(
            task_record.agent_path, task_record.input_data, task_record.agent_config
        )

        _log_task_completion(task_record, result, True, metrics=metrics)

        return {
            "task_id": task_record.id,
            "success": True,
            "result": result,
            "metrics": metrics.dict(),
        }

    except Exception as e:
        logger.error(f"Document task failed: {e}")
        _log_task_completion(task_record, None, False, str(e))
        raise


@current_task.task(bind=True)
def execute_critic_task(self, task_data: dict[str, Any]) -> dict[str, Any]:
    """Execute a critic evaluation task."""
    task_record = _create_task_record(
        task_name=task_data.get("name", "critic_task"),
        task_type="critic",
        project_id=task_data["project_id"],
        run_id=task_data["run_id"],
        input_data=task_data.get("input_data", {}),
        agent_path=task_data.get("agent_path", "critic_agent"),
        agent_config=task_data.get("agent_config", {}),
    )

    _log_task_start(task_record)

    try:
        result, metrics = _execute_agent_with_metrics(
            task_record.agent_path, task_record.input_data, task_record.agent_config
        )

        _log_task_completion(task_record, result, True, metrics=metrics)

        return {
            "task_id": task_record.id,
            "success": True,
            "result": result,
            "metrics": metrics.dict(),
        }

    except Exception as e:
        logger.error(f"Critic task failed: {e}")
        _log_task_completion(task_record, None, False, str(e))
        raise


@current_task.task
def cleanup_old_results() -> dict[str, Any]:
    """Clean up old task results."""
    try:
        # This would implement cleanup logic for old results
        # For now, just log the cleanup
        logger.info("Cleanup old results task executed")
        return {"success": True, "cleaned_count": 0}
    except Exception as e:
        logger.error(f"Cleanup task failed: {e}")
        return {"success": False, "error": str(e)}


@current_task.task
def health_check() -> dict[str, Any]:
    """Health check task."""
    try:
        # Check Neo4j connection
        neo4j = get_neo4j_client()
        neo4j._execute_query("RETURN 1", {})

        # Check agent registry
        agents = registry.list_agents()

        return {
            "success": True,
            "neo4j_connected": True,
            "agents_available": len(agents),
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }
