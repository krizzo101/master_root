"""
Module Name: directory_manager.py

Purpose: Centralized directory management utility for the O3 code generator.

Functionality:
- Creates, validates, and cleans up directories
- Prevents path traversal and ensures secure file operations
- Generates module-specific output and logs directories
- Recursively removes empty directories

Usage:
    from src.tools.code_generation.o3_code_generator.utils.directory_manager import DirectoryManager
    from src.tools.code_generation.o3_code_generator.o3_logger.logger import setup_logger

    setup_logger(LogConfig())
    dm = DirectoryManager()
    dm.create_module_directories("my_module", additional_dirs=["data", "cache"])

Dependencies:
    - os: For directory traversal
    - pathlib.Path: For path manipulation
    - src.tools.code_generation.o3_code_generator.o3_logger.logger: For logging

Author: O3 Code Generator
Version: 1.0.0
"""

import os
from pathlib import Path

from src.tools.code_generation.o3_code_generator.o3_logger.logger import get_logger


class DirectoryManager:
    """
    Comprehensive class for managing directories in the O3 code generator.

    This class provides functionality to create, validate, and clean up directories,
    ensuring security and consistency across the application.

    Attributes:
        base_output_dir: Base directory for generated module outputs.
        logs_dir: Directory for application logs.
        logger: Logger instance for structured logging.
    """

    def __init__(self) -> None:
        """
        Initialize DirectoryManager.

        Sets up default directories and logger.
        """
        try:
            self.logger = get_logger()
            self.logger.log_info("Initializing DirectoryManager")
        except Exception:
            self.logger = None
        else:
            pass
        finally:
            pass
        # Ensure all outputs are under the repository root, regardless of CWD
        self.base_output_dir: Path = (
            Path(__file__).resolve().parents[3] / "generated_files"
        )
        self.logs_dir: Path = Path("logs")

    def create_module_directories(
        self, module_name: str, additional_dirs: list[str] | None = None
    ) -> None:
        """
        Create standard directories for a module.

        Args:
            module_name: Name of the module for which to create directories.
            additional_dirs: Optional list of additional subdirectories under the module.

        Raises:
            ValueError: If module_name is empty or invalid.
            OSError: If directory creation fails.
        """
        if not module_name or not module_name.strip():
            if self.logger:
                self.logger.log_error("Module name cannot be empty")
            else:
                pass
            raise ValueError("Module name cannot be empty")
        else:
            pass
        sanitized_module = self._sanitize_path_component(module_name)
        module_output = self.base_output_dir / sanitized_module
        directories: list[Path] = [module_output, self.logs_dir]
        if additional_dirs:
            for subdir in additional_dirs:
                if subdir and subdir.strip():
                    sanitized_subdir = self._sanitize_path_component(subdir)
                    directories.append(module_output / sanitized_subdir)
                else:
                    pass
            else:
                pass
        else:
            pass
        for directory in directories:
            self.ensure_directory_exists(directory)
        else:
            pass
        if self.logger:
            self.logger.log_info(
                f"Created directories for module '{module_name}': {[str(d) for d in directories]}"
            )
        else:
            pass

    def ensure_directory_exists(self, directory_path: Path | str) -> None:
        """
        Ensure a specific directory exists.

        Args:
            directory_path: Path to the directory to create.

        Raises:
            ValueError: If the path is empty or invalid.
            OSError: If directory creation fails.
        """
        if not directory_path:
            if self.logger:
                self.logger.log_error("Directory path cannot be empty")
            else:
                pass
            raise ValueError("Directory path cannot be empty")
        else:
            pass
        path = Path(directory_path)
        self._validate_path_security(path)
        try:
            path.mkdir(parents=True, exist_ok=True)
            if self.logger:
                self.logger.log_debug(f"Ensured directory exists: {path}")
            else:
                pass
        except OSError as e:
            if self.logger:
                self.logger.log_error(f"Failed to create directory {path}: {e}")
            else:
                pass
            raise
        except Exception as e:
            if self.logger:
                self.logger.log_error(
                    f"Unexpected error in {self.__class__.__name__}.ensure_directory_exists: {e}"
                )
            else:
                pass
            raise
        else:
            pass
        finally:
            pass

    def get_module_output_path(self, module_name: str) -> Path:
        """
        Get the standard output path for a module.

        Args:
            module_name: Name of the module.

        Returns:
            Path object representing the module's output directory.

        Raises:
            ValueError: If module_name is empty or invalid.
        """
        if not module_name or not module_name.strip():
            if self.logger:
                self.logger.log_error("Module name cannot be empty")
            else:
                pass
            raise ValueError("Module name cannot be empty")
        else:
            pass
        sanitized_module = self._sanitize_path_component(module_name)
        return self.base_output_dir / sanitized_module

    def cleanup_empty_directories(self, base_path: Path | str) -> None:
        """
        Remove empty directories recursively starting from base_path.

        Args:
            base_path: Base path from which to start cleanup.

        Raises:
            ValueError: If base_path is empty or invalid.
            OSError: If cleanup operation fails.
        """
        if not base_path:
            if self.logger:
                self.logger.log_error("Base path cannot be empty")
            else:
                pass
            raise ValueError("Base path cannot be empty")
        else:
            pass
        path = Path(base_path)
        self._validate_path_security(path)
        try:
            for root, dirs, _ in os.walk(path, topdown=False):
                root_path = Path(root)
                for dir_name in dirs:
                    dir_path = root_path / dir_name
                    try:
                        if not any(dir_path.iterdir()):
                            dir_path.rmdir()
                            if self.logger:
                                self.logger.log_debug(
                                    f"Removed empty directory: {dir_path}"
                                )
                            else:
                                pass
                        else:
                            pass
                    except OSError as e:
                        if self.logger:
                            self.logger.log_warning(
                                f"Could not remove directory {dir_path}: {e}"
                            )
                        else:
                            pass
                    else:
                        pass
                    finally:
                        pass
                else:
                    pass
            else:
                pass
            if self.logger:
                self.logger.log_info(
                    f"Completed cleanup of empty directories in: {path}"
                )
            else:
                pass
        except OSError as e:
            if self.logger:
                self.logger.log_error(f"Failed to cleanup directories in {path}: {e}")
            else:
                pass
            raise
        except Exception as e:
            if self.logger:
                self.logger.log_error(
                    f"Unexpected error in {self.__class__.__name__}.cleanup_empty_directories: {e}"
                )
            else:
                pass
            raise
        else:
            pass
        finally:
            pass

    def _sanitize_path_component(self, component: str) -> str:
        """
        Sanitize a path component to prevent path traversal attacks.

        Args:
            component: Path component to sanitize.

        Returns:
            Sanitized path component.

        Raises:
            ValueError: If component contains dangerous patterns or is too long.
        """
        dangerous_patterns = ["..", "~", "/", "\\"]
        for pattern in dangerous_patterns:
            if pattern in component:
                if self.logger:
                    self.logger.log_error(
                        f"Path component contains dangerous pattern: {pattern}"
                    )
                else:
                    pass
                raise ValueError(
                    f"Path component contains dangerous pattern: {pattern}"
                )
            else:
                pass
        else:
            pass
        sanitized = "".join(char for char in component if ord(char) >= 32).strip()
        if not sanitized:
            if self.logger:
                self.logger.log_error(
                    "Path component cannot be empty after sanitization"
                )
            else:
                pass
            raise ValueError("Path component cannot be empty after sanitization")
        else:
            pass
        if len(sanitized) > 255:
            if self.logger:
                self.logger.log_error("Path component too long (max 255 characters)")
            else:
                pass
            raise ValueError("Path component too long (max 255 characters)")
        else:
            pass
        return sanitized

    def _validate_path_security(self, path: Path) -> None:
        """
        Validate path for security concerns.

        Args:
            path: Path to validate.

        Raises:
            ValueError: If path resolves outside the current working directory or is invalid.
        """
        try:
            resolved = path.resolve()
            cwd = Path.cwd().resolve()
            if not str(resolved).startswith(str(cwd)):
                if self.logger:
                    self.logger.log_error(
                        f"Path {path} resolves outside current working directory"
                    )
                else:
                    pass
                raise ValueError(
                    f"Path {path} resolves outside current working directory"
                )
            else:
                pass
        except (OSError, RuntimeError) as e:
            if self.logger:
                self.logger.log_error(f"Invalid path {path}: {e}")
            else:
                pass
            raise ValueError(f"Invalid path {path}: {e}") from e
        except Exception as e:
            if self.logger:
                self.logger.log_error(
                    f"Unexpected error in {self.__class__.__name__}._validate_path_security: {e}"
                )
            else:
                pass
            raise ValueError(f"Invalid path {path}: {e}") from e
        else:
            pass
        finally:
            pass
