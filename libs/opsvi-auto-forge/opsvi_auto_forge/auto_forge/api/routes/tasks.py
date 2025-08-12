"""Task management routes for the autonomous software factory."""

import logging
from typing import Dict, Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Query
from prometheus_client import Counter, Histogram

from opsvi_auto_forge.config.models import (
    TaskRecord,
    Result,
    Critique,
    Artifact,
)
from opsvi_auto_forge.infrastructure.memory.graph.client import Neo4jClient

logger = logging.getLogger(__name__)

# Prometheus metrics
TASK_OPERATION_COUNT = Counter(
    "task_operation_total", "Total task operations", ["operation", "status"]
)
TASK_OPERATION_DURATION = Histogram(
    "task_operation_duration_seconds", "Task operation duration", ["operation"]
)

router = APIRouter()


async def get_neo4j_client() -> Neo4jClient:
    """Get Neo4j client instance."""
    client = Neo4jClient()
    await client.connect()
    return client


@router.get("/{task_id}", response_model=TaskRecord)
async def get_task(
    task_id: UUID, neo4j_client: Neo4jClient = Depends(get_neo4j_client)
) -> TaskRecord:
    """Get task by ID."""
    try:
        with TASK_OPERATION_DURATION.labels(operation="get").time():
            query = """
            MATCH (t:Task {id: $task_id})
            RETURN t
            """

            result = await neo4j_client.execute_query(query, {"task_id": str(task_id)})

            if not result:
                raise HTTPException(status_code=404, detail="Task not found")

            TASK_OPERATION_COUNT.labels(operation="get", status="success").inc()
            return TaskRecord(**result[0]["t"])

    except HTTPException:
        raise
    except Exception as e:
        TASK_OPERATION_COUNT.labels(operation="get", status="error").inc()
        logger.error(f"Failed to get task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get task: {e}")


@router.get("/", response_model=List[TaskRecord])
async def list_tasks(
    run_id: Optional[UUID] = Query(None),
    agent: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    neo4j_client: Neo4jClient = Depends(get_neo4j_client),
) -> List[TaskRecord]:
    """List tasks with pagination and filtering."""
    try:
        with TASK_OPERATION_DURATION.labels(operation="list").time():
            # Build query with filters
            query = """
            MATCH (t:Task)
            """
            parameters = {"limit": limit, "offset": offset}

            where_clauses = []

            if run_id:
                query += "-[:PART_OF]->(r:Run {id: $run_id})"
                parameters["run_id"] = str(run_id)

            if agent:
                where_clauses.append("t.agent = $agent")
                parameters["agent"] = agent

            if status:
                where_clauses.append("t.status = $status")
                parameters["status"] = status

            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)

            query += """
            RETURN t
            ORDER BY t.created_at DESC
            SKIP $offset
            LIMIT $limit
            """

            result = await neo4j_client.execute_query(query, parameters)
            tasks = [TaskRecord(**record["t"]) for record in result]

            TASK_OPERATION_COUNT.labels(operation="list", status="success").inc()
            return tasks

    except Exception as e:
        TASK_OPERATION_COUNT.labels(operation="list", status="error").inc()
        logger.error(f"Failed to list tasks: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list tasks: {e}")


@router.put("/{task_id}/status")
async def update_task_status(
    task_id: UUID,
    status: str,
    error: Optional[str] = None,
    score: Optional[float] = None,
    neo4j_client: Neo4jClient = Depends(get_neo4j_client),
) -> Dict[str, str]:
    """Update task status."""
    try:
        with TASK_OPERATION_DURATION.labels(operation="update_status").time():
            # Check if task exists
            existing_task = await get_task(task_id, neo4j_client)
            if not existing_task:
                raise HTTPException(status_code=404, detail="Task not found")

            # Update status
            updates = {}
            if error is not None:
                updates["error"] = error
            if score is not None:
                updates["score"] = score

            await neo4j_client.update_task_status(str(task_id), status, **updates)

            TASK_OPERATION_COUNT.labels(
                operation="update_status", status="success"
            ).inc()
            logger.info(f"Updated task {task_id} status to: {status}")

            return {"message": f"Task {task_id} status updated to {status}"}

    except HTTPException:
        raise
    except Exception as e:
        TASK_OPERATION_COUNT.labels(operation="update_status", status="error").inc()
        logger.error(f"Failed to update task {task_id} status: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to update task status: {e}"
        )


