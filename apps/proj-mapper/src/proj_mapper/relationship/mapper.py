"""Relationship mapping component for Project Mapper.

This module provides functionality for mapping relationships between code and documentation.
"""

import logging
import re
from typing import Dict, List, Set, Tuple, Optional, Any
from collections import defaultdict
from dataclasses import dataclass, field

from proj_mapper.models.code import CodeElement, CodeElementType
from proj_mapper.models.documentation import DocumentationElement, DocumentationType
from proj_mapper.models.relationship import Relationship, RelationshipType
from proj_mapper.core.pipeline import PipelineStage, PipelineContext
from proj_mapper.relationship.function_analyzer import FunctionCallAnalyzer

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class RelationshipMapper:
    """Maps relationships between code and documentation elements."""
    
    code_elements: Dict[str, CodeElement] = field(default_factory=dict)
    doc_elements: Dict[str, DocumentationElement] = field(default_factory=dict)
    relationships: List[Relationship] = field(default_factory=list)
    
    def add_code_elements(self, elements: List[CodeElement]) -> None:
        """Add code elements to the mapper.
        
        Args:
            elements: List of code elements to add
        """
        for element in elements:
            self.code_elements[element.id] = element
            
    def add_doc_elements(self, elements: List[DocumentationElement]) -> None:
        """Add documentation elements to the mapper.
        
        Args:
            elements: List of documentation elements to add
        """
        for element in elements:
            self.doc_elements[element.title] = element
            
    def map_relationships(self) -> List[Relationship]:
        """Map relationships between all elements.
        
        Returns:
            List of identified relationships
        """
        self.relationships = []
        
        # Map documentation references
        self._map_doc_to_code_refs()
        self._map_code_to_doc_refs()
        
        # Map code relationships
        self._map_function_calls()
        self._map_inheritance()
        
        # Map documentation relationships
        self._map_doc_to_doc_refs()
        
        return self.relationships
        
    def _map_doc_to_code_refs(self) -> None:
        """Map references from documentation to code elements."""
        for doc_id, doc in self.doc_elements.items():
            for code_id, code in self.code_elements.items():
                # Look for class/function names in documentation
                if code.name in doc.content:
                    confidence = self._calculate_doc_ref_confidence(doc.content, code)
                    if confidence > 0:
                        self.relationships.append(
                            Relationship(
                                source_id=doc_id,
                                target_id=code_id,
                                relationship_type=RelationshipType.REFERENCES,
                                confidence=confidence,
                                context=self._extract_reference_context(doc.content, code.name)
                            )
                        )
                        
    def _map_code_to_doc_refs(self) -> None:
        """Map references from code to documentation elements."""
        for code_id, code in self.code_elements.items():
            docstring = code.docstring or ""
            for doc_id, doc in self.doc_elements.items():
                # Look for documentation references in docstrings
                doc_name = doc.title.replace(".md", "")
                if doc_name.lower() in docstring.lower():
                    confidence = self._calculate_doc_ref_confidence(docstring, doc)
                    if confidence > 0:
                        self.relationships.append(
                            Relationship(
                                source_id=code_id,
                                target_id=doc_id,
                                relationship_type=RelationshipType.REFERENCES,
                                confidence=confidence,
                                context=self._extract_reference_context(docstring, doc_name)
                            )
                        )
                        
    def _map_function_calls(self) -> None:
        """Map function call relationships between code elements."""
        for source_id, source in self.code_elements.items():
            if "body" not in source.metadata:
                continue
                
            body = source.metadata["body"]
            for target_id, target in self.code_elements.items():
                if source_id == target_id:
                    continue
                    
                # Look for method calls in the function body
                if f"self.{target.name}" in body:
                    self.relationships.append(
                        Relationship(
                            source_id=source_id,
                            target_id=target_id,
                            relationship_type=RelationshipType.CALLS,
                            confidence=0.95,  # High confidence for explicit calls
                            context=self._extract_reference_context(body, target.name)
                        )
                    )
                    
    def _map_inheritance(self) -> None:
        """Map inheritance relationships between classes."""
        for source_id, source in self.code_elements.items():
            if "bases" not in source.metadata:
                continue
                
            for base in source.metadata["bases"]:
                for target_id, target in self.code_elements.items():
                    if target.name == base:
                        self.relationships.append(
                            Relationship(
                                source_id=source_id,
                                target_id=target_id,
                                relationship_type=RelationshipType.INHERITS_FROM,
                                confidence=1.0,  # Inheritance is explicit
                                context=f"Class {source.name} inherits from {target.name}"
                            )
                        )
                        
    def _map_doc_to_doc_refs(self) -> None:
        """Map references between documentation elements."""
        for source_id, source in self.doc_elements.items():
            for target_id, target in self.doc_elements.items():
                if source_id == target_id:
                    continue
                    
                # Look for markdown links to other docs
                if f"[{target.title}]" in source.content or f"]({target.title})" in source.content:
                    self.relationships.append(
                        Relationship(
                            source_id=source_id,
                            target_id=target_id,
                            relationship_type=RelationshipType.REFERENCES,
                            confidence=0.9,  # High confidence for explicit links
                            context=self._extract_reference_context(source.content, target.title)
                        )
                    )
                    
    def _calculate_doc_ref_confidence(self, text: str, element: CodeElement | DocumentationElement) -> float:
        """Calculate confidence score for a documentation reference.
        
        Args:
            text: The text containing the reference
            element: The referenced element
            
        Returns:
            Confidence score between 0 and 1
        """
        # Base confidence on:
        # 1. Number of occurrences
        # 2. Presence in headings/prominent locations
        # 3. Context of the reference
        
        name = element.name if isinstance(element, CodeElement) else element.title
        
        # Count occurrences
        occurrences = len(re.findall(rf"\b{re.escape(name)}\b", text))
        if occurrences == 0:
            return 0
            
        confidence = min(0.5 + (occurrences * 0.1), 0.9)  # More occurrences increase confidence
        
        # Check for headings (markdown)
        if re.search(rf"^#+\s+.*{re.escape(name)}.*$", text, re.MULTILINE):
            confidence += 0.1
            
        # Look for code blocks or inline code
        if re.search(rf"`{re.escape(name)}`", text):
            confidence += 0.1
            
        return min(confidence, 1.0)
        
    def _extract_reference_context(self, text: str, reference: str, context_chars: int = 100) -> str:
        """Extract context around a reference in text.
        
        Args:
            text: The text containing the reference
            reference: The reference to find context for
            context_chars: Number of characters of context to include
            
        Returns:
            Context string around the reference
        """
        match = re.search(rf"(?:^|\s)(?P<before>.{{0,{context_chars}}})(?P<ref>{re.escape(reference)})"
                         rf"(?P<after>.{{0,{context_chars}}})(?:\s|$)", text)
                         
        if not match:
            return ""
            
        before = match.group("before").strip()
        ref = match.group("ref")
        after = match.group("after").strip()
        
        return f"...{before} {ref} {after}..."


