"""Cross-reference resolver for Project Mapper.

This module provides functionality for resolving cross-references between
code and documentation elements.
"""

import logging
import re
from difflib import SequenceMatcher
from typing import Dict, List, Optional, Tuple, Set, Any, Union

from proj_mapper.models.code import CodeElement
from proj_mapper.models.documentation import DocumentationElement, DocumentationReference
from proj_mapper.models.relationship import Relationship, RelationshipType

# Configure logging
logger = logging.getLogger(__name__)


class ReferenceCandidate:
    """A potential match between a reference and an element.
    
    This class is used to represent a potential match during cross-reference resolution.
    """
    
    def __init__(self, 
                element_id: str, 
                element_type: str, 
                match_score: float, 
                metadata: Dict[str, Any] = None):
        """Initialize a reference candidate.
        
        Args:
            element_id: The ID of the potential matching element
            element_type: The type of the element ('code' or 'doc')
            match_score: The confidence score for this match (0.0-1.0)
            metadata: Additional information about the match
        """
        self.element_id = element_id
        self.element_type = element_type
        self.match_score = match_score
        self.metadata = metadata or {}
    
    def __str__(self) -> str:
        """Get string representation of the candidate.
        
        Returns:
            String representation with type and confidence
        """
        return f"{self.element_type}:{self.element_id} ({self.match_score:.2f})"


class ReferenceMatch:
    """A confirmed match between a reference and an element.
    
    This class is used to represent a resolved cross-reference.
    """
    
    def __init__(self,
                source_id: str,
                source_type: str,
                target_id: str,
                target_type: str,
                confidence: float,
                match_type: str,
                metadata: Dict[str, Any] = None):
        """Initialize a reference match.
        
        Args:
            source_id: The ID of the referring element
            source_type: The type of the referring element ('code' or 'doc')
            target_id: The ID of the referenced element
            target_type: The type of the referenced element ('code' or 'doc')
            confidence: The confidence score for this match (0.0-1.0)
            match_type: The type of match (e.g., 'exact', 'fuzzy', 'partial')
            metadata: Additional information about the match
        """
        self.source_id = source_id
        self.source_type = source_type
        self.target_id = target_id
        self.target_type = target_type
        self.confidence = confidence
        self.match_type = match_type
        self.metadata = metadata or {}
    
    def to_relationship(self) -> Relationship:
        """Convert match to a relationship.
        
        Returns:
            A Relationship object representing this match
        """
        # Determine relationship type
        if self.source_type == "doc" and self.target_type == "code":
            rel_type = RelationshipType.DOCUMENTS
        elif self.source_type == "code" and self.target_type == "doc":
            rel_type = RelationshipType.DOCUMENTED_BY
        elif self.match_type == "import":
            rel_type = RelationshipType.IMPORTS
        elif self.match_type == "call":
            rel_type = RelationshipType.CALLS
        elif self.match_type == "inherit":
            rel_type = RelationshipType.INHERITS_FROM
        else:
            rel_type = RelationshipType.REFERENCES
        
        # Create and return the relationship
        return Relationship(
            source_id=self.source_id,
            target_id=self.target_id,
            relationship_type=rel_type,
            confidence=self.confidence,
            metadata={
                **self.metadata,
                "match_type": self.match_type,
                "reference_match": True,
            }
        )


