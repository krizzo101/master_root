#!/usr/bin/env python3
"""
OAMAT Main Entry Point

Orchestration and Automation Management Application and Tools (OAMAT)
Intelligent workflow orchestration using LangGraph-based agentic planning.
"""

import argparse
import asyncio
from datetime import datetime
import json
import logging
import os
from pathlib import Path
import re
import sys
import time
import traceback
from typing import Any, Callable, Dict, List, Tuple

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langgraph.constants import Send
from langgraph.graph import END, START, StateGraph

# Send API now available with LangGraph >= 0.5.0


# Debug logging for import tracking
def debug_import(module_name, description=""):
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] 🔍 DEBUG: Importing {module_name} {description}")
    sys.stdout.flush()


print(
    f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] 🚀 DEBUG: Starting OAMAT main.py imports"
)
sys.stdout.flush()

# Explicitly load the .env file at the module level to ensure it's loaded before anything else
debug_import("dotenv", "for environment variables")
dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=dotenv_path, override=True)

# Prevent Python bytecode (pyc) file generation
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.dont_write_bytecode = True

# Add src to path for imports
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent.parent
sys.path.insert(0, str(project_root))

print(
    f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] 🔍 DEBUG: About to import OAMAT core modules..."
)
sys.stdout.flush()

# OAMAT Core Imports with debug tracking
debug_import("LLMBaseAgent")

debug_import("sophisticated orchestration components")
from src.applications.oamat.agents.manager.workflow_manager import WorkflowManager
from src.applications.oamat.utils.mcp_tool_registry import (
    create_mcp_tool_registry,
)
from src.applications.oamat.utils.project_context import ProjectContextManager
from src.applications.oamat.workflows.orchestrator.execution import WorkflowExecutor
from src.applications.oamat.workflows.orchestrator.graph_builder import (
    WorkflowGraphBuilder,
)

debug_import("AgenticWorkflowState and create_initial_state")
from src.applications.oamat.workflows.orchestrator.state import (
    AgenticWorkflowState,
    create_initial_state,
)

debug_import("logging utilities")
from src.applications.oamat.oamat_logging import (
    UserLogger,
    analyze_api_errors,
    log_prompt_response,
    setup_logging,
)

debug_import("AgentFactory")
from src.applications.oamat.agents.agent_factory.factory import AgentFactory

debug_import("Config classes")

debug_import("pydantic ValidationError")

debug_import("Parallel execution and task decomposition")

# RULE 955: Command-based routing imports
debug_import("Command-based routing")
from dataclasses import dataclass
from typing import Union


# RULE 955: Command objects for modern routing
@dataclass
class HandoffCommand:
    target_agent: str
    task_description: str
    context: Dict[str, Any]


@dataclass
class CompletionCommand:
    reason: str = "workflow_completed"


# Type alias for routing commands
RoutingCommand = Union[HandoffCommand, CompletionCommand]

print(
    f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] ✅ DEBUG: All imports completed successfully"
)
sys.stdout.flush()


# TODO: These are placeholder functions and need to be implemented correctly.
# This function will now be a method of OAMATMain
# def create_agent_creator(role: str, node_id: str): ...


