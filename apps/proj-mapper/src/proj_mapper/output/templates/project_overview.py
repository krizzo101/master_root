"""Project overview template for Project Mapper.

This module provides a template for generating complete project overview maps.
"""

import logging
from typing import Any, Dict, List, Optional, Set

from proj_mapper.models.relationship import RelationshipType
from proj_mapper.relationship.graph import RelationshipGraph, Node, Edge
from proj_mapper.output.generator import MapTemplate
from proj_mapper.output.config import GeneratorConfig

# Configure logging
logger = logging.getLogger(__name__)


class ProjectOverviewTemplate(MapTemplate):
    """Template for generating complete project overview maps."""
    
    @property
    def name(self) -> str:
        """Get the template name.
        
        Returns:
            The template name
        """
        return "project_overview"
    
    def generate(self, graph: RelationshipGraph, config: GeneratorConfig) -> Dict[str, Any]:
        """Generate a project overview map from the relationship graph.
        
        Args:
            graph: The relationship graph
            config: The generator configuration
            
        Returns:
            The generated map structure
        """
        logger.info("Generating project overview map")
        
        # Create the basic map structure
        map_structure = {
            "project": self._get_project_name(graph),
            "version": "1.0.0",
            "generated_at": self._get_timestamp(),
            "statistics": self._get_statistics(graph),
        }
        
        # Add metadata if configured
        if config.include_metadata:
            map_structure["metadata"] = self._get_metadata(graph)
        
        # Process nodes to add code and documentation elements
        self._process_nodes(graph, map_structure, config)
        
        # Process edges to add relationships
        self._process_relationships(graph, map_structure, config)
        
        return map_structure
    
    def _get_project_name(self, graph: RelationshipGraph) -> str:
        """Get the project name from the graph.
        
        Args:
            graph: The relationship graph
            
        Returns:
            The project name
        """
        # Try to get the project name from the graph metadata
        if hasattr(graph, "metadata") and isinstance(graph.metadata, dict):
            if "project_name" in graph.metadata:
                return graph.metadata["project_name"]
        
        return "Unknown Project"
    
    def _get_timestamp(self) -> str:
        """Get the current timestamp.
        
        Returns:
            The current timestamp as ISO format
        """
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _get_statistics(self, graph: RelationshipGraph) -> Dict[str, Any]:
        """Get statistics about the graph.
        
        Args:
            graph: The relationship graph
            
        Returns:
            Statistics about the graph
        """
        # Count nodes by type
        code_nodes = 0
        doc_nodes = 0
        
        for node in graph.nodes:
            if node.data and "type" in node.data:
                if node.data["type"] == "code":
                    code_nodes += 1
                elif node.data["type"] == "documentation":
                    doc_nodes += 1
        
        # Count edges by type
        relationship_counts = {}
        for edge in graph.edges:
            rel_type = edge.data.get("type", "unknown")
            relationship_counts[rel_type] = relationship_counts.get(rel_type, 0) + 1
        
        return {
            "code_elements": code_nodes,
            "documentation_elements": doc_nodes,
            "total_elements": len(graph.nodes),
            "relationships": len(graph.edges),
            "relationship_types": relationship_counts
        }
    
    def _get_metadata(self, graph: RelationshipGraph) -> Dict[str, Any]:
        """Get metadata from the graph.
        
        Args:
            graph: The relationship graph
            
        Returns:
            Metadata about the graph
        """
        metadata = {
            "schema_version": "1.0",
            "graph_info": {
                "node_count": len(graph.nodes),
                "edge_count": len(graph.edges),
                "directed": True
            }
        }
        
        # Add graph metadata if available
        if hasattr(graph, "metadata") and isinstance(graph.metadata, dict):
            metadata.update(graph.metadata)
        
        return metadata
    
    def _process_nodes(self, graph: RelationshipGraph, map_structure: Dict[str, Any], config: GeneratorConfig) -> None:
        """Process nodes from the graph to add code and documentation elements.
        
        Args:
            graph: The relationship graph
            map_structure: The map structure to update
            config: The generator configuration
        """
        # Process code elements if configured
        if config.include_code:
            code_elements = []
            for node in graph.nodes:
                if node.data and node.data.get("type") == "code":
                    element_data = self._extract_element_data(node)
                    if element_data:
                        code_elements.append(element_data)
            
            map_structure["code_elements"] = code_elements
        
        # Process documentation elements if configured
        if config.include_documentation:
            doc_elements = []
            for node in graph.nodes:
                if node.data and node.data.get("type") == "documentation":
                    element_data = self._extract_element_data(node)
                    if element_data:
                        doc_elements.append(element_data)
            
            map_structure["documentation_elements"] = doc_elements
    
    def _extract_element_data(self, node: Node) -> Optional[Dict[str, Any]]:
        """Extract data from a node for inclusion in the map.
        
        Args:
            node: The node to extract data from
            
        Returns:
            The extracted data, or None if the node has no data
        """
        if not node.data:
            return None
        
        # Create a copy of the node data
        element_data = dict(node.data)
        
        # Add the node ID if not present
        if "id" not in element_data:
            element_data["id"] = node.id
        
        return element_data
    
    def _process_relationships(self, graph: RelationshipGraph, map_structure: Dict[str, Any], config: GeneratorConfig) -> None:
        """Process edges from the graph to add relationships.
        
        Args:
            graph: The relationship graph
            map_structure: The map structure to update
            config: The generator configuration
        """
        relationships = []
        
        for edge in graph.edges:
            if not edge.data:
                continue
            
            # Check confidence threshold
            confidence = edge.data.get("confidence", 1.0)
            if confidence < config.min_confidence:
                continue
            
            # Check relationship type filter
            if config.relationship_types:
                rel_type = edge.data.get("type")
                if rel_type not in config.relationship_types:
                    continue
            
            # Create relationship data
            relationship = {
                "id": edge.id,
                "source_id": edge.source.id,
                "target_id": edge.target.id,
                "type": edge.data.get("type", "unknown"),
                "confidence": confidence
            }
            
            # Add additional edge data if present
            for key, value in edge.data.items():
                if key not in relationship:
                    relationship[key] = value
            
            relationships.append(relationship)
        
        map_structure["relationships"] = relationships 