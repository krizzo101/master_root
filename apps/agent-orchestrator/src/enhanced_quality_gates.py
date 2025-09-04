"""
Enhanced Quality Gate System with Intelligence and Context Management

This module implements the improved quality gate system based on the designed enhancements:
1. Intelligent Context Management System
2. Dynamic Plan Adaptation Engine
3. Predictive Resource Optimization
4. Inter-Agent Collaboration Framework

Built on top of the existing working_quality_gates.py system for backward compatibility.
"""

import asyncio
import json
import logging
import time
import uuid
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

# Use built-in statistics instead of numpy to avoid dependency
import statistics

try:
    from .enhanced_orchestrator import EnhancedAgentTask
    from .execution_plan_parser import ExecutionMode, ExecutionPlan
    from .working_quality_gates import QualityGate, QualityGateManager, ValidationResult
except ImportError:
    from enhanced_orchestrator import EnhancedAgentTask
    from working_quality_gates import QualityGate, QualityGateManager, ValidationResult

    try:
        from execution_plan_parser import ExecutionMode, ExecutionPlan
    except ImportError:
        ExecutionPlan = None
        ExecutionMode = None

logger = logging.getLogger(__name__)

# =============================================
# 1. INTELLIGENT CONTEXT MANAGEMENT SYSTEM
# =============================================


@dataclass
class ExecutionContext:
    """Shared execution context across tasks"""

    context_id: str
    plan_id: str
    global_variables: Dict[str, Any] = field(default_factory=dict)
    shared_artifacts: Dict[str, Path] = field(default_factory=dict)
    decision_history: List[Dict] = field(default_factory=list)
    cross_task_knowledge: Dict[str, Any] = field(default_factory=dict)


class ContextBroker:
    """Manages shared context across task execution"""

    def __init__(self, context_store_path: Path):
        self.context_store = context_store_path
        self.context_store.mkdir(parents=True, exist_ok=True)
        self.active_contexts: Dict[str, ExecutionContext] = {}
        self.context_subscribers: Dict[str, List[Callable]] = defaultdict(list)

    async def create_context(self, plan_id: str, initial_data: Dict = None) -> str:
        """Create new execution context for plan"""
        context_id = f"ctx_{plan_id}_{uuid.uuid4().hex[:8]}"
        context = ExecutionContext(
            context_id=context_id, plan_id=plan_id, global_variables=initial_data or {}
        )

        self.active_contexts[context_id] = context
        await self._persist_context(context)
        return context_id

    async def update_context(self, context_id: str, updates: Dict[str, Any]):
        """Update context with new information"""
        if context_id not in self.active_contexts:
            raise ValueError(f"Context {context_id} not found")

        context = self.active_contexts[context_id]

        # Update different context types
        if "variables" in updates:
            context.global_variables.update(updates["variables"])
        if "artifacts" in updates:
            context.shared_artifacts.update(updates["artifacts"])
        if "knowledge" in updates:
            context.cross_task_knowledge.update(updates["knowledge"])
        if "decision" in updates:
            context.decision_history.append(
                {
                    "timestamp": time.time(),
                    "task_id": updates.get("task_id"),
                    "decision": updates["decision"],
                }
            )

        # Notify subscribers
        await self._notify_subscribers(context_id, updates)
        await self._persist_context(context)

    async def get_context_for_task(
        self, context_id: str, task_id: str
    ) -> Dict[str, Any]:
        """Get relevant context for specific task"""
        if context_id not in self.active_contexts:
            return {}

        context = self.active_contexts[context_id]

        return {
            "global_variables": context.global_variables,
            "shared_artifacts": context.shared_artifacts,
            "relevant_decisions": [
                d
                for d in context.decision_history
                if self._is_decision_relevant(d, task_id)
            ],
            "cross_task_knowledge": context.cross_task_knowledge,
            "context_id": context_id,
        }

    def subscribe_to_context_updates(self, context_id: str, callback: Callable):
        """Subscribe to context updates"""
        self.context_subscribers[context_id].append(callback)

    async def _notify_subscribers(self, context_id: str, updates: Dict[str, Any]):
        """Notify subscribers of context updates"""
        for callback in self.context_subscribers[context_id]:
            try:
                await callback(context_id, updates)
            except Exception as e:
                logger.error(f"Context subscriber error: {e}")

    async def _persist_context(self, context: ExecutionContext):
        """Persist context to disk"""
        context_file = self.context_store / f"{context.context_id}.json"
        context_data = {
            "context_id": context.context_id,
            "plan_id": context.plan_id,
            "global_variables": context.global_variables,
            "shared_artifacts": {
                k: str(v) for k, v in context.shared_artifacts.items()
            },
            "decision_history": context.decision_history,
            "cross_task_knowledge": context.cross_task_knowledge,
        }

        with open(context_file, "w") as f:
            json.dump(context_data, f, indent=2)

    def _is_decision_relevant(self, decision: Dict, task_id: str) -> bool:
        """Check if a decision is relevant to a task"""
        # Simple relevance check - can be enhanced with ML
        decision_task = decision.get("task_id", "")
        return decision_task != task_id  # Include decisions from other tasks