class OAMATMain:
    """Main OAMAT application - LangGraph Supervisor-Based Multi-Agent System"""

    def __init__(
        self,
        debug_mode: bool = False,
        agent_details: bool = False,
        no_review: bool = False,
    ):
        """Initialize OAMAT system with sophisticated orchestration capabilities"""
        debug_timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{debug_timestamp}] 🔧 DEBUG: Initializing OAMATMain...")
        sys.stdout.flush()

        self.debug_mode = debug_mode
        self.agent_details = agent_details
        self.no_review = no_review
        self.logger = self._setup_logging()
        self.manager_logger = logging.getLogger("oamat.manager")

        # Initialize user-friendly logging interface
        self.user_logger = UserLogger(debug_mode=debug_mode)

        # Make UserLogger available globally for LLMBaseAgent access
        OAMATMain._current_user_logger = self.user_logger

        # Initialize sophisticated orchestration components
        print(
            f"[{debug_timestamp}] 🔧 DEBUG: Initializing sophisticated orchestration..."
        )

        # Initialize NEO4j client first
        self.neo4j_client = self._create_neo4j_client()

        # Initialize MCP Tool Registry for research capabilities
        try:
            self.mcp_registry = create_mcp_tool_registry()
            print(
                f"[{debug_timestamp}] ✅ DEBUG: MCP Tool Registry initialized successfully"
            )
        except Exception as e:
            print(
                f"[{debug_timestamp}] ⚠️ DEBUG: MCP Tool Registry initialization failed: {e}"
            )
            self.mcp_registry = None

        # Initialize WorkflowManager for AI-driven dynamic planning
        try:
            self.workflow_manager = WorkflowManager(
                neo4j_client=self.neo4j_client, model="o3-mini"
            )
            print(
                f"[{debug_timestamp}] ✅ DEBUG: WorkflowManager initialized successfully"
            )
        except Exception as e:
            print(
                f"[{debug_timestamp}] ❌ CRITICAL: WorkflowManager initialization failed: {e}"
            )
            print(
                f"[{debug_timestamp}] 💡 HINT: Check Neo4j connection and o3-mini model availability"
            )
            # SOPHISTICATED MODE REQUIRED: No longer setting to None, let it fail explicitly
            raise RuntimeError(
                f"Cannot initialize WorkflowManager - sophisticated mode requires this component: {e}"
            ) from e
            # COMMENTED OUT: Silent failure that enabled legacy fallback
            # self.workflow_manager = None

        # Initialize WorkflowExecutor for sophisticated execution (without SDLC manager)
        try:
            self.workflow_executor = (
                WorkflowExecutor()
            )  # Pure intelligence, no rigid frameworks
            print(
                f"[{debug_timestamp}] ✅ DEBUG: WorkflowExecutor initialized successfully"
            )
        except Exception as e:
            print(
                f"[{debug_timestamp}] ❌ CRITICAL: WorkflowExecutor initialization failed: {e}"
            )
            # SOPHISTICATED MODE REQUIRED: No longer setting to None, let it fail explicitly
            raise RuntimeError(
                f"Cannot initialize WorkflowExecutor - sophisticated mode requires this component: {e}"
            ) from e
            # COMMENTED OUT: Silent failure that enabled legacy fallback
            # self.workflow_executor = None

        # Initialize WorkflowGraphBuilder for dynamic graph construction
        try:
            self.graph_builder = WorkflowGraphBuilder(
                supervisor_node=self._supervisor_node,
                completion_node=self._completion_node,
            )
            print(
                f"[{debug_timestamp}] ✅ DEBUG: WorkflowGraphBuilder initialized successfully"
            )
        except Exception as e:
            print(
                f"[{debug_timestamp}] ❌ CRITICAL: WorkflowGraphBuilder initialization failed: {e}"
            )
            # SOPHISTICATED MODE REQUIRED: No longer setting to None, let it fail explicitly
            raise RuntimeError(
                f"Cannot initialize WorkflowGraphBuilder - sophisticated mode requires this component: {e}"
            ) from e
            # COMMENTED OUT: Silent failure that enabled legacy fallback
            # self.graph_builder = None

        # Initialize recursive workflow orchestration (replaces hardcoded TaskDecomposer)
        try:
            from src.applications.oamat.recursive_workflow_orchestrator import (
                RecursiveWorkflowOrchestrator,
            )

            self.recursive_orchestrator = RecursiveWorkflowOrchestrator(self)
            self.recursive_orchestrator.initialize_components()
            print(
                f"[{debug_timestamp}] ✅ DEBUG: Recursive workflow orchestrator initialized successfully"
            )
        except Exception as e:
            print(
                f"[{debug_timestamp}] ⚠️ WARNING: Recursive orchestration initialization failed: {e}"
            )
            self.recursive_orchestrator = None

        # Legacy components for backward compatibility
        try:
            from src.applications.oamat.task_decomposer import (
                SubWorkflowOrchestrator,
                TaskDecomposer,
            )

            self.task_decomposer = TaskDecomposer()
            self.subworkflow_orchestrator = SubWorkflowOrchestrator(self)
            print(
                f"[{debug_timestamp}] ✅ DEBUG: Legacy task decomposer available as fallback"
            )
        except Exception as e:
            print(
                f"[{debug_timestamp}] ⚠️ WARNING: Legacy task decomposition initialization failed: {e}"
            )
            self.task_decomposer = None
            self.subworkflow_orchestrator = None

        # Legacy components for fallback compatibility
        self.project_context = None
        self.agent_factory = None

        print(f"[{debug_timestamp}] 🎉 DEBUG: OAMATMain initialization complete")
        sys.stdout.flush()

    def _create_neo4j_client(self):
        """Create Neo4j client with proper error handling"""
        try:
            from src.shared.mcp.neo4j_mcp_client import Neo4jMCPClient

            client = Neo4jMCPClient(
                mcp_config_path=".cursor/mcp.json",
                debug=self.debug_mode,
            )

            # Test connection with timeout to prevent hanging
            try:
                import asyncio

                # Add timeout to prevent hanging
                async def test_connection_with_timeout():
                    try:
                        result = await asyncio.wait_for(
                            client.get_schema(), timeout=10.0
                        )
                        return result
                    except asyncio.TimeoutError:
                        self.logger.warning(
                            "⏰ Neo4j schema check timed out after 10 seconds"
                        )
                        return None

                result = asyncio.run(test_connection_with_timeout())
                if result and result.success:
                    self.logger.info("✅ Neo4j client connected successfully")
                elif result:
                    self.logger.warning(
                        f"⚠️ Neo4j client created but schema check failed: {result.error}"
                    )
                else:
                    self.logger.warning(
                        "⚠️ Neo4j client created but schema check timed out"
                    )

            except Exception as e:
                self.logger.warning(
                    f"⚠️ Neo4j client created but connection test failed: {e}"
                )

            return client

        except Exception as e:
            self.logger.warning(f"⚠️ Neo4j client creation failed: {e}")
            self.logger.info("🔄 Continuing without Neo4j client")
            return None

    def get_role_for_node(self, state: AgenticWorkflowState, node_id: str) -> str:
        """Finds the agent role for a given node_id from the workflow plan."""
        self.logger.debug(f"🔍 Looking up role for node_id: {node_id}")

        # For simplified static workflow, node_id IS the role
        static_roles = ["planner", "coder", "reviewer", "completion"]
        if node_id in static_roles:
            self.logger.debug(
                f"✅ Using static role '{node_id}' for simplified workflow"
            )
            return node_id

        # For complex workflows, look up in planned nodes
        planned_nodes = state.get("planned_nodes", [])
        for node in planned_nodes:
            if node.get("id") == node_id:
                role = node.get("agent_role", "unknown")
                self.logger.debug(f"✅ Found role '{role}' for node_id '{node_id}'")
                return role

        self.logger.warning(
            f"⚠️ Could not find role for node_id: {node_id}, returning node_id as role"
        )
        return node_id  # Fallback: use node_id as role

    def _get_agent_context(
        self, state: AgenticWorkflowState, node_id: str, role: str, project_path: Path
    ) -> Dict[str, Any]:
        """Get the context for the agent, including previous outputs."""
        # Ensure context key exists
        if "context" not in state:
            state["context"] = {}

        # CRITICAL FIX: Set project_path in state context for file system tools,
        # but create a clean shared_context for agents that excludes the project_path
        # to prevent agents from using full paths in write_file calls
        state["context"]["project_path"] = str(project_path)

        # Create agent-safe shared context that excludes project_path
        agent_safe_context = {
            k: v for k, v in state.get("context", {}).items() if k != "project_path"
        }

        # NEW: Enhanced context with file-level parallelization results
        enhanced_context = {
            "previous_outputs": state.get("agent_outputs", {}),
            "shared_context": agent_safe_context,
            # File-level parallelization context
            "file_artifacts": state.get("workflow_artifacts", []),
            "subtask_outputs": state.get("subtask_outputs", {}),
            # File generation summaries from previous nodes
            "file_generation_history": self._extract_file_generation_history(state),
            # Dependency file contents for reference
            "dependency_files": self._extract_dependency_file_context(state, role),
        }

        return enhanced_context

    def _extract_file_generation_history(
        self, state: AgenticWorkflowState
    ) -> Dict[str, Any]:
        """Extract file generation history from previous agent outputs"""
        file_history = {
            "total_files_generated": 0,
            "parallel_execution_summary": {},
            "file_types_generated": set(),
            "execution_performance": {},
        }

        agent_outputs = state.get("agent_outputs", {})

        for agent_role, output in agent_outputs.items():
            if isinstance(output, dict):
                # Track files from decomposed execution
                if output.get("decomposed_execution"):
                    files_generated = output.get("total_files_generated", 0)
                    file_history["total_files_generated"] += files_generated

                    # Track parallel execution info
                    if output.get("file_parallel_execution"):
                        file_history["parallel_execution_summary"][agent_role] = output[
                            "file_parallel_execution"
                        ]

                    # Track execution performance
                    if output.get("execution_performance"):
                        file_history["execution_performance"][agent_role] = output[
                            "execution_performance"
                        ]

                # Extract file artifacts
                file_artifacts = output.get("file_artifacts", [])
                for artifact in file_artifacts:
                    if isinstance(artifact, str):
                        # Extract file extension for type tracking
                        if "." in artifact:
                            file_type = artifact.split(".")[-1]
                            file_history["file_types_generated"].add(file_type)

        # Convert set to list for JSON serialization
        file_history["file_types_generated"] = list(
            file_history["file_types_generated"]
        )

        return file_history

    def _extract_dependency_file_context(
        self, state: AgenticWorkflowState, current_role: str
    ) -> Dict[str, Any]:
        """Extract file contents from dependency nodes for current agent to reference"""
        dependency_files = {}

        # Get workflow plan to understand dependencies
        workflow_plan = state.get("workflow_plan")
        if not workflow_plan or not isinstance(workflow_plan, dict):
            return dependency_files

        # Find current node and its dependencies
        current_node_deps = []
        nodes = workflow_plan.get("nodes", [])

        for node in nodes:
            if isinstance(node, dict) and node.get("agent_role") == current_role:
                current_node_deps = node.get("dependencies", [])
                break

        # Extract file artifacts from dependency nodes
        agent_outputs = state.get("agent_outputs", {})

        for dep_role in current_node_deps:
            if dep_role in agent_outputs:
                dep_output = agent_outputs[dep_role]
                if isinstance(dep_output, dict):
                    # Get file artifacts from this dependency
                    dep_artifacts = dep_output.get("file_artifacts", [])

                    if dep_artifacts:
                        dependency_files[dep_role] = {
                            "role": dep_role,
                            "files_created": dep_artifacts,
                            "execution_type": dep_output.get(
                                "execution_performance", {}
                            ).get("file_level_parallelization", False),
                            "files_count": len(dep_artifacts),
                        }

                        # Include file generation summary for context
                        if "file_generation_summary" in dep_output:
                            dependency_files[dep_role][
                                "generation_summary"
                            ] = dep_output["file_generation_summary"]

        return dependency_files

    def _create_project_context(self, state: AgenticWorkflowState) -> Tuple[str, Path]:
        """Generates a unique project name and creates its directory, or reuses existing context if available."""
        self.logger.debug("🔍 _create_project_context() called")
        self.logger.info(
            f"🏗️ Creating project context for request: {state.get('user_request', 'Unknown request')[:100]}..."
        )

        # CRITICAL FIX: Check if project already exists in state to prevent multiple directories
        if state and "project_name" in state and "project_path" in state:
            existing_project_name = state["project_name"]
            existing_project_path = Path(state["project_path"])

            if existing_project_path.exists():
                self.logger.info(
                    f"🔄 Reusing existing project context: {existing_project_name} at {existing_project_path}"
                )
                self.logger.debug(
                    f"🔍 _create_project_context() returning existing: ({existing_project_name}, {existing_project_path})"
                )
                return existing_project_name, existing_project_path
            else:
                self.logger.warning(
                    f"⚠️ Existing project path not found: {existing_project_path}, creating new one"
                )

        # Sanitize the request to create a file-system-friendly slug
        self.logger.debug("🧹 Sanitizing user request for file system...")
        sanitized_request = (
            re.sub(r"[^\w\s-]", "", state.get("user_request", "")).strip().lower()
        )
        self.logger.debug(f"🧹 Sanitized request: '{sanitized_request}'")

        project_slug = re.sub(r"[-\s]+", "-", sanitized_request)
        self.logger.debug(f"🏷️ Initial project slug: '{project_slug}'")

        project_slug = "-".join(project_slug.split("-")[:5])
        self.logger.debug(f"🏷️ Truncated project slug: '{project_slug}'")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.logger.debug(f"🕐 Generated timestamp: {timestamp}")

        project_name = f"{project_slug}-{timestamp}"
        self.logger.debug(f"🏷️ Final project name: '{project_name}'")

        project_path = Path("projects") / project_name
        self.logger.debug(f"📁 Computed project path: {project_path}")

        self.logger.info(f"📁 Creating project directory: {project_path}")

        try:
            self.logger.debug("📁 Calling project_path.mkdir()...")
            project_path.mkdir(parents=True, exist_ok=True)
            self.logger.debug("✅ project_path.mkdir() completed successfully")
        except Exception as e:
            self.logger.error(f"❌ Error creating project directory: {e}")
            raise

        if project_path.exists():
            self.logger.info(
                f"✅ Project directory created successfully: {project_path}"
            )
            self.logger.debug(f"📊 Project directory exists: {project_path.exists()}")
            self.logger.debug(f"📊 Project directory is_dir: {project_path.is_dir()}")
        else:
            self.logger.error(f"❌ Failed to create project directory: {project_path}")

        self.logger.info(
            f"🏷️ Project context created: {project_name} at {project_path}"
        )
        self.logger.debug(
            f"🔍 _create_project_context() returning: ({project_name}, {project_path})"
        )
        return project_name, project_path

    def _run_agent_node(
        self, state: AgenticWorkflowState, config: Dict[str, Any], node_id: str
    ):
        """Runs a single agent node in the workflow."""
        try:
            role = self.get_role_for_node(state, node_id)
            project_path = state.get("project_path")

            self.logger.info(f"--- Running Agent: {role} (Node: {node_id}) ---")

            # USER LOGGING: Start node execution
            if hasattr(self, "user_logger") and self.user_logger:
                self.user_logger.start_node_execution(node_id, role, depth=0)

            # Check if task should use recursive AI-driven subdivision
            if not state.get(
                "parallel_execution", False
            ):  # Skip subdivision for already subdivided tasks
                if self.recursive_orchestrator:
                    # Use new recursive AI-driven approach
                    user_request = state.get("user_request", "No request found")
                    task_description = self._get_task_for_role(role, user_request)

                    # Create recursive execution context
                    from src.applications.oamat.recursive_workflow_orchestrator import (
                        RecursionDepth,
                        RecursiveExecutionContext,
                    )

                    recursion_context = RecursiveExecutionContext(
                        user_request=user_request,
                        parent_node_id=node_id,
                        parent_agent_role=role,
                        recursion_depth=RecursionDepth.LEVEL_1,  # Main workflow level
                        parent_context={
                            "task_description": task_description,
                            "project_path": state.get("project_path"),
                            "workflow_state": state,
                        },
                    )

                    # Use asyncio to run the recursive analysis
                    import asyncio

                    try:
                        loop = asyncio.get_event_loop()
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)

                    self.logger.info(
                        f"🧠 RECURSIVE: Analyzing {role} for AI-driven subdivision..."
                    )

                    recursive_result = loop.run_until_complete(
                        self.recursive_orchestrator.execute_node_with_subdivision(
                            recursion_context
                        )
                    )

                    if (
                        recursive_result.get("success")
                        and recursive_result.get("execution_type") != "atomic"
                    ):
                        self.logger.info(
                            f"✅ RECURSIVE: {role} executed with recursive subdivision"
                        )
                        # Update state with recursive results and return
                        state["agent_outputs"][node_id] = recursive_result
                        state["completed_nodes"] = list(
                            set(state.get("completed_nodes", [])) | {node_id}
                        )
                        return state
                    else:
                        self.logger.info(f"⚡ RECURSIVE: {role} executed as atomic task")
                        # Continue with normal execution below

                elif self.task_decomposer:
                    # Fallback to legacy hardcoded approach
                    self.logger.warning(
                        f"⚠️ FALLBACK: Using legacy TaskDecomposer for {role}"
                    )
                    decomposer = self.task_decomposer
                    user_request = state.get("user_request", "No request found")
                    task_description = self._get_task_for_role(role, user_request)

                    subtasks = decomposer.decompose_task(
                        task_description, role, user_request
                    )

                    if subtasks:
                        self.logger.info(
                            f"🔧 LEGACY: Breaking {role} into {len(subtasks)} subtasks"
                        )

                        # Execute subtasks in parallel
                        orchestrator = self.subworkflow_orchestrator

                        # Use asyncio to run the async method
                        import asyncio

                        try:
                            loop = asyncio.get_event_loop()
                        except RuntimeError:
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)

                        subtask_results = loop.run_until_complete(
                            orchestrator.execute_subtasks(subtasks, state)
                        )

                    if subtask_results.get("success"):
                        self.logger.info(
                            f"✅ DECOMPOSE: Completed all {len(subtasks)} subtasks for {role}"
                        )

                        # Enhanced context consolidation from file-level parallelization
                        consolidated_context = subtask_results.get(
                            "consolidated_context", {}
                        )

                        # Combine subtask results into main agent output with enhanced context
                        combined_output = {
                            "agent_role": role,
                            "decomposed_execution": True,
                            "subtasks_completed": subtask_results.get(
                                "completed_subtasks", []
                            ),
                            "subtask_results": subtask_results.get(
                                "subtask_results", {}
                            ),
                            "summary": f"Successfully completed {len(subtasks)} parallel subtasks for {role}",
                            # NEW: Enhanced context consolidation
                            "file_parallel_execution": consolidated_context.get(
                                "file_parallel_execution", {}
                            ),
                            "total_files_generated": consolidated_context.get(
                                "file_generation_summary", {}
                            ).get("total_files", 0),
                            "file_artifacts": consolidated_context.get(
                                "file_artifacts", []
                            ),
                            "execution_performance": {
                                "parallel_subtasks": len(subtasks),
                                "file_level_parallelization": any(
                                    result.get("execution_type") == "file_parallel"
                                    for result in subtask_results.get(
                                        "subtask_results", {}
                                    ).values()
                                ),
                                "total_execution_levels": len(
                                    set(
                                        result.get("level", 0)
                                        for result in subtask_results.get(
                                            "subtask_results", {}
                                        ).values()
                                    )
                                ),
                            },
                        }

                        # CRITICAL: Update state with consolidated context from all levels
                        # This ensures dependent nodes receive complete context
                        state.update(consolidated_context)

                        # Update state with combined results
                        if "agent_outputs" not in state:
                            state["agent_outputs"] = {}
                        state["agent_outputs"][role] = combined_output

                        # IMPORTANT: Track file artifacts for dependent nodes
                        if "workflow_artifacts" not in state:
                            state["workflow_artifacts"] = []
                        state["workflow_artifacts"].extend(
                            consolidated_context.get("file_artifacts", [])
                        )

                        return state
                    else:
                        self.logger.warning(
                            f"⚠️ DECOMPOSE: Subtasks failed for {role}, falling back to single agent"
                        )
                        # Fall through to normal execution

            # Ensure state has required fields initialized
            if "agent_outputs" not in state:
                state["agent_outputs"] = {}
            if "completed_nodes" not in state:
                state["completed_nodes"] = []
            if "failed_nodes" not in state:
                state["failed_nodes"] = []
            if "errors" not in state:
                state["errors"] = []

            # Simplified task description for role-based workflow
            # CRITICAL FIX: Include the actual user request in each role's task description
            user_request = state.get("user_request", "No request found")

            role_tasks = {
                "planner": f"Create a comprehensive project plan for this specific request: '{user_request}'. Break down the work into clear, actionable steps that will accomplish this exact goal.",
                "coder": f"Implement the solution for this request: '{user_request}'. Write clean, well-documented code that fulfills this specific requirement. Follow best practices and coding standards.",
                "reviewer": f"Review the implemented solution for this request: '{user_request}'. Verify it meets the specific requirements, check for quality, correctness, and adherence to standards.",
            }

            task_description = role_tasks.get(
                role,
                f"Execute the {role} role for: {user_request}",
            )

            self.logger.debug(f"🔍 Task for {role}: {task_description}")

            # Check for existing project context
            project_name = state.get("project_name")
            project_path = state.get("project_path")
            if project_path and isinstance(project_path, str):
                project_path = Path(project_path)

            if not project_path or not project_path.exists():
                project_name, project_path = self._create_project_context(state)
            else:
                self.logger.debug("🔍 Using existing project context")

            # Store project context in state (top level for other parts of the system)
            state["project_name"] = project_name
            state["project_path"] = str(project_path)

            # CRITICAL: Store inside the context dict for the file_system tools
            if "context" not in state:
                state["context"] = {}
            state["context"]["project_name"] = project_name
            state["context"]["project_path"] = str(project_path)

            try:
                agent_executable = self._create_agent_executable(
                    role=role, node_id=node_id
                )
            except Exception as e:
                self.logger.error(f"❌ Primary agent creation failed for {role}: {e}")
                self.logger.info(
                    f"🔄 Falling back to researcher agent for node {node_id}"
                )
                agent_executable = self._create_agent_executable(
                    role="researcher", node_id=node_id
                )

            # Enhance task description to explicitly instruct file saving
            enhanced_task = f"""{task_description}

IMPORTANT: You MUST save all your work to files using the write_file tool. Create appropriate files for your output:
- Save documentation as .md files
- Save code as .py files (or appropriate extension)
- Save plans, requirements, architecture as .md files
- Use descriptive filenames that reflect the content

Example: write_file("project_plan.md", "# Project Plan\\n\\nYour content here...")

Your work is only valuable if it's saved to files. Always use write_file for your deliverables."""

            # Construct the input message for the agent
            agent_input = {"messages": [HumanMessage(content=enhanced_task)]}

            # Add all previous agent outputs to the context for this agent
            context = self._get_agent_context(state, node_id, role, project_path)
            agent_input["context"] = context

            # CRITICAL FIX: Set project context globally for tools to access
            from src.applications.oamat.utils.project_context import project_context

            project_context.set_context(project_name, str(project_path))

            self.logger.debug(
                f"🔍 DEBUG: Set global context: {project_context.get_context()}"
            )

            self.logger.debug(
                f"🔧 Agent {role} executing with project context: {project_path}"
            )
            self.logger.debug(f"💬 Agent {role} input: {agent_input}")

            # Invoke the agent
            self.logger.info(f"⚡ Invoking agent {role}...")
            self.logger.debug(f"🔍 About to call agent_executable.invoke() for {role}")
            output = agent_executable.invoke(agent_input)

            self.logger.debug(
                f"🔍 DEBUG: After agent execution, context: {project_context.get_context()}"
            )

            # NOTE: Don't clear context here - keep it available for subsequent agents
            # Context will be cleared in the completion node
            self.logger.info(f"--- Agent {role} completed ---")

            # Update state
            state["agent_outputs"][node_id] = output
            # Use set to avoid duplicates, which was a previous bug
            state["completed_nodes"] = list(
                set(state.get("completed_nodes", [])) | {node_id}
            )

            # USER LOGGING: Mark node as completed
            if hasattr(self, "user_logger") and self.user_logger:
                self.user_logger.complete_node(
                    node_id, success=True, execution_type="standard"
                )

            self.logger.debug(
                f"🔍 _run_agent_node() returning updated state with keys: {list(state.keys())}"
            )
            return state

        except Exception as e:
            self.logger.error(f"💥 Critical error in agent node {node_id}: {e}")
            # Update state to mark node as failed but continue workflow
            if "failed_nodes" not in state:
                state["failed_nodes"] = []
            state["failed_nodes"].append(node_id)
            state["errors"].append(f"Node {node_id} failed: {str(e)}")

            # USER LOGGING: Mark node as failed
            if hasattr(self, "user_logger") and self.user_logger:
                self.user_logger.complete_node(
                    node_id, success=False, execution_type="standard"
                )

            return state

    def _create_agent_executable(self, role: str, node_id: str):
        """Creates a runnable agent executable from the agent factory."""
        self.logger.debug(
            f"🔍 _create_agent_executable() called with role={role}, node_id={node_id}"
        )
        self.logger.info(f"Creating agent for role: {role} (node: {node_id})")

        # Define a comprehensive spec that includes file system tools for all agents
        agent_spec = {
            "role": role,
            "dependencies": [
                "file_system",
                "web_search",
                "knowledge_search",
                "generate_code",
            ],
        }

        agent = self.agent_factory.create_agent_with_tools(spec=agent_spec)
        self.logger.info(f"✅ Agent '{role}' created successfully with tools.")
        return agent

    def _supervisor_node(self, state):
        """RULE 955: Command-based supervisor for intelligent routing"""
        self.logger.debug("🔍 _supervisor_node() called")
        print(f"🎯 SUPERVISOR: Starting with state keys: {list(state.keys())}")

        # Analyze current workflow state
        command = self._analyze_next_step(state)

        # CRITICAL FIX: Handle parallel execution by setting state markers
        if isinstance(command, list):  # List of Send commands for parallel execution
            self.logger.info(f"🚀 Parallel execution: dispatching {len(command)} agents")
            print(f"🎯 SUPERVISOR: ✅ Parallel dispatch of {len(command)} agents")

            # Store the Send commands in state for the graph to process
            parallel_nodes = []
            for send_cmd in command:
                parallel_nodes.append(
                    {"node_id": send_cmd.node, "agent_state": send_cmd.arg}
                )

            state["parallel_commands"] = parallel_nodes
            state["next_node"] = "parallel_execution"
            return state

        # Store command decision in state for debugging (single agent routing)
        if isinstance(command, HandoffCommand):
            state["next_node"] = command.target_agent
            self.logger.info(f"🎯 Command routing to: {command.target_agent}")
            print(f"🎯 SUPERVISOR: ✅ Handoff to {command.target_agent}")
        elif isinstance(command, CompletionCommand):
            state["next_node"] = "completion"
            self.logger.info(f"🏁 Command completion: {command.reason}")
            print(f"🎯 SUPERVISOR: ✅ Completion - {command.reason}")

        return state

    def _analyze_next_step(self, state) -> RoutingCommand:
        """RULE 955: Intelligent next step analysis using Command objects"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

        # Enhanced logging for routing decision
        routing_log = f"""
