"""Relationship models for Project Mapper.

This module contains models related to relationships between code elements.
"""

from enum import Enum, auto
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, field_validator
from dataclasses import dataclass, field
import json


class RelationshipType(Enum):
    """Types of relationships between code elements.

    The enum specifies the different types of relationships that can exist
    between code elements.
    """

    # Class-related relationships
    INHERITS_FROM = auto()
    IMPLEMENTS = auto()

    # Function-related relationships
    CALLS = auto()
    OVERRIDES = auto()
    DECORATES = auto()

    # Module-related relationships
    IMPORTS = auto()
    IMPORTS_FROM = auto()
    
    # Variable-related relationships
    ASSIGNS = auto()
    REFERENCES = auto()

    # Object-related relationships
    INSTANTIATES = auto()
    CONTAINS = auto()

    # Type-related relationships
    RETURNS = auto()
    RECEIVES = auto()
    SUBSCRIBES = auto()

    # Test-related relationships
    TESTS = auto()
    MOCKS = auto()

    # Other relationships
    CONFIGURES = auto()
    EXTENDS = auto()
    IS_SIMILAR_TO = auto()
    
    # Documentation relationships
    DESCRIBES = auto()
    DESCRIBES_PARAMETER = auto()
    DESCRIBES_RETURN = auto()
    DESCRIBES_EXCEPTION = auto()
    REFERENCES_CODE = auto()

    @classmethod
    def get_inverse(cls, relationship_type: "RelationshipType") -> Optional["RelationshipType"]:
        """Get the inverse relationship type or None if not invertible.

        Args:
            relationship_type: The original relationship type

        Returns:
            The inverse relationship type or None if no inverse exists
        """
        if relationship_type == cls.INHERITS_FROM:
            return cls.CONTAINS
        elif relationship_type == cls.IMPLEMENTS:
            return None  # No direct inverse
        elif relationship_type == cls.CALLS:
            return cls.CALLED_BY  # Note: This doesn't exist yet
        elif relationship_type == cls.IMPORTS:
            return cls.IMPORTED_BY  # Note: This doesn't exist yet
        elif relationship_type == cls.IMPORTS_FROM:
            return cls.IMPORTED_BY  # Note: This doesn't exist yet
        elif relationship_type == cls.INSTANTIATES:
            return None  # No direct inverse
        elif relationship_type == cls.CONTAINS:
            return cls.INHERITS_FROM
        elif relationship_type == cls.RETURNS:
            return None  # No direct inverse
        elif relationship_type == cls.RECEIVES:
            return None  # No direct inverse
        elif relationship_type == cls.TESTS:
            return cls.TESTED_BY  # Note: This doesn't exist yet
        elif relationship_type == cls.CONFIGURES:
            return None  # No direct inverse
        return None
        
    @property
    def value(self) -> str:
        """Get the value of the enum, maintaining backward compatibility.
        
        For RelationshipType enums created using auto(), the .value attribute
        is not useful for serialization or display. This property returns
        the name of the enum instead, which is what was likely intended
        when code tried to access .value.
        
        Returns:
            The name of the enum as a string
        """
        return self.name


class Relationship(BaseModel):
    """Model for a relationship between two elements.

    The Relationship class models a relationship between a source and a target
    element, with a confidence score and optional metadata.
    """

    source_id: str = Field(..., description="The ID of the source element")
    target_id: str = Field(..., description="The ID of the target element")
    relationship_type: Union[RelationshipType, str] = Field(
        ..., description="The type of relationship between source and target"
    )
    confidence: float = Field(
        1.0,
        description="Confidence score for the relationship (0.0-1.0)",
        ge=0.0,
        le=1.0,
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Optional metadata for the relationship"
    )

    @field_validator("confidence")
    def check_confidence(cls, v):
        """Validate that confidence is between 0 and 1."""
        if not 0 <= v <= 1:
            raise ValueError("Confidence must be between 0 and 1")
        return v

    @field_validator("relationship_type")
    def validate_relationship_type(cls, v):
        """Validate the relationship type.
        
        Accept either a RelationshipType enum or a string matching a
        RelationshipType name.
        """
        if isinstance(v, str):
            try:
                return RelationshipType[v]
            except KeyError:
                # Allow string values for backward compatibility
                return v
        return v

    def to_dict(self) -> Dict[str, Any]:
        """Convert the relationship to a dictionary.

        Returns:
            Dictionary representation of the relationship
        """
        rel_type = self.relationship_type
        if isinstance(rel_type, RelationshipType):
            rel_type = rel_type.name

        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relationship_type": rel_type,
            "confidence": self.confidence,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Relationship":
        """Create a Relationship from a dictionary.

        Args:
            data: Dictionary with relationship data

        Returns:
            A new Relationship instance
        """
        return cls(**data)

    def to_json(self) -> str:
        """Convert the relationship to a JSON string.

        Returns:
            JSON string representation of the relationship
        """
        return json.dumps(self.to_dict())

    def get_inverse(self) -> Optional["Relationship"]:
        """Get the inverse of this relationship if possible.

        Returns:
            The inverse relationship or None if not invertible
        """
        inverse_type = RelationshipType.get_inverse(self.relationship_type)
        if inverse_type is None:
            return None

        return Relationship(
            source_id=self.target_id,
            target_id=self.source_id,
            relationship_type=inverse_type,
            confidence=self.confidence,
            metadata=self.metadata,
        )


@dataclass
class Relationship:
    """A relationship between two elements."""
    
    source_id: str
    target_id: str
    relationship_type: RelationshipType
    source_type: str = "unknown"
    target_type: str = "unknown"
    confidence: float = 1.0
    context: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict) 