#!/usr/bin/env python3
"""
Logging configuration and utilities for answer_review.py
Provides structured logging with rotation, audit trails, and performance metrics.
"""

import hashlib
import json
import logging
import logging.handlers
import os
import pathlib
import time
from datetime import datetime
from typing import Any, Dict, Optional


class StructuredFormatter(logging.Formatter):
    """Custom formatter that outputs structured JSON logs."""
    
    def format(self, record):
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add extra fields if present
        if hasattr(record, "session_id"):
            log_obj["session_id"] = record.session_id
        if hasattr(record, "extra_data"):
            log_obj.update(record.extra_data)
            
        return json.dumps(log_obj)


class AuditLogger:
    """Handles immutable audit logging for review decisions."""
    
    def __init__(self, base_dir: pathlib.Path):
        self.audit_dir = base_dir / "audit"
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        
    def log_review(self, session_id: str, review_data: Dict[str, Any]):
        """Log a review decision to the audit trail."""
        audit_file = self.audit_dir / f"review_audit_{datetime.now():%Y-%m-%d}.jsonl"
        
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": session_id,
            "review_id": hashlib.sha256(f"{session_id}{time.time()}".encode()).hexdigest()[:16],
            **review_data
        }
        
        # Hash sensitive content for privacy
        if "assistant_response" in audit_entry:
            audit_entry["response_hash"] = hashlib.sha256(
                audit_entry["assistant_response"].encode()
            ).hexdigest()
            audit_entry["response_length"] = len(audit_entry["assistant_response"])
            # Only keep first 100 chars for context
            audit_entry["response_preview"] = audit_entry["assistant_response"][:100] + "..."
            del audit_entry["assistant_response"]
            
        if "user_prompts" in audit_entry:
            audit_entry["prompts_hashes"] = [
                hashlib.sha256(p.encode()).hexdigest()[:16] 
                for p in audit_entry["user_prompts"]
            ]
            audit_entry["prompts_count"] = len(audit_entry["user_prompts"])
            del audit_entry["user_prompts"]
        
        # Append to audit log (create if doesn't exist)
        with open(audit_file, "a") as f:
            f.write(json.dumps(audit_entry) + "\n")


class PerformanceLogger:
    """Tracks performance metrics for monitoring and optimization."""
    
    def __init__(self, base_dir: pathlib.Path):
        self.metrics_dir = base_dir / "metrics"
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        self.timers = {}
        
    def start_timer(self, operation: str, session_id: str):
        """Start timing an operation."""
        key = f"{session_id}:{operation}"
        self.timers[key] = time.perf_counter()
        
    def end_timer(self, operation: str, session_id: str, metadata: Optional[Dict] = None):
        """End timing and log the metric."""
        key = f"{session_id}:{operation}"
        if key not in self.timers:
            return
            
        duration_ms = (time.perf_counter() - self.timers[key]) * 1000
        del self.timers[key]
        
        metrics_file = self.metrics_dir / f"performance_{datetime.now():%Y-%m-%d}.jsonl"
        
        metric = {
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": session_id,
            "operation": operation,
            "duration_ms": round(duration_ms, 2),
            "metadata": metadata or {}
        }
        
        with open(metrics_file, "a") as f:
            f.write(json.dumps(metric) + "\n")
            
        return duration_ms


def setup_logging(
    base_dir: Optional[pathlib.Path] = None,
    log_level: str = "INFO",
    enable_console: bool = False
) -> tuple[logging.Logger, AuditLogger, PerformanceLogger]:
    """
    Set up comprehensive logging for answer_review.
    
    Returns:
        Tuple of (logger, audit_logger, performance_logger)
    """
    if base_dir is None:
        base_dir = pathlib.Path(os.getenv("CLAUDE_PROJECT_DIR", ".")) / ".claude" / "hooks" / "logs"
    
    base_dir.mkdir(parents=True, exist_ok=True)
    operational_dir = base_dir / "operational"
    operational_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure main logger
    logger = logging.getLogger("answer_review")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # File handler with rotation (10MB max, keep 5 backups)
    log_file = operational_dir / f"answer_review_{datetime.now():%Y-%m-%d}.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(StructuredFormatter())
    logger.addHandler(file_handler)
    
    # Console handler if requested
    if enable_console or os.getenv("DEBUG"):
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        logger.addHandler(console_handler)
    
    # Create specialized loggers
    audit_logger = AuditLogger(base_dir)
    perf_logger = PerformanceLogger(base_dir)
    
    return logger, audit_logger, perf_logger


def log_with_context(logger: logging.Logger, level: str, message: str, 
                     session_id: Optional[str] = None, **extra_data):
    """Helper to log with session context and extra data."""
    log_method = getattr(logger, level.lower())
    extra = {"extra_data": extra_data}
    if session_id:
        extra["session_id"] = session_id
    log_method(message, extra=extra)


# Convenience function for getting singleton loggers
_loggers = None

def get_loggers():
    """Get or create the singleton logger instances."""
    global _loggers
    if _loggers is None:
        _loggers = setup_logging(
            log_level=os.getenv("REVIEW_LOG_LEVEL", "INFO"),
            enable_console=os.getenv("DEBUG", "").lower() == "true"
        )
    return _loggers