"""
Smart Decomposition Project Context Manager

Provides a thread-safe way for tools to access the current project context
when it's not available through LangGraph's state management.

Based on the proven pattern from old OAMAT application.
"""

import logging
import threading
from typing import Optional

# Import enhanced logging system
from src.applications.oamat_sd.src.sd_logging import LogConfig, LoggerFactory

logger = logging.getLogger("SmartDecomposition.ProjectContext")

# Initialize enhanced logging for project context operations
_log_config = LogConfig()
_logger_factory = LoggerFactory(_log_config)


class ProjectContextManager:
    """Global project context manager for Smart Decomposition tools."""

    _lock = threading.Lock()
    _global_context = None  # Single global context instead of thread-specific

    @classmethod
    def set_context(cls, project_name: str, project_path: str):
        """Set the global project context."""
        with cls._lock:
            # Capture previous context for audit trail
            previous_context = (
                cls._global_context.copy() if cls._global_context else None
            )

            # Enhanced logging: Log project context set operation
            _logger_factory.log_component_operation(
                component="project_context",
                operation="set_context",
                data={
                    "project_name": project_name,
                    "project_path": str(project_path),
                    "thread_safety": "global_lock_acquired",
                    "previous_context": previous_context,
                    "context_set_successfully": True,
                },
                success=True,
            )

            cls._global_context = {
                "project_name": project_name,
                "project_path": str(project_path),
            }
            logger.info(f"✅ Project context set: {project_name} at {project_path}")

    @classmethod
    def get_project_path(cls) -> Optional[str]:
        """Get the project path from global context."""
        with cls._lock:
            return (
                cls._global_context.get("project_path") if cls._global_context else None
            )

    @classmethod
    def get_project_name(cls) -> Optional[str]:
        """Get the project name from global context."""
        with cls._lock:
            return (
                cls._global_context.get("project_name") if cls._global_context else None
            )

    @classmethod
    def clear_context(cls):
        """Clear the global project context."""
        with cls._lock:
            # Capture context being cleared for audit trail
            cleared_context = (
                cls._global_context.copy() if cls._global_context else None
            )

            # Enhanced logging: Log project context clear operation
            _logger_factory.log_component_operation(
                component="project_context",
                operation="clear_context",
                data={
                    "thread_safety": "global_lock_acquired",
                    "previous_context": cleared_context,
                    "context_cleared_successfully": True,
                },
                success=True,
            )

            cls._global_context = None
            logger.info("🧹 Project context cleared")

    @classmethod
    def get_context(cls) -> Optional[dict]:
        """Get the full global context."""
        with cls._lock:
            context_available = cls._global_context is not None

            # Enhanced logging: Log project context access operation
            _logger_factory.log_component_operation(
                component="project_context",
                operation="get_context",
                data={
                    "thread_safety": "global_lock_acquired",
                    "context_available": context_available,
                    "project_name": (
                        cls._global_context.get("project_name")
                        if cls._global_context
                        else None
                    ),
                    "context_accessed_successfully": True,
                },
                success=True,
            )

            return cls._global_context.copy() if cls._global_context else None


# Global instance
project_context = ProjectContextManager()
