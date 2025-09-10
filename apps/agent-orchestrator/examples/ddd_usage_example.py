#!/usr/bin/env python3
"""
Example usage of DDD-based domain models.

Demonstrates how to use the behavior-rich domain entities and aggregates.
"""

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.domain import (  # noqa: E402
    AgentTask,
    RetryPolicy,
    TaskAggregate,
    TaskPriority,
    TaskResult,
    ValidationResult,
)


async def example_executor(task: AgentTask) -> str:
    """Example task executor function"""
    print(f"Executing task: {task.task_id} - {task.prompt}")

    # Simulate some work
    await asyncio.sleep(0.5)

    # Simulate occasional failures for retry demonstration
    import random

    if random.random() < 0.2:
        raise ConnectionError("Simulated connection error")

    return f"Result for task {task.task_id}"


async def failing_executor(task: AgentTask) -> str:
    """Example executor that always fails"""
    raise ValueError("This task always fails")


async def main():
    """Demonstrate DDD domain model usage"""

    print("=" * 60)
    print("DDD Domain Models Example")
    print("=" * 60)

    # 1. Create and validate a single task
    print("\n1. Single Task with Validation")
    print("-" * 40)

    task1 = AgentTask(
        task_id="task-001",
        task_type="analysis",
        prompt="Analyze system performance metrics",
        priority=TaskPriority.high(deadline=datetime.utcnow() + timedelta(hours=2)),
        retry_policy=RetryPolicy(max_attempts=3, initial_delay=1.0),
    )

    # Validate task
    validation = task1.validate()
    print(f"Task validation: {validation.to_dict()}")

    # Execute task
    task1.set_executor(example_executor)
    result = await task1.execute()
    print(f"Task result: {result.to_dict()}")

    # 2. Task with retry mechanism
    print("\n2. Task with Retry Policy")
    print("-" * 40)

    task2 = AgentTask(
        task_id="task-002",
        task_type="data_processing",
        prompt="Process large dataset with retry on failure",
        retry_policy=RetryPolicy(
            max_attempts=3,
            initial_delay=0.5,
            exponential_base=2.0,
            retryable_errors=["ConnectionError", "TimeoutError"],
        ),
    )

    task2.set_executor(example_executor)

    # Add event handlers
    async def on_retry(task):
        print(f"Task {task.task_id} is being retried (attempt {task._retry_count + 1})")

    task2.add_event_handler("task_retrying", on_retry)

    # Execute with potential retry
    result = await task2.execute()
    print(f"Task result after retries: {result.to_dict()}")

    # 3. Task Aggregate with Dependencies
    print("\n3. Task Aggregate with Dependencies")
    print("-" * 40)

    aggregate = TaskAggregate(
        aggregate_id="workflow-001",
        name="Data Processing Pipeline",
        max_parallel_tasks=3,
        timeout=30.0,
    )

    # Create tasks for the pipeline
    extract_task = AgentTask(
        task_id="extract",
        task_type="data_extraction",
        prompt="Extract data from source systems",
        priority=TaskPriority.high(),
    )

    transform_task1 = AgentTask(
        task_id="transform1",
        task_type="data_transformation",
        prompt="Clean and normalize data",
        priority=TaskPriority.normal(),
    )

    transform_task2 = AgentTask(
        task_id="transform2",
        task_type="data_transformation",
        prompt="Apply business rules and calculations",
        priority=TaskPriority.normal(),
    )

    load_task = AgentTask(
        task_id="load",
        task_type="data_loading",
        prompt="Load processed data to target system",
        priority=TaskPriority.high(),
    )

    # Add tasks to aggregate with dependencies
    print("Adding tasks to aggregate...")

    # Extract has no dependencies
    validation = aggregate.add_task(extract_task, executor=example_executor)
    print(f"Added extract task: {validation.is_valid}")

    # Transform tasks depend on extract
    validation = aggregate.add_task(
        transform_task1, executor=example_executor, dependencies=["extract"]
    )
    print(f"Added transform1 task: {validation.is_valid}")

    validation = aggregate.add_task(
        transform_task2, executor=example_executor, dependencies=["extract"]
    )
    print(f"Added transform2 task: {validation.is_valid}")

    # Load depends on both transform tasks
    validation = aggregate.add_task(
        load_task, executor=example_executor, dependencies=["transform1", "transform2"]
    )
    print(f"Added load task: {validation.is_valid}")

    # Validate aggregate
    print("\nValidating aggregate...")
    validation = aggregate.validate()
    print(f"Aggregate validation: {validation.to_dict()}")

    # Execute aggregate
    print("\nExecuting aggregate pipeline...")
    results = await aggregate.execute()

    # Display results
    print("\nAggregate Execution Results:")
    for task_id, result in results.items():
        status = "✓" if result.is_success() else "✗"
        print(f"  {status} {task_id}: {result.status.value}")

    # Get aggregate metrics
    metrics = aggregate.get_metrics()
    print("\nAggregate Metrics:")
    print(f"  Total tasks: {metrics['total_tasks']}")
    print(f"  Completed: {metrics['completed_tasks']}")
    print(f"  Failed: {metrics['failed_tasks']}")
    print(f"  Success rate: {metrics['success_rate']:.1%}")
    if "duration" in metrics:
        print(f"  Duration: {metrics['duration']:.2f}s")

    # 4. Using TaskResult factory methods
    print("\n4. TaskResult Value Object Examples")
    print("-" * 40)

    # Success result
    success_result = TaskResult.success(
        data={"processed_records": 1000},
        execution_time=5.2,
        metadata={"source": "database"},
    )
    print(f"Success result: {success_result.to_dict()}")

    # Failure result
    failure_result = TaskResult.failure(
        error="Database connection failed", error_type="ConnectionError", retry_count=2
    )
    print(f"Failure result: {failure_result.to_dict()}")
    print(f"Is retryable: {failure_result.is_retryable()}")

    # Timeout result
    timeout_result = TaskResult.timeout(execution_time=30.0, retry_count=1)
    print(f"Timeout result: {timeout_result.to_dict()}")

    # 5. Custom validation rules
    print("\n5. Custom Validation Rules")
    print("-" * 40)

    def validate_prompt_length(task: AgentTask) -> ValidationResult:
        """Custom validator for prompt length"""
        if len(task.prompt) < 10:
            return ValidationResult.invalid(
                errors=["Prompt must be at least 10 characters"]
            )
        if len(task.prompt) > 1000:
            return ValidationResult.valid(
                warnings=["Prompt is very long (>1000 characters)"]
            )
        return ValidationResult.valid()

    task_with_validation = AgentTask(
        task_id="task-003",
        task_type="validation_demo",
        prompt="Short",  # Will fail validation
        validation_rules=[validate_prompt_length],
    )

    validation = task_with_validation.validate()
    print(f"Custom validation result: {validation.to_dict()}")

    print("\n" + "=" * 60)
    print("Example completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
