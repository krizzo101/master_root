"""Model router for agent task execution."""

import logging
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID
import json
from pathlib import Path

from pydantic import BaseModel, Field, field_validator, ConfigDict

from opsvi_auto_forge.config.models import AgentRole
from opsvi_auto_forge.infrastructure.memory.graph.client import Neo4jClient
from opsvi_auto_forge.infrastructure.monitoring.metrics.decision_metrics import (
    decision_success,
    decision_failure,
    dk_decision_confidence_bucket,
    router_escalations_total,
)

# TaskType enum values for routing

logger = logging.getLogger(__name__)


class ModelProvider(str, Enum):
    """Supported model providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class ModelConfig(BaseModel):
    """Configuration for a specific model."""

    provider: ModelProvider
    model: str
    temperature: float = Field(0.1, ge=0.0, le=2.0)
    max_tokens: int = Field(4000, gt=0)
    top_p: float = Field(1.0, ge=0.0, le=1.0)
    frequency_penalty: float = Field(0.0, ge=-2.0, le=2.0)
    presence_penalty: float = Field(0.0, ge=-2.0, le=2.0)
    stop_sequences: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(use_enum_values=True)

    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        """Validate temperature is between 0 and 2."""
        if not 0.0 <= v <= 2.0:
            raise ValueError("Temperature must be between 0 and 2")
        return v

    @field_validator("max_tokens")
    @classmethod
    def validate_max_tokens(cls, v: int) -> int:
        """Validate max tokens is positive."""
        if v <= 0:
            raise ValueError("Max tokens must be positive")
        return v


class TaskSpec(BaseModel):
    """Specification for a task to be executed."""

    id: str
    name: str
    agent: str  # "ResearcherAgent" | "CoderAgent" | "CriticAgent" | ...
    inputs_json: str
    depends_on: List[str] = Field(default_factory=list)
    queue: str = "default"
    budget_tokens: Optional[int] = None


class ExecutionPlan(BaseModel):
    """Execution plan for a run."""

    run_id: str
    tasks: List[TaskSpec]  # topologically sorted or with dep graph
    graph: Dict[str, List[str]] = Field(default_factory=dict)  # task_id -> children


class Manager:
    """Manager for orchestrating task execution."""

    def __init__(self, neo4j_client: Optional[Neo4jClient] = None):
        """Initialize the manager."""
        self.neo4j_client = neo4j_client or Neo4jClient()
        self.router = ModelRouter(neo4j_client)

    async def plan_run(
        self,
        project: Dict[str, Any],
        goal: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> ExecutionPlan:
        """Create an execution plan for a run."""
        from uuid import uuid4

        run_id = str(uuid4())

        # Minimal plan: Researcher → Coder → Critic → (optional) Fix Loop → Finalize
        tasks = [
            TaskSpec(
                id=f"{run_id}_researcher",
                name="Research Requirements",
                agent="ResearcherAgent",
                inputs_json=json.dumps({"goal": goal, "project": project}),
            ),
            TaskSpec(
                id=f"{run_id}_coder",
                name="Implement Solution",
                agent="CoderAgent",
                inputs_json=json.dumps({"goal": goal, "project": project}),
                depends_on=[f"{run_id}_researcher"],
            ),
            TaskSpec(
                id=f"{run_id}_critic",
                name="Review and Validate",
                agent="CriticAgent",
                inputs_json=json.dumps({"goal": goal, "project": project}),
                depends_on=[f"{run_id}_coder"],
            ),
        ]

        return ExecutionPlan(run_id=run_id, tasks=tasks)

    async def submit_plan(self, plan: ExecutionPlan) -> None:
        """Submit an execution plan for processing."""
        try:
            # Submit tasks to Celery for execution
            for task in plan.tasks:
                await self._submit_task_to_celery(task)

            logger.info(
                f"Submitted execution plan: {plan.run_id} with {len(plan.tasks)} tasks"
            )

        except Exception as e:
            logger.error(f"Failed to submit execution plan {plan.run_id}: {e}")
            raise TaskRoutingError(f"Plan submission failed: {e}")

    async def handle_task_result(self, task_id: str, result: Dict[str, Any]) -> None:
        """Handle a task result."""
        try:
            # Process task result and update graph
            await self._process_task_result(task_id, result)
            await self._update_task_graph(task_id, result)

            logger.info(f"Handled task result: {task_id}")

        except Exception as e:
            logger.error(f"Failed to handle task result {task_id}: {e}")
            raise TaskRoutingError(f"Task result handling failed: {e}")

    async def complete_run(self, run_id: str, status: str, summary: str) -> None:
        """Complete a run with final status."""
        try:
            # Update run status and persist results
            await self._update_run_status(run_id, status, summary)
            await self._persist_run_results(run_id, status, summary)

            logger.info(f"Completed run: {run_id} with status: {status}")

        except Exception as e:
            logger.error(f"Failed to complete run {run_id}: {e}")
            raise TaskRoutingError(f"Run completion failed: {e}")

    async def _submit_task_to_celery(self, task: TaskSpec) -> None:
        """Submit a task to Celery for execution."""
        try:
            from opsvi_auto_forge.infrastructure.workers.agent_tasks import (
                submit_agent_task,
            )

            # Submit task to Celery
            celery_task = submit_agent_task(
                agent_type=task.agent,
                task_execution_data={"inputs_json": task.inputs_json},
                queue=task.queue,
            )

            logger.debug(f"Submitted task {task.id} to Celery: {celery_task.id}")

        except Exception as e:
            logger.error(f"Failed to submit task {task.id} to Celery: {e}")
            raise

    async def _process_task_result(self, task_id: str, result: Dict[str, Any]) -> None:
        """Process task result and update Neo4j."""
        try:
            # Update task node in Neo4j
            query = """
            MATCH (t:Task {id: $task_id})
            SET t.status = $status,
                t.result = $result,
                t.completed_at = datetime(),
                t.execution_time = $execution_time
            """

            await self.neo4j_client.run_query(
                query,
                {
                    "task_id": task_id,
                    "status": result.get("status", "completed"),
                    "result": json.dumps(result),
                    "execution_time": result.get("execution_time", 0),
                },
            )

        except Exception as e:
            logger.error(f"Failed to process task result for {task_id}: {e}")
            raise

    async def _update_task_graph(self, task_id: str, result: Dict[str, Any]) -> None:
        """Update task graph relationships in Neo4j."""
        try:
            # Get child task IDs from result
            child_task_ids = result.get("child_tasks", [])

            if child_task_ids:
                # Create PARENT_OF relationships
                query = """
                MATCH (parent:Task {id: $parent_id})
                MATCH (child:Task)
                WHERE child.id IN $child_ids
                MERGE (parent)-[:PARENT_OF]->(child)
                """

                await self.neo4j_client.run_query(
                    query, {"parent_id": task_id, "child_ids": child_task_ids}
                )

                logger.debug(
                    f"Updated task graph for {task_id} with {len(child_task_ids)} children"
                )

        except Exception as e:
            logger.error(f"Failed to update task graph for {task_id}: {e}")
            raise

    async def _update_run_status(self, run_id: str, status: str, summary: str) -> None:
        """Update run status in Neo4j."""
        try:
            query = """
            MATCH (r:Run {id: $run_id})
            SET r.status = $status,
                r.summary = $summary,
                r.completed_at = datetime()
            """

            await self.neo4j_client.run_query(
                query, {"run_id": run_id, "status": status, "summary": summary}
            )

        except Exception as e:
            logger.error(f"Failed to update run status for {run_id}: {e}")
            raise

    async def _persist_run_results(
        self, run_id: str, status: str, summary: str
    ) -> None:
        """Persist run results to storage."""
        try:
            # Store results in Neo4j or external storage
            query = """
            MATCH (r:Run {id: $run_id})
            CREATE (result:RunResult {
                run_id: $run_id,
                status: $status,
                summary: $summary,
                created_at: datetime()
            })
            MERGE (r)-[:HAS_RESULT]->(result)
            """

            await self.neo4j_client.run_query(
                query, {"run_id": run_id, "status": status, "summary": summary}
            )

        except Exception as e:
            logger.error(f"Failed to persist run results for {run_id}: {e}")
            raise


class RoutingRule(BaseModel):
    """Rule for model routing."""

    name: str
    description: str
    agent_role: Optional[AgentRole] = None
    task_type: Optional[str] = None
    complexity: Optional[str] = None  # low, medium, high
    priority: int = Field(0, ge=0)
    ai_model_config: ModelConfig
    enabled: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(use_enum_values=True)


class RoutingDecision(BaseModel):
    """Decision made by the router."""

    task_id: UUID
    agent_role: AgentRole
    task_type: str
    selected_model: ModelConfig
    routing_rule: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str
    alternatives: List[ModelConfig] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(use_enum_values=True)

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        """Validate confidence is between 0 and 1."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Confidence must be between 0 and 1")
        return v


