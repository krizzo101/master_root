"""Chunking strategies for project maps.

This module contains strategy classes for chunking large maps into smaller,
more manageable pieces for AI consumption.
"""

from proj_mapper.output.chunking.strategies.base import ChunkingStrategy
from proj_mapper.output.chunking.strategies.hierarchical import HierarchicalChunkingStrategy

__all__ = [
    'ChunkingStrategy',
    'HierarchicalChunkingStrategy'
] 