"""Generator configuration for Project Mapper.

This module contains configuration classes for map generation.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

# Configure logging
logger = logging.getLogger(__name__)


class MapFormatType(Enum):
    """Supported map format types."""
    
    JSON = "json"
    MARKDOWN = "markdown"
    YAML = "yaml"
    DOT = "dot"


@dataclass
class GeneratorConfig:
    """Configuration for map generation.
    
    Attributes:
        include_code: Whether to include code elements in the map
        include_documentation: Whether to include documentation elements in the map
        include_metadata: Whether to include metadata in the map
        enable_chunking: Whether to enable chunking for large maps
        max_tokens: Maximum token estimate (0 for no limit)
        ai_optimize: Whether to apply AI optimization
        format_type: The format type for the map
    """
    
    include_code: bool = True
    include_documentation: bool = True
    include_metadata: bool = True
    enable_chunking: bool = False
    max_tokens: int = 0
    ai_optimize: bool = False
    format_type: MapFormatType = MapFormatType.JSON
    
    def to_dict(self) -> dict:
        """Convert the config to a serializable dictionary.
        
        Returns:
            A dictionary representation of this config
        """
        return {
            "include_code": self.include_code,
            "include_documentation": self.include_documentation,
            "include_metadata": self.include_metadata,
            "enable_chunking": self.enable_chunking,
            "max_tokens": self.max_tokens,
            "ai_optimize": self.ai_optimize,
            "format_type": self.format_type.value
        } 