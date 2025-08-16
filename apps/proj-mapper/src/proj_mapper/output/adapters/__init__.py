"""Output adapters for Project Mapper.

This module provides the base OutputAdapter class and related functionality
for converting the internal map structure to specific output formats.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any

from proj_mapper.output.generator import GeneratorConfig

# Configure logging
logger = logging.getLogger(__name__)


class OutputAdapter(ABC):
    """Base class for output format adapters.
    
    Output adapters are responsible for converting the internal map structure
    to specific output formats.
    """
    
    def __init__(self):
        """Initialize the output adapter."""
        pass
    
    @abstractmethod
    def render(self, map_structure: Any, config: GeneratorConfig) -> Any:
        """Render the map structure to a specific output format.
        
        Args:
            map_structure: The map structure to render
            config: The generator configuration
            
        Returns:
            The rendered map in the specific format
        """
        pass
    
    def get_extension(self) -> str:
        """Get the file extension for this format.
        
        Returns:
            The file extension (including the dot)
        """
        return ".txt"
    
    def get_content_type(self) -> str:
        """Get the MIME content type for this format.
        
        Returns:
            The MIME content type
        """
        return "text/plain" 