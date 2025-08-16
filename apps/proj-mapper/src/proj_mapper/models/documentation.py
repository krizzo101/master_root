"""Documentation model classes.

This module contains models related to documentation elements.
"""

from enum import Enum, auto
from typing import Dict, List, Optional, Any, Set, Union
from pathlib import Path
from pydantic import Field, validator, BaseModel as PydanticBaseModel
from dataclasses import dataclass, field

from proj_mapper.models.base import BaseModel
from proj_mapper.models.code import LocationModel, Location
from proj_mapper.utils.json_encoder import register_serializer


class DocumentationType(Enum):
    """Types of documentation elements."""
    
    SECTION = auto()
    CODE_BLOCK = auto()
    PARAGRAPH = auto()
    LIST = auto()
    LIST_ITEM = auto()
    MARKDOWN = auto()
    RST = auto()
    DOCSTRING = auto()
    COMMENT = auto()
    
    @property
    def value(self) -> str:
        """Get the value of the enum, maintaining backward compatibility.
        
        For DocumentationType enums created using auto(), the .value attribute
        is not useful for serialization or display. This property returns
        the name of the enum instead, which is what was likely intended
        when code tried to access .value.
        
        Returns:
            The name of the enum as a string
        """
        return self.name


# Alias for backward compatibility
DocumentationElementType = DocumentationType


@dataclass
class DocumentationElement:
    """A documentation element found in the codebase."""
    
    title: str
    element_type: DocumentationType
    location: Union[str, Location, LocationModel]
    content: str
    parent: Optional[str] = None
    children: List[str] = field(default_factory=list)
    references: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_child(self, child_id: str) -> None:
        """Add a child element to this element.
        
        Args:
            child_id: Identifier of the child element
        """
        if child_id not in self.children:
            self.children.append(child_id)
    
    def add_reference(self, reference_type: str, reference_id: str, 
                     location: Optional[Union[Location, LocationModel, Dict[str, Any]]] = None,
                     context: Optional[str] = None,
                     confidence: float = 1.0,
                     metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add a reference to another element.
        
        Args:
            reference_type: Type of the reference (code, doc, external)
            reference_id: Identifier of the referenced element
            location: Location information for the reference (optional)
            context: Context around the reference (optional)
            confidence: Confidence score for this reference
            metadata: Additional metadata for the reference (optional)
        """
        # Convert Location to dict if needed
        location_dict = None
        if location:
            if isinstance(location, Location):
                location_dict = {
                    "file": str(location.file_path),
                    "start_line": location.start_line,
                    "end_line": location.end_line,
                    "start_column": location.start_column,
                    "end_column": location.end_column
                }
            elif isinstance(location, LocationModel):
                location_dict = {
                    "file": str(location.file_path),
                    "start_line": location.start_line,
                    "end_line": location.end_line,
                    "start_column": location.start_column,
                    "end_column": location.end_column
                }
            elif isinstance(location, dict):
                # Handle dictionary location format
                file_path = location.get('file', '')
                if not file_path and 'file_path' in location:
                    file_path = location['file_path']
                    
                location_dict = {
                    "file": file_path,
                    "start_line": location.get('line', location.get('start_line')),
                    "end_line": location.get('end_line'),
                    "start_column": location.get('column', location.get('start_column')),
                    "end_column": location.get('end_column')
                }
                
        # Create a new reference as a dictionary
        reference = {
            "source_id": self.title,
            "reference_id": reference_id,
            "reference_type": reference_type,
            "confidence": confidence,
            "metadata": metadata or {}
        }
        
        # Add location and context if available
        if location_dict:
            reference["location"] = location_dict
            
        if context:
            reference["context"] = context
        
        # Check if a similar reference already exists
        for ref in self.references:
            if (ref["reference_id"] == reference_id and 
                ref["reference_type"] == reference_type):
                return
        
        self.references.append(reference)
    
    def to_reference(self) -> Dict[str, Any]:
        """Convert the element to a simplified reference format.
        
        Returns:
            A dictionary with key information about the element
        """
        location_info = None
        if isinstance(self.location, (Location, LocationModel)):
            location_info = {
                "file": str(self.location.file_path),
                "start_line": self.location.start_line,
                "end_line": self.location.end_line,
            }
        else:
            location_info = {"file": str(self.location)}
            
        return {
            "title": self.title,
            "type": self.element_type,
            "location": location_info
        }


class DocumentationReference(BaseModel):
    """Represents a reference from a documentation element to another resource.
    
    This can be a reference to code, another documentation element, or an external resource.
    """
    
    source_id: str = Field(..., description="ID of the source documentation element")
    reference_id: str = Field(..., description="ID of the referenced resource")
    reference_type: str = Field(..., description="Type of reference (e.g., 'code', 'doc', 'external')")
    location: Optional[LocationModel] = Field(None, description="Location of the reference within the document")
    context: Optional[str] = Field(None, description="Surrounding context of the reference")
    confidence: float = Field(default=1.0, description="Confidence score for this reference (0.0-1.0)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    def __str__(self) -> str:
        """Get string representation of the reference.
        
        Returns:
            String representation
        """
        return f"{self.source_id} -> {self.reference_id} ({self.reference_type})"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary representation.
        
        Returns:
            Dictionary with reference information
        """
        result = {
            "source_id": self.source_id,
            "reference_id": self.reference_id,
            "reference_type": self.reference_type,
            "confidence": self.confidence,
        }
        
        if self.location:
            result["location"] = {
                "file": str(self.location.file_path),
                "start_line": self.location.start_line,
                "end_line": self.location.end_line,
            }
            
        if self.context:
            result["context"] = self.context
            
        return result

# Register DocumentationReference serializer
register_serializer(DocumentationReference, lambda ref: ref.to_dict()) 