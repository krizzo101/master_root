"""
Enhanced Orchestrator Integration Layer

This module provides the integration between the enhanced quality gates system
and the existing orchestrator infrastructure. It maintains backward compatibility
while enabling the new intelligent features.
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from .enhanced_orchestrator import EnhancedAgentTask, EnhancedOrchestrator
    from .enhanced_quality_gates import (
        AgentMesh,
        ContextBroker,
        EnhancedQualityGateManager,
        PlanAdaptationEngine,
        ResourcePredictor,
        TaskMetrics,
        create_enhanced_quality_manager,
    )
    from .execution_plan_parser import ExecutionMode, ExecutionPlan
except ImportError:
    from enhanced_orchestrator import EnhancedAgentTask, EnhancedOrchestrator
    from enhanced_quality_gates import (
        AgentMesh,
        ContextBroker,
        EnhancedQualityGateManager,
        PlanAdaptationEngine,
        ResourcePredictor,
        TaskMetrics,
        create_enhanced_quality_manager,
    )

    try:
        from execution_plan_parser import ExecutionMode, ExecutionPlan
    except ImportError:
        ExecutionPlan = None
        ExecutionMode = None

logger = logging.getLogger(__name__)


class IntelligentOrchestrator(EnhancedOrchestrator):
    """
    Enhanced orchestrator with full intelligence features:
    - Intelligent Context Management
    - Dynamic Plan Adaptation
    - Predictive Resource Optimization
    - Inter-Agent Collaboration

    Maintains full backward compatibility with existing code.
    """

    def __init__(
        self,
        output_dir: Path,
        max_parallel: int = 10,
        tokens: List[str] = None,
        use_optimizations: bool = True,
        # Intelligence features
        enable_intelligent_gates: bool = True,
        enable_context_management: bool = True,
        enable_resource_prediction: bool = True,
        enable_collaboration: bool = True,
        enable_adaptation: bool = True,
        # Configuration
        intelligence_config: Dict[str, Any] = None,
        **kwargs,
    ):
        # Initialize parent with basic quality gates disabled
        # We'll replace it with the enhanced version
        super().__init__(
            output_dir=output_dir,
            max_parallel=max_parallel,
            tokens=tokens,
            use_optimizations=use_optimizations,
            enable_quality_gates=False,  # Disable basic gates
            enable_monitoring=kwargs.get("enable_monitoring", True),
            **kwargs,
        )

        # Intelligence feature flags
        self.enable_intelligent_gates = enable_intelligent_gates
        self.enable_context_management = enable_context_management
        self.enable_resource_prediction = enable_resource_prediction
        self.enable_collaboration = enable_collaboration
        self.enable_adaptation = enable_adaptation

        # Initialize intelligence components
        self._initialize_intelligence_components(intelligence_config or {})

        # Enhanced metrics
        self.intelligence_metrics = {
            "context_updates": 0,
            "adaptations_made": 0,
            "predictions_generated": 0,
            "collaboration_events": 0,
            "intelligence_time_saved": 0,
        }

        logger.info(
            f"IntelligentOrchestrator initialized with features: "
            f"gates={enable_intelligent_gates}, context={enable_context_management}, "
            f"prediction={enable_resource_prediction}, collaboration={enable_collaboration}, "
            f"adaptation={enable_adaptation}"
        )

    def _initialize_intelligence_components(self, config: Dict[str, Any]):
        """Initialize intelligence components"""

        # Enhanced Quality Gate Manager
        if self.enable_intelligent_gates:
            self.enhanced_quality_manager = create_enhanced_quality_manager(
                output_dir=self.output_dir,
                enabled_gates=config.get(
                    "enabled_gates", ["structure", "dependencies", "prompt"]
                ),
                enable_predictions=self.enable_resource_prediction,
                enable_collaboration=self.enable_collaboration,
                enable_context=self.enable_context_management,
            )

            # Set orchestrator reference for adaptation
            self.enhanced_quality_manager.set_orchestrator(self)

            # Replace the basic quality gate manager
            self.quality_gate_manager = self.enhanced_quality_manager

        # Context Management
        self.context_broker: Optional[ContextBroker] = None
        if self.enable_context_management:
            context_store = self.output_dir / "execution_contexts"
            self.context_broker = ContextBroker(context_store)
            self.current_context_id: Optional[str] = None

        # Resource Prediction
        self.resource_predictor: Optional[ResourcePredictor] = None
        if self.enable_resource_prediction:
            predictor_path = self.output_dir / "intelligence" / "resource_history.json"
            predictor_path.parent.mkdir(parents=True, exist_ok=True)
            self.resource_predictor = ResourcePredictor(predictor_path)

        # Collaboration
        self.agent_mesh: Optional[AgentMesh] = None
        if self.enable_collaboration:
            mesh_id = config.get("mesh_id", f"orchestrator_{self.output_dir.name}")
            self.agent_mesh = AgentMesh(mesh_id)

        # Plan Adaptation
        self.adaptation_engine: Optional[PlanAdaptationEngine] = None
        if self.enable_adaptation:
            self.adaptation_engine = PlanAdaptationEngine(self)

    async def execute_plan(self, execution_plan) -> Dict[str, Any]:
        """Execute plan with full intelligence features"""

        # Create execution context
        if self.context_broker:
            initial_context = {
                "plan_metadata": getattr(execution_plan, "metadata", {}),
                "execution_mode": getattr(execution_plan, "execution_mode", "parallel"),
                "start_time": time.time(),
            }

            plan_id = getattr(execution_plan, "id", f"plan_{int(time.time())}")
            self.current_context_id = await self.context_broker.create_context(
                plan_id, initial_context
            )

            logger.info(f"Created execution context: {self.current_context_id}")

        # Execute with adaptation loop
        if self.enable_adaptation and self.adaptation_engine:
            return await self._execute_with_adaptation(execution_plan)
        else:
            return await super().execute_plan(execution_plan)

    async def _execute_with_adaptation(self, execution_plan) -> Dict[str, Any]:
        """Execute plan with dynamic adaptation"""
        current_plan = execution_plan
        adaptation_count = 0
        max_adaptations = 5

        while adaptation_count < max_adaptations:
            try:
                # Execute plan
                result = await super().execute_plan(current_plan)

                # Check if adaptation is needed
                (
                    adaptation_needed,
                    trigger,
                    context,
                ) = await self._check_adaptation_needed(result)

                if not adaptation_needed:
                    break

                # Adapt plan
                logger.info(f"Adapting plan due to {trigger}")
                current_plan = await self.adaptation_engine.adapt_plan(
                    current_plan, trigger, context
                )
                adaptation_count += 1
                self.intelligence_metrics["adaptations_made"] += 1

                logger.info(
                    f"Plan adapted ({adaptation_count}/{max_adaptations}), retrying execution"
                )

            except Exception as e:
                if adaptation_count < max_adaptations:
                    # Attempt adaptation on exception
                    context = {"error": str(e), "exception_type": type(e).__name__}
                    current_plan = await self.adaptation_engine.adapt_plan(
                        current_plan, "execution_error", context
                    )
                    adaptation_count += 1
                    continue
                else:
                    raise

        # Add adaptation metadata to result
        if hasattr(result, "get") and adaptation_count > 0:
            result["intelligence_metadata"] = {
                "adaptations_made": adaptation_count,
                "adaptation_history": getattr(
                    self.adaptation_engine, "adaptation_history", []
                )[-adaptation_count:],
            }

        return result

    async def _check_adaptation_needed(self, result: Dict) -> tuple:
        """Check if plan adaptation is needed based on results"""
        # Check for failures
        if result.get("metrics", {}).get("failed", 0) > 0:
            failed_tasks = [
                r for r in result.get("results", []) if r.get("status") == "failed"
            ]
            if failed_tasks:
                return (
                    True,
                    "task_failure",
                    {
                        "failed_task_id": failed_tasks[0].get("task_id"),
                        "error": failed_tasks[0].get("error", "Unknown error"),
                    },
                )

        # Check quality gates
        if result.get("quality_metrics", {}).get("gates_failed", 0) > 0:
            return (
                True,
                "quality_gate_failure",
                {"failed_gates": result.get("quality_status", {})},
            )

        return False, None, {}

    async def execute_agent_enhanced(self, task: EnhancedAgentTask) -> Dict:
        """Execute enhanced task with full intelligence"""

        # Pre-execution intelligence
        await self._apply_pre_execution_intelligence(task)

        # Execute task
        start_time = time.time()
        result = await super().execute_agent_enhanced(task)

        # Post-execution intelligence
        await self._apply_post_execution_intelligence(
            task, result, time.time() - start_time
        )

        return result

    async def _apply_pre_execution_intelligence(self, task: EnhancedAgentTask):
        """Apply intelligence features before task execution"""

        # Context injection
        if self.context_broker and self.current_context_id:
            task_context = await self.context_broker.get_context_for_task(
                self.current_context_id, task.task_id
            )
            task.context.update(task_context)
            self.intelligence_metrics["context_updates"] += 1

        # Resource prediction
        if self.resource_predictor:
            prediction = self.resource_predictor.predict_resources(task)
            task.context["resource_prediction"] = {
                "estimated_tokens": prediction.estimated_tokens,
                "estimated_duration": prediction.estimated_duration,
                "confidence": prediction.confidence,
            }
            self.intelligence_metrics["predictions_generated"] += 1

            logger.info(
                f"Resource prediction for {task.task_id}: "
                f"{prediction.estimated_tokens} tokens, "
                f"{prediction.estimated_duration:.1f}s duration "
                f"(confidence: {prediction.confidence:.2f})"
            )

        # Collaboration setup
        if self.agent_mesh:
            capabilities = self._determine_agent_capabilities(task)
            self.agent_mesh.register_agent(task.task_id, capabilities)

            # Handle collaboration patterns
            await self._handle_pre_execution_collaboration(task)

    async def _apply_post_execution_intelligence(
        self, task: EnhancedAgentTask, result: Dict, duration: float
    ):
        """Apply intelligence features after task execution"""

        # Record execution for learning
        if self.resource_predictor:
            metrics = TaskMetrics(
                duration=duration,
                memory_usage=result.get("memory_usage"),
                tokens_used=result.get("tokens_used"),
                status=result.get("status", "completed"),
            )
            self.resource_predictor.record_execution(task, metrics)

        # Update context
        if self.context_broker and self.current_context_id:
            context_updates = self._extract_context_updates(task, result)
            if context_updates:
                await self.context_broker.update_context(
                    self.current_context_id, context_updates
                )
                self.intelligence_metrics["context_updates"] += 1

        # Post-execution collaboration
        if self.agent_mesh:
            await self._handle_post_execution_collaboration(task, result)

    async def _handle_pre_execution_collaboration(self, task: EnhancedAgentTask):
        """Handle collaboration before task execution"""

        # Expert consultation for complex tasks
        if hasattr(task, "expert_domains_needed") and task.expert_domains_needed:
            for domain in task.expert_domains_needed:
                consultation = await self.agent_mesh.collaboration_patterns.get(
                    "expert_consultation", lambda *args: {"success": False}
                )(task.task_id, task.prompt, domain)

                if consultation["success"]:
                    self.intelligence_metrics["collaboration_events"] += 1
                    logger.info(f"Expert consultation successful for domain: {domain}")

    async def _handle_post_execution_collaboration(
        self, task: EnhancedAgentTask, result: Dict
    ):
        """Handle collaboration after task execution"""
        # Share results with interested agents
        if result.get("status") == "completed":
            # Broadcast successful completion
            pass  # Implementation can be added based on needs

    def _extract_context_updates(self, task: EnhancedAgentTask, result: Dict) -> Dict:
        """Extract context updates from task results"""
        updates = {"task_id": task.task_id}

        # Extract artifacts
        if "files_created" in result:
            updates["artifacts"] = {f"{task.task_id}_output": result["files_created"]}

        # Extract knowledge
        if "insights" in result or "findings" in result:
            updates["knowledge"] = {
                task.task_id: {
                    "insights": result.get("insights", []),
                    "findings": result.get("findings", []),
                }
            }

        # Extract decisions
        if "decisions_made" in result:
            updates["decision"] = result["decisions_made"]

        return updates if len(updates) > 1 else {}

    def _determine_agent_capabilities(self, task: EnhancedAgentTask) -> List[str]:
        """Determine agent capabilities based on task"""
        capabilities = []

        task_type_mapping = {
            "research": ["information_gathering", "analysis"],
            "code": ["programming", "software_development"],
            "design": ["system_design", "architecture"],
            "test": ["testing", "quality_assurance"],
            "review": ["code_review", "quality_control"],
            "documentation": ["technical_writing", "documentation"],
        }

        if task.task_type in task_type_mapping:
            capabilities.extend(task_type_mapping[task.task_type])

        return capabilities

    async def execute_batch_with_optimization(
        self, tasks: List[EnhancedAgentTask]
    ) -> List[Dict]:
        """Execute batch with intelligent optimization"""

        if not self.enable_resource_prediction or not self.resource_predictor:
            return await self.execute_batch(tasks)

        # Generate predictions for all tasks
        predictions = {}
        for task in tasks:
            predictions[task.task_id] = self.resource_predictor.predict_resources(task)

        # Create optimized execution batches
        optimized_batches = self._create_optimal_batches(tasks, predictions)

        logger.info(
            f"Resource optimization: {len(optimized_batches)} optimized batches "
            f"for {len(tasks)} tasks"
        )

        # Execute optimized batches
        all_results = []
        for batch_num, batch_tasks in enumerate(optimized_batches):
            logger.info(
                f"Executing optimized batch {batch_num + 1}/{len(optimized_batches)}"
            )

            batch_results = await asyncio.gather(
                *[self.execute_agent_enhanced(task) for task in batch_tasks],
                return_exceptions=True,
            )

            # Process results
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Batch execution error: {result}")
                    all_results.append(
                        {"task_id": "unknown", "status": "failed", "error": str(result)}
                    )
                else:
                    all_results.append(result)

        return all_results

    def _create_optimal_batches(
        self, tasks: List[EnhancedAgentTask], predictions: Dict
    ) -> List[List[EnhancedAgentTask]]:
        """Create optimal execution batches based on predictions"""

        # Sort tasks by resource efficiency
        task_scores = []
        for task in tasks:
            pred = predictions.get(task.task_id)
            if pred:
                # Score combines efficiency metrics
                score = (
                    pred.parallel_compatibility * 0.4
                    + (1 - min(pred.estimated_tokens / 8000, 1.0)) * 0.3
                    + pred.confidence * 0.3  # Token efficiency
                )
            else:
                score = 0.5  # Default score

            task_scores.append((score, task))

        task_scores.sort(reverse=True, key=lambda x: x[0])

        # Create batches respecting dependencies and resource limits
        batches = []
        remaining_tasks = [task for _, task in task_scores]

        while remaining_tasks:
            batch = []
            batch_tokens = 0

            # Find tasks that can run together
            i = 0
            while i < len(remaining_tasks) and len(batch) < self.max_parallel:
                task = remaining_tasks[i]
                pred = predictions.get(task.task_id)

                # Check resource constraints
                task_tokens = pred.estimated_tokens if pred else 2000
                if batch_tokens + task_tokens <= 8000:  # Token limit
                    # Check dependencies
                    deps_satisfied = all(
                        dep not in [t.task_id for t in remaining_tasks]
                        for dep in task.dependencies
                    )

                    if deps_satisfied:
                        batch.append(task)
                        batch_tokens += task_tokens
                        remaining_tasks.pop(i)
                        continue

                i += 1

            if batch:
                batches.append(batch)
            elif remaining_tasks:
                # Force add the first task to avoid infinite loop
                batch.append(remaining_tasks.pop(0))
                batches.append(batch)

        return batches

    async def get_intelligence_report(self) -> Dict[str, Any]:
        """Get comprehensive intelligence report"""
        report = {
            "intelligence_metrics": self.intelligence_metrics,
            "features_enabled": {
                "intelligent_gates": self.enable_intelligent_gates,
                "context_management": self.enable_context_management,
                "resource_prediction": self.enable_resource_prediction,
                "collaboration": self.enable_collaboration,
                "adaptation": self.enable_adaptation,
            },
        }

        # Add component-specific reports
        if self.resource_predictor:
            report["resource_predictor"] = {
                "execution_history_size": len(
                    self.resource_predictor.execution_history
                ),
                "task_patterns": len(self.resource_predictor.task_patterns),
            }

        if self.context_broker:
            report["context_broker"] = {
                "active_contexts": len(self.context_broker.active_contexts),
                "current_context_id": self.current_context_id,
            }

        if self.agent_mesh:
            report["agent_mesh"] = {
                "active_agents": len(self.agent_mesh.active_agents),
                "mesh_id": self.agent_mesh.mesh_id,
            }

        if self.adaptation_engine:
            report["adaptation_engine"] = {
                "adaptations_made": len(self.adaptation_engine.adaptation_history)
            }

        return report


# Factory functions for common configurations


def create_intelligent_orchestrator(
    output_dir: Path,
    tokens: List[str] = None,
    max_parallel: int = 10,
    intelligence_level: str = "full",  # "minimal", "standard", "full"
) -> IntelligentOrchestrator:
    """Factory function to create orchestrator with different intelligence levels"""

    if intelligence_level == "minimal":
        return IntelligentOrchestrator(
            output_dir=output_dir,
            tokens=tokens,
            max_parallel=max_parallel,
            enable_intelligent_gates=True,
            enable_context_management=False,
            enable_resource_prediction=False,
            enable_collaboration=False,
            enable_adaptation=False,
        )
    elif intelligence_level == "standard":
        return IntelligentOrchestrator(
            output_dir=output_dir,
            tokens=tokens,
            max_parallel=max_parallel,
            enable_intelligent_gates=True,
            enable_context_management=True,
            enable_resource_prediction=True,
            enable_collaboration=False,
            enable_adaptation=False,
        )
    else:  # "full"
        return IntelligentOrchestrator(
            output_dir=output_dir,
            tokens=tokens,
            max_parallel=max_parallel,
            enable_intelligent_gates=True,
            enable_context_management=True,
            enable_resource_prediction=True,
            enable_collaboration=True,
            enable_adaptation=True,
        )


def create_development_orchestrator(
    output_dir: Path, tokens: List[str] = None
) -> IntelligentOrchestrator:
    """Create orchestrator optimized for software development"""

    intelligence_config = {
        "enabled_gates": ["structure", "dependencies", "prompt", "code_quality"],
        "mesh_id": "development_team",
    }

    return IntelligentOrchestrator(
        output_dir=output_dir,
        tokens=tokens,
        max_parallel=8,  # Good balance for development tasks
        intelligence_config=intelligence_config,
        enable_intelligent_gates=True,
        enable_context_management=True,
        enable_resource_prediction=True,
        enable_collaboration=True,
        enable_adaptation=True,
    )


# Export main classes
__all__ = [
    "IntelligentOrchestrator",
    "create_intelligent_orchestrator",
    "create_development_orchestrator",
]
