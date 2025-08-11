#!/usr/bin/env python3
"""
Smart Decomposition Agent - Modular Implementation

A modular, O3-powered agent system for complex project decomposition and execution.
This is the main orchestrator that coordinates all specialized modules.
"""

from datetime import datetime
from typing import Any

from src.applications.oamat_sd.src.agents.agent_creation import AgentCreationEngine
from src.applications.oamat_sd.src.execution.execution_engine import ExecutionEngine
from src.applications.oamat_sd.src.models.workflow_models import SmartDecompositionState
from src.applications.oamat_sd.src.operations.file_manager import FileOperationsManager

# Module imports
from src.applications.oamat_sd.src.reasoning.o3_pipeline import O3PipelineEngine
from src.applications.oamat_sd.src.reasoning.structured_output_enforcer import (
    StructuredOutputError,
)

# Core imports
from src.applications.oamat_sd.src.sd_logging import LoggerFactory
from src.applications.oamat_sd.src.synthesis.solution_synthesis import (
    SolutionSynthesisEngine,
)


class SmartDecompositionAgent:
    """
    Modular Smart Decomposition Agent with O3 Intelligence

    This agent orchestrates the complete workflow:
    1. O3 Reasoning -> Generate WorkflowSpecification
    2. Agent Creation -> Build specialized agents
    3. Parallel Execution -> Run agents concurrently
    4. Solution Synthesis -> Combine outputs with O3
    5. File Operations -> Extract and create deliverables
    """

    def __init__(
        self,
        logger_factory: LoggerFactory,
        mcp_tools_registry,
        openai_client,
        console_interface=None,
    ):
        """Initialize the Smart Decomposition Agent with all modules"""
        self.logger_factory = logger_factory
        self.logger = logger_factory.get_debug_logger()
        self.mcp_tools_registry = mcp_tools_registry
        self.openai_client = openai_client
        self.console = console_interface  # Beautiful console interface

        # Initialize all modular components
        self.o3_pipeline = O3PipelineEngine(logger_factory, openai_client)
        self.agent_creator = AgentCreationEngine(
            logger_factory, mcp_tools_registry, openai_client
        )
        self.execution_engine = ExecutionEngine(logger_factory)
        self.synthesis_engine = SolutionSynthesisEngine(logger_factory, openai_client)
        self.file_manager = FileOperationsManager(logger_factory)

        self.logger.info(
            "✅ Smart Decomposition Agent initialized with modular architecture"
        )

    async def process_request(
        self,
        user_request: str,
        project_name: str = None,
        project_path=None,
        standardized_request=None,
    ) -> dict[str, Any]:
        """
        Main entry point for processing user requests

        Args:
            user_request: The user's request to process
            project_name: Pre-created project name (optional)
            project_path: Pre-created project path (optional)
            standardized_request: Preprocessed standardized request (optional)

        Returns:
            Complete results including solution, files, and metadata
        """
        self.logger.info(f"🚀 Processing request: {user_request[:100]}...")

        start_time = datetime.now()

        try:
            # Use pre-created project context or create new one
            if project_name is None or project_path is None:
                project_name, project_path = self.file_manager.create_project_context(
                    user_request
                )
                # Reconfigure logging to use project-specific directory
                self.logger_factory.reconfigure_for_project(str(project_path))
            else:
                self.logger.info(
                    f"📁 Using pre-created project: {project_name} at {project_path}"
                )
                # Logging should already be configured for this project

            # 🔧 CRITICAL FIX: Set global project context for file system tools
            from src.applications.oamat_sd.src.utils.project_context import (
                ProjectContextManager,
            )

            ProjectContextManager.set_context(project_name, str(project_path))
            self.logger.info(
                f"✅ Global project context set: {project_name} at {project_path}"
            )

            # Initialize state
            state = SmartDecompositionState(
                user_request=user_request,
                project_name=project_name,
                project_path=project_path,
                context={
                    "standardized_request": (
                        standardized_request.model_dump()
                        if standardized_request
                        else None
                    )
                },
            )

            # Enhanced logging: Log workflow start
            self.logger_factory.log_component_operation(
                component="smart_decomposition_workflow",
                operation="workflow_start",
                data={
                    "request_length": len(user_request),
                    "project_name": project_name,
                    "project_path": str(project_path),
                    "modular_architecture": True,
                },
            )

            # Step 1: O3 Pipeline - Generate WorkflowSpecification
            state = await self.o3_pipeline.generate_workflow_specification(state)

            # Show beautiful workflow specification
            if self.console and state.get("workflow_specification"):
                self.console.show_workflow_specification(
                    state["workflow_specification"]
                )

            # Step 1.5: Subdivision Analysis - Check if subdivision workflow is needed
            subdivision_required = False
            if standardized_request and hasattr(
                standardized_request, "subdivision_metadata"
            ):
                subdivision_metadata = standardized_request.subdivision_metadata
                if subdivision_metadata and subdivision_metadata.requires_subdivision:
                    subdivision_required = True
                    # Show beautiful subdivision detection
                    if self.console:
                        self.console.show_subdivision_detection(subdivision_metadata)

            if subdivision_required:
                # Step 2A: Subdivision Agent Creation - Build specialized subdivision agents
                state = await self._create_subdivision_agents(
                    state, standardized_request
                )
                # Show beautiful subdivision agent creation results
                if self.console and state.get("subdivision_agents"):
                    self.console.show_agent_creation(
                        state["subdivision_agents"], subdivision=True
                    )

                # Step 3A: Parallel Execution - Run subdivision agents
                # CONTRACT ENFORCEMENT: Only subdivision agents are permitted
                if not state.get("specialized_agents"):
                    raise RuntimeError(
                        "No subdivision agents created - system must fail completely per NO FALLBACKS RULE"
                    )

                # Use subdivision executor for subdivision agents
                from src.applications.oamat_sd.src.execution.subdivision_executor import (
                    SubdivisionExecutor,
                )

                subdivision_executor = SubdivisionExecutor(self.logger_factory)

                agent_count = len(state.get("specialized_agents", {}))
                if self.console:
                    self.console.show_execution_start(agent_count)

                state = await subdivision_executor.execute_subdivision_workflow(
                    state=state,
                    subdivision_agents=state.get("specialized_agents", {}),
                    debug=True,
                )
            else:
                # Step 2B: Linear Workflow - Use O3-generated workflow specification
                self.logger.info("📋 Using O3-generated linear workflow specification")

                # Create agents from workflow specification
                state = await self._create_workflow_agents(state, standardized_request)

                # Show beautiful agent creation results
                if self.console and state.get("workflow_agents"):
                    self.console.show_agent_creation(
                        state["workflow_agents"], subdivision=False
                    )

                # Step 3B: Linear Execution - Run workflow agents
                agent_count = len(state.get("workflow_agents", {}))
                if self.console:
                    self.console.show_execution_start(agent_count)

                state = await self._execute_workflow_agents(state)

            # Step 4: Solution Synthesis - Combine outputs with O3
            if self.console:
                self.console.show_synthesis_start()
            state = await self.synthesis_engine.synthesize_final_solution(state)

            # Step 5: File Operations - Extract and create deliverables
            self.logger.info(
                "📁 Step 5: File Operations - Creating deliverable files..."
            )
            await self.file_manager.extract_and_create_files(state)

            # Calculate total execution time
            total_time = (datetime.now() - start_time).total_seconds() * 1000

            # Enhanced logging: Log workflow completion
            self.logger_factory.log_component_operation(
                component="smart_decomposition_workflow",
                operation="workflow_complete",
                data={
                    "total_execution_time_ms": total_time,
                    "agents_created": len(state.get("specialized_agents", {})),
                    "successful_agents": (
                        sum(
                            1
                            for output in state.get("agent_outputs", {}).values()
                            if isinstance(output, str)
                            and len(output.strip()) > 0  # Agent outputs are strings
                        )
                    ),
                    "final_solution_created": bool(state.get("final_solution")),
                    "files_extracted": True,
                    "project_path": str(project_path),
                    "workflow_success": True,
                    "success": True,
                },
                execution_time_ms=total_time,
            )

            # Prepare final results
            results = {
                "success": True,
                "project_name": project_name,
                "project_path": str(project_path.absolute()),
                "workflow_specification": state.get("workflow_specification"),
                "agents_created": len(state.get("specialized_agents", {})),
                "agent_outputs": state.get("agent_outputs", {}),
                "final_solution": state.get("final_solution"),
                "execution_time_ms": total_time,
                "timestamp": datetime.now().isoformat(),
            }

            # Show beautiful final results
            if self.console:
                files_created = []  # TODO: Get actual created files from file_manager
                self.console.show_final_results(
                    str(project_path.absolute()), total_time / 1000.0, success=True
                )

            return results

        except (StructuredOutputError, RuntimeError) as e:
            # CRITICAL: O3 generation failures must cause complete system failure
            # NO FALLBACKS RULE: System must fail completely if O3 generation fails
            total_time = (datetime.now() - start_time).total_seconds() * 1000

            self.logger_factory.log_component_operation(
                component="smart_decomposition_workflow",
                operation="o3_generation_failed",
                data={
                    "failure_reason": "o3_generation_failure",
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "total_execution_time_ms": total_time,
                    "request_length": len(user_request),
                    "success": False,
                    "no_fallbacks_rule_violation": False,  # This is correct behavior
                },
                execution_time_ms=total_time,
            )

            # Show failure message
            if self.console:
                self.console.show_error(
                    f"O3 Generation Failed - System Must Fail Completely: {str(e)}",
                    "NO FALLBACKS RULE ENFORCED",
                )

            # CRITICAL: Re-raise the exception to cause complete system failure
            # NO FALLBACKS RULE: Do not return error results, fail completely
            raise e

        except Exception as e:
            # Only catch truly unexpected exceptions (not O3-related)
            total_time = (datetime.now() - start_time).total_seconds() * 1000

            self.logger_factory.log_component_operation(
                component="smart_decomposition_workflow",
                operation="unexpected_error",
                data={
                    "failure_reason": "unexpected_error",
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "total_execution_time_ms": total_time,
                    "request_length": len(user_request),
                    "success": False,
                },
                execution_time_ms=total_time,
            )

            # Show error display for unexpected errors
            if self.console:
                self.console.show_error(str(e), "Unexpected Error")
                self.console.show_final_results(
                    (
                        str(project_path.absolute())
                        if "project_path" in locals()
                        else "Unknown"
                    ),
                    total_time / 1000.0,
                    success=False,
                )

            # Return error results for unexpected errors only
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "execution_time_ms": total_time,
                "timestamp": datetime.now().isoformat(),
            }

    async def health_check(self) -> dict[str, Any]:
        """Perform a health check on all modules"""
        health_status = {
            "overall_status": "healthy",
            "components": {},
            "timestamp": datetime.now().isoformat(),
        }

        try:
            # Check O3 Pipeline
            health_status["components"]["o3_pipeline"] = {
                "status": "healthy",
                "model": "o3-mini",
                "ready": bool(self.o3_pipeline.reasoning_model),
            }

            # Check Agent Creator
            health_status["components"]["agent_creator"] = {
                "status": "healthy",
                "mcp_registry": bool(self.mcp_tools_registry),
                "openai_client": bool(self.openai_client),
            }

            # Check Execution Engine
            health_status["components"]["execution_engine"] = {
                "status": "healthy",
                "logger": bool(self.execution_engine.logger),
            }

            # Check Synthesis Engine
            health_status["components"]["synthesis_engine"] = {
                "status": "healthy",
                "model": "o3-mini",
                "ready": bool(self.synthesis_engine.reasoning_model),
            }

            # Check File Manager
            health_status["components"]["file_manager"] = {
                "status": "healthy",
                "logger": bool(self.file_manager.logger),
            }

            self.logger.info("✅ Health check completed - all systems operational")

        except Exception as e:
            health_status["overall_status"] = "degraded"
            health_status["error"] = str(e)
            self.logger.error(f"❌ Health check failed: {e}")

        return health_status

    def get_capabilities(self) -> dict[str, Any]:
        """Return the capabilities of this agent system"""
        return {
            "system_name": "Smart Decomposition Agent",
            "version": "2.0.0-modular",
            "architecture": "modular",
            "capabilities": [
                "O3 meta-intelligence reasoning",
                "Dynamic workflow specification generation",
                "Specialized agent creation",
                "Parallel agent execution",
                "Intelligent solution synthesis",
                "Automated file extraction and creation",
                "Comprehensive logging and monitoring",
            ],
            "supported_request_types": [
                "Application development",
                "API service creation",
                "Script and tool development",
                "System architecture design",
                "Analysis and reporting",
                "Documentation generation",
            ],
            "components": {
                "o3_pipeline": "O3 reasoning and workflow generation",
                "agent_creator": "Specialized agent creation",
                "execution_engine": "Parallel agent execution",
                "synthesis_engine": "Solution synthesis with O3",
                "file_manager": "File operations and project management",
            },
            "models_used": ["o3-mini", "gpt-4.1-mini"],
            "tools_available": (
                len(getattr(self.mcp_tools_registry, "tools", {}))
                if hasattr(self.mcp_tools_registry, "tools")
                else "unknown"
            ),
        }

    async def _create_subdivision_agents(
        self, state: SmartDecompositionState, standardized_request: Any
    ) -> SmartDecompositionState:
        """
        Create specialized agents for subdivided workflow

        Args:
            state: Current execution state
            standardized_request: Preprocessed request with subdivision metadata

        Returns:
            Updated state with subdivision agents
        """
        try:
            # Import subdivision agent factory
            from src.applications.oamat_sd.src.agents.subdivision_agent_factory import (
                SubdivisionAgentFactory,
            )

            # Create subdivision agent factory
            subdivision_factory = SubdivisionAgentFactory(
                logger_factory=self.logger_factory,
                tool_registry=getattr(self, "tool_registry", None),
            )

            # Create subdivision agents using O3 specifications
            subdivision_agents = await subdivision_factory.create_subdivision_agents(
                standardized_request=standardized_request,
                subdivision_metadata=standardized_request.subdivision_metadata,
                debug=True,
            )

            # Convert subdivision agents to the expected format for execution engine
            specialized_agents = {}
            for agent_id, agent_data in subdivision_agents.items():
                specialized_agents[agent_id] = {
                    "agent": agent_data["agent"],
                    "role": agent_data["specification"].role_name,
                    "specialization": agent_data["specification"].domain_specialization,
                    "prompt": agent_data["specification"].system_prompt,
                    "created_timestamp": agent_data["created_at"],
                    "subdivision_agent": True,  # Mark as subdivision agent
                }

            # Update state with subdivision agents
            state["specialized_agents"] = specialized_agents

            # Add subdivision metadata to context
            state["context"]["subdivision_mode"] = True
            state["context"][
                "subdivision_metadata"
            ] = standardized_request.subdivision_metadata.model_dump()

            # Get subdivision metrics for logging
            metrics = subdivision_factory.get_subdivision_metrics(subdivision_agents)

            self.logger.info(f"✅ Created {metrics['total_agents']} subdivision agents")
            self.logger.info(
                f"🎯 Specializations: {', '.join(metrics['specializations'])}"
            )
            self.logger.info(f"🔗 Handoff connections: {metrics['handoff_connections']}")

            return state

        except Exception as e:
            self.logger.error(f"❌ Subdivision agent creation failed: {e}")
            # CONTRACT ENFORCEMENT: System must fail completely if O3 generation fails
            raise RuntimeError(
                f"Subdivision agent creation failed - system must fail completely per NO FALLBACKS RULE: {e}"
            ) from e

    async def _create_workflow_agents(
        self, state: SmartDecompositionState, standardized_request: Any
    ) -> SmartDecompositionState:
        """
        Create agents from O3-generated workflow specification

        Args:
            state: Current execution state
            standardized_request: Preprocessed request

        Returns:
            Updated state with workflow agents
        """
        try:
            # Get workflow specification from state
            workflow_spec = state.get("workflow_specification")
            if not workflow_spec:
                raise RuntimeError("No workflow specification found in state")

            # Create agents from workflow specification
            workflow_agents = {}

            for agent_spec in workflow_spec["agent_specifications"]:
                # Create agent using agent creator
                # Create agent using agent creation engine
                from src.applications.oamat_sd.src.agents.agent_creation import (
                    AgentCreationEngine,
                )

                agent_creator = AgentCreationEngine(
                    logger_factory=self.logger_factory,
                    mcp_tools_registry=self.mcp_tools_registry,
                    openai_client=self.openai_client,
                )

                # Convert tool specs to functions
                tools = agent_creator._convert_tool_specs_to_functions(
                    agent_spec["required_tools"]
                )

                # Create agent from specification
                agent_data = await agent_creator._create_react_agent_from_spec(
                    agent_spec=agent_spec,
                    tools=tools,
                    state=state,
                    structured_output_schema=None,
                )

                workflow_agents[agent_spec["agent_id"]] = {
                    "agent": agent_data,
                    "role": agent_spec["role"],
                    "specialized_capabilities": agent_spec["specialized_capabilities"],
                    "required_deliverables": agent_spec["required_deliverables"],
                    "prompt": agent_spec["complete_prompt"],
                    "timeout_minutes": agent_spec["timeout_minutes"],
                    "quality_criteria": agent_spec["quality_criteria"],
                    "workflow_agent": True,  # Mark as workflow agent
                }

            # Update state with workflow agents
            state["workflow_agents"] = workflow_agents

            # Add workflow metadata to context
            state["context"]["workflow_mode"] = True
            state["context"]["execution_strategy"] = workflow_spec["execution_strategy"]

            self.logger.info(f"✅ Created {len(workflow_agents)} workflow agents")
            self.logger.info(
                f"🎯 Execution strategy: {workflow_spec['execution_strategy']}"
            )

            return state

        except Exception as e:
            self.logger.error(f"❌ Workflow agent creation failed: {e}")
            # CONTRACT ENFORCEMENT: System must fail completely if O3 generation fails
            raise RuntimeError(
                f"Workflow agent creation failed - system must fail completely per NO FALLBACKS RULE: {e}"
            ) from e

    async def _execute_workflow_agents(
        self, state: SmartDecompositionState
    ) -> SmartDecompositionState:
        """
        Execute workflow agents using execution engine

        Args:
            state: Current execution state

        Returns:
            Updated state with agent outputs
        """
        try:
            # Get workflow agents from state
            workflow_agents = state.get("workflow_agents", {})
            if not workflow_agents:
                raise RuntimeError("No workflow agents found in state")

            # Get workflow specification for execution strategy
            workflow_spec = state.get("workflow_specification")
            execution_strategy = (
                workflow_spec["execution_strategy"] if workflow_spec else "sequential"
            )

            # Execute agents using execution engine
            agent_outputs = {}

            # Execute agents using execution engine
            from src.applications.oamat_sd.src.execution.execution_engine import (
                ExecutionEngine,
            )

            execution_engine = ExecutionEngine(logger_factory=self.logger_factory)

            # Execute agents using the available method
            self.logger.info("🚀 Executing workflow agents")
            agent_outputs = await execution_engine.execute_agents_parallel(state=state)

            # Update state with agent outputs
            state["agent_outputs"] = agent_outputs

            # Log execution results
            successful_agents = sum(
                1
                for output in agent_outputs.values()
                if output and len(str(output).strip()) > 0
            )
            self.logger.info(
                f"✅ Workflow execution complete: {successful_agents}/{len(workflow_agents)} agents successful"
            )

            return state

        except Exception as e:
            self.logger.error(f"❌ Workflow agent execution failed: {e}")
            # CONTRACT ENFORCEMENT: System must fail completely if O3 generation fails
            raise RuntimeError(
                f"Workflow agent execution failed - system must fail completely per NO FALLBACKS RULE: {e}"
            ) from e
