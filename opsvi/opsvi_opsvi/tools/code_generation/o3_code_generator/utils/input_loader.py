"""
Input Loader - Universal input file loading with validation and error handling.

This module provides centralized input file loading functionality to eliminate
code duplication across the O3 Code Generator application. It supports JSON and
YAML formats, with comprehensive validation, error handling, and template data
cleaning.
"""

import json
from pathlib import Path
from typing import Any

import yaml

from src.tools.code_generation.o3_code_generator.o3_logger.logger import get_logger


class UniversalInputLoader:
    """
    Universal input file loading with validation and error handling.

    Attributes:
        logger: O3Logger instance for structured logging.
        max_file_size: Maximum file size in bytes.
        supported_formats: Supported file extensions.
    """

    def __init__(self, logger: Any | None = None) -> None:
        """
        Initialize the input loader.

        Args:
            logger: Logger instance for structured logging. If None, creates a default logger.
        """
        self.logger = logger or get_logger()
        self.max_file_size: int = 10 * 1024 * 1024
        self.supported_formats: set[str] = {".json", ".yaml", ".yml"}

    def load_json_file(self, file_path: str | Path) -> dict[str, Any]:
        """
        Load and validate JSON input file.

        Args:
            file_path: Path to the JSON file to load.

        Returns:
            Parsed JSON data as a dictionary.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file is not valid JSON or does not contain a dictionary.
            OSError: If there are file system errors.
        """
        path = Path(file_path)
        self._validate_file_path(path)
        try:
            self.logger.log_info(f"Loading JSON file: {path}")
            self._validate_file_size(path)
            content = path.read_text(encoding="utf-8")
            try:
                data = json.loads(content)
            except json.JSONDecodeError as e:
                error_msg = f"Invalid JSON in file {path}: {e}"
                self.logger.log_error(e, error_msg)
                raise ValueError(error_msg) from e
            else:
                pass
            finally:
                pass
            if not isinstance(data, dict):
                error_msg = f"JSON file {path} must contain a dictionary/object"
                self.logger.log_error(ValueError(error_msg), error_msg)
                raise ValueError(error_msg)
            else:
                pass
            self.logger.log_info(f"Successfully loaded JSON file: {path}")
            return data
        except FileNotFoundError as e:
            error_msg = f"File not found: {path}"
            self.logger.log_error(e, error_msg)
            raise
        except OSError as e:
            error_msg = f"Error reading file {path}: {e}"
            self.logger.log_error(e, error_msg)
            raise OSError(error_msg) from e
        else:
            pass
        finally:
            pass

    def load_yaml_file(self, file_path: str | Path) -> dict[str, Any]:
        """
        Load and validate YAML input file.

        Args:
            file_path: Path to the YAML file to load.

        Returns:
            Parsed YAML data as a dictionary.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file is not valid YAML or does not contain a dictionary.
            OSError: If there are file system errors.
        """
        path = Path(file_path)
        self._validate_file_path(path)
        try:
            self.logger.log_info(f"Loading YAML file: {path}")
            self._validate_file_size(path)
            content = path.read_text(encoding="utf-8")
            try:
                data = yaml.safe_load(content)
            except yaml.YAMLError as e:
                error_msg = f"Invalid YAML in file {path}: {e}"
                self.logger.log_error(e, error_msg)
                raise ValueError(error_msg) from e
            else:
                pass
            finally:
                pass
            if not isinstance(data, dict):
                error_msg = f"YAML file {path} must contain a dictionary/object"
                self.logger.log_error(ValueError(error_msg), error_msg)
                raise ValueError(error_msg)
            else:
                pass
            self.logger.log_info(f"Successfully loaded YAML file: {path}")
            return data
        except FileNotFoundError as e:
            error_msg = f"File not found: {path}"
            self.logger.log_error(e, error_msg)
            raise
        except OSError as e:
            error_msg = f"Error reading file {path}: {e}"
            self.logger.log_error(e, error_msg)
            raise OSError(error_msg) from e
        else:
            pass
        finally:
            pass

    def load_file_by_extension(self, file_path: str | Path) -> dict[str, Any]:
        """
        Auto-detect file type by extension and load appropriately.

        Args:
            file_path: Path to the file to load.

        Returns:
            Parsed file data as a dictionary.

        Raises:
            ValueError: If the file format is not supported.
            FileNotFoundError: If the file does not exist.
            OSError: If there are file system errors.
        """
        path = Path(file_path)
        self._validate_file_path(path)
        ext = path.suffix.lower()
        if ext == ".json":
            return self.load_json_file(path)
        else:
            pass
        if ext in {".yaml", ".yml"}:
            return self.load_yaml_file(path)
        else:
            pass
        error_msg = f"Unsupported file format: {ext}. Supported formats: {self.supported_formats}"
        self.logger.log_error(ValueError(error_msg), error_msg)
        raise ValueError(error_msg)

    def validate_required_fields(
        self, data: dict[str, Any], required_fields: list[str]
    ) -> None:
        """
        Validate that required fields are present in the data.

        Args:
            data: Data dictionary to validate.
            required_fields: List of field names that must be present.

        Raises:
            ValueError: If data is not a dictionary, required_fields is not a list,
                        or any required fields are missing.
        """
        if not isinstance(data, dict):
            error_msg = "Data must be a dictionary"
            self.logger.log_error(ValueError(error_msg), error_msg)
            raise ValueError(error_msg)
        else:
            pass
        if not isinstance(required_fields, list):
            error_msg = "Required fields must be a list"
            self.logger.log_error(ValueError(error_msg), error_msg)
            raise ValueError(error_msg)
        else:
            pass
        missing = [f for f in required_fields if data.get(f) is None]
        if missing:
            error_msg = f"Missing required fields: {missing}"
            self.logger.log_error(ValueError(error_msg), error_msg)
            raise ValueError(error_msg)
        else:
            pass
        self.logger.log_debug(f"Validated required fields: {required_fields}")

    def clean_template_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Remove template comments and metadata from data.

        Args:
            data: Dictionary containing the data to clean.

        Returns:
            Cleaned dictionary with keys starting with '_' removed.
        """
        if not isinstance(data, dict):
            return data
        else:
            pass
        cleaned: dict[str, Any] = {}
        for key, value in data.items():
            if not key.startswith("_"):
                cleaned[key] = (
                    self.clean_template_data(value)
                    if isinstance(value, dict)
                    else value
                )
            else:
                pass
        else:
            pass
        return cleaned

    def _validate_file_path(self, file_path: Path) -> None:
        """
        Validate file path for security and existence.

        Args:
            file_path: Path to validate.

        Raises:
            ValueError: If the path is invalid, empty, or resolves outside cwd.
        """
        if not file_path:
            error_msg = "File path cannot be empty"
            self.logger.log_error(ValueError(error_msg), error_msg)
            raise ValueError(error_msg)
        else:
            pass
        try:
            resolved = file_path.resolve()
            cwd = Path.cwd().resolve()
            if not str(resolved).startswith(str(cwd)):
                error_msg = (
                    f"File path {file_path} resolves outside current working directory"
                )
                self.logger.log_error(ValueError(error_msg), error_msg)
                raise ValueError(error_msg)
            else:
                pass
        except (OSError, RuntimeError) as e:
            error_msg = f"Invalid file path {file_path}: {e}"
            self.logger.log_error(e, error_msg)
            raise ValueError(error_msg) from e
        else:
            pass
        finally:
            pass

    def _validate_file_size(self, file_path: Path) -> None:
        """
        Validate file size to prevent memory issues.

        Args:
            file_path: Path to the file to validate.

        Raises:
            ValueError: If the file is too large.
            OSError: If unable to determine file size.
        """
        try:
            size = file_path.stat().st_size
            if size > self.max_file_size:
                error_msg = f"File {file_path} is too large ({size} bytes). Maximum size: {self.max_file_size} bytes"
                self.logger.log_error(ValueError(error_msg), error_msg)
                raise ValueError(error_msg)
            else:
                pass
        except OSError as e:
            error_msg = f"Could not determine file size for {file_path}: {e}"
            self.logger.log_error(e, error_msg)
            raise OSError(error_msg) from e
        else:
            pass
        finally:
            pass
