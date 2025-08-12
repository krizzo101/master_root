"""
OAMAT Workflow Node Integration with Context Abstraction
Shows how parent nodes integrate the context abstraction system to prevent
information overload while maintaining essential information flow.
"""

from typing import Any, Dict, List

from langchain_core.runnables import RunnableLambda
from langgraph.graph import START, StateGraph

from src.applications.oamat.context_abstraction import (
    AbstractedSummary,
    AbstractionLevel,
    ChildWorkflowResult,
    ParentNodeContextManager,
)
from src.applications.oamat.models.workflow_models import (
    AgentRole,
    EnhancedWorkflowNode,
    OAMATState,
)


class ContextAwareWorkflowNode(EnhancedWorkflowNode):
    """
    Enhanced workflow node that uses context abstraction to prevent
    information overload from child workflows
    """

    def __init__(
        self,
        node_id: str,
        description: str,
        agent_role: AgentRole,
        abstraction_level: AbstractionLevel,
        parent_context: str,
        **kwargs,
    ):
        super().__init__(
            node_id=node_id, description=description, agent_role=agent_role, **kwargs
        )
        self.abstraction_level = abstraction_level
        self.parent_context = parent_context
        self.context_manager = ParentNodeContextManager(
            abstraction_level=abstraction_level, parent_context=parent_context
        )

    async def process_child_workflows(
        self, child_workflow_results: List[Dict[str, Any]]
    ) -> AbstractedSummary:
        """
        Process results from child workflows with intelligent context abstraction
        """

        # Convert raw child results to structured format
        structured_results = []
        for raw_result in child_workflow_results:
            child_result = ChildWorkflowResult(
                workflow_id=raw_result.get("workflow_id", "unknown"),
                agent_role=raw_result.get("agent_role", "unknown"),
                task_description=raw_result.get("task_description", ""),
                completion_status=raw_result.get("status", "unknown"),
                key_decisions=raw_result.get("decisions", []),
                technical_details=raw_result.get("technical_details", {}),
                dependencies_created=raw_result.get("dependencies", []),
                risks_identified=raw_result.get("risks", []),
                resource_usage=raw_result.get("resources", {}),
                deliverables=raw_result.get("deliverables", []),
                raw_output=raw_result.get("raw_output", ""),
            )
            structured_results.append(child_result)

        # Get abstracted summary appropriate for this parent's level
        abstracted_summary = await self.context_manager.process_child_results(
            structured_results
        )

        return abstracted_summary


