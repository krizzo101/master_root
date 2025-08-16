"""Analysis module for Project Mapper.

This module contains the CombinedAnalysisStage class which handles analyzing
discovered files and generating project maps.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from proj_mapper.analyzers.factory import AnalyzerFactory
from proj_mapper.core.pipeline import PipelineContext, PipelineStage
from proj_mapper.models.file import DiscoveredProject, FileType
from proj_mapper.models.project import Project, ProjectMap

# Configure logging
logger = logging.getLogger(__name__)

class CombinedAnalysisStage(PipelineStage):
    """Pipeline stage for analyzing discovered files."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the analysis stage.
        
        Args:
            config: Optional configuration dictionary
        """
        super().__init__()
        self.config = config or {}
        self.analyzer_factory = AnalyzerFactory()
        
        logger.debug("CombinedAnalysisStage initialized")
    
    def process(self, context: PipelineContext) -> None:
        """Process the analysis stage.
        
        Args:
            context: The pipeline context
            
        Raises:
            ValueError: If discovered project is not set in context
        """
        discovered_project = context.get('discovered_project')
        if not discovered_project:
            raise ValueError("Discovered project not set in context")
            
        logger.debug(f"Starting analysis of project: {discovered_project.name}")
        
        # Create project instance
        project = Project(
            name=discovered_project.name,
            root_path=discovered_project.root_path
        )
        
        # Analyze each file
        for file in discovered_project.files:
            logger.debug(f"Analyzing file: {file.relative_path}")
            
            # Skip binary files
            if file.is_binary:
                logger.debug(f"Skipping binary file: {file.relative_path}")
                continue
                
            # Get appropriate analyzer
            analyzer = self.analyzer_factory.get_analyzer_for_file(file)
            if not analyzer:
                logger.debug(f"No analyzer available for file type {file.file_type}")
                continue
                
            try:
                # Analyze file
                analysis_result = analyzer.analyze(file)
                if analysis_result:
                    logger.debug(f"Analysis completed for {file.relative_path}")
                    file.metadata['analysis'] = analysis_result.to_dict()
                else:
                    logger.debug(f"No analysis results for {file.relative_path}")
            except Exception as e:
                logger.error(f"Error analyzing {file.relative_path}: {e}")
                continue
            
            # Add file to project
            project.add_file(file)
        
        # Create project map
        project_map = ProjectMap(
            project=project,
            created_at=datetime.now(),
            metadata={"timestamp": context.get('timestamp')}
        )
        
        # Store in context
        context.set('project_map', project_map)
        logger.debug("Analysis completed") 