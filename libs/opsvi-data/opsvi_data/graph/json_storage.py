"""
JSONStorageAdapter - JSON file storage implementation
Provides async file operations with error handling and validation
"""

import json
from pathlib import Path
from typing import Any

import aiofiles

from ..core.config import SKGConfig
from ..core.exceptions import StorageError


class JSONStorageAdapter:
    """
    Adapter for JSON file storage operations
    Provides async file I/O with proper error handling
    """

    def __init__(self, config: SKGConfig):
        self.config = config
        self.encoding = "utf-8"
        self.indent = 2

    async def read_json(self, file_path: Path) -> dict[str, Any]:
        """
        Read and parse JSON file asynchronously
        """
        try:
            if not file_path.exists():
                raise StorageError(
                    f"File not found: {file_path}",
                    file_path=str(file_path),
                    operation="read",
                )

            async with aiofiles.open(file_path, encoding=self.encoding) as f:
                content = await f.read()

            if not content.strip():
                raise StorageError(
                    f"File is empty: {file_path}",
                    file_path=str(file_path),
                    operation="read",
                )

            try:
                data = json.loads(content)
                return data
            except json.JSONDecodeError as e:
                raise StorageError(
                    f"Invalid JSON in file {file_path}: {str(e)}",
                    file_path=str(file_path),
                    operation="read",
                    details={"json_error": str(e)},
                )

        except StorageError:
            raise
        except Exception as e:
            raise StorageError(
                f"Failed to read file {file_path}: {str(e)}",
                file_path=str(file_path),
                operation="read",
            )

    async def write_json(
        self, file_path: Path, data: dict[str, Any], create_dirs: bool = True
    ) -> None:
        """
        Write data to JSON file asynchronously
        """
        try:
            # Create parent directories if needed
            if create_dirs:
                file_path.parent.mkdir(parents=True, exist_ok=True)

            # Validate data can be serialized
            try:
                json_content = json.dumps(
                    data,
                    indent=self.indent,
                    ensure_ascii=False,
                    default=self._json_serializer,
                )
            except (TypeError, ValueError) as e:
                raise StorageError(
                    f"Data cannot be serialized to JSON: {str(e)}",
                    file_path=str(file_path),
                    operation="write",
                    details={"serialization_error": str(e)},
                )

            # Write to temporary file first for atomic operation
            temp_path = file_path.with_suffix(f"{file_path.suffix}.tmp")

            try:
                async with aiofiles.open(temp_path, "w", encoding=self.encoding) as f:
                    await f.write(json_content)

                # Atomic move to final location
                temp_path.replace(file_path)

            except Exception as e:
                # Clean up temporary file if it exists
                if temp_path.exists():
                    temp_path.unlink()
                raise e

        except StorageError:
            raise
        except Exception as e:
            raise StorageError(
                f"Failed to write file {file_path}: {str(e)}",
                file_path=str(file_path),
                operation="write",
            )

    async def read_json_list(self, file_path: Path) -> list[dict[str, Any]]:
        """
        Read JSON file expecting a list of objects
        """
        try:
            data = await self.read_json(file_path)

            if not isinstance(data, list):
                raise StorageError(
                    f"Expected list in JSON file, got {type(data).__name__}",
                    file_path=str(file_path),
                    operation="read_list",
                )

            return data

        except StorageError:
            raise
        except Exception as e:
            raise StorageError(
                f"Failed to read JSON list from {file_path}: {str(e)}",
                file_path=str(file_path),
                operation="read_list",
            )

    async def write_json_list(
        self, file_path: Path, data_list: list[dict[str, Any]], create_dirs: bool = True
    ) -> None:
        """
        Write list of objects to JSON file
        """
        try:
            if not isinstance(data_list, list):
                raise StorageError(
                    f"Expected list, got {type(data_list).__name__}",
                    file_path=str(file_path),
                    operation="write_list",
                )

            await self.write_json(file_path, data_list, create_dirs)

        except StorageError:
            raise
        except Exception as e:
            raise StorageError(
                f"Failed to write JSON list to {file_path}: {str(e)}",
                file_path=str(file_path),
                operation="write_list",
            )

    async def append_to_json_list(
        self, file_path: Path, new_item: dict[str, Any]
    ) -> None:
        """
        Append an item to a JSON list file
        """
        try:
            # Read existing list or create empty one
            if file_path.exists():
                data_list = await self.read_json_list(file_path)
            else:
                data_list = []

            # Append new item
            data_list.append(new_item)

            # Write back to file
            await self.write_json_list(file_path, data_list)

        except StorageError:
            raise
        except Exception as e:
            raise StorageError(
                f"Failed to append to JSON list {file_path}: {str(e)}",
                file_path=str(file_path),
                operation="append_list",
            )

    async def update_json_list_item(
        self,
        file_path: Path,
        item_id: str,
        updated_item: dict[str, Any],
        id_field: str = "id",
    ) -> bool:
        """
        Update an item in a JSON list file by ID
        """
        try:
            if not file_path.exists():
                return False

            data_list = await self.read_json_list(file_path)

            # Find and update the item
            for i, item in enumerate(data_list):
                if item.get(id_field) == item_id:
                    data_list[i] = updated_item
                    await self.write_json_list(file_path, data_list)
                    return True

            return False

        except StorageError:
            raise
        except Exception as e:
            raise StorageError(
                f"Failed to update item in JSON list {file_path}: {str(e)}",
                file_path=str(file_path),
                operation="update_list_item",
            )

    async def remove_from_json_list(
        self, file_path: Path, item_id: str, id_field: str = "id"
    ) -> bool:
        """
        Remove an item from a JSON list file by ID
        """
        try:
            if not file_path.exists():
                return False

            data_list = await self.read_json_list(file_path)

            # Find and remove the item
            for i, item in enumerate(data_list):
                if item.get(id_field) == item_id:
                    data_list.pop(i)
                    await self.write_json_list(file_path, data_list)
                    return True

            return False

        except StorageError:
            raise
        except Exception as e:
            raise StorageError(
                f"Failed to remove item from JSON list {file_path}: {str(e)}",
                file_path=str(file_path),
                operation="remove_list_item",
            )

    async def file_exists(self, file_path: Path) -> bool:
        """
        Check if file exists asynchronously
        """
        try:
            return file_path.exists() and file_path.is_file()
        except Exception:
            return False

    async def get_file_size(self, file_path: Path) -> int:
        """
        Get file size in bytes
        """
        try:
            if not file_path.exists():
                return 0
            return file_path.stat().st_size
        except Exception:
            return 0

    async def backup_file(self, file_path: Path, backup_suffix: str = ".bak") -> Path:
        """
        Create a backup copy of a file
        """
        try:
            if not file_path.exists():
                raise StorageError(
                    f"Cannot backup non-existent file: {file_path}",
                    file_path=str(file_path),
                    operation="backup",
                )

            backup_path = file_path.with_suffix(f"{file_path.suffix}{backup_suffix}")

            # Read original file
            async with aiofiles.open(file_path, "rb") as src:
                content = await src.read()

            # Write backup file
            async with aiofiles.open(backup_path, "wb") as dst:
                await dst.write(content)

            return backup_path

        except StorageError:
            raise
        except Exception as e:
            raise StorageError(
                f"Failed to backup file {file_path}: {str(e)}",
                file_path=str(file_path),
                operation="backup",
            )

    async def validate_json_file(self, file_path: Path) -> dict[str, Any]:
        """
        Validate that a file contains valid JSON
        Returns validation results
        """
        result = {"valid": False, "error": None, "size": 0, "exists": False}

        try:
            result["exists"] = file_path.exists()
            if not result["exists"]:
                result["error"] = "File does not exist"
                return result

            result["size"] = await self.get_file_size(file_path)
            if result["size"] == 0:
                result["error"] = "File is empty"
                return result

            # Try to read and parse JSON
            await self.read_json(file_path)
            result["valid"] = True

        except StorageError as e:
            result["error"] = e.message
        except Exception as e:
            result["error"] = str(e)

        return result

    def _json_serializer(self, obj):
        """
        Custom JSON serializer for special types
        """
        # Handle datetime objects
        if hasattr(obj, "isoformat"):
            return obj.isoformat()

        # Handle Path objects
        if isinstance(obj, Path):
            return str(obj)

        # Handle sets
        if isinstance(obj, set):
            return list(obj)

        # Default behavior
        raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

    async def cleanup_temp_files(self, directory: Path) -> int:
        """
        Clean up temporary files in a directory
        Returns number of files cleaned up
        """
        try:
            if not directory.exists() or not directory.is_dir():
                return 0

            count = 0
            for temp_file in directory.glob("*.tmp"):
                try:
                    temp_file.unlink()
                    count += 1
                except Exception:
                    # Continue with other files if one fails
                    continue

            return count

        except Exception:
            return 0