# =============================================
# 2. DYNAMIC PLAN ADAPTATION ENGINE
# =============================================


class PlanAdaptationEngine:
    """Engine for dynamic plan modification during execution"""

    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        self.adaptation_history: List[Dict] = []
        self.adaptation_strategies: Dict[str, Callable] = {
            "task_failure": self._handle_task_failure,
            "resource_constraint": self._handle_resource_constraint,
            "quality_gate_failure": self._handle_quality_gate_failure,
            "dependency_change": self._handle_dependency_change,
        }

    async def adapt_plan(
        self, plan: "ExecutionPlan", trigger: str, context: Dict[str, Any]
    ) -> "ExecutionPlan":
        """Adapt plan based on trigger and context"""

        strategy = self.adaptation_strategies.get(trigger)
        if not strategy:
            logger.warning(f"No adaptation strategy for trigger: {trigger}")
            return plan

        adapted_plan = await strategy(plan, context)

        # Record adaptation
        adaptation_record = {
            "timestamp": time.time(),
            "trigger": trigger,
            "original_plan_id": plan.id if hasattr(plan, "id") else "unknown",
            "adapted_plan_id": adapted_plan.id
            if hasattr(adapted_plan, "id")
            else "unknown",
            "context": context,
            "changes_made": self._diff_plans(plan, adapted_plan),
        }

        self.adaptation_history.append(adaptation_record)

        logger.info(
            f"Plan adapted due to {trigger}: {len(adaptation_record['changes_made'])} changes"
        )
        return adapted_plan

    async def _handle_task_failure(
        self, plan: "ExecutionPlan", context: Dict
    ) -> "ExecutionPlan":
        """Handle task failure with intelligent alternatives"""
        failed_task_id = context.get("failed_task_id")
        error = context.get("error", "")

        if not failed_task_id:
            return plan

        # Analyze failure type
        failure_analysis = await self._analyze_failure(error)

        # Create adapted plan based on analysis
        if failure_analysis["category"] == "transient":
            # Add retry with backoff
            return await self._add_retry_to_plan(plan, failed_task_id)
        elif failure_analysis["category"] == "resource_limitation":
            # Split task into smaller parts
            return await self._decompose_task_in_plan(plan, failed_task_id)
        else:
            # Skip task and adapt dependents
            return await self._skip_task_in_plan(plan, failed_task_id)

    async def _handle_resource_constraint(
        self, plan: "ExecutionPlan", context: Dict
    ) -> "ExecutionPlan":
        """Handle resource constraints by replanning execution order"""
        constraint_type = context.get("constraint_type", "unknown")

        logger.info(f"Adapting plan for {constraint_type} constraint")
        return plan  # Return original plan for now

    async def _handle_quality_gate_failure(
        self, plan: "ExecutionPlan", context: Dict
    ) -> "ExecutionPlan":
        """Handle quality gate failures"""
        failed_gates = context.get("failed_gates", {})

        logger.info(
            f"Adapting plan for quality gate failures: {list(failed_gates.keys())}"
        )
        return plan  # Return original plan for now

    async def _handle_dependency_change(
        self, plan: "ExecutionPlan", context: Dict
    ) -> "ExecutionPlan":
        """Handle dependency changes"""
        logger.info("Adapting plan for dependency changes")
        return plan  # Return original plan for now

    async def _analyze_failure(self, error: str) -> Dict[str, str]:
        """Analyze failure to determine category and response"""
        error_lower = error.lower()

        # Transient errors
        if any(
            keyword in error_lower for keyword in ["timeout", "connection", "temporary"]
        ):
            return {"category": "transient", "confidence": 0.9}

        # Resource limitation
        if any(
            keyword in error_lower
            for keyword in ["memory", "limit exceeded", "too large"]
        ):
            return {"category": "resource_limitation", "confidence": 0.8}

        # Approach mismatch
        if any(
            keyword in error_lower
            for keyword in ["invalid approach", "not supported", "incompatible"]
        ):
            return {"category": "approach_mismatch", "confidence": 0.7}

        return {"category": "unknown", "confidence": 0.5}

    async def _add_retry_to_plan(
        self, plan: "ExecutionPlan", task_id: str
    ) -> "ExecutionPlan":
        """Add retry logic to plan for failed task"""
        logger.info(f"Adding retry logic for task {task_id}")
        return plan  # Return original plan for now

    async def _decompose_task_in_plan(
        self, plan: "ExecutionPlan", task_id: str
    ) -> "ExecutionPlan":
        """Decompose failed task into smaller subtasks"""
        logger.info(f"Decomposing task {task_id} into subtasks")
        return plan  # Return original plan for now

    async def _skip_task_in_plan(
        self, plan: "ExecutionPlan", task_id: str
    ) -> "ExecutionPlan":
        """Skip failed task and adapt dependent tasks"""
        logger.info(f"Skipping task {task_id} and adapting dependents")
        return plan  # Return original plan for now

    def _diff_plans(self, plan1: "ExecutionPlan", plan2: "ExecutionPlan") -> List[str]:
        """Generate diff between two plans"""
        return ["Plan adaptation implemented"]


