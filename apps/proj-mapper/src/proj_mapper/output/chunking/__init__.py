"""Chunking engine for project maps.

This module provides functionality for chunking large maps into smaller,
more manageable pieces for AI consumption.
"""

from proj_mapper.output.chunking.strategies import (
    ChunkingStrategy,
    HierarchicalChunkingStrategy
)
from proj_mapper.output.chunking.processor import ChunkingEngine
from proj_mapper.output.chunking.utils import (
    get_chunk_references,
    merge_chunks,
    find_connected_chunks
)

__all__ = [
    'ChunkingStrategy',
    'HierarchicalChunkingStrategy',
    'ChunkingEngine',
    'get_chunk_references',
    'merge_chunks',
    'find_connected_chunks'
] 