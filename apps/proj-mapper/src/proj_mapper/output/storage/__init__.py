"""Storage management for Project Mapper.

This module provides functionality for storing and retrieving generated maps.
"""

from proj_mapper.output.storage.base import MapStorageProvider
from proj_mapper.output.storage.file_storage import LocalFileSystemStorage
from proj_mapper.output.storage.manager import StorageManager

__all__ = [
    'MapStorageProvider',
    'LocalFileSystemStorage',
    'StorageManager',
] 