========================================
🎯 SUPERVISOR ROUTING ANALYSIS
========================================
TIMESTAMP: {timestamp}
STATE KEYS: {list(state.keys())}
========================================
"""
        print(routing_log)

        # Get workflow execution status
        completed_nodes = state.get("completed_nodes", [])
        failed_nodes = state.get("failed_nodes", [])
        workflow_plan = state.get("workflow_plan")
        user_request = state.get("user_request", "")

        if not workflow_plan:
            self.logger.error("No workflow plan found")
            print("🎯 SUPERVISOR: ❌ No workflow plan found - routing to completion")
            return CompletionCommand("no_workflow_plan")

        print(f"🎯 ANALYZER: Checking {len(workflow_plan['nodes'])} nodes")
        print(f"🎯 ANALYZER: Completed: {completed_nodes}")
        print(f"🎯 ANALYZER: Failed: {failed_nodes}")

        # Build role-to-node-id mapping for dependency resolution
        role_to_node_id = {}
        for node_dict in workflow_plan["nodes"]:
            role_to_node_id[node_dict["agent_role"]] = node_dict["id"]

        # Find next eligible nodes using dependency checking
        eligible_nodes = []
        for node_dict in workflow_plan["nodes"]:
            node_id = node_dict["id"]
            node_role = node_dict["agent_role"]
            node_dependencies = node_dict.get("dependencies", [])

            # Skip if already processed
            if node_id in completed_nodes or node_id in failed_nodes:
                continue

            # Check dependencies - convert role names to node IDs
            dependency_node_ids = [
                role_to_node_id.get(dep, dep) for dep in node_dependencies
            ]
            dependencies_met = all(
                dep_node_id in completed_nodes for dep_node_id in dependency_node_ids
            )

            if dependencies_met:
                eligible_nodes.append(
                    {
                        "node_id": node_id,
                        "agent_role": node_role,
                        "description": node_dict.get("description", ""),
                        "dependencies": node_dependencies,
                    }
                )
            else:
                missing_deps = [
                    dep
                    for dep in node_dependencies
                    if role_to_node_id.get(dep, dep) not in completed_nodes
                ]
                print(f"🎯 ANALYZER: Node {node_id} waiting for: {missing_deps}")

        # If no eligible nodes, workflow is complete
        if not eligible_nodes:
            print("🎯 ANALYZER: ✅ All nodes completed")
            return CompletionCommand("all_nodes_completed")

        # PARALLEL PROCESSING: Check for multiple eligible nodes
        if len(eligible_nodes) > 1:
            print(
                f"🚀 PARALLEL: Found {len(eligible_nodes)} nodes ready for parallel execution"
            )

            # Identify which nodes can run in parallel (no interdependencies)
            parallel_candidates = self._identify_parallel_candidates(
                eligible_nodes, workflow_plan
            )

            if len(parallel_candidates) > 1:
                print(
                    f"🚀 PARALLEL: Dispatching {len(parallel_candidates)} agents simultaneously"
                )
                return self._create_parallel_dispatch(
                    parallel_candidates, user_request, state
                )

        # Enhanced intelligent routing using WorkflowManager (single node)
        if len(eligible_nodes) == 1:
            # Only one option - no need for intelligent decision
            chosen_node = eligible_nodes[0]
            print(
                f"🎯 ANALYZER: ✅ Single option: {chosen_node['node_id']} ({chosen_node['agent_role']})"
            )
        else:
            # Multiple options - use WorkflowManager intelligence for routing decision
            print(
                f"🎯 ANALYZER: 🧠 Multiple options available ({len(eligible_nodes)}), consulting WorkflowManager..."
            )

            if self.workflow_manager:
                try:
                    # Prepare context for intelligent routing decision
                    routing_context = {
                        "eligible_nodes": eligible_nodes,
                        "workflow_progress": len(completed_nodes)
                        / len(workflow_plan["nodes"]),
                        "completed_nodes": completed_nodes,
                        "failed_nodes": failed_nodes,
                        "user_request": user_request,
                    }

                    # Log manager agent routing decision call
                    manager_routing_log = f"""