class ContextAwareWorkflowManager:
    """
    Workflow manager that creates context-aware nodes with appropriate
    abstraction levels based on hierarchy position
    """

    def __init__(self):
        self.hierarchy_levels = {
            0: AbstractionLevel.EXECUTIVE,  # Root level - strategic overview
            1: AbstractionLevel.MANAGERIAL,  # First subdivision - tactical coordination
            2: AbstractionLevel.OPERATIONAL,  # Second subdivision - detailed implementation
            3: AbstractionLevel.TECHNICAL,  # Leaf nodes - full technical details
        }

    def create_workflow_node(
        self, node_spec: Dict[str, Any], hierarchy_depth: int, parent_context: str
    ) -> ContextAwareWorkflowNode:
        """
        Create a workflow node with appropriate abstraction level
        based on its position in the hierarchy
        """

        # Determine abstraction level based on hierarchy depth
        abstraction_level = self.hierarchy_levels.get(
            hierarchy_depth,
            AbstractionLevel.TECHNICAL,  # Default to technical for deep hierarchies
        )

        return ContextAwareWorkflowNode(
            node_id=node_spec["id"],
            description=node_spec["description"],
            agent_role=AgentRole(node_spec["agent_role"]),
            abstraction_level=abstraction_level,
            parent_context=parent_context,
            requires_subdivision=node_spec.get("requires_subdivision", False),
            estimated_sub_nodes=node_spec.get("estimated_sub_nodes", 0),
            complexity_score=node_spec.get("complexity_score", 5),
            dependencies=node_spec.get("dependencies", []),
        )

    async def create_enhanced_workflow_plan(
        self, user_request: str, complexity_assessment: Dict[str, Any]
    ) -> StateGraph:
        """
        Create enhanced workflow plan with context abstraction at each level
        """

        # Create root workflow graph
        workflow_graph = StateGraph(OAMATState)

        # Add START node
        workflow_graph.add_node("start", self._create_start_node())

        # Create context-aware supervisor for this level
        supervisor_node = self._create_context_aware_supervisor(
            hierarchy_depth=0, parent_context=f"User Request: {user_request}"
        )
        workflow_graph.add_node("supervisor", supervisor_node)

        # Add workflow nodes based on complexity assessment
        if complexity_assessment["requires_subdivision"]:
            await self._add_subdivided_nodes(
                workflow_graph,
                complexity_assessment,
                hierarchy_depth=1,
                parent_context=user_request,
            )
        else:
            # Simple workflow - single execution node
            execution_node = self._create_context_aware_execution_node(
                hierarchy_depth=1, parent_context=user_request
            )
            workflow_graph.add_node("execute", execution_node)

        # Add END node
        workflow_graph.add_node("end", self._create_end_node())

        # Define edges
        workflow_graph.add_edge(START, "start")
        workflow_graph.add_edge("start", "supervisor")
        # Additional edges added by _add_subdivided_nodes or for simple execution

        return workflow_graph.compile()

    def _create_context_aware_supervisor(
        self, hierarchy_depth: int, parent_context: str
    ) -> RunnableLambda:
        """
        Create supervisor node that uses context abstraction for child result processing
        """

        abstraction_level = self.hierarchy_levels.get(
            hierarchy_depth, AbstractionLevel.TECHNICAL
        )
        context_manager = ParentNodeContextManager(abstraction_level, parent_context)

        async def supervisor_logic(state: OAMATState) -> Dict[str, Any]:
            """
            Supervisor logic with context abstraction
            """

            # Check if we have child workflow results to process
            if "child_results" in state and state["child_results"]:
                # Process child results with context abstraction
                abstracted_summary = await context_manager.process_child_results(
                    state["child_results"]
                )

                # Update state with abstracted information instead of raw details
                state["processed_results"] = {
                    "summary": abstracted_summary.executive_summary,
                    "key_outcomes": abstracted_summary.key_outcomes,
                    "critical_dependencies": abstracted_summary.critical_dependencies,
                    "escalated_risks": abstracted_summary.escalated_risks,
                    "confidence_level": abstracted_summary.confidence_level,
                }

                # Determine if escalation to parent level is needed
                if context_manager.should_escalate_to_parent(abstracted_summary):
                    state["escalate_to_parent"] = True
                    state[
                        "escalation_reason"
                    ] = "Critical issues or low confidence detected"

                # Clear raw child results to prevent context pollution
                state["child_results"] = []

            # Make routing decision based on abstracted information
            next_action = self._determine_next_action(state, abstraction_level)

            return {
                **state,
                "next_action": next_action,
                "abstraction_level": abstraction_level.name,
            }

        return RunnableLambda(supervisor_logic)

    def _create_context_aware_execution_node(
        self, hierarchy_depth: int, parent_context: str
    ) -> RunnableLambda:
        """
        Create execution node that produces appropriately abstracted results
        """

        abstraction_level = self.hierarchy_levels.get(
            hierarchy_depth, AbstractionLevel.TECHNICAL
        )

        async def execution_logic(state: OAMATState) -> Dict[str, Any]:
            """
            Execution logic that produces results appropriate for parent abstraction level
            """

            # Execute the actual work (this would be the agent execution)
            execution_result = await self._execute_agent_work(state)

            # Format result based on what parent level needs
            if abstraction_level == AbstractionLevel.EXECUTIVE:
                # Executive level - strategic overview only
                formatted_result = {
                    "outcome": execution_result.get("high_level_outcome", ""),
                    "business_impact": execution_result.get("business_impact", ""),
                    "strategic_decisions": execution_result.get("key_decisions", [])[
                        :2
                    ],
                    "escalated_risks": execution_result.get("critical_risks", []),
                }

            elif abstraction_level == AbstractionLevel.MANAGERIAL:
                # Managerial level - tactical summary
                formatted_result = {
                    "tactical_outcome": execution_result.get("outcome", ""),
                    "architecture_decisions": execution_result.get("architecture", {}),
                    "resource_requirements": execution_result.get("resources", {}),
                    "implementation_risks": execution_result.get("risks", []),
                    "dependencies": execution_result.get("dependencies", []),
                }

            elif abstraction_level == AbstractionLevel.OPERATIONAL:
                # Operational level - implementation details
                formatted_result = {
                    "implementation_details": execution_result.get(
                        "implementation", {}
                    ),
                    "technical_specifications": execution_result.get("tech_specs", {}),
                    "testing_requirements": execution_result.get("testing", []),
                    "operational_risks": execution_result.get("risks", []),
                }

            else:  # TECHNICAL level
                # Technical level - full details
                formatted_result = execution_result  # Full details preserved

            return {
                **state,
                "result": formatted_result,
                "completion_status": "completed",
                "abstraction_level": abstraction_level.name,
            }

        return RunnableLambda(execution_logic)

    async def _add_subdivided_nodes(
        self,
        workflow_graph: StateGraph,
        complexity_assessment: Dict[str, Any],
        hierarchy_depth: int,
        parent_context: str,
    ) -> None:
        """
        Add subdivided workflow nodes with appropriate context abstraction
        """

        sub_workflows = complexity_assessment.get("sub_workflows", [])

        for i, sub_workflow_spec in enumerate(sub_workflows):
            node_id = f"sub_workflow_{i}"

            # Create context-aware sub-workflow node
            sub_workflow_node = self.create_workflow_node(
                node_spec=sub_workflow_spec,
                hierarchy_depth=hierarchy_depth,
                parent_context=parent_context,
            )

            # If this sub-workflow also requires subdivision, recursively create
            if sub_workflow_spec.get("requires_subdivision", False):
                # Create another level of subdivision
                sub_graph = await self.create_enhanced_workflow_plan(
                    user_request=sub_workflow_spec["description"],
                    complexity_assessment=sub_workflow_spec,
                )

                # Wrap sub-graph with context abstraction
                wrapped_node = self._wrap_subgraph_with_abstraction(
                    sub_graph, hierarchy_depth + 1, sub_workflow_spec["description"]
                )
                workflow_graph.add_node(node_id, wrapped_node)
            else:
                # Leaf node - direct execution
                execution_node = self._create_context_aware_execution_node(
                    hierarchy_depth=hierarchy_depth + 1,
                    parent_context=sub_workflow_spec["description"],
                )
                workflow_graph.add_node(node_id, execution_node)

            # Add edges from supervisor to sub-workflows
            workflow_graph.add_edge("supervisor", node_id)

    def _wrap_subgraph_with_abstraction(
        self, sub_graph: StateGraph, hierarchy_depth: int, context: str
    ) -> RunnableLambda:
        """
        Wrap a sub-graph with context abstraction to filter results for parent
        """

        abstraction_level = self.hierarchy_levels.get(
            hierarchy_depth, AbstractionLevel.TECHNICAL
        )
        context_manager = ParentNodeContextManager(abstraction_level, context)

        async def wrapped_execution(state: OAMATState) -> Dict[str, Any]:
            """
            Execute sub-graph and abstract results for parent consumption
            """

            # Execute the sub-graph
            sub_result = await sub_graph.ainvoke(state)

            # Convert sub-graph results to ChildWorkflowResult format
            child_results = [
                ChildWorkflowResult(
                    workflow_id=f"subgraph_{hierarchy_depth}",
                    agent_role="sub_workflow",
                    task_description=context,
                    completion_status=sub_result.get("completion_status", "completed"),
                    key_decisions=sub_result.get("decisions", []),
                    technical_details=sub_result.get("technical_details", {}),
                    dependencies_created=sub_result.get("dependencies", []),
                    risks_identified=sub_result.get("risks", []),
                    resource_usage=sub_result.get("resources", {}),
                    deliverables=sub_result.get("deliverables", []),
                    raw_output=str(sub_result),
                )
            ]

            # Abstract the results for parent consumption
            abstracted_summary = await context_manager.process_child_results(
                child_results
            )

            # Return only the abstracted information
            return {
                **state,
                "sub_workflow_result": {
                    "summary": abstracted_summary.executive_summary,
                    "key_outcomes": abstracted_summary.key_outcomes,
                    "critical_dependencies": abstracted_summary.critical_dependencies,
                    "escalated_risks": abstracted_summary.escalated_risks,
                },
            }

        return RunnableLambda(wrapped_execution)

    def _determine_next_action(
        self, state: OAMATState, abstraction_level: AbstractionLevel
    ) -> str:
        """
        Determine next action based on state and abstraction level
        """

        # Check for escalation needs
        if state.get("escalate_to_parent", False):
            return "escalate"

        # Check completion status
        if state.get("completion_status") == "completed":
            return "finalize"

        # Continue processing
        return "continue"

    async def _execute_agent_work(self, state: OAMATState) -> Dict[str, Any]:
        """
        Execute actual agent work (placeholder for real agent execution)
        """

        # This would be replaced with actual agent execution logic
        # For now, return mock results
        return {
            "high_level_outcome": "Task completed successfully",
            "business_impact": "Positive impact on user experience",
            "key_decisions": [
                "Used React for frontend",
                "Implemented JWT auth",
                "Chose PostgreSQL",
            ],
            "critical_risks": ["Performance bottleneck in data processing"],
            "outcome": "Web application development completed",
            "architecture": {
                "frontend": "React",
                "backend": "FastAPI",
                "database": "PostgreSQL",
            },
            "resources": {"cpu_time": 150, "memory_mb": 512},
            "risks": ["Performance bottleneck", "Scalability concerns"],
            "dependencies": ["Authentication service", "User database"],
            "implementation": {"code_files": 15, "test_coverage": "85%"},
            "tech_specs": {"api_endpoints": 12, "database_tables": 5},
            "testing": ["Unit tests", "Integration tests", "E2E tests"],
        }

    def _create_start_node(self) -> RunnableLambda:
        """Create workflow start node"""

        def start_logic(state: OAMATState) -> Dict[str, Any]:
            return {**state, "status": "started"}

        return RunnableLambda(start_logic)

    def _create_end_node(self) -> RunnableLambda:
        """Create workflow end node"""

        def end_logic(state: OAMATState) -> Dict[str, Any]:
            return {**state, "status": "completed"}

        return RunnableLambda(end_logic)


