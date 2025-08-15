"""Hierarchical chunking strategy for project maps.

This module contains the implementation of a hierarchical chunking strategy
that creates a hierarchy of chunks based on map sections.
"""

import logging
import copy
from typing import Any, Dict, List, Set, Tuple

from proj_mapper.output.ai_optimization import TokenizationEstimator
from proj_mapper.output.config import GeneratorConfig
from proj_mapper.output.chunking.strategies.base import ChunkingStrategy

# Import chunking implementations
from proj_mapper.output.chunking.strategies._code_chunking import _chunk_code_elements
from proj_mapper.output.chunking.strategies._doc_chunking import _chunk_documentation_elements
from proj_mapper.output.chunking.strategies._relationship_chunking import _chunk_relationships

# Configure logging
logger = logging.getLogger(__name__)


class HierarchicalChunkingStrategy(ChunkingStrategy):
    """Chunking strategy that creates a hierarchy of chunks based on map sections."""
    
    def __init__(self, target_chunk_size: int = 4000, overlap: float = 0.1):
        """Initialize the chunking strategy.
        
        Args:
            target_chunk_size: The target token size for each chunk
            overlap: The percentage of overlap between chunks (0.0-1.0)
        """
        self.target_chunk_size = target_chunk_size
        self.overlap = overlap
        self.token_estimator = TokenizationEstimator()
    
    def chunk_map(self, map_structure: Dict[str, Any], config: GeneratorConfig) -> Dict[str, Dict[str, Any]]:
        """Chunk a map into smaller pieces using a hierarchical approach.
        
        Args:
            map_structure: The complete map structure
            config: The generator configuration
            
        Returns:
            A dictionary of chunk IDs to chunk data
        """
        logger.info(f"Chunking map with target size {self.target_chunk_size} tokens")
        
        # Create a copy of the map to avoid modifying the original
        map_copy = copy.deepcopy(map_structure)
        
        # Create a master chunk with metadata and references
        master_chunk = {
            "type": "master",
            "project": map_copy.get("project", "Unknown Project"),
            "version": map_copy.get("version", "1.0.0"),
            "chunks": [],
            "statistics": map_copy.get("statistics", {}),
        }
        
        # Initialize the chunks dictionary with the master chunk
        chunks = {"master": master_chunk}
        
        # Process the code elements
        self._chunk_code_elements(map_copy, chunks, master_chunk)
        
        # Process the documentation elements
        self._chunk_documentation_elements(map_copy, chunks, master_chunk)
        
        # Process the relationships
        self._chunk_relationships(map_copy, chunks, master_chunk)
        
        # Update the master chunk with final chunk count
        master_chunk["chunk_count"] = len(chunks)
        
        logger.info(f"Created {len(chunks)} chunks from map")
        
        return chunks
    
    # Add the chunking methods
    _chunk_code_elements = _chunk_code_elements
    _chunk_documentation_elements = _chunk_documentation_elements
    _chunk_relationships = _chunk_relationships 