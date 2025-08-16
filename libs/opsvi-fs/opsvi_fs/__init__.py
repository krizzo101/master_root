"""opsvi-fs - File system and storage management.

Comprehensive opsvi-fs library for the OPSVI ecosystem
"""
from __future__ import annotations

__version__ = "0.1.0"
__author__ = "OPSVI Team"
__email__ = "team@opsvi.com"

# Core exports
from .core.base import BaseComponent, ComponentError
from .config.settings import LibraryConfig, LibrarySettings
from .exceptions.base import LibraryError, LibraryConfigurationError, ProviderError

# Provider interfaces and a default local provider
from .providers.interfaces import StorageProvider
from .providers.local_adapter import LocalStorageProvider

# Schemas
from .schemas.models import FileLocation, FileStat, ListEntry

__all__ = [
    # Meta
    "__version__",
    "__author__",
    "__email__",
    # Core
    "BaseComponent",
    "ComponentError",
    "LibraryConfig",
    "LibrarySettings",
    "LibraryError",
    "LibraryConfigurationError",
    "ProviderError",
    # Providers
    "StorageProvider",
    "LocalStorageProvider",
    # Schemas
    "FileLocation",
    "FileStat",
    "ListEntry",
]


def get_version() -> str:
    return __version__


def get_author() -> str:
    return __author__
