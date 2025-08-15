"""Tests for the Markdown analyzer."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from proj_mapper.analyzers.documentation.markdown import MarkdownAnalyzer
from proj_mapper.models.documentation import DocumentationType
from proj_mapper.models.file import DiscoveredFile, FileType


class TestMarkdownAnalyzer(unittest.TestCase):
    """Tests for the MarkdownAnalyzer class."""
    
    def setUp(self):
        """Set up for the tests."""
        self.analyzer = MarkdownAnalyzer()
        
        # Create a temporary file for testing
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_file_path = Path(self.temp_dir.name) / "test_file.md"
        
        # Simple Markdown content for testing
        self.markdown_content = """---
title: Test Document
author: Test Author
---

# Heading 1

This is a paragraph with some text.

## Heading 2

This is another paragraph.

```python
import os
from pathlib import Path

def test_function():
    return "test"
```

### Heading 3

- List item 1
- List item 2
- List item 3

Reference to [test_file.py](./test_file.py)
"""
        
        # Write content to the file
        with open(self.temp_file_path, "w") as f:
            f.write(self.markdown_content)
            
        # Create a discovered file
        self.file = DiscoveredFile.create_mock(
            path=self.temp_file_path,
            relative_path=self.temp_file_path.name,
            file_type=FileType.MARKDOWN
        )
        
    def tearDown(self):
        """Clean up after the tests."""
        self.temp_dir.cleanup()
        
    def test_can_analyze(self):
        """Test the can_analyze method."""
        # Markdown file
        md_file = DiscoveredFile.create_mock(
            path=Path("test.md"),
            relative_path="test.md",
            file_type=FileType.MARKDOWN
        )
        self.assertTrue(self.analyzer.can_analyze(md_file))
        
        # Alternate Markdown extension
        markdown_file = DiscoveredFile.create_mock(
            path=Path("test.markdown"),
            relative_path="test.markdown",
            file_type=FileType.TEXT
        )
        self.assertTrue(self.analyzer.can_analyze(markdown_file))
        
        # Non-Markdown file
        text_file = DiscoveredFile.create_mock(
            path=Path("test.txt"),
            relative_path="test.txt",
            file_type=FileType.TEXT
        )
        self.assertFalse(self.analyzer.can_analyze(text_file))
        
    def test_analyze(self):
        """Test the analyze method."""
        result = self.analyzer.analyze(self.file)
        
        # Check basic properties
        self.assertTrue(result.success)
        self.assertIsNone(result.error_message)
        self.assertEqual(result.file_path, str(self.temp_file_path))
        
        # Should have found elements
        self.assertGreater(len(result.elements), 0)
        
        # Check if found the front matter
        self.assertIsNotNone(result.metadata)
        self.assertEqual(result.metadata.get("title"), "Test Document")
        self.assertEqual(result.metadata.get("author"), "Test Author")
        
        # Check if title was extracted
        self.assertEqual(result.title, "Test Document")
        
        # Check for specific element types
        element_types = {elem.element_type for elem in result.elements}
        
        self.assertIn(DocumentationType.SECTION, element_types)
        self.assertIn(DocumentationType.PARAGRAPH, element_types)
        self.assertIn(DocumentationType.CODE_BLOCK, element_types)
        self.assertIn(DocumentationType.LIST, element_types)
        
        # Check heading elements
        headings = [e for e in result.elements if e.element_type == DocumentationType.SECTION]
        heading_titles = {e.title for e in headings}
        
        self.assertIn("Heading 1", heading_titles)
        self.assertIn("Heading 2", heading_titles)
        self.assertIn("Heading 3", heading_titles)
        
        # Check code block
        code_blocks = [e for e in result.elements if e.element_type == DocumentationType.CODE_BLOCK]
        self.assertGreaterEqual(len(code_blocks), 1)
        
        # Check if code elements have language info
        python_block = None
        for block in code_blocks:
            if block.metadata.get("language") == "python":
                python_block = block
                break
                
        self.assertIsNotNone(python_block)
        self.assertIn("import os", python_block.content)
        
        # Check for file references
        found_reference = False
        for elem in result.elements:
            for ref in elem.references:
                # References are now dictionaries, not objects
                if ref.get("reference_type") == "file" and ref.get("reference_id") == "./test_file.py":
                    found_reference = True
                    break
                    
        self.assertTrue(found_reference)
        
    def test_analyze_with_errors(self):
        """Test analyzing a nonexistent file."""
        # Test with a nonexistent file
        nonexistent_path = Path(self.temp_dir.name) / "nonexistent.md"
        nonexistent_file = DiscoveredFile.create_mock(
            path=nonexistent_path,
            relative_path="nonexistent.md",
            file_type=FileType.MARKDOWN
        )
        
        result = self.analyzer.analyze(nonexistent_file)
        
        # Check error handling
        self.assertFalse(result.success)
        self.assertIsNotNone(result.error_message)
        
    def test_extract_front_matter(self):
        """Test the front matter extraction."""
        # YAML front matter
        content = """---
title: Test
author: Author
---

Content"""
        # Use the parser instance from the analyzer
        content_without_front_matter, metadata = self.analyzer.parser.extract_front_matter(content)
        
        self.assertEqual(metadata.get("title"), "Test")
        self.assertEqual(metadata.get("author"), "Author")
        self.assertEqual(content_without_front_matter.strip(), "Content")
        
        # No front matter
        content = "# Title\n\nContent"
        content_without_front_matter, metadata = self.analyzer.parser.extract_front_matter(content)
        
        self.assertEqual(metadata, {})
        self.assertEqual(content_without_front_matter.strip(), "# Title\n\nContent")


if __name__ == "__main__":
    unittest.main() 