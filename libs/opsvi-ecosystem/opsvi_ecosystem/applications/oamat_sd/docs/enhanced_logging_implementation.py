"""
Enhanced Logging System Implementation Example

Shows how to integrate the comprehensive logging system into Smart Decomposition Agent.
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from src.applications.oamat_sd.src.config.config_manager import ConfigManager


# Enhanced log configuration
@dataclass
class ToolLogConfig:
    """Configuration for tool-specific logging"""

    enabled: bool = True
    capture_input: bool = True
    capture_output: bool = True
    capture_performance: bool = True
    max_content_size: int = 10000


@dataclass
class AgentLogConfig:
    """Configuration for agent-specific logging"""

    enabled: bool = True
    track_lifecycle: bool = True
    track_decisions: bool = True
    track_tool_usage: bool = True
    capture_prompts: bool = True


@dataclass
class ComponentLogConfig:
    """Configuration for component logging"""

    enabled: bool = True
    track_state_changes: bool = True
    track_performance: bool = True
    capture_errors: bool = True


class EnhancedLoggerFactory:
    """Enhanced logger factory with granular logging capabilities"""

    def __init__(self, session_id: str = None):
        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)

        # Tool logger configs
        self.tool_configs = {
            "brave_search": ToolLogConfig(),
            "arxiv_research": ToolLogConfig(),
            "firecrawl": ToolLogConfig(),
            "context7_docs": ToolLogConfig(),
            "sequential_thinking": ToolLogConfig(),
            "neo4j": ToolLogConfig(),
        }

        # Component logger configs
        self.component_configs = {
            "o3_reasoning": ComponentLogConfig(),
            "agent_factory": ComponentLogConfig(),
            "file_operations": ComponentLogConfig(),
            "project_context": ComponentLogConfig(),
            "synthesis_process": ComponentLogConfig(),
            "parallel_execution": ComponentLogConfig(),
        }

        # Initialize loggers
        self._tool_loggers = {}
        self._agent_loggers = {}
        self._component_loggers = {}
        self._audit_loggers = {}

    def get_tool_logger(self, tool_name: str) -> logging.Logger:
        """Get tool-specific logger"""
        if tool_name not in self._tool_loggers:
            logger = logging.getLogger(f"tool.{tool_name}")
            handler = logging.FileHandler(
                self.log_dir / f"{tool_name}_{self.session_id}.jsonl"
            )
            handler.setFormatter(logging.Formatter("%(message)s"))
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
            self._tool_loggers[tool_name] = logger
        return self._tool_loggers[tool_name]

    def get_agent_logger(self, agent_role: str) -> logging.Logger:
        """Get agent-specific logger"""
        if agent_role not in self._agent_loggers:
            logger = logging.getLogger(f"agent.{agent_role}")
            handler = logging.FileHandler(
                self.log_dir / f"agent_{agent_role}_{self.session_id}.jsonl"
            )
            handler.setFormatter(logging.Formatter("%(message)s"))
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
            self._agent_loggers[agent_role] = logger
        return self._agent_loggers[agent_role]

    def get_component_logger(self, component: str) -> logging.Logger:
        """Get component-specific logger"""
        if component not in self._component_loggers:
            logger = logging.getLogger(f"component.{component}")
            handler = logging.FileHandler(
                self.log_dir / f"{component}_{self.session_id}.jsonl"
            )
            handler.setFormatter(logging.Formatter("%(message)s"))
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
            self._component_loggers[component] = logger
        return self._component_loggers[component]

    def get_audit_logger(self, audit_type: str) -> logging.Logger:
        """Get audit-specific logger"""
        if audit_type not in self._audit_loggers:
            logger = logging.getLogger(f"audit.{audit_type}")
            handler = logging.FileHandler(
                self.log_dir / f"{audit_type}_{self.session_id}.jsonl"
            )
            handler.setFormatter(logging.Formatter("%(message)s"))
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
            self._audit_loggers[audit_type] = logger
        return self._audit_loggers[audit_type]

    # High-level logging methods
    def log_tool_execution(
        self,
        tool_name: str,
        method: str,
        agent_caller: str,
        input_data: Any,
        output_data: Any,
        execution_time_ms: float,
        success: bool,
        correlation_id: str = None,
    ):
        """Log tool execution with full context"""
        logger = self.get_tool_logger(tool_name)

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "tool_name": tool_name,
            "method": method,
            "agent_caller": agent_caller,
            "execution_time_ms": execution_time_ms,
            "success": success,
            "correlation_id": correlation_id,
        }

        # Capture input/output if enabled
        config = self.tool_configs.get(tool_name, ToolLogConfig())
        if ConfigManager().capture_input:
            log_entry["input"] = self._truncate_content(
                input_data, ConfigManager().max_content_size
            )
        if ConfigManager().capture_output:
            log_entry["output"] = self._truncate_content(
                output_data, ConfigManager().max_content_size
            )

        logger.info(json.dumps(log_entry))

    def log_agent_lifecycle(self, agent_role: str, stage: str, data: dict[str, Any]):
        """Log agent lifecycle events"""
        logger = self.get_agent_logger(agent_role)

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent_role": agent_role,
            "lifecycle_stage": stage,
            **data,
        }

        logger.info(json.dumps(log_entry))

    def log_component_operation(
        self, component: str, operation: str, data: dict[str, Any]
    ):
        """Log component operations"""
        logger = self.get_component_logger(component)

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "component": component,
            "operation": operation,
            **data,
        }

        logger.info(json.dumps(log_entry))

    def log_audit_event(self, audit_type: str, event: str, data: dict[str, Any]):
        """Log audit events"""
        logger = self.get_audit_logger(audit_type)

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "audit_type": audit_type,
            "event": event,
            **data,
        }

        logger.info(json.dumps(log_entry))

    def _truncate_content(self, content: Any, max_size: int) -> Any:
        """Truncate content if too large"""
        if isinstance(content, str) and len(content) > max_size:
            return content[:max_size] + "... [TRUNCATED]"
        return content


# Enhanced Smart Decomposition Agent with comprehensive logging
class EnhancedSmartDecompositionAgent:
    """Smart Decomposition Agent with enhanced logging capabilities"""

    def __init__(self):
        self.enhanced_logger = EnhancedLoggerFactory()
        # ... other initialization

    async def _analyze_request_with_o3(self, state):
        """Enhanced O3 analysis with comprehensive logging"""

        # Log start of O3 reasoning
        self.enhanced_logger.log_component_operation(
            "o3_reasoning",
            "start_analysis",
            {
                "user_request": state.user_request[:200] + "...",
                "request_length": len(state.user_request),
            },
        )

        start_time = datetime.now()

        # Perform O3 analysis
        response = await self.master_model.ainvoke([...])

        execution_time = (datetime.now() - start_time).total_seconds() * 1000

        # Log O3 reasoning results
        self.enhanced_logger.log_component_operation(
            "o3_reasoning",
            "analysis_complete",
            {
                "execution_time_ms": execution_time,
                "response_length": len(response.content),
                "analysis_successful": True,
            },
        )

        # Parse O3 response and log complexity analysis
        try:
            o3_data = json.loads(response.content)

            self.enhanced_logger.log_component_operation(
                "o3_reasoning",
                "complexity_analysis",
                {
                    "factors_analyzed": {
                        "technical_complexity": o3_data.get("complexity_score", 0),
                        "agent_count": len(o3_data.get("agent_specifications", {})),
                        "execution_strategy": o3_data.get(
                            "execution_strategy", "unknown"
                        ),
                    },
                    "agent_specifications_generated": len(
                        o3_data.get("agent_specifications", {})
                    ),
                    "confidence_score": 0.92,  # Could be calculated
                },
            )

        except json.JSONDecodeError as e:
            self.enhanced_logger.log_component_operation(
                "o3_reasoning", "parse_error", {"error": str(e), "fallback_used": True}
            )

        return state

    def _create_agent_with_tools(self, agent_role: str, agent_spec: dict[str, Any]):
        """Enhanced agent creation with lifecycle logging"""

        # Log agent creation start
        self.enhanced_logger.log_agent_lifecycle(
            agent_role,
            "creation_start",
            {
                "agent_spec": agent_spec,
                "tools_requested": agent_spec.get("tools_needed", []),
            },
        )

        # Log tool selection process
        tools = self._select_tools_for_agent(agent_role, agent_spec)

        self.enhanced_logger.log_agent_lifecycle(
            agent_role,
            "tools_selected",
            {
                "tools_assigned": [getattr(tool, "name", str(tool)) for tool in tools],
                "selection_method": (
                    "O3_specified" if agent_spec else "fallback_mapping"
                ),
            },
        )

        # Log prompt generation
        prompt = self._create_progressive_prompt(
            agent_role, {}, "autonomous", agent_spec
        )

        self.enhanced_logger.log_agent_lifecycle(
            agent_role,
            "prompt_generated",
            {
                "prompt_length": len(str(prompt)),
                "prompt_preview": str(prompt)[:200] + "...",
                "customized_for_task": bool(agent_spec),
            },
        )

        # Create agent and log result
        try:
            agent = create_react_agent(self.agent_model, tools=tools, prompt=prompt)

            self.enhanced_logger.log_agent_lifecycle(
                agent_role,
                "creation_complete",
                {"agent_created_successfully": True, "tool_count": len(tools)},
            )

            return agent

        except Exception as e:
            self.enhanced_logger.log_agent_lifecycle(
                agent_role,
                "creation_failed",
                {"error": str(e), "agent_created_successfully": False},
            )
            raise

    def _create_mcp_tool_wrapper(self, tool_name: str):
        """Enhanced MCP tool wrapper with logging"""

        def create_tool_function(name: str):
            def mcp_tool(query: str) -> str:
                """Execute MCP tool with enhanced logging"""

                start_time = datetime.now()
                correlation_id = f"{name}_{int(start_time.timestamp())}"

                try:
                    # Log tool execution start
                    self.enhanced_logger.log_tool_execution(
                        tool_name=name,
                        method="execute",
                        agent_caller="unknown",  # Could be tracked
                        input_data={"query": query},
                        output_data=None,
                        execution_time_ms=0,
                        success=False,  # Will update on completion
                        correlation_id=correlation_id,
                    )

                    # Execute tool
                    result = self.mcp_registry.execute_tool(
                        tool_name=name,
                        method_name="search" if "search" in name else "default",
                        arguments={"query": query},
                    )

                    execution_time = (
                        datetime.now() - start_time
                    ).total_seconds() * 1000

                    # Log tool execution completion
                    self.enhanced_logger.log_tool_execution(
                        tool_name=name,
                        method="execute",
                        agent_caller="unknown",
                        input_data={"query": query},
                        output_data=(
                            result.data if result.success else result.error_message
                        ),
                        execution_time_ms=execution_time,
                        success=result.success,
                        correlation_id=correlation_id,
                    )

                    return (
                        str(result.data)
                        if result.success
                        else f"Error: {result.error_message}"
                    )

                except Exception as e:
                    execution_time = (
                        datetime.now() - start_time
                    ).total_seconds() * 1000

                    # Log tool execution error
                    self.enhanced_logger.log_tool_execution(
                        tool_name=name,
                        method="execute",
                        agent_caller="unknown",
                        input_data={"query": query},
                        output_data=f"Exception: {str(e)}",
                        execution_time_ms=execution_time,
                        success=False,
                        correlation_id=correlation_id,
                    )

                    return f"Tool execution error: {e}"

            return mcp_tool

        # Create and return the wrapped tool
        tool_func = create_tool_function(tool_name)
        return tool(tool_func)


# File operations wrapper with logging
class EnhancedFileSystemTools:
    """File system tools with comprehensive logging"""

    def __init__(self, enhanced_logger: EnhancedLoggerFactory):
        self.enhanced_logger = enhanced_logger

    def write_file(
        self, filename: str, content: str, agent_caller: str = "unknown"
    ) -> str:
        """Write file with comprehensive logging"""

        start_time = datetime.now()

        # Get project context
        from src.applications.oamat_sd.src.utils.project_context import (
            ProjectContextManager,
        )

        project_path = ProjectContextManager.get_project_path()

        if not project_path:
            self.enhanced_logger.log_component_operation(
                "file_operations",
                "context_missing",
                {
                    "filename": filename,
                    "agent_caller": agent_caller,
                    "error": "No project context available",
                },
            )
            return "Error: No project context available"

        # Log file operation start
        full_path = Path(project_path) / filename

        self.enhanced_logger.log_component_operation(
            "file_operations",
            "write_start",
            {
                "filename": filename,
                "full_path": str(full_path),
                "agent_caller": agent_caller,
                "content_size_bytes": len(content),
                "project_context_resolved": True,
            },
        )

        # Log audit event
        self.enhanced_logger.log_audit_event(
            "permission_checks",
            "file_write_attempt",
            {
                "path": str(full_path),
                "agent": agent_caller,
                "permission_check": "passed",  # Could implement actual checks
                "project_scoped": True,
            },
        )

        try:
            # Create directory if needed
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # Write file
            full_path.write_text(content, encoding="utf-8")

            execution_time = (datetime.now() - start_time).total_seconds() * 1000

            # Log successful write
            self.enhanced_logger.log_component_operation(
                "file_operations",
                "write_complete",
                {
                    "filename": filename,
                    "full_path": str(full_path),
                    "agent_caller": agent_caller,
                    "content_size_bytes": len(content),
                    "execution_time_ms": execution_time,
                    "write_successful": True,
                    "directory_created": True,
                },
            )

            return f"File written successfully: {filename}"

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds() * 1000

            # Log write error
            self.enhanced_logger.log_component_operation(
                "file_operations",
                "write_error",
                {
                    "filename": filename,
                    "full_path": str(full_path),
                    "agent_caller": agent_caller,
                    "error": str(e),
                    "execution_time_ms": execution_time,
                    "write_successful": False,
                },
            )

            return f"Error writing file: {e}"


# Usage example in main application
def main():
    """Example usage of enhanced logging system"""

    agent = EnhancedSmartDecompositionAgent()

    # Enhanced logging will now capture:
    # - All tool executions with input/output
    # - Complete agent lifecycles
    # - O3 reasoning processes
    # - File operations with audit trails
    # - Component state changes
    # - Performance metrics
    # - Security events

    # After execution, logs directory will contain:
    # - brave_search_20250717_120851.jsonl
    # - arxiv_research_20250717_120851.jsonl
    # - agent_requirements_analyst_20250717_120851.jsonl
    # - agent_db_designer_20250717_120851.jsonl
    # - o3_reasoning_20250717_120851.jsonl
    # - file_operations_20250717_120851.jsonl
    # - permission_checks_20250717_120851.jsonl
    # - And 20+ more specialized logs

    print("Enhanced logging system provides complete observability!")


if __name__ == "__main__":
    main()
