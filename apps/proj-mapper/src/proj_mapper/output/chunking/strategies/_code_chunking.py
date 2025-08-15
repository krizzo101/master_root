"""Code element chunking implementation for the hierarchical chunking strategy."""

import logging
from typing import Any, Dict

# Configure logging
logger = logging.getLogger(__name__)


def _chunk_code_elements(self, 
                       map_structure: Dict[str, Any], 
                       chunks: Dict[str, Dict[str, Any]], 
                       master_chunk: Dict[str, Any]) -> None:
    """Chunk code elements into manageable pieces.
    
    Args:
        map_structure: The complete map structure
        chunks: The dictionary of chunks to update
        master_chunk: The master chunk to update
    """
    code_elements = map_structure.get("code_elements", [])
    
    if not code_elements:
        logger.debug("No code elements to chunk")
        return
    
    # Estimate the token size of each code element
    element_sizes = []
    for element in code_elements:
        size = self.token_estimator.estimate_tokens(element)
        element_sizes.append((element, size))
    
    # Sort elements by size (largest first) to help with balanced chunking
    element_sizes.sort(key=lambda x: x[1], reverse=True)
    
    logger.debug(f"Chunking {len(code_elements)} code elements")
    
    # Create chunks for code elements
    current_chunk = []
    current_size = 0
    chunk_index = 1
    
    for element, size in element_sizes:
        # If the element itself is too large, we might need to trim it
        if size > self.target_chunk_size:
            logger.debug(f"Large code element found: {element.get('id', 'unknown')}, size: {size} tokens")
            
            # Create a reference-only version for other chunks
            reference_element = {
                "id": element.get("id"),
                "name": element.get("name"),
                "type": element.get("type"),
                "location": element.get("location"),
                "is_reference": True,
                "reference_chunk": f"code_{chunk_index}"
            }
            
            # Create a dedicated chunk for this large element
            chunks[f"code_{chunk_index}"] = {
                "type": "code",
                "index": chunk_index,
                "elements": [element]
            }
            
            # Add reference to master chunk
            master_chunk["chunks"].append({
                "id": f"code_{chunk_index}",
                "type": "code",
                "count": 1,
                "token_estimate": size
            })
            
            # Store the reference instead of the full element
            element = reference_element
            size = self.token_estimator.estimate_tokens(reference_element)
            chunk_index += 1
        
        # If adding this element would exceed the target size, start a new chunk
        if current_size + size > self.target_chunk_size and current_chunk:
            chunks[f"code_{chunk_index}"] = {
                "type": "code",
                "index": chunk_index,
                "elements": current_chunk
            }
            
            # Add reference to master chunk
            master_chunk["chunks"].append({
                "id": f"code_{chunk_index}",
                "type": "code",
                "count": len(current_chunk),
                "token_estimate": current_size
            })
            
            chunk_index += 1
            current_chunk = []
            current_size = 0
        
        current_chunk.append(element)
        current_size += size
    
    # Don't forget the last chunk
    if current_chunk:
        chunks[f"code_{chunk_index}"] = {
            "type": "code",
            "index": chunk_index,
            "elements": current_chunk
        }
        
        # Add reference to master chunk
        master_chunk["chunks"].append({
            "id": f"code_{chunk_index}",
            "type": "code",
            "count": len(current_chunk),
            "token_estimate": current_size
        })
    
    # Update the master chunk with element references
    master_chunk["code_chunks"] = [c["id"] for c in master_chunk["chunks"] if c["type"] == "code"] 