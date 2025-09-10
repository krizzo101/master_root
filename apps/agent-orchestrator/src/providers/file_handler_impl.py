"""
Concrete FileHandler implementation wrapping existing FileIOManager
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

from ..interfaces.file_handler import IFileHandler
from ..io.file_io_manager import FileIOManager

logger = logging.getLogger(__name__)


class FileHandlerImpl(IFileHandler):
    """
    Concrete implementation of IFileHandler interface.
    Wraps the existing FileIOManager to provide dependency injection.
    """

    def __init__(
        self,
        base_dir: Optional[Path] = None,
        enable_metrics: bool = True,
        max_file_size: int = 100 * 1024 * 1024,  # 100MB
    ):
        """
        Initialize the file handler.

        Args:
            base_dir: Base directory for file operations
            enable_metrics: Enable metrics collection
            max_file_size: Maximum allowed file size in bytes
        """
        self._manager = FileIOManager(base_dir=base_dir, enable_metrics=enable_metrics)
        self._max_file_size = max_file_size
        self._operation_count = 0

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
        path = Path(path)

        if not await self.exists(path):
            raise FileNotFoundError(f"File not found: {path}")

        try:
            data = await self._manager.read_json(path)
            self._operation_count += 1
            return data
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error reading JSON from {path}: {e}")
            raise

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
        try:
            written_path = await self._manager.write_json(
                path, data, indent=indent, ensure_ascii=ensure_ascii
            )
            self._operation_count += 1
            return written_path
        except Exception as e:
            logger.error(f"Error writing JSON to {path}: {e}")
            raise IOError(f"Failed to write JSON: {e}")

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
        path = Path(path)

        if not await self.exists(path):
            raise FileNotFoundError(f"File not found: {path}")

        try:
            if hasattr(self._manager, "read_yaml"):
                data = await self._manager.read_yaml(path)
            else:
                # Fallback implementation
                content = await self.read_text(path)
                data = await asyncio.to_thread(yaml.safe_load, content)

            self._operation_count += 1
            return data
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML in {path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error reading YAML from {path}: {e}")
            raise

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
        try:
            if hasattr(self._manager, "write_yaml"):
                written_path = await self._manager.write_yaml(
                    path, data, default_flow_style=default_flow_style
                )
            else:
                # Fallback implementation
                yaml_str = await asyncio.to_thread(
                    yaml.dump, data, default_flow_style=default_flow_style
                )
                written_path = await self.write_text(path, yaml_str)

            self._operation_count += 1
            return Path(written_path)
        except Exception as e:
            logger.error(f"Error writing YAML to {path}: {e}")
            raise IOError(f"Failed to write YAML: {e}")

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
        path = Path(path)

        if not await self.exists(path):
            raise FileNotFoundError(f"File not found: {path}")

        try:
            if hasattr(self._manager, "read_text"):
                content = await self._manager.read_text(path, encoding=encoding)
            else:
                # Fallback using aiofiles
                import aiofiles

                async with aiofiles.open(path, "r", encoding=encoding) as f:
                    content = await f.read()

            self._operation_count += 1
            return content
        except UnicodeDecodeError as e:
            logger.error(f"Encoding error reading {path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error reading text from {path}: {e}")
            raise

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
        try:
            if hasattr(self._manager, "write_text"):
                written_path = await self._manager.write_text(
                    path, content, encoding=encoding
                )
            else:
                # Fallback using aiofiles
                import aiofiles

                path = Path(path)
                await self._manager.ensure_dir(path.parent)
                async with aiofiles.open(path, "w", encoding=encoding) as f:
                    await f.write(content)
                written_path = path

            self._operation_count += 1
            return Path(written_path)
        except Exception as e:
            logger.error(f"Error writing text to {path}: {e}")
            raise IOError(f"Failed to write text: {e}")

    async def exists(self, path: Union[str, Path]) -> bool:
        """
        Check if file exists.

        Args:
            path: File path to check

        Returns:
            True if file exists, False otherwise
        """
        path = Path(path)
        return await asyncio.to_thread(path.exists)

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
        path = Path(path)

        try:
            if await self.exists(path):
                await asyncio.to_thread(path.unlink)
                self._operation_count += 1
                logger.debug(f"Deleted file: {path}")
                return True
            return False
        except PermissionError as e:
            logger.error(f"Permission denied deleting {path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error deleting {path}: {e}")
            raise

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
        path = Path(path)

        if not await asyncio.to_thread(path.is_dir):
            raise NotADirectoryError(f"Not a directory: {path}")

        try:
            if recursive:
                glob_pattern = f"**/{pattern}"
                files = await asyncio.to_thread(lambda: list(path.glob(glob_pattern)))
            else:
                files = await asyncio.to_thread(lambda: list(path.glob(pattern)))

            # Filter to only files (not directories)
            files = [f for f in files if f.is_file()]

            self._operation_count += 1
            return files
        except Exception as e:
            logger.error(f"Error listing files in {path}: {e}")
            raise

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
        try:
            created_path = await self._manager.ensure_dir(path)
            self._operation_count += 1
            return created_path
        except PermissionError as e:
            logger.error(f"Permission denied creating directory {path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error ensuring directory {path}: {e}")
            raise

    async def get_metrics(self) -> Dict:
        """
        Get file operation metrics.

        Returns:
            Dictionary containing I/O metrics
        """
        metrics = {
            "total_operations": self._operation_count,
            "max_file_size": self._max_file_size,
        }

        if hasattr(self._manager, "operations") and self._manager.operations:
            recent_ops = self._manager.operations[-100:]  # Last 100 operations

            successful_ops = [op for op in recent_ops if op.success]
            failed_ops = [op for op in recent_ops if not op.success]

            metrics.update(
                {
                    "recent_operations": len(recent_ops),
                    "successful_operations": len(successful_ops),
                    "failed_operations": len(failed_ops),
                    "operation_types": {
                        op_type: sum(1 for op in recent_ops if op.operation == op_type)
                        for op_type in set(op.operation for op in recent_ops)
                    },
                }
            )

            if successful_ops:
                total_size = sum(op.size_bytes or 0 for op in successful_ops)
                metrics["total_bytes_processed"] = total_size

        return metrics
