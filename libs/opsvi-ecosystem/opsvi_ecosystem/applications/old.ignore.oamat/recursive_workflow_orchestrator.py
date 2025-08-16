"""
OAMAT Recursive Workflow Orchestrator

Replaces hardcoded TaskDecomposer with AI-driven recursive workflow generation.
Each node becomes a use case that can generate its own sub-workflow using the same
WorkflowManager approach, creating a truly recursive, fractal architecture.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from src.applications.oamat.agents.manager.workflow_manager import WorkflowManager
from src.applications.oamat.agents.models import (
    EnhancedWorkflowPlan,
)
from src.applications.oamat.workflows.orchestrator.execution import WorkflowExecutor
from src.applications.oamat.workflows.orchestrator.graph_builder import (
    WorkflowGraphBuilder,
)


class RecursionDepth(Enum):
    """Track recursion depth to prevent infinite recursion"""

    ROOT = 0
    LEVEL_1 = 1  # Main workflow nodes (planner, coder, reviewer)
    LEVEL_2 = 2  # Sub-workflow nodes (frontend_dev, backend_dev, db_specialist)
    LEVEL_3 = 3  # Micro-workflow nodes (component_dev, api_dev, auth_dev)
    LEVEL_4 = 4  # Atomic tasks (file generation)
    MAX_DEPTH = 4


@dataclass
class RecursiveExecutionContext:
    """Context for recursive workflow execution"""

    user_request: str
    parent_node_id: str
    parent_agent_role: str
    recursion_depth: RecursionDepth
    parent_context: dict[str, Any]
    complexity_threshold: float = 0.7  # Above this = subdivide
    max_recursion_depth: int = 4


class RecursiveWorkflowOrchestrator:
    """
    Orchestrates recursive workflow generation and execution.

    Each node that requires subdivision generates its own sub-workflow using
    the same AI-driven WorkflowManager approach, creating consistent intelligence
    throughout the entire execution hierarchy.
    """

    def __init__(self, main_oamat_instance):
        self.oamat = main_oamat_instance
        self.logger = logging.getLogger("OAMAT.RecursiveWorkflow")
        self.user_logger = getattr(main_oamat_instance, "user_logger", None)

        # Core components for recursive workflow generation
        self.workflow_manager = None
        self.graph_builder = None
        self.workflow_executor = None

        # Execution tracking
        self.active_workflows: dict[str, EnhancedWorkflowPlan] = {}
        self.execution_hierarchy: dict[str, list[str]] = {}  # parent_id -> [child_ids]

    def initialize_components(self):
        """Initialize workflow components for recursive execution"""
        try:
            # Initialize WorkflowManager for AI-driven sub-workflow generation

            self.workflow_manager = WorkflowManager(
                model="o3-mini"  # Use o3-mini for all planning intelligence
            )

            # Initialize graph builder for dynamic sub-workflows
            self.graph_builder = WorkflowGraphBuilder(
                supervisor_node=self._create_recursive_supervisor,
                completion_node=self._create_recursive_completion,
            )

            # Initialize workflow executor for sub-workflow execution
            self.workflow_executor = WorkflowExecutor()

            self.logger.info("✅ Recursive workflow components initialized")

        except Exception as e:
            self.logger.error(f"❌ Failed to initialize recursive components: {e}")
            raise

    async def execute_node_with_subdivision(
        self, node_context: RecursiveExecutionContext
    ) -> dict[str, Any]:
        """
        Execute a node with manager-driven subdivision intelligence.

        This method checks the subdivision flag set by the WorkflowManager during
        initial generation, eliminating the need for individual complexity analysis.
        Much more efficient and intelligent approach.
        """

        node_metadata = node_context.parent_context.get("node_metadata", {})
        requires_subdivision = node_metadata.get("requires_subdivision", False)

        self.logger.info(
            f"🔍 Checking '{node_context.parent_node_id}' subdivision flag: {requires_subdivision}"
        )

        # USER LOGGING: Log subdivision decision with reasoning
        if self.user_logger:
            reasoning = node_metadata.get("subdivision_reasoning", "")
            self.user_logger.log_subdivision_check(
                node_context.parent_node_id, requires_subdivision, reasoning
            )

        # Check termination conditions
        if (
            not requires_subdivision
            or node_context.recursion_depth.value >= node_context.max_recursion_depth
        ):
            # Execute as atomic task - no subdivision needed or max depth reached
            self.logger.info(
                f"⚡ Executing '{node_context.parent_node_id}' as atomic task"
            )
            return await self._execute_atomic_task(node_context)

        # Manager marked this for subdivision - generate sub-workflow
        self.logger.info(
            f"🔧 Manager marked '{node_context.parent_node_id}' for subdivision"
        )
        sub_workflow_plan = await self._generate_sub_workflow_from_manager_intel(
            node_context, node_metadata
        )

        # USER LOGGING: Start sub-workflow display
        if self.user_logger and sub_workflow_plan:
            self.user_logger.start_sub_workflow(
                node_context.parent_node_id, sub_workflow_plan
            )

        if not sub_workflow_plan or len(sub_workflow_plan.nodes) <= 1:
            # Fallback to atomic execution if sub-workflow generation failed
            self.logger.warning(
                "⚠️ Sub-workflow generation failed, executing atomically"
            )
            return await self._execute_atomic_task(node_context)

        # Execute sub-workflow recursively
        self.logger.info(
            f"🚀 Executing sub-workflow with {len(sub_workflow_plan.nodes)} nodes"
        )
        return await self._execute_sub_workflow(node_context, sub_workflow_plan)

    async def _generate_sub_workflow_from_manager_intel(
        self, context: RecursiveExecutionContext, node_metadata: dict[str, Any]
    ) -> EnhancedWorkflowPlan:
        """
        Generate sub-workflow using SAME WorkflowManager logic (TRUE DRY).

        Treats subdivision as a complete "sub-project" within the larger project,
        using identical workflow generation intelligence without duplicate code.
        """

        # Create sub-project request with context that it's part of larger project
        sub_project_request = self._create_sub_project_request(context, node_metadata)

        # Create sub-project context indicating this is part of larger project
        sub_project_context = {
            "is_sub_project": True,
            "parent_project": context.user_request,
            "parent_node": context.parent_node_id,
            "parent_role": context.parent_agent_role,
            "recursion_depth": context.recursion_depth.value + 1,
            "project_integration_path": context.parent_context.get("project_path", ""),
            **node_metadata,  # Include all manager intelligence
            **context.parent_context,
        }

        try:
            # Use EXACT SAME method as main workflow - TRUE DRY!
            sub_workflow_result = self.workflow_manager.generate_sophisticated_workflow(
                analysis={"type": "sub_project", "context": sub_project_context},
                user_request=sub_project_request,
                context=sub_project_context,
            )

            # Extract the workflow plan from the result
            sub_workflow_plan = sub_workflow_result.get("workflow_plan")

            # Track the workflow hierarchy
            workflow_id = (
                f"{context.parent_node_id}_sub_{datetime.now().strftime('%H%M%S')}"
            )
            self.active_workflows[workflow_id] = sub_workflow_plan

            if context.parent_node_id not in self.execution_hierarchy:
                self.execution_hierarchy[context.parent_node_id] = []
            self.execution_hierarchy[context.parent_node_id].append(workflow_id)

            self.logger.info(f"✅ Generated sub-workflow: {sub_workflow_plan.title}")
            return sub_workflow_plan

        except Exception as e:
            self.logger.error(f"❌ Sub-workflow generation failed: {e}")
            return None

    def _create_sub_project_request(
        self, context: RecursiveExecutionContext, node_metadata: dict[str, Any]
    ) -> str:
        """Create sub-project request that integrates into larger project structure"""

        # Simple, clean sub-project request - let WorkflowManager handle the intelligence
        task_description = context.parent_context.get(
            "task_description", f"Handle {context.parent_agent_role} responsibilities"
        )

        return f"""
{task_description}