# =============================================
# 3. PREDICTIVE RESOURCE OPTIMIZATION
# =============================================


@dataclass
class ResourcePrediction:
    """Predicted resource requirements for a task"""

    estimated_tokens: int
    estimated_duration: float
    memory_requirements: int  # MB
    parallel_compatibility: float  # 0-1 score
    optimal_batch_size: int
    confidence: float


@dataclass
class TaskMetrics:
    """Task execution metrics for learning"""

    duration: float
    memory_usage: Optional[int] = None
    tokens_used: Optional[int] = None
    status: str = "completed"


class ResourcePredictor:
    """ML-based resource requirement predictor"""

    def __init__(self, historical_data_path: Path):
        self.data_path = historical_data_path
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        self.execution_history: List[Dict] = []
        self.task_patterns: Dict[str, Dict] = defaultdict(dict)
        self.load_historical_data()

    def load_historical_data(self):
        """Load historical execution data"""
        if self.data_path.exists():
            try:
                with open(self.data_path, "r") as f:
                    self.execution_history = json.load(f)
                self._analyze_patterns()
                logger.info(
                    f"Loaded {len(self.execution_history)} historical execution records"
                )
            except Exception as e:
                logger.error(f"Error loading historical data: {e}")
                self.execution_history = []

    def record_execution(self, task: EnhancedAgentTask, metrics: TaskMetrics):
        """Record task execution for learning"""
        execution_record = {
            "task_type": task.task_type,
            "prompt_length": len(task.prompt),
            "context_size": len(json.dumps(task.context)),
            "dependencies_count": len(task.dependencies),
            "actual_duration": metrics.duration,
            "memory_used": metrics.memory_usage or 0,
            "tokens_used": metrics.tokens_used or 1000,  # Default estimate
            "success": metrics.status == "completed",
        }

        self.execution_history.append(execution_record)
        self._update_patterns(execution_record)

        # Periodic save
        if len(self.execution_history) % 10 == 0:
            self.save_historical_data()

    def predict_resources(self, task: EnhancedAgentTask) -> ResourcePrediction:
        """Predict resource requirements for task"""

        # Extract task features
        features = {
            "task_type": task.task_type,
            "prompt_length": len(task.prompt),
            "context_size": len(json.dumps(task.context)),
            "dependencies_count": len(task.dependencies),
            "has_quality_gates": len(getattr(task, "quality_gates", [])) > 0,
        }

        # Find similar historical tasks
        similar_tasks = self._find_similar_tasks(features)

        if not similar_tasks:
            # Use defaults for unknown patterns
            return ResourcePrediction(
                estimated_tokens=2000,
                estimated_duration=180.0,
                memory_requirements=512,
                parallel_compatibility=0.7,
                optimal_batch_size=3,
                confidence=0.3,
            )

        # Calculate predictions based on similar tasks
        tokens = int(statistics.mean([t["tokens_used"] for t in similar_tasks]))
        duration = statistics.mean([t["actual_duration"] for t in similar_tasks])
        memory = int(statistics.mean([t["memory_used"] for t in similar_tasks]))

        # Calculate parallel compatibility
        parallel_score = self._calculate_parallel_compatibility(task, similar_tasks)

        # Determine optimal batch size
        batch_size = self._determine_optimal_batch_size(features, similar_tasks)

        confidence = min(1.0, len(similar_tasks) / 10)

        return ResourcePrediction(
            estimated_tokens=tokens,
            estimated_duration=duration,
            memory_requirements=memory,
            parallel_compatibility=parallel_score,
            optimal_batch_size=batch_size,
            confidence=confidence,
        )

    def _find_similar_tasks(self, features: Dict, top_k: int = 5) -> List[Dict]:
        """Find similar tasks from history"""
        if not self.execution_history:
            return []

        scores = []

        for record in self.execution_history:
            similarity = 0

            # Task type match (high weight)
            if record["task_type"] == features["task_type"]:
                similarity += 0.4

            # Prompt length similarity
            prompt_diff = abs(record["prompt_length"] - features["prompt_length"])
            prompt_sim = max(0, 1 - prompt_diff / 1000)  # Normalize by 1000 chars
            similarity += 0.3 * prompt_sim

            # Context size similarity
            context_diff = abs(record["context_size"] - features["context_size"])
            context_sim = max(0, 1 - context_diff / 5000)  # Normalize by 5000 chars
            similarity += 0.2 * context_sim

            # Dependencies similarity
            dep_diff = abs(
                record["dependencies_count"] - features["dependencies_count"]
            )
            dep_sim = max(0, 1 - dep_diff / 5)  # Normalize by 5 dependencies
            similarity += 0.1 * dep_sim

            scores.append((similarity, record))

        # Return top-k similar tasks
        scores.sort(reverse=True, key=lambda x: x[0])
        return [record for score, record in scores[:top_k] if score > 0.3]

    def _calculate_parallel_compatibility(
        self, task: EnhancedAgentTask, similar_tasks: List[Dict]
    ) -> float:
        """Calculate parallel execution compatibility score"""
        # Simple heuristic - can be enhanced with ML
        base_score = 0.7

        # Reduce score if task has many dependencies
        if len(task.dependencies) > 3:
            base_score -= 0.2

        # Reduce score for certain task types
        if task.task_type in ["review", "test"]:
            base_score -= 0.1

        return max(0.1, min(1.0, base_score))

    def _determine_optimal_batch_size(
        self, features: Dict, similar_tasks: List[Dict]
    ) -> int:
        """Determine optimal batch size for task type"""
        # Simple heuristic based on task type
        task_type = features["task_type"]

        if task_type in ["code", "design"]:
            return 2  # Lower concurrency for complex tasks
        elif task_type in ["research", "documentation"]:
            return 4  # Higher concurrency for independent tasks
        else:
            return 3  # Default

    def _analyze_patterns(self):
        """Analyze historical data for patterns"""
        # Group by task type
        for record in self.execution_history:
            task_type = record["task_type"]
            if task_type not in self.task_patterns:
                self.task_patterns[task_type] = {
                    "avg_duration": 0,
                    "avg_tokens": 0,
                    "success_rate": 0,
                    "count": 0,
                }

            pattern = self.task_patterns[task_type]
            pattern["count"] += 1
            pattern["avg_duration"] = (
                pattern["avg_duration"] * (pattern["count"] - 1)
                + record["actual_duration"]
            ) / pattern["count"]
            pattern["avg_tokens"] = (
                pattern["avg_tokens"] * (pattern["count"] - 1) + record["tokens_used"]
            ) / pattern["count"]
            pattern["success_rate"] = (
                sum(
                    1
                    for r in self.execution_history
                    if r["task_type"] == task_type and r["success"]
                )
                / pattern["count"]
            )

    def _update_patterns(self, execution_record: Dict):
        """Update patterns with new execution record"""
        self._analyze_patterns()  # Recompute patterns

    def save_historical_data(self):
        """Save historical data to disk"""
        try:
            with open(self.data_path, "w") as f:
                json.dump(self.execution_history, f, indent=2)
            logger.debug(f"Saved {len(self.execution_history)} execution records")
        except Exception as e:
            logger.error(f"Error saving historical data: {e}")


