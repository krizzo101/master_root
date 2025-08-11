"""Module Name: file_generator.py

Purpose: Centralized file generation and management for the O3 code generator.

Functionality:
- Creates timestamped filenames
- Saves files with backup and cleanup capabilities
- Generates output in JSON, Markdown, HTML, and YAML formats using OutputFormatter
- Sanitizes filenames to prevent invalid characters and path traversal
- Cleans up old files based on age threshold

Usage:
    from src.tools.code_generation.o3_code_generator.utils.file_generator import FileGenerator

    generator = FileGenerator()
    files = generator.create_analysis_files(data, 'module', 'report')

Dependencies:
    - shutil: For file copying during backup
    - pathlib: For file path handling
    - datetime: For timestamp generation
    - typing: For type hints
    - src.tools.code_generation.o3_code_generator.o3_logger.logger: For logging
    - src.tools.code_generation.o3_code_generator.utils.directory_manager: For directory management
    - src.tools.code_generation.o3_code_generator.utils.output_formatter: For output formatting

Author: O3 Code Generator
Version: 1.0.0
"""

from datetime import datetime
from pathlib import Path
import shutil
from typing import Any

from src.tools.code_generation.o3_code_generator.o3_logger.logger import get_logger
from src.tools.code_generation.o3_code_generator.utils.directory_manager import (
    DirectoryManager,
)
from src.tools.code_generation.o3_code_generator.utils.output_formatter import (
    OutputFormatter,
)


