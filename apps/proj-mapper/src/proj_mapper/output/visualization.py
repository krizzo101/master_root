"""Visualization generator for Project Mapper.

This module provides functionality for generating various types of visualizations
from project maps.

This module is maintained for backward compatibility and directly imports from
the new visualization submodule.
"""

from proj_mapper.output.visualization.base import (
    VisualizationType,
    VisualizationFormat,
    VisualizationConfig
)
from proj_mapper.output.visualization.graph import (
    GraphRenderer,
    DotRenderer
)
from proj_mapper.output.visualization.generator import VisualizationGenerator

# For backward compatibility
__all__ = [
    'VisualizationType',
    'VisualizationFormat',
    'VisualizationConfig',
    'GraphRenderer',
    'DotRenderer',
    'VisualizationGenerator'
]