@router.get("/{task_id}/result")
async def get_task_result(
    task_id: UUID, neo4j_client: Neo4jClient = Depends(get_neo4j_client)
) -> Result:
    """Get result for a specific task."""
    try:
        with TASK_OPERATION_DURATION.labels(operation="get_result").time():
            query = """
            MATCH (t:Task {id: $task_id})-[:RESULTED_IN]->(r:Result)
            RETURN r
            """

            result = await neo4j_client.execute_query(query, {"task_id": str(task_id)})

            if not result:
                raise HTTPException(status_code=404, detail="Task result not found")

            TASK_OPERATION_COUNT.labels(operation="get_result", status="success").inc()
            return Result(**result[0]["r"])

    except HTTPException:
        raise
    except Exception as e:
        TASK_OPERATION_COUNT.labels(operation="get_result", status="error").inc()
        logger.error(f"Failed to get result for task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get task result: {e}")


@router.get("/{task_id}/critique")
async def get_task_critique(
    task_id: UUID, neo4j_client: Neo4jClient = Depends(get_neo4j_client)
) -> Critique:
    """Get critique for a specific task."""
    try:
        with TASK_OPERATION_DURATION.labels(operation="get_critique").time():
            query = """
            MATCH (t:Task {id: $task_id})<-[:EVALUATED_BY]-(c:Critique)
            RETURN c
            """

            result = await neo4j_client.execute_query(query, {"task_id": str(task_id)})

            if not result:
                raise HTTPException(status_code=404, detail="Task critique not found")

            TASK_OPERATION_COUNT.labels(
                operation="get_critique", status="success"
            ).inc()
            return Critique(**result[0]["c"])

    except HTTPException:
        raise
    except Exception as e:
        TASK_OPERATION_COUNT.labels(operation="get_critique", status="error").inc()
        logger.error(f"Failed to get critique for task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get task critique: {e}")


@router.get("/{task_id}/artifacts", response_model=List[Artifact])
async def get_task_artifacts(
    task_id: UUID,
    artifact_type: Optional[str] = Query(None),
    neo4j_client: Neo4jClient = Depends(get_neo4j_client),
) -> List[Artifact]:
    """Get artifacts produced by a specific task."""
    try:
        with TASK_OPERATION_DURATION.labels(operation="get_artifacts").time():
            # Build query with filters
            query = """
            MATCH (t:Task {id: $task_id})-[:GENERATES]->(a:Artifact)
            """
            parameters = {"task_id": str(task_id)}

            if artifact_type:
                query += " WHERE a.type = $artifact_type"
                parameters["artifact_type"] = artifact_type

            query += """
            RETURN a
            ORDER BY a.created_at ASC
            """

            result = await neo4j_client.execute_query(query, parameters)
            artifacts = [Artifact(**record["a"]) for record in result]

            TASK_OPERATION_COUNT.labels(
                operation="get_artifacts", status="success"
            ).inc()
            return artifacts

    except Exception as e:
        TASK_OPERATION_COUNT.labels(operation="get_artifacts", status="error").inc()
        logger.error(f"Failed to get artifacts for task {task_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get task artifacts: {e}"
        )


@router.get("/{task_id}/decisions")
async def get_task_decisions(
    task_id: UUID, neo4j_client: Neo4jClient = Depends(get_neo4j_client)
) -> List[Dict[str, Any]]:
    """Get decisions made for a specific task."""
    try:
        with TASK_OPERATION_DURATION.labels(operation="get_decisions").time():
            query = """
            MATCH (t:Task {id: $task_id})<-[:FOR_TASK]-(d:Decision)
            RETURN d
            ORDER BY d.created_at ASC
            """

            result = await neo4j_client.execute_query(query, {"task_id": str(task_id)})
            decisions = [record["d"] for record in result]

            TASK_OPERATION_COUNT.labels(
                operation="get_decisions", status="success"
            ).inc()
            return decisions

    except Exception as e:
        TASK_OPERATION_COUNT.labels(operation="get_decisions", status="error").inc()
        logger.error(f"Failed to get decisions for task {task_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get task decisions: {e}"
        )


