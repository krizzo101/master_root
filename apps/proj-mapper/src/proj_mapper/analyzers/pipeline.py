"""Analysis pipeline.

This module provides a pipeline for analyzing project files.
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from proj_mapper.claude_code_adapter import AnalysisResult, Analyzer, AnalyzerFactory
from proj_mapper.models.analysis import CodeAnalysisResult, DocumentationAnalysisResult
from proj_mapper.models.file import DiscoveredFile, DiscoveredProject, FileType

# Configure logging
logger = logging.getLogger(__name__)


class AnalysisPipeline:
    """Pipeline for analyzing project files.

    This class coordinates the analysis of files using the appropriate analyzers.
    """

    def __init__(self, max_workers: int = 4):
        """Initialize the analysis pipeline.

        Args:
            max_workers: Maximum number of worker threads for parallel analysis
        """
        self.factory = AnalyzerFactory()
        self.max_workers = max_workers
        self.results: Dict[str, AnalysisResult] = {}
        self.code_results: Dict[str, CodeAnalysisResult] = {}
        self.doc_results: Dict[str, DocumentationAnalysisResult] = {}

    def analyze_project(
        self, project: DiscoveredProject, file_types: Optional[Set[FileType]] = None
    ) -> Dict[str, AnalysisResult]:
        """Analyze all files in a project.

        Args:
            project: The project to analyze
            file_types: Optional set of file types to analyze (all file types if None)

        Returns:
            Dictionary mapping file paths to analysis results
        """
        files_to_analyze = []
        for file in project.files:
            if file_types is not None and file.file_type not in file_types:
                continue

            analyzer = self.factory.get_analyzer_for_file(file)
            if analyzer is not None:
                files_to_analyze.append((file, analyzer))

        logger.info(
            f"Analyzing {len(files_to_analyze)} files in project {project.name}"
        )

        # Clear previous results
        self.results = {}
        self.code_results = {}
        self.doc_results = {}

        # Run analysis in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_file = {
                executor.submit(self._analyze_file, file, analyzer): file.path
                for file, analyzer in files_to_analyze
            }

            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    result = future.result()
                    if result:
                        self.results[str(file_path)] = result

                        # Store specialized result references
                        if isinstance(result, CodeAnalysisResult):
                            self.code_results[str(file_path)] = result
                        elif isinstance(result, DocumentationAnalysisResult):
                            self.doc_results[str(file_path)] = result
                except Exception as e:
                    logger.error(f"Error analyzing {file_path}: {e}")

        logger.info(
            f"Analysis complete. {len(self.results)} files analyzed successfully."
        )
        return self.results

    def _analyze_file(
        self, file: DiscoveredFile, analyzer: Analyzer
    ) -> Optional[AnalysisResult]:
        """Analyze a single file.

        Args:
            file: The file to analyze
            analyzer: The analyzer to use

        Returns:
            Analysis result or None if analysis failed
        """
        try:
            logger.debug(f"Analyzing file: {file.relative_path}")
            result = analyzer.analyze(file)
            return result
        except Exception as e:
            logger.error(f"Error analyzing {file.relative_path}: {e}")
            return None

    def get_related_files(
        self,
        file_path: str,
        relationship_type: str = "import",
        recursive: bool = False,
        max_depth: int = 5,
    ) -> List[str]:
        """Get files related to the specified file.

        Args:
            file_path: Path to the file
            relationship_type: Type of relationship to look for
            recursive: Whether to find relationships recursively
            max_depth: Maximum recursion depth

        Returns:
            List of related file paths
        """
        if not self.results:
            logger.warning("No analysis results available. Run analyze_project first.")
            return []

        # Standardize file path
        file_path = str(Path(file_path).resolve())

        if file_path not in self.code_results:
            return []

        result = self.code_results[file_path]
        related = set()

        # Direct relationships
        for element in result.elements:
            for ref in element.references:
                if ref.reference_type == relationship_type:
                    # Try to resolve the reference to a file
                    # This is a simplified approach - in reality we'd need more complex resolution
                    for potential_match in self.results:
                        if potential_match.endswith(ref.reference_id + ".py"):
                            related.add(potential_match)

        # Recursive relationships
        if recursive and max_depth > 0:
            next_level = set()
            for rel in related:
                next_level.update(
                    self.get_related_files(rel, relationship_type, True, max_depth - 1)
                )
            related.update(next_level)

        return list(related)

    def get_code_references_to_file(
        self, file_path: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Find code references to the specified file.

        Args:
            file_path: Path to the file

        Returns:
            Dictionary mapping source files to lists of references
        """
        if not self.results:
            logger.warning("No analysis results available. Run analyze_project first.")
            return {}

        # Standardize and get file path components for flexible matching
        file_path = str(Path(file_path).resolve())
        file_name = Path(file_path).name
        rel_path = Path(file_path).name  # Simplified - should use proper relative path

        references = {}

        # Look for references in each code analysis result
        for path, result in self.code_results.items():
            file_refs = []

            for element in result.elements:
                for ref in element.references:
                    # More flexible matching to handle different reference formats
                    ref_id = ref.reference_id
                    # Match by exact path, filename, or as part of a path
                    if (
                        ref_id == file_path
                        or ref_id == file_name
                        or ref_id.endswith("/" + file_name)
                        or ref_id + ".py" == file_name
                        or Path(ref_id).name == file_name
                    ):
                        file_refs.append(
                            {
                                "referencing_element": element.name,  # Use name instead of title for CodeElement
                                "location": element.location.to_dict()
                                if element.location
                                else None,
                                "reference_type": ref.reference_type,
                            }
                        )

            if file_refs:
                references[path] = file_refs

        return references

    def get_documentation_for_code(
        self, code_file_path: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Find documentation references to a code file.

        Args:
            code_file_path: Path to the code file

        Returns:
            Dictionary mapping documentation files to references
        """
        if not self.results:
            logger.warning("No analysis results available. Run analyze_project first.")
            return {}

        # Standardize file path
        code_file_path = str(Path(code_file_path).resolve())
        file_name = Path(code_file_path).name

        references = {}

        # Look for references in documentation files
        for path, result in self.doc_results.items():
            doc_refs = []

            for element in result.elements:
                for ref in element.references:
                    if ref.reference_type == "file" and (
                        ref.reference_id == file_name
                        or ref.reference_id.endswith("/" + file_name)
                    ):
                        doc_refs.append(
                            {
                                "doc_element": element.title,
                                "element_type": element.element_type,
                                "location": element.location.to_dict()
                                if element.location
                                else None,
                                "context": element.content[:50] + "..."
                                if len(element.content) > 50
                                else element.content,
                            }
                        )

            if doc_refs:
                references[path] = doc_refs

        return references

    def generate_summary(self) -> Dict[str, Any]:
        """Generate a summary of the analysis results.

        Returns:
            Summary statistics and information
        """
        if not self.results:
            logger.warning("No analysis results available. Run analyze_project first.")
            return {}

        summary = {
            "total_files_analyzed": len(self.results),
            "code_files": len(self.code_results),
            "documentation_files": len(self.doc_results),
            "successful_analyses": sum(1 for r in self.results.values() if r.success),
            "failed_analyses": sum(1 for r in self.results.values() if not r.success),
            "total_code_elements": sum(
                len(r.elements) for r in self.code_results.values()
            ),
            "total_doc_elements": sum(
                len(r.elements) for r in self.doc_results.values()
            ),
            "file_types": {},
            "errors": [],
        }

        # Count file types
        for file_path, result in self.results.items():
            file_ext = Path(file_path).suffix
            if file_ext in summary["file_types"]:
                summary["file_types"][file_ext] += 1
            else:
                summary["file_types"][file_ext] = 1

        # Gather errors
        for file_path, result in self.results.items():
            if not result.success and result.error_message:
                summary["errors"].append(
                    {"file": file_path, "error": result.error_message}
                )

        return summary
