"""Markdown documentation elements.

This module provides functions for working with markdown document elements.
"""

from typing import Dict, List, Optional, Any, Tuple, Union
import re

from proj_mapper.models.code import Location, LocationModel
from proj_mapper.models.documentation import DocumentationElement, DocumentationType

def detect_markdown_links(element: DocumentationElement) -> None:
    """Detect Markdown links in content and extract file references.
    
    Args:
        element: The documentation element to analyze
    """
    # Look for markdown link syntax [text](url)
    link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    for match in re.finditer(link_pattern, element.content):
        link_text = match.group(1)
        link_target = match.group(2)
        
        # Check if it's a file reference (has extension)
        if '.' in link_target and not link_target.startswith(('http://', 'https://', 'ftp://', 'mailto:')):
            element.add_reference(
                reference_type="file",
                reference_id=link_target,
                metadata={"link_text": link_text}
            )

def detect_code_references(element: DocumentationElement) -> None:
    """Detect code references in code blocks or other elements.
    
    Args:
        element: The documentation element to analyze
    """
    if element.element_type != DocumentationType.CODE_BLOCK:
        return
    
    content = element.content
    language = element.metadata.get("language", "")
    
    # Check for Python imports
    if language.lower() in ["python", "py"]:
        import_pattern = r"^\s*(from\s+(\S+)\s+)?import\s+(\S+)(\s+as\s+(\S+))?"
        for line in content.split("\n"):
            match = re.match(import_pattern, line)
            if match:
                from_module = match.group(2)
                import_name = match.group(3)
                
                # Add reference (simplified - in reality would need to resolve)
                element.add_reference(
                    reference_type="code", 
                    reference_id=f"{from_module}.{import_name}" if from_module else import_name
                )
    
    # Check for file path references
    file_path_pattern = r"['\"]([\w\-\.\/]+\.\w+)['\"]"
    for match in re.finditer(file_path_pattern, content):
        path = match.group(1)
        if "." in path:  # Only consider strings that look like file paths
            element.add_reference(
                reference_type="file",
                reference_id=path
            )
            
    # Check for VSCode-style references (line:col:file)
    vscode_ref_pattern = r"(\d+):(\d+):([^\s]+)"
    for match in re.finditer(vscode_ref_pattern, content):
        line = match.group(1)
        col = match.group(2)
        ref_file = match.group(3)
        
        element.add_reference(
            reference_type="location",
            reference_id=ref_file,
            location={
                "line": int(line),
                "column": int(col)
            }
        ) 