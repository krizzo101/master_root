"""Visualization generator for Project Mapper.

This module provides the main visualization generator class.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional

from proj_mapper.models.project import ProjectMap
from proj_mapper.output.visualization.base import (
    VisualizationType,
    VisualizationConfig
)
from proj_mapper.output.visualization.visualization_types import (
    generate_relationship_visualization,
    generate_dependency_visualization,
    generate_hierarchy_visualization,
    generate_module_visualization,
    generate_documentation_visualization
)

# Configure logging
logger = logging.getLogger(__name__)


class VisualizationGenerator:
    """Generator for creating visualizations from project maps."""

    def __init__(self, config: Optional[VisualizationConfig] = None):
        """Initialize the visualization generator.

        Args:
            config: The visualization configuration
        """
        self.config = config or VisualizationConfig()

    def generate(
        self,
        project_map: "ProjectMap",
        output_path: Path,
        vis_type: VisualizationType = VisualizationType.RELATIONSHIP,
    ) -> Optional[Path]:
        """Generate a visualization.

        Args:
            project_map: The project map to visualize
            output_path: The path to save the visualization
            vis_type: The type of visualization to generate

        Returns:
            Path to the generated visualization, or None if generation failed
        """
        project_name = project_map.project.name
        output_dir = output_path.parent
        map_data = project_map.to_dict()

        logger.info(f"Generating {vis_type.value} visualization for {project_name}")

        # Create output directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate the visualization based on type
        try:
            if vis_type == VisualizationType.RELATIONSHIP:
                return generate_relationship_visualization(map_data, output_path, project_name, self.config)
            elif vis_type == VisualizationType.DEPENDENCY:
                return generate_dependency_visualization(map_data, output_path, project_name, self.config)
            elif vis_type == VisualizationType.HIERARCHY:
                return generate_hierarchy_visualization(map_data, output_path, project_name, self.config)
            elif vis_type == VisualizationType.MODULE:
                return generate_module_visualization(map_data, output_path, project_name, self.config)
            elif vis_type == VisualizationType.DOCUMENTATION:
                return generate_documentation_visualization(map_data, output_path, project_name, self.config)
            else:
                logger.error(f"Unsupported visualization type: {vis_type}")
                return None
        except Exception as e:
            logger.error(f"Failed to generate visualization: {e}")
            return None
