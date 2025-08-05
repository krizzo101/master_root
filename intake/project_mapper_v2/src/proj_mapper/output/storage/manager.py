"""Storage manager for Project Mapper output.

This module provides functionality for storing and loading project maps.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional, Union

from proj_mapper.models.project_map import ProjectMap
from proj_mapper.core.config import Configuration
from proj_mapper.output.storage.file_storage import LocalFileSystemStorage

logger = logging.getLogger(__name__)

class StorageManager:
    """Manages storage and retrieval of project maps."""
    
    def __init__(self, base_dir: str = ".maps"):
        """Initialize the storage manager.
        
        Args:
            base_dir: Base directory for storing maps
        """
        self.base_dir = base_dir
        logger.debug(f"StorageManager initialized with base_dir: {base_dir}")
    
    def _get_format_extension(self, format_type: str) -> str:
        """Get the file extension for a given format type.
        
        Args:
            format_type: Format type (e.g., 'json', 'yaml')
            
        Returns:
            File extension including dot
        """
        format_extensions = {
            'json': '.json',
            'yaml': '.yaml',
            'yml': '.yml'
        }
        return format_extensions.get(format_type.lower(), '.json')
    
    def store_map(self, project_map: ProjectMap, project_path: str, config: Configuration) -> str:
        """Store a project map.
        
        Args:
            project_map: Project map to store
            project_path: Path to the project
            config: Configuration object
            
        Returns:
            Path to the stored map file
            
        Raises:
            IOError: If the map cannot be stored
        """
        logger.debug(f"Storing project map for project at: {project_path}")
        
        try:
            # Create output directory
            output_dir = Path(project_path) / self.base_dir
            output_dir.mkdir(exist_ok=True)
            
            # Get format extension
            format_type = getattr(config, 'format_type', 'json')
            extension = self._get_format_extension(format_type)
            
            # Create output path
            output_path = output_dir / f"project_map{extension}"
            
            # Convert project map to dictionary
            map_dict = project_map.to_dict()
            
            # Add metadata
            map_dict['metadata'] = {
                'format_type': format_type,
                'version': '1.0.0',
                'config': {
                    'include_code': getattr(config, 'include_code', True),
                    'include_documentation': getattr(config, 'include_documentation', True),
                    'include_metadata': getattr(config, 'include_metadata', True),
                    'enable_chunking': getattr(config, 'enable_chunking', True),
                    'max_tokens': getattr(config, 'max_tokens', 2048),
                    'ai_optimize': getattr(config, 'ai_optimize', True)
                }
            }
            
            # Write to file
            logger.debug(f"Writing map to: {output_path}")
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(map_dict, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Project map stored at: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Error storing project map: {e}")
            raise IOError(f"Failed to store project map: {e}")
    
    def load_map(self, project_path: str) -> ProjectMap:
        """Load a project map.
        
        Args:
            project_path: Path to the project
            
        Returns:
            Loaded project map
            
        Raises:
            FileNotFoundError: If the map file doesn't exist
            ValueError: If the map file is invalid
        """
        logger.debug(f"Loading project map for project at: {project_path}")
        
        try:
            # Look for map file with any supported extension
            output_dir = Path(project_path) / self.base_dir
            map_file = None
            
            for ext in ['.json', '.yaml', '.yml']:
                potential_file = output_dir / f"project_map{ext}"
                if potential_file.exists():
                    map_file = potential_file
                    break
            
            if not map_file:
                raise FileNotFoundError(f"No project map found in: {output_dir}")
            
            logger.debug(f"Loading map from: {map_file}")
            
            # Read file
            with open(map_file, 'r', encoding='utf-8') as f:
                map_dict = json.load(f)
            
            # Create project map
            project_map = ProjectMap.from_dict(map_dict)
            
            logger.info(f"Project map loaded from: {map_file}")
            return project_map
            
        except FileNotFoundError:
            logger.error(f"Project map not found in: {project_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in project map: {e}")
            raise ValueError(f"Invalid project map format: {e}")
        except Exception as e:
            logger.error(f"Error loading project map: {e}")
            raise ValueError(f"Failed to load project map: {e}")
    
    def delete_map(self, project_path: str) -> None:
        """Delete a project map.
        
        Args:
            project_path: Path to the project
            
        Raises:
            FileNotFoundError: If the map file doesn't exist
        """
        logger.debug(f"Deleting project map for project at: {project_path}")
        
        try:
            # Look for map file with any supported extension
            output_dir = Path(project_path) / self.base_dir
            deleted = False
            
            for ext in ['.json', '.yaml', '.yml']:
                map_file = output_dir / f"project_map{ext}"
                if map_file.exists():
                    map_file.unlink()
                    deleted = True
                    logger.info(f"Deleted project map: {map_file}")
            
            if not deleted:
                raise FileNotFoundError(f"No project map found in: {output_dir}")
            
        except FileNotFoundError:
            logger.error(f"Project map not found in: {project_path}")
            raise
        except Exception as e:
            logger.error(f"Error deleting project map: {e}")
            raise 
    
    def get_latest_map(self, project_name: str) -> str | None:
        """
        Return absolute path to the most recently modified map file
        for `project_name` using the active backend.

        Args:
            project_name: Repository slug or project name.

        Returns:
            Absolute path (str) to the newest map or None if none exist.
        """
        backend = LocalFileSystemStorage(base_dir=self.base_dir)
        return backend.get_latest_map(project_name)