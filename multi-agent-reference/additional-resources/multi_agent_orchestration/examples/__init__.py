"""
Example workflows and usage patterns for multi-agent orchestration.

This module provides practical examples demonstrating different orchestration
patterns, agent collaboration scenarios, and workflow configurations.
"""

from .demo_application import main as run_demo
from .workflow_examples import (
    create_conditional_workflow,
    create_data_analysis_workflow,
    create_parallel_processing_workflow,
    create_research_pipeline,
)

__all__ = [
    "create_data_analysis_workflow",
    "create_research_pipeline",
    "create_parallel_processing_workflow",
    "create_conditional_workflow",
    "run_demo",
]
