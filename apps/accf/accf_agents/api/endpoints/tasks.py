"""
Task execution endpoints for the ACCF Research Agent.

This module provides endpoints for executing tasks and workflows.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
import uuid

from ...core.orchestrator import AgentOrchestrator
from ...agents import Task
from ...utils.validation import validate_task
from ..app import get_orchestrator

router = APIRouter()


@router.post("/execute")
async def execute_task(
    task_data: Dict[str, Any],
    orchestrator: AgentOrchestrator = Depends(get_orchestrator),
) -> Dict[str, Any]:
    """Execute a single task."""

    try:
        # Create task from request data
        task = Task(
            id=task_data.get("id", str(uuid.uuid4())),
            type=task_data["type"],
            parameters=task_data.get("parameters", {}),
            priority=task_data.get("priority", 1),
            timeout=task_data.get("timeout"),
        )

        # Validate task
        validation_errors = validate_task(task)
        if validation_errors:
            raise HTTPException(
                status_code=400,
                detail=f"Task validation failed: {', '.join(validation_errors)}",
            )

        # Execute task
        result = await orchestrator.execute_workflow(task)

        return {
            "task_id": result.task_id,
            "status": result.status,
            "data": result.data,
            "error_message": result.error_message,
            "execution_time": result.execution_time,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Task execution failed: {str(e)}")


@router.post("/execute-batch")
async def execute_batch_tasks(
    tasks_data: List[Dict[str, Any]],
    orchestrator: AgentOrchestrator = Depends(get_orchestrator),
) -> Dict[str, Any]:
    """Execute multiple tasks in parallel."""

    try:
        # Create tasks from request data
        tasks = []
        for task_data in tasks_data:
            task = Task(
                id=task_data.get("id", str(uuid.uuid4())),
                type=task_data["type"],
                parameters=task_data.get("parameters", {}),
                priority=task_data.get("priority", 1),
                timeout=task_data.get("timeout"),
            )

            # Validate task
            validation_errors = validate_task(task)
            if validation_errors:
                raise HTTPException(
                    status_code=400,
                    detail=f"Task validation failed for {task.id}: {', '.join(validation_errors)}",
                )

            tasks.append(task)

        # Execute tasks in parallel
        results = await orchestrator.execute_parallel_workflow(tasks)

        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append(
                {
                    "task_id": result.task_id,
                    "status": result.status,
                    "data": result.data,
                    "error_message": result.error_message,
                    "execution_time": result.execution_time,
                }
            )

        return {"total_tasks": len(tasks), "results": formatted_results}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Batch task execution failed: {str(e)}"
        )


@router.get("/status/{task_id}")
async def get_task_status(
    task_id: str, orchestrator: AgentOrchestrator = Depends(get_orchestrator)
) -> Dict[str, Any]:
    """Get the status of a specific task."""

    # This would typically query a task store/database
    # For now, return a placeholder response
    return {
        "task_id": task_id,
        "status": "unknown",
        "message": "Task status tracking not implemented yet",
    }
