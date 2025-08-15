"""
Structured logging system with context management and log aggregation.
"""

import logging
import json
import sys
import traceback
from typing import Dict, Any, Optional, Union, List
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager
from dataclasses import dataclass, asdict
import threading
from collections import deque
from enum import Enum

import structlog
from pythonjsonlogger import jsonlogger


class LogLevel(Enum):
    """Log levels with priority values."""
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


@dataclass
class LogEntry:
    """Structured log entry."""
    timestamp: str
    level: str
    message: str
    context: Dict[str, Any]
    traceback: Optional[str] = None
    correlation_id: Optional[str] = None
    component: Optional[str] = None
    duration_ms: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        # Remove None values
        return {k: v for k, v in data.items() if v is not None}


class LogBuffer:
    """Thread-safe circular buffer for recent logs."""
    
    def __init__(self, max_size: int = 1000):
        self.buffer = deque(maxlen=max_size)
        self.lock = threading.Lock()
    
    def add(self, entry: LogEntry):
        """Add a log entry to the buffer."""
        with self.lock:
            self.buffer.append(entry)
    
    def get_recent(self, count: int = 100) -> List[LogEntry]:
        """Get recent log entries."""
        with self.lock:
            return list(self.buffer)[-count:]
    
    def search(self, 
               level: Optional[str] = None,
               component: Optional[str] = None,
               correlation_id: Optional[str] = None,
               limit: int = 100) -> List[LogEntry]:
        """Search logs with filters."""
        with self.lock:
            results = []
            for entry in reversed(self.buffer):
                if level and entry.level != level:
                    continue
                if component and entry.component != component:
                    continue
                if correlation_id and entry.correlation_id != correlation_id:
                    continue
                results.append(entry)
                if len(results) >= limit:
                    break
            return results


class StructuredLogger:
    """Enhanced structured logger with context management."""
    
    def __init__(self, name: str, log_dir: Optional[Path] = None):
        self.name = name
        self.log_dir = Path(log_dir) if log_dir else Path("logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create log buffer for recent logs
        self.buffer = LogBuffer()
        
        # Configure structlog
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.CallsiteParameterAdder(
                    parameters=[
                        structlog.processors.CallsiteParameter.FILENAME,
                        structlog.processors.CallsiteParameter.FUNC_NAME,
                        structlog.processors.CallsiteParameter.LINENO,
                    ]
                ),
                structlog.processors.dict_tracebacks,
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )
        
        self.logger = structlog.get_logger(name)
        self._setup_handlers()
        
        # Thread-local storage for context
        self.context = threading.local()
        self.context.data = {}
    
    def _setup_handlers(self):
        """Set up log handlers for file and console output."""
        # JSON file handler
        json_handler = logging.FileHandler(
            self.log_dir / f"{self.name}.json",
            encoding='utf-8'
        )
        json_handler.setFormatter(jsonlogger.JsonFormatter(
            fmt='%(timestamp)s %(level)s %(name)s %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        
        # Human-readable file handler
        text_handler = logging.FileHandler(
            self.log_dir / f"{self.name}.log",
            encoding='utf-8'
        )
        text_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        
        # Console handler (colored output)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(
            '\033[1m%(asctime)s\033[0m - \033[34m%(name)s\033[0m - '
            '%(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        ))
        
        # Add handlers to root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        root_logger.addHandler(json_handler)
        root_logger.addHandler(text_handler)
        root_logger.addHandler(console_handler)
    
    def _create_entry(self, level: str, message: str, **kwargs) -> LogEntry:
        """Create a structured log entry."""
        entry = LogEntry(
            timestamp=datetime.utcnow().isoformat(),
            level=level,
            message=message,
            context={**self.context.data, **kwargs},
            component=self.name,
            correlation_id=self.context.data.get('correlation_id'),
            traceback=traceback.format_exc() if sys.exc_info()[0] else None
        )
        
        # Add to buffer
        self.buffer.add(entry)
        
        return entry
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        entry = self._create_entry('DEBUG', message, **kwargs)
        self.logger.debug(message, **entry.to_dict())
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        entry = self._create_entry('INFO', message, **kwargs)
        self.logger.info(message, **entry.to_dict())
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        entry = self._create_entry('WARNING', message, **kwargs)
        self.logger.warning(message, **entry.to_dict())
    
    def error(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """Log error message with optional exception."""
        if exception:
            kwargs['exception'] = str(exception)
            kwargs['exception_type'] = exception.__class__.__name__
        entry = self._create_entry('ERROR', message, **kwargs)
        self.logger.error(message, **entry.to_dict())
    
    def critical(self, message: str, **kwargs):
        """Log critical message."""
        entry = self._create_entry('CRITICAL', message, **kwargs)
        self.logger.critical(message, **entry.to_dict())
    
    @contextmanager
    def context_manager(self, **context_data):
        """Context manager for adding temporary context to logs."""
        old_context = dict(self.context.data)
        self.context.data.update(context_data)
        try:
            yield self
        finally:
            self.context.data = old_context
    
    def add_context(self, **context_data):
        """Add permanent context data."""
        self.context.data.update(context_data)
    
    def clear_context(self):
        """Clear all context data."""
        self.context.data = {}
    
    def get_recent_logs(self, count: int = 100) -> List[Dict[str, Any]]:
        """Get recent log entries as dictionaries."""
        return [entry.to_dict() for entry in self.buffer.get_recent(count)]
    
    def search_logs(self, **filters) -> List[Dict[str, Any]]:
        """Search logs with filters."""
        entries = self.buffer.search(**filters)
        return [entry.to_dict() for entry in entries]


class LogContext:
    """Global log context manager."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.loggers: Dict[str, StructuredLogger] = {}
        self.global_context: Dict[str, Any] = {}
    
    def get_logger(self, name: str) -> StructuredLogger:
        """Get or create a logger."""
        if name not in self.loggers:
            self.loggers[name] = StructuredLogger(name)
            # Add global context
            self.loggers[name].add_context(**self.global_context)
        return self.loggers[name]
    
    def set_global_context(self, **context_data):
        """Set global context for all loggers."""
        self.global_context.update(context_data)
        # Update existing loggers
        for logger in self.loggers.values():
            logger.add_context(**context_data)
    
    def get_all_recent_logs(self, count: int = 100) -> List[Dict[str, Any]]:
        """Get recent logs from all loggers."""
        all_logs = []
        for logger in self.loggers.values():
            all_logs.extend(logger.get_recent_logs(count))
        
        # Sort by timestamp
        all_logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return all_logs[:count]


# Global functions for easy access
_log_context = LogContext()


def get_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance."""
    return _log_context.get_logger(name)


def setup_logging(log_level: str = 'INFO', 
                  log_dir: Optional[str] = None,
                  **global_context):
    """Set up global logging configuration."""
    # Set log level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(level=numeric_level)
    
    # Set global context
    _log_context.set_global_context(**global_context)
    
    # Configure log directory if provided
    if log_dir:
        Path(log_dir).mkdir(parents=True, exist_ok=True)


# Example usage
if __name__ == "__main__":
    # Set up logging
    setup_logging(
        log_level='DEBUG',
        environment='development',
        service='autonomous-claude-agent'
    )
    
    # Get logger
    logger = get_logger('example')
    
    # Log with context
    with logger.context_manager(request_id='123', user='admin'):
        logger.info("Processing request", action='start')
        try:
            # Simulate work
            result = 42
            logger.info("Request completed", result=result)
        except Exception as e:
            logger.error("Request failed", exception=e)