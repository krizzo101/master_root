"""
Logger Factory for Smart Decomposition Architecture

Creates specialized loggers with structured JSON output and intelligent routing.
"""

from datetime import datetime
import json
import logging
import logging.handlers
from typing import Any, Dict, List, Optional

import structlog
from structlog.stdlib import LoggerFactory as StructlogLoggerFactory

from src.applications.oamat_sd.src.sd_logging.correlation import (
    get_correlation_context,
    get_correlation_id,
)
from src.applications.oamat_sd.src.sd_logging.log_config import (
    LogConfig,
    LogFileConfig,
)


class SmartDecompositionProcessor:
    """Custom structlog processor for Smart Decomposition architecture"""

    def __init__(self, config: LogConfig):
        self.config = config

    def __call__(self, logger, method_name, event_dict):
        """Process log events with correlation context and intelligent routing"""

        # Add correlation context
        correlation_context = get_correlation_context()
        if correlation_context:
            event_dict.update(correlation_context.to_dict())
        else:
            event_dict["correlation_id"] = get_correlation_id()

        # Add standard fields
        event_dict["timestamp"] = datetime.now().isoformat()
        event_dict["level"] = method_name.upper()
        event_dict["logger_name"] = logger.name

        # Truncate prompts for console output if needed
        if "prompt" in event_dict and "console" in logger.name:
            prompt = event_dict["prompt"]
            if len(prompt) > self.config.truncate_prompts_console:
                event_dict["prompt"] = (
                    prompt[: self.config.truncate_prompts_console] + "..."
                )
                event_dict["prompt_truncated"] = True

        return event_dict