# Usage example
async def example_context_aware_workflow():
    """Example of creating and running a context-aware workflow"""

    workflow_manager = ContextAwareWorkflowManager()

    # Complex request that will trigger subdivision
    user_request = "Build a complete e-commerce platform with user management, product catalog, shopping cart, and payment processing"

    complexity_assessment = {
        "complexity_score": 9,
        "requires_subdivision": True,
        "estimated_sub_nodes": 4,
        "sub_workflows": [
            {
                "id": "user_management",
                "description": "User registration, authentication, and profile management",
                "agent_role": "backend_developer",
                "complexity_score": 6,
                "requires_subdivision": True,
                "estimated_sub_nodes": 2,
            },
            {
                "id": "product_catalog",
                "description": "Product management, search, and categorization",
                "agent_role": "full_stack_developer",
                "complexity_score": 5,
                "requires_subdivision": False,
            },
            {
                "id": "shopping_cart",
                "description": "Cart management and checkout process",
                "agent_role": "frontend_developer",
                "complexity_score": 4,
                "requires_subdivision": False,
            },
            {
                "id": "payment_processing",
                "description": "Payment gateway integration and transaction handling",
                "agent_role": "backend_developer",
                "complexity_score": 7,
                "requires_subdivision": True,
                "estimated_sub_nodes": 2,
            },
        ],
    }

    # Create workflow with context abstraction
    workflow = await workflow_manager.create_enhanced_workflow_plan(
        user_request=user_request, complexity_assessment=complexity_assessment
    )

    # Initial state
    initial_state = OAMATState(
        request=user_request,
        complexity_assessment=complexity_assessment,
        child_results=[],
        abstraction_level="EXECUTIVE",
    )

    # Execute workflow
    result = await workflow.ainvoke(initial_state)

    return result
