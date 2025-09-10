"""
Safety components for HECATON enhanced patterns.
Provides checkpoint/rollback and error boundary capabilities.
"""

from .checkpoint_manager import Checkpoint, CheckpointManager
from .error_boundaries import ErrorBoundary, ErrorResult, ErrorSeverity

__all__ = [
    "Checkpoint",
    "CheckpointManager",
    "ErrorBoundary",
    "ErrorResult",
    "ErrorSeverity",
]
