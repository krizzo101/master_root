"""Relationship detection rules.

This module contains the implementations of various relationship detection rules.
"""

import re
import logging
from typing import Optional, Union, Dict, Any

from proj_mapper.models.code import CodeElement, CodeElementType
from proj_mapper.models.documentation import DocumentationElement
from proj_mapper.models.relationship import Relationship, RelationshipType
from proj_mapper.relationship.detector.base import RelationshipRule

# Configure logging
logger = logging.getLogger(__name__)


class ImportRelationshipRule(RelationshipRule):
    """Rule for detecting import relationships between code elements."""
    
    @property
    def relationship_type(self) -> RelationshipType:
        return RelationshipType.IMPORTS
    
    def detect(self, source_element: Union[CodeElement, DocumentationElement],
              target_element: Union[CodeElement, DocumentationElement]) -> Optional[Relationship]:
        """Detect import relationships between code elements.
        
        Args:
            source_element: The source element to check
            target_element: The target element to check
            
        Returns:
            A Relationship object if an import is detected, None otherwise
        """
        # Only applicable for code elements
        if not isinstance(source_element, CodeElement) or not isinstance(target_element, CodeElement):
            return None
        
        # Check if target is imported by source
        if any(ref.reference_type == "import" and ref.reference_id == target_element.id 
               for ref in source_element.references):
            return Relationship(
                source_id=source_element.id,
                source_type="code",
                target_id=target_element.id,
                target_type="code",
                relationship_type=self.relationship_type,
                confidence=1.0,  # High confidence for explicit imports
                metadata={
                    "source_name": source_element.name,
                    "target_name": target_element.name,
                    "detection_rule": self.__class__.__name__
                }
            )
        
        return None


class InheritanceRelationshipRule(RelationshipRule):
    """Rule for detecting inheritance relationships between classes."""
    
    @property
    def relationship_type(self) -> RelationshipType:
        return RelationshipType.INHERITS
    
    def detect(self, source_element: Union[CodeElement, DocumentationElement],
              target_element: Union[CodeElement, DocumentationElement]) -> Optional[Relationship]:
        """Detect inheritance relationships between classes.
        
        Args:
            source_element: The source element to check
            target_element: The target element to check
            
        Returns:
            A Relationship object if inheritance is detected, None otherwise
        """
        # Only applicable for code elements
        if not isinstance(source_element, CodeElement) or not isinstance(target_element, CodeElement):
            return None
        
        # Only applicable for classes
        if source_element.element_type != CodeElementType.CLASS or target_element.element_type != CodeElementType.CLASS:
            return None
        
        # Check if source inherits from target
        if any(ref.reference_type == "inherit" and ref.reference_id == target_element.id 
               for ref in source_element.references):
            return Relationship(
                source_id=source_element.id,
                source_type="code",
                target_id=target_element.id,
                target_type="code",
                relationship_type=self.relationship_type,
                confidence=1.0,  # High confidence for explicit inheritance
                metadata={
                    "source_name": source_element.name,
                    "target_name": target_element.name,
                    "detection_rule": self.__class__.__name__
                }
            )
        
        return None


class FunctionCallRelationshipRule(RelationshipRule):
    """Rule for detecting function/method call relationships."""
    
    @property
    def relationship_type(self) -> RelationshipType:
        return RelationshipType.CALLS
    
    def detect(self, source_element: Union[CodeElement, DocumentationElement],
              target_element: Union[CodeElement, DocumentationElement]) -> Optional[Relationship]:
        """Detect function/method call relationships.
        
        Args:
            source_element: The source element to check
            target_element: The target element to check
            
        Returns:
            A Relationship object if a call is detected, None otherwise
        """
        # Only applicable for code elements
        if not isinstance(source_element, CodeElement) or not isinstance(target_element, CodeElement):
            return None
        
        # Check if target is called by source
        if any(ref.reference_type == "call" and ref.reference_id == target_element.id 
               for ref in source_element.references):
            return Relationship(
                source_id=source_element.id,
                source_type="code",
                target_id=target_element.id,
                target_type="code",
                relationship_type=self.relationship_type,
                confidence=1.0,  # High confidence for explicit calls
                metadata={
                    "source_name": source_element.name,
                    "target_name": target_element.name,
                    "detection_rule": self.__class__.__name__
                }
            )
        
        return None


class DocumentationReferenceRule(RelationshipRule):
    """Rule for detecting documentation references to code elements."""
    
    @property
    def relationship_type(self) -> RelationshipType:
        return RelationshipType.DOCUMENTS
    
    def detect(self, source_element: Union[CodeElement, DocumentationElement],
              target_element: Union[CodeElement, DocumentationElement]) -> Optional[Relationship]:
        """Detect documentation references to code elements.
        
        Args:
            source_element: The source element to check
            target_element: The target element to check
            
        Returns:
            A Relationship object if a documentation reference is detected, None otherwise
        """
        # Only applicable for doc -> code references
        if not isinstance(source_element, DocumentationElement) or not isinstance(target_element, CodeElement):
            return None
        
        # Check if the documentation element references the code element
        if any(ref.reference_type == "code" and ref.reference_id == target_element.id 
               for ref in source_element.references):
            return Relationship(
                source_id=source_element.id,
                source_type="doc",
                target_id=target_element.id,
                target_type="code",
                relationship_type=self.relationship_type,
                confidence=0.9,  # High confidence for explicit references
                metadata={
                    "source_title": source_element.title,
                    "target_name": target_element.name,
                    "detection_rule": self.__class__.__name__
                }
            )
        
        return None