class LoggerFactory:
    """Factory for creating specialized loggers with intelligent decomposition"""

    def __init__(self, config: LogConfig, setup_file_handlers: bool = True):
        self.config = config
        self._loggers: Dict[str, structlog.stdlib.BoundLogger] = {}
        self._file_handlers_setup = False
        self._setup_structlog()
        if setup_file_handlers:
            self._setup_file_handlers()

    def _setup_structlog(self):
        """Configure structlog for structured JSON logging"""
        structlog.configure(
            processors=[
                SmartDecompositionProcessor(self.config),
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer(),
            ],
            context_class=dict,
            logger_factory=StructlogLoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

    def _setup_file_handlers(self):
        """Setup rotating file handlers for each log category"""
        if self._file_handlers_setup:
            return  # Already set up

        # Ensure log directory exists (moved from LogConfig to prevent early creation)
        self.config.log_dir.mkdir(parents=True, exist_ok=True)

        for category, file_config in self.config.get_log_files().items():
            self._create_file_handler(file_config)

        self._file_handlers_setup = True

    def _create_file_handler(self, file_config: LogFileConfig):
        """Create a rotating file handler for a specific log category"""
        log_file_path = self.config.log_dir / file_config.filename

        # Create rotating file handler
        handler = logging.handlers.RotatingFileHandler(
            log_file_path,
            maxBytes=file_config.max_size_mb * 1024 * 1024,
            backupCount=file_config.backup_count,
        )

        # Set level and formatter
        handler.setLevel(getattr(logging, file_config.level.value))

        if file_config.format_type == "json":
            # JSON formatter for structured logs
            formatter = logging.Formatter("%(message)s")
        else:
            # Text formatter for human-readable logs
            formatter = logging.Formatter(self.config.get_file_format())

        handler.setFormatter(formatter)

        # Create logger for this category
        logger = logging.getLogger(f"oamat.smart.{file_config.category.value}")
        logger.addHandler(handler)
        logger.setLevel(getattr(logging, file_config.level.value))

    def get_console_logger(self) -> structlog.stdlib.BoundLogger:
        """Get logger for user-friendly console output"""
        if "console" not in self._loggers:
            logger = structlog.get_logger("oamat.smart.console")
            self._loggers["console"] = logger
        return self._loggers["console"]

    def get_debug_logger(self) -> structlog.stdlib.BoundLogger:
        """Get comprehensive debug logger"""
        if "debug" not in self._loggers:
            logger = structlog.get_logger("oamat.smart.debug")
            self._loggers["debug"] = logger
        return self._loggers["debug"]

    def get_api_logger(self) -> structlog.stdlib.BoundLogger:
        """Get logger for API calls and responses"""
        if "api" not in self._loggers:
            logger = structlog.get_logger("oamat.smart.api")
            self._loggers["api"] = logger
        return self._loggers["api"]

    def get_workflow_logger(self) -> structlog.stdlib.BoundLogger:
        """Get logger for DAG execution and agent coordination"""
        if "workflow" not in self._loggers:
            logger = structlog.get_logger("oamat.smart.workflow")
            self._loggers["workflow"] = logger
        return self._loggers["workflow"]

    def get_performance_logger(self) -> structlog.stdlib.BoundLogger:
        """Get logger for timing and resource metrics"""
        if "performance" not in self._loggers:
            logger = structlog.get_logger("oamat.smart.performance")
            self._loggers["performance"] = logger
        return self._loggers["performance"]

    def get_complexity_logger(self) -> structlog.stdlib.BoundLogger:
        """Get logger for complexity analysis and decision-making"""
        if "complexity" not in self._loggers:
            logger = structlog.get_logger("oamat.smart.complexity")
            self._loggers["complexity"] = logger
        return self._loggers["complexity"]

    def get_error_logger(self) -> structlog.stdlib.BoundLogger:
        """Get logger for errors, exceptions, and recovery"""
        if "error" not in self._loggers:
            logger = structlog.get_logger("oamat.smart.error")
            self._loggers["error"] = logger
        return self._loggers["error"]

    def get_audit_logger(self, audit_type: str) -> structlog.stdlib.BoundLogger:
        """Get audit-specific logger"""
        logger_key = f"audit_{audit_type}"
        if logger_key not in self._loggers:
            logger = structlog.get_logger(f"oamat.audit.{audit_type}")

            # Create file handler for this audit type
            log_file_path = self.config.log_dir / self.config.get_audit_log_filename(
                audit_type
            )
            handler = logging.FileHandler(log_file_path)
            handler.setFormatter(logging.Formatter("%(message)s"))

            # Get the underlying stdlib logger and add handler
            stdlib_logger = logging.getLogger(f"oamat.audit.{audit_type}")
            stdlib_logger.addHandler(handler)
            stdlib_logger.setLevel(logging.INFO)

            self._loggers[logger_key] = logger
        return self._loggers[logger_key]

    def log_api_call(
        self,
        method: str,
        url: str,
        request_data: Optional[Dict[str, Any]] = None,
        response_data: Optional[Dict[str, Any]] = None,
        status_code: Optional[int] = None,
        duration_ms: Optional[float] = None,
        error: Optional[str] = None,
    ):
        """Log an API call with comprehensive details"""
        api_logger = self.get_api_logger()

        log_data = {
            "method": method,
            "url": url,
            "status_code": status_code,
            "duration_ms": duration_ms,
        }

        if request_data:
            log_data["request"] = request_data

        if response_data:
            log_data["response"] = response_data

        if error:
            log_data["error"] = error
            api_logger.error("API call failed", **log_data)
        else:
            api_logger.info("API call completed", **log_data)

    def log_agent_interaction(
        self,
        agent_id: str,
        action: str,
        input_data: Optional[Dict[str, Any]] = None,
        output_data: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Log agent interactions and handoffs"""
        workflow_logger = self.get_workflow_logger()

        log_data = {
            "agent_id": agent_id,
            "action": action,
            "duration_ms": duration_ms,
        }

        if input_data:
            log_data["input"] = input_data

        if output_data:
            log_data["output"] = output_data

        if metadata:
            log_data["metadata"] = metadata

        workflow_logger.info("Agent interaction", **log_data)

    def log_complexity_analysis(
        self,
        user_request: str,
        factors: Dict[str, float],
        overall_score: float,
        decision: str,
        reasoning: str,
        user_override: bool = False,
    ):
        """Log complexity analysis decisions"""
        complexity_logger = self.get_complexity_logger()

        complexity_logger.info(
            "Complexity analysis completed",
            user_request=user_request,
            factors=factors,
            overall_score=overall_score,
            decision=decision,
            reasoning=reasoning,
            user_override=user_override,
        )

    def log_performance_metrics(
        self,
        operation: str,
        duration_ms: float,
        resource_usage: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Log performance and resource usage metrics"""
        performance_logger = self.get_performance_logger()

        log_data = {
            "operation": operation,
            "duration_ms": duration_ms,
        }

        if resource_usage:
            log_data["resource_usage"] = resource_usage

        if metadata:
            log_data["metadata"] = metadata

        performance_logger.info("Performance metrics", **log_data)

    def log_workflow_execution(
        self,
        workflow_type: str,  # "linear" or "dag"
        agents: list,
        dependencies: Optional[Dict[str, list]] = None,
        execution_plan: Optional[Dict[str, Any]] = None,
        results: Optional[Dict[str, Any]] = None,
        total_duration_ms: Optional[float] = None,
    ):
        """Log complete workflow execution"""
        workflow_logger = self.get_workflow_logger()

        log_data = {
            "workflow_type": workflow_type,
            "agents": agents,
            "total_duration_ms": total_duration_ms,
        }

        if dependencies:
            log_data["dependencies"] = dependencies

        if execution_plan:
            log_data["execution_plan"] = execution_plan

        if results:
            log_data["results"] = results

        workflow_logger.info("Workflow execution completed", **log_data)

    # ===== ENHANCED LOGGING METHODS =====
    # Tool-Specific Logging Methods

    def get_tool_logger(self, tool_name: str) -> structlog.stdlib.BoundLogger:
        """Get tool-specific logger for MCP tools"""
        logger_key = f"tool_{tool_name}"
        if logger_key not in self._loggers:
            logger = structlog.get_logger(f"oamat.tool.{tool_name}")

            # Create file handler for this tool
            log_file_path = self.config.log_dir / self.config.get_tool_log_filename(
                tool_name
            )
            handler = logging.FileHandler(log_file_path)
            handler.setFormatter(logging.Formatter("%(message)s"))

            # Get the underlying stdlib logger and add handler
            stdlib_logger = logging.getLogger(f"oamat.tool.{tool_name}")
            stdlib_logger.addHandler(handler)
            stdlib_logger.setLevel(logging.INFO)

            self._loggers[logger_key] = logger
        return self._loggers[logger_key]

    def log_tool_execution(
        self,
        tool_name: str,
        method: str,
        agent_caller: str,
        input_data: Any,
        output_data: Any = None,
        execution_time_ms: float = 0,
        success: bool = False,
        correlation_id: str = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Log comprehensive tool execution details"""
        tool_logger = self.get_tool_logger(tool_name)

        log_data = {
            "tool_name": tool_name,
            "method": method,
            "agent_caller": agent_caller,
            "execution_time_ms": execution_time_ms,
            "success": success,
            "correlation_id": correlation_id or get_correlation_id(),
        }

        # Safely handle input/output data
        if input_data:
            log_data["input"] = self._truncate_content(input_data, 10000)
        if output_data:
            log_data["output"] = self._truncate_content(output_data, 10000)
        if metadata:
            log_data.update(metadata)

        if success:
            tool_logger.info("Tool execution completed", **log_data)
        else:
            tool_logger.error("Tool execution failed", **log_data)

    # Agent Lifecycle Logging Methods

    def get_agent_logger(self, agent_role: str) -> structlog.stdlib.BoundLogger:
        """Get agent-specific logger"""
        logger_key = f"agent_{agent_role}"
        if logger_key not in self._loggers:
            logger = structlog.get_logger(f"oamat.agent.{agent_role}")

            # Create file handler for this agent
            log_file_path = self.config.log_dir / self.config.get_agent_log_filename(
                agent_role
            )
            handler = logging.FileHandler(log_file_path)
            handler.setFormatter(logging.Formatter("%(message)s"))

            # Get the underlying stdlib logger and add handler
            stdlib_logger = logging.getLogger(f"oamat.agent.{agent_role}")
            stdlib_logger.addHandler(handler)
            stdlib_logger.setLevel(logging.INFO)

            self._loggers[logger_key] = logger
        return self._loggers[logger_key]

    def log_agent_lifecycle(
        self,
        agent_role: str,
        stage: str,
        data: Dict[str, Any],
        execution_time_ms: Optional[float] = None,
    ):
        """Log agent lifecycle events (creation, execution, completion)"""
        agent_logger = self.get_agent_logger(agent_role)

        log_data = {
            "agent_role": agent_role,
            "lifecycle_stage": stage,
            "execution_time_ms": execution_time_ms,
            **data,
        }

        agent_logger.info(f"Agent lifecycle: {stage}", **log_data)

    # Component Investigation Logging Methods

    def get_component_logger(self, component: str) -> structlog.stdlib.BoundLogger:
        """Get component-specific logger"""
        logger_key = f"component_{component}"
        if logger_key not in self._loggers:
            logger = structlog.get_logger(f"oamat.component.{component}")

            # Create file handler for this component
            log_file_path = (
                self.config.log_dir / self.config.get_component_log_filename(component)
            )
            handler = logging.FileHandler(log_file_path)
            handler.setFormatter(logging.Formatter("%(message)s"))

            # Get the underlying stdlib logger and add handler
            stdlib_logger = logging.getLogger(f"oamat.component.{component}")
            stdlib_logger.addHandler(handler)
            stdlib_logger.setLevel(logging.INFO)

            self._loggers[logger_key] = logger
        return self._loggers[logger_key]

    def log_component_operation(
        self,
        component: str,
        operation: str,
        data: Dict[str, Any],
        execution_time_ms: Optional[float] = None,
        success: bool = True,
    ):
        """Log component operations with context"""
        component_logger = self.get_component_logger(component)

        log_data = {
            "component": component,
            "operation": operation,
            "execution_time_ms": execution_time_ms,
            "success": success,
            **data,
        }

        if success:
            component_logger.info(f"Component operation: {operation}", **log_data)
        else:
            component_logger.error(
                f"Component operation failed: {operation}", **log_data
            )

    # Audit & Security Logging Methods

    def get_audit_logger(self, audit_type: str) -> structlog.stdlib.BoundLogger:
        """Get audit-specific logger"""
        logger_key = f"audit_{audit_type}"
        if logger_key not in self._loggers:
            logger = structlog.get_logger(f"oamat.audit.{audit_type}")
            self._loggers[logger_key] = logger
        return self._loggers[logger_key]

    def log_audit_event(
        self,
        audit_type: str,
        event: str,
        data: Dict[str, Any],
        severity: str = "info",
    ):
        """Log audit and security events"""
        audit_logger = self.get_audit_logger(audit_type)

        log_data = {
            "audit_type": audit_type,
            "event": event,
            "severity": severity,
            **data,
        }

        if severity == "error":
            audit_logger.error(f"Audit event: {event}", **log_data)
        elif severity == "warning":
            audit_logger.warning(f"Audit event: {event}", **log_data)
        else:
            audit_logger.info(f"Audit event: {event}", **log_data)

    # Performance & Monitoring Logging Methods

    def log_timing_breakdown(
        self,
        operation: str,
        total_time_ms: float,
        breakdown: Dict[str, float],
        bottlenecks: Optional[List[str]] = None,
        optimization_suggestions: Optional[List[str]] = None,
    ):
        """Log detailed timing breakdown for performance analysis"""
        performance_logger = self.get_performance_logger()

        log_data = {
            "operation": operation,
            "total_time_ms": total_time_ms,
            "breakdown": breakdown,
        }

        if bottlenecks:
            log_data["bottlenecks"] = bottlenecks
        if optimization_suggestions:
            log_data["optimization_suggestions"] = optimization_suggestions

        performance_logger.info("Timing breakdown analysis", **log_data)

    def log_success_metrics(
        self,
        operation: str,
        success_count: int,
        total_count: int,
        success_rate: float,
        quality_scores: Optional[Dict[str, float]] = None,
    ):
        """Log success rates and quality metrics"""
        performance_logger = self.get_performance_logger()

        log_data = {
            "operation": operation,
            "success_count": success_count,
            "total_count": total_count,
            "success_rate": success_rate,
        }

        if quality_scores:
            log_data["quality_scores"] = quality_scores

        performance_logger.info("Success metrics", **log_data)

    def log_memory_usage(
        self,
        operation: str,
        memory_peak_mb: float,
        memory_average_mb: float,
        memory_limit_mb: Optional[float] = None,
    ):
        """Log memory usage metrics"""
        performance_logger = self.get_performance_logger()

        log_data = {
            "operation": operation,
            "memory_peak_mb": memory_peak_mb,
            "memory_average_mb": memory_average_mb,
        }

        if memory_limit_mb:
            log_data["memory_limit_mb"] = memory_limit_mb
            log_data["memory_utilization_percent"] = (
                memory_peak_mb / memory_limit_mb
            ) * 100

        performance_logger.info("Memory usage metrics", **log_data)

    def log_request_flow(
        self,
        request_id: str,
        flow_stages: List[Dict[str, Any]],
        total_duration_ms: float,
    ):
        """Log end-to-end request processing flow"""
        performance_logger = self.get_performance_logger()

        log_data = {
            "request_id": request_id,
            "flow_stages": flow_stages,
            "total_duration_ms": total_duration_ms,
            "stage_count": len(flow_stages),
        }

        performance_logger.info("Request flow completed", **log_data)

    # Enhanced Error Logging

    def log_error_with_context(
        self,
        error: Exception,
        operation: str,
        context: Dict[str, Any],
        recovery_action: Optional[str] = None,
    ):
        """Log errors with comprehensive context"""
        error_logger = self.get_error_logger()

        log_data = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "operation": operation,
            "context": context,
        }

        if recovery_action:
            log_data["recovery_action"] = recovery_action

        error_logger.error("Operation failed with context", **log_data)

    # Utility Methods

    def _truncate_content(self, content: Any, max_size: int) -> Any:
        """Truncate content if too large for logging"""
        if isinstance(content, str) and len(content) > max_size:
            return content[:max_size] + "... [TRUNCATED]"
        elif isinstance(content, dict):
            content_str = json.dumps(content, indent=2)
            if len(content_str) > max_size:
                return {
                    "truncated": True,
                    "size": len(content_str),
                    "preview": content_str[:max_size],
                }
        return content

    def create_master_log(self, log_directory: str = None) -> str:
        """Create a centralized master log that captures ALL log entries"""
        import logging
        from pathlib import Path

        if log_directory:
            log_dir = Path(log_directory)
        else:
            log_dir = self.config.log_dir

        log_dir.mkdir(parents=True, exist_ok=True)

        master_log_path = log_dir / f"MASTER_LOG_{self.config.session_id}.log"

        # Create master log handler
        master_handler = logging.FileHandler(master_log_path)
        master_handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)8s] %(name)-30s: %(message)s")
        )
        master_handler.setLevel(logging.DEBUG)

        # Add to ALL relevant loggers
        patterns = [
            "oamat",
            "smart",
            "decomposition",
            "src.applications.oamat_sd",
            "agent",
            "o3",
            "mcp",
            "tool",
            "reasoning",
            "execution",
            "synthesis",
            "validation",
            "component",
            "audit",
            "langgraph",
        ]

        loggers_updated = 0
        for pattern in patterns:
            for logger_name in list(logging.Logger.manager.loggerDict.keys()):
                if pattern in logger_name.lower():
                    logger = logging.getLogger(logger_name)
                    # Check if handler already exists to avoid duplicates
                    if not any(
                        isinstance(h, logging.FileHandler)
                        and str(h.baseFilename).endswith(master_log_path.name)
                        for h in logger.handlers
                    ):
                        logger.addHandler(master_handler)
                        logger.setLevel(logging.DEBUG)
                        loggers_updated += 1

        # Also add to root logger
        root_logger = logging.getLogger()
        if not any(
            isinstance(h, logging.FileHandler)
            and str(h.baseFilename).endswith(master_log_path.name)
            for h in root_logger.handlers
        ):
            root_logger.addHandler(master_handler)

        self.get_console_logger().info(
            f"📋 Master log created: {master_log_path.name} (monitoring {loggers_updated} loggers)"
        )

        return str(master_log_path)

    def reconfigure_for_project(self, project_path: str):
        """Reconfigure logging to use project-specific log directory"""
        from pathlib import Path

        # Create project logs directory
        project_logs_dir = Path(project_path) / "logs"
        project_logs_dir.mkdir(exist_ok=True)

        # Update config to use project logs directory
        self.config.log_dir = project_logs_dir

        # Clear existing loggers to force recreation with new paths
        self._loggers.clear()

        # Remove existing handlers from ALL loggers that might be logging to files
        import logging

        # Clear all existing file handlers from ALL loggers
        for name in list(logging.Logger.manager.loggerDict.keys()):
            # Skip basic loggers but catch all our application loggers
            if any(
                pattern in name.lower()
                for pattern in [
                    "oamat",
                    "smart",
                    "decomposition",
                    "src.applications.oamat_sd",  # Module-based loggers
                    "agent",
                    "o3",
                    "mcp",
                    "tool",
                    "reasoning",
                    "execution",
                    "synthesis",
                    "validation",
                ]
            ):
                logger = logging.getLogger(name)
                for handler in logger.handlers[:]:
                    if isinstance(
                        handler,
                        (logging.FileHandler, logging.handlers.RotatingFileHandler),
                    ):
                        handler.close()
                        logger.removeHandler(handler)
                # Also clear any parent propagation to avoid duplicate logs
                logger.propagate = False

        # Flush any pending logs before switching
        logging.shutdown()

        # Set up a global root handler to catch any missed logs
        root_logger = logging.getLogger()

        # Remove any existing root handlers to prevent duplication
        for handler in root_logger.handlers[:]:
            if isinstance(
                handler, (logging.FileHandler, logging.handlers.RotatingFileHandler)
            ):
                handler.close()
                root_logger.removeHandler(handler)

        # Add a project-specific root handler for any uncaught logs
        root_file_handler = logging.FileHandler(project_logs_dir / "uncaught.log")
        root_file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        root_file_handler.setLevel(logging.INFO)
        root_logger.addHandler(root_file_handler)

        # 🔥 NEW: Create centralized master log that captures EVERYTHING
        master_log_handler = logging.FileHandler(
            project_logs_dir / f"MASTER_LOG_{self.config.session_id}.log"
        )
        master_log_handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)8s] %(name)-30s: %(message)s")
        )
        master_log_handler.setLevel(logging.DEBUG)  # Capture everything

        # Add master handler to ALL oamat loggers
        for pattern in [
            "oamat",
            "smart",
            "decomposition",
            "src.applications.oamat_sd",
            "agent",
            "o3",
            "mcp",
            "tool",
            "reasoning",
            "execution",
            "synthesis",
            "validation",
            "component",
            "audit",
        ]:
            for logger_name in list(logging.Logger.manager.loggerDict.keys()):
                if pattern in logger_name.lower():
                    logger = logging.getLogger(logger_name)
                    logger.addHandler(master_log_handler)
                    logger.setLevel(logging.DEBUG)

        # Also add to root logger for comprehensive coverage
        root_logger.addHandler(master_log_handler)

        # Reset the file handlers setup flag and recreate with new log directory
        self._file_handlers_setup = False
        self._setup_file_handlers()

        self.get_console_logger().info(
            f"📁 Logging reconfigured for project: {project_logs_dir}"
        )
        self.get_debug_logger().info(
            f"🔄 All logging redirected from global logs to project: {project_logs_dir}"
        )
        self.get_console_logger().info(
            f"📋 Centralized master log created: MASTER_LOG_{self.config.session_id}.log"
        )


# Global logger factory instance
_logger_factory: Optional[LoggerFactory] = None


def get_logger_factory(config: Optional[LogConfig] = None) -> LoggerFactory:
    """Get the global logger factory instance"""
    global _logger_factory

    if _logger_factory is None:
        if config is None:
            from src.applications.oamat_sd.src.sd_logging.log_config import (
                default_config,
            )

            config = default_config
        _logger_factory = LoggerFactory(config)

    return _logger_factory


def reset_logger_factory():
    """Reset the global logger factory (useful for testing)"""
    global _logger_factory
    _logger_factory = None