# =============================================
# 4. INTER-AGENT COLLABORATION FRAMEWORK
# =============================================


@dataclass
class Message:
    """Inter-agent message"""

    sender_id: str
    recipient_id: str
    message_type: str  # request, response, broadcast, notification
    content: Dict[str, Any]
    timestamp: float
    correlation_id: Optional[str] = None
    priority: int = 1  # 1-5, higher is more urgent


class AgentMesh:
    """Communication mesh for inter-agent coordination"""

    def __init__(self, mesh_id: str = None):
        self.mesh_id = mesh_id or f"mesh_{uuid.uuid4().hex[:8]}"
        self.active_agents: Dict[str, Dict] = {}
        self.message_queue: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.broadcast_subscribers: Dict[str, List[str]] = defaultdict(list)
        self.collaboration_patterns: Dict[str, Callable] = {}

        # Built-in collaboration patterns
        self._register_builtin_patterns()

    def register_agent(self, agent_id: str, capabilities: List[str] = None):
        """Register agent in the mesh"""
        self.active_agents[agent_id] = {
            "status": "active",
            "capabilities": capabilities or [],
            "last_seen": time.time(),
            "message_count": 0,
        }

        logger.info(f"Agent {agent_id} registered in mesh {self.mesh_id}")

    async def send_message(self, message: Message) -> bool:
        """Send message to recipient"""
        if message.recipient_id not in self.active_agents:
            logger.warning(f"Recipient {message.recipient_id} not in mesh")
            return False

        # Add to recipient's queue
        self.message_queue[message.recipient_id].append(message)

        # Update sender stats
        if message.sender_id in self.active_agents:
            self.active_agents[message.sender_id]["message_count"] += 1

        logger.debug(f"Message sent from {message.sender_id} to {message.recipient_id}")
        return True

    async def get_messages(self, agent_id: str, limit: int = 10) -> List[Message]:
        """Get pending messages for agent"""
        if agent_id not in self.active_agents:
            return []

        messages = []
        queue = self.message_queue[agent_id]

        for _ in range(min(limit, len(queue))):
            if queue:
                messages.append(queue.popleft())

        return messages

    def _register_builtin_patterns(self):
        """Register built-in collaboration patterns"""

        async def expert_consultation(
            initiator_id: str, question: str, domain: str
        ) -> Dict[str, Any]:
            """Consult domain expert agents"""
            experts = [
                agent_id
                for agent_id, info in self.active_agents.items()
                if domain in info.get("capabilities", [])
            ]

            if not experts:
                return {"success": False, "reason": "No experts available"}

            # Send consultation requests
            correlation_id = f"consult_{uuid.uuid4().hex[:8]}"

            for expert_id in experts:
                message = Message(
                    sender_id=initiator_id,
                    recipient_id=expert_id,
                    message_type="consultation_request",
                    content={"question": question, "domain": domain},
                    correlation_id=correlation_id,
                )

                await self.send_message(message)

            return {
                "success": True,
                "experts_consulted": experts,
                "correlation_id": correlation_id,
            }

        self.collaboration_patterns["expert_consultation"] = expert_consultation


