"""Relationship chunking implementation for the hierarchical chunking strategy."""

import logging
from typing import Any, Dict, List, Set, Tuple

# Configure logging
logger = logging.getLogger(__name__)


def _chunk_relationships(self, 
                       map_structure: Dict[str, Any], 
                       chunks: Dict[str, Dict[str, Any]], 
                       master_chunk: Dict[str, Any]) -> None:
    """Chunk relationships into manageable pieces.
    
    Args:
        map_structure: The complete map structure
        chunks: The dictionary of chunks to update
        master_chunk: The master chunk to update
    """
    relationships = map_structure.get("relationships", [])
    
    if not relationships:
        logger.debug("No relationships to chunk")
        return
    
    # Estimate the token size of each relationship
    relationship_sizes = []
    for rel in relationships:
        size = self.token_estimator.estimate_tokens(rel)
        relationship_sizes.append((rel, size))
    
    logger.debug(f"Chunking {len(relationships)} relationships")
    
    # Create chunks for relationships, grouped by source element
    source_groups: Dict[str, List[Tuple[Dict[str, Any], int]]] = {}
    
    for rel, size in relationship_sizes:
        source_id = rel.get("source_id", "unknown")
        if source_id not in source_groups:
            source_groups[source_id] = []
        source_groups[source_id].append((rel, size))
    
    # Now create chunks based on these groups
    chunk_index = 1
    current_chunk = []
    current_size = 0
    current_sources = set()
    
    # Helper to finalize a chunk
    def finalize_chunk():
        nonlocal chunk_index, current_chunk, current_size, current_sources
        
        if current_chunk:
            chunks[f"rel_{chunk_index}"] = {
                "type": "relationships",
                "index": chunk_index,
                "relationships": current_chunk,
                "sources": list(current_sources)
            }
            
            # Add reference to master chunk
            master_chunk["chunks"].append({
                "id": f"rel_{chunk_index}",
                "type": "relationships",
                "count": len(current_chunk),
                "token_estimate": current_size
            })
            
            chunk_index += 1
            current_chunk = []
            current_size = 0
            current_sources = set()
    
    # Process each source group
    for source_id, rels in source_groups.items():
        group_size = sum(size for _, size in rels)
        
        # If this group alone is too large, we need to split it
        if group_size > self.target_chunk_size:
            logger.debug(f"Large relationship group for source {source_id}, size: {group_size} tokens")
            
            # Create a dedicated chunk for this source
            sub_chunk = []
            sub_size = 0
            
            for rel, size in rels:
                sub_chunk.append(rel)
                sub_size += size
                
                # If the sub-chunk is getting too large, finalize it
                if sub_size >= self.target_chunk_size:
                    chunks[f"rel_{chunk_index}"] = {
                        "type": "relationships",
                        "index": chunk_index,
                        "relationships": sub_chunk,
                        "sources": [source_id]
                    }
                    
                    # Add reference to master chunk
                    master_chunk["chunks"].append({
                        "id": f"rel_{chunk_index}",
                        "type": "relationships",
                        "count": len(sub_chunk),
                        "token_estimate": sub_size
                    })
                    
                    chunk_index += 1
                    sub_chunk = []
                    sub_size = 0
            
            # Don't forget the last sub-chunk
            if sub_chunk:
                chunks[f"rel_{chunk_index}"] = {
                    "type": "relationships",
                    "index": chunk_index,
                    "relationships": sub_chunk,
                    "sources": [source_id]
                }
                
                # Add reference to master chunk
                master_chunk["chunks"].append({
                    "id": f"rel_{chunk_index}",
                    "type": "relationships",
                    "count": len(sub_chunk),
                    "token_estimate": sub_size
                })
                
                chunk_index += 1
        else:
            # If adding this group would exceed the target size, start a new chunk
            if current_size + group_size > self.target_chunk_size and current_chunk:
                finalize_chunk()
            
            # Add all relationships from this group to the current chunk
            for rel, size in rels:
                current_chunk.append(rel)
                current_size += size
                current_sources.add(source_id)
    
    # Don't forget the last chunk
    finalize_chunk()
    
    # Update the master chunk with relationship references
    master_chunk["relationship_chunks"] = [c["id"] for c in master_chunk["chunks"] if c["type"] == "relationships"] 