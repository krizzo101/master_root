"""Result Collector - Collect and process task execution results."""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from opsvi_auto_forge.config.models import TaskStatus
from opsvi_auto_forge.infrastructure.memory.graph.client import Neo4jClient
from opsvi_auto_forge.application.orchestrator.task_models import TaskResult

logger = logging.getLogger(__name__)


class ResultCollector:
    """Collect and process task execution results.

    This component provides the missing systematic result collection and
    processing functionality identified in the gap analysis.
    """

    def __init__(self, neo4j_client: Neo4jClient):
        """Initialize the Result Collector.

        Args:
            neo4j_client: Neo4j client for result persistence
        """
        self.neo4j_client = neo4j_client
        logger.info("ResultCollector initialized successfully")

    async def process_result(
        self, task_id: UUID, raw_result: Dict[str, Any]
    ) -> TaskResult:
        """Process raw Celery result into structured TaskResult.

        Args:
            task_id: Task ID that produced the result
            raw_result: Raw result from Celery task execution

        Returns:
            TaskResult: Structured and validated task result
        """
        try:
            logger.info(f"Processing result for task {task_id}")

            # Extract metrics and metadata
            metrics = self._extract_metrics(raw_result)

            # Validate result structure
            validated_result = self._validate_result(raw_result)

            # Determine status
            status = self._determine_status(validated_result)

            # Calculate score
            score = self._calculate_score(validated_result, metrics)

            # Create TaskResult object
            task_result = TaskResult(
                task_id=task_id,
                status=status,
                score=score,
                metrics=metrics,
                errors=validated_result.get("errors", []),
                warnings=validated_result.get("warnings", []),
                artifacts=validated_result.get("artifacts", []),
                execution_time_seconds=validated_result.get("execution_time"),
                memory_usage_mb=validated_result.get("memory_usage"),
                cpu_usage_percent=validated_result.get("cpu_usage"),
                tokens_used=validated_result.get("tokens_used"),
                cost=validated_result.get("cost"),
                metadata=validated_result.get("metadata", {}),
            )

            # Persist to Neo4j
            await self._persist_result(task_result)

            logger.info(f"Result processed successfully for task {task_id}: {status}")
            return task_result

        except Exception as e:
            logger.error(f"Failed to process result for task {task_id}: {e}")

            # Create error result
            error_result = TaskResult(
                task_id=task_id,
                status=TaskStatus.FAILED,
                score=0.0,
                errors=[f"Result processing failed: {str(e)}"],
                warnings=[],
                artifacts=[],
                metadata={"processing_error": str(e)},
            )

            return error_result

    def _extract_metrics(self, raw_result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract performance and quality metrics from raw result.

        Args:
            raw_result: Raw result from Celery task

        Returns:
            Dictionary of extracted metrics
        """
        metrics = {}

        try:
            # Performance metrics
            if "execution_time" in raw_result:
                metrics["execution_time_seconds"] = float(raw_result["execution_time"])

            if "memory_usage" in raw_result:
                metrics["memory_usage_mb"] = float(raw_result["memory_usage"])

            if "cpu_usage" in raw_result:
                metrics["cpu_usage_percent"] = float(raw_result["cpu_usage"])

            # Token usage metrics
            if "tokens_used" in raw_result:
                metrics["tokens_used"] = int(raw_result["tokens_used"])

            if "cost" in raw_result:
                metrics["cost_usd"] = float(raw_result["cost"])

            # Quality metrics
            if "quality_score" in raw_result:
                metrics["quality_score"] = float(raw_result["quality_score"])

            if "test_coverage" in raw_result:
                metrics["test_coverage_percent"] = float(raw_result["test_coverage"])

            if "code_complexity" in raw_result:
                metrics["code_complexity"] = int(raw_result["code_complexity"])

            # Custom metrics
            if "custom_metrics" in raw_result:
                metrics.update(raw_result["custom_metrics"])

        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to extract metrics: {e}")

        return metrics

    def _validate_result(self, raw_result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean raw result structure.

        Args:
            raw_result: Raw result from Celery task

        Returns:
            Validated and cleaned result
        """
        validated = {}

        # Required fields
        if "status" not in raw_result:
            validated["status"] = "unknown"
        else:
            validated["status"] = str(raw_result["status"])

        # Optional fields with defaults
        validated["errors"] = raw_result.get("errors", [])
        validated["warnings"] = raw_result.get("warnings", [])
        validated["artifacts"] = raw_result.get("artifacts", [])
        validated["metadata"] = raw_result.get("metadata", {})

        # Performance fields
        validated["execution_time"] = raw_result.get("execution_time")
        validated["memory_usage"] = raw_result.get("memory_usage")
        validated["cpu_usage"] = raw_result.get("cpu_usage")
        validated["tokens_used"] = raw_result.get("tokens_used")
        validated["cost"] = raw_result.get("cost")

        # Ensure lists are actually lists
        if not isinstance(validated["errors"], list):
            validated["errors"] = [str(validated["errors"])]

        if not isinstance(validated["warnings"], list):
            validated["warnings"] = [str(validated["warnings"])]

        if not isinstance(validated["artifacts"], list):
            validated["artifacts"] = [str(validated["artifacts"])]

        return validated

    def _determine_status(self, validated_result: Dict[str, Any]) -> TaskStatus:
        """Determine task status from validated result.

        Args:
            validated_result: Validated result data

        Returns:
            TaskStatus enum value
        """
        status_str = validated_result.get("status", "unknown").lower()

        # Map status strings to TaskStatus enum
        status_mapping = {
            "success": TaskStatus.COMPLETED,
            "completed": TaskStatus.COMPLETED,
            "ok": TaskStatus.COMPLETED,
            "failed": TaskStatus.FAILED,
            "error": TaskStatus.FAILED,
            "timeout": TaskStatus.FAILED,
            "cancelled": TaskStatus.CANCELLED,
            "pending": TaskStatus.PENDING,
            "running": TaskStatus.RUNNING,
            "unknown": TaskStatus.FAILED,
        }

        return status_mapping.get(status_str, TaskStatus.FAILED)

    def _calculate_score(
        self, validated_result: Dict[str, Any], metrics: Dict[str, Any]
    ) -> float:
        """Calculate overall score for the task result.

        Args:
            validated_result: Validated result data
            metrics: Extracted metrics

        Returns:
            Score between 0.0 and 1.0
        """
        try:
            # Base score from status
            status = validated_result.get("status", "unknown").lower()
            if status in ["success", "completed", "ok"]:
                base_score = 1.0
            elif status in ["failed", "error", "timeout"]:
                base_score = 0.0
            elif status == "cancelled":
                base_score = 0.5
            else:
                base_score = 0.0

            # Adjust score based on errors and warnings
            error_penalty = len(validated_result.get("errors", [])) * 0.1
            warning_penalty = len(validated_result.get("warnings", [])) * 0.02

            # Adjust score based on quality metrics
            quality_bonus = 0.0
            if "quality_score" in metrics:
                quality_bonus = metrics["quality_score"] * 0.2

            # Calculate final score
            final_score = max(
                0.0,
                min(1.0, base_score - error_penalty - warning_penalty + quality_bonus),
            )

            return round(final_score, 3)

        except Exception as e:
            logger.warning(f"Failed to calculate score: {e}")
            return 0.0

    async def _persist_result(self, task_result: TaskResult) -> None:
        """Persist task result to Neo4j.

        Args:
            task_result: TaskResult to persist
        """
        try:
            # Prepare data for Neo4j
            result_data = {
                "id": str(task_result.task_id),
                "status": task_result.status.value
                if hasattr(task_result.status, "value")
                else str(task_result.status),
                "score": task_result.score,
                "metrics": json.dumps(task_result.metrics),
                "errors": json.dumps(task_result.errors),
                "warnings": json.dumps(task_result.warnings),
                "artifacts": json.dumps(task_result.artifacts),
                "execution_time_seconds": task_result.execution_time_seconds,
                "memory_usage_mb": task_result.memory_usage_mb,
                "cpu_usage_percent": task_result.cpu_usage_percent,
                "tokens_used": task_result.tokens_used,
                "cost": task_result.cost,
                "metadata": json.dumps(task_result.metadata),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

            # Upsert result
            query = """
            MERGE (r:TaskResult {id: $id})
            SET r += $data
            """

            await self.neo4j_client.run_query(
                query, parameters={"id": str(task_result.task_id), "data": result_data}
            )

            # Create relationship to task execution
            relationship_query = """
            MATCH (t:TaskExecution {id: $task_id})
            MATCH (r:TaskResult {id: $result_id})
            MERGE (t)-[:RESULTED_IN]->(r)
            """

            await self.neo4j_client.run_query(
                relationship_query,
                parameters={
                    "task_id": str(task_result.task_id),
                    "result_id": str(task_result.task_id),
                },
            )

            logger.debug(f"Result persisted to Neo4j for task {task_result.task_id}")

        except Exception as e:
            logger.error(
                f"Failed to persist result for task {task_result.task_id}: {e}"
            )
            raise

    async def get_result(self, task_id: UUID) -> Optional[TaskResult]:
        """Get task result from Neo4j.

        Args:
            task_id: Task ID to get result for

        Returns:
            TaskResult or None if not found
        """
        try:
            query = """
            MATCH (r:TaskResult {id: $task_id})
            RETURN r
            """

            result = await self.neo4j_client.run_query(
                query, parameters={"task_id": str(task_id)}
            )

            if result:
                result_data = dict(result[0]["r"])

                # Parse JSON fields
                metrics = json.loads(result_data.get("metrics", "{}"))
                errors = json.loads(result_data.get("errors", "[]"))
                warnings = json.loads(result_data.get("warnings", "[]"))
                artifacts = json.loads(result_data.get("artifacts", "[]"))
                metadata = json.loads(result_data.get("metadata", "{}"))

                return TaskResult(
                    task_id=UUID(result_data["id"]),
                    status=TaskStatus(result_data["status"]),
                    score=float(result_data["score"]),
                    metrics=metrics,
                    errors=errors,
                    warnings=warnings,
                    artifacts=artifacts,
                    execution_time_seconds=result_data.get("execution_time_seconds"),
                    memory_usage_mb=result_data.get("memory_usage_mb"),
                    cpu_usage_percent=result_data.get("cpu_usage_percent"),
                    tokens_used=result_data.get("tokens_used"),
                    cost=result_data.get("cost"),
                    metadata=metadata,
                )

            return None

        except Exception as e:
            logger.error(f"Failed to get result for task {task_id}: {e}")
            return None

    async def get_results_by_status(self, status: TaskStatus) -> List[TaskResult]:
        """Get all results with a specific status.

        Args:
            status: Status to filter by

        Returns:
            List of TaskResult objects
        """
        try:
            query = """
            MATCH (r:TaskResult)
            WHERE r.status = $status
            RETURN r
            ORDER BY r.created_at DESC
            """

            result = await self.neo4j_client.run_query(
                query,
                parameters={
                    "status": status.value if hasattr(status, "value") else str(status)
                },
            )

            results = []
            for record in result:
                result_data = dict(record["r"])

                # Parse JSON fields
                metrics = json.loads(result_data.get("metrics", "{}"))
                errors = json.loads(result_data.get("errors", "[]"))
                warnings = json.loads(result_data.get("warnings", "[]"))
                artifacts = json.loads(result_data.get("artifacts", "[]"))
                metadata = json.loads(result_data.get("metadata", "{}"))

                task_result = TaskResult(
                    task_id=UUID(result_data["id"]),
                    status=TaskStatus(result_data["status"]),
                    score=float(result_data["score"]),
                    metrics=metrics,
                    errors=errors,
                    warnings=warnings,
                    artifacts=artifacts,
                    execution_time_seconds=result_data.get("execution_time_seconds"),
                    memory_usage_mb=result_data.get("memory_usage_mb"),
                    cpu_usage_percent=result_data.get("cpu_usage_percent"),
                    tokens_used=result_data.get("tokens_used"),
                    cost=result_data.get("cost"),
                    metadata=metadata,
                )

                results.append(task_result)

            return results

        except Exception as e:
            logger.error(f"Failed to get results by status {status}: {e}")
            return []


class ResultProcessingError(Exception):
    """Exception raised for result processing errors."""

    pass
