"""Discovered file model for Project Mapper.

This module contains the DiscoveredFile class used to represent files found in a project.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any, Union

from pydantic import Field, field_validator

from proj_mapper.models.base import BaseModel
from proj_mapper.models.file.types import FileType


class DiscoveredFile(BaseModel):
    """Represents a file discovered in the project."""
    
    path: Path = Field(..., description="Absolute path to the file")
    relative_path: str = Field(..., description="Path relative to project root")
    file_type: FileType = Field(..., description="Type of the file")
    size: int = Field(..., description="Size of the file in bytes")
    modified_time: datetime = Field(..., description="Last modification time")
    created_time: Optional[datetime] = Field(None, description="Creation time if available")
    is_binary: bool = Field(False, description="Whether the file is binary or text")
    is_directory: bool = Field(False, description="Whether this is a directory")
    is_symlink: bool = Field(False, description="Whether this is a symbolic link")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional file metadata")
    
    @field_validator("file_type", mode="before")
    @classmethod
    def set_file_type_from_path(cls, v: Any, info) -> FileType:
        """Determine file type from path if not provided.
        
        Args:
            v: The current value
            info: The validation info containing field values
            
        Returns:
            The determined file type
        """
        if v is not None and isinstance(v, FileType):
            return v
        
        # In Pydantic V2, we need to access field values differently
        field_values = info.data
        path = field_values.get("path")
        if path is None:
            return FileType.UNKNOWN
        
        suffix = Path(path).suffix
        return FileType.from_extension(suffix)
    
    @classmethod
    def from_path(cls, path: Union[str, Path], project_root: Union[str, Path]) -> "DiscoveredFile":
        """Create a DiscoveredFile instance from a file path.
        
        Args:
            path: Path to the file
            project_root: Root path of the project
            
        Returns:
            A new DiscoveredFile instance
            
        Raises:
            FileNotFoundError: If the file doesn't exist
        """
        path_obj = Path(path).resolve()
        root_obj = Path(project_root).resolve()
        
        if not path_obj.exists():
            raise FileNotFoundError(f"File not found: {path_obj}")
        
        try:
            relative = path_obj.relative_to(root_obj)
        except ValueError:
            # Fall back to using the filename if not under project root
            relative = path_obj.name
        
        stat = path_obj.stat()
        
        return cls(
            path=path_obj,
            relative_path=str(relative),
            file_type=FileType.from_extension(path_obj.suffix),
            size=stat.st_size,
            modified_time=datetime.fromtimestamp(stat.st_mtime),
            created_time=datetime.fromtimestamp(stat.st_ctime),
            is_binary=cls._is_binary(path_obj),
            is_directory=path_obj.is_dir(),
            is_symlink=path_obj.is_symlink(),
        )
    
    @staticmethod
    def _is_binary(path: Path) -> bool:
        """Check if a file is likely binary.
        
        Args:
            path: The path to check
            
        Returns:
            True if the file is likely binary, False otherwise
        """
        # Skip check for directories
        if path.is_dir():
            return False
            
        # Common binary extensions
        binary_extensions = {
            ".pyc", ".pyd", ".so", ".dll", ".exe", ".bin", ".dat",
            ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".ico", ".tif", ".tiff",
            ".mp3", ".mp4", ".avi", ".mov", ".mkv", ".wav", ".flac",
            ".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx",
            ".zip", ".tar", ".gz", ".bz2", ".xz", ".7z", ".rar",
        }
        
        if path.suffix.lower() in binary_extensions:
            return True
        
        # Check file content
        try:
            # Read first 8KB of the file
            chunk_size = 8192
            with open(path, 'rb') as f:
                chunk = f.read(chunk_size)
                
            # Check for null bytes which often indicate binary
            if b'\x00' in chunk:
                return True
                
            # Try decoding as UTF-8
            try:
                chunk.decode('utf-8')
                return False
            except UnicodeDecodeError:
                return True
                
        except (IOError, OSError):
            # If we can't read the file, assume it's binary
            return True
            
        return False
    
    @classmethod
    def create_mock(cls, path: Union[str, Path], relative_path: Optional[str] = None, 
                    file_type: Optional[FileType] = None) -> "DiscoveredFile":
        """Create a mock DiscoveredFile instance for testing purposes.
        
        This method creates a simplified mock instance without checking if the file exists.
        
        Args:
            path: Path to the file
            relative_path: Relative path to the file (defaults to the basename of path)
            file_type: File type (detected from path if not provided)
            
        Returns:
            A mock DiscoveredFile instance for testing
        """
        path_obj = Path(path)
        
        if relative_path is None:
            relative_path = path_obj.name
            
        # Handle string file_type
        if isinstance(file_type, str):
            file_type_obj = file_type  # Will be converted by the validator
        elif file_type is None:
            file_type_obj = FileType.from_extension(path_obj.suffix)
        else:
            file_type_obj = file_type
            
        # Use fixed values for testing
        return cls(
            path=path_obj,
            relative_path=relative_path,
            file_type=file_type_obj,
            size=1024,  # Arbitrary size
            modified_time=datetime.now(),
            created_time=datetime.now(),
            is_binary=False,
            is_directory=False,
            is_symlink=False,
            metadata={}
        )
    
    def get_directory(self) -> Path:
        """Get the directory containing this file.
        
        Returns:
            Path to the containing directory
        """
        return self.path.parent
    
    def get_extension(self) -> str:
        """Get the file extension.
        
        Returns:
            File extension with leading dot
        """
        return self.path.suffix
    
    def get_name(self) -> str:
        """Get the filename without extension.
        
        Returns:
            Filename without extension
        """
        return self.path.stem
    
    def get_full_name(self) -> str:
        """Get the full filename with extension.
        
        Returns:
            Full filename
        """
        return self.path.name
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary representation.
        
        Returns:
            Dictionary with file information
        """
        return {
            "path": str(self.path),
            "relative_path": self.relative_path,
            "file_type": self.file_type.value,  # Convert enum to string value
            "size": self.size,
            "modified_time": self.modified_time.isoformat(),
            "created_time": self.created_time.isoformat() if self.created_time else None,
            "is_binary": self.is_binary,
            "is_directory": self.is_directory,
            "is_symlink": self.is_symlink,
        } 