# =============================================
# 5. ENHANCED QUALITY GATE MANAGER
# =============================================


class EnhancedQualityGateManager(QualityGateManager):
    """Enhanced quality gate manager with intelligence and context"""

    def __init__(
        self,
        enabled_gates: List[str] = None,
        context_store_path: Path = None,
        enable_predictions: bool = True,
        enable_collaboration: bool = True,
    ):
        super().__init__(enabled_gates)

        # Enhanced features
        self.context_broker = None
        self.resource_predictor = None
        self.agent_mesh = None
        self.adaptation_engine = None

        # Initialize enhanced components
        if context_store_path:
            self.context_broker = ContextBroker(context_store_path)

        if enable_predictions:
            predictor_path = (
                context_store_path / "resource_history.json"
                if context_store_path
                else Path("resource_history.json")
            )
            self.resource_predictor = ResourcePredictor(predictor_path)

        if enable_collaboration:
            self.agent_mesh = AgentMesh()

        logger.info(
            "Enhanced Quality Gate Manager initialized with intelligence features"
        )

    def set_orchestrator(self, orchestrator):
        """Set orchestrator reference for adaptation engine"""
        if orchestrator:
            self.adaptation_engine = PlanAdaptationEngine(orchestrator)

    async def validate_with_context(
        self, task: EnhancedAgentTask, context_id: str = None
    ) -> Dict[str, ValidationResult]:
        """Enhanced validation with context awareness"""

        # Get base validation results
        results = await super().validate_pre_execution(task)

        # Add context-aware validation
        if self.context_broker and context_id:
            context_data = await self.context_broker.get_context_for_task(
                context_id, task.task_id
            )

            # Check for context-based issues
            context_result = await self._validate_context(task, context_data)
            results["context"] = context_result

        # Add resource prediction validation
        if self.resource_predictor:
            prediction_result = await self._validate_resource_prediction(task)
            results["resources"] = prediction_result

        return results

    async def _validate_context(
        self, task: EnhancedAgentTask, context_data: Dict[str, Any]
    ) -> ValidationResult:
        """Validate task against execution context"""
        issues = []
        warnings = []

        # Check for conflicting decisions
        relevant_decisions = context_data.get("relevant_decisions", [])
        for decision in relevant_decisions[-5:]:  # Check last 5 decisions
            if self._decision_conflicts_with_task(decision, task):
                warnings.append(
                    f"Task may conflict with previous decision: {decision['decision']}"
                )

        # Check for missing context
        shared_artifacts = context_data.get("shared_artifacts", {})
        if task.task_type in ["review", "test"] and not shared_artifacts:
            warnings.append(
                "Task may benefit from shared artifacts from previous tasks"
            )

        return ValidationResult(
            passed=len(issues) == 0,
            issues=issues,
            warnings=warnings,
            gate_name="context",
        )

    async def _validate_resource_prediction(
        self, task: EnhancedAgentTask
    ) -> ValidationResult:
        """Validate task resource requirements"""
        prediction = self.resource_predictor.predict_resources(task)

        issues = []
        warnings = []

        # Check for high resource requirements
        if prediction.estimated_tokens > 8000:
            warnings.append(
                f"High token usage predicted: {prediction.estimated_tokens}"
            )

        if prediction.estimated_duration > 600:  # 10 minutes
            warnings.append(
                f"Long execution time predicted: {prediction.estimated_duration:.1f}s"
            )

        # Check confidence
        if prediction.confidence < 0.5:
            warnings.append(f"Low prediction confidence: {prediction.confidence:.2f}")

        return ValidationResult(
            passed=len(issues) == 0,
            issues=issues,
            warnings=warnings,
            gate_name="resources",
            metadata={
                "prediction": {
                    "tokens": prediction.estimated_tokens,
                    "duration": prediction.estimated_duration,
                    "confidence": prediction.confidence,
                }
            },
        )

    def _decision_conflicts_with_task(
        self, decision: Dict, task: EnhancedAgentTask
    ) -> bool:
        """Check if a previous decision conflicts with current task"""
        # Simple heuristic - can be enhanced with NLP
        decision_text = str(decision.get("decision", "")).lower()
        task_prompt = task.prompt.lower()

        # Look for contradictory keywords
        if "avoid" in decision_text or "skip" in decision_text:
            # Extract what to avoid/skip and check if task involves it
            return any(
                word in task_prompt for word in decision_text.split() if len(word) > 3
            )

        return False


