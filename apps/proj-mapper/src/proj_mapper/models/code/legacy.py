"""Legacy code models for backward compatibility.

This module contains legacy dataclass versions of code models that are maintained
for backward compatibility with existing code.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set, Union

from proj_mapper.models.code.base import CodeElementType, Location


@dataclass
class CodeElement:
    """A code element found in the codebase.
    
    This is a legacy dataclass version maintained for backward compatibility.
    """
    
    id: str
    element_type: CodeElementType
    name: str
    location: Union[str, Location, Dict[str, Any]]
    content: str
    documentation: Optional[str] = None
    docstring: Optional[str] = None
    parent_id: Optional[str] = None
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
                     location: Optional[Union[Location, Dict[str, Any]]] = None,
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
                location_dict = location.to_dict()
            elif isinstance(location, dict):
                location_dict = location
            
        # Create a new reference as a dictionary
        reference = {
            "source_id": self.id,
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
            if (ref.get("reference_id") == reference_id and 
                ref.get("reference_type") == reference_type):
                return
        
        self.references.append(reference) 