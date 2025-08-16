"""Pipeline stage for mapping relationships between code and documentation elements."""

from typing import Dict, List, Any
from dataclasses import dataclass

from ..pipeline import PipelineStage, PipelineContext
from ..models.code import CodeElement
from ..models.documentation import DocumentationElement
from ..models.relationship import Relationship
from .mapper import RelationshipMapper

@dataclass
class RelationshipMappingStage(PipelineStage):
    """Pipeline stage that maps relationships between code and documentation elements."""
    
    def process(self, context: PipelineContext) -> PipelineContext:
        """Process the pipeline context to map relationships.
        
        Args:
            context: Pipeline context containing analysis results
            
        Returns:
            Updated context with mapped relationships
        """
        # Get code analysis results
        code_elements = self._get_code_elements(context)
        
        # Get documentation analysis results
        doc_elements = self._get_doc_elements(context)
        
        # Create and configure mapper
        mapper = RelationshipMapper()
        mapper.add_code_elements(code_elements)
        mapper.add_doc_elements(doc_elements)
        
        # Map relationships
        relationships = mapper.map_relationships()
        
        # Store relationships in context
        context.set_result("relationships", relationships)
        
        return context
        
    def _get_code_elements(self, context: PipelineContext) -> List[CodeElement]:
        """Get code elements from the context.
        
        Args:
            context: Pipeline context
            
        Returns:
            List of code elements
        """
        code_results = context.get_result("code_analysis", {})
        elements = []
        
        # Collect elements from all analyzers
        for analyzer_results in code_results.values():
            if isinstance(analyzer_results, dict):
                elements.extend(analyzer_results.get("elements", []))
            elif isinstance(analyzer_results, list):
                elements.extend(analyzer_results)
                
        return elements
        
    def _get_doc_elements(self, context: PipelineContext) -> List[DocumentationElement]:
        """Get documentation elements from the context.
        
        Args:
            context: Pipeline context
            
        Returns:
            List of documentation elements
        """
        doc_results = context.get_result("documentation_analysis", {})
        elements = []
        
        # Collect elements from all analyzers
        for analyzer_results in doc_results.values():
            if isinstance(analyzer_results, dict):
                elements.extend(analyzer_results.get("elements", []))
            elif isinstance(analyzer_results, list):
                elements.extend(analyzer_results)
                
        return elements 