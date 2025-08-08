"""Simple text-splitting document processor for opsvi-rag."""
from typing import Any, List

class TextSplitter:
    def __init__(self, max_chars: int = 800) -> None:
        self.max_chars = max_chars

    async def process(self, doc: Any) -> List[str]:
        text = str(doc)
        return [text[i:i + self.max_chars] for i in range(0, len(text), self.max_chars)]
