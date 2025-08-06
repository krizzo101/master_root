"""
Testing module for opsvi-core.

Provides core test fixtures, factories, and helpers.
"""

from opsvi_foundation import (
    BaseComponent,
    ComponentError,
    get_logger,
)

# Base testing infrastructure
from .base import (
    MockServices,
    PerformanceTester,
    TestCase,
    TestFixtures,
    TestHelpers,
)

__all__ = [
    # Base classes
    "MockServices",
    "PerformanceTester",
    "TestCase",
    "TestFixtures",
    "TestHelpers",
]

__version__ = "1.0.0"
