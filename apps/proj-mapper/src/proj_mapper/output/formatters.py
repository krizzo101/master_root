"""Output formatters for Project Mapper.

This module contains formatters for various output formats.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path


class JSONFormatter:
    """Formatter for JSON output."""
    
    format_name = "json"
    
    def __init__(self):
        """Initialize the JSON formatter."""
        pass
    
    def format(self, relationship_map) -> Dict[str, Any]:
        """Format a relationship map to JSON.
        
        Args:
            relationship_map: The relationship map to format
            
        Returns:
            A dictionary ready for JSON serialization
        """
        # Basic structure for compatibility with tests
        result = {
            "schema_version": "1.0",
            "nodes": [],
            "relationships": [],
            "metadata": {}
        }
        
        # Add nodes if the relationship_map has nodes
        if hasattr(relationship_map, "nodes"):
            for node_id, node_data in relationship_map.nodes.items():
                node_type = node_data.get("type", "unknown")
                metadata = node_data.get("metadata", {})
                
                result["nodes"].append({
                    "id": node_id,
                    "type": node_type,
                    "metadata": metadata
                })
        
        # Add relationships if the relationship_map has relationships
        if hasattr(relationship_map, "relationships"):
            for rel in relationship_map.relationships:
                result["relationships"].append({
                    "source": rel.get("source_id"),
                    "target": rel.get("target_id"),
                    "type": rel.get("type"),
                    "confidence": rel.get("confidence", 1.0)
                })
        
        return result 