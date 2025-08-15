"""Integration tests for the Documentation analyzer with the pipeline system."""

import os
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional

import pytest

from proj_mapper.core.pipeline import Pipeline, PipelineContext
from proj_mapper.analyzers.documentation import MarkdownAnalyzer, DocumentationAnalysisStage
from proj_mapper.models.file import DiscoveredFile, FileType


@pytest.fixture
def test_docs_dir():
    """Create a temporary directory with test documentation files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a simple markdown file
        simple_file = Path(temp_dir) / "simple.md"
        simple_content = """# Simple Document

This is a simple markdown document for testing.

## Introduction

This document demonstrates basic Markdown features.

## Features

- Lists
- *Emphasis*
- **Strong emphasis**
- `Code snippets`

## Conclusion

This is a test document.
"""
        with open(simple_file, 'w') as f:
            f.write(simple_content)

        # Create a markdown file with front matter
        front_matter_file = Path(temp_dir) / "with_frontmatter.md"
        front_matter_content = """---
title: Document with Front Matter
author: Test Author
version: 1.0.0
---

# Document with Front Matter

This document has YAML front matter.

## Section 1

Content with code reference to `analyze_markdown()` function.

```python
def sample_code():
    print("This is sample code")
```

## Section 2

More content here.
"""
        with open(front_matter_file, 'w') as f:
            f.write(front_matter_content)

        yield temp_dir


class TestDocumentationAnalyzerPipeline:
    """Integration tests for the Documentation analyzer pipeline."""
    
    def test_documentation_analyzer_pipeline(self, test_docs_dir):
        """Test that the Documentation analyzer works correctly within a pipeline."""
        # Create discovered files
        project_path = Path(test_docs_dir)
        
        simple_file = project_path / "simple.md"
        front_matter_file = project_path / "with_frontmatter.md"
        
        discovered_files = [
            DiscoveredFile.from_path(simple_file, project_path),
            DiscoveredFile.from_path(front_matter_file, project_path)
        ]
        
        # Create and run pipeline
        pipeline = Pipeline()
        doc_analysis_stage = DocumentationAnalysisStage()
        pipeline.add_stage(doc_analysis_stage)
        
        results = pipeline.run(discovered_files)
        
        # Check results
        assert len(results) == 2
        assert all(r["success"] for r in results)
        
        # Check context
        context = pipeline.context
        assert context.contains("documentation_analysis_results")
        
        # Verify analysis results in context
        analysis_results = context.get("documentation_analysis_results")
        assert len(analysis_results) == 2
        
        # Check simple.md analysis
        simple_result = next(r for r in analysis_results 
                          if r["file"].relative_path == "simple.md")
        assert simple_result["success"]
        
        simple_analysis = simple_result["analysis"]
        assert simple_analysis.title == "Simple Document"
        assert "simple markdown document" in simple_analysis.summary
        
        # Check with_frontmatter.md analysis
        frontmatter_result = next(r for r in analysis_results 
                              if r["file"].relative_path == "with_frontmatter.md")
        assert frontmatter_result["success"]
        
        frontmatter_analysis = frontmatter_result["analysis"]
        assert frontmatter_analysis.title == "Document with Front Matter"
        assert "metadata" in frontmatter_analysis.__dict__
        assert frontmatter_analysis.metadata.get("author") == "Test Author"
        
        # Check that elements were extracted correctly
        sections = frontmatter_analysis.get_sections()
        assert len(sections) >= 3  # Main + 2 sections 