class CrossReferenceResolver:
    """Resolver for cross-references between code and documentation.
    
    This component resolves references between different elements, especially
    references from documentation to code elements.
    """
    
    def __init__(self, fuzzy_threshold: float = 0.7):
        """Initialize the cross-reference resolver.
        
        Args:
            fuzzy_threshold: Minimum similarity score for fuzzy matching (0.0-1.0)
        """
        self.fuzzy_threshold = fuzzy_threshold
        self.code_elements: Dict[str, CodeElement] = {}
        self.doc_elements: Dict[str, DocumentationElement] = {}
    
    def add_code_elements(self, elements: List[CodeElement]) -> None:
        """Add code elements for reference resolution.
        
        Args:
            elements: List of code elements to add
        """
        for element in elements:
            self.code_elements[element.id] = element
        logger.debug(f"Added {len(elements)} code elements to reference resolver")
    
    def add_documentation_elements(self, elements: List[DocumentationElement]) -> None:
        """Add documentation elements for reference resolution.
        
        Args:
            elements: List of documentation elements to add
        """
        for element in elements:
            self.doc_elements[element.title] = element
        logger.debug(f"Added {len(elements)} documentation elements to reference resolver")
    
    def resolve_doc_references(self) -> List[ReferenceMatch]:
        """Resolve references from documentation elements.
        
        Returns:
            List of resolved reference matches
        """
        matches: List[ReferenceMatch] = []
        
        for doc_id, doc_element in self.doc_elements.items():
            # Process each reference in the documentation element
            for doc_ref in doc_element.references:
                # Skip if already resolved
                if doc_ref.metadata.get("resolved", False):
                    continue
                
                # If it's a code reference with a specific ID
                if doc_ref.reference_type == "code" and doc_ref.reference_id:
                    # Check if it's a direct reference to a known code element
                    if doc_ref.reference_id in self.code_elements:
                        match = ReferenceMatch(
                            source_id=doc_id,
                            source_type="doc",
                            target_id=doc_ref.reference_id,
                            target_type="code",
                            confidence=doc_ref.confidence,
                            match_type="exact",
                            metadata={
                                "source_title": doc_element.title,
                                "target_name": self.code_elements[doc_ref.reference_id].name,
                                "reference_context": doc_ref.context
                            }
                        )
                        matches.append(match)
                        continue
                
                # Try fuzzy matching for unresolved references
                context = doc_ref.context or ""
                if context:
                    candidates = self._find_code_candidates(context)
                    if candidates:
                        best_candidate = max(candidates, key=lambda c: c.match_score)
                        if best_candidate.match_score >= self.fuzzy_threshold:
                            match = ReferenceMatch(
                                source_id=doc_id,
                                source_type="doc",
                                target_id=best_candidate.element_id,
                                target_type="code",
                                confidence=best_candidate.match_score,
                                match_type="fuzzy",
                                metadata={
                                    "source_title": doc_element.title,
                                    "target_name": self.code_elements[best_candidate.element_id].name,
                                    "reference_context": context,
                                    "match_score": best_candidate.match_score
                                }
                            )
                            matches.append(match)
        
        logger.info(f"Resolved {len(matches)} documentation references")
        return matches
    
    def resolve_code_references(self) -> List[ReferenceMatch]:
        """Resolve references from code elements.
        
        Returns:
            List of resolved reference matches
        """
        matches: List[ReferenceMatch] = []
        
        for code_id, code_element in self.code_elements.items():
            # Process each reference in the code element
            for code_ref in code_element.references:
                # Skip if not resolvable
                if not code_ref.reference_id or code_ref.is_resolved:
                    continue
                
                # Check if it's a direct reference to a known code element
                if code_ref.reference_id in self.code_elements:
                    match = ReferenceMatch(
                        source_id=code_id,
                        source_type="code",
                        target_id=code_ref.reference_id,
                        target_type="code",
                        confidence=code_ref.confidence,
                        match_type=code_ref.reference_type,
                        metadata={
                            "source_name": code_element.name,
                            "target_name": self.code_elements[code_ref.reference_id].name,
                            "reference_location": str(code_ref.location) if code_ref.location else None
                        }
                    )
                    matches.append(match)
        
        logger.info(f"Resolved {len(matches)} code references")
        return matches
    
    def resolve_all_references(self) -> List[ReferenceMatch]:
        """Resolve all references.
        
        Returns:
            List of all resolved reference matches
        """
        doc_matches = self.resolve_doc_references()
        code_matches = self.resolve_code_references()
        
        return doc_matches + code_matches
    
    def _find_code_candidates(self, text: str) -> List[ReferenceCandidate]:
        """Find code elements that might be referenced in the given text.
        
        Args:
            text: The text to search for references
            
        Returns:
            List of candidate matches
        """
        candidates: List[ReferenceCandidate] = []
        
        # Extract potential code names from text
        code_names = self._extract_potential_code_names(text)
        
        # Check each extracted name against code elements
        for name in code_names:
            for code_id, code_element in self.code_elements.items():
                # Calculate name similarity
                similarity = self._calculate_similarity(name, code_element.name)
                
                if similarity >= self.fuzzy_threshold:
                    candidates.append(ReferenceCandidate(
                        element_id=code_id,
                        element_type="code",
                        match_score=similarity,
                        metadata={
                            "name": code_element.name,
                            "extracted_name": name,
                            "similarity": similarity
                        }
                    ))
        
        return candidates
    
    def _extract_potential_code_names(self, text: str) -> Set[str]:
        """Extract potential code names from text.
        
        Args:
            text: The text to process
            
        Returns:
            Set of potential code names
        """
        names: Set[str] = set()
        
        # Look for text in backticks, which often indicates code
        backtick_pattern = r'`([^`]+)`'
        for match in re.finditer(backtick_pattern, text):
            names.add(match.group(1).strip())
        
        # Look for CamelCase or PascalCase names, common in code
        camel_case_pattern = r'\b([A-Z][a-z0-9]+[A-Z]|[A-Z][A-Za-z0-9]*)\b'
        for match in re.finditer(camel_case_pattern, text):
            names.add(match.group(1).strip())
        
        # Look for snake_case names, common in code
        snake_case_pattern = r'\b([a-z][a-z0-9]*(_[a-z0-9]+)+)\b'
        for match in re.finditer(snake_case_pattern, text):
            names.add(match.group(1).strip())
        
        return names
    
    def _calculate_similarity(self, name1: str, name2: str) -> float:
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
        
        # Lowercase comparison
        if name1.lower() == name2.lower():
            return 0.95
        
        # One is a substring of the other
        if name1 in name2:
            return 0.9
        if name2 in name1:
            return 0.85
        
        # Use sequence matcher for fuzzier matching
        matcher = SequenceMatcher(None, name1.lower(), name2.lower())
        return matcher.ratio() 