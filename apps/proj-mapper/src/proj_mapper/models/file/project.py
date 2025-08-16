"""Project discovery model for Project Mapper.

This module contains the DiscoveredProject class used to represent projects in a file system.
"""

import fnmatch
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

from pydantic import Field

from proj_mapper.models.base import BaseModel
from proj_mapper.models.file.discovered import DiscoveredFile
from proj_mapper.models.file.types import FileType


class DiscoveredProject(BaseModel):
    """Represents a discovered project with its files and metadata."""
    
    name: str = Field(..., description="Project name")
    root_path: Path = Field(..., description="Absolute path to the project root")
    files: List[DiscoveredFile] = Field(default_factory=list, description="Files in the project")
    excluded_patterns: List[str] = Field(default_factory=list, description="Patterns for excluded files")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional project metadata")
    
    @classmethod
    def from_directory(cls, directory: Union[str, Path], name: Optional[str] = None, 
                      excluded_patterns: Optional[List[str]] = None) -> "DiscoveredProject":
        """Create a DiscoveredProject from a directory.
        
        Args:
            directory: Path to the project directory
            name: Optional project name (defaults to directory name)
            excluded_patterns: Optional list of glob patterns to exclude
            
        Returns:
            A new DiscoveredProject instance
            
        Raises:
            FileNotFoundError: If the directory doesn't exist
        """
        directory_path = Path(directory).resolve()
        
        if not directory_path.exists() or not directory_path.is_dir():
            raise FileNotFoundError(f"Directory not found: {directory_path}")
        
        if name is None:
            name = directory_path.name
            
        if excluded_patterns is None:
            excluded_patterns = [
                "**/.git/**",
                "**/.svn/**",
                "**/__pycache__/**",
                "**/node_modules/**",
                "**/venv/**",
                "**/.venv/**",
                "**/.env/**",
                "**/dist/**",
                "**/build/**",
                "**/.idea/**",
                "**/.vscode/**"
            ]
            
        files = []
        
        # Walk the directory and collect files
        for path in directory_path.glob("**/*"):
            # Skip excluded patterns
            skip = False
            relative_path = path.relative_to(directory_path)
            rel_path_str = str(relative_path)
            
            for pattern in excluded_patterns:
                if cls._matches_pattern(rel_path_str, pattern):
                    skip = True
                    break
                    
            if skip:
                continue
                
            # Create DiscoveredFile for each file
            try:
                if path.is_file():
                    file = DiscoveredFile.from_path(path, directory_path)
                    files.append(file)
            except Exception as e:
                print(f"Error processing file {path}: {e}")
                
        return cls(
            name=name,
            root_path=directory_path,
            files=files,
            excluded_patterns=excluded_patterns
        )
    
    @staticmethod
    def _matches_pattern(path: str, pattern: str) -> bool:
        """Check if a path matches a glob pattern.
        
        This is a simplified implementation of glob matching.
        
        Args:
            path: Path to check
            pattern: Glob pattern
            
        Returns:
            True if the path matches the pattern
        """
        return fnmatch.fnmatch(path, pattern)
    
    def get_files_by_type(self, file_type: FileType) -> List[DiscoveredFile]:
        """Get all files of a specific type.
        
        Args:
            file_type: The file type to filter by
            
        Returns:
            List of files matching the given type
        """
        return [f for f in self.files if f.file_type == file_type]
    
    def get_file_by_path(self, path: Union[str, Path]) -> Optional[DiscoveredFile]:
        """Get a file by its path.
        
        Args:
            path: Absolute or relative path to the file
            
        Returns:
            The DiscoveredFile or None if not found
        """
        path_obj = Path(path)
        
        # Try absolute path
        if path_obj.is_absolute():
            for file in self.files:
                if file.path == path_obj:
                    return file
        else:
            # Try relative path
            for file in self.files:
                if file.relative_path == str(path_obj):
                    return file
                
        return None
        
    @classmethod
    def create_mock(cls, name: str, files: Optional[List[DiscoveredFile]] = None, 
                   root_path: Optional[Union[str, Path]] = None) -> "DiscoveredProject":
        """Create a mock DiscoveredProject for testing purposes.
        
        Args:
            name: Project name
            files: List of DiscoveredFile instances (empty list if None)
            root_path: Project root path (defaults to a temporary path)
            
        Returns:
            A mock DiscoveredProject instance for testing
        """
        if files is None:
            files = []
            
        if root_path is None:
            root_path = Path(tempfile.gettempdir()) / name
            
        return cls(
            name=name,
            root_path=Path(root_path),
            files=files
        ) 