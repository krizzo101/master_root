"""
OAMAT Agent Factory - File System Tools

File system operations for LangGraph agents.
Extracted from agent_factory.py for better modularity and maintainability.
"""

import logging
from pathlib import Path
from typing import Annotated

from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState

# Import the project context manager
from src.applications.oamat.utils.project_context import project_context

logger = logging.getLogger("OAMAT.AgentFactory.FileSystemTools")


def create_file_system_tools():
    """
    Creates a suite of tools for file system operations that derive their
    project context from the workflow state.
    """

    @tool
    def write_file(
        file_path: str, content: str, state: Annotated[dict, InjectedState]
    ) -> str:
        """
        Writes or overwrites content to a specified file within the project directory.
        The project directory is determined by the 'project_path' in the workflow state.
        """
        # First try to get project_path from the global context manager
        project_path = project_context.get_project_path()
        logger.debug(f"🔍 DEBUG: write_file called with file_path: {file_path}")
        logger.debug(f"🔍 DEBUG: Global context project_path: {project_path}")

        # Fallback: try to get from LangGraph state (legacy support)
        if not project_path:
            context = state.get("context", {})
            project_path = (
                context.get("project_path")  # Direct access
                or context.get("shared_context", {}).get(
                    "project_path"
                )  # Agent context structure
                or state.get("project_path")  # Top-level state access
            )
            logger.debug(f"🔍 DEBUG: Fallback project_path from state: {project_path}")

        if not project_path:
            logger.error("🔍 DEBUG: write_file project_path not found!")
            logger.error(f"🔍 DEBUG: Global context: {project_context.get_context()}")
            logger.error(f"🔍 DEBUG: Full state keys: {list(state.keys())}")
            logger.error(
                f"🔍 DEBUG: Context keys: {list(state.get('context', {}).keys())}"
            )
            return "Error: project_path not found in workflow state context."

        # CRITICAL FIX: Prevent nested project directory creation
        # Check if project_path already contains "projects/" in a nested way
        project_path_str = str(project_path)
        if "projects/" in project_path_str and project_path_str.count("projects/") > 1:
            logger.error(
                f"🚨 CRITICAL: Detected nested project directory: {project_path_str}"
            )
            logger.error(
                f"🚨 This would create file at: {Path(project_path) / file_path}"
            )
            return f"Error: Refusing to write to nested project directory: {project_path_str}"

        try:
            # FIX: Handle case where file_path already contains the project path
            # This prevents duplication when agents pass the full path instead of relative path
            if file_path.startswith(project_path):
                # Strip the project path from file_path to make it relative
                relative_file_path = file_path[len(project_path) :].lstrip("/")
                file_path = relative_file_path

            full_file_path = Path(project_path) / file_path

            # Additional safety check: ensure we're not creating deeply nested projects
            full_path_str = str(full_file_path)
            if "projects/" in full_path_str and full_path_str.count("projects/") > 1:
                logger.error(
                    f"🚨 CRITICAL: Would create deeply nested file: {full_path_str}"
                )
                return f"Error: Refusing to create nested project file: {full_path_str}"

            full_file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(full_file_path, "w", encoding="utf-8") as f:
                f.write(content)

            logger.info(f"✅ File written successfully: {full_file_path}")
            return f"✅ File written successfully: {full_file_path}"
        except Exception as e:
            error_msg = f"❌ Error writing file to {file_path}: {e}"
            logger.error(error_msg)
            raise OSError(error_msg)

    @tool
    def read_file(file_path: str, state: Annotated[dict, InjectedState]) -> str:
        """
        Reads content from a specified file within the project directory.
        The project directory is determined by the 'project_path' in the workflow state.
        """
        # First try to get project_path from the global context manager
        project_path = project_context.get_project_path()

        # Fallback: try to get from LangGraph state (legacy support)
        if not project_path:
            context = state.get("context", {})
            # Try multiple possible locations for project_path
            project_path = (
                context.get("project_path")  # Direct access
                or context.get("shared_context", {}).get(
                    "project_path"
                )  # Agent context structure
                or state.get("project_path")  # Top-level state access
            )

        if not project_path:
            logger.error("🔍 DEBUG: read_file project_path not found!")
            logger.error(f"🔍 DEBUG: Global context: {project_context.get_context()}")
            logger.error(f"🔍 DEBUG: Full state keys: {list(state.keys())}")
            logger.error(
                f"🔍 DEBUG: Context keys: {list(state.get('context', {}).keys())}"
            )
            return "Error: project_path not found in workflow state context."

        try:
            # FIX: Handle case where file_path already contains the project path
            # This prevents duplication when agents pass the full path instead of relative path
            if file_path.startswith(project_path):
                # Strip the project path from file_path to make it relative
                relative_file_path = file_path[len(project_path) :].lstrip("/")
                file_path = relative_file_path

            full_file_path = Path(project_path) / file_path

            if not full_file_path.exists():
                raise FileNotFoundError(
                    f"❌ Error: File does not exist: {full_file_path}"
                )

            with open(full_file_path, encoding="utf-8") as f:
                content = f.read()

            logger.info(f"✅ File read successfully: {full_file_path}")
            return content
        except FileNotFoundError:
            raise
        except Exception as e:
            error_msg = f"❌ Error reading file {file_path}: {e}"
            logger.error(error_msg)
            raise OSError(error_msg)

    @tool
    def list_files(
        state: Annotated[dict, InjectedState], directory_path: str = "."
    ) -> list[str]:
        """
        Lists files in a specified directory within the project directory.
        Defaults to listing the project's root if no directory is specified.
        The project directory is determined by the 'project_path' in the workflow state.
        """
        # First try to get project_path from the global context manager
        project_path = project_context.get_project_path()

        # Fallback: try to get from LangGraph state (legacy support)
        if not project_path:
            context = state.get("context", {})
            # Try multiple possible locations for project_path
            project_path = (
                context.get("project_path")  # Direct access
                or context.get("shared_context", {}).get(
                    "project_path"
                )  # Agent context structure
                or state.get("project_path")  # Top-level state access
            )

        if not project_path:
            logger.error("🔍 DEBUG: list_files project_path not found!")
            logger.error(f"🔍 DEBUG: Global context: {project_context.get_context()}")
            logger.error(f"🔍 DEBUG: Full state keys: {list(state.keys())}")
            logger.error(
                f"🔍 DEBUG: Context keys: {list(state.get('context', {}).keys())}"
            )
            return "Error: project_path not found in workflow state context."

        # FIX: Handle case where directory_path already contains the project path
        # This prevents duplication when agents pass the full path instead of relative path
        if directory_path.startswith(project_path):
            # Strip the project path from directory_path to make it relative
            relative_directory_path = directory_path[len(project_path) :].lstrip("/")
            directory_path = relative_directory_path

        target_path = Path(project_path) / directory_path

        if not target_path.exists() or not target_path.is_dir():
            raise FileNotFoundError(f"❌ Error: Directory does not exist: {target_path}")

        contents = []
        for item in target_path.iterdir():
            if item.is_file():
                contents.append(f"📄 {item.name}")
            elif item.is_dir():
                contents.append(f"📁 {item.name}/")

        if not contents:
            return f"📂 Directory is empty: {target_path}"

        result = f"📂 Contents of {target_path}:\n" + "\n".join(sorted(contents))
        logger.info(f"✅ Directory listed successfully: {target_path}")
        return result

    return [write_file, read_file, list_files]
