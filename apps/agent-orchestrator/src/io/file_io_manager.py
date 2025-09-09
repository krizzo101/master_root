#!/usr/bin/env python3
"""
Async File I/O Manager for Agent Orchestrator
Centralizes all async file operations using aiofiles for better performance
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import aiofiles
import yaml

logger = logging.getLogger(__name__)


@dataclass
class FileOperation:
    """Tracks file operation metrics"""

    operation: str
    file_path: Path
    start_time: float
    end_time: Optional[float] = None
    size_bytes: Optional[int] = None
    success: bool = True
    error: Optional[str] = None


class FileIOManager:
    """
    Centralized async file I/O operations manager.
    Provides async methods for common file operations with performance tracking.
    """

    def __init__(self, base_dir: Optional[Path] = None, enable_metrics: bool = True):
        """
        Initialize the FileIOManager.

        Args:
            base_dir: Base directory for relative path operations
            enable_metrics: Enable operation metrics tracking
        """
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        self.enable_metrics = enable_metrics
        self.operations: List[FileOperation] = []
        self._lock = asyncio.Lock()

    def _resolve_path(self, path: Union[str, Path]) -> Path:
        """Resolve path relative to base_dir if not absolute"""
        path = Path(path)
        if not path.is_absolute():
            path = self.base_dir / path
        return path

    async def _track_operation(self, operation: FileOperation):
        """Track file operation metrics"""
        if self.enable_metrics:
            async with self._lock:
                self.operations.append(operation)
                # Keep only last 1000 operations
                if len(self.operations) > 1000:
                    self.operations = self.operations[-1000:]

    async def ensure_dir(self, path: Union[str, Path]) -> Path:
        """Ensure directory exists (async-safe)"""
        path = self._resolve_path(path)

        # Use asyncio.to_thread for thread-safe directory creation
        await asyncio.to_thread(path.mkdir, parents=True, exist_ok=True)
        return path

    async def write_json(
        self,
        path: Union[str, Path],
        data: Any,
        indent: int = 2,
        ensure_ascii: bool = False,
        default: Optional[Any] = str,
    ) -> Path:
        """
        Write JSON data to file asynchronously.

        Args:
            path: File path to write to
            data: Data to serialize as JSON
            indent: JSON indentation level
            ensure_ascii: Ensure ASCII encoding
            default: Default serializer for non-JSON types

        Returns:
            Path to written file
        """
        path = self._resolve_path(path)
        op = FileOperation("write_json", path, asyncio.get_event_loop().time())

        try:
            # Ensure parent directory exists
            await self.ensure_dir(path.parent)

            # Serialize JSON first (CPU-bound)
            json_str = await asyncio.to_thread(
                json.dumps,
                data,
                indent=indent,
                ensure_ascii=ensure_ascii,
                default=default,
            )

            # Write asynchronously
            async with aiofiles.open(path, "w", encoding="utf-8") as f:
                await f.write(json_str)

            op.size_bytes = len(json_str.encode("utf-8"))
            op.end_time = asyncio.get_event_loop().time()

            logger.debug(f"Wrote JSON to {path} ({op.size_bytes} bytes)")

        except Exception as e:
            op.success = False
            op.error = str(e)
            op.end_time = asyncio.get_event_loop().time()
            logger.error(f"Failed to write JSON to {path}: {e}")
            raise

        finally:
            await self._track_operation(op)

        return path

    async def read_json(self, path: Union[str, Path]) -> Any:
        """
        Read JSON data from file asynchronously.

        Args:
            path: File path to read from

        Returns:
            Parsed JSON data
        """
        path = self._resolve_path(path)
        op = FileOperation("read_json", path, asyncio.get_event_loop().time())

        try:
            async with aiofiles.open(path, "r", encoding="utf-8") as f:
                content = await f.read()

            # Parse JSON (CPU-bound)
            data = await asyncio.to_thread(json.loads, content)

            op.size_bytes = len(content.encode("utf-8"))
            op.end_time = asyncio.get_event_loop().time()

            logger.debug(f"Read JSON from {path} ({op.size_bytes} bytes)")
            return data

        except Exception as e:
            op.success = False
            op.error = str(e)
            op.end_time = asyncio.get_event_loop().time()
            logger.error(f"Failed to read JSON from {path}: {e}")
            raise

        finally:
            await self._track_operation(op)

    async def write_text(
        self, path: Union[str, Path], content: str, encoding: str = "utf-8"
    ) -> Path:
        """
        Write text content to file asynchronously.

        Args:
            path: File path to write to
            content: Text content to write
            encoding: Text encoding

        Returns:
            Path to written file
        """
        path = self._resolve_path(path)
        op = FileOperation("write_text", path, asyncio.get_event_loop().time())

        try:
            # Ensure parent directory exists
            await self.ensure_dir(path.parent)

            async with aiofiles.open(path, "w", encoding=encoding) as f:
                await f.write(content)

            op.size_bytes = len(content.encode(encoding))
            op.end_time = asyncio.get_event_loop().time()

            logger.debug(f"Wrote text to {path} ({op.size_bytes} bytes)")

        except Exception as e:
            op.success = False
            op.error = str(e)
            op.end_time = asyncio.get_event_loop().time()
            logger.error(f"Failed to write text to {path}: {e}")
            raise

        finally:
            await self._track_operation(op)

        return path

    async def read_text(self, path: Union[str, Path], encoding: str = "utf-8") -> str:
        """
        Read text content from file asynchronously.

        Args:
            path: File path to read from
            encoding: Text encoding

        Returns:
            File content as string
        """
        path = self._resolve_path(path)
        op = FileOperation("read_text", path, asyncio.get_event_loop().time())

        try:
            async with aiofiles.open(path, "r", encoding=encoding) as f:
                content = await f.read()

            op.size_bytes = len(content.encode(encoding))
            op.end_time = asyncio.get_event_loop().time()

            logger.debug(f"Read text from {path} ({op.size_bytes} bytes)")
            return content

        except Exception as e:
            op.success = False
            op.error = str(e)
            op.end_time = asyncio.get_event_loop().time()
            logger.error(f"Failed to read text from {path}: {e}")
            raise

        finally:
            await self._track_operation(op)

    async def append_text(
        self, path: Union[str, Path], content: str, encoding: str = "utf-8"
    ) -> Path:
        """
        Append text to file asynchronously.

        Args:
            path: File path to append to
            content: Text content to append
            encoding: Text encoding

        Returns:
            Path to file
        """
        path = self._resolve_path(path)
        op = FileOperation("append_text", path, asyncio.get_event_loop().time())

        try:
            # Ensure parent directory exists
            await self.ensure_dir(path.parent)

            async with aiofiles.open(path, "a", encoding=encoding) as f:
                await f.write(content)

            op.size_bytes = len(content.encode(encoding))
            op.end_time = asyncio.get_event_loop().time()

            logger.debug(f"Appended to {path} ({op.size_bytes} bytes)")

        except Exception as e:
            op.success = False
            op.error = str(e)
            op.end_time = asyncio.get_event_loop().time()
            logger.error(f"Failed to append to {path}: {e}")
            raise

        finally:
            await self._track_operation(op)

        return path

    async def write_yaml(
        self, path: Union[str, Path], data: Any, default_flow_style: bool = False
    ) -> Path:
        """
        Write YAML data to file asynchronously.

        Args:
            path: File path to write to
            data: Data to serialize as YAML
            default_flow_style: YAML flow style

        Returns:
            Path to written file
        """
        path = self._resolve_path(path)
        op = FileOperation("write_yaml", path, asyncio.get_event_loop().time())

        try:
            # Ensure parent directory exists
            await self.ensure_dir(path.parent)

            # Serialize YAML (CPU-bound)
            yaml_str = await asyncio.to_thread(
                yaml.dump, data, default_flow_style=default_flow_style
            )

            async with aiofiles.open(path, "w", encoding="utf-8") as f:
                await f.write(yaml_str)

            op.size_bytes = len(yaml_str.encode("utf-8"))
            op.end_time = asyncio.get_event_loop().time()

            logger.debug(f"Wrote YAML to {path} ({op.size_bytes} bytes)")

        except Exception as e:
            op.success = False
            op.error = str(e)
            op.end_time = asyncio.get_event_loop().time()
            logger.error(f"Failed to write YAML to {path}: {e}")
            raise

        finally:
            await self._track_operation(op)

        return path

    async def read_yaml(self, path: Union[str, Path]) -> Any:
        """
        Read YAML data from file asynchronously.

        Args:
            path: File path to read from

        Returns:
            Parsed YAML data
        """
        path = self._resolve_path(path)
        op = FileOperation("read_yaml", path, asyncio.get_event_loop().time())

        try:
            async with aiofiles.open(path, "r", encoding="utf-8") as f:
                content = await f.read()

            # Parse YAML (CPU-bound)
            data = await asyncio.to_thread(yaml.safe_load, content)

            op.size_bytes = len(content.encode("utf-8"))
            op.end_time = asyncio.get_event_loop().time()

            logger.debug(f"Read YAML from {path} ({op.size_bytes} bytes)")
            return data

        except Exception as e:
            op.success = False
            op.error = str(e)
            op.end_time = asyncio.get_event_loop().time()
            logger.error(f"Failed to read YAML from {path}: {e}")
            raise

        finally:
            await self._track_operation(op)

    async def exists(self, path: Union[str, Path]) -> bool:
        """Check if file exists (async-safe)"""
        path = self._resolve_path(path)
        return await asyncio.to_thread(path.exists)

    async def delete(self, path: Union[str, Path]) -> bool:
        """
        Delete file asynchronously.

        Args:
            path: File path to delete

        Returns:
            True if deleted, False if didn't exist
        """
        path = self._resolve_path(path)
        op = FileOperation("delete", path, asyncio.get_event_loop().time())

        try:
            if await self.exists(path):
                await asyncio.to_thread(path.unlink)
                op.end_time = asyncio.get_event_loop().time()
                logger.debug(f"Deleted {path}")
                return True
            else:
                op.end_time = asyncio.get_event_loop().time()
                return False

        except Exception as e:
            op.success = False
            op.error = str(e)
            op.end_time = asyncio.get_event_loop().time()
            logger.error(f"Failed to delete {path}: {e}")
            raise

        finally:
            await self._track_operation(op)

    async def copy(self, src: Union[str, Path], dst: Union[str, Path]) -> Path:
        """
        Copy file asynchronously.

        Args:
            src: Source file path
            dst: Destination file path

        Returns:
            Path to destination file
        """
        src = self._resolve_path(src)
        dst = self._resolve_path(dst)
        op = FileOperation("copy", src, asyncio.get_event_loop().time())

        try:
            # Ensure destination directory exists
            await self.ensure_dir(dst.parent)

            # Read and write in chunks for memory efficiency
            async with aiofiles.open(src, "rb") as fsrc:
                async with aiofiles.open(dst, "wb") as fdst:
                    chunk_size = 64 * 1024  # 64KB chunks
                    total_bytes = 0
                    while True:
                        chunk = await fsrc.read(chunk_size)
                        if not chunk:
                            break
                        await fdst.write(chunk)
                        total_bytes += len(chunk)

            op.size_bytes = total_bytes
            op.end_time = asyncio.get_event_loop().time()

            logger.debug(f"Copied {src} to {dst} ({op.size_bytes} bytes)")
            return dst

        except Exception as e:
            op.success = False
            op.error = str(e)
            op.end_time = asyncio.get_event_loop().time()
            logger.error(f"Failed to copy {src} to {dst}: {e}")
            raise

        finally:
            await self._track_operation(op)

    async def batch_write_json(
        self, files: Dict[Union[str, Path], Any], **kwargs
    ) -> List[Path]:
        """
        Write multiple JSON files concurrently.

        Args:
            files: Dictionary mapping file paths to data
            **kwargs: Additional arguments for write_json

        Returns:
            List of written file paths
        """
        tasks = [self.write_json(path, data, **kwargs) for path, data in files.items()]
        return await asyncio.gather(*tasks)

    async def batch_read_json(self, paths: List[Union[str, Path]]) -> List[Any]:
        """
        Read multiple JSON files concurrently.

        Args:
            paths: List of file paths to read

        Returns:
            List of parsed JSON data
        """
        tasks = [self.read_json(path) for path in paths]
        return await asyncio.gather(*tasks)

    def get_metrics(self) -> Dict[str, Any]:
        """Get I/O operation metrics"""
        if not self.enable_metrics or not self.operations:
            return {}

        total_ops = len(self.operations)
        successful_ops = sum(1 for op in self.operations if op.success)
        failed_ops = total_ops - successful_ops

        # Calculate average operation times by type
        op_times = {}
        for op in self.operations:
            if op.end_time:
                duration = op.end_time - op.start_time
                if op.operation not in op_times:
                    op_times[op.operation] = []
                op_times[op.operation].append(duration)

        avg_times = {
            op_type: sum(times) / len(times) for op_type, times in op_times.items()
        }

        # Calculate total bytes processed
        total_bytes = sum(
            op.size_bytes for op in self.operations if op.size_bytes is not None
        )

        return {
            "total_operations": total_ops,
            "successful_operations": successful_ops,
            "failed_operations": failed_ops,
            "success_rate": successful_ops / total_ops if total_ops > 0 else 0,
            "average_operation_times": avg_times,
            "total_bytes_processed": total_bytes,
            "operations_by_type": {
                op_type: sum(1 for op in self.operations if op.operation == op_type)
                for op_type in set(op.operation for op in self.operations)
            },
        }

    async def save_checkpoint(
        self,
        checkpoint_dir: Union[str, Path],
        checkpoint_data: Dict[str, Any],
        checkpoint_id: Optional[str] = None,
    ) -> Path:
        """
        Save a checkpoint file with automatic naming.

        Args:
            checkpoint_dir: Directory to save checkpoint in
            checkpoint_data: Data to save in checkpoint
            checkpoint_id: Optional checkpoint ID (auto-generated if not provided)

        Returns:
            Path to saved checkpoint file
        """
        checkpoint_dir = self._resolve_path(checkpoint_dir)
        await self.ensure_dir(checkpoint_dir)

        if not checkpoint_id:
            checkpoint_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        checkpoint_file = checkpoint_dir / f"checkpoint_{checkpoint_id}.json"

        # Add metadata
        checkpoint_data["_metadata"] = {
            "checkpoint_id": checkpoint_id,
            "timestamp": datetime.now().isoformat(),
            "version": "1.0",
        }

        await self.write_json(checkpoint_file, checkpoint_data)
        logger.info(f"Saved checkpoint: {checkpoint_file}")

        return checkpoint_file

    async def load_checkpoint(
        self, checkpoint_path: Union[str, Path]
    ) -> Dict[str, Any]:
        """
        Load a checkpoint file.

        Args:
            checkpoint_path: Path to checkpoint file

        Returns:
            Checkpoint data
        """
        checkpoint_path = self._resolve_path(checkpoint_path)

        if not await self.exists(checkpoint_path):
            raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")

        data = await self.read_json(checkpoint_path)
        logger.info(f"Loaded checkpoint: {checkpoint_path}")

        return data

    async def cleanup_old_checkpoints(
        self, checkpoint_dir: Union[str, Path], keep_count: int = 10
    ) -> List[Path]:
        """
        Clean up old checkpoint files, keeping only the most recent ones.

        Args:
            checkpoint_dir: Directory containing checkpoints
            keep_count: Number of checkpoints to keep

        Returns:
            List of deleted checkpoint paths
        """
        checkpoint_dir = self._resolve_path(checkpoint_dir)

        if not await self.exists(checkpoint_dir):
            return []

        # Get all checkpoint files
        checkpoints = await asyncio.to_thread(
            lambda: sorted(
                checkpoint_dir.glob("checkpoint_*.json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
        )

        deleted = []
        if len(checkpoints) > keep_count:
            to_delete = checkpoints[keep_count:]
            for checkpoint in to_delete:
                await self.delete(checkpoint)
                deleted.append(checkpoint)
                logger.info(f"Deleted old checkpoint: {checkpoint}")

        return deleted


# Singleton instance for global use
_global_io_manager: Optional[FileIOManager] = None


def get_io_manager(base_dir: Optional[Path] = None) -> FileIOManager:
    """Get or create global FileIOManager instance"""
    global _global_io_manager
    if _global_io_manager is None:
        _global_io_manager = FileIOManager(base_dir)
    return _global_io_manager


async def init_io_manager(base_dir: Optional[Path] = None) -> FileIOManager:
    """Initialize global FileIOManager instance (async)"""
    global _global_io_manager
    _global_io_manager = FileIOManager(base_dir)
    return _global_io_manager
