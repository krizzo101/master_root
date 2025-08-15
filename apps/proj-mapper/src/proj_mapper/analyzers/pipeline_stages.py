"""Pipeline stages for analysis.

This module provides pipeline stages that integrate analyzers with the pipeline.
"""

import logging
from typing import Dict, List, Any, Optional, Union
from concurrent.futures import ThreadPoolExecutor, as_completed
import traceback
import time
from datetime import datetime

from proj_mapper.core.pipeline import PipelineStage, PipelineContext
from proj_mapper.models.file import DiscoveredFile, FileType
from proj_mapper.analyzers.factory import AnalyzerFactory
from proj_mapper.analyzers.pipeline import AnalysisPipeline
from proj_mapper.models.project import Project
from proj_mapper.models.project_map import ProjectMap

# Configure logging
logger = logging.getLogger(__name__)


class CodeAnalysisStage(PipelineStage):
    """Pipeline stage for analyzing code files.

    This stage analyzes code files in the project.
    """

    def __init__(self, max_workers: int = 4):
        """Initialize the code analysis stage.

        Args:
            max_workers: Maximum number of worker threads for parallel analysis
        """
        logger.debug(f"Initializing CodeAnalysisStage with max_workers={max_workers}")
        self.factory = AnalyzerFactory()
        self.pipeline = AnalysisPipeline(max_workers=max_workers)

    def process(self, context: PipelineContext) -> PipelineContext:
        """Process the pipeline context.

        Args:
            context: The pipeline context to process

        Returns:
            Updated pipeline context with code analysis results

        Raises:
            ValueError: If the project is not available in the context
        """
        logger.debug(f"CodeAnalysisStage.process: Starting with context keys: {list(context.data.keys())}")
        start_time = time.time()

        try:
            project = context.get_data("project")
            if not project:
                logger.error("CodeAnalysisStage.process: Project not available in context")
                raise ValueError("Project not available in context")

            logger.info(f"Starting code analysis for project: {project.name}")
            logger.debug(f"CodeAnalysisStage.process: Project has {len(project.files)} total files")

            # Analyze code files
            code_file_types = {
                FileType.PYTHON, FileType.JAVA, FileType.JAVASCRIPT,
                FileType.TYPESCRIPT, FileType.CPP, FileType.C, FileType.CSHARP,
                FileType.GO, FileType.RUBY, FileType.PHP, FileType.RUST
            }

            # Filter files to only include code files
            code_files = [f for f in project.files if f.file_type in code_file_types]
            logger.debug(f"CodeAnalysisStage.process: Filtered to {len(code_files)} code files")

            # Create a mini-project with just code files for analysis
            from proj_mapper.models.file import DiscoveredProject
            code_project = DiscoveredProject(
                name=project.name,
                root_path=project.root_path,
                files=code_files
            )

            # Analyze the code files
            logger.debug(f"CodeAnalysisStage.process: Starting code analysis pipeline")
            results = self.pipeline.analyze_project(code_project)
            logger.debug(f"CodeAnalysisStage.process: Analysis pipeline completed with {len(results) if results else 0} results")

            # Store results in context
            analysis_results = {
                "code": self.pipeline.code_results,
                "summary": self.pipeline.generate_summary()
            }
            context.set_data("analysis_results", analysis_results)
            logger.debug(f"CodeAnalysisStage.process: Stored analysis results in context")

            logger.info(f"Completed code analysis: {len(results)} files analyzed")

        except Exception as e:
            logger.error(f"CodeAnalysisStage.process: Error during code analysis: {e}")
            logger.debug(f"CodeAnalysisStage.process: Exception details: {traceback.format_exc()}")
            raise
        finally:
            duration = time.time() - start_time
            logger.debug(f"CodeAnalysisStage.process: Completed in {duration:.2f} seconds")

        return context


