#!/usr/bin/env python3
"""
Enhanced Debug Logging System for GenericOrchestrator

Provides comprehensive "debug-level" logging that captures every value, state change,
and decision point during orchestrator execution for detailed analysis and debugging.
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class DebugLogger:
    """Enhanced logger with detailed value tracking and performance monitoring"""
    
    def __init__(self, name: str, output_dir: Path):
        self.name = name
        self.output_dir = output_dir
        self.logs_dir = output_dir / "logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Create timestamp for this session
        self.session_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Setup enhanced logging
        self.setup_enhanced_logging()
    
    def setup_enhanced_logging(self):
        """Setup comprehensive logging with multiple handlers"""
        
        self.logger = logging.getLogger(f"debug.{self.name}")
        self.logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers to avoid duplicates
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Main debug log - detailed text format
        debug_handler = logging.FileHandler(
            self.logs_dir / f"debug_{self.name}_{self.session_timestamp}.log"
        )
        debug_handler.setLevel(logging.DEBUG)
        
        # Values tracking log - JSON format for analysis
        self.values_handler = logging.FileHandler(
            self.logs_dir / f"values_{self.name}_{self.session_timestamp}.jsonl"
        )
        self.values_handler.setLevel(logging.DEBUG)
        
        # Performance metrics log
        perf_handler = logging.FileHandler(
            self.logs_dir / f"performance_{self.name}_{self.session_timestamp}.log"
        )
        perf_handler.setLevel(logging.DEBUG)
        
        # Enhanced formatters
        debug_formatter = logging.Formatter(
            "%(asctime)s.%(msecs)03d | %(levelname)8s | %(name)20s | %(funcName)15s:%(lineno)4d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
        values_formatter = logging.Formatter("%(message)s")  # JSON only
        perf_formatter = logging.Formatter(
            "%(asctime)s.%(msecs)03d | PERF | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
        debug_handler.setFormatter(debug_formatter)
        self.values_handler.setFormatter(values_formatter)
        perf_handler.setFormatter(perf_formatter)
        
        self.logger.addHandler(debug_handler)
        self.logger.addHandler(perf_handler)
        
        # Create separate logger for values to avoid cross-contamination
        self.values_logger = logging.getLogger(f"values.{self.name}")
        self.values_logger.setLevel(logging.DEBUG)
        self.values_logger.addHandler(self.values_handler)
        
        # Prevent propagation to root logger
        self.logger.propagate = False
        self.values_logger.propagate = False
        
        self.logger.debug(f"Enhanced debug logging initialized for {self.name}")
    
    def debug(self, message: str, **context):
        """Log debug message with optional context"""
        if context:
            formatted_context = " | ".join([f"{k}={v}" for k, v in context.items()])
            self.logger.debug(f"{message} | {formatted_context}")
        else:
            self.logger.debug(message)
    
    def info(self, message: str, **context):
        """Log info message with optional context"""
        if context:
            formatted_context = " | ".join([f"{k}={v}" for k, v in context.items()])
            self.logger.info(f"{message} | {formatted_context}")
        else:
            self.logger.info(message)
    
    def warning(self, message: str, **context):
        """Log warning message with optional context"""
        if context:
            formatted_context = " | ".join([f"{k}={v}" for k, v in context.items()])
            self.logger.warning(f"{message} | {formatted_context}")
        else:
            self.logger.warning(message)
    
    def error(self, message: str, **context):
        """Log error message with optional context"""
        if context:
            formatted_context = " | ".join([f"{k}={v}" for k, v in context.items()])
            self.logger.error(f"{message} | {formatted_context}")
        else:
            self.logger.error(message)
    
    def log_values(self, context: str, **values):
        """Log key-value pairs in JSON format for analysis"""
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "context": context,
                "values": self._serialize_values(values)
            }
            self.values_logger.debug(json.dumps(log_entry, default=str))
        except Exception as e:
            self.logger.error(f"Failed to log values: {e}")
    
    def log_performance(self, operation: str, duration: float, **metrics):
        """Log performance metrics"""
        try:
            formatted_metrics = " | ".join([f"{k}={v}" for k, v in metrics.items()])
            self.logger.debug(f"{operation} | duration={duration:.3f}s | {formatted_metrics}")
        except Exception as e:
            self.logger.error(f"Failed to log performance: {e}")
    
    def log_state_change(self, component: str, old_state: Any, new_state: Any, **context):
        """Log state changes with before/after values"""
        self.log_values(f"{component}.state_change",
            component=component,
            old_state=old_state,
            new_state=new_state,
            **context
        )
        
        self.debug(f"{component} state change: {old_state} -> {new_state}",
                  **context)
    
    def _serialize_values(self, values: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize values for JSON logging, handling complex types"""
        serialized = {}
        for key, value in values.items():
            try:
                if value is None:
                    serialized[key] = None
                elif isinstance(value, (str, int, float, bool)):
                    serialized[key] = value
                elif isinstance(value, (list, tuple)):
                    serialized[key] = [self._serialize_single_value(v) for v in value]
                elif isinstance(value, dict):
                    serialized[key] = {k: self._serialize_single_value(v) for k, v in value.items()}
                elif isinstance(value, set):
                    serialized[key] = list(value)
                elif hasattr(value, '__dict__'):
                    # Object with attributes
                    serialized[key] = {
                        "type": type(value).__name__,
                        "repr": repr(value),
                        "str": str(value)[:200]  # Truncate long strings
                    }
                else:
                    serialized[key] = str(value)[:200]  # Fallback to string
            except Exception as e:
                serialized[key] = f"<serialization_error: {e}>"
        
        return serialized
    
    def _serialize_single_value(self, value: Any) -> Any:
        """Serialize a single value"""
        try:
            if value is None or isinstance(value, (str, int, float, bool)):
                return value
            elif isinstance(value, (list, tuple)):
                return [str(v) for v in value]  # Simplified for nested structures
            elif isinstance(value, dict):
                return {str(k): str(v) for k, v in value.items()}
            else:
                return str(value)[:100]  # Truncate
        except Exception:
            return "<serialization_error>"


class TimedOperation:
    """Context manager for timing operations"""
    
    def __init__(self, debug_logger: DebugLogger, operation_name: str, **context):
        self.debug_logger = debug_logger
        self.operation_name = operation_name
        self.context = context
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        self.debug_logger.debug(f"Starting {self.operation_name}", **self.context)
        self.debug_logger.log_values(f"{self.operation_name}.start", **self.context)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        
        if exc_type is None:
            self.debug_logger.debug(f"Completed {self.operation_name}", duration=f"{duration:.3f}s", **self.context)
            self.debug_logger.log_performance(self.operation_name, duration, **self.context)
        else:
            self.debug_logger.error(f"Failed {self.operation_name}", 
                                   duration=f"{duration:.3f}s",
                                   error_type=exc_type.__name__,
                                   error_message=str(exc_val),
                                   **self.context)
        
        self.debug_logger.log_values(f"{self.operation_name}.end", 
                                    duration=duration,
                                    success=exc_type is None,
                                    **self.context)


def create_debug_logger(component_name: str, output_dir: Path) -> DebugLogger:
    """Factory function to create debug logger for a component"""
    return DebugLogger(component_name, output_dir)