class NameMatchRelationshipRule(RelationshipRule):
    """Rule for detecting relationships based on name matching."""
    
    def __init__(self, base_confidence: float = 0.7):
        """Initialize the name match rule.
        
        Args:
            base_confidence: Base confidence score for name matches
        """
        self.base_confidence = base_confidence
    
    @property
    def relationship_type(self) -> RelationshipType:
        return RelationshipType.RELATED_TO
    
    def detect(self, source_element: Union[CodeElement, DocumentationElement],
              target_element: Union[CodeElement, DocumentationElement]) -> Optional[Relationship]:
        """Detect relationships based on name similarity.
        
        Args:
            source_element: The source element to check
            target_element: The target element to check
            
        Returns:
            A Relationship object if name similarity is detected, None otherwise
        """
        # Get names to compare
        source_name = source_element.name if isinstance(source_element, CodeElement) else source_element.title
        target_name = target_element.name if isinstance(target_element, CodeElement) else target_element.title
        
        # Convert to lowercase for comparison
        source_name_lower = source_name.lower()
        target_name_lower = target_name.lower()
        
        # Calculate similarity score
        confidence = self._calculate_name_similarity(source_name_lower, target_name_lower)
        
        # Return relationship if confidence exceeds threshold
        if confidence > 0.3:
            return Relationship(
                source_id=source_element.id if isinstance(source_element, CodeElement) else source_element.title,
                source_type="code" if isinstance(source_element, CodeElement) else "doc",
                target_id=target_element.id if isinstance(target_element, CodeElement) else target_element.title,
                target_type="code" if isinstance(target_element, CodeElement) else "doc",
                relationship_type=self.relationship_type,
                confidence=confidence,
                metadata={
                    "source_name": source_name,
                    "target_name": target_name,
                    "detection_rule": self.__class__.__name__,
                    "similarity": confidence
                }
            )
        
        return None
    
    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate the similarity between two names.
        
        Args:
            name1: First name
            name2: Second name
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        # Exact match
        if name1 == name2:
            return 1.0
        
        # One is a substring of the other
        if name1 in name2 or name2 in name1:
            return 0.8
        
        # Split into parts and check for common parts
        parts1 = re.split(r'[_\-\s]', name1)
        parts2 = re.split(r'[_\-\s]', name2)
        
        # Count matching parts
        matching_parts = sum(1 for p1 in parts1 if any(p2 == p1 for p2 in parts2))
        total_parts = max(len(parts1), len(parts2))
        
        if total_parts > 0 and matching_parts > 0:
            return self.base_confidence * (matching_parts / total_parts)
        
        return 0.0


class ContentSimilarityRule(RelationshipRule):
    """Rule for detecting relationships based on content similarity."""
    
    def __init__(self, base_confidence: float = 0.6):
        """Initialize the content similarity rule.
        
        Args:
            base_confidence: Base confidence score for content similarities
        """
        self.base_confidence = base_confidence
    
    @property
    def relationship_type(self) -> RelationshipType:
        return RelationshipType.RELATED_TO
    
    def detect(self, source_element: Union[CodeElement, DocumentationElement],
              target_element: Union[CodeElement, DocumentationElement]) -> Optional[Relationship]:
        """Detect relationships based on content similarity.
        
        Args:
            source_element: The source element to check
            target_element: The target element to check
            
        Returns:
            A Relationship object if content similarity is detected, None otherwise
        """
        # Most useful for doc <-> code relationships
        if isinstance(source_element, DocumentationElement) and isinstance(target_element, CodeElement):
            doc_content = source_element.content
            code_content = target_element.docstring or ""
            
            # Skip if either content is empty
            if not doc_content or not code_content:
                return None
            
            # Calculate similarity
            similarity = self._calculate_content_similarity(doc_content, code_content)
            
            if similarity > 0.4:
                return Relationship(
                    source_id=source_element.title,
                    source_type="doc",
                    target_id=target_element.id,
                    target_type="code",
                    relationship_type=self.relationship_type,
                    confidence=similarity,
                    metadata={
                        "source_title": source_element.title,
                        "target_name": target_element.name,
                        "detection_rule": self.__class__.__name__,
                        "similarity": similarity
                    }
                )
        
        return None
    
    def _calculate_content_similarity(self, content1: str, content2: str) -> float:
        """Calculate the similarity between two text contents.
        
        Args:
            content1: First content
            content2: Second content
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        # Convert to lowercase and tokenize
        tokens1 = set(re.findall(r'\w+', content1.lower()))
        tokens2 = set(re.findall(r'\w+', content2.lower()))
        
        # Skip if either token set is empty
        if not tokens1 or not tokens2:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)
        
        jaccard = len(intersection) / len(union) if union else 0.0
        
        return min(self.base_confidence + (jaccard * 0.4), 1.0) 