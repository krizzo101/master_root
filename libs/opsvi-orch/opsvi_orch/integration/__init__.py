"""
Integration Module
------------------
Integration layers for connecting orchestration with existing systems.
"""

from .v1_integration import (
    V1OrchestrationIntegration,
    enhance_v1_with_orchestration
)

__all__ = [
    'V1OrchestrationIntegration',
    'enhance_v1_with_orchestration',
]