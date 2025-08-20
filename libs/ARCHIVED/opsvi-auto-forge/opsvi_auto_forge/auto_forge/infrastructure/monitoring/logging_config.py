"""Structured logging configuration for production."""

import logging
import sys
import time
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Optional

import structlog
from structlog.contextvars import merge_contextvars
from structlog.processors import JSONRenderer, TimeStamper
from structlog.stdlib import LoggerFactory

# Context variables for correlation tracking
request_id: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
user_id: ContextVar[Optional[str]] = ContextVar("user_id", default=None)
session_id: ContextVar[Optional[str]] = ContextVar("session_id", default=None)
correlation_id: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)
pipeline_phase: ContextVar[Optional[str]] = ContextVar("pipeline_phase", default=None)
task_id: ContextVar[Optional[str]] = ContextVar("task_id", default=None)
agent_type: ContextVar[Optional[str]] = ContextVar("agent_type", default=None)


def generate_correlation_id() -> str:
    """Generate a unique correlation ID."""
    return str(uuid.uuid4())


def get_correlation_id() -> Optional[str]:
    """Get the current correlation ID."""
    return correlation_id.get()


def set_correlation_id(corr_id: str) -> None:
    """Set the current correlation ID."""
    correlation_id.set(corr_id)


def set_pipeline_context(
    phase: str, task_id_param: str = None, agent: str = None
) -> None:
    """Set pipeline context for logging."""
    pipeline_phase.set(phase)
    if task_id_param:
        task_id.set(task_id_param)
    if agent:
        agent_type.set(agent)


# Custom processors for enhanced logging
class CorrelationProcessor:
    """Add correlation IDs to log entries."""

    def __call__(self, logger, method_name, event_dict):
        # Add correlation ID if available
        if correlation_id.get():
            event_dict["correlation_id"] = correlation_id.get()

        # Add pipeline context if available
        if pipeline_phase.get():
            event_dict["pipeline_phase"] = pipeline_phase.get()
        if task_id.get():
            event_dict["task_id"] = task_id.get()
        if agent_type.get():
            event_dict["agent_type"] = agent_type.get()

        return event_dict


class PerformanceProcessor:
    """Add performance metrics to log entries."""

    def __call__(self, logger, method_name, event_dict):
        # Add timestamp in ISO format
        event_dict["timestamp"] = datetime.now(timezone.utc).isoformat()

        # Add performance context if available
        if "duration_ms" not in event_dict and "start_time" in event_dict:
            duration = (time.time() - event_dict["start_time"]) * 1000
            event_dict["duration_ms"] = round(duration, 2)
            del event_dict["start_time"]

        return event_dict


class AuditProcessor:
    """Add audit information to log entries."""

    def __call__(self, logger, method_name, event_dict):
        # Add user context if available
        if user_id.get():
            event_dict["user_id"] = user_id.get()
        if session_id.get():
            event_dict["session_id"] = session_id.get()

        return event_dict


class SecurityProcessor:
    """Add security context to log entries."""

    def __call__(self, logger, method_name, event_dict):
        # Add security context
        event_dict["security_level"] = "standard"

        # Mask sensitive data
        sensitive_keys = ["password", "token", "secret", "key"]
        for key in sensitive_keys:
            if key in event_dict:
                event_dict[key] = "***MASKED***"

        return event_dict


class DebugProcessor:
    """Add debug information for development."""

    def __call__(self, logger, method_name, event_dict):
        # Add debug context
        event_dict["debug_info"] = {
            "logger_name": logger.name,
            "method_name": method_name,
            "log_level": method_name.upper(),
        }

        # Add stack trace for errors
        if method_name == "error" and "exc_info" in event_dict:
            import traceback

            event_dict["stack_trace"] = traceback.format_exc()

        return event_dict


