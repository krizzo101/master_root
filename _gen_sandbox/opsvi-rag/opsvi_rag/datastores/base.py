"""Vector datastore base for opsvi-rag."""
from typing import Any, List
from opsvi_rag.core.base import OpsviRagManager

class VectorStore(OpsviRagManager):
    async def upsert(self, vectors: List[Any]) -> None:
        raise NotImplementedError
