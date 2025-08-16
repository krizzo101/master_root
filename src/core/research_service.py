# mypy: ignore-errors
import uuid
from datetime import datetime

from src.chunks.chunker import chunk_text
from src.db.qdrant_client import QdrantWrapper
from src.providers.openai_provider import OpenAIProvider
from src.providers.perplexity_provider import PerplexityProvider
from src.schemas.research import Citation, ResearchPackage


class ResearchService:
    def __init__(self):
        self.openai = OpenAIProvider()
        self.search_provider = PerplexityProvider()
        self.qdrant = QdrantWrapper()

    async def handle_query(self, query: str) -> ResearchPackage:
        await self.qdrant.ensure_collections()
        results = await self.search_provider.search(query, k=3)

        texts: list[str] = []
        payloads = []
        for res in results:
            text_to_chunk = res.snippet or res.title or ""
            for idx, chunk in enumerate(chunk_text(text_to_chunk, 100)):
                texts.append(chunk)
                payloads.append({
                    "source_url": res.url,
                    "title": res.title,
                    "text": chunk,
                    "chunk_index": idx,
                    "created": datetime.utcnow().isoformat(),
                })
        if texts:
            embed_resp = await self.openai.embed_texts(texts)
            await self.qdrant.upsert_chunks(embed_resp.embeddings, payloads)

        query_vec = (await self.openai.embed_texts([query])).embeddings[0]
        search_hits = await self.qdrant.search(query_vec, limit=5)

        citations: list[Citation] = []
        snippets: list[str] = []
        for hit in search_hits:
            payload = hit.payload or {}
            citations.append(
                Citation(
                    chunk_id=str(hit.id),
                    source_url=payload.get("source_url", "http://example.com"),
                    title=payload.get("title"),
                    snippet=payload.get("text", "")
                )
            )
            snippets.append(payload.get("text", ""))

        answer = "\n\n".join(snippets) if snippets else "No relevant information found."

        return ResearchPackage(
            query=query,
            answer=answer,
            citations=citations,
            audit_id=str(uuid.uuid4()),
            model_signature="o4-mini+gpt-5-mini:RAG:v1",
        )
