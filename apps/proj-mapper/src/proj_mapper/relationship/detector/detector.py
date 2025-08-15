"""Relationship detector implementation.

This module provides the main detector class for relationship detection.
"""

import logging
from typing import List, Union, Optional

from proj_mapper.models.code import CodeElement
from proj_mapper.models.documentation import DocumentationElement
from proj_mapper.models.relationship import Relationship
from proj_mapper.relationship.detector.base import RelationshipRule
from proj_mapper.relationship.detector.rules import (
    ImportRelationshipRule,
    InheritanceRelationshipRule,
    FunctionCallRelationshipRule,
    DocumentationReferenceRule,
    NameMatchRelationshipRule,
    ContentSimilarityRule
)

# Configure logging
logger = logging.getLogger(__name__)


class RelationshipDetector:
    """Main component for detecting relationships between elements.
    
    This detector manages a set of relationship rules and applies them to detect
    relationships between code and documentation elements.
    """
    
    def __init__(self, config_manager=None):
        """Initialize the relationship detector with default rules.
        
        Args:
            config_manager: Optional configuration manager
        """
        self.rules: List[RelationshipRule] = [
            ImportRelationshipRule(),
            InheritanceRelationshipRule(),
            FunctionCallRelationshipRule(),
            DocumentationReferenceRule(),
            NameMatchRelationshipRule(),
            ContentSimilarityRule()
        ]
        
        # Additional initialization using config if provided
        self.config_manager = config_manager
    
    def add_rule(self, rule: RelationshipRule) -> None:
        """Add a relationship detection rule.
        
        Args:
            rule: The rule to add
        """
        self.rules.append(rule)
        logger.debug(f"Added relationship rule: {rule.__class__.__name__}")
    
    def detect_relationships(self, 
                           source_element: Union[CodeElement, DocumentationElement],
                           target_elements: List[Union[CodeElement, DocumentationElement]]) -> List[Relationship]:
        """Detect relationships between a source element and multiple target elements.
        
        Args:
            source_element: The source element
            target_elements: List of potential target elements
            
        Returns:
            List of detected relationships
        """
        relationships: List[Relationship] = []
        
        for target_element in target_elements:
            # Skip self-relationships
            if isinstance(source_element, CodeElement) and isinstance(target_element, CodeElement):
                if source_element.id == target_element.id:
                    continue
            elif isinstance(source_element, DocumentationElement) and isinstance(target_element, DocumentationElement):
                if source_element.title == target_element.title:
                    continue
            
            # Apply each rule
            for rule in self.rules:
                relationship = rule.detect(source_element, target_element)
                if relationship:
                    relationships.append(relationship)
        
        return relationships
    
    def detect_all_relationships(self,
                               code_elements: List[CodeElement],
                               doc_elements: List[DocumentationElement]) -> List[Relationship]:
        """Detect all relationships between the given code and documentation elements.
        
        Args:
            code_elements: List of code elements
            doc_elements: List of documentation elements
            
        Returns:
            List of all detected relationships
        """
        all_relationships: List[Relationship] = []
        
        # Code-to-code relationships
        for source in code_elements:
            relationships = self.detect_relationships(source, code_elements)
            all_relationships.extend(relationships)
        
        # Doc-to-doc relationships
        for source in doc_elements:
            relationships = self.detect_relationships(source, doc_elements)
            all_relationships.extend(relationships)
        
        # Code-to-doc relationships
        for source in code_elements:
            relationships = self.detect_relationships(source, [d for d in doc_elements])
            all_relationships.extend(relationships)
        
        # Doc-to-code relationships
        for source in doc_elements:
            relationships = self.detect_relationships(source, [c for c in code_elements])
            all_relationships.extend(relationships)
        
        logger.info(f"Detected {len(all_relationships)} total relationships")
        return all_relationships 