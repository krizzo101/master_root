"""Base code models for Project Mapper.

This module contains fundamental code model types like Location, LocationModel,
and enumeration types shared across all code models.
"""

from enum import Enum, auto
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from dataclasses import dataclass

from pydantic import Field, validator, model_serializer

from proj_mapper.models.base import BaseModel
from proj_mapper.utils.json_encoder import register_serializer


class CodeElementType(Enum):
    """Types of code elements."""
    
    MODULE = auto()
    CLASS = auto()
    METHOD = auto()
    FUNCTION = auto()
    VARIABLE = auto()
    CONSTANT = auto()
    IMPORT = auto()
    
    @property
    def value(self) -> str:
        """Get the value of the enum, maintaining backward compatibility.
        
        For CodeElementType enums created using auto(), the .value attribute
        is not useful for serialization or display. This property returns
        the name of the enum instead, which is what was likely intended
        when code tried to access .value.
        
        Returns:
            The name of the enum as a string
        """
        return self.name


class Visibility(str, Enum):
    """Visibility levels for code elements."""
    
    PUBLIC = "public"
    PROTECTED = "protected"
    PRIVATE = "private"
    PACKAGE = "package"
    UNKNOWN = "unknown"


@dataclass
class Location:
    """Location in the codebase.
    
    Defines a starting and ending position in a file.
    """
    
    file_path: Union[str, Path]
    start_line: int
    end_line: int
    start_column: int = 0
    end_column: int = 0
    
    def __post_init__(self):
        """Convert file_path to Path if it's a string."""
        if isinstance(self.file_path, str):
            self.file_path = Path(self.file_path)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the Location to a dictionary.
        
        Returns:
            Dictionary with file_path, start_line, end_line, start_column, end_column
        """
        return {
            "file_path": str(self.file_path),
            "start_line": self.start_line,
            "end_line": self.end_line,
            "start_column": self.start_column,
            "end_column": self.end_column
        }
    
    def __str__(self) -> str:
        """Get string representation.
        
        Returns:
            String in the format file_path:start_line-end_line
        """
        return f"{self.file_path}:{self.start_line}-{self.end_line}"
        
    def model_dump(self) -> Dict[str, Any]:
        """Method to support Pydantic serialization.
        
        Returns:
            Dictionary representation of this Location
        """
        return self.to_dict()
        
    @classmethod
    def __get_validators__(cls):
        """For Pydantic v1 compatibility.
        
        Yields:
            Functions that validate a Location object
        """
        yield cls.validate
        
    @classmethod
    def validate(cls, v):
        """Validate and convert a value to a Location.
        
        Args:
            v: Value to validate
            
        Returns:
            Location object
            
        Raises:
            ValueError: If the value cannot be converted to a Location
        """
        if isinstance(v, cls):
            return v
        elif isinstance(v, dict):
            return cls(**v)
        elif isinstance(v, str):
            # Handle string format like "file.py:10-20"
            try:
                path_part, line_part = v.split(':', 1)
                start_line, end_line = map(int, line_part.split('-', 1))
                return cls(file_path=path_part, start_line=start_line, end_line=end_line)
            except Exception as e:
                raise ValueError(f"Cannot parse location string: {v}") from e
        raise ValueError(f"Cannot convert {type(v)} to Location")
        
    def __eq__(self, other):
        """Check if two locations are equal.
        
        Args:
            other: Another Location object
            
        Returns:
            True if the locations are equal, False otherwise
        """
        if not isinstance(other, Location):
            return False
        return (str(self.file_path) == str(other.file_path) and
                self.start_line == other.start_line and
                self.end_line == other.end_line and
                self.start_column == other.start_column and
                self.end_column == other.end_column)


# Register Location serializer function with the JSON encoder
register_serializer(Location, lambda loc: loc.to_dict())


class LocationModel(BaseModel):
    """Pydantic model for Location."""
    
    file_path: str = Field(..., description="Path to the file")
    start_line: Optional[int] = Field(None, description="Starting line number")
    end_line: Optional[int] = Field(None, description="Ending line number")
    start_column: Optional[int] = Field(None, description="Starting column number")
    end_column: Optional[int] = Field(None, description="Ending column number")
    
    @classmethod
    def from_location(cls, location: Location) -> 'LocationModel':
        """Create a LocationModel from a Location object.
        
        Args:
            location: Location object
            
        Returns:
            LocationModel
        """
        return cls(
            file_path=str(location.file_path),
            start_line=location.start_line,
            end_line=location.end_line,
            start_column=location.start_column,
            end_column=location.end_column
        )
    
    def to_location(self) -> Location:
        """Convert to a Location object.
        
        Returns:
            Location object
        """
        return Location(
            file_path=self.file_path,
            start_line=self.start_line,
            end_line=self.end_line,
            start_column=self.start_column,
            end_column=self.end_column
        )
    
    def __str__(self) -> str:
        """String representation of the location.
        
        Returns:
            String representation showing file path and line numbers
        """
        line_info = ""
        if self.start_line is not None:
            line_info = f":{self.start_line}"
            if self.end_line is not None and self.end_line != self.start_line:
                line_info += f"-{self.end_line}"
        
        return f"{self.file_path}{line_info}"


class CodeReference(BaseModel):
    """Represents a reference from one code element to another."""
    
    source_id: str = Field(..., description="ID of the source element making the reference")
    reference_id: str = Field(..., description="ID of the referenced element or resource")
    reference_type: str = Field(..., description="Type of reference (e.g., 'import', 'call', 'inherit')")
    location: Optional[LocationModel] = Field(None, description="Location of the reference in the source file")
    confidence: float = Field(default=1.0, description="Confidence score for this reference (0.0-1.0)")
    is_resolved: bool = Field(default=False, description="Whether the reference has been resolved to a known element")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata about the reference")
    
    def __str__(self) -> str:
        """Get string representation of the reference.
        
        Returns:
            String in the format "source -> target (type)"
        """
        return f"{self.source_id} -> {self.reference_id} ({self.reference_type})"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary representation.
        
        Returns:
            Dictionary with reference information
        """
        return {
            "source_id": self.source_id,
            "reference_id": self.reference_id,
            "reference_type": self.reference_type,
            "location": self.location.dict() if self.location else None,
            "confidence": self.confidence,
            "is_resolved": self.is_resolved,
        } 