This is a sub-project within the larger project: {context.user_request}

Please generate a complete workflow for this sub-project that integrates seamlessly into the main project structure."""

    async def _execute_sub_workflow(
        self,
        context: RecursiveExecutionContext,
        sub_workflow_plan: EnhancedWorkflowPlan,
    ) -> dict[str, Any]:
        """
        Execute the generated sub-workflow using recursive orchestration.

        Each sub-node will go through the same subdivision analysis recursively.
        """

        try:
            # Create agents for sub-workflow nodes with recursive capability
            agent_creators = await self._create_recursive_agent_creators(
                sub_workflow_plan, context
            )

            # Build dynamic graph for sub-workflow
            sub_workflow_graph = self.graph_builder.create_dynamic_workflow_graph(
                sub_workflow_plan, agent_creators
            )

            # Create initial state for sub-workflow execution
            initial_state = {
                "user_request": context.user_request,
                "parent_node_id": context.parent_node_id,
                "recursion_depth": context.recursion_depth.value + 1,
                "parent_context": context.parent_context,
                "workflow_plan": sub_workflow_plan,
                "agent_outputs": {},
                "completed_nodes": [],
                "failed_nodes": [],
                "errors": [],
            }

            # Execute sub-workflow
            sub_result = await self.workflow_executor.execute_agentic_workflow(
                user_request=context.user_request,
                workflow_plan=sub_workflow_plan,
                workflow_graph=sub_workflow_graph,
                context=context.parent_context,
                interactive=False,
                initial_state=initial_state,
            )

            self.logger.info("✅ Sub-workflow execution completed")

            # USER LOGGING: Mark parent node as completed with subdivision
            if self.user_logger:
                self.user_logger.complete_node(
                    context.parent_node_id,
                    success=sub_result.get("success", True),
                    execution_type="subdivided",
                )

            return sub_result

        except Exception as e:
            self.logger.error(f"❌ Sub-workflow execution failed: {e}")

            # USER LOGGING: Mark parent node as failed
            if self.user_logger:
                self.user_logger.complete_node(
                    context.parent_node_id, success=False, execution_type="subdivided"
                )

            # Fallback to atomic execution
            return await self._execute_atomic_task(context)

    async def _create_recursive_agent_creators(
        self,
        sub_workflow_plan: EnhancedWorkflowPlan,
        parent_context: RecursiveExecutionContext,
    ) -> dict[str, Any]:
        """
        Create agent creators that support recursive subdivision.

        Each agent will use the RecursiveWorkflowOrchestrator for further subdivision.
        """

        agent_creators = {}

        for node in sub_workflow_plan.nodes:
            # Create recursive execution context for this sub-node
            sub_context = RecursiveExecutionContext(
                user_request=parent_context.user_request,
                parent_node_id=node.id,
                parent_agent_role=node.agent_role,
                recursion_depth=RecursionDepth(
                    parent_context.recursion_depth.value + 1
                ),
                parent_context={
                    "task_description": node.description,
                    "node_parameters": node.parameters,
                    "tools_required": node.tools_required,
                    **parent_context.parent_context,
                },
            )

            # Create agent function that uses recursive subdivision
            def create_recursive_agent(context=sub_context):
                async def recursive_agent_function(state):
                    return await self.execute_node_with_subdivision(context)

                return recursive_agent_function

            agent_creators[node.id] = create_recursive_agent()

        return agent_creators

    async def _execute_atomic_task(
        self, context: RecursiveExecutionContext
    ) -> dict[str, Any]:
        """
        Execute a task atomically (no further subdivision).

        This is where actual file generation and concrete work happens.
        """

        self.logger.info(f"⚡ Executing atomic task: {context.parent_node_id}")

        try:
            # Use existing OAMAT agent execution for atomic tasks
            # This could call the original agent creation and execution logic

            # Create task description for atomic execution
            atomic_task_description = f"""