========================================
🧠 MANAGER AGENT ROUTING DECISION
========================================
TIMESTAMP: {datetime.now().strftime("%H:%M:%S.%f")[:-3]}
ELIGIBLE OPTIONS: {[node['agent_role'] for node in eligible_nodes]}
CONTEXT: {json.dumps(routing_context, indent=2)}
========================================
"""
                    print(manager_routing_log)
                    self.manager_logger.info(manager_routing_log)

                    available_options = [node["node_id"] for node in eligible_nodes]
                    decision = self.workflow_manager.make_intelligent_routing_decision(
                        node_id="supervisor",
                        workflow_state=state,
                        available_options=available_options,
                        context=routing_context,
                    )

                    # Log manager agent decision response
                    decision_log = f"""
========================================
🧠 MANAGER AGENT ROUTING DECISION RESPONSE
========================================
TIMESTAMP: {datetime.now().strftime("%H:%M:%S.%f")[:-3]}
DECISION: {decision.get('decision', 'N/A')}
REASONING: {decision.get('reasoning', 'N/A')[:100]}...
CONFIDENCE: {decision.get('confidence', 'N/A')}
RISK ASSESSMENT: {decision.get('risk_assessment', 'N/A')}
========================================
"""
                    print(decision_log)
                    self.manager_logger.info(decision_log)

                    # Find the chosen node based on decision
                    chosen_node_id = decision.get("decision")
                    chosen_node = next(
                        (
                            node
                            for node in eligible_nodes
                            if node["node_id"] == chosen_node_id
                        ),
                        eligible_nodes[0],
                    )

                    print(
                        f"🎯 ANALYZER: 🧠 WorkflowManager chose: {chosen_node['node_id']} ({chosen_node['agent_role']})"
                    )

                except Exception as e:
                    print(
                        f"🎯 ANALYZER: ⚠️ WorkflowManager routing failed: {e}, using first eligible option"
                    )
                    chosen_node = eligible_nodes[0]
            else:
                print(
                    "🎯 ANALYZER: ⚠️ WorkflowManager not available, using first eligible option"
                )
                chosen_node = eligible_nodes[0]

        # Create task description for the chosen agent
        task_description = self._get_task_for_role(
            chosen_node["agent_role"], user_request
        )

        print(
            f"🎯 ANALYZER: ✅ Final decision: {chosen_node['node_id']} ({chosen_node['agent_role']})"
        )

        return HandoffCommand(
            target_agent=chosen_node["node_id"],
            task_description=task_description,
            context={
                "role": chosen_node["agent_role"],
                "dependencies_completed": [
                    dep for dep in chosen_node["dependencies"] if dep in completed_nodes
                ],
                "workflow_progress": len(completed_nodes) / len(workflow_plan["nodes"]),
            },
        )

    def _identify_parallel_candidates(
        self, eligible_nodes: List[Dict], workflow_plan: Dict
    ) -> List[Dict]:
        """Identify nodes that can run in parallel (no interdependencies)"""
        parallel_candidates = []

        for node in eligible_nodes:
            node_id = node["node_id"]
            node_role = node["agent_role"]

            # Check if this node has any dependencies on other eligible nodes
            has_parallel_conflicts = False
            for other_node in eligible_nodes:
                if other_node["node_id"] == node_id:
                    continue

                # Check if this node depends on the other node
                if other_node["agent_role"] in node.get("dependencies", []):
                    has_parallel_conflicts = True
                    break

                # Check if the other node depends on this node
                if node_role in other_node.get("dependencies", []):
                    has_parallel_conflicts = True
                    break

            if not has_parallel_conflicts:
                parallel_candidates.append(node)

        print(
            f"🔍 PARALLEL: {len(parallel_candidates)}/{len(eligible_nodes)} nodes can run in parallel"
        )
        return parallel_candidates

    def _create_parallel_dispatch(
        self, parallel_nodes: List[Dict], user_request: str, state: Dict
    ) -> List[Send]:
        """Create Send commands for parallel execution"""
        send_commands = []

        for node in parallel_nodes:
            node_id = node["node_id"]
            agent_role = node["agent_role"]

            # Create task description for this agent
            task_description = self._get_task_for_role(agent_role, user_request)

            # Create state for this specific agent
            agent_state = state.copy()
            agent_state.update(
                {
                    "current_node": node_id,
                    "current_role": agent_role,
                    "task_description": task_description,
                    "parallel_execution": True,
                    "parallel_batch_id": f"batch_{len(send_commands)}",
                }
            )

            print(f"🚀 PARALLEL: Dispatching {agent_role} (node: {node_id})")
            send_commands.append(Send(node_id, agent_state))

        return send_commands

    def _get_task_for_role(self, role: str, user_request: str) -> str:
        """Generate task description for agent role"""
        role_tasks = {
            "planner": f"Create a comprehensive project plan for: '{user_request}'. Break down into actionable steps.",
            "coder": f"Implement the solution for: '{user_request}'. Write clean, documented code following best practices.",
            "reviewer": f"Review the implemented solution for: '{user_request}'. Verify quality, correctness, and standards compliance.",
            "doc": f"Create comprehensive documentation for: '{user_request}'. Include usage examples and technical details.",
            "tester": f"Create and run tests for: '{user_request}'. Ensure comprehensive coverage and validation.",
        }
        return role_tasks.get(role, f"Execute the {role} role for: {user_request}")

    def _completion_node(self, state):
        """Final node that processes completion."""
        self.logger.debug("🔍 _completion_node() called")
        self.logger.debug(
            f"🔍 Completion input state keys: {list(state.keys()) if state else 'None'}"
        )
        self.logger.info("🏁 Executing completion node")

        completed_nodes = state.get("completed_nodes", [])
        agent_outputs = state.get("agent_outputs", {})
        project_name = state.get("project_name", "Unknown")
        project_path = state.get("project_path", "Unknown")
        errors = state.get("errors", [])
        failed_nodes = state.get("failed_nodes", [])

        self.logger.debug(f"🔍 Completion completed_nodes: {completed_nodes}")
        self.logger.debug(
            f"🔍 Completion agent_outputs keys: {list(agent_outputs.keys())}"
        )
        self.logger.debug(f"🔍 Completion project_name: {project_name}")
        self.logger.debug(f"🔍 Completion project_path: {project_path}")
        self.logger.debug(f"🔍 Completion errors: {errors}")
        self.logger.debug(f"🔍 Completion failed_nodes: {failed_nodes}")

        # Check if workflow succeeded or failed
        has_errors = bool(errors) or bool(failed_nodes)

        if has_errors:
            self.logger.error("❌ Workflow completed with errors")
            if errors:
                for error in errors:
                    self.logger.error(f"  • {error}")
            if failed_nodes:
                self.logger.error(f"  • Failed nodes: {failed_nodes}")

            success = False
            error_message = f"Workflow failed with {len(errors)} errors and {len(failed_nodes)} failed nodes"
        else:
            self.logger.info("🎉 Workflow completed successfully with no errors")
            success = True
            error_message = None

        self.logger.info("📊 Workflow completion summary:")
        self.logger.info(f"  🎯 Project: {project_name}")
        self.logger.info(f"  📁 Path: {project_path}")
        self.logger.info(
            f"  ✅ Completed nodes: {len(completed_nodes)} - {completed_nodes}"
        )
        self.logger.info(f"  📝 Agent outputs: {len(agent_outputs)} outputs generated")
        self.logger.info(f"  ⚠️ Errors: {len(errors)}")
        self.logger.info(f"  ❌ Failed nodes: {len(failed_nodes)}")
        self.logger.info(f"  🏆 Success: {success}")

        # Log details of each agent output
        for node_id, output in agent_outputs.items():
            self.logger.debug(
                f"🔍 Agent output {node_id}: {type(output)} - {str(output)[:100]}..."
            )

        # Check final project status
        if project_path and project_path != "Unknown":
            self.logger.debug(f"🔍 Checking final project status for: {project_path}")
            from pathlib import Path

            project_dir = Path(project_path)
            if project_dir.exists():
                try:
                    files = list(project_dir.glob("*"))
                    self.logger.info(f"📂 Project contains {len(files)} files:")
                    for file in files[:10]:  # Show first 10 files
                        self.logger.info(f"  📄 {file.name}")
                    if len(files) > 10:
                        self.logger.info(f"  ... and {len(files) - 10} more files")
                except Exception as e:
                    self.logger.warning(f"Could not list project files: {e}")
            else:
                self.logger.warning(f"Project directory does not exist: {project_path}")

        # CRITICAL FIX: Explicitly return ALL state values that need to be preserved
        # LangGraph requires nodes to return state updates, not just modify state in place
        completion_state_update = {
            "success": success,
            "completed_nodes": completed_nodes,
            "agent_outputs": agent_outputs,
            "project_name": project_name,
            "project_path": project_path,
            "errors": errors,
            "failed_nodes": failed_nodes,
        }

        # Add error message if present
        if error_message:
            completion_state_update["error"] = error_message

        # Add final output summary
        completion_state_update["final_output"] = {
            "summary": f"Workflow completed with {len(completed_nodes)} nodes, {len(agent_outputs)} agent outputs",
            "project_name": project_name,
            "project_path": project_path,
            "success": success,
        }

        self.logger.debug(
            f"🔍 COMPLETION DEBUG: Returning state update with keys: {list(completion_state_update.keys())}"
        )
        self.logger.debug(
            f"🔍 COMPLETION DEBUG: agent_outputs being returned: {len(completion_state_update['agent_outputs'])} outputs"
        )
        self.logger.debug(
            f"🔍 COMPLETION DEBUG: completed_nodes being returned: {len(completion_state_update['completed_nodes'])} nodes"
        )

        return completion_state_update

    def _setup_logging(self) -> logging.Logger:
        """Setup enhanced logging configuration with file outputs"""
        # Set console logging level based on debug mode
        console_level = logging.DEBUG if self.debug_mode else logging.INFO

        # Set up detailed logging to files for analysis (always DEBUG for files)
        self.log_files = setup_logging(
            console_level=console_level, file_level=logging.DEBUG
        )

        return logging.getLogger(self.__class__.__name__)

    def _analyze_workflow_logs(self) -> None:
        """Analyze logs from the workflow execution for issues"""
        try:
            print("\n📊 LOG ANALYSIS")
            print(f"   Debug Log: {self.log_files['debug_file']}")
            print(f"   Error Log: {self.log_files['error_file']}")
            print(f"   API Log: {self.log_files['api_file']}")

            # Analyze API errors specifically
            analyze_api_errors()

        except Exception as e:
            self.logger.warning(f"Could not analyze logs: {e}")

    async def run_workflow(
        self,
        user_request: str,
        context: Dict[str, Any] = None,
        interactive: bool = True,
    ) -> Dict[str, Any]:
        """
        Execute sophisticated agentic workflow using dynamic planning and orchestration.

        This method replaces the static workflow with AI-driven dynamic planning:
        1. WorkflowManager creates dynamic plan from natural language request
        2. WorkflowGraphBuilder constructs LangGraph from plan
        3. WorkflowExecutor handles sophisticated execution with MCP tools
        """
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        start_time = datetime.now()
        print(
            f"[{timestamp}] 🚀 DEBUG: Starting sophisticated workflow execution for: {user_request}"
        )
        sys.stdout.flush()

        try:
            # Check if sophisticated orchestration components are available
            if not self.workflow_manager:
                print(
                    f"[{timestamp}] ❌ ERROR: WorkflowManager not available - sophisticated mode required"
                )
                raise RuntimeError(
                    "WorkflowManager initialization failed - cannot proceed without sophisticated orchestration"
                )
                # COMMENTED OUT: Legacy fallback disabled to force sophisticated mode
                # return await self._run_legacy_workflow(
                #     user_request, context, interactive
                # )

            # Phase 1: Dynamic Workflow Planning using WorkflowManager
            print(
                f"[{timestamp}] 🧠 DEBUG: Creating dynamic workflow plan with WorkflowManager..."
            )

            workflow_plan = self.workflow_manager.create_enhanced_workflow_plan(
                user_request=user_request,
                context=context or {},
                interactive=interactive,
            )

            if not workflow_plan:
                print(f"[{timestamp}] ❌ CRITICAL: Failed to create workflow plan")
                print(
                    f"[{timestamp}] 💡 HINT: Check WorkflowManager.create_enhanced_workflow_plan() method"
                )
                raise RuntimeError(
                    "WorkflowManager failed to create workflow plan - sophisticated mode requires valid plan generation"
                )

            print(
                f"[{timestamp}] ✅ DEBUG: Workflow plan created with {len(workflow_plan.nodes)} nodes"
            )

            # USER LOGGING: Start workflow with clean visual display
            if hasattr(self, "user_logger") and self.user_logger:
                self.user_logger.start_workflow(user_request, workflow_plan)

            # Phase 1.5: Setup Project Context for File Operations
            print(
                f"[{timestamp}] 📁 DEBUG: Setting up project context for file operations..."
            )

            # Create project directory based on user request (same logic as legacy workflow)
            sanitized_request = re.sub(r"[^\w\s-]", "", user_request).strip().lower()
            project_slug = re.sub(r"[-\s]+", "-", sanitized_request)
            project_slug = "-".join(project_slug.split("-")[:5])
            timestamp_for_project = datetime.now().strftime("%Y%m%d_%H%M")

            project_name = f"{project_slug}_{timestamp_for_project}"
            project_path = Path("projects") / project_name

            # Create the project directory
            project_path.mkdir(parents=True, exist_ok=True)
            print(f"[{timestamp}] 📁 DEBUG: Created project directory: {project_path}")

            # Set global project context that agents can access
            ProjectContextManager.set_context(
                project_name=project_name, project_path=str(project_path)
            )
            print(
                f"[{timestamp}] ✅ DEBUG: Global project context set - agents can now write files to: {project_path}"
            )

            # Phase 2: Dynamic Graph Construction using WorkflowGraphBuilder
            print(
                f"[{timestamp}] 📊 DEBUG: Building dynamic LangGraph from workflow plan..."
            )

            # Create MCP-enabled agents for each node in the plan
            agent_creators = await self._create_mcp_enabled_agents(workflow_plan)

            if not self.graph_builder:
                print(f"[{timestamp}] ❌ CRITICAL: WorkflowGraphBuilder not available")
                raise RuntimeError(
                    "WorkflowGraphBuilder component missing - sophisticated mode requires this for dynamic graph construction"
                )

            workflow_graph = self.graph_builder.create_dynamic_workflow_graph(
                workflow_plan=workflow_plan, agent_creators=agent_creators
            )

            print(f"[{timestamp}] ✅ DEBUG: Dynamic LangGraph constructed successfully")

            # Phase 3: Sophisticated Execution using WorkflowExecutor
            print(
                f"[{timestamp}] ⚡ DEBUG: Executing workflow with sophisticated orchestration..."
            )

            if not self.workflow_executor:
                print(f"[{timestamp}] ❌ CRITICAL: WorkflowExecutor not available")
                raise RuntimeError(
                    "WorkflowExecutor component missing - sophisticated mode requires this for execution"
                )

            # CRITICAL FIX: Include project context in the context passed to WorkflowExecutor
            # so it gets properly included in the initial LangGraph state
            enhanced_context = (context or {}).copy()
            enhanced_context.update(
                {
                    "project_name": project_name,
                    "project_path": str(project_path),
                }
            )

            print(
                f"[{timestamp}] 🔧 DEBUG: Enhanced context with project info: {list(enhanced_context.keys())}"
            )

            # CRITICAL FIX: Create initial_state to prevent WorkflowExecutor from re-creating project
            initial_state = create_initial_state(
                user_request=user_request,
                context=enhanced_context,
                workflow_plan=workflow_plan,
            )

            result = await self.workflow_executor.execute_agentic_workflow(
                user_request=user_request,
                workflow_plan=workflow_plan,
                workflow_graph=workflow_graph,
                context=enhanced_context,  # Pass enhanced context with project info
                interactive=interactive,
                initial_state=initial_state,  # Pass initial state to prevent re-initialization
            )

            print(
                f"[{timestamp}] 🎉 DEBUG: Sophisticated workflow execution completed successfully"
            )

            # USER LOGGING: Complete workflow with success banner
            total_time = str(datetime.now() - start_time).split(".")[0]
            if hasattr(self, "user_logger") and self.user_logger:
                self.user_logger.complete_workflow(success=True, total_time=total_time)

            # Cleanup: Clear project context after execution
            ProjectContextManager.clear_context()
            print(
                f"[{timestamp}] 🧹 DEBUG: Project context cleared after successful execution"
            )

            return result

        except Exception as e:
            error_msg = f"Sophisticated workflow execution failed: {str(e)}"
            print(f"[{timestamp}] ❌ DEBUG: {error_msg}")
            print(f"[{timestamp}] 🔧 DEBUG: Traceback: {traceback.format_exc()}")

            # USER LOGGING: Complete workflow with failure banner
            total_time = str(datetime.now() - start_time).split(".")[0]
            if hasattr(self, "user_logger") and self.user_logger:
                self.user_logger.complete_workflow(
                    success=False, total_time=total_time, error_msg=error_msg
                )

            # Cleanup: Clear project context even on failure
            ProjectContextManager.clear_context()
            print(f"[{timestamp}] 🧹 DEBUG: Project context cleared after error")

            # COMMENTED OUT: Legacy fallback disabled to force sophisticated mode
            # Fallback to legacy workflow if sophisticated orchestration fails
            # print(
            #     f"[{timestamp}] 🔄 DEBUG: Falling back to legacy workflow due to error"
            # )
            # return await self._run_legacy_workflow(user_request, context, interactive)

            # Re-raise the exception instead of falling back
            raise RuntimeError(
                f"Sophisticated workflow execution failed: {str(e)}"
            ) from e

    async def _create_mcp_enabled_agents(self, workflow_plan) -> Dict[str, Callable]:
        """Create MCP-enabled agents for each node in the workflow plan"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(
            f"[{timestamp}] 🤖 DEBUG: Creating MCP-enabled agents for {len(workflow_plan.nodes)} nodes..."
        )

        agent_creators = {}

        # Initialize AgentFactory with MCP tools if not already done
        if not self.agent_factory:
            try:
                self.agent_factory = AgentFactory(
                    llm_config={"model": "gpt-4.1-mini"},
                    neo4j_client=self.neo4j_client,  # FIXED: Changed from gpt-4o to approved model
                )
                print(
                    f"[{timestamp}] ✅ DEBUG: AgentFactory initialized with MCP support"
                )
            except Exception as e:
                print(
                    f"[{timestamp}] ⚠️ DEBUG: AgentFactory initialization failed: {e}"
                )
                return {}

        for node in workflow_plan.nodes:
            try:
                # Create agent spec with MCP tools enabled
                agent_spec = {
                    "role": node.agent_role,
                    "task_description": node.description,  # Fix: use correct attribute name
                    "tools": node.tools_required
                    or [],  # Fix: use correct attribute name
                    "enable_mcp_tools": True,  # Enable MCP research capabilities
                    "mcp_registry": self.mcp_registry,
                    "node_id": node.id,
                    "dependencies": node.dependencies
                    or [],  # Now available in the model
                }

                # Create agent creator function that will be used by the graph
                def create_agent_for_node(node_spec=agent_spec):
                    def agent_node_function(state):
                        return self._run_mcp_enabled_agent_node(state, node_spec)

                    return agent_node_function

                agent_creators[node.id] = create_agent_for_node()
                print(
                    f"[{timestamp}] ✅ DEBUG: Created MCP-enabled agent for node: {node.id} (role: {node.agent_role})"
                )

            except Exception as e:
                print(
                    f"[{timestamp}] ⚠️ DEBUG: Failed to create agent for node {node.id}: {e}"
                )
                continue

        print(
            f"[{timestamp}] 🎉 DEBUG: Created {len(agent_creators)} MCP-enabled agents"
        )
        return agent_creators

    def _run_mcp_enabled_agent_node(
        self, state: AgenticWorkflowState, agent_spec: Dict[str, Any]
    ):
        """Execute an MCP-enabled agent node using AgentFactory with enhanced tools"""
        from datetime import datetime

        from langchain_core.messages import HumanMessage

        start_time = time.time()  # FIX: Add missing start_time definition
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] 🚀 DEBUG: _run_mcp_enabled_agent_node called")

        role = agent_spec.get("role", "unknown")
        node_id = agent_spec.get("node_id", role)

        print(f"[{timestamp}] 🤖 DEBUG: Executing {role} agent (node: {node_id})")

        # CRITICAL FIX: Ensure global project context is set for this agent
        project_name = state.get("project_name")
        project_path = state.get("project_path")

        if project_name and project_path:
            from src.applications.oamat.utils.project_context import (
                ProjectContextManager,
            )

            ProjectContextManager.set_context(project_name, project_path)
            print(
                f"[{timestamp}] ✅ DEBUG: Set global project context for {role} agent: {project_path}"
            )
        else:
            print(
                f"[{timestamp}] ⚠️ DEBUG: No project context found in state for {role} agent"
            )
            print(f"[{timestamp}] 🔍 DEBUG: State keys: {list(state.keys())}")

        # Create the agent with AgentFactory
        agent_creation_start = time.time()
        print(f"[{timestamp}] 🏗️ DEBUG: Creating agent with AgentFactory...")

        if not self.agent_factory:
            print(f"[{timestamp}] ❌ DEBUG: AgentFactory not initialized")
            return {"errors": [f"AgentFactory not available for {role}"]}

        enhanced_agent_spec = agent_spec.copy()

        # Essential tools that every agent should have
        essential_tools = ["file_system", "complete"]

        # Role-specific tool additions
        role_specific_tools = {
            "planner": ["generate_code", "knowledge_search"],
            "architect": ["diagram_generators", "web_search"],
            "frontend_developer": ["generate_code", "web_search"],
            "backend_developer": ["generate_code", "web_search"],
            "tester": ["testing_frameworks", "generate_code"],
            "deployer": ["deployment_tools", "monitoring_tools"],
            "reviewer": ["review_content", "quality_tools"],
        }

        if role in role_specific_tools:
            essential_tools.extend(role_specific_tools[role])

        # If no tools specified, use essential tools
        if not enhanced_agent_spec.get("tools"):
            enhanced_agent_spec["tools"] = essential_tools
            print(f"[{timestamp}] ✅ DEBUG: Added essential tools: {essential_tools}")
        else:
            # Merge with existing tools, ensuring no duplicates
            existing_tools = enhanced_agent_spec.get("tools", [])
            merged_tools = list(set(existing_tools + essential_tools))
            enhanced_agent_spec["tools"] = merged_tools
            print(f"[{timestamp}] ✅ DEBUG: Merged tools: {merged_tools}")

        # Create agent with tools enabled via create_agent_with_tools
        agent_spec_for_creation = {
            "role": role,
            "dependencies": enhanced_agent_spec["tools"],  # Use tools as dependencies
        }

        agent = self.agent_factory.create_agent_with_tools(spec=agent_spec_for_creation)
        agent_creation_time = time.time() - agent_creation_start
        print(
            f"[{timestamp}] ✅ DEBUG: Agent created in {agent_creation_time:.3f}s WITH {len(enhanced_agent_spec['tools'])} tools"
        )

        # Execute agent with current state context
        agent_context = self._get_agent_context(
            state, node_id, role, self._get_project_path(state)
        )

        # Create prompt from agent task description and user request
        user_request = state.get("user_request", "")
        task_description = agent_spec.get(
            "task_description", f"Complete the {role} task"
        )

        # ENHANCED: Add explicit file saving instructions
        enhanced_prompt = f"""
**User Request**: {user_request}

**Your Task as {role}**: {task_description}

**Previous Agent Outputs**: {agent_context.get("previous_outputs", {})}

**Project Context**: {agent_context.get("shared_context", {})}

**CRITICAL REQUIREMENTS**:
- You MUST save all your work to files using the write_file tool
- Create appropriate files for your output (e.g., .md for documentation, .py for code)
- Use descriptive filenames that reflect the content
- Example: write_file("project_plan.md", "# Project Plan\\n\\nYour content here...")

Your work is only valuable if it's saved to files. Always use write_file for your deliverables.

Please complete this task and save your results to appropriate files.
            """.strip()

        # Invoke agent with context
        invoke_start = time.time()
        print(f"[{timestamp}] 🚀 DEBUG: Invoking agent with LLM call...")
        print(
            f"[{timestamp}] 🚀 DEBUG: Prompt length: {len(enhanced_prompt)} characters"
        )

        # Log prompt with truncation for debug/console and full content for API
        log_prompt_response(
            content=enhanced_prompt,
            content_type="prompt",
            context=f"{role} Agent",
            timestamp=timestamp,
            debug_mode=True,
        )

        result = agent.invoke({"messages": [HumanMessage(content=enhanced_prompt)]})
        invoke_time = time.time() - invoke_start
        print(
            f"[{timestamp}] ✅ DEBUG: Agent invocation completed in {invoke_time:.3f}s"
        )

        if invoke_time < 1.0:
            print(
                f"[{timestamp}] 🚨 WARNING: Agent invocation too fast! ({invoke_time:.3f}s)"
            )
            print(f"[{timestamp}] 🚨 This suggests no real LLM call was made!")

        # Log response with truncation for debug/console and full content for API
        if isinstance(result, dict) and "messages" in result and result["messages"]:
            last_msg = result["messages"][-1]
            if hasattr(last_msg, "content"):
                response_content = str(last_msg.content)
                log_prompt_response(
                    content=response_content,
                    content_type="response",
                    context=f"{role} Agent",
                    timestamp=timestamp,
                    debug_mode=True,
                )

        # Check result structure
        print(f"[{timestamp}] 📊 DEBUG: Result type: {type(result)}")
        print(
            f"[{timestamp}] 📊 DEBUG: Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}"
        )
        if isinstance(result, dict) and "messages" in result:
            print(
                f"[{timestamp}] 📊 DEBUG: Number of messages in result: {len(result['messages'])}"
            )
            if result["messages"]:
                last_msg = result["messages"][-1]
                print(f"[{timestamp}] 📊 DEBUG: Last message type: {type(last_msg)}")
                if hasattr(last_msg, "content"):
                    print(
                        f"[{timestamp}] 📊 DEBUG: Last message content length: {len(str(last_msg.content))}"
                    )

        # Update state with agent result
        if "messages" not in state:
            state["messages"] = []
        state["messages"].extend(result.get("messages", []))
        state["current_agent"] = role
        state["last_agent_output"] = str(
            result.get("messages", [])[-1].content if result.get("messages") else ""
        )

        # Mark this node as completed so supervisor can track progress
        if "completed_nodes" not in state:
            state["completed_nodes"] = []
        if node_id not in state["completed_nodes"]:
            state["completed_nodes"].append(node_id)
            print(
                f"[{timestamp}] ✅ DEBUG: Added {node_id} to completed_nodes: {state['completed_nodes']}"
            )

        # Store agent output for later reference
        if "agent_outputs" not in state:
            state["agent_outputs"] = {}
        state["agent_outputs"][node_id] = {
            "role": role,
            "output": state["last_agent_output"],
            "timestamp": timestamp,
        }

        total_time = time.time() - start_time
        print(
            f"[{timestamp}] ✅ DEBUG: MCP-enabled agent {node_id} completed successfully in {total_time:.3f}s"
        )

        if total_time < 2.0:
            print(
                f"[{timestamp}] 🚨 WARNING: Total agent execution too fast! ({total_time:.3f}s)"
            )
            print(f"[{timestamp}] 🚨 Real agent execution should take 5-30+ seconds!")

        return state

    def _get_mcp_tools_for_role(self, role: str) -> List[str]:
        """Get appropriate MCP tools for an agent role (DEPRECATED - use _get_mcp_tool_instances_for_role)"""
        if not self.mcp_registry:
            return []

        # Define role-to-tools mapping for intelligent tool selection
        role_tool_mapping = {
            "researcher": [
                "brave_web_search",
                "arxiv_search",
                "firecrawl_scrape",
                "sequential_thinking",
            ],
            "planner": ["sequential_thinking", "neo4j_query"],
            "coder": ["sequential_thinking", "context7_docs"],
            "reviewer": ["sequential_thinking", "context7_docs"],
            "analyst": [
                "brave_web_search",
                "arxiv_search",
                "sequential_thinking",
                "neo4j_query",
            ],
            "writer": ["brave_web_search", "sequential_thinking"],
            "default": ["sequential_thinking"],
        }

        return role_tool_mapping.get(role.lower(), role_tool_mapping["default"])

    def _get_mcp_tool_instances_for_role(self, role: str) -> List[Any]:
        """Get actual MCP tool instances for an agent role"""
        if not self.mcp_registry:
            return []

        # Define role-to-MCP-tools mapping using correct MCP tool names
        role_tool_mapping = {
            "researcher": [
                "mcp_mcp_web_search_brave_web_search",
                "mcp_research_papers_search_papers",
                "mcp_web_scraping_firecrawl_scrape",
                "mcp_thinking_sequentialthinking",
            ],
            "planner": [
                "mcp_thinking_sequentialthinking",
                "mcp_neo4j-mcp_read_neo4j_cypher",
            ],
            "coder": [
                "mcp_thinking_sequentialthinking",
                "mcp_tech_docs_get-library-docs",
            ],
            "tester": [
                "mcp_shell_shell_exec",
            ],
            "reviewer": [
                "mcp_thinking_sequentialthinking",
                "mcp_tech_docs_get-library-docs",
            ],
            "analyst": [
                "mcp_mcp_web_search_brave_web_search",
                "mcp_research_papers_search_papers",
                "mcp_thinking_sequentialthinking",
                "mcp_neo4j-mcp_read_neo4j_cypher",
            ],
            "writer": [
                "mcp_mcp_web_search_brave_web_search",
                "mcp_thinking_sequentialthinking",
            ],
            "doc": ["mcp_thinking_sequentialthinking"],
            "default": ["mcp_thinking_sequentialthinking"],
        }

        tool_names = role_tool_mapping.get(role.lower(), role_tool_mapping["default"])
        tool_instances = []

        # Get actual tool instances from MCP registry
        for tool_name in tool_names:
            try:
                tool_instance = self.mcp_registry.get_tool(tool_name)
                if tool_instance:
                    tool_instances.append(tool_instance)
                    print(f"🔧 DEBUG: Added MCP tool: {tool_name}")
                else:
                    print(f"⚠️ DEBUG: MCP tool not found: {tool_name}")
            except Exception as e:
                print(f"❌ DEBUG: Error getting MCP tool {tool_name}: {e}")

        return tool_instances

    def _get_project_path(self, state: AgenticWorkflowState) -> Path:
        """Get project path from state or global context"""
        if hasattr(state, "project_path") and state.get("project_path"):
            return Path(state["project_path"])

        # Try to get project path from global project context
        global_project_path = ProjectContextManager.get_project_path()
        if global_project_path:
            return Path(global_project_path)

        # Fallback: create default project path
        project_name = f"default_project_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        return Path("projects") / project_name

    async def _run_legacy_workflow(
        self,
        user_request: str,
        context: Dict[str, Any] = None,
        interactive: bool = True,
    ) -> Dict[str, Any]:
        """
        Legacy workflow execution method (kept for fallback compatibility).
        This is the original static workflow that gets replaced by sophisticated orchestration.
        """
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] 🔄 DEBUG: Executing legacy workflow as fallback...")

        # Initialize agent factory if not done
        if not self.agent_factory:
            try:
                self.agent_factory = AgentFactory(
                    llm_config={"model": "gpt-4.1-mini"},
                    neo4j_client=self.neo4j_client,  # FIXED: Changed from gpt-4o to approved model
                )
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to initialize AgentFactory: {e}",
                }

        try:
            # Define the static graph with timeout protection
            workflow = StateGraph(AgenticWorkflowState)

            # Define nodes
            workflow.add_node("supervisor", self._supervisor_node)
            workflow.add_node("planner", self._run_agent_node_factory("planner"))
            workflow.add_node("coder", self._run_agent_node_factory("coder"))
            workflow.add_node("reviewer", self._run_agent_node_factory("reviewer"))
            workflow.add_node("completion", self._completion_node)

            # Define edges
            workflow.add_edge(START, "supervisor")
            # RULE 955: Command-based routing with simplified conditional edges
            workflow.add_conditional_edges(
                "supervisor",
                self._command_router,
                {
                    "planner": "planner",
                    "coder": "coder",
                    "reviewer": "reviewer",
                    "completion": "completion",
                },
            )
            workflow.add_edge("planner", "supervisor")
            workflow.add_edge("coder", "supervisor")
            workflow.add_edge("reviewer", "supervisor")
            workflow.add_edge("completion", END)

            # Compile graph with timeout handling
            import signal

            compilation_timeout = 60

            def compilation_timeout_handler(signum, frame):
                raise TimeoutError(
                    f"Graph compilation timed out after {compilation_timeout} seconds"
                )

            signal.signal(signal.SIGALRM, compilation_timeout_handler)
            signal.alarm(compilation_timeout)

            try:
                compiled_graph = workflow.compile()
                signal.alarm(0)  # Cancel timeout
            except TimeoutError:
                return {"success": False, "error": "Graph compilation timeout"}

            # Create initial state
            project_name, project_path = self._create_project_context(
                {"user_request": user_request}
            )
            initial_state = create_initial_state(
                user_request, project_name, str(project_path)
            )

            # Execute workflow with timeout
            async def run_with_timeout():
                try:
                    final_state = await compiled_graph.ainvoke(initial_state)
                    return final_state
                except Exception as e:
                    print(f"[{timestamp}] ❌ DEBUG: Workflow execution failed: {e}")
                    return {"success": False, "error": str(e)}

            final_state = await asyncio.wait_for(run_with_timeout(), timeout=600)

            # Analyze results
            self._analyze_workflow_logs()

            return {
                "success": final_state.get("success", False),
                "message": "Legacy workflow completed",
                "files_created": final_state.get("total_files_created", 0),
                "project_path": str(project_path),
                "final_state": final_state,
            }

        except Exception as e:
            error_msg = f"Legacy workflow failed: {str(e)}"
            print(f"[{timestamp}] ❌ DEBUG: {error_msg}")
            return {"success": False, "error": error_msg}

    def _command_router(self, state):
        """RULE 955: Command-based router for modern LangGraph patterns"""
        self.logger.debug("🔍 _command_router() called")

        # Read the Command decision from supervisor
        next_node = state.get("next_node", "completion")
        self.logger.debug(f"🎯 Command routing to: {next_node}")

        # Route based on Command decision (supports dynamic workflow nodes)
        if next_node == "completion":
            return "completion"
        elif next_node in ["planner", "coder", "reviewer", "doc", "tester"]:
            return next_node
        else:
            # Graceful fallback for unknown commands
            self.logger.warning(
                f"⚠️ Unknown command target: {next_node}, routing to completion"
            )
            return "completion"

    def _run_agent_node_factory(self, role: str):
        """Returns a function that runs an agent node for a specific role."""

        def _run_agent_node_for_role(state):
            # The config parameter is not used in the static graph, so we can pass an empty dict
            return self._run_agent_node(state, config={}, node_id=role)

        return _run_agent_node_for_role

    def run_interactive(self) -> None:
        """Run interactive workflow mode"""
        print(
            """
🚀 OAMAT - INTELLIGENT WORKFLOW ORCHESTRATION
========================================

Welcome to OAMAT's LangGraph Supervisor-Based Multi-Agent System!

This system features:
• 🧠 AI Supervisor: Intelligent routing decisions based on workflow state
• 🤖 Self-Contained Agents: Research, Code, Review, Documentation agents
• 🔄 LangGraph Native: MessagesState, checkpointing, and conditional edges
• 🛠️ Tool Integration: Neo4j knowledge base and MCP tools
• 📊 Quality Assurance: Built-in validation and error recovery

Based on proven patterns from gpt-researcher and LangGraph best practices.

Type 'quit', 'exit', or 'q' to exit.
"""
        )

        while True:
            try:
                # Get user input
                user_request = input("\n🎯 Enter your request: ").strip()

                if user_request.lower() in ["quit", "exit", "q", ""]:
                    print("Goodbye!")
                    break

                # Execute workflow with interactive review (unless --no-review is set)
                print(f"\n🚀 Processing: {user_request}")
                interactive_review = not self.no_review
                result = asyncio.run(
                    self.run_workflow(user_request, interactive=interactive_review)
                )

                # Display results with improved formatting
                if result.get("success"):
                    print("\n✅ Workflow completed successfully!")

                    # Show workflow details
                    workflow_id = result.get("workflow_id", "Unknown")
                    print(f"   🆔 Workflow ID: {workflow_id}")

                    # Show agents used
                    agent_outputs = result.get("agent_outputs", {})
                    if agent_outputs:
                        print(f"   🤖 Agents used: {', '.join(agent_outputs.keys())}")

                    # Show final output with pretty formatting
                    final_output = result.get("final_output")
                    if final_output:
                        print("\n📋 Results:")
                        if isinstance(final_output, dict):
                            for key, value in final_output.items():
                                if key not in ["workflow_id", "timestamp", "success"]:
                                    if isinstance(value, str) and len(value) > 100:
                                        # Truncate long strings
                                        print(f"   {key}: {value[:100]}...")
                                    elif isinstance(value, dict) or isinstance(
                                        value, list
                                    ):
                                        print(f"   {key}: {len(value)} items")
                                    else:
                                        print(f"   {key}: {value}")
                        else:
                            print(f"   {final_output}")

                    # Show timing if available
                    timestamp = result.get("timestamp")
                    if timestamp:
                        print(f"   🕐 Completed: {timestamp}")

                else:
                    print(
                        f"\n❌ Workflow failed: {result.get('error', 'Unknown error')}"
                    )

            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                if self.debug_mode:
                    import traceback

                    traceback.print_exc()

    def run_single_request(
        self, user_request: str, context: Dict[str, Any] = None
    ) -> None:
        """Run a single request and exit."""
        self.logger.debug("🔍 run_single_request() called")
        self.logger.debug(f"🔍 user_request: {user_request}")
        self.logger.debug(f"🔍 context: {context}")
        self.logger.info("🎯 Running single request mode")
        self.logger.info(f"📝 Request: {user_request}")

        print(f"\n{'='*80}")
        print("🚀 OAMAT - MODERN LANGGRAPH ORCHESTRATION")
        print(f"{'='*80}")
        print(f"\nProcessing: {user_request}")

        try:
            # Run the workflow
            self.logger.debug("🔍 Calling asyncio.run() with run_workflow()...")
            result = asyncio.run(
                self.run_workflow(user_request, context, interactive=False)
            )
            self.logger.debug("🔍 asyncio.run() completed")
            self.logger.debug(f"🔍 Single request result: {result}")

            if result.get("success"):
                self.logger.info("✅ Single request completed successfully")
                self.logger.debug(f"🔍 Success result details: {result}")
                print("\n✅ SUCCESS: Workflow completed")

                # Show project information
                if result.get("project_name"):
                    self.logger.debug(
                        f"🔍 Displaying project_name: {result['project_name']}"
                    )
                    print(f"📁 Project: {result['project_name']}")
                if result.get("project_path"):
                    self.logger.debug(
                        f"🔍 Displaying project_path: {result['project_path']}"
                    )
                    print(f"📂 Location: {result['project_path']}")
                if result.get("execution_time"):
                    self.logger.debug(
                        f"🔍 Displaying execution_time: {result['execution_time']}"
                    )
                    print(f"⏱️ Time: {result['execution_time']:.2f} seconds")

            else:
                self.logger.error(f"❌ Single request failed: {result.get('error')}")
                self.logger.debug(f"🔍 Failure result details: {result}")
                print(f"\n❌ ERROR: {result.get('error', 'Unknown error')}")

        except Exception as e:
            self.logger.error(f"💥 Exception in single request: {e}")
            self.logger.debug(
                f"🔍 Single request exception: {type(e).__name__}: {str(e)}"
            )
            print(f"\n💥 EXCEPTION: {e}")
            import traceback

            traceback.print_exc()


