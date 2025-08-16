"""Chunking utilities for project maps.

This module provides utility functions for working with chunked maps.
"""

import logging
from typing import Any, Dict, List, Optional, Set, Tuple

# Configure logging
logger = logging.getLogger(__name__)


def get_chunk_references(chunks: Dict[str, Dict[str, Any]]) -> Dict[str, List[str]]:
    """Get a mapping of which chunks reference which other chunks.
    
    Args:
        chunks: The dictionary of chunks
        
    Returns:
        A dictionary mapping chunk IDs to lists of referenced chunk IDs
    """
    references = {}
    
    for chunk_id, chunk_data in chunks.items():
        # Skip the master chunk, as it references everything
        if chunk_id == "master":
            continue
        
        chunk_references = []
        
        # Check for element references
        elements = chunk_data.get("elements", [])
        for element in elements:
            if element.get("is_reference") and "reference_chunk" in element:
                chunk_references.append(element["reference_chunk"])
        
        # Check for relationship references
        relationships = chunk_data.get("relationships", [])
        for rel in relationships:
            if rel.get("is_reference") and "reference_chunk" in rel:
                chunk_references.append(rel["reference_chunk"])
        
        # Store the references for this chunk
        if chunk_references:
            references[chunk_id] = list(set(chunk_references))
    
    return references


def merge_chunks(chunks: Dict[str, Dict[str, Any]], chunk_ids: List[str]) -> Dict[str, Any]:
    """Merge multiple chunks into a single coherent structure.
    
    Args:
        chunks: The dictionary of chunks
        chunk_ids: The IDs of chunks to merge
        
    Returns:
        A merged map structure
    """
    if not chunk_ids:
        logger.warning("No chunk IDs provided for merging")
        return {}
    
    # Start with an empty merged structure
    merged = {
        "code_elements": [],
        "documentation_elements": [],
        "relationships": []
    }
    
    # Track element IDs to avoid duplicates
    code_ids = set()
    doc_ids = set()
    rel_ids = set()
    
    # Process each chunk
    for chunk_id in chunk_ids:
        if chunk_id not in chunks:
            logger.warning(f"Chunk ID {chunk_id} not found in chunks")
            continue
        
        chunk = chunks[chunk_id]
        
        # Process code elements
        for element in chunk.get("elements", []):
            # Skip reference-only elements
            if element.get("is_reference", False):
                continue
            
            # Skip duplicates
            element_id = element.get("id")
            if not element_id or element_id in code_ids:
                continue
            
            merged["code_elements"].append(element)
            code_ids.add(element_id)
        
        # Process relationships
        for rel in chunk.get("relationships", []):
            # Skip reference-only relationships
            if rel.get("is_reference", False):
                continue
            
            # Skip duplicates (using a composite key of source and target)
            rel_key = f"{rel.get('source_id')}:{rel.get('target_id')}"
            if rel_key in rel_ids:
                continue
            
            merged["relationships"].append(rel)
            rel_ids.add(rel_key)
    
    return merged


def find_connected_chunks(chunks: Dict[str, Dict[str, Any]], start_chunk_id: str) -> List[str]:
    """Find all chunks connected to a starting chunk through references.
    
    Args:
        chunks: The dictionary of chunks
        start_chunk_id: The ID of the starting chunk
        
    Returns:
        A list of chunk IDs that are connected to the starting chunk
    """
    if start_chunk_id not in chunks:
        logger.warning(f"Start chunk ID {start_chunk_id} not found in chunks")
        return []
    
    # Get chunk references
    references = get_chunk_references(chunks)
    
    # Track visited chunks and chunks to visit
    visited = set()
    to_visit = {start_chunk_id}
    
    # Process chunks until none left to visit
    while to_visit:
        chunk_id = to_visit.pop()
        visited.add(chunk_id)
        
        # Add any referenced chunks to the to-visit set
        for ref_id in references.get(chunk_id, []):
            if ref_id not in visited and ref_id in chunks:
                to_visit.add(ref_id)
    
    return list(visited) 