class DocumentationAnalysisStage(PipelineStage):
    """Pipeline stage for analyzing documentation files.

    This stage analyzes documentation files in the project.
    """

    def __init__(self, max_workers: int = 4):
        """Initialize the documentation analysis stage.

        Args:
            max_workers: Maximum number of worker threads for parallel analysis
        """
        logger.debug(f"Initializing DocumentationAnalysisStage with max_workers={max_workers}")
        self.factory = AnalyzerFactory()
        self.pipeline = AnalysisPipeline(max_workers=max_workers)

    def process(self, context: PipelineContext) -> PipelineContext:
        """Process the pipeline context.

        Args:
            context: The pipeline context to process

        Returns:
            Updated pipeline context with documentation analysis results

        Raises:
            ValueError: If the project is not available in the context
        """
        logger.debug(f"DocumentationAnalysisStage.process: Starting with context keys: {list(context.data.keys())}")
        start_time = time.time()

        try:
            project = context.get_data("project")
            if not project:
                logger.error("DocumentationAnalysisStage.process: Project not available in context")
                raise ValueError("Project not available in context")

            logger.info(f"Starting documentation analysis for project: {project.name}")
            logger.debug(f"DocumentationAnalysisStage.process: Project has {len(project.files)} total files")

            # Analyze documentation files
            doc_file_types = {
                FileType.MARKDOWN, FileType.TEXT, FileType.HTML,
                FileType.XML, FileType.JSON, FileType.YAML
            }

            # Filter files to only include documentation files
            doc_files = [f for f in project.files if f.file_type in doc_file_types]
            logger.debug(f"DocumentationAnalysisStage.process: Filtered to {len(doc_files)} documentation files")

            # Create a mini-project with just documentation files for analysis
            from proj_mapper.models.file import DiscoveredProject
            doc_project = DiscoveredProject(
                name=project.name,
                root_path=project.root_path,
                files=doc_files
            )

            # Analyze the documentation files
            logger.debug(f"DocumentationAnalysisStage.process: Starting documentation analysis pipeline")
            results = self.pipeline.analyze_project(doc_project)
            logger.debug(f"DocumentationAnalysisStage.process: Analysis pipeline completed with {len(results) if results else 0} results")

            # Get existing analysis results or create new ones
            analysis_results = context.get_data("analysis_results", {})
            logger.debug(f"DocumentationAnalysisStage.process: Retrieved existing analysis results with keys: {list(analysis_results.keys())}")

            # Always include documentation results even if empty
            analysis_results["documentation"] = self.pipeline.doc_results or {}

            # Add or update summary information
            if "summary" in analysis_results:
                analysis_results["summary"].update(self.pipeline.generate_summary())
                logger.debug("DocumentationAnalysisStage.process: Updated existing summary information")
            else:
                analysis_results["summary"] = self.pipeline.generate_summary()
                logger.debug("DocumentationAnalysisStage.process: Created new summary information")

            # Update context with the updated analysis results
            context.set_data("analysis_results", analysis_results)
            logger.debug("DocumentationAnalysisStage.process: Updated analysis results in context")

            logger.info(f"Completed documentation analysis: {len(results)} files analyzed")

        except Exception as e:
            logger.error(f"DocumentationAnalysisStage.process: Error during documentation analysis: {e}")
            logger.debug(f"DocumentationAnalysisStage.process: Exception details: {traceback.format_exc()}")
            raise
        finally:
            duration = time.time() - start_time
            logger.debug(f"DocumentationAnalysisStage.process: Completed in {duration:.2f} seconds")

        return context


