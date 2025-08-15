"""Tests for the analysis pipeline."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from proj_mapper.analyzers.pipeline import AnalysisPipeline
from proj_mapper.models.analysis import CodeAnalysisResult, DocumentationAnalysisResult
from proj_mapper.models.code import CodeElement, CodeReference, CodeElementType, Location
from proj_mapper.models.documentation import DocumentationElement, DocumentationType, DocumentationReference
from proj_mapper.models.file import DiscoveredFile, DiscoveredProject, FileType


class TestAnalysisPipeline(unittest.TestCase):
    """Tests for the AnalysisPipeline class."""
    
    def setUp(self):
        """Set up for the tests."""
        self.pipeline = AnalysisPipeline(max_workers=1)  # Use 1 worker for deterministic testing
        
        # Create temporary files for testing
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_dir = Path(self.temp_dir.name)
        
        # Create Python file
        self.python_file_path = self.project_dir / "test_module.py"
        with open(self.python_file_path, "w") as f:
            f.write('''"""Test module for testing analysis."""
import os
from pathlib import Path

def test_function():
    """Test function docstring."""
    return "test"
''')
            
        # Create Markdown file
        self.markdown_file_path = self.project_dir / "README.md"
        with open(self.markdown_file_path, "w") as f:
            f.write('''# Test Project

This is a test project for testing the analysis pipeline.

## Usage

```python
from test_module import test_function

result = test_function()
print(result)
```
''')
            
        # Create test project
        self.python_file = DiscoveredFile.create_mock(
            path=self.python_file_path,
            relative_path="test_module.py",
            file_type=FileType.PYTHON
        )
        
        self.markdown_file = DiscoveredFile.create_mock(
            path=self.markdown_file_path,
            relative_path="README.md",
            file_type=FileType.MARKDOWN
        )
        
        self.project = DiscoveredProject.create_mock(
            name="test_project",
            root_path=self.project_dir,
            files=[self.python_file, self.markdown_file]
        )
        
    def tearDown(self):
        """Clean up temporary files."""
        self.temp_dir.cleanup()
        
    def test_analyze_project(self):
        """Test analyzing a project."""
        results = self.pipeline.analyze_project(self.project)
        
        # Should have analyzed both files
        self.assertEqual(len(results), 2)
        self.assertIn(str(self.python_file_path), results)
        self.assertIn(str(self.markdown_file_path), results)
        
        # Check result types
        self.assertIsInstance(results[str(self.python_file_path)], CodeAnalysisResult)
        self.assertIsInstance(results[str(self.markdown_file_path)], DocumentationAnalysisResult)
        
        # Check specialized result collections
        self.assertEqual(len(self.pipeline.code_results), 1)
        self.assertEqual(len(self.pipeline.doc_results), 1)
        
    def test_analyze_project_with_filter(self):
        """Test analyzing a project with file type filter."""
        results = self.pipeline.analyze_project(self.project, file_types={FileType.PYTHON})
        
        # Should have analyzed only the Python file
        self.assertEqual(len(results), 1)
        self.assertIn(str(self.python_file_path), results)
        self.assertNotIn(str(self.markdown_file_path), results)
        
    def test_get_related_files(self):
        """Test getting related files."""
        # Create mock results with references
        code_result = CodeAnalysisResult(file_path="/path/to/source.py")
        code_element = CodeElement.create_mock(
            id="test_element",
            name="test_function",
            element_type=CodeElementType.FUNCTION,
            file_path="/path/to/source.py",
            line_start=1
        )
        ref = CodeReference(
            source_id="test_element",
            reference_id="target_module",
            reference_type="import"
        )
        code_element.references.append(ref)
        code_result.elements.append(code_element)
        
        # Add results to pipeline
        self.pipeline.results = {
            "/path/to/source.py": code_result,
            "/path/to/target_module.py": CodeAnalysisResult(file_path="/path/to/target_module.py")
        }
        self.pipeline.code_results = {
            "/path/to/source.py": code_result,
            "/path/to/target_module.py": CodeAnalysisResult(file_path="/path/to/target_module.py")
        }
        
        # Get related files
        related = self.pipeline.get_related_files("/path/to/source.py", "import")
        
        # Should find the reference
        self.assertEqual(len(related), 1)
        self.assertIn("/path/to/target_module.py", related)
        
    def test_get_code_references_to_file(self):
        """Test getting code references to a file."""
        # Create mock results with references
        code_result = CodeAnalysisResult(file_path="/path/to/source.py")
        code_element = CodeElement.create_mock(
            id="test_element",
            name="test_function",
            element_type=CodeElementType.FUNCTION,
            file_path="/path/to/source.py",
            line_start=1,
            line_end=5
        )
        
        location = Location(file_path="/path/to/source.py", start_line=3, end_line=3)
        code_element.location = location
        
        # Use the exact same target filename in the reference and the lookup
        target_file = "target.py"
        
        ref = CodeReference(
            source_id="test_element",
            reference_id=target_file,
            reference_type="import",
            location=location
        )
        code_element.references.append(ref)
        code_result.elements.append(code_element)
        
        # Add results to pipeline
        self.pipeline.results = {"/path/to/source.py": code_result}
        self.pipeline.code_results = {"/path/to/source.py": code_result}
        
        # Get references to file - use the exact same path as in the reference
        references = self.pipeline.get_code_references_to_file(target_file)
        
        # Should find the reference
        self.assertEqual(len(references), 1)
        self.assertIn("/path/to/source.py", references)
        self.assertEqual(len(references["/path/to/source.py"]), 1)
        self.assertEqual(references["/path/to/source.py"][0]["referencing_element"], "test_function")
        
    def test_get_documentation_for_code(self):
        """Test getting documentation references to code."""
        # Create mock doc results with references
        doc_result = DocumentationAnalysisResult(file_path="/path/to/readme.md")
        doc_element = DocumentationElement(
            title="code_block",
            element_type=DocumentationType.CODE_BLOCK,
            location=Location(file_path="/path/to/readme.md", start_line=10, end_line=15),
            content="import module"
        )
        doc_element.add_reference("file", "target.py")
        doc_result.elements.append(doc_element)
        
        # Add results to pipeline
        self.pipeline.results = {"/path/to/readme.md": doc_result}
        self.pipeline.doc_results = {"/path/to/readme.md": doc_result}
        
        # Get documentation for code
        references = self.pipeline.get_documentation_for_code("/path/to/target.py")
        
        # Should find the reference
        self.assertEqual(len(references), 1)
        self.assertIn("/path/to/readme.md", references)
        self.assertEqual(len(references["/path/to/readme.md"]), 1)
        self.assertEqual(references["/path/to/readme.md"][0]["doc_element"], "code_block")
        
    def test_generate_summary(self):
        """Test generating a summary."""
        # Analyze the project
        self.pipeline.analyze_project(self.project)
        
        # Generate summary
        summary = self.pipeline.generate_summary()
        
        # Check summary content
        self.assertEqual(summary["total_files_analyzed"], 2)
        self.assertEqual(summary["code_files"], 1)
        self.assertEqual(summary["documentation_files"], 1)
        self.assertEqual(summary["successful_analyses"], 2)
        self.assertEqual(summary["failed_analyses"], 0)
        self.assertIn("file_types", summary)
        self.assertIn(".py", summary["file_types"])
        self.assertIn(".md", summary["file_types"])
        
    def test_generate_summary_with_errors(self):
        """Test generating a summary with errors."""
        # Create failed results
        python_result = CodeAnalysisResult(
            file_path=str(self.python_file_path),
            success=False,
            error_message="Test error"
        )
        
        markdown_result = DocumentationAnalysisResult(
            file_path=str(self.markdown_file_path)
        )
        
        # Add results to pipeline
        self.pipeline.results = {
            str(self.python_file_path): python_result,
            str(self.markdown_file_path): markdown_result
        }
        self.pipeline.code_results = {str(self.python_file_path): python_result}
        self.pipeline.doc_results = {str(self.markdown_file_path): markdown_result}
        
        # Generate summary
        summary = self.pipeline.generate_summary()
        
        # Check summary content
        self.assertEqual(summary["total_files_analyzed"], 2)
        self.assertEqual(summary["successful_analyses"], 1)
        self.assertEqual(summary["failed_analyses"], 1)
        self.assertEqual(len(summary["errors"]), 1)
        self.assertEqual(summary["errors"][0]["file"], str(self.python_file_path))
        self.assertEqual(summary["errors"][0]["error"], "Test error")


if __name__ == "__main__":
    unittest.main() 