def configure_logging(
    log_level: str = "DEBUG",  # Changed default to DEBUG for better visibility
    log_format: str = "json",
    enable_console: bool = True,
    enable_file: bool = True,
    log_file_path: str = "data/logs/app.log",
    enable_audit_log: bool = True,
    audit_log_path: str = "data/logs/audit.log",
    enable_security_log: bool = True,
    security_log_path: str = "data/logs/security.log",
    enable_debug_log: bool = True,  # New debug log
    debug_log_path: str = "data/logs/debug.log",
):
    """Configure structured logging for production with enhanced debug capabilities."""

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )

    # Configure structlog with enhanced processors
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        merge_contextvars,
        CorrelationProcessor(),
        AuditProcessor(),
        PerformanceProcessor(),
        SecurityProcessor(),
        DebugProcessor(),  # Add debug processor
    ]

    if log_format.lower() == "json":
        processors.append(JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure file handlers
    if enable_file:
        # Main application log
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_formatter = logging.Formatter("%(message)s")
        file_handler.setFormatter(file_formatter)

        # Get the root logger and add the file handler
        root_logger = logging.getLogger()
        root_logger.addHandler(file_handler)

        # Debug log (new)
        if enable_debug_log:
            debug_handler = logging.FileHandler(debug_log_path)
            debug_handler.setLevel(logging.DEBUG)
            debug_handler.setFormatter(file_formatter)

            debug_logger = logging.getLogger("debug")
            debug_logger.addHandler(debug_handler)
            debug_logger.setLevel(logging.DEBUG)
            debug_logger.propagate = False

        # Audit log
        if enable_audit_log:
            audit_handler = logging.FileHandler(audit_log_path)
            audit_handler.setLevel(logging.INFO)
            audit_handler.setFormatter(file_formatter)

            audit_logger = logging.getLogger("audit")
            audit_logger.addHandler(audit_handler)
            audit_logger.setLevel(logging.INFO)
            audit_logger.propagate = False

        # Security log
        if enable_security_log:
            security_handler = logging.FileHandler(security_log_path)
            security_handler.setLevel(logging.WARNING)
            security_handler.setFormatter(file_formatter)

            security_logger = logging.getLogger("security")
            security_logger.addHandler(security_handler)
            security_logger.setLevel(logging.WARNING)
            security_logger.propagate = False


def get_logger(name: str = None) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


def log_request_start(
    request_id: str, method: str, url: str, user_id: str = None, **kwargs
):
    """Log the start of an HTTP request."""
    logger = get_logger("http.request")
    logger.info(
        "HTTP request started",
        request_id=request_id,
        method=method,
        url=url,
        user_id=user_id,
        start_time=time.time(),
        **kwargs,
    )


def log_request_end(
    request_id: str,
    method: str,
    url: str,
    status_code: int,
    duration_ms: float,
    **kwargs,
):
    """Log the end of an HTTP request."""
    logger = get_logger("http.request")
    logger.info(
        "HTTP request completed",
        request_id=request_id,
        method=method,
        url=url,
        status_code=status_code,
        duration_ms=duration_ms,
        **kwargs,
    )


def log_pipeline_phase_start(phase: str, run_id: str, project_id: str, **kwargs):
    """Log the start of a pipeline phase."""
    logger = get_logger("pipeline.phase")
    set_pipeline_context(phase)
    logger.info(
        f"Pipeline phase {phase} started",
        phase=phase,
        run_id=run_id,
        project_id=project_id,
        start_time=time.time(),
        **kwargs,
    )


def log_pipeline_phase_end(
    phase: str, run_id: str, project_id: str, success: bool, **kwargs
):
    """Log the end of a pipeline phase."""
    logger = get_logger("pipeline.phase")
    set_pipeline_context(phase)
    logger.info(
        f"Pipeline phase {phase} {'completed' if success else 'failed'}",
        phase=phase,
        run_id=run_id,
        project_id=project_id,
        success=success,
        **kwargs,
    )


def log_task_start(task_id: str, task_type: str, agent_type: str = None, **kwargs):
    """Log the start of a task execution."""
    logger = get_logger("task.execution")
    set_pipeline_context("task", task_id, agent_type)
    logger.info(
        f"Task {task_type} started",
        task_id=task_id,
        task_type=task_type,
        agent_type=agent_type,
        start_time=time.time(),
        **kwargs,
    )


def log_task_end(
    task_id: str, task_type: str, success: bool, agent_type: str = None, **kwargs
):
    """Log the end of a task execution."""
    logger = get_logger("task.execution")
    set_pipeline_context("task", task_id, agent_type)
    logger.info(
        f"Task {task_type} {'completed' if success else 'failed'}",
        task_id=task_id,
        task_type=task_type,
        agent_type=agent_type,
        success=success,
        **kwargs,
    )


def log_agent_decision(
    agent_type: str, decision: str, confidence: float = None, **kwargs
):
    """Log an agent decision."""
    logger = get_logger("agent.decision")
    set_pipeline_context("agent", agent=agent_type)
    logger.info(
        f"Agent {agent_type} made decision: {decision}",
        agent_type=agent_type,
        decision=decision,
        confidence=confidence,
        **kwargs,
    )


def log_debug(message: str, **kwargs):
    """Log a debug message with full context."""
    logger = get_logger("debug")
    logger.debug(message, **kwargs)


def log_error(message: str, error: Exception = None, **kwargs):
    """Log an error with full context."""
    logger = get_logger("error")
    logger.error(
        message,
        error=str(error) if error else None,
        exc_info=error is not None,
        **kwargs,
    )
