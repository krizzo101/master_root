"""Base storage provider classes.

This module provides the base classes for storage providers.
"""

import logging
from typing import Any, Dict, List, Optional

from proj_mapper.output.config import GeneratorConfig

# Configure logging
logger = logging.getLogger(__name__)


class MapStorageProvider:
    """Base class for map storage providers."""
    
    def store_map(self, 
                 map_data: Any, 
                 project_name: str, 
                 config: GeneratorConfig, 
                 format_extension: str = ".json") -> str:
        """Store a generated map.
        
        Args:
            map_data: The map data to store
            project_name: The name of the project
            config: The generator configuration
            format_extension: The file extension for the format
            
        Returns:
            The path to the stored map
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    def store_chunked_map(self, 
                         chunked_map: Dict[str, Any], 
                         project_name: str,
                         config: GeneratorConfig,
                         format_extension: str = ".json") -> str:
        """Store a chunked map.
        
        Args:
            chunked_map: The chunked map data to store
            project_name: The name of the project
            config: The generator configuration
            format_extension: The file extension for the format
            
        Returns:
            The path to the master chunk
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    def get_latest_map(self, project_name: str) -> Optional[str]:
        """Get the path to the latest map for a project.
        
        Args:
            project_name: The name of the project
            
        Returns:
            The path to the latest map, or None if not found
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    def get_map_history(self, project_name: str) -> List[Dict[str, Any]]:
        """Get the history of maps for a project.
        
        Args:
            project_name: The name of the project
            
        Returns:
            A list of map metadata dictionaries
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    def clean_old_maps(self, project_name: str, keep_count: int = 5) -> int:
        """Clean old maps for a project.
        
        Args:
            project_name: The name of the project
            keep_count: The number of maps to keep
            
        Returns:
            The number of maps deleted
        """
        raise NotImplementedError("Subclasses must implement this method") 