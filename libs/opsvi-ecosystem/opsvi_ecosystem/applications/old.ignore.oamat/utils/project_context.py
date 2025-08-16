"""
OAMAT Project Context Manager

Provides a thread-safe way for tools to access the current project context
when it's not available through LangGraph's state management.
"""

import threading


class ProjectContextManager:
    """Global project context manager for OAMAT tools."""

    _lock = threading.Lock()
    _global_context = None  # Single global context instead of thread-specific

    @classmethod
    def set_context(cls, project_name: str, project_path: str):
        """Set the global project context."""
        with cls._lock:
            cls._global_context = {
                "project_name": project_name,
                "project_path": str(project_path),
            }

    @classmethod
    def get_project_path(cls) -> str | None:
        """Get the project path from global context."""
        with cls._lock:
            return (
                cls._global_context.get("project_path") if cls._global_context else None
            )

    @classmethod
    def get_project_name(cls) -> str | None:
        """Get the project name from global context."""
        with cls._lock:
            return (
                cls._global_context.get("project_name") if cls._global_context else None
            )

    @classmethod
    def clear_context(cls):
        """Clear the global project context."""
        with cls._lock:
            cls._global_context = None

    @classmethod
    def get_context(cls) -> dict | None:
        """Get the full global context."""
        with cls._lock:
            return cls._global_context


# Global instance
project_context = ProjectContextManager()
