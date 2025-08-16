"""Pipeline stages for map generation.

This module contains pipeline stages for generating different types of maps.
"""

import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, cast

from proj_mapper.core.pipeline import PipelineStage, PipelineContext
from proj_mapper.models.code import CodeElement
from proj_mapper.models.documentation import DocumentationElement
from proj_mapper.models.relationship import Relationship
from proj_mapper.output.generator import MapGenerator
from proj_mapper.output.visualization import (
    VisualizationGenerator,
    VisualizationConfig,
    VisualizationType,
    VisualizationFormat
)

# Configure logging
logger = logging.getLogger(__name__)


class MapGenerationStage(PipelineStage):
    """Pipeline stage for generating maps.
    
    This stage generates maps from code elements, documentation elements, and relationships.
    """
    
    def __init__(
        self, 
        output_dir: Optional[Path] = None,
        project_name: str = "Project"
    ):
        """Initialize the map generation stage.
        
        Args:
            output_dir: Directory to output maps to (default: None, in-memory only)
            project_name: Name of the project
        """
        self.generator = MapGenerator()
        self.output_dir = output_dir
        self.project_name = project_name
    
    def process(self, context: PipelineContext, input_data: Any) -> Dict[str, Any]:
        """Process code elements, documentation elements, and relationships to generate maps.
        
        Args:
            context: The pipeline context
            input_data: Input data (not used, reads from context)
            
        Returns:
            Dictionary with generated maps
            
        Notes:
            This stage reads code elements, documentation elements, and relationships
            from the pipeline context and generates various maps. The results are added
            to the context under the key 'generated_maps'.
        """
        logger.info("Starting map generation stage")
        
        # Get elements and relationships from context
        code_elements = []
        doc_elements = []
        relationships = []
        
        # Get code elements
        if context.contains("code_analysis_results"):
            code_results = context.get("code_analysis_results")
            for result in code_results:
                if result.get("success", False) and "analysis" in result:
                    analysis = result["analysis"]
                    if hasattr(analysis, "elements"):
                        code_elements.extend(analysis.elements)
        
        # Get documentation elements
        if context.contains("documentation_analysis_results"):
            doc_results = context.get("documentation_analysis_results")
            for result in doc_results:
                if result.get("success", False) and "analysis" in result:
                    analysis = result["analysis"]
                    if hasattr(analysis, "elements"):
                        doc_elements.extend(analysis.elements)
        
        # Get relationships
        if context.contains("relationships"):
            relationships = context.get("relationships")
        
        logger.info(f"Found {len(code_elements)} code elements, {len(doc_elements)} doc elements, and {len(relationships)} relationships")
        
        # Generate maps
        maps = {}
        
        # Generate project map
        project_map = self.generator.generate_project_map(
            code_elements=code_elements,
            doc_elements=doc_elements,
            relationships=relationships,
            project_name=self.project_name,
            output_dir=self.output_dir,
            metadata={
                "source": "Project Mapper",
                "version": context.get_metadata("version", ""),
                "code_files": len(context.get("code_analysis_results", [])),
                "doc_files": len(context.get("documentation_analysis_results", []))
            }
        )
        maps["project_map"] = project_map
        
        # Generate relationship graph
        relationship_graph = self.generator.generate_relationship_graph(
            relationships=relationships,
            code_elements=code_elements,
            doc_elements=doc_elements,
            project_name=self.project_name,
            output_dir=self.output_dir
        )
        maps["relationship_graph"] = relationship_graph
        
        # Generate documentation structure map
        if doc_elements:
            doc_structure = self.generator.generate_documentation_structure_map(
                doc_elements=doc_elements,
                relationships=relationships,
                project_name=self.project_name,
                output_dir=self.output_dir
            )
            maps["documentation_structure"] = doc_structure
        
        # Add maps to context
        context.set("generated_maps", maps)
        
        logger.info(f"Map generation completed: {len(maps)} maps generated")
        
        return maps 

class VisualizationGenerationStage(PipelineStage):
    """Pipeline stage for generating visualizations.
    
    This stage generates various visualizations from the generated maps.
    """
    
    def __init__(
        self,
        output_dir: Optional[Path] = None,
        visualization_types: Optional[List[VisualizationType]] = None,
        config: Optional[VisualizationConfig] = None
    ):
        """Initialize the visualization generation stage.
        
        Args:
            output_dir: Directory to output visualizations to (default: None)
            visualization_types: Types of visualizations to generate (default: all)
            config: Visualization configuration (default: None)
        """
        self.output_dir = output_dir
        self.visualization_types = visualization_types or list(VisualizationType)
        self.generator = VisualizationGenerator(config)
    
    def process(self, context: PipelineContext, input_data: Any) -> Dict[str, Any]:
        """Process generated maps to create visualizations.
        
        Args:
            context: The pipeline context
            input_data: Input data (not used, reads from context)
            
        Returns:
            Dictionary with generated visualization paths
            
        Notes:
            This stage reads generated maps from the pipeline context and creates
            visualizations. The results are added to the context under the key
            'generated_visualizations'.
        """
        logger.info("Starting visualization generation stage")
        
        # Get maps from context
        if not context.contains("generated_maps"):
            logger.error("No generated maps found in context")
            return {}
        
        maps = context.get("generated_maps")
        project_name = context.get("project_name", "project")
        
        # Create output directory if specified
        if self.output_dir:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            vis_dir = self.output_dir / "visualizations"
        else:
            vis_dir = Path(".maps") / "visualizations"
        
        # Generate visualizations
        visualizations = {}
        
        for vis_type in self.visualization_types:
            try:
                output_path = self.generator.generate_visualization(
                    map_data=maps,
                    vis_type=vis_type,
                    output_dir=vis_dir,
                    project_name=project_name
                )
                
                if output_path:
                    visualizations[vis_type.value] = str(output_path)
                    logger.info(f"Generated {vis_type.value} visualization: {output_path}")
            except Exception as e:
                logger.error(f"Failed to generate {vis_type.value} visualization: {e}")
        
        # Add visualizations to context
        context.set("generated_visualizations", visualizations)
        
        logger.info(f"Visualization generation completed: {len(visualizations)} visualizations generated")
        
        return visualizations 