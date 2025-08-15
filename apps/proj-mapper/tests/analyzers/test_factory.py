"""Tests for the analyzer factory."""

import unittest
from unittest.mock import Mock, patch

from proj_mapper.analyzers.base import Analyzer
from proj_mapper.analyzers.factory import AnalyzerFactory
from proj_mapper.analyzers.code.python import PythonAnalyzer
from proj_mapper.analyzers.documentation.markdown import MarkdownAnalyzer
from proj_mapper.models.file import DiscoveredFile, FileType


class TestAnalyzerFactory(unittest.TestCase):
    """Tests for the AnalyzerFactory class."""
    
    def setUp(self):
        """Set up for the tests."""
        self.factory = AnalyzerFactory()
        
    def test_init(self):
        """Test the initialization of the factory."""
        # Check if the factory was initialized properly
        self.assertIsNotNone(self.factory)
        # Test that the factory's _analyzers attribute is initialized
        self.assertTrue(hasattr(self.factory, '_analyzers'))
        
    def test_get_analyzer_for_file(self):
        """Test getting an analyzer for a file."""
        # Python file
        python_file = DiscoveredFile.create_mock(
            path="test.py",
            relative_path="test.py",
            file_type=FileType.PYTHON
        )
        analyzer = self.factory.get_analyzer_for_file(python_file)
        self.assertIsNotNone(analyzer)
        self.assertIsInstance(analyzer, PythonAnalyzer)
        
        # Text file (no analyzer)
        text_file = DiscoveredFile.create_mock(
            path="test.txt",
            relative_path="test.txt",
            file_type=FileType.TEXT
        )
        analyzer = self.factory.get_analyzer_for_file(text_file)
        self.assertIsNone(analyzer)
        
    def test_create_analyzer(self):
        """Test creating an analyzer based on file type."""
        # Python file type
        analyzer = self.factory.create_analyzer(FileType.PYTHON)
        self.assertIsNotNone(analyzer)
        self.assertIsInstance(analyzer, PythonAnalyzer)
        
        # Text file type (no analyzer)
        analyzer = self.factory.create_analyzer(FileType.TEXT)
        self.assertIsNone(analyzer)


if __name__ == "__main__":
    unittest.main() 