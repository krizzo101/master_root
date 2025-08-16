"""
Smart Decomposition File System Tools

File system operations for LangGraph agents that automatically use project context.
Based on the proven pattern from old OAMAT application.
"""

import logging
from pathlib import Path
from typing import Annotated

from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState

# Import enhanced logging system
from src.applications.oamat_sd.src.sd_logging import LogConfig, LoggerFactory

# Import the project context manager
from src.applications.oamat_sd.src.utils.project_context import project_context

logger = logging.getLogger("SmartDecomposition.FileSystemTools")

# Initialize enhanced logging for file operations
_log_config = LogConfig()
_logger_factory = LoggerFactory(_log_config)


def create_file_system_tools():
    """
    Creates a suite of tools for file system operations that derive their
    project context from the global project context manager.
    """

    @tool
    def write_file(
        file_path: str, content: str, state: Annotated[dict, InjectedState]
    ) -> str:
        """
        Writes or overwrites content to a specified file within the project directory.
        The project directory is determined by the global project context manager.

        Args:
            file_path: Relative path within the project directory (e.g., "src/main.py", "README.md")
            content: Content to write to the file
            state: LangGraph state (automatically injected)

        Returns:
            Success message with full file path

        Example:
            write_file("hello_world.py", "print('Hello, World!')")
        """
        logger.debug(f"🔍 write_file called with file_path: {file_path}")

        # First try to get project_path from the global context manager
        project_path = project_context.get_project_path()
        logger.debug(f"🔍 Global context project_path: {project_path}")

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
            logger.debug(f"🔍 Fallback project_path from state: {project_path}")

        if not project_path:
            logger.error("🔍 write_file project_path not found!")
            logger.error(f"🔍 Global context: {project_context.get_context()}")
            logger.error(f"🔍 Full state keys: {list(state.keys())}")
            logger.error(f"🔍 Context keys: {list(state.get('context', {}).keys())}")
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
                logger.debug(f"🔧 Converted absolute to relative path: {file_path}")

            full_file_path = Path(project_path) / file_path

            # Additional safety check: ensure we're not creating deeply nested projects
            full_path_str = str(full_file_path)
            if "projects/" in full_path_str and full_path_str.count("projects/") > 1:
                logger.error(
                    f"🚨 CRITICAL: Would create deeply nested file: {full_path_str}"
                )
                return f"Error: Refusing to create nested project file: {full_path_str}"

            # Enhanced logging: Log file operation start
            directory_created = not full_file_path.parent.exists()

            _logger_factory.log_component_operation(
                component="file_operations",
                operation="write_file",
                data={
                    "agent_caller": state.get("agent_context", {}).get(
                        "role", "unknown"
                    ),
                    "filename": file_path,
                    "full_path": str(full_file_path),
                    "content_size_bytes": len(content),
                    "project_context_resolved": True,
                    "directory_created": directory_created,
                },
            )

            # Create parent directories if they don't exist
            full_file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write content to file
            with open(full_file_path, "w", encoding="utf-8") as f:
                f.write(content)

            # Enhanced logging: Log file operation success
            _logger_factory.log_component_operation(
                component="file_operations",
                operation="write_file",
                data={
                    "agent_caller": state.get("agent_context", {}).get(
                        "role", "unknown"
                    ),
                    "filename": file_path,
                    "full_path": str(full_file_path),
                    "content_size_bytes": len(content),
                    "project_context_resolved": True,
                    "write_successful": True,
                    "directory_created": directory_created,
                },
                success=True,
            )

            logger.info(f"✅ File written successfully: {full_file_path}")
            return f"✅ File written successfully: {full_file_path}"

        except Exception as e:
            # Enhanced logging: Log file operation failure
            _logger_factory.log_component_operation(
                component="file_operations",
                operation="write_file",
                data={
                    "agent_caller": state.get("agent_context", {}).get(
                        "role", "unknown"
                    ),
                    "filename": file_path,
                    "full_path": (
                        str(full_file_path)
                        if "full_file_path" in locals()
                        else f"{project_path}/{file_path}"
                    ),
                    "content_size_bytes": len(content),
                    "project_context_resolved": bool(project_path),
                    "write_successful": False,
                    "error": str(e),
                },
                success=False,
            )

            error_msg = f"❌ Error writing file to {file_path}: {e}"
            logger.error(error_msg)
            return error_msg

    @tool
    def read_file(file_path: str, state: Annotated[dict, InjectedState]) -> str:
        """
        Reads content from a specified file within the project directory.
        The project directory is determined by the global project context manager.

        Args:
            file_path: Relative path within the project directory
            state: LangGraph state (automatically injected)

        Returns:
            File content or error message
        """
        logger.debug(f"🔍 read_file called with file_path: {file_path}")

        # First try to get project_path from the global context manager
        project_path = project_context.get_project_path()

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

        if not project_path:
            logger.error("🔍 read_file project_path not found!")
            logger.error(f"🔍 Global context: {project_context.get_context()}")
            logger.error(f"🔍 Full state keys: {list(state.keys())}")
            logger.error(f"🔍 Context keys: {list(state.get('context', {}).keys())}")
            return "Error: project_path not found in workflow state context."

        try:
            # FIX: Handle case where file_path already contains the project path
            if file_path.startswith(project_path):
                # Strip the project path from file_path to make it relative
                relative_file_path = file_path[len(project_path) :].lstrip("/")
                file_path = relative_file_path

            full_file_path = Path(project_path) / file_path

            if not full_file_path.exists():
                # Enhanced logging: Log file not found
                _logger_factory.log_component_operation(
                    component="file_operations",
                    operation="read_file",
                    data={
                        "agent_caller": state.get("agent_context", {}).get(
                            "role", "unknown"
                        ),
                        "filename": file_path,
                        "full_path": str(full_file_path),
                        "project_context_resolved": True,
                        "read_successful": False,
                        "error": "File does not exist",
                    },
                    success=False,
                )
                return f"❌ Error: File does not exist: {full_file_path}"

            with open(full_file_path, encoding="utf-8") as f:
                content = f.read()

            # Enhanced logging: Log file read success
            _logger_factory.log_component_operation(
                component="file_operations",
                operation="read_file",
                data={
                    "agent_caller": state.get("agent_context", {}).get(
                        "role", "unknown"
                    ),
                    "filename": file_path,
                    "full_path": str(full_file_path),
                    "content_size_bytes": len(content),
                    "project_context_resolved": True,
                    "read_successful": True,
                },
                success=True,
            )

            logger.info(f"✅ File read successfully: {full_file_path}")
            return content

        except Exception as e:
            # Enhanced logging: Log file read error
            _logger_factory.log_component_operation(
                component="file_operations",
                operation="read_file",
                data={
                    "agent_caller": state.get("agent_context", {}).get(
                        "role", "unknown"
                    ),
                    "filename": file_path,
                    "full_path": (
                        str(full_file_path)
                        if "full_file_path" in locals()
                        else f"{project_path}/{file_path}"
                    ),
                    "project_context_resolved": bool(project_path),
                    "read_successful": False,
                    "error": str(e),
                },
                success=False,
            )

            error_msg = f"❌ Error reading file {file_path}: {e}"
            logger.error(error_msg)
            return error_msg

    @tool
    def list_files(
        state: Annotated[dict, InjectedState], directory_path: str = "."
    ) -> str:
        """
        Lists files in a specified directory within the project directory.
        Defaults to listing the project's root if no directory is specified.

        Args:
            state: LangGraph state (automatically injected)
            directory_path: Relative directory path within project (defaults to ".")

        Returns:
            Formatted list of files and directories
        """
        logger.debug(f"🔍 list_files called with directory_path: {directory_path}")

        # First try to get project_path from the global context manager
        project_path = project_context.get_project_path()

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

        if not project_path:
            logger.error("🔍 list_files project_path not found!")
            logger.error(f"🔍 Global context: {project_context.get_context()}")
            logger.error(f"🔍 Full state keys: {list(state.keys())}")
            logger.error(f"🔍 Context keys: {list(state.get('context', {}).keys())}")
            return "Error: project_path not found in workflow state context."

        try:
            # FIX: Handle case where directory_path already contains the project path
            if directory_path.startswith(project_path):
                # Strip the project path from directory_path to make it relative
                relative_directory_path = directory_path[len(project_path) :].lstrip(
                    "/"
                )
                directory_path = relative_directory_path

            target_path = Path(project_path) / directory_path

            if not target_path.exists() or not target_path.is_dir():
                # Enhanced logging: Log directory not found
                _logger_factory.log_component_operation(
                    component="file_operations",
                    operation="list_files",
                    data={
                        "agent_caller": state.get("agent_context", {}).get(
                            "role", "unknown"
                        ),
                        "directory_path": directory_path,
                        "full_path": str(target_path),
                        "project_context_resolved": True,
                        "list_successful": False,
                        "error": "Directory does not exist",
                    },
                    success=False,
                )
                return f"❌ Error: Directory does not exist: {target_path}"

            contents = []
            for item in target_path.iterdir():
                if item.is_file():
                    contents.append(f"📄 {item.name}")
                elif item.is_dir():
                    contents.append(f"📁 {item.name}/")

            # Enhanced logging: Log directory listing success
            _logger_factory.log_component_operation(
                component="file_operations",
                operation="list_files",
                data={
                    "agent_caller": state.get("agent_context", {}).get(
                        "role", "unknown"
                    ),
                    "directory_path": directory_path,
                    "full_path": str(target_path),
                    "project_context_resolved": True,
                    "list_successful": True,
                    "items_found": len(contents),
                },
                success=True,
            )

            if not contents:
                return f"📂 Directory is empty: {target_path}"

            result = f"📂 Contents of {target_path}:\n" + "\n".join(sorted(contents))
            logger.info(f"✅ Directory listed successfully: {target_path}")
            return result

        except Exception as e:
            # Enhanced logging: Log directory listing error
            _logger_factory.log_component_operation(
                component="file_operations",
                operation="list_files",
                data={
                    "agent_caller": state.get("agent_context", {}).get(
                        "role", "unknown"
                    ),
                    "directory_path": directory_path,
                    "full_path": (
                        str(target_path)
                        if "target_path" in locals()
                        else f"{project_path}/{directory_path}"
                    ),
                    "project_context_resolved": bool(project_path),
                    "list_successful": False,
                    "error": str(e),
                },
                success=False,
            )

            error_msg = f"❌ Error listing directory {directory_path}: {e}"
            logger.error(error_msg)
            return error_msg

    return [write_file, read_file, list_files]
