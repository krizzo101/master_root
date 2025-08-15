"""Storage management for Project Mapper.

This module provides functionality for storing and retrieving generated maps.

DEPRECATED: This module is kept for backward compatibility.
Use the classes from the proj_mapper.output.storage package instead.
"""

import warnings

from proj_mapper.output.storage.base import MapStorageProvider
from proj_mapper.output.storage.file_storage import LocalFileSystemStorage
from proj_mapper.output.storage.manager import StorageManager

# Issue a deprecation warning
warnings.warn(
    "Direct imports from proj_mapper.output.storage are deprecated. "
    "Use proj_mapper.output.storage.* modules instead.",
    DeprecationWarning,
    stacklevel=2
)

__all__ = [
    'MapStorageProvider',
    'LocalFileSystemStorage',
    'StorageManager',
] 