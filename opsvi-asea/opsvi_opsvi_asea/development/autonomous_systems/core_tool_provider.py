#!/usr/bin/env python3
"""
Core Tool Provider

Provides direct, low-level access to the instantiated core system tools.
This module is intended for use by orchestrator plugins to prevent
recursive callbacks into the high-level interface.
"""
import sys
import os

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from core_systems.mistake_prevention_system import MistakePreventionSystem
from core_systems.session_continuity_system import SessionContinuitySystem
from core_systems.autonomous_decision_system import AutonomousDecisionSystem

# Singleton instances of the core tools
mistake_prevention_tool = MistakePreventionSystem()
session_continuity_tool = SessionContinuitySystem()
decision_system_tool = AutonomousDecisionSystem()


def get_session_continuity_tool():
    """Returns the singleton instance of the SessionContinuitySystem."""
    return session_continuity_tool


def get_decision_system_tool():
    """Returns the singleton instance of the AutonomousDecisionSystem."""
    return decision_system_tool


def get_mistake_prevention_tool():
    """Returns the singleton instance of the MistakePreventionSystem."""
    return mistake_prevention_tool
