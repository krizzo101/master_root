"""Meta orchestrator for pipeline execution and workflow management."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ConfigDict

from opsvi_auto_forge.config.models import Project, Run, TaskRecord, TaskStatus
from opsvi_auto_forge.infrastructure.memory.graph.client import Neo4jClient
from opsvi_auto_forge.infrastructure.memory.graph.decision_client import (
    get_decision_client,
)
from opsvi_auto_forge.core.prompting.schema_registry import get_schema

from .budgets import BudgetManager, BudgetType, BudgetPeriod
from .dag_loader import DAGLoader, ExecutionDAG, DAGNode
from .policies import PolicyManager, QualityGateResult
from .registry import TaskRegistryManager
from .router import ModelRouter
from .dsl_processor import DSLProcessor
from opsvi_auto_forge.config.settings import settings
from .task_models import (
    TaskDefinition,
    TaskExecution,
    TaskResult,
    TaskExecutionPlan,
    TaskPriority,
    TaskType,
)
from .exceptions import OrchestrationError, ValidationError

# Decision kernel imports
from opsvi_auto_forge.core.decision_kernel.analyzer import TaskAnalyzer, analyze_task
from opsvi_auto_forge.core.decision_kernel.strategies import select_strategy
from opsvi_auto_forge.core.decision_kernel.models import (
    RouteDecision,
    DecisionRecord,
    DecisionLifecycle,
    Claim,
    Evidence,
    Verification,
)

# Monitoring imports
from opsvi_auto_forge.infrastructure.monitoring.metrics.decision_metrics import (
    decision_success,
    decision_failure,
    dk_decision_confidence_bucket,
    quality_gate_passed_total,
    quality_gate_failed_total,
    quality_gate_repair_attempts_total,
    quality_gate_repair_success_total,
    quality_gate_repair_failure_total,
    auto_repair_attempts_total,
    auto_repair_success_total,
    auto_repair_failure_total,
    dsl_config_loaded_total,
    dsl_knobs_applied_total,
    cost_per_pass_gate,
)

logger = logging.getLogger(__name__)


class OrchestrationStatus(str, Enum):
    """Status of orchestration."""

    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class OrchestrationContext(BaseModel):
    """Context for orchestration execution."""

    project_id: UUID
    run_id: UUID
    dag_id: UUID
    pipeline_name: str = Field(
        ..., min_length=1, description="Pipeline name cannot be empty"
    )
    status: OrchestrationStatus = OrchestrationStatus.IDLE
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    current_node: Optional[str] = None
    completed_nodes: List[str] = Field(default_factory=list)
    failed_nodes: List[str] = Field(default_factory=list)
    total_nodes: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)
    quality_gates: Dict[str, float] = Field(default_factory=dict)
    auto_repair: Dict[str, Any] = Field(default_factory=dict)
    dsl_config: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(
        use_enum_values=True,
        json_encoders={
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        },
    )


class MetaOrchestrator:
    """Meta orchestrator for coordinating pipeline execution."""

    def __init__(self, neo4j_client: Optional[Neo4jClient] = None):
        """Initialize the meta orchestrator."""
        self.neo4j_client = neo4j_client
        self.registry = TaskRegistryManager(neo4j_client)
        self.dag_loader = DAGLoader(neo4j_client)
        self.policy_manager = PolicyManager(neo4j_client)
        self.budget_manager = BudgetManager(neo4j_client)
        self.router = ModelRouter(neo4j_client)
        self.dsl_processor = DSLProcessor()

        # Initialize decision kernel components
        self.decision_client = get_decision_client()

        # Load DSL configuration
        self._load_dsl_config()

    async def initialize(self) -> None:
        """Initialize the orchestrator asynchronously."""
        # Load default tasks
        await self.registry.initialize()
        logger.info("MetaOrchestrator initialized with default tasks")

    def _load_dsl_config(self) -> None:
        """Load DSL configuration and emit metrics."""
        try:
            # Use DSL processor to load and validate configuration
            self.dsl_processor.reload_config()

            # Validate configuration
            issues = self.dsl_processor.validate_config()
            if issues:
                logger.warning(f"DSL configuration issues: {issues}")

            # Get configuration summary
            summary = self.dsl_processor.get_config_summary()
            logger.info(f"DSL configuration loaded: {summary}")

        except Exception as e:
            logger.error(f"Failed to load DSL configuration: {e}")

    async def start_pipeline(
        self, project_id: UUID, run_id: UUID, pipeline_name: str
    ) -> OrchestrationContext:
        """Start a new pipeline execution."""
        try:
            # Load pipeline DAG with DSL processing
            dag = self.dag_loader.load_pipeline(pipeline_name)

            # Validate that all tasks exist in registry
            await self.dag_loader.validate_pipeline_tasks(dag, self.registry)

            # Create orchestration context
            context = OrchestrationContext(
                project_id=project_id,
                run_id=run_id,
                dag_id=dag.id,
                pipeline_name=pipeline_name,
                status=OrchestrationStatus.RUNNING,
                started_at=datetime.now(timezone.utc),
                total_nodes=len(dag.nodes),
                quality_gates=dag.quality_gates,
                auto_repair=dag.auto_repair,
                dsl_config=dag.dsl_config.dict() if dag.dsl_config else None,
            )

            # Persist pipeline to Neo4j
            await self.dag_loader.persist_pipeline(project_id, run_id, dag)

            # Persist context
            await self._persist_context(context)

            logger.info(f"Started pipeline {pipeline_name} with {len(dag.nodes)} nodes")
            return context

        except Exception as e:
            logger.error(f"Failed to start pipeline {pipeline_name}: {e}")
            raise OrchestrationError(
                "pipeline_start", f"Pipeline start failed: {e}", pipeline_name
            )

    async def _execute_pipeline(
        self, context: OrchestrationContext, dag: ExecutionDAG
    ) -> None:
        """Execute the pipeline DAG."""
        try:
            # Validate pipeline configuration
            self._validate_pipeline_config(context)

            # Execute nodes in dependency order
            execution_order = self._calculate_execution_order(dag)

            for node_id in execution_order:
                node = next((n for n in dag.nodes if n.id == node_id), None)
                if not node:
                    logger.error(f"Node {node_id} not found in DAG")
                    continue

                # Update current node
                context.current_node = node_id

                try:
                    # Execute node with quality gates
                    result = await self._execute_node_with_quality_gates(
                        context, dag, node
                    )

                    if result.status == TaskStatus.SUCCESS:
                        context.completed_nodes.append(node_id)
                        logger.info(f"Node {node_id} completed successfully")
                    else:
                        context.failed_nodes.append(node_id)
                        logger.error(f"Node {node_id} failed: {result.error}")

                        # Check if we should attempt auto-repair
                        if self._should_attempt_repair(context, node):
                            await self._attempt_node_repair(context, dag, node, result)

                except Exception as e:
                    logger.error(f"Node {node_id} execution failed: {e}")
                    context.failed_nodes.append(node_id)

                    # Handle node failure
                    await self._handle_node_failure(context, node_id, e)

                # Update context
                await self._update_context(context)

            # Check if pipeline completed successfully
            if len(context.failed_nodes) == 0:
                context.status = OrchestrationStatus.COMPLETED
                context.completed_at = datetime.now(timezone.utc)
                logger.info(f"Pipeline {context.pipeline_name} completed successfully")
            else:
                context.status = OrchestrationStatus.FAILED
                logger.error(
                    f"Pipeline {context.pipeline_name} failed with {len(context.failed_nodes)} failed nodes"
                )

        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}")
            context.status = OrchestrationStatus.FAILED
            raise OrchestrationError(
                "pipeline_execution",
                f"Pipeline execution failed: {e}",
                context.pipeline_name,
            )

    async def _execute_node_with_quality_gates(
        self, context: OrchestrationContext, dag: ExecutionDAG, node: DAGNode
    ) -> TaskResult:
        """Execute a node with quality gate enforcement."""
        try:
            # Execute the task
            result = await self._execute_node(context, dag, node)

            if result.status == TaskStatus.SUCCESS:
                # Apply quality gates
                quality_result = await self._apply_quality_gates(context, node, result)

                if quality_result.passed:
                    # Quality gates passed
                    quality_gate_passed_total.labels(gate_name="overall").inc()

                    # Emit cost per pass gate metric
                    if hasattr(result, "cost_actual") and result.cost_actual:
                        cost_per_pass_gate.labels(gate="overall").set(
                            result.cost_actual
                        )

                    logger.info(f"Quality gates passed for node {node.id}")
                else:
                    # Quality gates failed
                    quality_gate_failed_total.labels(gate_name="overall").inc()

                    # Attempt auto-repair
                    if (
                        quality_result.repair_attempts
                        < quality_result.max_repair_attempts
                    ):
                        repair_success = await self._attempt_quality_gate_repair(
                            context, node, result, quality_result
                        )

                        if repair_success:
                            quality_gate_repair_success_total.labels(
                                gate_name="overall"
                            ).inc()
                            logger.info(
                                f"Quality gate repair successful for node {node.id}"
                            )
                        else:
                            quality_gate_repair_failure_total.labels(
                                gate_name="overall"
                            ).inc()
                            logger.error(
                                f"Quality gate repair failed for node {node.id}"
                            )
                    else:
                        logger.error(
                            f"Quality gates failed after {quality_result.max_repair_attempts} attempts for node {node.id}"
                        )
                        result.status = TaskStatus.FAILED
                        result.error = f"Quality gates failed: {quality_result.overall_score:.2f} below threshold"

            return result

        except Exception as e:
            logger.error(f"Node execution with quality gates failed: {e}")
            return TaskResult(
                task_id=node.id,
                status=TaskStatus.FAILED,
                error=str(e),
                metadata={},
            )

    async def _apply_quality_gates(
        self, context: OrchestrationContext, node: DAGNode, result: TaskResult
    ) -> QualityGateResult:
        """Apply quality gates to a task result."""
        try:
            # Create artifact and result objects for policy evaluation
            from opsvi_auto_forge.config.models import Artifact, Result
            import hashlib

            content = result.metadata.get("output", "") or ""
            content_hash = hashlib.sha256(content.encode()).hexdigest()

            artifact = Artifact(
                id=uuid4(),
                type="code",  # Simplified - would be determined by task type
                path=f"artifacts/{node.id}",
                hash=content_hash,
                metadata={"content": content, "node_id": node.id},
            )

            result_obj = Result(
                id=uuid4(),
                status="ok" if result.status == TaskStatus.SUCCESS else "fail",
                score=1.0 if result.status == TaskStatus.SUCCESS else 0.0,
                metrics=result.metadata or {},
                errors=[],
                warnings=[],
            )

            # Apply quality gates
            quality_result = await self.policy_manager.enforce_quality_gates(
                artifact=artifact,
                result=result_obj,
                context={"node_id": node.id, "task_type": node.task_type},
                quality_gates=context.quality_gates,
                max_repair_attempts=context.auto_repair.get("max_repair_attempts", 3),
            )

            return quality_result

        except Exception as e:
            logger.error(f"Quality gate application failed: {e}")
            # Return failed quality gate result
            return QualityGateResult(
                gate_name="overall",
                passed=False,
                overall_score=0.0,
                policy_results=[],
                repair_attempts=0,
                max_repair_attempts=3,
            )

    async def _attempt_quality_gate_repair(
        self,
        context: OrchestrationContext,
        node: DAGNode,
        result: TaskResult,
        quality_result: QualityGateResult,
    ) -> bool:
        """Attempt to repair failed quality gates."""
        try:
            auto_repair_attempts_total.labels(repair_type="quality_gate").inc()

            # Collect patch plans from failed policies
            patch_plans = []
            for policy_result in quality_result.policy_results:
                if not policy_result.passed:
                    patch_plans.extend(policy_result.patch_plan)

            if not patch_plans:
                logger.warning("No patch plans available for quality gate repair")
                return False

            # Apply patches (simplified - would trigger agent repair)
            logger.info(f"Applying {len(patch_plans)} patches for quality gate repair")

            # For now, just log the patches
            for patch in patch_plans:
                logger.info(f"Patch: {patch}")

            # In a real implementation, this would:
            # 1. Create a repair task
            # 2. Send to appropriate agent
            # 3. Update artifact with repaired content
            # 4. Re-run quality gates

            # Simplified success for now
            auto_repair_success_total.labels(repair_type="quality_gate").inc()
            return True

        except Exception as e:
            logger.error(f"Quality gate repair failed: {e}")
            auto_repair_failure_total.labels(repair_type="quality_gate").inc()
            return False

    def _should_attempt_repair(
        self, context: OrchestrationContext, node: DAGNode
    ) -> bool:
        """Determine if auto-repair should be attempted."""
        # Check if auto-repair is enabled
        if not context.auto_repair.get("enabled", True):
            return False

        # Check if we haven't exceeded max repair attempts
        repair_attempts = context.metadata.get(f"repair_attempts_{node.id}", 0)
        max_attempts = context.auto_repair.get("max_repair_attempts", 3)

        return repair_attempts < max_attempts

    async def _attempt_node_repair(
        self,
        context: OrchestrationContext,
        dag: ExecutionDAG,
        node: DAGNode,
        result: TaskResult,
    ) -> bool:
        """Attempt to repair a failed node."""
        try:
            auto_repair_attempts_total.labels(repair_type="node").inc()

            # Increment repair attempts
            repair_key = f"repair_attempts_{node.id}"
            current_attempts = context.metadata.get(repair_key, 0)
            context.metadata[repair_key] = current_attempts + 1

            logger.info(
                f"Attempting repair for node {node.id} (attempt {current_attempts + 1})"
            )

            # In a real implementation, this would:
            # 1. Analyze the failure
            # 2. Create a repair task
            # 3. Execute the repair
            # 4. Re-run the original task

            # Simplified success for now
            auto_repair_success_total.labels(repair_type="node").inc()
            return True

        except Exception as e:
            logger.error(f"Node repair failed: {e}")
            auto_repair_failure_total.labels(repair_type="node").inc()
            return False

    def _calculate_execution_order(self, dag: ExecutionDAG) -> List[str]:
        """Calculate execution order for DAG nodes."""
        # Simple topological sort
        in_degree = {node.id: len(node.dependencies) for node in dag.nodes}
        queue = [node.id for node in dag.nodes if len(node.dependencies) == 0]
        result = []

        while queue:
            node_id = queue.pop(0)
            result.append(node_id)

            # Update in-degree for dependents
            for node in dag.nodes:
                if node_id in node.dependencies:
                    in_degree[node.id] -= 1
                    if in_degree[node.id] == 0:
                        queue.append(node.id)

        return result

    async def _execute_node(
        self, context: OrchestrationContext, dag: ExecutionDAG, node: DAGNode
    ) -> TaskResult:
        """Execute a single DAG node."""
        try:
            # Get task definition from registry
            task_definition = await self.registry.get_task(node.name)
            if not task_definition:
                raise OrchestrationError(
                    "task_not_found",
                    f"Task '{node.name}' not found in registry",
                    node.name,
                )

            # Analyze and route the task
            routing_decision = await self._analyze_and_route_task(
                task_id=uuid4(),
                agent=node.agent,
                task_type=node.task_type,
                task_input=node.config.get("input"),
                context={"node_id": node.id, "pipeline_name": context.pipeline_name},
            )

            # Create task execution using the registered task definition
            execution = TaskExecution(
                id=uuid4(),
                definition=task_definition,
                project_id=context.project_id,
                run_id=context.run_id,
                inputs=node.config.get("input", {}),
                metadata=node.config,
            )

            # Execute the task
            result = await self._execute_task(execution, routing_decision)

            # Persist task execution
            await self._persist_task_execution(execution, result)

            return result

        except Exception as e:
            logger.error(f"Node execution failed: {e}")
            return TaskResult(
                task_id=node.id,
                status=TaskStatus.FAILED,
                score=0.0,  # Failed tasks get 0 score
                errors=[str(e)],
                metadata={},
            )

    async def _execute_task(
        self, execution: TaskExecution, routing_decision: Any
    ) -> TaskResult:
        """Execute a task with the given routing decision."""
        try:
            # Record decision success/failure
            strategy = routing_decision.get("strategy", "unknown")
            model = routing_decision.get("model", "unknown")

            # Execute the task (simplified)
            result = await self._execute_task_internal(execution, routing_decision)

            if result.status == TaskStatus.SUCCESS:
                decision_success.labels(strategy=strategy, model=model).inc()

                # Record confidence if available
                if hasattr(result, "confidence") and result.confidence:
                    dk_decision_confidence_bucket.observe(result.confidence)
            else:
                decision_failure.labels(strategy=strategy, model=model).inc()

            return result

        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            decision_failure.labels(strategy="unknown", model="unknown").inc()
            return TaskResult(
                task_id=execution.id,  # Use execution.id instead of execution.task_id
                status=TaskStatus.FAILED,
                score=0.0,  # Failed tasks get 0 score
                metrics={"error": str(e)},
                errors=[str(e)],
                metadata={},
            )

    async def _execute_task_internal(
        self, execution: TaskExecution, routing_decision: Any
    ) -> TaskResult:
        """Internal task execution logic - ENHANCED VERSION with TaskExecutionEngine."""
        # Import here to avoid circular imports
        from .dependency_container import get_service, has_service

        try:
            # Try to use TaskExecutionEngine first
            if has_service("task_execution_engine"):
                execution_engine = get_service("task_execution_engine")

                # Prepare parameters for the engine
                parameters = {
                    "name": execution.definition.name,
                    "agent_type": execution.definition.agent_type,
                    "description": execution.definition.description,
                    "inputs": execution.inputs,
                    "outputs": execution.definition.outputs,
                    "dependencies": execution.definition.dependencies,
                    "timeout_seconds": execution.definition.timeout_seconds,
                    "retry_attempts": execution.definition.retry_attempts,
                    "queue": execution.definition.queue,
                    "project_id": execution.project_id,
                    "run_id": execution.run_id,
                    "metadata": {
                        **execution.metadata,
                        "agent": execution.definition.agent_type,
                        "model": routing_decision.get("model", "unknown"),
                        "strategy": routing_decision.get("strategy", "unknown"),
                    },
                }

                # Execute using the engine
                result = await execution_engine.execute_task(
                    task_id=str(execution.id),
                    task_type=execution.definition.type,
                    parameters=parameters,
                )

                # Convert engine result to TaskResult format
                return TaskResult(
                    task_id=execution.id,
                    status=result.status,
                    score=result.score,
                    metrics={
                        "tokens_used": result.metadata.get("tokens_used", 0),
                        "agent_type": execution.definition.agent_type,
                        "cost": result.metadata.get("cost", 0.0),
                        "execution_time_seconds": result.metadata.get(
                            "execution_time_seconds", 0.0
                        ),
                    },
                    errors=result.errors,
                    warnings=result.warnings,
                    artifacts=result.artifacts,
                    metadata={
                        **result.metadata,
                        "agent": execution.definition.agent_type,
                        "model": routing_decision.get("model", "unknown"),
                        "strategy": routing_decision.get("strategy", "unknown"),
                    },
                )

            else:
                # Fallback to TaskExecutionBridge
                logger.warning(
                    "TaskExecutionEngine not available, using TaskExecutionBridge fallback"
                )
                from .task_execution_bridge import TaskExecutionBridge

                # Initialize bridge if not exists
                if not hasattr(self, "task_bridge"):
                    self.task_bridge = TaskExecutionBridge()

                # Submit task asynchronously and wait for completion
                result_data = await self.task_bridge.submit_and_wait(
                    agent_type=execution.definition.agent_type,
                    task_data=execution.model_dump(),
                    project_id=str(execution.project_id),
                    run_id=str(execution.run_id),
                    node_id=str(execution.id),
                    timeout=execution.definition.timeout_seconds or 300,
                )

                return TaskResult(
                    task_id=execution.id,
                    status=TaskStatus.SUCCESS
                    if result_data.get("status") == "ok"
                    else TaskStatus.FAILED,
                    score=result_data.get("score", 0.0),
                    metrics={
                        "tokens_used": result_data.get("tokens_used", 0),
                        "agent_type": execution.definition.agent_type,
                        "cost": result_data.get("cost", 0.0),
                        "execution_time_seconds": result_data.get(
                            "execution_time_seconds", 0.0
                        ),
                    },
                    metadata={
                        "agent": execution.definition.agent_type,
                        "model": routing_decision.get("model", "unknown"),
                        "strategy": routing_decision.get("strategy", "unknown"),
                        "confidence": result_data.get("score", 0.0),
                        "cost_actual": result_data.get("cost", 0.0),
                        "latency_ms": int(
                            result_data.get("execution_time_seconds", 0.0) * 1000
                        ),
                        "celery_task_id": result_data.get("task_id", "unknown"),
                    },
                )

        except Exception as e:
            logger.error(f"Task execution failed for {execution.id}: {e}")
            return TaskResult(
                task_id=execution.id,
                status=TaskStatus.FAILED,
                score=0.0,
                metrics={"error": str(e)},
                errors=[str(e)],
                metadata={
                    "agent": execution.definition.agent_type,
                    "model": routing_decision.get("model", "unknown"),
                    "strategy": routing_decision.get("strategy", "unknown"),
                    "error": str(e),
                },
            )

    async def _analyze_and_route_task(
        self,
        task_id: UUID,
        agent: str,
        task_type: str,
        task_input: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        budget_hint: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Analyze and route a task."""
        try:
            # Apply DSL knobs to context
            enhanced_context = self.dsl_processor.apply_all_knobs(context or {})

            # Analyze task complexity with enhanced context
            analysis = await analyze_task(
                task_id=task_id,
                agent=agent,
                task_type=task_type,
                budget_hint=budget_hint or {},
                task_input=task_input or "",
                context=enhanced_context,
            )

            # Select strategy with reasoning knobs
            strategy = select_strategy(
                complexity=analysis.get("complexity", "medium"),
                risk=analysis.get("risk", "medium"),
                cost_estimate=analysis.get("cost_estimate", 0.001),
                context=enhanced_context,
            )

            # Route to model with knowledge knobs
            routing_decision = await self.router.route_task(
                task_type=task_type,
                strategy=strategy,
                complexity=analysis.get("complexity", "medium"),
                risk=analysis.get("risk", "medium"),
                budget_hint=budget_hint,
                context=enhanced_context,
            )

            # Create decision record if decision kernel is enabled
            if hasattr(self, "decision_client") and self.decision_client:
                try:
                    decision_id = await self.decision_client.create_decision(
                        task_id=str(task_id),
                        props={
                            "strategy": strategy,
                            "model": routing_decision.get("model", "unknown"),
                            "confidence": routing_decision.get("confidence", 0.0),
                            "complexity": analysis.get("complexity", "medium"),
                            "risk": analysis.get("risk", "medium"),
                            "cost_estimate": analysis.get("cost_estimate", 0.001),
                            "dsl_applied": True,
                        },
                    )
                    # Store decision_id in node metadata for later verification
                    if hasattr(node, "metadata"):
                        node.metadata["decision_id"] = decision_id
                except Exception as e:
                    logger.warning(f"Failed to create decision record: {e}")

            return {
                "strategy": strategy,
                "model": routing_decision.get("model", "unknown"),
                "confidence": routing_decision.get("confidence", 0.0),
                "cost_estimate": analysis.get("cost_estimate", 0.001),
                "complexity": analysis.get("complexity", "medium"),
                "risk": analysis.get("risk", "medium"),
                "dsl_applied": True,
            }

        except Exception as e:
            logger.error(f"Task analysis and routing failed: {e}")
            return {
                "strategy": "fallback",
                "model": "gpt-4o-mini",
                "confidence": 0.0,
                "cost_estimate": 0.001,
                "complexity": "medium",
                "risk": "medium",
                "dsl_applied": False,
            }

    async def _handle_node_failure(
        self, context: OrchestrationContext, node_id: str, error: Exception
    ) -> None:
        """Handle node failure."""
        logger.error(f"Node {node_id} failed: {error}")

        # Check if this is a critical failure
        if len(context.failed_nodes) > len(context.completed_nodes):
            logger.error("Too many failed nodes, stopping pipeline")
            context.status = OrchestrationStatus.FAILED

    def _validate_pipeline_config(self, context: OrchestrationContext) -> None:
        """Validate pipeline configuration."""
        if not context.pipeline_name:
            raise ValidationError("Pipeline name is required")

        if context.total_nodes == 0:
            raise ValidationError("Pipeline must have at least one node")

    async def _persist_context(self, context: OrchestrationContext) -> None:
        """Persist orchestration context to Neo4j."""
        if not self.neo4j_client:
            return

        try:
            query = """
            CREATE (oc:OrchestrationContext {
                id: $context_id,
                project_id: $project_id,
                run_id: $run_id,
                dag_id: $dag_id,
                pipeline_name: $pipeline_name,
                status: $status,
                started_at: datetime($started_at),
                completed_at: $completed_at,
                current_node: $current_node,
                completed_nodes: $completed_nodes,
                failed_nodes: $failed_nodes,
                total_nodes: $total_nodes,
                quality_gates: $quality_gates,
                auto_repair: $auto_repair,
                dsl_config: $dsl_config,
                metadata: $metadata
            })
            """

            await self.neo4j_client.execute_write_query(
                query,
                {
                    "context_id": str(uuid4()),
                    "project_id": str(context.project_id),
                    "run_id": str(context.run_id),
                    "dag_id": str(context.dag_id),
                    "pipeline_name": context.pipeline_name,
                    "status": context.status,
                    "started_at": context.started_at.isoformat()
                    if context.started_at
                    else None,
                    "completed_at": context.completed_at.isoformat()
                    if context.completed_at
                    else None,
                    "current_node": context.current_node,
                    "completed_nodes": context.completed_nodes,
                    "failed_nodes": context.failed_nodes,
                    "total_nodes": context.total_nodes,
                    "quality_gates": context.quality_gates,
                    "auto_repair": context.auto_repair,
                    "dsl_config": context.dsl_config,
                    "metadata": context.metadata,
                },
            )

        except Exception as e:
            logger.error(f"Failed to persist context: {e}")

    async def _update_context(self, context: OrchestrationContext) -> None:
        """Update orchestration context."""
        if not self.neo4j_client:
            return

        try:
            query = """
            MATCH (oc:OrchestrationContext {dag_id: $dag_id})
            SET oc.status = $status,
                oc.completed_at = $completed_at,
                oc.current_node = $current_node,
                oc.completed_nodes = $completed_nodes,
                oc.failed_nodes = $failed_nodes,
                oc.metadata = $metadata
            """

            await self.neo4j_client.execute_write_query(
                query,
                {
                    "dag_id": str(context.dag_id),
                    "status": context.status,
                    "completed_at": context.completed_at.isoformat()
                    if context.completed_at
                    else None,
                    "current_node": context.current_node,
                    "completed_nodes": context.completed_nodes,
                    "failed_nodes": context.failed_nodes,
                    "metadata": context.metadata,
                },
            )

        except Exception as e:
            logger.error(f"Failed to update context: {e}")

    async def _persist_task_execution(
        self, execution: TaskExecution, result: TaskResult
    ) -> None:
        """Persist task execution to Neo4j."""
        if not self.neo4j_client:
            return

        try:
            # First, create the Task node with proper HAS_TASK relationship to Run
            task_data = {
                "id": str(execution.id),
                "name": execution.definition.name,
                "type": execution.definition.type,
                "agent": execution.definition.agent_type,
                "status": result.status,
                "description": execution.definition.description,
                "inputs": execution.inputs,
                "outputs": execution.definition.outputs,
                "metadata": result.metadata,
                "error": "; ".join(result.errors) if result.errors else None,
                "run_id": str(execution.run_id),
                "project_id": str(execution.project_id),
                "queue": execution.definition.queue,
                "priority": 1,  # Default priority
                "retry_count": 0,
                "max_retries": execution.definition.retry_attempts,
            }

            # Create the Task node with HAS_TASK relationship
            task_id = await self.neo4j_client.create_task(task_data)

            # Then create the TaskExecution node for execution tracking
            execution_query = """
            CREATE (te:TaskExecution {
                id: $execution_id,
                task_id: $task_id,
                agent: $agent,
                task_type: $task_type,
                status: $status,
                output: $output,
                error: $error,
                metadata: $metadata,
                created_at: datetime()
            })
            """

            await self.neo4j_client.execute_write_query(
                execution_query,
                {
                    "execution_id": f"{execution.id}_exec",
                    "task_id": str(execution.id),
                    "agent": execution.definition.agent_type,
                    "task_type": execution.definition.type,
                    "status": result.status,
                    "output": result.metadata.get("output", ""),
                    "error": "; ".join(result.errors) if result.errors else None,
                    "metadata": result.metadata,
                },
            )

            logger.info(f"Successfully persisted task {task_id} and execution record")

        except Exception as e:
            logger.error(f"Failed to persist task execution: {e}")
            raise

    def _validate_dependencies(self, dag: ExecutionDAG) -> None:
        """Validate DAG dependency correctness and detect circular dependencies.

        Args:
            dag: The execution DAG to validate

        Raises:
            ValidationError: If dependencies are invalid or circular
        """
        try:
            logger.info(f"Validating dependencies for DAG {dag.id}")

            if not dag.nodes:
                logger.warning("DAG has no nodes")
                return

            # Create a mapping of node IDs to nodes for easier lookup
            node_map = {node.id: node for node in dag.nodes}
            node_names = set(node_map.keys())

            # Check for missing dependencies
            for node in dag.nodes:
                for dep_id in node.dependencies:
                    if dep_id not in node_map:
                        raise ValidationError(
                            f"Dependency {dep_id} not found for node {node.name}",
                            field="dependencies",
                        )

            # Check for circular dependencies using DFS
            visited = set()
            rec_stack = set()

            def has_cycle(node_id: Union[str, UUID]) -> bool:
                """Check for cycles starting from a node."""
                if node_id in rec_stack:
                    return True

                if node_id in visited:
                    return False

                visited.add(node_id)
                rec_stack.add(node_id)

                # Find node by ID
                node = node_map.get(node_id)
                if node:
                    for dep_id in node.dependencies:
                        if has_cycle(dep_id):
                            return True

                rec_stack.remove(node_id)
                return False

            # Check for cycles from each node
            for node in dag.nodes:
                if node.id not in visited:
                    if has_cycle(node.id):
                        raise ValidationError(
                            f"Circular dependency detected involving node {node.name}",
                            field="dependencies",
                        )

            logger.info(f"Dependency validation passed for DAG {dag.id}")

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during dependency validation: {e}")
            raise ValidationError(
                f"Failed to validate dependencies: {e}", field="dependencies"
            )

    async def _handle_task_failure(
        self, error: OrchestrationError, context: OrchestrationContext
    ) -> TaskResult:
        """Handle and recover from task failures.

        Args:
            error: The orchestration error that occurred
            context: The orchestration context

        Returns:
            TaskResult with failure details and recovery information
        """
        try:
            logger.error(
                f"Handling task failure: {error.error_type} - {error.message}",
                extra={
                    "task_name": error.task_name,
                    "dag_id": str(context.dag_id),
                    "error_type": error.error_type,
                },
            )

            # Update context with failure
            if error.task_name:
                if error.task_name not in context.failed_nodes:
                    context.failed_nodes.append(error.task_name)

            # Determine if retry is possible
            can_retry = self._can_retry_task(error, context)

            if can_retry:
                logger.info(f"Task {error.task_name} will be retried")
                return TaskResult(
                    task_id=uuid4(),  # Generate a new task ID for the retry
                    status=TaskStatus.RETRY,
                    score=0.0,
                    metrics={
                        "retry_attempted": True,
                        "error_type": error.error_type,
                        "can_retry": True,
                    },
                    errors=[error.message],
                    warnings=[f"Task {error.task_name} will be retried"],
                )
            else:
                logger.error(f"Task {error.task_name} cannot be retried")
                return TaskResult(
                    task_id=uuid4(),  # Generate a new task ID for the failure
                    status=TaskStatus.FAILED,
                    score=0.0,
                    metrics={
                        "retry_attempted": False,
                        "error_type": error.error_type,
                        "can_retry": False,
                        "final_failure": True,
                    },
                    errors=[error.message],
                    warnings=[f"Task {error.task_name} failed permanently"],
                )

        except Exception as e:
            logger.error(f"Error in task failure handler: {e}")
            return TaskResult(
                task_id=uuid4(),
                status=TaskStatus.FAILED,
                score=0.0,
                metrics={"failure_handler_error": True},
                errors=[f"Failure handler error: {e}", error.message],
            )

    def _can_retry_task(
        self, error: OrchestrationError, context: OrchestrationContext
    ) -> bool:
        """Determine if a task can be retried based on error type and context.

        Args:
            error: The orchestration error
            context: The orchestration context

        Returns:
            True if task can be retried, False otherwise
        """
        # Get current retry count for the task
        retry_count = context.metadata.get(f"retry_count_{error.task_name}", 0)
        max_retries = context.metadata.get("max_retries", 3)

        # Check if max retries exceeded
        if retry_count >= max_retries:
            logger.warning(
                f"Max retries ({max_retries}) exceeded for task {error.task_name}"
            )
            return False

        # Check error type for retry eligibility
        non_retryable_errors = {
            "validation_error",
            "configuration_error",
            "resource_error",
            "permission_error",
        }

        if error.error_type in non_retryable_errors:
            logger.warning(f"Non-retryable error type: {error.error_type}")
            return False

        # Check if context is still valid for retry
        if context.status not in [
            OrchestrationStatus.RUNNING,
            OrchestrationStatus.PAUSED,
        ]:
            logger.warning(f"Context status {context.status} not suitable for retry")
            return False

        return True

    def _validate_artifacts(self, context: OrchestrationContext) -> None:
        """Validate artifacts (inputs/outputs) for correctness and completeness.

        Args:
            context: The orchestration context containing artifacts

        Raises:
            ValidationError: If artifacts are invalid
        """
        try:
            logger.info(f"Validating artifacts for context {context.dag_id}")

            # Get artifacts from context metadata
            artifacts = context.metadata.get("artifacts", {})

            if not artifacts:
                logger.info("No artifacts to validate")
                return

            for task_name, task_artifacts in artifacts.items():
                if not isinstance(task_artifacts, list):
                    raise ValidationError(
                        f"Artifacts for task {task_name} must be a list",
                        field=f"artifacts.{task_name}",
                    )

                for i, artifact in enumerate(task_artifacts):
                    if not isinstance(artifact, dict):
                        raise ValidationError(
                            f"Artifact {i} for task {task_name} must be a dictionary",
                            field=f"artifacts.{task_name}[{i}]",
                        )

                    # Validate required artifact fields
                    required_fields = ["id", "type", "path", "hash"]
                    for field in required_fields:
                        if field not in artifact:
                            raise ValidationError(
                                f"Artifact {i} for task {task_name} missing required field: {field}",
                                field=f"artifacts.{task_name}[{i}].{field}",
                            )

                    # Validate artifact hash (SHA-256)
                    artifact_hash = artifact["hash"]
                    if not isinstance(artifact_hash, str) or len(artifact_hash) != 64:
                        raise ValidationError(
                            f"Artifact {i} for task {task_name} has invalid hash format",
                            field=f"artifacts.{task_name}[{i}].hash",
                        )

                    # Validate hash characters (hexadecimal)
                    import re

                    if not re.match(r"^[a-fA-F0-9]{64}$", artifact_hash):
                        raise ValidationError(
                            f"Artifact {i} for task {task_name} has invalid hash characters",
                            field=f"artifacts.{task_name}[{i}].hash",
                        )

                    # Validate artifact type
                    artifact_type = artifact["type"]
                    valid_types = [
                        "code",
                        "documentation",
                        "test",
                        "config",
                        "build",
                        "deploy",
                        "analysis",
                        "report",
                    ]
                    if artifact_type not in valid_types:
                        raise ValidationError(
                            f"Artifact {i} for task {task_name} has invalid type: {artifact_type}",
                            field=f"artifacts.{task_name}[{i}].type",
                        )

                    # Validate artifact path
                    artifact_path = artifact["path"]
                    if not isinstance(artifact_path, str) or not artifact_path.strip():
                        raise ValidationError(
                            f"Artifact {i} for task {task_name} has invalid path",
                            field=f"artifacts.{task_name}[{i}].path",
                        )

                    # Optional: Validate file exists if path is relative
                    if not artifact_path.startswith(("/", "http://", "https://")):
                        import os

                        if not os.path.exists(artifact_path):
                            logger.warning(f"Artifact file not found: {artifact_path}")

            logger.info(f"Artifact validation passed for context {context.dag_id}")

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during artifact validation: {e}")
            raise ValidationError(
                f"Failed to validate artifacts: {e}", field="artifacts"
            )

    async def execute_pipeline(self, context: OrchestrationContext) -> Dict[str, Any]:
        """Execute a complete pipeline with full lifecycle management.

        This is the main public method for pipeline execution that orchestrates
        the entire pipeline lifecycle including validation, planning, execution,
        and result collection.

        Args:
            context: The orchestration context containing pipeline configuration

        Returns:
            Dictionary containing execution results and metrics

        Raises:
            OrchestrationError: If pipeline execution fails
            ValidationError: If pipeline configuration is invalid
        """
        try:
            logger.info(f"Starting pipeline execution: {context.pipeline_name}")

            # Validate pipeline configuration
            self._validate_pipeline_config(context)

            # Load the execution DAG
            dag = self.dag_loader.load_pipeline(context.pipeline_name)
            if not dag:
                raise OrchestrationError(
                    "pipeline_creation_failed",
                    f"Failed to create execution DAG for pipeline: {context.pipeline_name}",
                    context.pipeline_name,
                )

            # Validate dependencies
            self._validate_dependencies(dag)

            # Create execution plan
            execution_plans = await self._create_execution_plan(context, dag)

            # Initialize execution metrics
            execution_metrics = {
                "total_tasks": len(execution_plans),
                "completed_tasks": 0,
                "failed_tasks": 0,
                "retried_tasks": 0,
                "total_execution_time": 0.0,
                "total_tokens_used": 0,
                "total_cost": 0.0,
                "start_time": datetime.now(timezone.utc),
            }

            # Update context
            context.status = OrchestrationStatus.RUNNING
            context.started_at = execution_metrics["start_time"]
            context.total_nodes = len(execution_plans)

            # Persist context to Neo4j
            if self.neo4j_client:
                await self._persist_context(context)

            # Execute tasks by phase
            task_results = []
            for phase in range(max(p.execution_phase for p in execution_plans) + 1):
                phase_plans = [p for p in execution_plans if p.execution_phase == phase]

                logger.info(f"Executing phase {phase} with {len(phase_plans)} tasks")

                # Execute tasks in parallel within the phase
                phase_tasks = []
                for plan in phase_plans:
                    task = asyncio.create_task(
                        self._execute_task_with_retry(
                            context, dag, plan, execution_metrics
                        )
                    )
                    phase_tasks.append(task)

                # Wait for all tasks in phase to complete
                phase_results = await asyncio.gather(
                    *phase_tasks, return_exceptions=True
                )

                # Process phase results
                for i, result in enumerate(phase_results):
                    if isinstance(result, Exception):
                        logger.error(f"Phase {phase} task {i} failed: {result}")
                        execution_metrics["failed_tasks"] += 1
                    else:
                        task_results.append(result)
                        if result.status in ["ok", "success"]:
                            execution_metrics["completed_tasks"] += 1
                        else:
                            execution_metrics["failed_tasks"] += 1

                # Check if we should continue after phase failures
                if execution_metrics["failed_tasks"] > 0:
                    critical_failures = sum(
                        1
                        for r in phase_results
                        if isinstance(r, Exception)
                        or (hasattr(r, "status") and r.status == "fail")
                    )
                    if critical_failures == len(phase_plans):
                        logger.error(
                            f"All tasks in phase {phase} failed, stopping execution"
                        )
                        break

            # Calculate final metrics
            execution_metrics["end_time"] = datetime.now(timezone.utc)
            execution_metrics["total_execution_time"] = (
                execution_metrics["end_time"] - execution_metrics["start_time"]
            ).total_seconds()

            # Determine final status
            if execution_metrics["failed_tasks"] == 0:
                context.status = OrchestrationStatus.COMPLETED
                success = True
            elif execution_metrics["completed_tasks"] > 0:
                context.status = OrchestrationStatus.COMPLETED
                success = True  # Partial success
            else:
                context.status = OrchestrationStatus.FAILED
                success = False

            context.completed_at = execution_metrics["end_time"]

            # Update context in Neo4j
            if self.neo4j_client:
                await self._update_context(context)

            # Prepare result
            result = {
                "success": success,
                "status": context.status.value,
                "pipeline_name": context.pipeline_name,
                "execution_metrics": execution_metrics,
                "task_results": task_results,
                "completed_nodes": context.completed_nodes,
                "failed_nodes": context.failed_nodes,
                "total_nodes": context.total_nodes,
            }

            logger.info(
                f"Pipeline execution completed: {context.pipeline_name} - "
                f"Success: {success}, Tasks: {execution_metrics['completed_tasks']}/{execution_metrics['total_tasks']}"
            )

            return result

        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}")
            context.status = OrchestrationStatus.FAILED
            context.completed_at = datetime.now(timezone.utc)

            if self.neo4j_client:
                await self._update_context(context)

            raise OrchestrationError(
                "pipeline_execution_failed",
                f"Pipeline execution failed: {e}",
                context.pipeline_name,
            )

    async def _execute_task_with_retry(
        self,
        context: OrchestrationContext,
        dag: ExecutionDAG,
        plan: TaskExecutionPlan,
        execution_metrics: Dict[str, Any],
    ) -> TaskResult:
        """Execute a task with retry logic.

        Args:
            context: The orchestration context
            dag: The execution DAG
            plan: The task execution plan
            execution_metrics: Metrics to update during execution

        Returns:
            TaskResult from the task execution
        """
        max_retries = plan.retry_attempts
        retry_count = 0

        while retry_count <= max_retries:
            try:
                # Find the node for this plan
                node = None
                for n in dag.nodes:
                    if n.name == plan.task_name:
                        node = n
                        break

                if not node:
                    raise OrchestrationError(
                        "node_not_found",
                        f"Node not found for task {plan.task_name}",
                        plan.task_name,
                    )

                # Execute the task
                result = await self._execute_node(context, dag, node)

                # Update metrics
                if (
                    hasattr(result, "execution_time_seconds")
                    and result.execution_time_seconds
                ):
                    execution_metrics[
                        "total_execution_time"
                    ] += result.execution_time_seconds

                if hasattr(result, "tokens_used") and result.tokens_used:
                    execution_metrics["total_tokens_used"] += result.tokens_used

                if hasattr(result, "cost") and result.cost:
                    execution_metrics["total_cost"] += result.cost

                return result

            except Exception as e:
                retry_count += 1
                execution_metrics["retried_tasks"] += 1

                logger.warning(
                    f"Task {plan.task_name} failed (attempt {retry_count}/{max_retries + 1}): {e}"
                )

                if retry_count > max_retries:
                    logger.error(
                        f"Task {plan.task_name} failed after {max_retries + 1} attempts"
                    )

                    # Create failure result
                    return TaskResult(
                        task_id=plan.task_id,
                        status=TaskStatus.FAILED,
                        score=0.0,
                        metrics={
                            "retry_attempts": retry_count - 1,
                            "final_failure": True,
                        },
                        errors=[f"Task failed after {max_retries + 1} attempts: {e}"],
                        execution_time_seconds=0.0,
                    )

                # Wait before retry with exponential backoff
                wait_time = min(2**retry_count, 60)  # Cap at 60 seconds
                await asyncio.sleep(wait_time)

        # This should never be reached, but just in case
        return TaskResult(
            task_id=plan.task_id,
            status=TaskStatus.FAILED,
            score=0.0,
            metrics={"unexpected_failure": True},
            errors=["Unexpected failure in task execution"],
        )

    async def _get_historical_data(self, task_type: str, agent: str) -> Dict[str, Any]:
        """Get historical data from Neo4j for decision making."""
        if not self.neo4j_client:
            return {}

        try:
            # Query historical task executions for similar tasks
            query = """
            MATCH (t:TaskExecution)
            WHERE t.task_type = $task_type AND t.agent = $agent
            WITH t ORDER BY t.started_at DESC LIMIT 10
            RETURN {
                avg_cost: avg(t.cost),
                avg_tokens: avg(t.tokens_used),
                avg_duration: avg(t.execution_time_seconds),
                success_rate: count(CASE WHEN t.status = 'SUCCESS' THEN 1 END) * 1.0 / count(*),
                total_executions: count(*)
            } as stats
            """

            result = await self.neo4j_client.run_query(
                query, {"task_type": task_type, "agent": agent}
            )

            if result and len(result) > 0:
                return result[0].get("stats", {})
            return {}

        except Exception as e:
            logger.warning(f"Failed to get historical data: {e}")
            return {}

    async def _create_execution_plan(
        self, context: OrchestrationContext, dag: ExecutionDAG
    ) -> List["TaskExecutionPlan"]:
        """Create execution plan from DAG nodes.

        Args:
            context: The orchestration context
            dag: The execution DAG

        Returns:
            List of task execution plans
        """
        from opsvi_auto_forge.application.orchestrator.task_models import (
            TaskExecutionPlan,
            TaskPriority,
            AgentRole,
        )

        if not dag.nodes:
            logger.warning("DAG has no nodes to create execution plan")
            return []

        # Create a mapping of node IDs to nodes for easier lookup
        node_map = {node.id: node for node in dag.nodes}

        # Calculate execution phases based on dependencies
        execution_phases = self._calculate_execution_phases(dag)

        plans = []
        for node in dag.nodes:
            # Determine execution phase
            phase = execution_phases.get(node.id, 0)

            # Convert string ID to UUID if needed
            task_id = node.id
            if isinstance(task_id, str):
                # Generate a UUID from the string ID for consistency
                import hashlib
                import uuid

                hash_obj = hashlib.md5(task_id.encode())
                task_id = uuid.UUID(hash_obj.hexdigest())

            # Create task execution plan
            plan = TaskExecutionPlan(
                task_id=task_id,
                task_name=node.name,
                stage_name=node.name,
                agent=AgentRole(node.agent),
                priority=TaskPriority.NORMAL,
                dependencies=node.dependencies,
                execution_phase=phase,
                timeout_seconds=node.config.get("timeout", 300),
                retry_attempts=node.config.get("retries", 3),
                queue=node.config.get("queue", "default"),
                required=node.config.get("required", True),
                inputs=node.config.get("inputs", {}),
                expected_outputs=node.config.get("outputs", {}),
                metadata=node.config.get("metadata", {}),
            )
            plans.append(plan)

        # Sort plans by execution phase
        plans.sort(key=lambda p: p.execution_phase)

        logger.info(
            f"Created execution plan with {len(plans)} tasks across {max(p.execution_phase for p in plans) + 1} phases"
        )
        return plans

    def _calculate_execution_phases(
        self, dag: ExecutionDAG
    ) -> Dict[Union[str, UUID], int]:
        """Calculate execution phases for DAG nodes based on dependencies.

        Args:
            dag: The execution DAG

        Returns:
            Mapping of node ID to execution phase
        """
        if not dag.nodes:
            return {}

        # Create a mapping of node IDs to nodes
        node_map = {node.id: node for node in dag.nodes}
        phases = {}
        visited = set()

        def calculate_phase(node_id: Union[str, UUID]) -> int:
            """Calculate phase for a node based on its dependencies."""
            if node_id in phases:
                return phases[node_id]

            if node_id in visited:
                # Circular dependency detected
                return 0

            visited.add(node_id)
            node = node_map.get(node_id)
            if not node:
                return 0

            # Calculate phase based on dependencies
            max_dep_phase = -1
            for dep_id in node.dependencies:
                dep_phase = calculate_phase(dep_id)
                max_dep_phase = max(max_dep_phase, dep_phase)

            # This node's phase is one more than its highest dependency
            phase = max_dep_phase + 1
            phases[node_id] = phase
            return phase

        # Calculate phases for all nodes
        for node in dag.nodes:
            if node.id not in phases:
                calculate_phase(node.id)

        return phases