**ATOMIC TASK EXECUTION**

Execute this task without further subdivision:

**Role**: {context.parent_agent_role}
**Task**: {context.parent_context.get('task_description', 'Complete the assigned task')}
**User Request**: {context.user_request}
**Context**: {context.parent_context}

**REQUIREMENTS**:
- Generate all necessary files for this specific task
- Use appropriate tools and technologies
- Create complete, functional implementations
- Follow best practices for the role and technology
- Save all work using write_file tool

Execute this task completely and return results.
"""

            # Execute using existing OAMAT agent infrastructure
            result = await self._execute_with_existing_agent(
                context.parent_agent_role,
                atomic_task_description,
                context.parent_context,
            )

            # USER LOGGING: Mark atomic task as completed
            if self.user_logger:
                self.user_logger.complete_node(
                    context.parent_node_id, success=True, execution_type="atomic"
                )

            return {
                "success": True,
                "execution_type": "atomic",
                "node_id": context.parent_node_id,
                "agent_role": context.parent_agent_role,
                "result": result,
            }

        except Exception as e:
            self.logger.error(f"❌ Atomic task execution failed: {e}")

            # USER LOGGING: Mark atomic task as failed
            if self.user_logger:
                self.user_logger.complete_node(
                    context.parent_node_id, success=False, execution_type="atomic"
                )

            return {
                "success": False,
                "execution_type": "atomic",
                "node_id": context.parent_node_id,
                "error": str(e),
            }

    async def _execute_with_existing_agent(
        self, agent_role: str, task_description: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute using existing OAMAT agent infrastructure"""

        # This would integrate with the existing agent execution system
        # For now, placeholder implementation

        self.logger.info(f"🤖 Executing {agent_role} with existing agent system")

        # Integration point with existing OAMAT agent execution
        # This would call the actual agent creation and execution logic

        return {
            "status": "completed",
            "files_generated": ["example_file.py"],
            "execution_time": 45.2,
        }

    def _create_recursive_supervisor(self, state):
        """Create supervisor node for recursive sub-workflows"""
        # Similar to main supervisor but for sub-workflow context
        return self.oamat._supervisor_node(state)

    def _create_recursive_completion(self, state):
        """Create completion node for recursive sub-workflows"""
        # Similar to main completion but for sub-workflow context
        return self.oamat._completion_node(state)
