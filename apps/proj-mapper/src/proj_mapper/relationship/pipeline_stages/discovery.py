"""Pipeline stages for relationship discovery.

This module provides pipeline stages for discovering relationships between elements.
"""

import logging
from typing import Dict, List, Any

from proj_mapper.core.pipeline import PipelineStage, PipelineContext
from proj_mapper.models.code import CodeElement
from proj_mapper.models.documentation import DocumentationElement
from proj_mapper.models.relationship import Relationship
from proj_mapper.relationship.detector import RelationshipDetector

# Configure logging
logger = logging.getLogger(__name__)


class RelationshipDetectionStage(PipelineStage):
    """Pipeline stage for detecting relationships between elements.
    
    This stage detects relationships between code and documentation elements.
    """
    
    def __init__(self):
        """Initialize the relationship detection stage."""
        self.detector = RelationshipDetector()
    
    def process(self, context: PipelineContext, input_data: Any) -> List[Relationship]:
        """Process the pipeline context to detect relationships.
        
        Args:
            context: The pipeline context containing analysis results
            input_data: The input data (not used in this stage)
            
        Returns:
            List of detected relationships
            
        Raises:
            ValueError: If analysis results are not available in the context
        """
        # Check if analysis results are available
        if not context.has_data("analysis_results"):
            raise ValueError("Analysis results not available in context")
        
        analysis_results = context.get_data("analysis_results")
        
        # Extract code and documentation elements
        code_elements = self._extract_code_elements(analysis_results)
        doc_elements = self._extract_doc_elements(analysis_results)
        
        logger.info(f"Detecting relationships between {len(code_elements)} code elements and {len(doc_elements)} documentation elements")
        
        # Detect relationships
        relationships = self.detector.detect_all_relationships(
            code_elements=code_elements,
            doc_elements=doc_elements
        )
        
        # Store the elements and relationships in context
        context.set_data("code_elements", code_elements)
        context.set_data("doc_elements", doc_elements)
        context.set_data("relationships", relationships)
        context.set_metadata("relationship_detection_count", len(relationships))
        
        logger.info(f"Detected {len(relationships)} relationships")
        
        return relationships
    
    def _extract_code_elements(self, analysis_results: Dict[str, Any]) -> List[CodeElement]:
        """Extract code elements from analysis results.
        
        Args:
            analysis_results: The analysis results
            
        Returns:
            List of code elements
        """
        code_elements = []
        
        # Extract from code analysis results
        code_analysis = analysis_results.get("code", {})
        for file_path, file_results in code_analysis.items():
            elements = file_results.get("elements", [])
            for element_data in elements:
                if isinstance(element_data, CodeElement):
                    code_elements.append(element_data)
                elif isinstance(element_data, dict):
                    # Convert dict to CodeElement if needed
                    pass
        
        return code_elements
    
    def _extract_doc_elements(self, analysis_results: Dict[str, Any]) -> List[DocumentationElement]:
        """Extract documentation elements from analysis results.
        
        Args:
            analysis_results: The analysis results
            
        Returns:
            List of documentation elements
        """
        doc_elements = []
        
        # Extract from documentation analysis results
        doc_analysis = analysis_results.get("documentation", {})
        for file_path, file_results in doc_analysis.items():
            elements = file_results.get("elements", [])
            for element_data in elements:
                if isinstance(element_data, DocumentationElement):
                    doc_elements.append(element_data)
                elif isinstance(element_data, dict):
                    # Convert dict to DocumentationElement if needed
                    pass
        
        return doc_elements 