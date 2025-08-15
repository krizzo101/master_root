"""Chunking processor for project maps.

This module provides the engine for processing and chunking maps into smaller,
more manageable pieces for AI consumption.
"""

import logging
from typing import Any, Dict, Optional

from proj_mapper.output.chunking.strategies import ChunkingStrategy, HierarchicalChunkingStrategy
from proj_mapper.output.config import GeneratorConfig

# Configure logging
logger = logging.getLogger(__name__)


class ChunkingEngine:
    """Engine for chunking maps into smaller pieces."""
    
    def __init__(self, strategy: Optional[ChunkingStrategy] = None):
        """Initialize the chunking engine.
        
        Args:
            strategy: The chunking strategy to use (defaults to HierarchicalChunkingStrategy)
        """
        self.strategy = strategy or HierarchicalChunkingStrategy()
    
    def chunk_map(self, map_structure: Dict[str, Any], config: GeneratorConfig) -> Dict[str, Dict[str, Any]]:
        """Chunk a map into smaller pieces.
        
        Args:
            map_structure: The complete map structure
            config: The generator configuration
            
        Returns:
            A dictionary of chunk IDs to chunk data
        """
        logger.info("Processing map for chunking")
        
        # Validate input
        if not isinstance(map_structure, dict):
            logger.error("Invalid map structure provided to chunking engine")
            raise ValueError("Map structure must be a dictionary")
        
        # Delegate to the strategy for actual chunking
        chunks = self.strategy.chunk_map(map_structure, config)
        
        logger.info(f"Map chunked into {len(chunks)} pieces")
        
        return chunks 