"""CodeElement model for Project Mapper.

This module contains the primary CodeElement model that represents code structures
like classes, functions, and variables in the codebase.
"""

from typing import Dict, List, Optional, Any, Union

from pydantic import Field, field_validator

from proj_mapper.models.base import BaseModel
from proj_mapper.models.code.base import CodeElementType, Visibility, LocationModel, CodeReference, Location


class CodeElement(BaseModel):
    """Represents a code element such as a class, function, or variable."""
    
    id: str = Field(..., description="Unique identifier for the element")
    name: str = Field(..., description="Name of the code element")
    element_type: CodeElementType = Field(..., description="Type of code element")
    file_path: str = Field(..., description="Path to the file containing the element")
    
    # Location within file
    line_start: int = Field(..., description="Starting line number in the file")
    line_end: Optional[int] = Field(None, description="Ending line number in the file")
    col_start: Optional[int] = Field(None, description="Starting column in the file")
    col_end: Optional[int] = Field(None, description="Ending column in the file")
    
    # Hierarchical structure
    module: Optional[str] = Field(None, description="Module path or name containing this element")
    parent_id: Optional[str] = Field(None, description="ID of the parent element")
    children_ids: List[str] = Field(default_factory=list, description="IDs of child elements")
    
    # Element details
    visibility: Visibility = Field(default=Visibility.UNKNOWN, description="Visibility of the element")
    signature: Optional[str] = Field(None, description="Signature of the element (for functions/methods)")
    docstring: Optional[str] = Field(None, description="Documentation string")
    is_abstract: bool = Field(default=False, description="Whether the element is abstract")
    is_static: bool = Field(default=False, description="Whether the element is static")
    annotations: Dict[str, str] = Field(default_factory=dict, description="Type annotations or decorators")
    
    # Relationships
    dependencies: List[str] = Field(default_factory=list, 
                                  description="IDs of elements this element depends on")
    dependents: List[str] = Field(default_factory=list, 
                                description="IDs of elements that depend on this element")
    references: List[CodeReference] = Field(default_factory=list, 
                                description="References to other elements or resources")
    
    # Additional info
    complexity: Optional[float] = Field(None, description="Code complexity metric")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @field_validator('id')
    @classmethod
    def id_must_be_valid(cls, v: str) -> str:
        """Validate that the ID is properly formatted.
        
        Args:
            v: The ID value
            
        Returns:
            The validated ID
            
        Raises:
            ValueError: If the ID is invalid
        """
        if not v or len(v) < 3:
            raise ValueError("ID must be at least 3 characters long")
        return v
    
    def add_child(self, child_id: str) -> None:
        """Add a child element ID to this element.
        
        Args:
            child_id: The ID of the child element
        """
        if child_id not in self.children_ids:
            self.children_ids.append(child_id)
    
    def add_dependency(self, dependency_id: str) -> None:
        """Add a dependency element ID to this element.
        
        Args:
            dependency_id: The ID of the dependency element
        """
        if dependency_id not in self.dependencies:
            self.dependencies.append(dependency_id)
    
    def add_dependent(self, dependent_id: str) -> None:
        """Add a dependent element ID to this element.
        
        Args:
            dependent_id: The ID of the dependent element
        """
        if dependent_id not in self.dependents:
            self.dependents.append(dependent_id)
    
    def add_reference(self, reference_id: str, reference_type: str = "unknown", 
                     location: Optional[Union[Location, LocationModel]] = None, confidence: float = 1.0) -> None:
        """Add a reference to another element or resource.
        
        Args:
            reference_id: ID of the referenced element or resource
            reference_type: Type of reference relationship
            location: Optional location of the reference (Location or LocationModel)
            confidence: Confidence score for this reference
        """
        # Check if a reference to this ID and type already exists
        for ref in self.references:
            if ref.reference_id == reference_id and ref.reference_type == reference_type:
                return
        
        # Convert Location to LocationModel if needed
        location_model = None
        if location:
            if isinstance(location, Location):
                location_model = LocationModel.from_location(location)
            else:
                location_model = location
                
        # Create and add a new reference
        reference = CodeReference(
            source_id=self.id,
            reference_id=reference_id,
            reference_type=reference_type,
            location=location_model,
            confidence=confidence
        )
        self.references.append(reference)
    
    def to_reference(self) -> Dict[str, Any]:
        """Convert to a simplified reference format.
        
        Returns:
            Dictionary with basic element information
        """
        return {
            "id": self.id,
            "name": self.name,
            "element_type": self.element_type,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "module": self.module,
        }
    
    def get_full_name(self) -> str:
        """Get the fully qualified name including module path.
        
        Returns:
            Full name with module prefix
        """
        if self.module:
            return f"{self.module}.{self.name}"
        return self.name 
        
    @classmethod
    def create_mock(cls, id: str, name: str, element_type: CodeElementType, 
                  file_path: str, line_start: int = 1, line_end: Optional[int] = None,
                  references: Optional[List[CodeReference]] = None) -> "CodeElement":
        """Create a mock CodeElement for testing.
        
        Args:
            id: Unique identifier
            name: Element name
            element_type: Type of code element
            file_path: Path to the file
            line_start: Starting line number
            line_end: Ending line number
            references: List of references
            
        Returns:
            A mock CodeElement instance
        """
        element = cls(
            id=id,
            name=name,
            element_type=element_type,
            file_path=file_path,
            line_start=line_start,
            line_end=line_end or line_start + 5,
            module=None,
            parent_id=None
        )
        
        if references:
            element.references = references
            
        return element 