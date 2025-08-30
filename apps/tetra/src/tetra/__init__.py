"""
Tetra - Hybrid Multi-Agent Orchestration System

A powerful orchestration system combining Claude and OpenAI for AI-driven development.
"""

__version__ = "0.1.0"
__author__ = "Opsvi Team"

from .core.config import get_config, set_config

__all__ = ["get_config", "set_config"]