class CombinedAnalysisStage(PipelineStage):
    """Pipeline stage that combines code and documentation analysis."""

    def __init__(self, config: Optional[Union[int, Dict[str, Any]]] = None):
        """Initialize the combined analysis stage.

        Args:
            config: Either the max_workers value as an integer or a config dictionary
                   containing analysis configuration options
        """
        # Extract max_workers from the config if it's a dictionary
        if config is None:
            self.max_workers = None
            logger.debug("CombinedAnalysisStage.__init__: Initialized with default config (None)")
        elif isinstance(config, dict):
            self.max_workers = config.get('max_workers', None)
            self.analyze_code = config.get('analyze_code', True)
            self.analyze_docs = config.get('analyze_docs', True)
            self.detect_relationships = config.get('detect_relationships', True)
            self.min_confidence = config.get('min_confidence', 0.5)
            logger.debug(f"CombinedAnalysisStage.__init__: Initialized with config dict: max_workers={self.max_workers}, "
                        f"analyze_code={self.analyze_code}, analyze_docs={self.analyze_docs}, "
                        f"detect_relationships={self.detect_relationships}, min_confidence={self.min_confidence}")
        else:
            # If config is an int, it's the max_workers value
            self.max_workers = config
            self.analyze_code = True
            self.analyze_docs = True
            self.detect_relationships = True
            self.min_confidence = 0.5
            logger.debug(f"CombinedAnalysisStage.__init__: Initialized with max_workers={self.max_workers}")

        self.analyzer_factory = AnalyzerFactory()

    def process(self, context: PipelineContext) -> PipelineContext:
        """Process the project by analyzing code and documentation.

        Args:
            context: The pipeline context

        Returns:
            The updated pipeline context
        """
        logger.debug(f"CombinedAnalysisStage.process: Starting with context keys: {list(context.data.keys())}")
        start_time = time.time()

        try:
            project = context.get_data("project")
            if not project:
                logger.error("CombinedAnalysisStage.process: Project not available in context")
                raise ValueError("Project not available in context")

            logger.info(f"Starting combined analysis for project: {project.name}")

            # Get categorized files from context
            categorized_files = context.get_data("categorized_files", {})
            logger.debug(f"CombinedAnalysisStage.process: Retrieved categorized files with types: {list(categorized_files.keys())}")

            # Initialize results dictionary
            analysis_results: Dict[str, Dict[str, Any]] = {}
            code_results: Dict[str, Dict[str, Any]] = {}
            doc_results: Dict[str, Dict[str, Any]] = {}

            # Process code files
            code_files = []
            # Use string values of FileType instead of enum objects
            code_file_types = ["python", "javascript", "typescript"]
            for file_type in code_file_types:
                if file_type in categorized_files:
                    logger.debug(f"CombinedAnalysisStage.process: Adding {len(categorized_files.get(file_type, []))} {file_type} files for analysis")
                    code_files.extend(categorized_files.get(file_type, []))

            if code_files:
                logger.info(f"Analyzing {len(code_files)} code files")
                code_results = self._analyze_files(code_files)
                logger.debug(f"CombinedAnalysisStage.process: Code analysis completed with {len(code_results)} results")
                analysis_results.update(code_results)
            else:
                logger.debug("CombinedAnalysisStage.process: No code files to analyze")

            # Process documentation files
            # Use string value of FileType.MARKDOWN
            doc_files = categorized_files.get("markdown", [])
            if doc_files:
                logger.info(f"Analyzing {len(doc_files)} documentation files")
                doc_results = self._analyze_files(doc_files)
                logger.debug(f"CombinedAnalysisStage.process: Documentation analysis completed with {len(doc_results)} results")
                analysis_results.update(doc_results)
            else:
                logger.debug("CombinedAnalysisStage.process: No documentation files to analyze")

            # Store results in context
            context.set_data("analysis_results", {
                "code": {str(path): results for path, results in code_results.items()},
                "doc": {str(path): results for path, results in doc_results.items()},
            })
            logger.debug("CombinedAnalysisStage.process: Updated analysis results in context")

            logger.info(f"Combined analysis completed for project: {project.name}")

        except Exception as e:
            logger.error(f"CombinedAnalysisStage.process: Error during combined analysis: {e}")
            logger.debug(f"CombinedAnalysisStage.process: Exception details: {traceback.format_exc()}")
            raise
        finally:
            duration = time.time() - start_time
            logger.debug(f"CombinedAnalysisStage.process: Completed in {duration:.2f} seconds")

        return context

    def _analyze_files(self, files: List[DiscoveredFile]) -> Dict[str, Dict[str, Any]]:
        """Analyze a list of files in parallel.

        Args:
            files: List of files to analyze

        Returns:
            Dictionary mapping file paths to analysis results
        """
        logger.debug(f"CombinedAnalysisStage._analyze_files: Starting analysis of {len(files)} files with max_workers={self.max_workers}")
        results: Dict[str, Dict[str, Any]] = {}
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_file = {
                executor.submit(self._analyze_file, file): file
                for file in files
            }

            completed_count = 0
            for future in as_completed(future_to_file):
                file = future_to_file[future]
                completed_count += 1

                if completed_count % 10 == 0 or completed_count == len(files):
                    logger.debug(f"CombinedAnalysisStage._analyze_files: Processed {completed_count}/{len(files)} files")

                try:
                    result = future.result()
                    if result:
                        results[str(file.path)] = result
                        logger.debug(f"CombinedAnalysisStage._analyze_files: Successfully analyzed {file.path}")
                    else:
                        logger.debug(f"CombinedAnalysisStage._analyze_files: No results for {file.path}")
                except Exception as e:
                    logger.error(f"Error analyzing {file.path}: {e}")
                    logger.debug(f"CombinedAnalysisStage._analyze_files: Exception details for {file.path}: {traceback.format_exc()}")

        duration = time.time() - start_time
        logger.debug(f"CombinedAnalysisStage._analyze_files: Completed analysis of {len(files)} files in {duration:.2f} seconds")
        return results

    def _analyze_file(self, file: DiscoveredFile) -> Optional[Dict[str, Any]]:
        """Analyze a single file.

        Args:
            file: The file to analyze

        Returns:
            Analysis results dictionary or None if analysis fails
        """
        logger.debug(f"CombinedAnalysisStage._analyze_file: Starting analysis of {file.path}")
        start_time = time.time()

        try:
            # Use get_analyzer_for_file instead of create_analyzer to ensure proper analyzer detection
            analyzer = self.analyzer_factory.get_analyzer_for_file(file)
            if analyzer:
                logger.debug(f"CombinedAnalysisStage._analyze_file: Using analyzer {analyzer.__class__.__name__} for {file.path}")
                result = analyzer.analyze(file)
                duration = time.time() - start_time
                logger.debug(f"CombinedAnalysisStage._analyze_file: Completed analysis of {file.path} in {duration:.2f} seconds")
                return result
            else:
                logger.debug(f"CombinedAnalysisStage._analyze_file: No suitable analyzer found for {file.path}")
                return None
        except Exception as e:
            logger.error(f"Error analyzing {file.path}: {e}")
            logger.debug(f"CombinedAnalysisStage._analyze_file: Exception details: {traceback.format_exc()}")
            duration = time.time() - start_time
            logger.debug(f"CombinedAnalysisStage._analyze_file: Failed analysis of {file.path} in {duration:.2f} seconds")
            return None