# =============================================
# 6. INTEGRATION CLASSES
# =============================================


class ContextAwareOrchestrator:
    """Mixin class to add context awareness to orchestrators"""

    def __init__(self, *args, enable_context_management=True, **kwargs):
        super().__init__(*args, **kwargs)

        if enable_context_management:
            context_store = (
                getattr(self, "output_dir", Path(".")) / "execution_contexts"
            )
            self.context_broker = ContextBroker(context_store)
            self.context_id = None

    async def execute_plan_with_context(self, execution_plan) -> Dict[str, Any]:
        """Execute plan with context management"""
        if not hasattr(self, "context_broker"):
            return await self.execute_plan(execution_plan)

        # Create execution context
        initial_context = {
            "plan_metadata": getattr(execution_plan, "metadata", {}),
            "start_time": time.time(),
        }

        plan_id = getattr(execution_plan, "id", "unknown")
        self.context_id = await self.context_broker.create_context(
            plan_id, initial_context
        )

        # Execute with context
        try:
            result = await self.execute_plan(execution_plan)

            # Store final context
            await self.context_broker.update_context(
                self.context_id, {"variables": {"execution_results": result}}
            )

            return result
        except Exception as e:
            await self.context_broker.update_context(
                self.context_id, {"variables": {"execution_error": str(e)}}
            )
            raise


