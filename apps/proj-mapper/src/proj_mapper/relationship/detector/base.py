"""Base classes for relationship detection.

This module contains the base classes and interfaces for relationship detection.
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional, Union

from proj_mapper.models.code import CodeElement
from proj_mapper.models.documentation import DocumentationElement
from proj_mapper.models.relationship import Relationship, RelationshipType

# Configure logging
logger = logging.getLogger(__name__)


class RelationshipRule(ABC):
    """Abstract base class for relationship detection rules.
    
    Rules define specific heuristics for identifying relationships between elements.
    """
    
    @abstractmethod
    def detect(self, source_element: Union[CodeElement, DocumentationElement],
              target_element: Union[CodeElement, DocumentationElement]) -> Optional[Relationship]:
        """Detect if a relationship exists between the elements.
        
        Args:
            source_element: The source element to check
            target_element: The target element to check
            
        Returns:
            A Relationship object if detected, None otherwise
        """
        pass
    
    @property
    def relationship_type(self) -> RelationshipType:
        """Get the type of relationship this rule detects.
        
        Returns:
            The relationship type
        """
        return RelationshipType.OTHER 