def analyze_file(file_path: str, content: Optional[str] = None) -> Dict[str, Any]:
    """Analyze a single file.

    Args:
        file_path: Path to the file to analyze
        content: Optional file content (if already loaded)

    Returns:
        Analysis result as a dictionary
    """
    logger.debug(f"analyze_file: Starting analysis of {file_path}")
    start_time = time.time()

    from pathlib import Path
    import os

    try:
        # Create a discovered file
        file_path_obj = Path(file_path)
        file_type = _determine_file_type(file_path)
        logger.debug(f"analyze_file: Determined file type for {file_path}: {file_type}")

        relative_path = os.path.basename(file_path)
        discovered_file = DiscoveredFile.create_mock(
            path=file_path_obj,
            relative_path=relative_path,
            file_type=file_type
        )

        # Get an analyzer for the file
        factory = AnalyzerFactory()
        analyzer = factory.get_analyzer_for_file(discovered_file)

        if not analyzer:
            logger.debug(f"analyze_file: No suitable analyzer found for {file_path}")
            return {
                "file_path": file_path,
                "success": False,
                "error_message": "No suitable analyzer found"
            }

        # Analyze the file
        try:
            logger.debug(f"analyze_file: Using analyzer {analyzer.__class__.__name__} for {file_path}")
            result = analyzer.analyze(discovered_file, content)
            logger.debug(f"analyze_file: Analysis completed successfully for {file_path}")

            duration = time.time() - start_time
            logger.debug(f"analyze_file: Completed analysis of {file_path} in {duration:.2f} seconds")
            return result.dict()
        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")
            logger.debug(f"analyze_file: Exception during analysis: {traceback.format_exc()}")
            return {
                "file_path": file_path,
                "success": False,
                "error_message": str(e)
            }
    except Exception as e:
        logger.error(f"Error setting up analysis for {file_path}: {e}")
        logger.debug(f"analyze_file: Exception during setup: {traceback.format_exc()}")
        return {
            "file_path": file_path,
            "success": False,
            "error_message": f"Analysis setup error: {str(e)}"
        }


