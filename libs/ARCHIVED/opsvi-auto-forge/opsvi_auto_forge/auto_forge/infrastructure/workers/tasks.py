"""Celery tasks for the autonomous software factory."""

import random
import time
import uuid
from typing import Any, Dict, Optional

from celery.utils.log import get_task_logger
from opsvi_auto_forge.infrastructure.workers.celery_app import app

logger = get_task_logger(__name__)

# ============================================================================
# DEFAULT QUEUE TASKS
# ============================================================================


@app.task(
    bind=True,
    name="workers.tasks.default.process_data",
    queue="default",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
    default_retry_delay=1,
)
def process_data(
    self,
    data: Dict[str, Any],
    project_id: Optional[str] = None,
    run_id: Optional[str] = None,
    node_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Process data in the default queue with idempotent task ID."""

    # Generate idempotent task ID if not provided
    task_id = getattr(self.request, "idempotency_key", None)
    if not task_id:
        task_id = f"process_data_{project_id}_{run_id}_{node_id}_{uuid.uuid4().hex[:8]}"
        self.request.idempotency_key = task_id

    logger.info(
        f"Processing data in default queue - Task ID: {task_id}",
        extra={
            "task_id": task_id,
            "queue": "default",
            "project_id": project_id,
            "run_id": run_id,
            "node_id": node_id,
        },
    )

    # Simulate processing
    time.sleep(random.uniform(0.1, 0.5))

    # Simulate occasional failures for retry testing
    if random.random() < 0.1:  # 10% failure rate
        raise Exception("Simulated processing failure")

    return {
        "task_id": task_id,
        "status": "completed",
        "data_processed": len(data),
        "queue": "default",
        "project_id": project_id,
        "run_id": run_id,
        "node_id": node_id,
    }


@app.task(
    bind=True,
    name="workers.tasks.default.validate_input",
    queue="default",
    autoretry_for=(ValueError,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=2,
    default_retry_delay=1,
)
def validate_input(
    self,
    input_data: Dict[str, Any],
    project_id: Optional[str] = None,
    run_id: Optional[str] = None,
    node_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Validate input data in the default queue."""

    task_id = f"validate_input_{project_id}_{run_id}_{node_id}_{uuid.uuid4().hex[:8]}"

    logger.info(
        f"Validating input in default queue - Task ID: {task_id}",
        extra={
            "task_id": task_id,
            "queue": "default",
            "project_id": project_id,
            "run_id": run_id,
            "node_id": node_id,
        },
    )

    # Simulate validation
    time.sleep(random.uniform(0.05, 0.2))

    # Simulate validation failure
    if not input_data.get("required_field"):
        raise ValueError("Missing required field")

    return {
        "task_id": task_id,
        "status": "validated",
        "valid": True,
        "queue": "default",
        "project_id": project_id,
        "run_id": run_id,
        "node_id": node_id,
    }


# ============================================================================
# IO QUEUE TASKS
# ============================================================================


@app.task(
    bind=True,
    name="workers.tasks.io.file_operation",
    queue="io",
    autoretry_for=(IOError,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
    default_retry_delay=2,
)
def file_operation(
    self,
    file_path: str,
    operation: str,
    project_id: Optional[str] = None,
    run_id: Optional[str] = None,
    node_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Perform file operations in the IO queue."""

    task_id = (
        f"file_op_{operation}_{project_id}_{run_id}_{node_id}_{uuid.uuid4().hex[:8]}"
    )

    logger.info(
        f"Performing file operation {operation} in IO queue - Task ID: {task_id}",
        extra={
            "task_id": task_id,
            "queue": "io",
            "project_id": project_id,
            "run_id": run_id,
            "node_id": node_id,
            "file_path": file_path,
            "operation": operation,
        },
    )

    # Simulate file operation
    time.sleep(random.uniform(0.5, 2.0))

    # Simulate IO failure
    if random.random() < 0.05:  # 5% failure rate
        raise IOError(f"Simulated IO error for {operation}")

    return {
        "task_id": task_id,
        "status": "completed",
        "operation": operation,
        "file_path": file_path,
        "queue": "io",
        "project_id": project_id,
        "run_id": run_id,
        "node_id": node_id,
    }


@app.task(
    bind=True,
    name="workers.tasks.io.database_query",
    queue="io",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
    default_retry_delay=1,
)
def database_query(
    self,
    query: str,
    project_id: Optional[str] = None,
    run_id: Optional[str] = None,
    node_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Execute database queries in the IO queue."""

    task_id = f"db_query_{project_id}_{run_id}_{node_id}_{uuid.uuid4().hex[:8]}"

    logger.info(
        f"Executing database query in IO queue - Task ID: {task_id}",
        extra={
            "task_id": task_id,
            "queue": "io",
            "project_id": project_id,
            "run_id": run_id,
            "node_id": node_id,
            "query": query[:100] + "..." if len(query) > 100 else query,
        },
    )

    # Simulate database query
    time.sleep(random.uniform(0.2, 1.5))

    # Simulate database error
    if random.random() < 0.03:  # 3% failure rate
        raise Exception("Simulated database connection error")

    return {
        "task_id": task_id,
        "status": "completed",
        "query_executed": True,
        "result_count": random.randint(1, 100),
        "queue": "io",
        "project_id": project_id,
        "run_id": run_id,
        "node_id": node_id,
    }


# ============================================================================
# HEAVY QUEUE TASKS
# ============================================================================


@app.task(
    bind=True,
    name="workers.tasks.heavy.complex_calculation",
    queue="heavy",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=2,
    default_retry_delay=5,
)
def complex_calculation(
    self,
    data: Dict[str, Any],
    project_id: Optional[str] = None,
    run_id: Optional[str] = None,
    node_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Perform complex calculations in the heavy queue."""

    task_id = f"calc_{project_id}_{run_id}_{node_id}_{uuid.uuid4().hex[:8]}"

    logger.info(
        f"Performing complex calculation in heavy queue - Task ID: {task_id}",
        extra={
            "task_id": task_id,
            "queue": "heavy",
            "project_id": project_id,
            "run_id": run_id,
            "node_id": node_id,
        },
    )

    # Simulate heavy computation
    time.sleep(random.uniform(3.0, 8.0))

    # Simulate computation failure
    if random.random() < 0.02:  # 2% failure rate
        raise Exception("Simulated computation error")

    return {
        "task_id": task_id,
        "status": "completed",
        "calculation_result": random.uniform(0, 1000),
        "processing_time": time.time(),
        "queue": "heavy",
        "project_id": project_id,
        "run_id": run_id,
        "node_id": node_id,
    }


@app.task(
    bind=True,
    name="workers.tasks.heavy.machine_learning",
    queue="heavy",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=2,
    default_retry_delay=10,
)
def machine_learning(
    self,
    model_params: Dict[str, Any],
    project_id: Optional[str] = None,
    run_id: Optional[str] = None,
    node_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Execute machine learning tasks in the heavy queue."""

    task_id = f"ml_{project_id}_{run_id}_{node_id}_{uuid.uuid4().hex[:8]}"

    logger.info(
        f"Executing machine learning task in heavy queue - Task ID: {task_id}",
        extra={
            "task_id": task_id,
            "queue": "heavy",
            "project_id": project_id,
            "run_id": run_id,
            "node_id": node_id,
        },
    )

    # Simulate ML training
    time.sleep(random.uniform(5.0, 15.0))

    # Simulate ML failure
    if random.random() < 0.01:  # 1% failure rate
        raise Exception("Simulated ML training error")

    return {
        "task_id": task_id,
        "status": "completed",
        "model_accuracy": random.uniform(0.8, 0.99),
        "training_time": time.time(),
        "queue": "heavy",
        "project_id": project_id,
        "run_id": run_id,
        "node_id": node_id,
    }


# ============================================================================
# TEST QUEUE TASKS
# ============================================================================


@app.task(
    bind=True,
    name="workers.tasks.test.unit_test",
    queue="test",
    autoretry_for=(AssertionError,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=2,
    default_retry_delay=1,
)
def unit_test(
    self,
    test_name: str,
    project_id: Optional[str] = None,
    run_id: Optional[str] = None,
    node_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Run unit tests in the test queue."""

    task_id = (
        f"unit_test_{test_name}_{project_id}_{run_id}_{node_id}_{uuid.uuid4().hex[:8]}"
    )

    logger.info(
        f"Running unit test {test_name} in test queue - Task ID: {task_id}",
        extra={
            "task_id": task_id,
            "queue": "test",
            "project_id": project_id,
            "run_id": run_id,
            "node_id": node_id,
            "test_name": test_name,
        },
    )

    # Simulate test execution
    time.sleep(random.uniform(0.1, 1.0))

    # Simulate test failure
    if random.random() < 0.15:  # 15% failure rate for testing
        raise AssertionError(f"Unit test {test_name} failed")

    return {
        "task_id": task_id,
        "status": "passed",
        "test_name": test_name,
        "execution_time": time.time(),
        "queue": "test",
        "project_id": project_id,
        "run_id": run_id,
        "node_id": node_id,
    }


@app.task(
    bind=True,
    name="workers.tasks.test.integration_test",
    queue="test",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=2,
    default_retry_delay=2,
)
def integration_test(
    self,
    test_suite: str,
    project_id: Optional[str] = None,
    run_id: Optional[str] = None,
    node_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Run integration tests in the test queue."""

    task_id = f"integration_test_{test_suite}_{project_id}_{run_id}_{node_id}_{uuid.uuid4().hex[:8]}"

    logger.info(
        f"Running integration test suite {test_suite} in test queue - Task ID: {task_id}",
        extra={
            "task_id": task_id,
            "queue": "test",
            "project_id": project_id,
            "run_id": run_id,
            "node_id": node_id,
            "test_suite": test_suite,
        },
    )

    # Simulate integration test execution
    time.sleep(random.uniform(1.0, 3.0))

    # Simulate integration test failure
    if random.random() < 0.08:  # 8% failure rate
        raise Exception(f"Integration test suite {test_suite} failed")

    return {
        "task_id": task_id,
        "status": "passed",
        "test_suite": test_suite,
        "tests_run": random.randint(10, 50),
        "execution_time": time.time(),
        "queue": "test",
        "project_id": project_id,
        "run_id": run_id,
        "node_id": node_id,
    }


# ============================================================================
# UTILITY TASKS
# ============================================================================


@app.task(
    bind=True,
    name="workers.tasks.utility.cleanup",
    queue="default",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=2,
    default_retry_delay=1,
)
def cleanup(
    self,
    cleanup_type: str,
    project_id: Optional[str] = None,
    run_id: Optional[str] = None,
    node_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Cleanup utility task."""

    task_id = (
        f"cleanup_{cleanup_type}_{project_id}_{run_id}_{node_id}_{uuid.uuid4().hex[:8]}"
    )

    logger.info(
        f"Performing cleanup {cleanup_type} - Task ID: {task_id}",
        extra={
            "task_id": task_id,
            "queue": "default",
            "project_id": project_id,
            "run_id": run_id,
            "node_id": node_id,
            "cleanup_type": cleanup_type,
        },
    )

    # Simulate cleanup
    time.sleep(random.uniform(0.1, 0.5))

    return {
        "task_id": task_id,
        "status": "completed",
        "cleanup_type": cleanup_type,
        "queue": "default",
        "project_id": project_id,
        "run_id": run_id,
        "node_id": node_id,
    }


# ============================================================================
# TASK REGISTRY
# ============================================================================

# Export all tasks
__all__ = [
    # Default queue tasks
    "process_data",
    "validate_input",
    # IO queue tasks
    "file_operation",
    "database_query",
    # Heavy queue tasks
    "complex_calculation",
    "machine_learning",
    # Test queue tasks
    "unit_test",
    "integration_test",
    # Utility tasks
    "cleanup",
]
