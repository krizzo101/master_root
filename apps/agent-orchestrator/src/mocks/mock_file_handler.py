"""
Mock FileHandler implementation for testing
"""

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

from ..interfaces.file_handler import IFileHandler


class MockFileHandler(IFileHandler):
    """
    Mock implementation of IFileHandler for testing.
    Stores files in memory instead of disk.
    """

    def __init__(
        self,
        simulate_delays: bool = False,
        failure_rate: float = 0.0,
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
    ):
        """
        Initialize mock file handler.

        Args:
            simulate_delays: Add realistic delays to operations
            failure_rate: Probability of operations failing (0.0-1.0)
            max_file_size: Maximum file size in bytes
        """
        self.files: Dict[str, Any] = {}  # In-memory file storage
        self.simulate_delays = simulate_delays
        self.failure_rate = failure_rate
        self.max_file_size = max_file_size

        # Tracking for assertions
        self.read_count = 0
        self.write_count = 0
        self.delete_count = 0
        self.operation_history: List[Dict] = []

    async def _maybe_fail(self):
        """Simulate random failures for testing error handling"""
        import random

        if random.random() < self.failure_rate:
            raise IOError("Simulated file operation failure")

    async def _maybe_delay(self, min_ms: int = 5, max_ms: int = 30):
        """Add realistic delays if configured"""
        if self.simulate_delays:
            import random

            delay = random.randint(min_ms, max_ms) / 1000
            await asyncio.sleep(delay)

    def _normalize_path(self, path: Union[str, Path]) -> str:
        """Normalize path to string for dictionary key"""
        return str(Path(path).resolve())

    async def read_json(self, path: Union[str, Path]) -> Any:
        """Read JSON from mock storage"""
        await self._maybe_delay()
        await self._maybe_fail()

        path_str = self._normalize_path(path)

        if path_str not in self.files:
            raise FileNotFoundError(f"File not found: {path}")

        content = self.files[path_str]

        if isinstance(content, str):
            try:
                data = json.loads(content)
            except json.JSONDecodeError:
                raise json.JSONDecodeError(f"Invalid JSON in {path}", content, 0)
        else:
            data = content

        self.read_count += 1
        self.operation_history.append(
            {
                "operation": "read_json",
                "path": path_str,
                "success": True,
            }
        )

        return data

    async def write_json(
        self,
        path: Union[str, Path],
        data: Any,
        indent: int = 2,
        ensure_ascii: bool = False,
    ) -> Path:
        """Write JSON to mock storage"""
        await self._maybe_delay()
        await self._maybe_fail()

        path_str = self._normalize_path(path)

        # Serialize to JSON string for storage
        json_str = json.dumps(data, indent=indent, ensure_ascii=ensure_ascii)

        if len(json_str.encode()) > self.max_file_size:
            raise IOError(f"File size exceeds maximum of {self.max_file_size} bytes")

        self.files[path_str] = json_str
        self.write_count += 1

        self.operation_history.append(
            {
                "operation": "write_json",
                "path": path_str,
                "size": len(json_str),
                "success": True,
            }
        )

        return Path(path)

    async def read_yaml(self, path: Union[str, Path]) -> Any:
        """Read YAML from mock storage"""
        await self._maybe_delay()
        await self._maybe_fail()

        path_str = self._normalize_path(path)

        if path_str not in self.files:
            raise FileNotFoundError(f"File not found: {path}")

        content = self.files[path_str]

        if isinstance(content, str):
            try:
                data = yaml.safe_load(content)
            except yaml.YAMLError as e:
                raise yaml.YAMLError(f"Invalid YAML in {path}: {e}")
        else:
            data = content

        self.read_count += 1
        self.operation_history.append(
            {
                "operation": "read_yaml",
                "path": path_str,
                "success": True,
            }
        )

        return data

    async def write_yaml(
        self, path: Union[str, Path], data: Any, default_flow_style: bool = False
    ) -> Path:
        """Write YAML to mock storage"""
        await self._maybe_delay()
        await self._maybe_fail()

        path_str = self._normalize_path(path)

        # Serialize to YAML string for storage
        yaml_str = yaml.dump(data, default_flow_style=default_flow_style)

        if len(yaml_str.encode()) > self.max_file_size:
            raise IOError(f"File size exceeds maximum of {self.max_file_size} bytes")

        self.files[path_str] = yaml_str
        self.write_count += 1

        self.operation_history.append(
            {
                "operation": "write_yaml",
                "path": path_str,
                "size": len(yaml_str),
                "success": True,
            }
        )

        return Path(path)

    async def read_text(self, path: Union[str, Path], encoding: str = "utf-8") -> str:
        """Read text from mock storage"""
        await self._maybe_delay()
        await self._maybe_fail()

        path_str = self._normalize_path(path)

        if path_str not in self.files:
            raise FileNotFoundError(f"File not found: {path}")

        content = self.files[path_str]

        if not isinstance(content, str):
            content = str(content)

        self.read_count += 1
        self.operation_history.append(
            {
                "operation": "read_text",
                "path": path_str,
                "encoding": encoding,
                "success": True,
            }
        )

        return content

    async def write_text(
        self, path: Union[str, Path], content: str, encoding: str = "utf-8"
    ) -> Path:
        """Write text to mock storage"""
        await self._maybe_delay()
        await self._maybe_fail()

        path_str = self._normalize_path(path)

        if len(content.encode(encoding)) > self.max_file_size:
            raise IOError(f"File size exceeds maximum of {self.max_file_size} bytes")

        self.files[path_str] = content
        self.write_count += 1

        self.operation_history.append(
            {
                "operation": "write_text",
                "path": path_str,
                "size": len(content),
                "encoding": encoding,
                "success": True,
            }
        )

        return Path(path)

    async def exists(self, path: Union[str, Path]) -> bool:
        """Check if file exists in mock storage"""
        await self._maybe_delay(2, 10)

        path_str = self._normalize_path(path)
        return path_str in self.files

    async def delete(self, path: Union[str, Path]) -> bool:
        """Delete file from mock storage"""
        await self._maybe_delay()
        await self._maybe_fail()

        path_str = self._normalize_path(path)

        if path_str in self.files:
            del self.files[path_str]
            self.delete_count += 1

            self.operation_history.append(
                {
                    "operation": "delete",
                    "path": path_str,
                    "success": True,
                }
            )

            return True

        return False

    async def list_files(
        self, path: Union[str, Path], pattern: str = "*", recursive: bool = False
    ) -> List[Path]:
        """List files in mock storage"""
        await self._maybe_delay()
        await self._maybe_fail()

        path_str = self._normalize_path(path)
        matched_files = []

        for file_path in self.files.keys():
            file_path_obj = Path(file_path)

            # Check if file is under the specified path
            try:
                file_path_obj.relative_to(path_str)
            except ValueError:
                continue

            # Check pattern matching
            if pattern != "*":
                import fnmatch

                if not fnmatch.fnmatch(file_path_obj.name, pattern):
                    continue

            # Check recursion
            if not recursive:
                # Only include direct children
                rel_path = file_path_obj.relative_to(path_str)
                if len(rel_path.parts) > 1:
                    continue

            matched_files.append(file_path_obj)

        self.operation_history.append(
            {
                "operation": "list_files",
                "path": path_str,
                "pattern": pattern,
                "recursive": recursive,
                "count": len(matched_files),
                "success": True,
            }
        )

        return matched_files

    async def ensure_dir(self, path: Union[str, Path]) -> Path:
        """Mock directory creation (no-op in memory storage)"""
        await self._maybe_delay(5, 15)
        await self._maybe_fail()

        path_obj = Path(path)

        self.operation_history.append(
            {
                "operation": "ensure_dir",
                "path": str(path_obj),
                "success": True,
            }
        )

        return path_obj

    async def get_metrics(self) -> Dict:
        """Get mock metrics for testing"""
        await self._maybe_delay(5, 10)

        total_size = sum(
            len(content.encode() if isinstance(content, str) else str(content).encode())
            for content in self.files.values()
        )

        return {
            "total_files": len(self.files),
            "total_size_bytes": total_size,
            "read_operations": self.read_count,
            "write_operations": self.write_count,
            "delete_operations": self.delete_count,
            "total_operations": len(self.operation_history),
            "max_file_size": self.max_file_size,
            "simulated_delays": self.simulate_delays,
            "failure_rate": self.failure_rate,
        }

    # Testing utility methods

    def reset(self):
        """Reset mock to initial state for testing"""
        self.files.clear()
        self.read_count = 0
        self.write_count = 0
        self.delete_count = 0
        self.operation_history.clear()

    def set_file(self, path: Union[str, Path], content: Any):
        """Directly set file content for testing"""
        path_str = self._normalize_path(path)
        self.files[path_str] = content

    def get_file(self, path: Union[str, Path]) -> Optional[Any]:
        """Directly get file content for testing"""
        path_str = self._normalize_path(path)
        return self.files.get(path_str)

    def get_all_files(self) -> Dict[str, Any]:
        """Get all files for testing assertions"""
        return self.files.copy()

    def get_operation_history(self) -> List[Dict]:
        """Get operation history for assertions"""
        return self.operation_history.copy()
