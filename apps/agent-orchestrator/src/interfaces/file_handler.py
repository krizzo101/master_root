"""
File Handler Interface for dependency injection
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Union


class IFileHandler(ABC):
    """
    Abstract interface for file handling operations.
    Provides async methods for file I/O with consistent error handling.
    """

    @abstractmethod
    async def read_json(self, path: Union[str, Path]) -> Any:
        """
        Read JSON data from file.

        Args:
            path: File path to read from

        Returns:
            Parsed JSON data

        Raises:
            FileNotFoundError: If file doesn't exist
            json.JSONDecodeError: If file contains invalid JSON
        """
        pass

    @abstractmethod
    async def write_json(
        self,
        path: Union[str, Path],
        data: Any,
        indent: int = 2,
        ensure_ascii: bool = False,
    ) -> Path:
        """
        Write JSON data to file.

        Args:
            path: File path to write to
            data: Data to serialize as JSON
            indent: JSON indentation level
            ensure_ascii: Ensure ASCII encoding

        Returns:
            Path to written file

        Raises:
            IOError: If write fails
        """
        pass

    @abstractmethod
    async def read_yaml(self, path: Union[str, Path]) -> Any:
        """
        Read YAML data from file.

        Args:
            path: File path to read from

        Returns:
            Parsed YAML data

        Raises:
            FileNotFoundError: If file doesn't exist
            yaml.YAMLError: If file contains invalid YAML
        """
        pass

    @abstractmethod
    async def write_yaml(
        self, path: Union[str, Path], data: Any, default_flow_style: bool = False
    ) -> Path:
        """
        Write YAML data to file.

        Args:
            path: File path to write to
            data: Data to serialize as YAML
            default_flow_style: Use flow style for YAML

        Returns:
            Path to written file

        Raises:
            IOError: If write fails
        """
        pass

    @abstractmethod
    async def read_text(self, path: Union[str, Path], encoding: str = "utf-8") -> str:
        """
        Read text from file.

        Args:
            path: File path to read from
            encoding: Text encoding

        Returns:
            File contents as string

        Raises:
            FileNotFoundError: If file doesn't exist
            UnicodeDecodeError: If encoding fails
        """
        pass

    @abstractmethod
    async def write_text(
        self, path: Union[str, Path], content: str, encoding: str = "utf-8"
    ) -> Path:
        """
        Write text to file.

        Args:
            path: File path to write to
            content: Text content to write
            encoding: Text encoding

        Returns:
            Path to written file

        Raises:
            IOError: If write fails
        """
        pass

    @abstractmethod
    async def exists(self, path: Union[str, Path]) -> bool:
        """
        Check if file exists.

        Args:
            path: File path to check

        Returns:
            True if file exists, False otherwise
        """
        pass

    @abstractmethod
    async def delete(self, path: Union[str, Path]) -> bool:
        """
        Delete a file.

        Args:
            path: File path to delete

        Returns:
            True if file was deleted, False if it didn't exist

        Raises:
            PermissionError: If deletion not permitted
        """
        pass

    @abstractmethod
    async def list_files(
        self, path: Union[str, Path], pattern: str = "*", recursive: bool = False
    ) -> List[Path]:
        """
        List files in directory.

        Args:
            path: Directory path
            pattern: Glob pattern for filtering
            recursive: Search recursively

        Returns:
            List of file paths

        Raises:
            NotADirectoryError: If path is not a directory
        """
        pass

    @abstractmethod
    async def ensure_dir(self, path: Union[str, Path]) -> Path:
        """
        Ensure directory exists, creating if necessary.

        Args:
            path: Directory path

        Returns:
            Path to directory

        Raises:
            PermissionError: If creation not permitted
        """
        pass

    @abstractmethod
    async def get_metrics(self) -> Dict:
        """
        Get file operation metrics.

        Returns:
            Dictionary containing I/O metrics
        """
        pass
