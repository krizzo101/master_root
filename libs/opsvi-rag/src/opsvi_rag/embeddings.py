"""Embeddings for OPSVI RAG."""


def get_embeddings(texts: list[str]) -> list[list[float]]:
    """Get embeddings for a list of texts."""
    # TODO: Implement embeddings
    return [[0.0] * 384 for _ in texts]