def analyze_files(files: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Analyze multiple files.

    Args:
        files: List of file dictionaries with 'path' and optional 'content'

    Returns:
        Dictionary mapping file paths to analysis results
    """
    logger.debug(f"analyze_files: Starting analysis of {len(files)} files")
    results = {}
    start_time = time.time()

    for idx, file_info in enumerate(files):
        file_path = file_info.get("path")
        content = file_info.get("content")

        if not file_path:
            logger.debug(f"analyze_files: Skipping file at index {idx} due to missing path")
            continue

        logger.debug(f"analyze_files: Processing file {idx+1}/{len(files)}: {file_path}")
        result = analyze_file(file_path, content)
        results[file_path] = result

    duration = time.time() - start_time
    logger.debug(f"analyze_files: Completed analysis of {len(files)} files in {duration:.2f} seconds")
    return results


def _determine_file_type(file_path: str) -> str:
    """Determine the file type from the file path.

    Args:
        file_path: Path to the file

    Returns:
        File type as a string
    """
    from proj_mapper.models.file import FileType

    extension = file_path.lower().split(".")[-1] if "." in file_path else ""
    logger.debug(f"_determine_file_type: Determining file type for {file_path} with extension '{extension}'")

    if extension in ("py", "pyi"):
        return FileType.PYTHON
    elif extension in ("md", "markdown", "mdown", "mkd"):
        return FileType.MARKDOWN
    elif extension in ("c", "cpp", "h", "hpp", "java", "js", "ts"):
        return FileType.SOURCE
    elif extension in ("txt", "rst", "asciidoc"):
        return FileType.TEXT
    else:
        logger.debug(f"_determine_file_type: Unknown file type for extension '{extension}'")
        return FileType.UNKNOWN


class ProjectMapCreationStage(PipelineStage):
    """Pipeline stage that creates the final project map."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the project map creation stage.

        Args:
            config: Configuration for map creation
        """
        super().__init__()  # Call parent class constructor
        self.config = config or {}
        logger.debug(f"ProjectMapCreationStage initialized with config: {self.config}")

    def process(self, context: PipelineContext) -> PipelineContext:
        """Process the pipeline context to create a project map.

        Args:
            context: Pipeline context

        Returns:
            Updated pipeline context with project map

        Raises:
            ValueError: If required data is missing from context
        """
        logger.info("Starting project map creation stage")

        try:
            # Get project from context
            project = context.get_data('project')
            if not project:
                raise ValueError("No project found in context")

            # Get discovered files
            discovered_files = context.get_data('discovered_files')
            if not discovered_files:
                raise ValueError("No discovered files found in context")

            # Get analysis results
            code_analysis = context.get_data('code_analysis')
            doc_analysis = context.get_data('doc_analysis')
            relationships = context.get_data('relationships')

            # Create project map
            project_map = ProjectMap(
                project=project,
                files=discovered_files,
                code_analysis=code_analysis if self.config.get('include_code', True) else None,
                doc_analysis=doc_analysis if self.config.get('include_documentation', True) else None,
                relationships=relationships,
                metadata={
                    'timestamp': datetime.now().isoformat(),
                    'config': self.config if self.config.get('include_metadata', True) else None
                }
            )

            # Add project map to context
            context.set_data('project_map', project_map)

            logger.info("Project map creation completed")
            logger.debug(f"Created project map with {len(discovered_files)} files")

        except Exception as e:
            logger.error(f"Error creating project map: {e}")
            raise

        return context