#!/usr/bin/env python3
"""
DPO Path Setup Module

Centralizes sys.path configuration for consistent imports across all DPO modules.
This module MUST be imported first in any DPO module that needs agent-orchestrator imports.

Usage:
    from ._path_setup import setup_paths
    setup_paths()

    # Now imports from agent-orchestrator will work
    from generic_orchestrator import AgentTask, GenericOrchestrator
    from intelligence_review_engine import IntelligenceReviewEngine
"""

import sys
from pathlib import Path

# Constants for consistent path management
MASTER_ROOT = Path("/home/opsvi/master_root")
AGENT_ORCHESTRATOR_SRC = MASTER_ROOT / "apps" / "agent-orchestrator" / "src"
DPO_SRC = MASTER_ROOT / "apps" / "dpo" / "src"


def setup_paths():
    """
    Setup sys.path for consistent imports across DPO modules.

    This function:
    1. Adds agent-orchestrator root for package imports
    2. Adds agent-orchestrator/src for direct module imports
    3. Ensures DPO src directory is in path for local imports
    4. Removes duplicates and maintains order
    """
    paths_to_add = [
        str(
            AGENT_ORCHESTRATOR_SRC
        ),  # For direct module imports from agent-orchestrator
        str(AGENT_ORCHESTRATOR_SRC.parent),  # For 'from src.module' imports
        str(DPO_SRC),  # For local DPO imports
    ]

    # Add paths if they don't exist and the directories exist
    for path in paths_to_add:
        if Path(path).exists() and path not in sys.path:
            sys.path.insert(0, path)


def get_agent_orchestrator_path():
    """Return the agent-orchestrator source path."""
    return AGENT_ORCHESTRATOR_SRC


def get_dpo_path():
    """Return the DPO source path."""
    return DPO_SRC


# Auto-setup when module is imported
setup_paths()
