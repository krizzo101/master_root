"""File system storage provider.

This module provides storage implementation using the local file system.
"""

import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

from proj_mapper.output.config import GeneratorConfig
from proj_mapper.output.storage.base import MapStorageProvider
from proj_mapper.utils.json_encoder import EnumEncoder

# Configure logging
logger = logging.getLogger(__name__)


class LocalFileSystemStorage(MapStorageProvider):
    """Storage provider that uses the local file system."""
    
    def __init__(self, base_dir: str = ".maps"):
        """Initialize the storage provider.
        
        Args:
            base_dir: The base directory for storing maps
        """
        self.base_dir = base_dir
    
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
        # Create the maps directory if it doesn't exist
        self._ensure_maps_dir()
        
        # Sanitize the project name for use in filenames
        safe_project_name = self._sanitize_name(project_name)
        
        # Create the project directory if it doesn't exist
        project_dir = os.path.join(self.base_dir, safe_project_name)
        os.makedirs(project_dir, exist_ok=True)
        
        # Generate a timestamp for versioning
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Create the filename
        filename = f"{safe_project_name}_{timestamp}{format_extension}"
        file_path = os.path.join(project_dir, filename)
        
        # Add additional metadata
        generator_metadata = {
            "name": "Project Mapper",
            "version": "1.0.0",
            "timestamp": timestamp
        }
        
        if isinstance(map_data, dict):
            if "metadata" not in map_data:
                map_data["metadata"] = {}
            
            map_data["metadata"]["generator"] = generator_metadata
            map_data["metadata"]["timestamp"] = timestamp
            map_data["metadata"]["format"] = format_extension[1:]  # Remove the leading dot
            map_data["metadata"]["config"] = config.to_dict() if hasattr(config, 'to_dict') else config
        
        # Convert to JSON
        map_json = json.dumps(map_data, indent=2, cls=EnumEncoder)
        
        # Write to file
        with open(file_path, 'w') as f:
            f.write(map_json)
        
        logger.info(f"Stored map to {file_path}")
        
        # Update the latest symlink
        self._update_latest_link(project_dir, filename)
        
        # Generate an index file if it doesn't exist
        self._ensure_index_file(project_dir)
        
        # Update the index file with the new map
        self._update_index(project_dir, filename, config)
        
        return file_path
    
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
        # Create the maps directory if it doesn't exist
        self._ensure_maps_dir()
        
        # Sanitize the project name for use in filenames
        safe_project_name = self._sanitize_name(project_name)
        
        # Create the project directory if it doesn't exist
        project_dir = os.path.join(self.base_dir, safe_project_name)
        os.makedirs(project_dir, exist_ok=True)
        
        # Generate a timestamp for versioning
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Create a chunks directory for this map
        chunks_dir = os.path.join(project_dir, f"chunks_{timestamp}")
        os.makedirs(chunks_dir, exist_ok=True)
        
        # Store each chunk
        master_path = None
        for i, (chunk_id, chunk_data) in enumerate(chunked_map.items()):
            # Add additional metadata
            generator_metadata = {
                "name": "Project Mapper",
                "version": "1.0.0",
                "timestamp": timestamp
            }
            
            chunk_data["metadata"] = {
                "generator": generator_metadata,
                "chunk_id": chunk_id,
                "chunk_size": chunk_data.get("size", 0),
            }
            
            # Convert to JSON
            chunk_str = json.dumps(chunk_data, indent=2, cls=EnumEncoder)
            
            # Write to file
            chunk_file = os.path.join(chunks_dir, f"chunk_{i+1}.json")
            with open(chunk_file, 'w') as f:
                f.write(chunk_str)
            
            # Track the master chunk path
            if chunk_id == "master":
                master_path = chunk_file
        
        # Create a metadata file
        metadata = {
            "project": project_name,
            "timestamp": timestamp,
            "format": format_extension[1:],  # Remove the leading dot
            "chunks": list(chunked_map.keys()),
            "config": config.to_dict() if hasattr(config, 'to_dict') else config
        }
        
        metadata_path = os.path.join(chunks_dir, "metadata.json")
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
        
        # Update the latest chunked symlink
        latest_chunks_link = os.path.join(project_dir, "latest_chunks")
        if os.path.exists(latest_chunks_link):
            if os.path.islink(latest_chunks_link):
                os.unlink(latest_chunks_link)
            else:
                os.remove(latest_chunks_link)
        
        os.symlink(chunks_dir, latest_chunks_link, target_is_directory=True)
        
        logger.info(f"Stored chunked map to {chunks_dir}")
        
        return master_path or os.path.join(chunks_dir, "master" + format_extension)
    
    def get_latest_map(self, project_name: str) -> Optional[str]:
        """
        Return path to the newest map file (by modification time) or None.
        """
        safe_project_name = self._sanitize_name(project_name)
        project_dir = Path(self.base_dir) / safe_project_name
        if not project_dir.exists():
            return None

        # Gather candidate files
        candidates = list(project_dir.glob(f"{safe_project_name}_*.*"))
        if not candidates:
            return None

        latest = max(candidates, key=lambda p: p.stat().st_mtime)
        return str(latest.resolve())
    
    def get_map_history(self, project_name: str) -> List[Dict[str, Any]]:
        """Get the history of maps for a project.
        
        Args:
            project_name: The name of the project
            
        Returns:
            A list of map metadata dictionaries
        """
        # Sanitize the project name
        safe_project_name = self._sanitize_name(project_name)
        
        # Get the project directory
        project_dir = os.path.join(self.base_dir, safe_project_name)
        
        # Get the index file path
        index_path = os.path.join(project_dir, "_index.json")
        
        if not os.path.exists(index_path):
            return []
        
        # Load the index file
        with open(index_path, "r", encoding="utf-8") as f:
            index = json.load(f)
        
        return index
    
    def clean_old_maps(self, project_name: str, keep_count: int = 5) -> int:
        """Clean old maps for a project.
        
        Args:
            project_name: The name of the project
            keep_count: The number of maps to keep
            
        Returns:
            The number of maps deleted
        """
        # Sanitize the project name
        safe_project_name = self._sanitize_name(project_name)
        
        # Get the project directory
        project_dir = os.path.join(self.base_dir, safe_project_name)
        
        # Get all map files
        map_files = []
        for filename in os.listdir(project_dir):
            if filename.endswith(".json") and not filename == "index.json":
                map_files.append(filename)
        
        # Sort by timestamp (newest first)
        map_files.sort(reverse=True)
        
        # Delete old maps
        deleted_count = 0
        for filename in map_files[keep_count:]:
            file_path = os.path.join(project_dir, filename)
            try:
                os.remove(file_path)
                deleted_count += 1
            except Exception as e:
                logger.error(f"Error deleting map file {file_path}: {e}")
        
        return deleted_count
    
    def _ensure_maps_dir(self) -> None:
        """Create the maps directory if it doesn't exist."""
        os.makedirs(self.base_dir, exist_ok=True)
    
    def _sanitize_name(self, name: str) -> str:
        """Sanitize a name for use in filenames.
        
        Args:
            name: The name to sanitize
            
        Returns:
            The sanitized name
        """
        # Replace spaces with underscores and remove special characters
        return re.sub(r'[^\w\-_.]', '', name.replace(' ', '_'))
    
    def _update_latest_link(self, project_dir: str, filename: str) -> None:
        """Update the latest symlink for a project.
        
        Args:
            project_dir: The project directory
            filename: The filename to link to
        """
        latest_link = os.path.join(project_dir, "latest")
        if os.path.exists(latest_link):
            if os.path.islink(latest_link):
                os.unlink(latest_link)
            else:
                os.remove(latest_link)
        
        os.symlink(filename, latest_link)
    
    def _ensure_index_file(self, project_dir: str) -> None:
        """Make sure the index file exists.
        
        Args:
            project_dir: The project directory
        """
        index_path = os.path.join(project_dir, "_index.json")
        if not os.path.exists(index_path):
            with open(index_path, "w", encoding="utf-8") as f:
                json.dump([], f, indent=2)
    
    def _update_index(self, project_dir: str, filename: str, config: GeneratorConfig) -> None:
        """Update the index file with a new map.
        
        Args:
            project_dir: The project directory
            filename: The filename of the new map
            config: The generator configuration
        """
        # Load the existing index
        index_file = os.path.join(project_dir, "_index.json")
        index = []
        if os.path.exists(index_file):
            try:
                with open(index_file, "r", encoding="utf-8") as f:
                    index = json.load(f)
            except json.JSONDecodeError:
                # Invalid JSON, creating a new index
                index = []
        
        # Get information about the map file
        map_file = os.path.join(project_dir, filename)
        stats = os.stat(map_file)
        mod_time = stats.st_mtime
        size = stats.st_size
        
        # Create a config dictionary if needed
        config_dict = config.to_dict() if hasattr(config, 'to_dict') else config
        
        # Create the entry
        entry = {
            "filename": filename,
            "timestamp": datetime.now().isoformat() + "Z",
            "modified_time": datetime.fromtimestamp(mod_time).isoformat() + "Z",
            "size": size,
            "config": config_dict
        }
        
        # Add the entry to the index
        index.append(entry)
        
        # Sort the index by timestamp (newest first)
        index.sort(key=lambda x: x["timestamp"], reverse=True)
        
        # Write the index
        with open(index_file, "w", encoding="utf-8") as f:
            json.dump(index, f, indent=2) 