@router.get("/{task_id}/summary")
async def get_task_summary(
    task_id: UUID, neo4j_client: Neo4jClient = Depends(get_neo4j_client)
) -> Dict[str, Any]:
    """Get comprehensive summary of a task."""
    try:
        with TASK_OPERATION_DURATION.labels(operation="get_summary").time():
            # Get task details
            task = await get_task(task_id, neo4j_client)

            # Get related data
            result = None
            critique = None
            artifacts = []
            decisions = []

            try:
                result = await get_task_result(task_id, neo4j_client)
            except HTTPException:
                pass  # Result not found

            try:
                critique = await get_task_critique(task_id, neo4j_client)
            except HTTPException:
                pass  # Critique not found

            try:
                artifacts = await get_task_artifacts(task_id, neo4j_client)
            except HTTPException:
                pass  # Artifacts not found

            try:
                decisions = await get_task_decisions(task_id, neo4j_client)
            except HTTPException:
                pass  # Decisions not found

            summary = {
                "task": task.model_dump(),
                "result": result.model_dump() if result else None,
                "critique": critique.model_dump() if critique else None,
                "artifacts": [artifact.model_dump() for artifact in artifacts],
                "decisions": decisions,
                "metrics": {
                    "total_artifacts": len(artifacts),
                    "artifact_types": list(
                        set(artifact.type for artifact in artifacts)
                    ),
                    "total_decisions": len(decisions),
                    "has_result": result is not None,
                    "has_critique": critique is not None,
                    "overall_score": result.score if result else None,
                    "critique_score": critique.score if critique else None,
                },
            }

            TASK_OPERATION_COUNT.labels(operation="get_summary", status="success").inc()
            return summary

    except Exception as e:
        TASK_OPERATION_COUNT.labels(operation="get_summary", status="error").inc()
        logger.error(f"Failed to get summary for task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get task summary: {e}")


@router.get("/agent/{agent}/performance")
async def get_agent_performance(
    agent: str,
    limit: int = Query(100, ge=1, le=1000),
    neo4j_client: Neo4jClient = Depends(get_neo4j_client),
) -> Dict[str, Any]:
    """Get performance metrics for a specific agent."""
    try:
        with TASK_OPERATION_DURATION.labels(operation="get_agent_performance").time():
            performance_data = await neo4j_client.get_agent_performance(agent, limit)

            if not performance_data:
                return {
                    "agent": agent,
                    "total_tasks": 0,
                    "average_score": 0.0,
                    "success_rate": 0.0,
                    "performance_data": [],
                }

            # Calculate metrics
            total_tasks = len(performance_data)
            successful_tasks = sum(
                1 for p in performance_data if p.get("result", {}).get("status") == "ok"
            )
            success_rate = successful_tasks / total_tasks if total_tasks > 0 else 0.0

            scores = [
                p.get("overall_score", 0.0)
                for p in performance_data
                if p.get("overall_score") is not None
            ]
            average_score = sum(scores) / len(scores) if scores else 0.0

            TASK_OPERATION_COUNT.labels(
                operation="get_agent_performance", status="success"
            ).inc()

            return {
                "agent": agent,
                "total_tasks": total_tasks,
                "successful_tasks": successful_tasks,
                "average_score": average_score,
                "success_rate": success_rate,
                "performance_data": performance_data,
            }

    except Exception as e:
        TASK_OPERATION_COUNT.labels(
            operation="get_agent_performance", status="error"
        ).inc()
        logger.error(f"Failed to get performance for agent {agent}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get agent performance: {e}"
        )


