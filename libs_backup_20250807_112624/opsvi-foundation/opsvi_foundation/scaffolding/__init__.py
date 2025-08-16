"""
Scaffolding framework for OPSVI libraries.

Provides centralized patterns and utilities to eliminate repetition across all libraries.
"""

from __future__ import annotations

from .base import (
    ConfigurableLibrary,
    LibraryBase,
    ManagerLibrary,
    ServiceLibrary,
    create_library_base,
)
from .config import (
    LibraryConfig,
    LibrarySettings,
    create_library_config,
    create_library_settings,
    create_settings_instance,
    global_settings,
)
from .exceptions import (
    LibraryConfigurationError,
    LibraryConnectionError,
    LibraryError,
    LibraryInitializationError,
    LibraryResourceError,
    LibraryShutdownError,
    LibraryTimeoutError,
    LibraryValidationError,
    configuration_error,
    connection_error,
    create_library_exceptions,
    get_library_exception,
    resource_error,
    timeout_error,
    validation_error,
)
from .testing import (
    ConfigurableLibraryTestBase,
    LibraryTestBase,
    ManagerLibraryTestBase,
    ServiceLibraryTestBase,
    async_mock_component,
    create_library_test_class,
    create_test_suite,
    mock_component,
)

__all__ = [
    # Base classes
    "LibraryBase",
    "ConfigurableLibrary",
    "ServiceLibrary",
    "ManagerLibrary",
    "create_library_base",

    # Configuration
    "LibraryConfig",
    "LibrarySettings",
    "create_library_config",
    "create_library_settings",
    "create_settings_instance",
    "global_settings",

    # Exceptions
    "LibraryError",
    "LibraryConfigurationError",
    "LibraryConnectionError",
    "LibraryValidationError",
    "LibraryTimeoutError",
    "LibraryResourceError",
    "LibraryInitializationError",
    "LibraryShutdownError",
    "create_library_exceptions",
    "get_library_exception",
    "configuration_error",
    "connection_error",
    "validation_error",
    "timeout_error",
    "resource_error",

    # Testing
    "LibraryTestBase",
    "ConfigurableLibraryTestBase",
    "ServiceLibraryTestBase",
    "ManagerLibraryTestBase",
    "create_library_test_class",
    "create_test_suite",
    "mock_component",
    "async_mock_component",
]
