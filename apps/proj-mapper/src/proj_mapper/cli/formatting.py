"""Formatting utilities for CLI outputs.

This module provides utility functions for formatting data outputs in the CLI.
"""

import json
from typing import List, Dict, Any

def format_relationship(relationships: List[Dict[str, Any]], format_type: str = "text") -> str:
    """Format relationships for display.
    
    Args:
        relationships: List of relationship dictionaries to format
        format_type: Output format type (json, table, or text)
        
    Returns:
        Formatted string representation of relationships
    """
    if format_type == "json":
        return json.dumps(relationships, indent=2)
    
    if format_type == "table":
        return _format_as_table(relationships)
    
    # Default to text format
    return _format_as_text(relationships)

def _format_as_table(relationships: List[Dict[str, Any]]) -> str:
    """Format relationships as a table.
    
    Args:
        relationships: List of relationship dictionaries to format
        
    Returns:
        Table-formatted string representation
    """
    if not relationships:
        return "No relationships found."
    
    # Create header
    result = f"{'SOURCE ID':<40} | {'TARGET ID':<40} | {'TYPE':<20} | {'CONFIDENCE':<10}\n"
    result += "-" * 120 + "\n"
    
    # Add rows
    for rel in relationships:
        source_id = rel.get('source_id', '')[:38]
        target_id = rel.get('target_id', '')[:38]
        rel_type = rel.get('relationship_type', '')[:18]
        confidence = f"{rel.get('confidence', 0.0):.2f}"
        
        result += f"{source_id:<40} | {target_id:<40} | {rel_type:<20} | {confidence:<10}\n"
    
    return result

def _format_as_text(relationships: List[Dict[str, Any]]) -> str:
    """Format relationships as plain text.
    
    Args:
        relationships: List of relationship dictionaries to format
        
    Returns:
        Text-formatted string representation
    """
    if not relationships:
        return "No relationships found."
    
    result = f"Found {len(relationships)} relationships:\n\n"
    
    for i, rel in enumerate(relationships, 1):
        source_id = rel.get('source_id', 'unknown')
        target_id = rel.get('target_id', 'unknown')
        rel_type = rel.get('relationship_type', 'unknown')
        confidence = rel.get('confidence', 0.0)
        
        result += f"Relationship {i}:\n"
        result += f"  Source: {source_id}\n"
        result += f"  Target: {target_id}\n"
        result += f"  Type: {rel_type}\n"
        result += f"  Confidence: {confidence:.2f}\n"
        
        if rel.get('metadata'):
            result += f"  Metadata: {json.dumps(rel.get('metadata'), indent=2)}\n"
        
        result += "\n"
    
    return result 