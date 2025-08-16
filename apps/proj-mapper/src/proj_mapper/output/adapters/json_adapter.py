"""JSON adapter for Project Mapper.

This module provides the JSONAdapter class for outputting maps in JSON format.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Union

from proj_mapper.output.adapters import OutputAdapter
from proj_mapper.output.generator import GeneratorConfig
from proj_mapper.utils.json_encoder import EnumEncoder

# Configure logging
logger = logging.getLogger(__name__)


class JSONAdapter(OutputAdapter):
    """Adapter for JSON output format.
    
    This adapter converts the internal map structure to a JSON string or dictionary.
    """
    
    def render(self, map_structure: Any, config: GeneratorConfig) -> Union[str, Dict]:
        """Render the map structure to JSON.
        
        Args:
            map_structure: The map structure to render
            config: The generator configuration
            
        Returns:
            The rendered map as a JSON string or dictionary
        """
        logger.debug("Rendering map to JSON format")
        
        # Ensure the map is serializable
        serializable_map = self._make_serializable(map_structure)
        
        # Add metadata if configured
        if config.include_metadata:
            if "metadata" not in serializable_map:
                serializable_map["metadata"] = {}
            
            # Add generator metadata
            serializable_map["metadata"]["generator"] = {
                "name": "Project Mapper",
                "version": "1.0.0",
                "config": self._config_to_dict(config),
                "timestamp": self._get_timestamp()
            }
        
        # Format with indentation and sorting
        json_str = json.dumps(serializable_map, indent=2, sort_keys=True, cls=EnumEncoder)
        
        return json_str
    
    def get_extension(self) -> str:
        """Get the file extension for JSON output.
        
        Returns:
            The file extension for JSON
        """
        return ".json"
    
    def get_content_type(self) -> str:
        """Get the MIME content type for JSON.
        
        Returns:
            The MIME content type for JSON
        """
        return "application/json"
    
    def _make_serializable(self, obj: Any) -> Any:
        """Make an object JSON-serializable.
        
        Args:
            obj: The object to make serializable
            
        Returns:
            A JSON-serializable version of the object
        """
        if isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, set):
            return [self._make_serializable(item) for item in obj]
        elif hasattr(obj, "to_dict") and callable(getattr(obj, "to_dict")):
            return self._make_serializable(obj.to_dict())
        elif hasattr(obj, "__dict__"):
            return self._make_serializable(
                {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
            )
        else:
            return obj
    
    def _config_to_dict(self, config: GeneratorConfig) -> Dict[str, Any]:
        """Convert a generator configuration to a dictionary.
        
        Args:
            config: The generator configuration
            
        Returns:
            A dictionary representation of the configuration
        """
        # Start with basic attributes
        config_dict = {
            "output_format": config.output_format.value,
            "min_confidence": config.min_confidence,
            "include_code": config.include_code,
            "include_documentation": config.include_documentation,
            "include_metadata": config.include_metadata,
            "chunking_enabled": config.chunking_enabled,
            "max_token_estimate": config.max_token_estimate,
            "template_name": config.template_name
        }
        
        # Add relationship types if specified
        if config.relationship_types:
            config_dict["relationship_types"] = list(config.relationship_types)
        
        return config_dict
    
    def _get_timestamp(self) -> str:
        """Get the current timestamp.
        
        Returns:
            The current timestamp in ISO format
        """
        return datetime.now().isoformat()
    
    def _get_map_stats(self, map_structure: Dict[str, Any]) -> Dict[str, Any]:
        """Get statistics about the map structure.
        
        Args:
            map_structure: The map structure
            
        Returns:
            Statistics about the map structure
        """
        stats = {
            "top_level_keys": list(map_structure.keys())
        }
        
        # Count elements
        if "code_elements" in map_structure:
            stats["code_element_count"] = len(map_structure["code_elements"])
        
        if "documentation_elements" in map_structure:
            stats["documentation_element_count"] = len(map_structure["documentation_elements"])
        
        # Count relationships
        if "relationships" in map_structure:
            stats["relationship_count"] = len(map_structure["relationships"])
        
        # Estimate token count
        from proj_mapper.output.ai_optimization import TokenizationEstimator
        estimator = TokenizationEstimator()
        stats["estimated_tokens"] = estimator.estimate_tokens(map_structure)
        
        return stats 