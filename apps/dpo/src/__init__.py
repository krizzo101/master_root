"""
Development Process Orchestrator (DPO) System

A comprehensive intelligent development automation system that analyzes requests,
generates optimized workflows, and orchestrates specialized AI agents to deliver
high-quality software solutions.
"""

__version__ = "1.0.0"
__author__ = "Master Root AI Development Team"

from .dpo_intelligence_integration import (
    DPOIntelligenceIntegration,
    DPORequest,
    EnhancedDPOWorkflow,
)
from .dpo_main_controller import (
    DevelopmentProcessOrchestrator,
    DPOConfiguration,
    RequestAnalysis,
    RequestType,
)
from .dpo_orchestrator_integration import (
    DPOOrchestrator,
    WorkflowStatus,
    WorkflowSubmission,
)
from .intelligence_review_engine_enhanced import (
    EnhancementIntelligenceEngine,
    EnhancementNode,
    EnhancementScore,
)
from .sdlc_template_system import BaseTemplate, SDLCTemplateSystem, WorkflowPhase

__all__ = [
    # Version
    "__version__",
    "__author__",
    # Main Controller
    "DevelopmentProcessOrchestrator",
    "DPOConfiguration",
    "RequestType",
    "RequestAnalysis",
    # Intelligence Integration
    "DPORequest",
    "EnhancedDPOWorkflow",
    "DPOIntelligenceIntegration",
    # Orchestrator Integration
    "DPOOrchestrator",
    "WorkflowStatus",
    "WorkflowSubmission",
    # Template System
    "SDLCTemplateSystem",
    "WorkflowPhase",
    "BaseTemplate",
    # Intelligence Engine
    "EnhancementIntelligenceEngine",
    "EnhancementScore",
    "EnhancementNode",
]

# Module initialization
import logging
import sys
from pathlib import Path

# Setup import paths before any other imports
try:
    from ._path_setup import setup_paths
except ImportError:
    from _path_setup import setup_paths
setup_paths()

# Configure module logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Add module path to system path
module_path = Path(__file__).parent
if str(module_path) not in sys.path:
    sys.path.insert(0, str(module_path))

# Initialize default configuration
DEFAULT_CONFIG = DPOConfiguration()


def initialize(config_path: str = None) -> DevelopmentProcessOrchestrator:
    """
    Initialize the DPO system with optional configuration file.

    Args:
        config_path: Path to configuration file (optional)

    Returns:
        Initialized DevelopmentProcessOrchestrator instance
    """
    if config_path:
        config = DPOConfiguration.from_file(config_path)
    else:
        config = DEFAULT_CONFIG

    controller = DevelopmentProcessOrchestrator(config)
    logger.info(f"DPO System initialized (v{__version__})")

    return controller
