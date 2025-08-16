"""Map storage module for Project Mapper.

This module contains the MapStorage class which handles storing and loading project maps.
"""

import json
import logging
import traceback
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from proj_mapper.models.project import ProjectMap

# Configure logging
logger = logging.getLogger(__name__)

class MapStorage:
    """Handles storing and loading project maps."""
    
    def __init__(self, output_dir: str = ".maps"):
        """Initialize the map storage.
        
        Args:
            output_dir: Directory for storing maps
        """
        self.output_dir = output_dir
        logger.debug(f"MapStorage initialized with output_dir: {output_dir}")
    
    def save_map(self, project_path: str, project_map: ProjectMap) -> str:
        """Save a project map to disk.
        
        Args:
            project_path: Path to the project root
            project_map: Project map to save
            
        Returns:
            Path to the saved map file
            
        Raises:
            IOError: If the map cannot be saved
        """
        logger.debug(f"MapStorage.save_map: Starting save operation for project at {project_path}")
        start_time = time.time()
        
        try:
            # Create output directory if it doesn't exist
            output_path = Path(project_path) / self.output_dir
            logger.debug(f"MapStorage.save_map: Ensuring output directory exists: {output_path}")
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Create map file path
            map_file = output_path / "project_map.json"
            logger.debug(f"MapStorage.save_map: Map will be saved to: {map_file}")
            
            try:
                # Convert map to dictionary
                logger.debug("MapStorage.save_map: Converting project map to dictionary")
                map_dict = project_map.to_dict()
                
                # Add metadata
                logger.debug("MapStorage.save_map: Adding metadata to map dictionary")
                timestamp = datetime.utcnow().isoformat() + "Z"
                map_dict.update({
                    "schema_version": "1.0.0",
                    "timestamp": timestamp
                })
                logger.debug(f"MapStorage.save_map: Added metadata with timestamp: {timestamp}")
                
                # Save to file
                logger.debug(f"MapStorage.save_map: Writing map to file: {map_file}")
                with open(map_file, 'w') as f:
                    json.dump(map_dict, f, indent=2)
                    
                duration = time.time() - start_time
                logger.debug(f"MapStorage.save_map: Saved project map to: {map_file} in {duration:.2f} seconds")
                return str(map_file)
                
            except Exception as e:
                logger.error(f"Error saving project map: {e}")
                logger.debug(f"MapStorage.save_map: Exception details: {traceback.format_exc()}")
                raise IOError(f"Failed to save project map: {e}")
        except Exception as e:
            logger.error(f"Error in save_map: {e}")
            logger.debug(f"MapStorage.save_map: Exception details: {traceback.format_exc()}")
            raise
    
    def load_map(self, project_path: str) -> ProjectMap:
        """Load a project map from disk.
        
        Args:
            project_path: Path to the project root
            
        Returns:
            Loaded project map
            
        Raises:
            FileNotFoundError: If the map file doesn't exist
            ValueError: If the map file is invalid
        """
        logger.debug(f"MapStorage.load_map: Starting load operation for project at {project_path}")
        start_time = time.time()
        
        try:
            # Get map file path
            map_file = Path(project_path) / self.output_dir / "project_map.json"
            logger.debug(f"MapStorage.load_map: Looking for map file at: {map_file}")
            
            if not map_file.exists():
                logger.debug(f"MapStorage.load_map: Map file not found: {map_file}")
                raise FileNotFoundError(f"Map file not found: {map_file}")
            
            try:
                # Load from file
                logger.debug(f"MapStorage.load_map: Reading map file: {map_file}")
                with open(map_file, 'r') as f:
                    map_dict = json.load(f)
                    
                # Validate schema version
                schema_version = map_dict.get("schema_version")
                logger.debug(f"MapStorage.load_map: Map schema version: {schema_version}")
                if schema_version != "1.0.0":
                    logger.warning(f"Unexpected schema version: {schema_version}")
                
                # Create project map
                logger.debug("MapStorage.load_map: Creating ProjectMap from dictionary")
                project_map = ProjectMap.from_dict(map_dict)
                
                duration = time.time() - start_time
                logger.debug(f"MapStorage.load_map: Loaded project map from: {map_file} in {duration:.2f} seconds")
                
                # Debug log map structure and content
                if logger.isEnabledFor(logging.DEBUG):
                    try:
                        node_count = len(project_map.nodes) if hasattr(project_map, 'nodes') else 0
                        edge_count = len(project_map.edges) if hasattr(project_map, 'edges') else 0
                        logger.debug(f"MapStorage.load_map: Map contains {node_count} nodes and {edge_count} edges")
                    except Exception as e:
                        logger.debug(f"MapStorage.load_map: Error counting map elements: {e}")
                
                return project_map
                
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding map file: {e}")
                logger.debug(f"MapStorage.load_map: JSON decode error details: {traceback.format_exc()}")
                raise ValueError(f"Invalid map file format: {e}")
            except Exception as e:
                logger.error(f"Error loading project map: {e}")
                logger.debug(f"MapStorage.load_map: Exception details: {traceback.format_exc()}")
                raise ValueError(f"Failed to load project map: {e}")
        except FileNotFoundError:
            # Re-raise without additional logging since it's already logged
            raise
        except Exception as e:
            logger.error(f"Error in load_map: {e}")
            logger.debug(f"MapStorage.load_map: Exception details: {traceback.format_exc()}")
            raise
    
    def delete_map(self, project_path: str) -> None:
        """Delete a project map from disk.
        
        Args:
            project_path: Path to the project root
            
        Raises:
            FileNotFoundError: If the map file doesn't exist
        """
        logger.debug(f"MapStorage.delete_map: Starting delete operation for project at {project_path}")
        start_time = time.time()
        
        try:
            # Get map file path
            map_file = Path(project_path) / self.output_dir / "project_map.json"
            logger.debug(f"MapStorage.delete_map: Attempting to delete map file: {map_file}")
            
            if not map_file.exists():
                logger.debug(f"MapStorage.delete_map: Map file not found: {map_file}")
                raise FileNotFoundError(f"Map file not found: {map_file}")
            
            try:
                # Delete file
                map_file.unlink()
                duration = time.time() - start_time
                logger.debug(f"MapStorage.delete_map: Deleted project map: {map_file} in {duration:.2f} seconds")
                
            except Exception as e:
                logger.error(f"Error deleting project map: {e}")
                logger.debug(f"MapStorage.delete_map: Exception details: {traceback.format_exc()}")
                raise 
        except FileNotFoundError:
            # Re-raise without additional logging since it's already logged
            raise
        except Exception as e:
            logger.error(f"Error in delete_map: {e}")
            logger.debug(f"MapStorage.delete_map: Exception details: {traceback.format_exc()}")
            raise 