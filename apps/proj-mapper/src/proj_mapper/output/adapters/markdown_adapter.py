"""Markdown adapter for Project Mapper.

This module provides the MarkdownAdapter class for outputting maps in Markdown format.
"""

import logging
import json
from typing import Any, Dict, List, Optional, Union

from proj_mapper.output.adapters import OutputAdapter
from proj_mapper.output.generator import GeneratorConfig
from proj_mapper.models.project import ProjectMap
from proj_mapper.utils.json_encoder import EnumEncoder

# Configure logging
logger = logging.getLogger(__name__)


class MarkdownAdapter(OutputAdapter):
    """Adapter for Markdown output format.
    
    This adapter converts the internal map structure to a Markdown document.
    """
    
    def render(self, map_structure: Any, config: GeneratorConfig) -> str:
        """Render the map structure to Markdown.
        
        Args:
            map_structure: The map structure to render
            config: The generator configuration
            
        Returns:
            The rendered map as a Markdown string
        """
        logger.debug("Rendering map to Markdown format")
        
        # Build the markdown document
        lines = []
        
        # Add title
        project_name = map_structure.get("project", "Project Map")
        lines.append(f"# {project_name}")
        lines.append("")
        
        # Add metadata if configured
        if config.include_metadata and "metadata" in map_structure:
            lines.append("## Metadata")
            lines.append("")
            self._render_metadata(map_structure["metadata"], lines)
            lines.append("")
        
        # Add statistics if present
        if "statistics" in map_structure:
            lines.append("## Statistics")
            lines.append("")
            self._render_statistics(map_structure["statistics"], lines)
            lines.append("")
        
        # Add code elements if configured
        if config.include_code and "code_elements" in map_structure:
            lines.append("## Code Elements")
            lines.append("")
            self._render_elements(map_structure["code_elements"], lines)
            lines.append("")
        
        # Add documentation elements if configured
        if config.include_documentation and "documentation_elements" in map_structure:
            lines.append("## Documentation Elements")
            lines.append("")
            self._render_elements(map_structure["documentation_elements"], lines)
            lines.append("")
        
        # Add relationships
        if "relationships" in map_structure:
            lines.append("## Relationships")
            lines.append("")
            self._render_relationships(map_structure["relationships"], lines)
            lines.append("")
        
        # Join the lines to create the markdown document
        return "\n".join(lines)
    
    def get_extension(self) -> str:
        """Get the file extension for Markdown output.
        
        Returns:
            The file extension for Markdown
        """
        return ".md"
    
    def get_content_type(self) -> str:
        """Get the MIME content type for Markdown.
        
        Returns:
            The MIME content type for Markdown
        """
        return "text/markdown"
    
    def _render_metadata(self, metadata: Dict[str, Any], lines: List[str]) -> None:
        """Render metadata to Markdown.
        
        Args:
            metadata: The metadata to render
            lines: The list of lines to append to
        """
        if not metadata:
            lines.append("No metadata available.")
            return
        
        # Render basic metadata as a table
        lines.append("| Key | Value |")
        lines.append("| --- | ----- |")
        
        for key, value in sorted(metadata.items()):
            if isinstance(value, dict):
                value_str = "{...}"  # Placeholder for nested objects
            elif isinstance(value, list):
                value_str = "[...]"  # Placeholder for lists
            else:
                value_str = str(value)
            
            lines.append(f"| {key} | {value_str} |")
        
        # Add detailed generator information if present
        if "generator" in metadata:
            lines.append("")
            lines.append("### Generator Information")
            lines.append("")
            
            generator = metadata["generator"]
            lines.append(f"- Name: {generator.get('name', 'Unknown')}")
            lines.append(f"- Version: {generator.get('version', 'Unknown')}")
            lines.append(f"- Timestamp: {generator.get('timestamp', 'Unknown')}")
            
            if "config" in generator:
                lines.append("")
                lines.append("### Generator Configuration")
                lines.append("```json")
                lines.append(json.dumps(generator["config"], indent=2, cls=EnumEncoder))
                lines.append("```")
    
    def _render_statistics(self, statistics: Dict[str, Any], lines: List[str]) -> None:
        """Render statistics to Markdown.
        
        Args:
            statistics: The statistics to render
            lines: The list of lines to append to
        """
        if not statistics:
            lines.append("No statistics available.")
            return
        
        # Render statistics as a table
        lines.append("| Metric | Value |")
        lines.append("| ------ | ----- |")
        
        for key, value in sorted(statistics.items()):
            # Handle specialized rendering for certain keys
            if key == "relationship_types" and isinstance(value, dict):
                # Render relationship types separately
                value_str = "See below"
            else:
                value_str = str(value)
            
            lines.append(f"| {key} | {value_str} |")
        
        # Render relationship types if present
        if "relationship_types" in statistics and isinstance(statistics["relationship_types"], dict):
            lines.append("")
            lines.append("### Relationship Types")
            lines.append("")
            lines.append("| Type | Count |")
            lines.append("| ---- | ----- |")
            
            rel_types = statistics["relationship_types"]
            for rel_type, count in sorted(rel_types.items()):
                lines.append(f"| {rel_type} | {count} |")
    
    def _render_elements(self, elements: List[Dict[str, Any]], lines: List[str]) -> None:
        """Render elements to Markdown.
        
        Args:
            elements: The elements to render
            lines: The list of lines to append to
        """
        if not elements:
            lines.append("No elements available.")
            return
        
        # Render a summary of elements
        lines.append(f"Total: {len(elements)}")
        lines.append("")
        
        # Render each element as a section
        for element in elements:
            element_id = element.get("id", "unknown")
            element_name = element.get("name", element_id)
            element_type = element.get("type", "unknown")
            
            lines.append(f"### {element_name}")
            lines.append("")
            lines.append(f"- ID: `{element_id}`")
            lines.append(f"- Type: {element_type}")
            
            # Add location if present
            if "location" in element:
                location = element["location"]
                if isinstance(location, dict):
                    path = location.get("path", "unknown")
                    start_line = location.get("start_line", "?")
                    end_line = location.get("end_line", "?")
                    lines.append(f"- Location: {path}:{start_line}-{end_line}")
                else:
                    lines.append(f"- Location: {location}")
            
            # Add additional properties
            for key, value in element.items():
                if key not in {"id", "name", "type", "location", "content"}:
                    # Format value based on type
                    if isinstance(value, dict):
                        value_str = "{...}"  # Placeholder for nested objects
                    elif isinstance(value, list):
                        value_str = "[...]"  # Placeholder for lists
                    else:
                        value_str = str(value)
                    
                    lines.append(f"- {key}: {value_str}")
            
            # Add content if present
            if "content" in element and element["content"]:
                lines.append("")
                lines.append("#### Content")
                lines.append("")
                lines.append("```")
                content_lines = str(element["content"]).splitlines()
                # Limit content to max 20 lines
                if len(content_lines) > 20:
                    content_to_show = content_lines[:10] + ["..."] + content_lines[-10:]
                    lines.extend(content_to_show)
                else:
                    lines.extend(content_lines)
                lines.append("```")
            
            lines.append("")
    
    def _render_relationships(self, relationships: List[Dict[str, Any]], lines: List[str]) -> None:
        """Render relationships to Markdown.
        
        Args:
            relationships: The relationships to render
            lines: The list of lines to append to
        """
        if not relationships:
            lines.append("No relationships available.")
            return
        
        # Render a summary of relationships
        lines.append(f"Total: {len(relationships)}")
        lines.append("")
        
        # Render relationships as a table
        lines.append("| Source | Relationship | Target | Confidence |")
        lines.append("| ------ | ------------ | ------ | ---------- |")
        
        for rel in relationships:
            source_id = rel.get("source_id", "unknown")
            target_id = rel.get("target_id", "unknown")
            rel_type = rel.get("type", "unknown")
            confidence = rel.get("confidence", "unknown")
            
            # Format confidence as percentage if it's a number
            if isinstance(confidence, (int, float)):
                confidence_str = f"{confidence:.0%}" if confidence <= 1 else str(confidence)
            else:
                confidence_str = str(confidence)
            
            lines.append(f"| `{source_id}` | {rel_type} | `{target_id}` | {confidence_str} |") 