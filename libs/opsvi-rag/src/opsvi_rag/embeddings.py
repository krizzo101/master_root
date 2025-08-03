"""Embeddings for OPSVI RAG."""

from typing import List


def get_embeddings(texts: List[str]) -> List[List[float]]:
    """Get embeddings for a list of texts."""
    # TODO: Implement embeddings
    return [[0.0] * 384 for _ in texts]