class ModelRouter:
    """Router for selecting models based on task characteristics."""

    def __init__(self, neo4j_client: Optional[Neo4jClient] = None):
        """Initialize the router."""
        self.neo4j_client = neo4j_client or Neo4jClient()
        self.rules: List[RoutingRule] = []
        self.priors_path = Path("state/router_priors.json")
        self.priors = self._load_priors()
        self._load_default_rules()

    def _load_priors(self) -> Dict[str, Any]:
        """Load model performance priors from benchmark results."""
        try:
            # Try to load from benchmark priors first
            benchmark_priors_path = Path("state/router_priors.json")
            if benchmark_priors_path.exists():
                benchmark_priors = json.loads(benchmark_priors_path.read_text())
                logger.info(
                    f"Loaded benchmark priors with {len(benchmark_priors.get('models', {}))} models"
                )
                return benchmark_priors

            # Fallback to local priors
            if self.priors_path.exists():
                return json.loads(self.priors_path.read_text())
            else:
                return {
                    "models": {},
                    "strategies": {},
                    "benchmarks": {},
                    "updated": None,
                }
        except Exception as e:
            logger.warning(f"Failed to load priors: {e}")
            return {"models": {}, "strategies": {}, "benchmarks": {}, "updated": None}

    def _save_priors(self) -> None:
        """Save model performance priors."""
        try:
            self.priors["updated"] = "2025-07-28T18:28:40.998913"
            self.priors_path.parent.mkdir(parents=True, exist_ok=True)
            self.priors_path.write_text(json.dumps(self.priors, indent=2))
        except Exception as e:
            logger.warning(f"Failed to save priors: {e}")

    def update_priors(
        self, model: str, success: bool, cost: float, latency_ms: int
    ) -> None:
        """Update model performance priors."""
        if model not in self.priors["models"]:
            self.priors["models"][model] = {
                "success": 0,
                "fail": 0,
                "cost_sum": 0.0,
                "latency_sum": 0.0,
            }

        m = self.priors["models"][model]
        m["success"] += 1 if success else 0
        m["fail"] += 0 if success else 1
        m["cost_sum"] += float(cost)
        m["latency_sum"] += float(latency_ms)

        self._save_priors()

    def _load_default_rules(self) -> None:
        """Load default routing rules."""
        self.rules = [
            RoutingRule(
                name="default_o4_mini",
                description="Default rule for simple tasks",
                ai_model_config=ModelConfig(
                    provider=ModelProvider.ANTHROPIC,
                    model="o4-mini",
                    temperature=0.1,
                    max_tokens=4000,
                ),
                priority=0,
            ),
            RoutingRule(
                name="complex_gpt4",
                description="Rule for complex tasks",
                complexity="high",
                ai_model_config=ModelConfig(
                    provider=ModelProvider.OPENAI,
                    model="gpt-4o",
                    temperature=0.1,
                    max_tokens=4000,
                ),
                priority=10,
            ),
            RoutingRule(
                name="critical_o3",
                description="Rule for critical tasks",
                complexity="high",
                ai_model_config=ModelConfig(
                    provider=ModelProvider.ANTHROPIC,
                    model="o3",
                    temperature=0.1,
                    max_tokens=4000,
                ),
                priority=20,
            ),
        ]

    async def route_task(
        self,
        task_id: UUID,
        agent_role: AgentRole,
        task_type: str,
        context: Dict[str, Any],
        budget_hint: Optional[Dict[str, Any]] = None,
        escalation_enabled: bool = True,
    ) -> RoutingDecision:
        """Route a task to an appropriate model with escalation support."""

        # Get initial routing decision
        initial_decision = await self._route_initial(
            task_id, agent_role, task_type, context
        )

        # Check if escalation is needed
        if escalation_enabled and self._should_escalate(
            initial_decision, context, budget_hint
        ):
            escalated_decision = await self._escalate_decision(
                initial_decision, context, budget_hint
            )
            return escalated_decision

        return initial_decision

    async def _route_initial(
        self,
        task_id: UUID,
        agent_role: AgentRole,
        task_type: str,
        context: Dict[str, Any],
    ) -> RoutingDecision:
        """Make initial routing decision."""

        # Find matching rules
        matching_rules = self._find_matching_rules(agent_role, task_type, context)

        if not matching_rules:
            # Use default rule
            default_rule = next(r for r in self.rules if r.name == "default_o4_mini")
            confidence = 0.5
            reasoning = "No specific rules matched, using default"
        else:
            # Select best rule based on priority and priors
            best_rule = self._select_best_rule(matching_rules, context)
            confidence = self._calculate_confidence(
                best_rule, agent_role, task_type, context
            )
            reasoning = (
                f"Selected rule: {best_rule.name} (priority: {best_rule.priority})"
            )

        return RoutingDecision(
            task_id=task_id,
            agent_role=agent_role,
            task_type=task_type,
            selected_model=best_rule.ai_model_config,
            routing_rule=best_rule.name,
            confidence=confidence,
            reasoning=reasoning,
            alternatives=[r.ai_model_config for r in matching_rules[:3]],
        )

    def _should_escalate(
        self,
        decision: RoutingDecision,
        context: Dict[str, Any],
        budget_hint: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Determine if escalation is needed."""

        # Check budget constraints
        if budget_hint:
            max_cost = budget_hint.get("max_cost_usd", 1.0)
            if decision.selected_model.model == "o3" and max_cost < 0.5:
                return False  # Too expensive for budget

        # Check complexity-based escalation
        complexity = context.get("complexity", 0.0)
        if complexity > 0.7 and decision.selected_model.model in ["o4-mini", "gpt-4o"]:
            return True

        # Check risk-based escalation
        risk = context.get("risk", 0.0)
        if risk > 0.6 and decision.selected_model.model in ["o4-mini"]:
            return True

        # Check confidence-based escalation
        if decision.confidence < 0.7:
            return True

        return False

    async def _escalate_decision(
        self,
        initial_decision: RoutingDecision,
        context: Dict[str, Any],
        budget_hint: Optional[Dict[str, Any]] = None,
    ) -> RoutingDecision:
        """Escalate to a more capable model."""

        current_model = initial_decision.selected_model.model
        escalation_path = ["o4-mini", "gpt-4o", "o3"]

        try:
            current_index = escalation_path.index(current_model)
            next_index = min(current_index + 1, len(escalation_path) - 1)
            escalated_model = escalation_path[next_index]

            # Check budget constraints
            if budget_hint:
                max_cost = budget_hint.get("max_cost_usd", 1.0)
                if escalated_model == "o3" and max_cost < 0.5:
                    # Can't escalate to o3, stay with current
                    logger.warning(
                        f"Cannot escalate to {escalated_model} due to budget constraints"
                    )
                    return initial_decision

            # Create escalated model config
            escalated_config = self._create_model_config(escalated_model)

            # Record escalation
            if self.neo4j_client:
                await self.neo4j_client.add_escalation_event(
                    str(initial_decision.task_id),
                    current_model,
                    escalated_model,
                    f"Escalated due to complexity={context.get('complexity', 0.0)}, risk={context.get('risk', 0.0)}",
                )

            # Emit escalation metric
            router_escalations_total.labels(
                from_model=current_model, to_model=escalated_model
            ).inc()

            return RoutingDecision(
                task_id=initial_decision.task_id,
                agent_role=initial_decision.agent_role,
                task_type=initial_decision.task_type,
                selected_model=escalated_config,
                routing_rule=f"escalated_{initial_decision.routing_rule}",
                confidence=min(initial_decision.confidence + 0.1, 1.0),
                reasoning=f"Escalated from {current_model} to {escalated_model} due to complexity/risk",
                alternatives=initial_decision.alternatives,
                metadata={
                    **initial_decision.metadata,
                    "escalated_from": current_model,
                    "escalation_reason": "complexity_or_risk",
                },
            )

        except ValueError:
            # Model not in escalation path, return original
            logger.warning(f"Model {current_model} not in escalation path")
            return initial_decision

    def _create_model_config(self, model: str) -> ModelConfig:
        """Create model configuration for a given model."""

        if model == "o4-mini":
            return ModelConfig(
                provider=ModelProvider.ANTHROPIC,
                model="o4-mini",
                temperature=0.1,
                max_tokens=4000,
            )
        elif model == "gpt-4o":
            return ModelConfig(
                provider=ModelProvider.OPENAI,
                model="gpt-4o",
                temperature=0.1,
                max_tokens=4000,
            )
        elif model == "o3":
            return ModelConfig(
                provider=ModelProvider.ANTHROPIC,
                model="o3",
                temperature=0.1,
                max_tokens=4000,
            )
        else:
            # Default to o4-mini
            return ModelConfig(
                provider=ModelProvider.ANTHROPIC,
                model="o4-mini",
                temperature=0.1,
                max_tokens=4000,
            )

    def _select_best_rule(
        self,
        matching_rules: List[RoutingRule],
        context: Dict[str, Any],
    ) -> RoutingRule:
        """Select the best rule based on priority and priors."""

        # Sort by priority (higher is better)
        sorted_rules = sorted(matching_rules, key=lambda r: r.priority, reverse=True)

        # If multiple rules have same priority, use priors
        if (
            len(sorted_rules) > 1
            and sorted_rules[0].priority == sorted_rules[1].priority
        ):
            # Use priors to break tie
            best_rule = max(
                sorted_rules, key=lambda r: self._get_rule_score(r, context)
            )
        else:
            best_rule = sorted_rules[0]

        return best_rule

    def _get_rule_score(self, rule: RoutingRule, context: Dict[str, Any]) -> float:
        """Get score for a rule based on benchmark priors."""

        model = rule.ai_model_config.model
        if model in self.priors["models"]:
            model_stats = self.priors["models"][model]
            total_count = model_stats.get("total_count", 0)
            success_count = model_stats.get("success_count", 0)

            if total_count > 0:
                success_rate = success_count / total_count

                # Calculate average cost from samples
                cost_samples = model_stats.get("cost_samples", [])
                avg_cost = (
                    sum(cost_samples) / len(cost_samples) if cost_samples else 0.0
                )

                # Calculate average latency from samples
                latency_samples = model_stats.get("latency_samples", [])
                avg_latency = (
                    sum(latency_samples) / len(latency_samples)
                    if latency_samples
                    else 0.0
                )

                # Score based on success rate, cost efficiency, and latency
                success_weight = 0.6
                cost_weight = 0.25
                latency_weight = 0.15

                cost_score = 1.0 - min(avg_cost / 0.1, 1.0)  # Normalize cost
                latency_score = 1.0 - min(
                    avg_latency / 5000, 1.0
                )  # Normalize latency (5s max)

                score = (
                    success_rate * success_weight
                    + cost_score * cost_weight
                    + latency_score * latency_weight
                )

                logger.debug(
                    f"Model {model} score: {score:.3f} (success: {success_rate:.3f}, cost: {cost_score:.3f}, latency: {latency_score:.3f})"
                )
                return score

        return 0.5  # Default score

    def _find_matching_rules(
        self, agent_role: AgentRole, task_type: str, context: Dict[str, Any]
    ) -> List[RoutingRule]:
        """Find rules that match the task characteristics."""

        matching_rules = []

        for rule in self.rules:
            if not rule.enabled:
                continue

            # Check agent role match
            if rule.agent_role and rule.agent_role != agent_role:
                continue

            # Check task type match
            if rule.task_type and rule.task_type != task_type:
                continue

            # Check complexity match
            if rule.complexity:
                complexity = context.get("complexity", 0.0)
                if rule.complexity == "low" and complexity > 0.3:
                    continue
                elif rule.complexity == "medium" and (
                    complexity <= 0.3 or complexity > 0.7
                ):
                    continue
                elif rule.complexity == "high" and complexity <= 0.7:
                    continue

            matching_rules.append(rule)

        return matching_rules

    def _calculate_confidence(
        self,
        rule: RoutingRule,
        agent_role: AgentRole,
        task_type: str,
        context: Dict[str, Any],
    ) -> float:
        """Calculate confidence for a routing decision."""

        base_confidence = 0.7

        # Adjust based on rule priority
        priority_bonus = min(rule.priority / 20.0, 0.2)

        # Adjust based on model priors
        model = rule.ai_model_config.model
        if model in self.priors["models"]:
            model_stats = self.priors["models"][model]
            total_count = model_stats.get("total_count", 0)
            success_count = model_stats.get("success_count", 0)

            if total_count > 0:
                success_rate = success_count / total_count
                prior_bonus = success_rate * 0.2
            else:
                prior_bonus = 0.0
        else:
            prior_bonus = 0.0

        # Adjust based on context complexity
        complexity = context.get("complexity", 0.0)
        complexity_penalty = complexity * 0.1

        confidence = base_confidence + priority_bonus + prior_bonus - complexity_penalty
        return max(0.0, min(1.0, confidence))

    def _create_decision(
        self,
        task_id: UUID,
        agent_role: AgentRole,
        task_type: str,
        rule: RoutingRule,
        confidence: float,
        reasoning: str,
        alternatives: Optional[List[ModelConfig]] = None,
    ) -> RoutingDecision:
        """Create a routing decision."""

        return RoutingDecision(
            task_id=task_id,
            agent_role=agent_role,
            task_type=task_type,
            selected_model=rule.ai_model_config,
            routing_rule=rule.name,
            confidence=confidence,
            reasoning=reasoning,
            alternatives=alternatives or [],
        )

    async def add_rule(self, rule: RoutingRule) -> bool:
        """Add a new routing rule."""
        try:
            # Check for duplicate names
            if any(r.name == rule.name for r in self.rules):
                logger.warning(f"Rule with name {rule.name} already exists")
                return False

            self.rules.append(rule)

            # Persist to Neo4j if available
            if self.neo4j_client:
                await self._persist_rule(rule)

            logger.info(f"Added routing rule: {rule.name}")
            return True

        except Exception as e:
            logger.error(f"Error adding routing rule: {e}")
            return False

    async def remove_rule(self, rule_name: str) -> bool:
        """Remove a routing rule."""
        try:
            # Remove from memory
            self.rules = [r for r in self.rules if r.name != rule_name]

            # Remove from Neo4j if available
            if self.neo4j_client:
                await self._remove_rule_from_neo4j(rule_name)

            logger.info(f"Removed routing rule: {rule_name}")
            return True

        except Exception as e:
            logger.error(f"Error removing routing rule: {e}")


class TaskRoutingError(Exception):
    """Exception raised for task routing errors."""

    pass


class TaskExecutionError(Exception):
    """Exception raised for task execution errors."""

    pass


class TaskResultError(Exception):
    """Exception raised for task result processing errors."""

    pass

    async def get_routing_history(
        self,
        task_id: Optional[UUID] = None,
        agent_role: Optional[AgentRole] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get routing history from Neo4j."""

        if not self.neo4j_client:
            return []

        try:
            cypher = """
            MATCH (d:Decision)
            WHERE 1=1
            """
            params = {}

            if task_id:
                cypher += " AND d.task_id = $task_id"
                params["task_id"] = str(task_id)

            if agent_role:
                cypher += " AND d.agent_role = $agent_role"
                params["agent_role"] = agent_role.value

            cypher += """
            RETURN d
            ORDER BY d.created_at DESC
            LIMIT $limit
            """
            params["limit"] = limit

            with self.neo4j_client.driver.session() as session:
                result = session.run(cypher, **params)
                records = list(result)

                return [dict(record["d"]) for record in records]

        except Exception as e:
            logger.error(f"Error getting routing history: {e}")
            return []

    async def get_model_performance_stats(
        self, model: str, time_period: str = "7d"
    ) -> Dict[str, Any]:
        """Get performance statistics for a model."""

        if not self.neo4j_client:
            return {}

        try:
            cypher = """
            MATCH (d:Decision {model: $model})
            WHERE d.created_at > datetime() - duration($time_period)
            RETURN
                count(*) as total_decisions,
                sum(CASE WHEN d.success THEN 1 ELSE 0 END) as successful_decisions,
                avg(d.cost_actual_usd) as avg_cost,
                avg(d.latency_actual_ms) as avg_latency,
                avg(d.confidence) as avg_confidence
            """

            with self.neo4j_client.driver.session() as session:
                result = session.run(cypher, model=model, time_period=time_period)
                record = result.single()

                if record:
                    total = record["total_decisions"]
                    successful = record["successful_decisions"]

                    return {
                        "model": model,
                        "time_period": time_period,
                        "total_decisions": total,
                        "successful_decisions": successful,
                        "success_rate": successful / total if total > 0 else 0.0,
                        "avg_cost": record["avg_cost"],
                        "avg_latency": record["avg_latency"],
                        "avg_confidence": record["avg_confidence"],
                    }
                else:
                    return {
                        "model": model,
                        "time_period": time_period,
                        "total_decisions": 0,
                        "successful_decisions": 0,
                        "success_rate": 0.0,
                        "avg_cost": 0.0,
                        "avg_latency": 0.0,
                        "avg_confidence": 0.0,
                    }

        except Exception as e:
            logger.error(f"Error getting model performance stats: {e}")
            return {}

    async def _persist_rule(self, rule: RoutingRule) -> None:
        """Persist a routing rule to Neo4j."""

        try:
            cypher = """
            MERGE (r:RoutingRule {name: $name})
            SET r += $rule_props
            SET r.created_at = datetime()
            SET r.updated_at = datetime()
            RETURN r
            """

            rule_props = {
                "description": rule.description,
                "agent_role": rule.agent_role.value if rule.agent_role else None,
                "task_type": rule.task_type.value if rule.task_type else None,
                "complexity": rule.complexity,
                "priority": rule.priority,
                "enabled": rule.enabled,
                "model_provider": rule.ai_model_config.provider.value,
                "model": rule.ai_model_config.model,
                "temperature": rule.ai_model_config.temperature,
                "max_tokens": rule.ai_model_config.max_tokens,
            }

            with self.neo4j_client.driver.session() as session:
                session.run(cypher, name=rule.name, rule_props=rule_props)

        except Exception as e:
            logger.error(f"Error persisting routing rule: {e}")

    async def _persist_routing_decision(self, decision: RoutingDecision) -> None:
        """Persist a routing decision to Neo4j."""

        try:
            cypher = """
            CREATE (d:RoutingDecision {
                task_id: $task_id,
                agent_role: $agent_role,
                task_type: $task_type,
                selected_model: $selected_model,
                routing_rule: $routing_rule,
                confidence: $confidence,
                reasoning: $reasoning,
                created_at: datetime()
            })
            RETURN d
            """

            with self.neo4j_client.driver.session() as session:
                session.run(
                    cypher,
                    task_id=str(decision.task_id),
                    agent_role=decision.agent_role.value,
                    task_type=decision.task_type.value,
                    selected_model=decision.selected_model.model,
                    routing_rule=decision.routing_rule,
                    confidence=decision.confidence,
                    reasoning=decision.reasoning,
                )

        except Exception as e:
            logger.error(f"Error persisting routing decision: {e}")

    async def _remove_rule_from_neo4j(self, rule_name: str) -> None:
        """Remove a routing rule from Neo4j."""

        try:
            cypher = """
            MATCH (r:RoutingRule {name: $name})
            DELETE r
            """

            with self.neo4j_client.driver.session() as session:
                session.run(cypher, name=rule_name)

        except Exception as e:
            logger.error(f"Error removing routing rule from Neo4j: {e}")
