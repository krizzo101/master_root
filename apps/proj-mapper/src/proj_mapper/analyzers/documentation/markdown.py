"""Markdown documentation analyzer.

This module provides an analyzer for Markdown documentation files.

Note: This file is maintained for backward compatibility.
The implementation has been refactored into multiple modules under the
`proj_mapper.analyzers.documentation.markdown` package.
"""

# Re-export the MarkdownAnalyzer class and related components
from proj_mapper.analyzers.documentation.markdown.analyzer import MarkdownAnalyzer
from proj_mapper.analyzers.documentation.markdown.elements import detect_markdown_links, detect_code_references
from proj_mapper.analyzers.documentation.markdown.parser import MarkdownParser

__all__ = ['MarkdownAnalyzer'] 