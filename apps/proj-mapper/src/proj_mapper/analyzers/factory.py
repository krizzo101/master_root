"""Analyzer factory module.

This module provides the factory for creating analyzers.
"""

import importlib
import inspect
import logging
import time
import traceback
from typing import Dict, List, Optional, Type

# Import specific analyzers we know exist
from proj_mapper.analyzers.code.python import PythonAnalyzer
from proj_mapper.analyzers.documentation.markdown.analyzer import MarkdownAnalyzer
from proj_mapper.claude_code_adapter import Analyzer
from proj_mapper.models.file import DiscoveredFile, FileType

# Configure logging
logger = logging.getLogger(__name__)


class AnalyzerFactory:
    """Factory for creating analyzers.

    This class is responsible for creating the appropriate analyzer for a given file.
    """

    def __init__(self):
        """Initialize the analyzer factory."""
        logger.debug("AnalyzerFactory.__init__: Initializing analyzer factory")
        start_time = time.time()
        self._analyzers = {}
        self._register_analyzers()
        duration = time.time() - start_time
        logger.debug(
            f"AnalyzerFactory.__init__: Initialization completed in {duration:.2f} seconds with {len(self._analyzers)} analyzers registered"
        )

    def _register_analyzers(self):
        """Register all available analyzers."""
        logger.debug(
            "AnalyzerFactory._register_analyzers: Starting analyzer registration"
        )

        # Manually register known analyzers
        analyzers = {"python": PythonAnalyzer, "markdown": MarkdownAnalyzer}

        logger.debug(
            f"AnalyzerFactory._register_analyzers: Found {len(analyzers)} registered analyzer classes"
        )

        # Instantiate analyzers
        for name, analyzer_class in analyzers.items():
            try:
                logger.debug(
                    f"AnalyzerFactory._register_analyzers: Instantiating analyzer '{name}'"
                )
                self._analyzers[name] = analyzer_class()
                logger.debug(
                    f"AnalyzerFactory._register_analyzers: Successfully registered analyzer '{name}'"
                )
            except Exception as e:
                logger.error(f"Error instantiating analyzer '{name}': {e}")
                logger.debug(
                    f"AnalyzerFactory._register_analyzers: Exception details: {traceback.format_exc()}"
                )

        logger.debug(
            f"AnalyzerFactory._register_analyzers: Completed registration with {len(self._analyzers)} analyzers"
        )

    def get_analyzer_for_file(self, file: DiscoveredFile) -> Optional[Analyzer]:
        """Get an appropriate analyzer for the given file.

        Args:
            file: The file to get an analyzer for

        Returns:
            An analyzer instance or None if no suitable analyzer is found
        """
        logger.debug(
            f"AnalyzerFactory.get_analyzer_for_file: Finding analyzer for {file.relative_path} (type: {file.file_type})"
        )
        start_time = time.time()

        # Try each registered analyzer
        checked_analyzers = 0
        for name, analyzer in self._analyzers.items():
            checked_analyzers += 1
            logger.debug(
                f"AnalyzerFactory.get_analyzer_for_file: Checking if '{name}' can analyze {file.relative_path}"
            )
            try:
                if analyzer.can_analyze(file):
                    duration = time.time() - start_time
                    logger.debug(
                        f"AnalyzerFactory.get_analyzer_for_file: Found suitable analyzer '{name}' for {file.relative_path} after checking {checked_analyzers}/{len(self._analyzers)} analyzers in {duration:.2f} seconds"
                    )
                    return analyzer
            except Exception as e:
                logger.error(
                    f"Error checking if analyzer '{name}' can analyze {file.relative_path}: {e}"
                )
                logger.debug(
                    f"AnalyzerFactory.get_analyzer_for_file: Exception details: {traceback.format_exc()}"
                )

        duration = time.time() - start_time
        logger.debug(
            f"AnalyzerFactory.get_analyzer_for_file: No analyzer found for file: {file.relative_path} after checking {checked_analyzers} analyzers in {duration:.2f} seconds"
        )
        return None

    def create_analyzer(self, analyzer_name: str) -> Optional[Analyzer]:
        """Create an analyzer by name.

        Args:
            analyzer_name: The name of the analyzer to create (e.g., 'python', 'markdown')

        Returns:
            An analyzer instance or None if no suitable analyzer is found
        """
        logger.debug(
            f"AnalyzerFactory.create_analyzer: Creating analyzer for: {analyzer_name}"
        )

        # Convert to lowercase for case-insensitive matching
        analyzer_name = analyzer_name.lower()

        # Check if we have this analyzer registered
        if analyzer_name in self._analyzers:
            logger.debug(
                f"AnalyzerFactory.create_analyzer: Found registered analyzer for '{analyzer_name}'"
            )
            return self._analyzers[analyzer_name]

        logger.debug(
            f"AnalyzerFactory.create_analyzer: No analyzer found for: {analyzer_name}"
        )
        return None