def main():
    """Main entry point for OAMAT."""
    print("🔍 main() called")

    parser = argparse.ArgumentParser(
        description="OAMAT - Modern LangGraph Orchestration"
    )
    parser.add_argument("request", nargs="?", help="Single request to process")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument(
        "--agent-details", action="store_true", help="Show agent details"
    )
    parser.add_argument("--no-review", action="store_true", help="Skip review phase")

    args = parser.parse_args()
    print(f"🔍 Parsed args: {args}")

    # Initialize OAMAT
    print("�� Initializing OAMATMain...")
    oamat = OAMATMain(
        debug_mode=args.debug,
        agent_details=args.agent_details,
        no_review=args.no_review,
    )
    print("🔍 OAMATMain initialized")

    # Log startup information
    oamat.logger.info("🚀 OAMAT starting up...")
    oamat.logger.info(f"🔧 Debug mode: {args.debug}")
    oamat.logger.info(f"👥 Agent details: {args.agent_details}")
    oamat.logger.info(f"⏭️ Skip review: {args.no_review}")
    oamat.logger.debug(f"🔍 Command line args: {args}")

    if args.request:
        oamat.logger.info(f"📋 Single request mode: {args.request}")
        oamat.logger.debug("🔍 Calling run_single_request()...")
        oamat.run_single_request(args.request)
        oamat.logger.debug("🔍 run_single_request() completed")
    else:
        oamat.logger.info("💬 Interactive mode starting")
        oamat.logger.debug("🔍 Calling run_interactive()...")
        oamat.run_interactive()
        oamat.logger.debug("🔍 run_interactive() completed")

    oamat.logger.debug("🔍 main() completed")


if __name__ == "__main__":
    main()
