"""
KG-DB Optimization System

This module provides intelligent resource routing, performance optimization,
and zero-failure agent startup capabilities for multi-agent coordination systems.

Key Components:
- OptimizedResourceManager: Central resource management with intelligent routing
- DatabaseCoordinator: High-performance database operations with connection pooling
- KGManager: Knowledge Graph operations with caching and error recovery
- CacheManager: Intelligent caching with TTL and invalidation strategies
- Performance monitoring and alerting system

Author: System Architecture Team
Version: 1.0.0
Created: 2025-01-27
"""

from __future__ import annotations

__version__ = "1.0.0"
__author__ = "System Architecture Team"

# Core exports
from .resource_manager import OptimizedResourceManager
from .database_coordinator import DatabaseCoordinator
from .kg_manager import KGManager
from .cache_manager import CacheManager
from .performance_monitor import PerformanceMonitor
from .exceptions import (
    OptimizationError,
    DatabaseConnectionError,
    KGOperationError,
    CacheError,
    PerformanceError,
)

__all__ = [
    "OptimizedResourceManager",
    "DatabaseCoordinator",
    "KGManager",
    "CacheManager",
    "PerformanceMonitor",
    "OptimizationError",
    "DatabaseConnectionError",
    "KGOperationError",
    "CacheError",
    "PerformanceError",
]
