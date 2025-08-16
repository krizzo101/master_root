"""Project models module.

This module provides models for representing projects and project maps.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

from proj_mapper.models.file import DiscoveredFile, FileType


class Project:
    """Represents a project.
    
    Attributes:
        name: Name of the project
        root_path: Root path of the project
        files: List of discovered files
        analysis_results: Dictionary of analysis results
    """
    
    def __init__(
        self,
        name: str,
        root_path: Union[str, Path],
        files: Optional[List[DiscoveredFile]] = None,
        analysis_results: Optional[Dict[str, Any]] = None,
    ):
        """Initialize a project.
        
        Args:
            name: Name of the project
            root_path: Root path of the project
            files: Optional list of discovered files
            analysis_results: Optional dictionary of analysis results
        """
        self.name = name
        self.root_path = Path(root_path)
        self.files = files or []
        self.analysis_results = analysis_results or {}
    
    def __str__(self) -> str:
        """Get string representation.
        
        Returns:
            String representation
        """
        return f"{self.name} at {self.root_path}"
    
    def __repr__(self) -> str:
        """Get detailed string representation.
        
        Returns:
            Detailed string representation
        """
        return f"Project(name='{self.name}', root_path='{self.root_path}')"


class ProjectMap:
    """Represents a project map.
    
    Attributes:
        project: The project this map represents
        files: List of discovered files
        metadata: Optional metadata about the map
        timestamp: Timestamp of when the map was created
    """
    
    SCHEMA_VERSION = "1.0.0"
    
    def __init__(
        self,
        project: Project,
        files: Optional[List[DiscoveredFile]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[str] = None,
    ):
        """Initialize a project map.
        
        Args:
            project: The project this map represents
            files: Optional list of discovered files
            metadata: Optional metadata about the map
            timestamp: Optional timestamp string
        """
        self.project = project
        self.files = files or []
        self.metadata = metadata or {}
        self.timestamp = timestamp or datetime.utcnow().isoformat() + "Z"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the project map to a dictionary.
        
        Returns:
            Dictionary representation of the project map
        """
        # Convert files to dicts
        files = []
        for file in self.project.files:
            file_dict = {
                "path": str(file.relative_path),
                "type": file.file_type.value,
                "size": file.size,
                "modified_time": file.modified_time.isoformat() + "Z",
                "is_binary": file.is_binary,
                "is_directory": file.is_directory,
                "is_symlink": file.is_symlink,
            }
            
            # Add optional fields
            if file.created_time:
                file_dict["created_time"] = file.created_time.isoformat() + "Z"
            
            # Add metadata if available
            if file.metadata:
                file_dict["metadata"] = file.metadata
            
            files.append(file_dict)
        
        # Group files by type and create modules
        modules = []
        for file in self.project.files:
            if file.metadata.get('analysis'):
                module_data = file.metadata['analysis'].get('module')
                if module_data:
                    modules.append(module_data)
        
        # Extract relationships from elements
        relationships = []
        for file in self.project.files:
            if file.metadata.get('analysis'):
                analysis = file.metadata['analysis']
                if 'imports' in analysis:
                    for imp in analysis['imports']:
                        relationships.append({
                            "type": "import",
                            "source": str(file.relative_path),
                            "target": str(imp["path"]),
                            "confidence": imp.get("confidence", 1.0),
                        })
        
        # Convert metadata to JSON-serializable format
        serializable_metadata = {}
        for key, value in self.metadata.items():
            if hasattr(value, 'to_dict') and callable(getattr(value, 'to_dict')):
                serializable_metadata[key] = value.to_dict()
            elif hasattr(value, '__dict__') and callable(getattr(value, '__dict__')):
                serializable_metadata[key] = value.__dict__()
            else:
                # Try to convert any nested dictionaries
                if isinstance(value, dict):
                    serializable_metadata[key] = self._make_dict_serializable(value)
                else:
                    serializable_metadata[key] = value
        
        return {
            "schema_version": self.SCHEMA_VERSION,
            "project_name": self.project.name,
            "timestamp": self.timestamp,
            "metadata": serializable_metadata,
            "files": files,
            "modules": modules,
            "relationships": relationships,
        }
    
    def _make_dict_serializable(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make a dictionary JSON-serializable.
        
        Args:
            data: The dictionary to convert
            
        Returns:
            A serializable dictionary
        """
        result = {}
        for key, value in data.items():
            if hasattr(value, 'to_dict') and callable(getattr(value, 'to_dict')):
                result[key] = value.to_dict()
            elif hasattr(value, '__dict__') and callable(getattr(value, '__dict__')):
                result[key] = value.__dict__()
            elif isinstance(value, dict):
                result[key] = self._make_dict_serializable(value)
            elif isinstance(value, (list, tuple)):
                result[key] = [
                    item.to_dict() if hasattr(item, 'to_dict') and callable(getattr(item, 'to_dict')) 
                    else item.__dict__() if hasattr(item, '__dict__') and callable(getattr(item, '__dict__'))
                    else self._make_dict_serializable(item) if isinstance(item, dict)
                    else item
                    for item in value
                ]
            else:
                result[key] = value
        return result
    
    def __str__(self) -> str:
        """Get string representation.
        
        Returns:
            String representation
        """
        return f"Map for {self.project.name}"
    
    def __repr__(self) -> str:
        """Get detailed string representation.
        
        Returns:
            Detailed string representation
        """
        return f"ProjectMap(project={self.project}, files={len(self.files)})" 