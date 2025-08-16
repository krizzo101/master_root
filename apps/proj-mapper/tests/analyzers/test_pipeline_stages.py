"""Tests for the pipeline stages."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from proj_mapper.analyzers.pipeline_stages import (
    CodeAnalysisStage,
    DocumentationAnalysisStage,
    CombinedAnalysisStage,
    analyze_file,
    analyze_files
)
from proj_mapper.models.file import DiscoveredFile, DiscoveredProject, FileType


class TestPipelineStages(unittest.TestCase):
    """Tests for the pipeline stages."""
    
    def setUp(self):
        """Set up for the tests."""
        # Create a temporary directory for the project
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_dir = Path(self.temp_dir.name)
        
        # Create a Python file
        self.python_file = self.project_dir / "test.py"
        with open(self.python_file, "w") as f:
            f.write('''"""Test module."""

def test_function():
    """Test function."""
    return "test"
''')
        
        # Create a Markdown file
        self.markdown_file = self.project_dir / "test.md"
        with open(self.markdown_file, "w") as f:
            f.write('''# Test Document

This is a test document.

```python
def example():
    return "example"
```
''')
        
        # Create discovered files
        self.python_discovered = DiscoveredFile.create_mock(
            path=self.python_file,
            relative_path="test.py",
            file_type=FileType.PYTHON
        )
        
        self.markdown_discovered = DiscoveredFile.create_mock(
            path=self.markdown_file,
            relative_path="test.md",
            file_type=FileType.MARKDOWN
        )
        
        # Create a project
        self.project = DiscoveredProject.create_mock(
            name="test_project",
            root_path=self.project_dir,
            files=[self.python_discovered, self.markdown_discovered]
        )
        
        # Create a pipeline context
        self.context = MagicMock()
        self.context.project = self.project
    
    def tearDown(self):
        """Clean up after the tests."""
        self.temp_dir.cleanup()
    
    def test_code_analysis_stage(self):
        """Test the code analysis stage."""
        stage = CodeAnalysisStage()
        result_context = stage.process(self.context)
        
        # Check that analysis results were created
        self.assertTrue(hasattr(result_context, "analysis_results"))
        self.assertIn("code", result_context.analysis_results)
        self.assertIn("summary", result_context.analysis_results)
        
        # Check that Python file was analyzed
        code_results = result_context.analysis_results["code"]
        self.assertIn(str(self.python_file), code_results)
        
    def test_documentation_analysis_stage(self):
        """Test the documentation analysis stage."""
        # Set up mock results
        self.context.analysis_results = {}
        
        stage = DocumentationAnalysisStage()
        result_context = stage.process(self.context)
        
        # Check that analysis results were created
        self.assertTrue(hasattr(result_context, "analysis_results"))
        self.assertIn("documentation", result_context.analysis_results)
        self.assertIn("summary", result_context.analysis_results)
        
        # Check that Markdown file was analyzed
        doc_results = result_context.analysis_results["documentation"]
        self.assertIn(str(self.markdown_file), doc_results)
    
    def test_combined_analysis_stage(self):
        """Test the combined analysis stage."""
        stage = CombinedAnalysisStage()
        result_context = stage.process(self.context)
        
        # Check that analysis results were created
        self.assertTrue(hasattr(result_context, "analysis_results"))
        self.assertIn("code", result_context.analysis_results)
        self.assertIn("documentation", result_context.analysis_results)
        self.assertIn("summary", result_context.analysis_results)
        
        # Check that both files were analyzed
        code_results = result_context.analysis_results["code"]
        doc_results = result_context.analysis_results["documentation"]
        self.assertIn(str(self.python_file), code_results)
        self.assertIn(str(self.markdown_file), doc_results)
    
    def test_analyze_file(self):
        """Test analyzing a single file."""
        # Test with Python file
        result = analyze_file(str(self.python_file))
        self.assertTrue(result["success"])
        self.assertEqual(result["file_path"], str(self.python_file))
        
        # Test with non-existent file
        result = analyze_file("non_existent_file.py")
        self.assertFalse(result["success"])
        self.assertIn("error_message", result)
    
    def test_analyze_files(self):
        """Test analyzing multiple files."""
        # Test with valid files
        files = [
            {"path": str(self.python_file)},
            {"path": str(self.markdown_file)},
        ]
        results = analyze_files(files)
        
        self.assertEqual(len(results), 2)
        self.assertIn(str(self.python_file), results)
        self.assertIn(str(self.markdown_file), results)
        self.assertTrue(results[str(self.python_file)]["success"])
        self.assertTrue(results[str(self.markdown_file)]["success"])
        
        # Test with non-existent file
        files = [
            {"path": str(self.python_file)},
            {"path": "non_existent_file.py"},
        ]
        results = analyze_files(files)
        
        self.assertEqual(len(results), 2)
        self.assertTrue(results[str(self.python_file)]["success"])
        self.assertFalse(results["non_existent_file.py"]["success"])


if __name__ == "__main__":
    unittest.main() 