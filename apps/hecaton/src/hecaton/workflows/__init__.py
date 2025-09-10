"""
Enhanced workflow patterns for HECATON.
"""

from .handoff_protocol import HandoffPackage, HandoffProtocol
from .progressive_autonomy import AutonomyLevel, ProgressiveAutonomyManager
from .quality_gates import QualityGate, SDLCQualityGates, ValidationResult

__all__ = [
    "HandoffProtocol",
    "HandoffPackage",
    "ProgressiveAutonomyManager",
    "AutonomyLevel",
    "SDLCQualityGates",
    "QualityGate",
    "ValidationResult",
]
