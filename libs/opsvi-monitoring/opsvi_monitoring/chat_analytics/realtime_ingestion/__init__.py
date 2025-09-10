"""
Real-time chat log ingestion system for the unified context platform.

This package provides a complete solution for real-time monitoring, parsing,
and ingestion of Claude chat logs with immediate correlation and analytics.

Key Features:
- Real-time file watching and change detection
- High-performance buffering and batch processing
- Integration with existing correlator and database systems
- Comprehensive fault tolerance and circuit breaker patterns
- Health monitoring and alerting
- Production-ready service management

Main Components:
- ChatLogWatcher: Monitors directories for new/changed JSONL files
- RealTimeIngestionPipeline: Processes and correlates chat log entries
- FaultToleranceManager: Handles retries and circuit breaking
- MonitoringDashboard: Provides metrics and health monitoring
- RealTimeChatLogService: Main service coordinator

Usage:
    from opsvi_monitoring.chat_analytics.realtime_ingestion import RealTimeChatLogService

    service = RealTimeChatLogService()
    await service.start()

Or via command line:
    python -m opsvi_monitoring.chat_analytics.realtime_ingestion.service_runner start --config config.yml
"""

from .chat_log_watcher import ChatLogDiscovery, ChatLogWatcher, WatcherConfig
from .fault_tolerance import CircuitBreaker, FaultToleranceManager, RetryManager
from .ingestion_pipeline import (
    ChatLogParser,
    IngestionBuffer,
    RealTimeIngestionPipeline,
)
from .monitoring import HealthChecker, MetricsCollector, MonitoringDashboard
from .realtime_service import RealTimeChatLogService, ServiceManager
from .service_runner import ServiceConfiguration, ServiceRunner

__version__ = "1.0.0"
__author__ = "OPSVI Team"

__all__ = [
    # Core service
    "RealTimeChatLogService",
    "ServiceManager",
    "ServiceRunner",
    # Components
    "ChatLogWatcher",
    "ChatLogDiscovery",
    "RealTimeIngestionPipeline",
    "ChatLogParser",
    "IngestionBuffer",
    # Configuration
    "WatcherConfig",
    "ServiceConfiguration",
    # Fault tolerance
    "FaultToleranceManager",
    "CircuitBreaker",
    "RetryManager",
    # Monitoring
    "MonitoringDashboard",
    "MetricsCollector",
    "HealthChecker",
]
