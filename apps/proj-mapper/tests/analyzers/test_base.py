"""Tests for the base analyzer components."""

import unittest
from unittest.mock import Mock, patch

from proj_mapper.claude_code_adapter import AnalysisResult, Analyzer, AnalyzerRegistry
from proj_mapper.models.file import DiscoveredFile, FileType


class TestAnalysisResult(unittest.TestCase):
    """Tests for the AnalysisResult class."""

    def test_init(self):
        """Test initialization of AnalysisResult."""
        result = AnalysisResult(file_path="/path/to/file.py")
        self.assertEqual(result.file_path, "/path/to/file.py")
        self.assertTrue(result.success)
        self.assertIsNone(result.error_message)

    def test_failed_result(self):
        """Test creating a failed result."""
        result = AnalysisResult(
            file_path="/path/to/file.py",
            success=False,
            error_message="Failed to analyze",
        )
        self.assertEqual(result.file_path, "/path/to/file.py")
        self.assertFalse(result.success)
        self.assertEqual(result.error_message, "Failed to analyze")


class MockAnalyzer(Analyzer):
    """Mock analyzer for testing."""

    def can_analyze(self, file: DiscoveredFile) -> bool:
        """Check if this analyzer can analyze the given file."""
        return file.file_type == FileType.PYTHON

    def analyze(self, file: DiscoveredFile, content=None) -> AnalysisResult:
        """Analyze a file."""
        return AnalysisResult(file_path=str(file.path))


class TestAnalyzer(unittest.TestCase):
    """Tests for the Analyzer base class."""

    def test_can_analyze_abstract(self):
        """Test that can_analyze is abstract."""
        with self.assertRaises(TypeError):
            Analyzer()  # Can't instantiate abstract class

    def test_analyze_abstract(self):
        """Test that analyze is abstract."""

        # Create a concrete subclass with only can_analyze implemented
        class PartialAnalyzer(Analyzer):
            def can_analyze(self, file: DiscoveredFile) -> bool:
                return True

        # Should still fail because analyze is not implemented
        with self.assertRaises(TypeError):
            PartialAnalyzer()


class TestAnalyzerRegistry(unittest.TestCase):
    """Tests for the AnalyzerRegistry class."""

    def test_register(self):
        """Test registering analyzers."""
        registry = AnalyzerRegistry()
        analyzer = MockAnalyzer()

        registry.register(analyzer)
        self.assertEqual(len(registry.analyzers), 1)
        self.assertIs(registry.analyzers[0], analyzer)

    def test_register_duplicate(self):
        """Test registering the same analyzer twice."""
        registry = AnalyzerRegistry()
        analyzer = MockAnalyzer()

        registry.register(analyzer)
        registry.register(analyzer)  # Should have no effect
        self.assertEqual(len(registry.analyzers), 1)

    def test_unregister(self):
        """Test unregistering analyzers."""
        registry = AnalyzerRegistry()
        analyzer1 = MockAnalyzer()
        analyzer2 = MockAnalyzer()

        registry.register(analyzer1)
        registry.register(analyzer2)
        self.assertEqual(len(registry.analyzers), 2)

        registry.unregister(analyzer1)
        self.assertEqual(len(registry.analyzers), 1)
        self.assertIs(registry.analyzers[0], analyzer2)

    def test_unregister_nonexistent(self):
        """Test unregistering an analyzer that wasn't registered."""
        registry = AnalyzerRegistry()
        analyzer1 = MockAnalyzer()
        analyzer2 = MockAnalyzer()

        registry.register(analyzer1)
        registry.unregister(analyzer2)  # Should have no effect
        self.assertEqual(len(registry.analyzers), 1)
        self.assertIs(registry.analyzers[0], analyzer1)


if __name__ == "__main__":
    unittest.main()
