"""Base classes for chunking strategies.

This module contains base classes for implementing chunking strategies.
"""

import logging
from typing import Any, Dict

from proj_mapper.output.config import GeneratorConfig

# Configure logging
logger = logging.getLogger(__name__)


class ChunkingStrategy:
    """Base class for chunking strategies."""
    
    def chunk_map(self, map_structure: Dict[str, Any], config: GeneratorConfig) -> Dict[str, Dict[str, Any]]:
        """Chunk a map into smaller pieces.
        
        Args:
            map_structure: The complete map structure
            config: The generator configuration
            
        Returns:
            A dictionary of chunk IDs to chunk data
        """
        raise NotImplementedError("Subclasses must implement this method") 