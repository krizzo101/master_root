"""Base classes and utilities for visualization.

This module provides base classes and common utilities for visualization.
"""

import logging
from enum import Enum

# Configure logging
logger = logging.getLogger(__name__)


class VisualizationType(Enum):
    """Types of visualizations that can be generated."""
    
    DEPENDENCY = "dependency"
    HIERARCHY = "hierarchy"
    MODULE = "module"
    DOCUMENTATION = "documentation"
    RELATIONSHIP = "relationship"


class VisualizationFormat(Enum):
    """Output formats for visualizations."""
    
    DOT = "dot"  # Graphviz DOT format
    SVG = "svg"  # SVG format
    PNG = "png"  # PNG format
    HTML = "html"  # Interactive HTML


class VisualizationConfig:
    """Configuration for visualization generation."""
    
    def __init__(
        self,
        output_format: VisualizationFormat = VisualizationFormat.DOT,
        include_metadata: bool = True,
        include_weights: bool = True,
        min_confidence: float = 0.5,
        max_nodes: int = 100,
        theme: str = "dark",
        interactive: bool = False
    ):
        """Initialize visualization configuration.
        
        Args:
            output_format: The output format for the visualization
            include_metadata: Whether to include metadata in the visualization
            include_weights: Whether to include relationship weights/confidence
            min_confidence: Minimum confidence threshold for relationships
            max_nodes: Maximum number of nodes to include
            theme: Color theme for the visualization
            interactive: Whether to generate interactive visualizations
        """
        self.output_format = output_format
        self.include_metadata = include_metadata
        self.include_weights = include_weights
        self.min_confidence = min_confidence
        self.max_nodes = max_nodes
        self.theme = theme
        self.interactive = interactive