class FileGenerator:
    """
    Centralized file generation and management.

    Attributes:
        logger: O3Logger instance for structured logging.
        output_formatter: Formatter for various output formats.
        directory_manager: Manager for directory operations.
        base_output_dir: Base directory for generated files.
    """

    def __init__(
        self,
        custom_logger: Any | None = None,
        output_formatter: OutputFormatter | None = None,
        base_output_dir: str | Path | None = None,
    ) -> None:
        """
        Initialize the FileGenerator.

        Args:
            custom_logger: Optional logger instance. If None, uses get_logger().
            output_formatter: Optional OutputFormatter. If None, creates a default one.
            base_output_dir: Optional base directory for generated files. Defaults to './generated_files'.

        Raises:
            Exception: If base output directory cannot be created.
        """
        self.logger = custom_logger or get_logger()
        self.output_formatter = output_formatter or OutputFormatter()
        self.directory_manager = DirectoryManager()
        self.base_output_dir: Path = (
            Path(base_output_dir) if base_output_dir else Path("generated_files")
        )
        try:
            self.directory_manager.ensure_directory_exists(self.base_output_dir)
            self.logger.log_info(
                f"Initialized FileGenerator with base directory: {self.base_output_dir}"
            )
        except Exception as e:
            self.logger.log_error(f"Failed to ensure base output directory exists: {e}")
            raise
        else:
            pass
        finally:
            pass

    def create_analysis_files(
        self,
        analysis_data: dict[str, Any],
        module_name: str,
        title: str,
        formats: list[str] | None = None,
    ) -> list[str]:
        """
        Create standard output files (JSON, Markdown, HTML, YAML).

        Args:
            analysis_data: Dictionary containing the analysis data.
            module_name: Name of the module generating the files.
            title: Title for the output files.
            formats: List of formats to generate. Defaults to ['json', 'markdown', 'html', 'yaml'].

        Returns:
            List of created file paths as strings.

        Raises:
            ValueError: If inputs are invalid.
            OSError: If file creation fails.
        """
        if not isinstance(analysis_data, dict):
            raise ValueError("analysis_data must be a dictionary")
        else:
            pass
        if not module_name.strip():
            raise ValueError("module_name cannot be empty")
        else:
            pass
        if not title.strip():
            raise ValueError("title cannot be empty")
        else:
            pass
        if formats is None:
            formats = ["json", "markdown", "html", "yaml"]
        else:
            pass
        try:
            sanitized_module = self._sanitize_filename(module_name)
            module_dir = self.base_output_dir / sanitized_module
            self.directory_manager.ensure_directory_exists(module_dir)
            created_files: list[str] = []
            for fmt in formats:
                fmt_lower = fmt.lower()
                if fmt_lower == "json":
                    file_path = self._create_json_file(analysis_data, module_dir, title)
                elif fmt_lower == "markdown":
                    file_path = self._create_markdown_file(
                        analysis_data, module_dir, title
                    )
                elif fmt_lower == "html":
                    file_path = self._create_html_file(analysis_data, module_dir, title)
                elif fmt_lower == "yaml":
                    file_path = self._create_yaml_file(analysis_data, module_dir, title)
                else:
                    self.logger.log_warning(f"Unsupported format: {fmt}")
                    continue
                created_files.append(file_path)
            else:
                pass
            self.logger.log_info(
                f"Created {len(created_files)} files for module '{module_name}': {created_files}"
            )
            return created_files
        except OSError as e:
            self.logger.log_error(
                f"Failed to create analysis files for module '{module_name}': {e}"
            )
            raise
        except Exception as e:
            self.logger.log_error(f"Unexpected error in create_analysis_files: {e}")
            raise
        else:
            pass
        finally:
            pass

    def create_timestamped_filename(self, base_name: str, extension: str) -> str:
        """
        Create a timestamped filename.

        Args:
            base_name: Base name for the file.
            extension: File extension (with or without dot).

        Returns:
            Timestamped filename string.

        Raises:
            ValueError: If base_name is empty.
        """
        if not base_name.strip():
            raise ValueError("base_name cannot be empty")
        else:
            pass
        ext = extension if extension.startswith(".") else f".{extension}"
        sanitized_base = self._sanitize_filename(base_name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{sanitized_base}_{timestamp}{ext}"

    def save_file(self, content: str, file_path: str | Path) -> None:
        """
        Save content to a file with backup of existing files.

        Args:
            content: Content to save.
            file_path: Path where to save the file.

        Raises:
            ValueError: If content is empty or file_path is invalid.
            OSError: If file saving fails.
        """
        if not content:
            raise ValueError("content must be a non-empty string")
        else:
            pass
        path = Path(file_path)
        try:
            self.directory_manager.ensure_directory_exists(path.parent)
            if path.exists():
                self.create_backup(path)
            else:
                pass
            path.write_text(content, encoding="utf-8")
            self.logger.log_debug(f"Saved file: {path}")
        except OSError as e:
            self.logger.log_error(f"Failed to save file {path}: {e}")
            raise
        except Exception as e:
            self.logger.log_error(f"Unexpected error in save_file: {e}")
            raise
        else:
            pass
        finally:
            pass

    def create_backup(self, file_path: str | Path) -> None:
        """
        Create a timestamped backup of an existing file.

        Args:
            file_path: Path to the file to backup.

        Raises:
            OSError: If backup creation fails.
        """
        path = Path(file_path)
        if not path.exists():
            return
        else:
            pass
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{path.stem}.backup_{timestamp}{path.suffix}"
            backup_path = path.with_name(backup_name)
            shutil.copy2(path, backup_path)
            self.logger.log_debug(f"Created backup: {backup_path}")
        except OSError as e:
            self.logger.log_error(f"Failed to create backup of {path}: {e}")
            raise
        except Exception as e:
            self.logger.log_error(f"Unexpected error in create_backup: {e}")
            raise
        else:
            pass
        finally:
            pass

    def cleanup_old_files(self, directory: str | Path, days_old: int = 30) -> None:
        """
        Clean up files older than a given age in days.

        Args:
            directory: Directory to clean up.
            days_old: Age threshold in days for deletion.

        Raises:
            OSError: If cleanup operation fails.
        """
        dir_path = Path(directory)
        if not dir_path.exists():
            return
        else:
            pass
        try:
            cutoff = datetime.now().timestamp() - days_old * 86400
            deleted = 0
            for file in dir_path.rglob("*"):
                if file.is_file() and file.stat().st_mtime < cutoff:
                    try:
                        file.unlink()
                        deleted += 1
                        self.logger.log_debug(f"Deleted old file: {file}")
                    except OSError as e:
                        self.logger.log_warning(f"Could not delete file {file}: {e}")
                    else:
                        pass
                    finally:
                        pass
                else:
                    pass
            else:
                pass
            self.logger.log_info(f"Cleaned up {deleted} old files in {dir_path}")
        except OSError as e:
            self.logger.log_error(f"Failed to cleanup old files in {dir_path}: {e}")
            raise
        except Exception as e:
            self.logger.log_error(f"Unexpected error in cleanup_old_files: {e}")
            raise
        else:
            pass
        finally:
            pass

    def _create_json_file(
        self, data: dict[str, Any], output_dir: Path, title: str
    ) -> str:
        """
        Create a JSON output file.

        Args:
            data: Data to write.
            output_dir: Output directory.
            title: Title for filename.

        Returns:
            Path to the created JSON file as string.
        """
        filename = self.create_timestamped_filename(title, ".json")
        path = output_dir / filename
        content = self.output_formatter.to_json(data, pretty=True)
        self.save_file(content, path)
        return str(path)

    def _create_markdown_file(
        self, data: dict[str, Any], output_dir: Path, title: str
    ) -> str:
        """
        Create a Markdown output file.

        Args:
            data: Data to write.
            output_dir: Output directory.
            title: Title for filename.

        Returns:
            Path to the created Markdown file as string.
        """
        filename = self.create_timestamped_filename(title, ".md")
        path = output_dir / filename
        content = self.output_formatter.to_markdown(data, title)
        self.save_file(content, path)
        return str(path)

    def _create_html_file(
        self, data: dict[str, Any], output_dir: Path, title: str
    ) -> str:
        """
        Create an HTML output file.

        Args:
            data: Data to write.
            output_dir: Output directory.
            title: Title for filename.

        Returns:
            Path to the created HTML file as string.
        """
        filename = self.create_timestamped_filename(title, ".html")
        path = output_dir / filename
        content = self.output_formatter.to_html(data, title)
        self.save_file(content, path)
        return str(path)

    def _create_yaml_file(
        self, data: dict[str, Any], output_dir: Path, title: str
    ) -> str:
        """
        Create a YAML output file.

        Args:
            data: Data to write.
            output_dir: Output directory.
            title: Title for filename.

        Returns:
            Path to the created YAML file as string.
        """
        filename = self.create_timestamped_filename(title, ".yaml")
        path = output_dir / filename
        content = self.output_formatter.to_yaml(data)
        self.save_file(content, path)
        return str(path)

    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename to prevent invalid characters and traversal.

        Args:
            filename: Original filename.

        Returns:
            Sanitized filename.
        """
        invalid_chars = '<>:"/\\|?*'
        sanitized = "".join("_" if c in invalid_chars else c for c in filename)
        sanitized = sanitized.replace("..", "_").replace("~", "_")
        sanitized = "".join(c for c in sanitized if ord(c) >= 32)
        sanitized = sanitized.strip()[:100] or "unnamed"
        return sanitized
