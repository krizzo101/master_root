"""Ingestion pipeline for unified context system.

This module provides a pluggable architecture for ingesting data from various sources
(chat, code, git, errors) into the unified context database.

Core Components:
- BaseAdapter: Abstract interface for source adapters
- Pipeline: Main ingestion coordinator
- AdapterRegistry: Plugin management system
- DataTransformer: Common data transformation utilities
"""

from .adapters import ChatAdapter, CodeAdapter, ErrorAdapter, GitAdapter
from .base_adapter import AdapterConfig, BaseAdapter
from .config_manager import ConfigManager
from .database import DatabaseConnectionPool, IngestionDatabase
from .monitoring import PipelineMonitor
from .orchestrator import PipelineOrchestrator
from .pipeline import IngestionPipeline, PipelineConfig
from .registry import AdapterRegistry
from .transformers import DataTransformer

__all__ = [
    "IngestionPipeline",
    "PipelineConfig",
    "BaseAdapter",
    "AdapterConfig",
    "AdapterRegistry",
    "DataTransformer",
    "IngestionDatabase",
    "DatabaseConnectionPool",
    "PipelineMonitor",
    "ConfigManager",
    "PipelineOrchestrator",
    "ChatAdapter",
    "CodeAdapter",
    "GitAdapter",
    "ErrorAdapter",
]
