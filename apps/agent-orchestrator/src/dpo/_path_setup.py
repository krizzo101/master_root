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

# Constants for consistent path management - INTEGRATED VERSION
CURRENT_FILE = Path(__file__).resolve()
DPO_DIR = CURRENT_FILE.parent  # Now at agent-orchestrator/src/dpo
ORCHESTRATOR_SRC = DPO_DIR.parent  # agent-orchestrator/src
ORCHESTRATOR_ROOT = ORCHESTRATOR_SRC.parent  # agent-orchestrator root


def setup_paths():
    """
    Setup sys.path for DPO as integrated module within orchestrator.

    This function:
    1. Ensures orchestrator src is in path for sibling imports
    2. Adds orchestrator root for package imports
    3. DPO directory is already accessible as part of orchestrator
    """
    paths_to_add = [
        str(ORCHESTRATOR_SRC),  # For imports from orchestrator modules
        str(ORCHESTRATOR_ROOT),  # For 'from src.module' imports
    ]

    # Add paths if they don't exist and the directories exist
    for path in paths_to_add:
        if Path(path).exists() and path not in sys.path:
            sys.path.insert(0, path)


def get_agent_orchestrator_path():
    """Return the agent-orchestrator source path."""
    return ORCHESTRATOR_SRC


def get_dpo_path():
    """Return the DPO module path (now integrated)."""
    return DPO_DIR


# Auto-setup when module is imported
setup_paths()
