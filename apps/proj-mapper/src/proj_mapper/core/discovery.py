"""Project discovery stage for Project Mapper.

This module contains the ProjectDiscoveryStage class which handles discovering files
in a project and categorizing them by type.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Set

from proj_mapper.core.file_discovery import FileDiscovery
from proj_mapper.core.pipeline import PipelineContext, PipelineStage
from proj_mapper.models.file import DiscoveredProject

# Configure logging
logger = logging.getLogger(__name__)

class ProjectDiscoveryStage(PipelineStage):
    """Pipeline stage for discovering project files."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the discovery stage.
        
        Args:
            config: Optional configuration dictionary
        """
        super().__init__()
        self.config = config or {}
        
        # Extract file discovery settings from config
        self.include_patterns: Set[str] = set(self.config.get('include_patterns', [
            "**/*.py",
            "**/*.md",
            "**/*.rst"
        ]))
        self.exclude_patterns: Set[str] = set(self.config.get('exclude_patterns', [
            "**/.git/**", 
            "**/.venv/**", 
            "**/venv/**", 
            "**/__pycache__/**",
            "**/.maps/**",
            "**/node_modules/**",
            "**/build/**",
            "**/dist/**"
        ]))
        self.max_file_size = self.config.get('max_file_size', 1048576)  # 1MB default
        
        logger.debug(f"ProjectDiscoveryStage initialized with:")
        logger.debug(f"  Include patterns: {self.include_patterns}")
        logger.debug(f"  Exclude patterns: {self.exclude_patterns}")
        logger.debug(f"  Max file size: {self.max_file_size}")
    
    def process(self, context: PipelineContext) -> None:
        """Process the discovery stage.
        
        Args:
            context: The pipeline context
            
        Raises:
            ValueError: If project path is not set in context
        """
        project_path = context.get('project_path')
        if not project_path:
            raise ValueError("Project path not set in context")
            
        logger.debug(f"Starting file discovery in {project_path}")
        
        # Create file discovery instance with configuration
        discovery = FileDiscovery(
            include_patterns=self.include_patterns,
            exclude_patterns=self.exclude_patterns,
            max_file_size=self.max_file_size
        )
        
        # Discover files
        logger.debug("Discovering files...")
        discovered_files = discovery.discover_files(Path(project_path))
        logger.debug(f"Found {len(discovered_files)} files")
        
        # Create project instance
        project = DiscoveredProject(
            name=Path(project_path).name,
            root_path=Path(project_path),
            files=discovered_files,
            excluded_patterns=list(self.exclude_patterns)
        )
        
        # Log discovered files by type
        file_types = {}
        for file in discovered_files:
            file_type = str(file.file_type)
            if file_type not in file_types:
                file_types[file_type] = 0
            file_types[file_type] += 1
            
        logger.debug("Files by type:")
        for file_type, count in file_types.items():
            logger.debug(f"  {file_type}: {count}")
        
        # Store in context
        context.set('discovered_project', project)
        logger.debug("File discovery completed")