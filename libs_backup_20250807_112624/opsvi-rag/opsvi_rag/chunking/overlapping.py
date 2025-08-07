"""
overlapping chunking for opsvi-rag.

Overlapping text chunking
"""

from dataclasses import dataclass

from opsvi_foundation import BaseComponent, ComponentError, get_logger
from pydantic import BaseModel, Field


class ChunkingError(ComponentError):
    """Raised when chunking fails."""

    pass


@dataclass
class Chunk:
    """Represents a text chunk."""

    content: str
    start_index: int
    end_index: int
    metadata: dict


class OverlappingChunkerConfig(BaseModel):
    """Configuration for overlapping chunking."""

    chunk_size: int = Field(default=1000, description="Target chunk size in characters")
    overlap_size: int = Field(default=200, description="Overlap between chunks")
    # Add specific configuration options here


class OverlappingChunker(BaseComponent):
    """overlapping chunking strategy."""

    def __init__(self, config: OverlappingChunkerConfig):
        """Initialize overlapping chunker."""
        super().__init__()
        self.config = config
        self.logger = get_logger(__name__)

    def chunk(self, text: str) -> list[Chunk]:
        """Chunk the given text."""
        # TODO: Implement overlapping chunking logic
        chunks = []
        # Add chunking implementation here
        return chunks