@router.post("/{task_id}/retry")
async def retry_task(
    task_id: UUID, neo4j_client: Neo4jClient = Depends(get_neo4j_client)
) -> Dict[str, str]:
    """Retry a failed task."""
    try:
        with TASK_OPERATION_DURATION.labels(operation="retry").time():
            # Check if task exists and is in a retryable state
            existing_task = await get_task(task_id, neo4j_client)
            if not existing_task:
                raise HTTPException(status_code=404, detail="Task not found")

            if existing_task.status not in ["failed", "cancelled"]:
                raise HTTPException(
                    status_code=400, detail="Task is not in a retryable state"
                )

            # Update task status to pending for retry
            await neo4j_client.update_task_status(str(task_id), "pending")

            # Submit task to Celery queue for retry
            from opsvi_auto_forge.infrastructure.workers.agent_tasks import (
                submit_agent_task,
            )
            import json

            # Get task execution data
            query = """
            MATCH (t:Task {id: $task_id})
            RETURN t.agent as agent_type, t.inputs_json as inputs_json
            """
            task_data = await neo4j_client.execute_query(
                query, {"task_id": str(task_id)}
            )

            if task_data:
                task_record = task_data[0]
                agent_type = task_record["agent_type"]
                inputs_json = task_record["inputs_json"]

                # Parse inputs if it's a string
                if isinstance(inputs_json, str):
                    task_execution_data = json.loads(inputs_json)
                else:
                    task_execution_data = inputs_json or {}

                # Submit task for retry
                submit_agent_task(
                    agent_type=agent_type,
                    task_execution_data=task_execution_data,
                    project_id=existing_task.project_id,
                    run_id=existing_task.run_id,
                    node_id=str(task_id),
                )

                logger.info(f"Submitted task {task_id} for retry (agent: {agent_type})")
            else:
                logger.warning(f"Could not find task data for retry: {task_id}")

            TASK_OPERATION_COUNT.labels(operation="retry", status="success").inc()
            logger.info(f"Retrying task: {task_id}")

            return {"message": f"Task {task_id} queued for retry"}

    except HTTPException:
        raise
    except Exception as e:
        TASK_OPERATION_COUNT.labels(operation="retry", status="error").inc()
        logger.error(f"Failed to retry task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retry task: {e}")


@router.get("/stats/overview")
async def get_task_stats(
    neo4j_client: Neo4jClient = Depends(get_neo4j_client),
) -> Dict[str, Any]:
    """Get overall task statistics."""
    try:
        with TASK_OPERATION_DURATION.labels(operation="get_stats").time():
            # Get task counts by status
            status_query = """
            MATCH (t:Task)
            RETURN t.status as status, count(t) as count
            """
            status_result = await neo4j_client.execute_query(status_query)
            status_counts = {
                record["status"]: record["count"] for record in status_result
            }

            # Get task counts by agent
            agent_query = """
            MATCH (t:Task)
            RETURN t.agent as agent, count(t) as count
            """
            agent_result = await neo4j_client.execute_query(agent_query)
            agent_counts = {record["agent"]: record["count"] for record in agent_result}

            # Get average scores
            score_query = """
            MATCH (t:Task)-[:RESULTED_IN]->(r:Result)
            RETURN avg(r.score) as avg_score, min(r.score) as min_score, max(r.score) as max_score
            """
            score_result = await neo4j_client.execute_query(score_query)
            score_stats = (
                score_result[0]
                if score_result
                else {"avg_score": 0.0, "min_score": 0.0, "max_score": 0.0}
            )

            TASK_OPERATION_COUNT.labels(operation="get_stats", status="success").inc()

            return {
                "total_tasks": sum(status_counts.values()),
                "status_distribution": status_counts,
                "agent_distribution": agent_counts,
                "score_statistics": score_stats,
                "success_rate": (
                    status_counts.get("success", 0) / sum(status_counts.values())
                    if status_counts
                    else 0.0
                ),
            }

    except Exception as e:
        TASK_OPERATION_COUNT.labels(operation="get_stats", status="error").inc()
        logger.error(f"Failed to get task stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get task stats: {e}")
