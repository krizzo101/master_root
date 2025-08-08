"""Document processors for opsvi-rag."""
from typing import Any

class DocumentProcessor:
    async def process(self, doc: Any) -> Any:
        raise NotImplementedError
