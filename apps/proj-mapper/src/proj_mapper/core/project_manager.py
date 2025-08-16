"""Project Manager for Project Mapper.

This module defines the ProjectManager class, which serves as the main entry point
to the Project Mapper system.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, cast

from proj_mapper.core.config import Configuration
from proj_mapper.core.file_discovery import FileDiscovery
from proj_mapper.core.pipeline import Pipeline, PipelineContext, PipelineStage
from proj_mapper.models.file import DiscoveredFile, FileType
from proj_mapper.models.project import Project, ProjectMap
from proj_mapper.core.discovery import ProjectDiscoveryStage
from proj_mapper.analyzers.pipeline_stages import (
    CodeAnalysisStage,
    DocumentationAnalysisStage,
    CombinedAnalysisStage,
    ProjectMapCreationStage,
)
from proj_mapper.storage.map_storage import MapStorage

# Configure logging
logger = logging.getLogger(__name__)


class ProjectDiscoveryStage(PipelineStage):
    """Pipeline stage for discovering files in a project."""

    def __init__(self, config: Configuration):
        """Initialize the discovery stage.

        Args:
            config: The configuration to use
        """
        self.config = config

    def process(self, context: PipelineContext) -> PipelineContext:
        """Process the project by discovering its files.

        Args:
            context: The pipeline context

        Returns:
            The updated pipeline context
        """
        project = context.get_data("project")
        if not project:
            raise ValueError("Project not available in context")

        logger.info(f"Discovering files in project: {project.name}")

        # Create a file discovery instance with configuration
        discovery = FileDiscovery(
            include_patterns=self.config.include_patterns,
            exclude_patterns=self.config.exclude_patterns,
            max_file_size=self.config.max_file_size,
            respect_gitignore=self.config.respect_gitignore,
            project_root=project.root_path,
        )

        # Discover files
        discovered_files = discovery.discover_files(project.root_path)

        # Update the project
        project.files = discovered_files

        # Store discovered files in context for later stages
        context.set_data("discovered_files", discovered_files)

        # Store categorized files in context for later stages
        categorized = discovery.categorize_files(discovered_files)
        context.set_data("categorized_files", categorized)

        # Store the updated project back in context
        context.set_data("project", project)

        return context


class ProjectManager:
    """Main entry point for the Project Mapper system.

    The ProjectManager coordinates the analysis process and manages the overall workflow.
    """

    def __init__(self, config: Optional[Configuration] = None):
        """Initialize the project manager.

        Args:
            config: Optional configuration object
        """
        self.config = config or Configuration()
        self.map_storage = MapStorage()

        logger.debug("ProjectManager initialized")
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Configuration: {self.config.to_dict()}")

    def analyze_project(self, project_path: str) -> ProjectMap:
        """Analyze a project and generate a project map.

        Args:
            project_path: Path to the project root

        Returns:
            Generated project map

        Raises:
            ValueError: If project path is invalid
        """
        logger.debug(f"Analyzing project at: {project_path}")

        # Create pipeline
        pipeline = self._create_pipeline()

        # Create project instance
        project = Project(name=Path(project_path).name, root_path=project_path)
        logger.debug(f"Created project instance: {project.name} at {project.root_path}")

        # Create initial pipeline context with the project
        context = PipelineContext()
        context.set_data("project", project)
        logger.debug("Initialized pipeline context with project")

        # Execute pipeline
        try:
            logger.debug("Starting pipeline execution")
            result_context = pipeline.run(context)
            logger.debug("Pipeline execution completed")
        except Exception as e:
            logger.error(f"Error executing pipeline: {e}")
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(
                    f"Pipeline execution failed with exception: {type(e).__name__}",
                    exc_info=True,
                )
            raise

        # Get project map from context
        project_map = result_context.get_data("project_map")
        if not project_map:
            logger.error("Pipeline did not generate a project map")
            raise ValueError("Pipeline did not generate a project map")

        logger.debug(f"Project map generated with {len(project_map.files)} files")

        return project_map

    def update_map(self, project_path: str) -> ProjectMap:
        """Update an existing project map.

        Args:
            project_path: Path to the project root

        Returns:
            Updated project map

        Raises:
            ValueError: If project path is invalid
        """
        logger.debug(f"Updating project map for: {project_path}")

        # Load existing map if available
        try:
            existing_map = self.map_storage.load_map(project_path)
            logger.debug(
                f"Loaded existing map with {len(existing_map.files)} files and timestamp {existing_map.timestamp}"
            )
        except FileNotFoundError:
            logger.debug("No existing map found, will create new map")
            existing_map = None
        except Exception as e:
            logger.error(f"Error loading existing map: {e}")
            raise

        # Analyze project to get new map
        new_map = self.analyze_project(project_path)

        # If we have an existing map, merge the metadata
        if existing_map:
            new_map.metadata.update(existing_map.metadata)

        return new_map

    def update_project(self, project_path: str, full: bool = False) -> ProjectMap:
        """Update an existing project map.

        Args:
            project_path: Path to the project root
            full: If True, perform a full re-analysis of the project

        Returns:
            Updated project map
        """
        logger.debug(f"Updating project at: {project_path} (full: {full})")
        # For now, we only support full updates.
        return self.update_map(project_path)

    def _create_pipeline(self) -> Pipeline:
        """Create the analysis pipeline.

        Returns:
            Configured pipeline instance
        """
        logger.debug("Creating analysis pipeline")
        pipeline = Pipeline()

        # Add discovery stage
        pipeline.add_stage(ProjectDiscoveryStage(self.config))

        # Add analysis stage based on configuration
        if self.config.analyze_code or self.config.analyze_docs:
            analysis_config = {
                "max_workers": self.config.max_workers,
                "analyze_code": self.config.analyze_code,
                "analyze_docs": self.config.analyze_docs,
                "detect_relationships": self.config.detect_relationships,
                "min_confidence": self.config.min_confidence,
            }
            pipeline.add_stage(CombinedAnalysisStage(analysis_config))

        # Add map creation stage
        map_config = {
            "include_code": self.config.analyze_code,
            "include_documentation": self.config.analyze_docs,
            "include_metadata": True,
            "enable_chunking": True,
            "max_tokens": 8192,
            "ai_optimize": True,
        }
        pipeline.add_stage(ProjectMapCreationStage(map_config))

        return pipeline
