"""Embeddings providers for opsvi-rag."""
from typing import List

class EmbeddingsProvider:
    async def embed(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError
