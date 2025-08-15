"""Pipeline stage for documentation analysis.

This module provides a pipeline stage for analyzing documentation files.
"""

import logging
from typing import Dict, List, Any, Optional

from proj_mapper.core.pipeline import PipelineStage, PipelineContext
from proj_mapper.models.file import DiscoveredFile, FileType
from proj_mapper.analyzers.documentation import MarkdownAnalyzer

# Configure logging
logger = logging.getLogger(__name__)


class DocumentationAnalysisStage(PipelineStage):
    """Pipeline stage for analyzing documentation files.
    
    This stage processes documentation files (markdown, etc.) and extracts structure
    and references from them.
    """
    
    def __init__(self):
        """Initialize the documentation analysis stage."""
        self.markdown_analyzer = MarkdownAnalyzer()
    
    def process(self, context: PipelineContext, input_data: List[DiscoveredFile]) -> List[Dict[str, Any]]:
        """Process documentation files through the analyzer.
        
        Args:
            context: The pipeline context
            input_data: List of discovered files
            
        Returns:
            List of analysis results
            
        Notes:
            This stage filters for documentation files and passes them to the
            appropriate analyzer. The results are added to the pipeline context
            under the key 'documentation_analysis_results'.
        """
        # Filter for documentation files
        doc_files = [f for f in input_data if f.file_type == FileType.MARKDOWN or
                     f.is_documentation()]
        
        if not doc_files:
            logger.info("No documentation files found to analyze")
            context.set("documentation_analysis_results", [])
            return []
        
        logger.info(f"Analyzing {len(doc_files)} documentation files")
        
        results = []
        for file in doc_files:
            try:
                # Determine which analyzer to use
                analyzer = None
                if self.markdown_analyzer.can_analyze(file):
                    analyzer = self.markdown_analyzer
                
                if analyzer:
                    logger.debug(f"Analyzing documentation file: {file.relative_path}")
                    result = analyzer.analyze(file)
                    results.append({
                        "file": file,
                        "analysis": result,
                        "success": result.success
                    })
                else:
                    logger.warning(f"No suitable analyzer found for: {file.relative_path}")
                    results.append({
                        "file": file,
                        "error": "No suitable analyzer found",
                        "success": False
                    })
            except Exception as e:
                logger.error(f"Error analyzing file {file.relative_path}: {e}")
                results.append({
                    "file": file,
                    "error": str(e),
                    "success": False
                })
        
        # Store results in context
        context.set("documentation_analysis_results", results)
        
        # Log analysis summary
        success_count = sum(1 for r in results if r["success"])
        logger.info(f"Documentation analysis completed: {success_count}/{len(results)} files successful")
        
        return results 