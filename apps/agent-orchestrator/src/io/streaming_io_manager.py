#!/usr/bin/env python3
"""
Streaming File I/O Manager for Memory-Efficient Operations
Implements chunked reading/writing and streaming JSON processing
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any, AsyncIterator, Dict, Optional, Union

import aiofiles
import ijson  # For streaming JSON parsing

logger = logging.getLogger(__name__)


class StreamingIOManager:
    """
    Memory-efficient streaming I/O operations.
    Processes large files in chunks without loading entire content into memory.
    """

    def __init__(
        self,
        base_dir: Optional[Path] = None,
        chunk_size: int = 8192,  # 8KB chunks
        max_memory_buffer: int = 10 * 1024 * 1024,  # 10MB max buffer
    ):
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        self.chunk_size = chunk_size
        self.max_memory_buffer = max_memory_buffer

    def _resolve_path(self, path: Union[str, Path]) -> Path:
        """Resolve path relative to base_dir"""
        path = Path(path)
        if not path.is_absolute():
            path = self.base_dir / path
        return path

    async def write_json_streaming(
        self, path: Union[str, Path], data: Any, chunk_size: Optional[int] = None
    ) -> Path:
        """
        Write JSON data to file in chunks to avoid memory spikes.

        Args:
            path: File path to write to
            data: Data to serialize (can be generator/iterator)
            chunk_size: Size of chunks to write

        Returns:
            Path to written file
        """
        path = self._resolve_path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        chunk_size = chunk_size or self.chunk_size

        async with aiofiles.open(path, "wb") as f:
            # Start JSON array if data is iterable
            if hasattr(data, "__iter__") and not isinstance(data, (str, dict)):
                await f.write(b"[\n")
                first = True

                for item in data:
                    if not first:
                        await f.write(b",\n")
                    first = False

                    # Serialize item
                    item_json = json.dumps(item).encode("utf-8")

                    # Write in chunks if large
                    if len(item_json) > chunk_size:
                        for i in range(0, len(item_json), chunk_size):
                            chunk = item_json[i : i + chunk_size]
                            await f.write(chunk)
                            # Yield control periodically
                            await asyncio.sleep(0)
                    else:
                        await f.write(item_json)

                await f.write(b"\n]")
            else:
                # Regular JSON serialization for non-iterables
                json_bytes = json.dumps(data, indent=2).encode("utf-8")

                # Write in chunks
                for i in range(0, len(json_bytes), chunk_size):
                    chunk = json_bytes[i : i + chunk_size]
                    await f.write(chunk)
                    await asyncio.sleep(0)  # Yield control

        logger.debug(f"Streamed JSON to {path}")
        return path

    async def read_json_streaming(self, path: Union[str, Path]) -> AsyncIterator[Any]:
        """
        Stream JSON array elements without loading entire file.

        Args:
            path: File path to read from

        Yields:
            Individual JSON array elements
        """
        path = self._resolve_path(path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        # Use ijson for streaming JSON parsing
        async with aiofiles.open(path, "rb") as f:
            # Create parser for array items
            parser = ijson.items(f, "item")

            async for item in parser:
                yield item
                # Allow other tasks to run
                await asyncio.sleep(0)

    async def read_json_chunked(
        self, path: Union[str, Path], max_size: Optional[int] = None
    ) -> Any:
        """
        Read JSON file with size limits to prevent memory overflow.

        Args:
            path: File path to read
            max_size: Maximum file size to read (bytes)

        Returns:
            Parsed JSON data

        Raises:
            ValueError: If file exceeds max_size
        """
        path = self._resolve_path(path)
        max_size = max_size or self.max_memory_buffer

        # Check file size first
        file_size = path.stat().st_size
        if file_size > max_size:
            raise ValueError(
                f"File {path} size ({file_size} bytes) exceeds "
                f"max size ({max_size} bytes)"
            )

        # Read in chunks and accumulate
        chunks = []
        bytes_read = 0

        async with aiofiles.open(path, "rb") as f:
            while bytes_read < file_size:
                chunk_size = min(self.chunk_size, file_size - bytes_read)
                chunk = await f.read(chunk_size)
                if not chunk:
                    break

                chunks.append(chunk)
                bytes_read += len(chunk)

                # Yield control periodically
                await asyncio.sleep(0)

        # Combine chunks and parse
        content = b"".join(chunks)
        return json.loads(content.decode("utf-8"))

    async def write_lines_streaming(
        self, path: Union[str, Path], lines: AsyncIterator[str], buffer_size: int = 100
    ) -> Path:
        """
        Write lines to file with buffering for efficiency.

        Args:
            path: File path to write to
            lines: Async iterator of lines
            buffer_size: Number of lines to buffer before writing

        Returns:
            Path to written file
        """
        path = self._resolve_path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        buffer = []
        line_count = 0

        async with aiofiles.open(path, "w", encoding="utf-8") as f:
            async for line in lines:
                buffer.append(line)
                line_count += 1

                # Write buffer when full
                if len(buffer) >= buffer_size:
                    await f.write("\n".join(buffer) + "\n")
                    buffer.clear()

                    # Log progress periodically
                    if line_count % 1000 == 0:
                        logger.debug(f"Written {line_count} lines to {path}")

                    # Yield control
                    await asyncio.sleep(0)

            # Write remaining buffer
            if buffer:
                await f.write("\n".join(buffer) + "\n")

        logger.debug(f"Streamed {line_count} lines to {path}")
        return path

    async def read_lines_streaming(
        self, path: Union[str, Path], skip_empty: bool = True
    ) -> AsyncIterator[str]:
        """
        Stream lines from file without loading entire content.

        Args:
            path: File path to read from
            skip_empty: Skip empty lines

        Yields:
            Individual lines from the file
        """
        path = self._resolve_path(path)

        async with aiofiles.open(path, "r", encoding="utf-8") as f:
            async for line in f:
                line = line.rstrip("\n\r")
                if not skip_empty or line:
                    yield line
                    # Yield control periodically
                    await asyncio.sleep(0)

    async def copy_file_streaming(
        self,
        source: Union[str, Path],
        dest: Union[str, Path],
        chunk_size: Optional[int] = None,
    ) -> Path:
        """
        Copy file using streaming to minimize memory usage.

        Args:
            source: Source file path
            dest: Destination file path
            chunk_size: Size of chunks to copy

        Returns:
            Path to destination file
        """
        source = self._resolve_path(source)
        dest = self._resolve_path(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        chunk_size = chunk_size or self.chunk_size

        bytes_copied = 0

        async with aiofiles.open(source, "rb") as src:
            async with aiofiles.open(dest, "wb") as dst:
                while True:
                    chunk = await src.read(chunk_size)
                    if not chunk:
                        break

                    await dst.write(chunk)
                    bytes_copied += len(chunk)

                    # Log progress for large files
                    if bytes_copied % (100 * chunk_size) == 0:
                        logger.debug(
                            f"Copied {bytes_copied / 1024 / 1024:.1f}MB "
                            f"from {source} to {dest}"
                        )

                    # Yield control
                    await asyncio.sleep(0)

        logger.debug(f"Copied {bytes_copied} bytes from {source} to {dest}")
        return dest

    async def append_json_streaming(
        self, path: Union[str, Path], new_item: Any
    ) -> None:
        """
        Append item to JSON array file without loading entire array.

        Args:
            path: Path to JSON array file
            new_item: Item to append
        """
        path = self._resolve_path(path)

        if not path.exists():
            # Create new array file
            await self.write_json_streaming(path, [new_item])
            return

        # Create temporary file
        temp_path = path.with_suffix(".tmp")

        # Stream existing items and append new one
        async def generate_items():
            # Yield existing items
            async for item in self.read_json_streaming(path):
                yield item
            # Yield new item
            yield new_item

        # Write to temp file
        await self.write_json_streaming(temp_path, generate_items())

        # Atomic replace
        temp_path.replace(path)

        logger.debug(f"Appended item to {path}")

    async def get_file_info(self, path: Union[str, Path]) -> Dict:
        """
        Get file information without reading content.

        Args:
            path: File path

        Returns:
            Dictionary with file information
        """
        path = self._resolve_path(path)

        if not path.exists():
            return {"exists": False}

        stat = path.stat()
        return {
            "exists": True,
            "size_bytes": stat.st_size,
            "size_mb": stat.st_size / 1024 / 1024,
            "modified": stat.st_mtime,
            "created": stat.st_ctime,
            "is_file": path.is_file(),
            "is_dir": path.is_dir(),
        }


class ChunkedJSONWriter:
    """Context manager for writing large JSON structures in chunks"""

    def __init__(self, path: Path, chunk_size: int = 8192):
        self.path = path
        self.chunk_size = chunk_size
        self.file = None
        self.first_item = True

    async def __aenter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.file = await aiofiles.open(self.path, "w", encoding="utf-8")
        await self.file.write("[\n")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.file:
            await self.file.write("\n]")
            await self.file.close()

    async def write_item(self, item: Any):
        """Write a single item to the JSON array"""
        if not self.first_item:
            await self.file.write(",\n")
        self.first_item = False

        item_json = json.dumps(item, indent=2)

        # Write in chunks if large
        if len(item_json) > self.chunk_size:
            for i in range(0, len(item_json), self.chunk_size):
                chunk = item_json[i : i + self.chunk_size]
                await self.file.write(chunk)
                await asyncio.sleep(0)
        else:
            await self.file.write(item_json)


class StreamingResultProcessor:
    """Process task results as they stream in without accumulating in memory"""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.summary_file = output_dir / "streaming_summary.json"
        self.stats = {"total": 0, "completed": 0, "failed": 0, "total_size_mb": 0}

    async def process_result(self, result: Dict) -> None:
        """Process a single result without keeping it in memory"""
        self.stats["total"] += 1

        if result.get("status") == "completed":
            self.stats["completed"] += 1
        elif result.get("status") == "failed":
            self.stats["failed"] += 1

        # Estimate size
        size_mb = len(json.dumps(result).encode("utf-8")) / 1024 / 1024
        self.stats["total_size_mb"] += size_mb

        # Save individual result
        result_file = (
            self.output_dir
            / "streamed_results"
            / f"{result.get('task_id', 'unknown')}.json"
        )
        result_file.parent.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(result_file, "w") as f:
            await f.write(json.dumps(result, indent=2))

        # Update summary
        async with aiofiles.open(self.summary_file, "w") as f:
            await f.write(json.dumps(self.stats, indent=2))

        logger.debug(
            f"Processed result {result.get('task_id')}: "
            f"{self.stats['completed']}/{self.stats['total']} completed"
        )
