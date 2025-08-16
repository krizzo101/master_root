from typing import Any, Dict, Optional, List, Type
import asyncio
import uuid
import os
from dataclasses import asdict

from .tasks import execute_plugin_task
from .plugins.base_plugin import BasePlugin
from .plugins.plugin_manager import PluginManager
from .plugins.types import ExecutionContext, PluginConfig
from .plugins.ai_mixin import shared_ai_manager
from .workflow import WorkflowManager, WorkflowStep, WorkflowState
from .event_bus import EventBus
from .cognitive_database_client import CognitiveArangoDBClient


from .shared.logging_manager import get_logger

logger = get_logger(__name__)


class Orchestrator:
    """
    The main component responsible for orchestrating plugin execution based on workflows.
    """

    def __init__(
        self,
        plugins: List[Type[BasePlugin]],
        workflow_manager: WorkflowManager,
        ai_config: Optional[Dict[str, Any]] = None,
    ):
        self.plugin_manager = PluginManager(plugins=plugins)
        self.workflow_manager = workflow_manager
        self.plugin_dir = None  # No longer needed
        self.event_bus = EventBus()

        # Initialize shared AI manager for all plugins
        api_key = os.getenv("OPENAI_API_KEY")
        if ai_config and "openai_api_key" in ai_config:
            api_key = ai_config["openai_api_key"]

        if api_key:
            shared_ai_manager.initialize(api_key, ai_config or {})
            print("Shared AI manager initialized for all plugins")
        else:
            print("Warning: No OpenAI API key found - AI features will be disabled")

        # Initialize cognitive database client with correct connection parameters
        self.db_client = CognitiveArangoDBClient(
            host="http://127.0.0.1:8531",
            database="asea_prod_db",
            username="root",
            password="arango_production_password",
        )
        self._db_connected = False  # Initialize _db_connected attribute
        self.plugin_configs: Dict[str, PluginConfig] = {}

        print("Orchestrator discovered the following plugins:")
        for plugin_class in self.plugin_manager.plugins:
            print(f"- {plugin_class.get_name()}")

    def temp_configure_plugins(self, configs: Dict[str, PluginConfig]):
        """
        Temporarily stores plugin configs to be sent to tasks.
        """
        print("\nStoring plugin configs for dispatch...")
        self.plugin_configs = configs

    async def run_workflow(
        self,
        workflow_name: str,
        initial_state: Dict[str, Any] = None,
        run_id: str = None,
    ) -> Dict[str, Any]:
        """Runs a complete workflow from start to finish."""
        # Check if database client is available and connect if needed
        if self.db_client and not self._db_connected:
            connected = await self.db_client.connect()
            if connected:
                self._db_connected = True
                print(
                    "Connected to ArangoDB cognitive architecture for intelligent state management"
                )

        workflow = self.workflow_manager.get_workflow(workflow_name)
        if not workflow:
            raise ValueError(f"Workflow '{workflow_name}' not found.")

        # 1. Load or create workflow state
        if run_id:
            workflow_run_state = await self._load_checkpoint(run_id)
            if workflow_run_state:
                print(
                    f"Resuming workflow run {run_id} from step {workflow_run_state.current_step}"
                )
                # Reset status to RUNNING when resuming
                workflow_run_state.status = "RUNNING"
            else:
                print(
                    f"Run ID {run_id} provided but no checkpoint found. Starting new workflow."
                )
                workflow_run_state = WorkflowState(
                    run_id=run_id,
                    workflow_name=workflow_name,
                    status="RUNNING",
                    current_step=0,
                    state=initial_state.copy() if initial_state else {},
                )
                workflow_run_state.state["run_id"] = run_id
                await self._save_checkpoint(workflow_run_state)  # Save initial state
                print(f"Starting new workflow run {run_id}")
        else:
            print(f"Run ID {run_id} not provided. Starting new workflow.")
            workflow_run_state = WorkflowState(
                run_id=str(uuid.uuid4()),
                workflow_name=workflow_name,
                status="RUNNING",
                current_step=0,
                state=initial_state.copy() if initial_state else {},
            )
            workflow_run_state.state["run_id"] = workflow_run_state.run_id
            await self._save_checkpoint(workflow_run_state)  # Save initial state
            print(f"Starting new workflow run {workflow_run_state.run_id}")

        await self.event_bus.publish(
            "workflow_started",
            {"workflow_name": workflow_name, "run_id": workflow_run_state.run_id},
        )

        # 2. Get the workflow definition
        workflow = self.workflow_manager.get_workflow(workflow_name)
        if not workflow:
            raise ValueError(f"Workflow '{workflow_name}' not found.")

        # 3. Main execution loop
        start_step_index = workflow_run_state.current_step

        for i in range(start_step_index, len(workflow.steps)):
            step = workflow.steps[i]
            workflow_run_state.current_step = i

            # Checkpoint before executing the step
            await self._save_checkpoint(workflow_run_state)

            result_delta = await self._execute_step(step, workflow_run_state)

            workflow_run_state.state.update(result_delta)

            if not result_delta.get("success", True):
                workflow_run_state.status = "FAILED"
                await self._save_checkpoint(
                    workflow_run_state
                )  # Save final failed state
                break

            # Checkpoint after a successful step
            await self._save_checkpoint(workflow_run_state)

        # 5. Finalization
        if workflow_run_state.status != "FAILED":
            workflow_run_state.status = "COMPLETED"
            await self._save_checkpoint(
                workflow_run_state
            )  # Save final completed state

        await self.event_bus.publish(
            "workflow_finished",
            {"workflow_name": workflow_name, "run_id": workflow_run_state.run_id},
        )

        print(
            f"\n--- Workflow {workflow_name} (Run ID: {workflow_run_state.run_id}) finished "
            f"with status: {workflow_run_state.status} ---"
        )

        # Analyze patterns for compound learning if workflow completed successfully
        if workflow_run_state.status == "COMPLETED":
            try:
                analysis = await self.analyze_workflow_patterns()
                if "error" not in analysis:
                    print(
                        f"Pattern analysis: {analysis['total_patterns']} patterns, {analysis['high_quality_patterns']} high-quality"
                    )
            except Exception as e:
                logger.warning(f"Pattern analysis failed: {e}")

        return workflow_run_state.state

    async def cleanup(self):
        """Cleanup orchestrator resources including shared AI manager."""
        await shared_ai_manager.cleanup_all_clients()
        if self.db_client:
            # Cleanup temporary data and disconnect
            await self.db_client.cleanup_temporary_data()
            await self.db_client.disconnect()

    async def analyze_workflow_patterns(self) -> Dict[str, Any]:
        """Analyze successful workflow patterns for compound learning."""
        if not self._db_connected:
            return {"error": "Database not connected"}

        try:
            patterns = await self.db_client.get_workflow_patterns(limit=100)

            analysis = {
                "total_patterns": len(patterns),
                "high_quality_patterns": len(
                    [p for p in patterns if p.get("confidence_score", 0) > 0.8]
                ),
                "common_success_factors": self._extract_success_factors(patterns),
                "optimization_opportunities": self._identify_optimizations(patterns),
            }

            # Create semantic relationships between related patterns
            await self._create_pattern_relationships(patterns)

            return analysis

        except Exception as e:
            logger.error(f"Failed to analyze workflow patterns: {e}")
            return {"error": str(e)}

    def _extract_success_factors(self, patterns: List[Dict[str, Any]]) -> List[str]:
        """Extract common success factors from workflow patterns."""
        success_factors = {}

        for pattern in patterns:
            content = pattern.get("knowledge_content", {})
            for factor in content.get("success_patterns", []):
                success_factors[factor] = success_factors.get(factor, 0) + 1

        # Return factors that appear in multiple patterns
        return [factor for factor, count in success_factors.items() if count >= 2]

    def _identify_optimizations(
        self, patterns: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Identify optimization opportunities from pattern analysis."""
        optimizations = []

        # Analyze execution times
        fast_patterns = [
            p
            for p in patterns
            if p.get("knowledge_content", {}).get("execution_time", 999) < 30
        ]
        if fast_patterns:
            optimizations.append(
                {
                    "type": "execution_speed",
                    "opportunity": "Fast execution patterns identified",
                    "count": len(fast_patterns),
                }
            )

        # Analyze quality scores
        high_quality = [
            p
            for p in patterns
            if p.get("knowledge_content", {}).get("quality_score", 0) >= 9
        ]
        if high_quality:
            optimizations.append(
                {
                    "type": "quality_optimization",
                    "opportunity": "High-quality patterns for replication",
                    "count": len(high_quality),
                }
            )

        return optimizations

    async def _create_pattern_relationships(self, patterns: List[Dict[str, Any]]):
        """Create semantic relationships between related workflow patterns."""
        try:
            for i, pattern1 in enumerate(patterns):
                for pattern2 in patterns[i + 1 :]:
                    similarity = self._calculate_pattern_similarity(pattern1, pattern2)

                    if similarity > 0.7:
                        await self.db_client.create_semantic_relationship(
                            pattern1["concept_id"],
                            pattern2["concept_id"],
                            "compounds_with",
                            similarity,
                        )
        except Exception as e:
            logger.error(f"Failed to create pattern relationships: {e}")

    def _calculate_pattern_similarity(
        self, pattern1: Dict[str, Any], pattern2: Dict[str, Any]
    ) -> float:
        """Calculate similarity between two workflow patterns."""
        content1 = pattern1.get("knowledge_content", {})
        content2 = pattern2.get("knowledge_content", {})

        # Check for common success patterns
        patterns1 = set(content1.get("success_patterns", []))
        patterns2 = set(content2.get("success_patterns", []))

        if not patterns1 or not patterns2:
            return 0.0

        common_patterns = patterns1.intersection(patterns2)
        total_patterns = patterns1.union(patterns2)

        return len(common_patterns) / len(total_patterns) if total_patterns else 0.0

    async def _execute_step(
        self, step: WorkflowStep, workflow_run_state: WorkflowState
    ) -> Dict[str, Any]:
        """Helper to dispatch step execution based on type."""
        # Note: Parallel and control flow logic would need significant
        # redesign for a distributed model. Focusing on single step for now.
        return await self._run_single_step(
            step,
            workflow_run_state,
            self.plugin_configs.get(step.plugin_name),
        )

    async def _save_checkpoint(self, workflow_state: WorkflowState):
        """Saves the workflow state to cognitive architecture with quality filtering."""
        if self._db_connected:
            # Convert WorkflowState to dict for storage
            state_dict = {
                "run_id": workflow_state.run_id,
                "workflow_name": workflow_state.workflow_name,
                "status": workflow_state.status,
                "current_step": workflow_state.current_step,
                "state": workflow_state.state,
                "quality_score": workflow_state.state.get("quality_score", 0),
                "execution_time": workflow_state.state.get("execution_time", 0),
            }
            success = await self.db_client.save_workflow_state(
                workflow_state.run_id, state_dict
            )
            if success:
                print(
                    f"Saved cognitive checkpoint for run {workflow_state.run_id} at step {workflow_state.current_step}"
                )
            else:
                print(
                    f"Failed to save cognitive checkpoint for run {workflow_state.run_id}"
                )
        else:
            print(
                f"Database not connected - cognitive checkpoint for run {workflow_state.run_id} not saved"
            )

    async def _load_checkpoint(self, run_id: str) -> Optional[WorkflowState]:
        """Loads a workflow state from cognitive architecture."""
        if self._db_connected:
            data = await self.db_client.load_workflow_state(run_id)
            if data:
                print(f"Loaded cognitive checkpoint for run {run_id}")
                # Reconstruct WorkflowState from stored data
                return WorkflowState(
                    run_id=data["run_id"],
                    workflow_name=data["workflow_name"],
                    status=data["status"],
                    current_step=data["current_step"],
                    state=data["state"],
                )
        return None

    async def _run_single_step(
        self,
        step: WorkflowStep,
        workflow_run_state: WorkflowState,
        plugin_config: PluginConfig,
    ) -> Dict[str, Any]:
        """Runs a single plugin step."""

        max_attempts = step.retry.get("count", 1) if step.retry else 1
        delay = step.retry.get("delay", 0) if step.retry else 0
        state_delta = {}

        for attempt in range(max_attempts):
            await self.event_bus.publish(
                "step_started", {"step": step.plugin_name, "attempt": attempt + 1}
            )

            # Create properly mapped execution context
            mapped_context = self._create_execution_context(
                workflow_run_state.workflow_name,
                workflow_run_state.current_step,
                step,
                workflow_run_state.state,
            )

            # Dispatch the task to Celery
            task = execute_plugin_task.delay(
                plugin_name=step.plugin_name,
                config=asdict(plugin_config),
                context=asdict(mapped_context),
            )

            # This is a simple blocking wait. A more advanced implementation
            # would handle this asynchronously.
            result_dict = task.get(
                timeout=300
            )  # Wait for the result from the worker (5 minutes for AI processing)

            # Reconstruct the result object
            from .plugins.types import PluginResult

            result = PluginResult(**result_dict)

            await self.event_bus.publish(
                "step_completed", {"step": step.plugin_name, "success": result.success}
            )

            state_delta = {"success": result.success}
            if result.success:
                if result.data:
                    # Apply output mapping: plugin_output_key -> state_key
                    for plugin_output_key, state_key in step.outputs.items():
                        if plugin_output_key in result.data:
                            state_delta[state_key] = result.data[plugin_output_key]
                break  # Success, exit retry loop

            # Failure case
            state_delta["error_message"] = result.error_message

            # Apply output mapping even for failed results to preserve tracking data
            if result.data:
                for plugin_output_key, state_key in step.outputs.items():
                    if plugin_output_key in result.data:
                        state_delta[state_key] = result.data[plugin_output_key]

            if attempt < max_attempts - 1:
                print(
                    f"!! Step {workflow_run_state.current_step+1} ({step.plugin_name}) failed. Retrying in {delay}s..."
                )
                await asyncio.sleep(delay)
            else:
                print(
                    f"!! Step {workflow_run_state.current_step+1} ({step.plugin_name}) failed on final attempt: {result.error_message}"
                )

        return state_delta

    def _create_execution_context(
        self, workflow_name, step_index, step, workflow_state
    ):
        """Creates an execution context with properly mapped inputs."""
        # Start with a copy of the workflow state
        step_state = workflow_state.copy()

        # Apply input mapping: plugin_param -> state_key
        for plugin_param, state_key in step.inputs.items():
            if state_key in workflow_state:
                step_state[plugin_param] = workflow_state[state_key]

        # Add any step parameters
        step_state.update(step.parameters)

        return ExecutionContext(
            workflow_id=workflow_name, task_id=f"step-{step_index+1}", state=step_state
        )