class RelationshipMappingStage(PipelineStage):
    """Pipeline stage for mapping relationships between elements.
    
    This stage analyzes code and documentation elements and identifies
    relationships between them.
    """
    
    def __init__(self):
        """Initialize the relationship mapping stage."""
        self.mapper = RelationshipMapper()
    
    def process(self, context: PipelineContext, input_data: Any) -> List[Relationship]:
        """Process analysis results to map relationships.
        
        Args:
            context: The pipeline context
            input_data: Input data (not used, reads from context)
            
        Returns:
            List of identified relationships
            
        Notes:
            This stage reads code and documentation analysis results from the
            pipeline context and maps relationships between them. The results
            are added to the context under the key 'relationships'.
        """
        logger.info("Starting relationship mapping stage")
        
        # Reset the mapper
        self.mapper = RelationshipMapper()
        
        # Get code analysis results from context
        if context.contains("code_analysis_results"):
            code_results = context.get("code_analysis_results")
            code_elements = []
            
            for result in code_results:
                if result.get("success", False) and "analysis" in result:
                    analysis = result["analysis"]
                    if hasattr(analysis, "elements"):
                        code_elements.extend(analysis.elements)
            
            logger.debug(f"Found {len(code_elements)} code elements for relationship mapping")
            self.mapper.add_code_elements(code_elements)
        
        # Get documentation analysis results from context
        if context.contains("documentation_analysis_results"):
            doc_results = context.get("documentation_analysis_results")
            doc_elements = []
            
            for result in doc_results:
                if result.get("success", False) and "analysis" in result:
                    analysis = result["analysis"]
                    if hasattr(analysis, "elements"):
                        doc_elements.extend(analysis.elements)
            
            logger.debug(f"Found {len(doc_elements)} documentation elements for relationship mapping")
            self.mapper.add_doc_elements(doc_elements)
        
        # Map relationships
        relationships = self.mapper.map_relationships()
        
        # Store relationships in context
        context.set("relationships", relationships)
        
        logger.info(f"Relationship mapping completed: {len(relationships)} relationships identified")
        
        return relationships 