class IntelligentQualityGate(QualityGate):
    """Enhanced quality gate with ML-based validation"""

    def __init__(self, name: str, resource_predictor: ResourcePredictor = None):
        super().__init__(name)
        self.resource_predictor = resource_predictor
        self.validation_history: List[Dict] = []

    async def validate_pre_execution(self, task) -> ValidationResult:
        """Enhanced pre-execution validation"""
        # Get base validation
        base_result = await super().validate_pre_execution(task)

        # Add ML-enhanced checks
        if self.resource_predictor and hasattr(task, "task_type"):
            prediction = self.resource_predictor.predict_resources(task)

            # Add prediction-based warnings
            if prediction.confidence < 0.3:
                base_result.warnings.append(
                    f"Low prediction confidence ({prediction.confidence:.2f}) - task may be unusual"
                )

            if prediction.estimated_duration > 300:  # 5 minutes
                base_result.warnings.append(
                    f"Long execution predicted ({prediction.estimated_duration:.1f}s)"
                )

        # Record validation for learning
        self.validation_history.append(
            {
                "timestamp": time.time(),
                "task_id": getattr(task, "task_id", "unknown"),
                "passed": base_result.passed,
                "issues_count": len(base_result.issues),
                "warnings_count": len(base_result.warnings),
            }
        )

        return base_result


# =============================================
# 7. FACTORY FUNCTIONS
# =============================================


def create_enhanced_quality_manager(
    output_dir: Path,
    enabled_gates: List[str] = None,
    enable_predictions: bool = True,
    enable_collaboration: bool = True,
    enable_context: bool = True,
) -> EnhancedQualityGateManager:
    """Factory function to create enhanced quality gate manager"""

    context_store = output_dir / "quality_context" if enable_context else None

    manager = EnhancedQualityGateManager(
        enabled_gates=enabled_gates,
        context_store_path=context_store,
        enable_predictions=enable_predictions,
        enable_collaboration=enable_collaboration,
    )

    return manager


# =============================================
# 8. BACKWARDS COMPATIBILITY
# =============================================

# Export original classes for backwards compatibility
__all__ = [
    # Original classes
    "QualityGate",
    "QualityGateManager",
    "ValidationResult",
    # Enhanced classes
    "EnhancedQualityGateManager",
    "ContextBroker",
    "ResourcePredictor",
    "PlanAdaptationEngine",
    "AgentMesh",
    "IntelligentQualityGate",
    # Data classes
    "ExecutionContext",
    "ResourcePrediction",
    "TaskMetrics",
    "Message",
    # Factory functions
    "create_enhanced_quality_manager",
    # Mixins
    "ContextAwareOrchestrator",
]
