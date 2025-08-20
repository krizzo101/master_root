from __future__ import annotations

import hashlib
import logging
from typing import List

# Import inside functions to avoid circular imports
from opsvi_auto_forge.infrastructure.monitoring.metrics.hooks import time_retriever

from .models import RetrievalConfig, Snippet

logger = logging.getLogger(__name__)

# Feature flag for lexical search
LEXICAL_ENABLE = True


@time_retriever("vector")
async def vector_search(query: str, cfg: RetrievalConfig) -> List[Snippet]:
    """Vector search using ChromaDB context store."""
    try:
        from opsvi_auto_forge.infrastructure.memory.vector.chroma_client import (
            ChromaClient,
        )
        from opsvi_auto_forge.infrastructure.memory.vector.context_store import (
            ContextStore,
        )

        # Initialize vector store
        chroma_client = ChromaClient()
        context_store = ContextStore(chroma_client)

        # Search for relevant bundles
        results = context_store.search_bundles(
            query=query, top_k=cfg.top_k, min_score=0.7
        )

        snippets = []
        for doc_id, bundle, score in results:
            # Create snippet from context bundle
            snippet = Snippet(
                id=f"vec_{doc_id}",
                text=bundle.content[:1000],  # Truncate for snippet
                score=score,
                citation=f"vector://{doc_id}",
            )
            snippets.append(snippet)

        logger.info(f"Vector search returned {len(snippets)} snippets")
        return snippets

    except Exception as e:
        logger.warning(f"Vector search failed (ChromaDB not available): {e}")
        # Return empty results instead of hanging
        return []


@time_retriever("bm25")
async def bm25_search(query: str, cfg: RetrievalConfig) -> List[Snippet]:
    """BM25 lexical search using rank-bm25 library."""
    if not LEXICAL_ENABLE:
        return []

    try:
        import re
        from typing import List as TypeList

        from rank_bm25 import BM25Okapi

        # Get or create BM25 index
        bm25_index = await _get_bm25_index()
        if not bm25_index:
            logger.info("BM25 search disabled - no corpus available")
            return []

        # Tokenize query
        query_tokens = _tokenize_text(query)
        if not query_tokens:
            return []

        # Get scores and document IDs
        scores = bm25_index.get_scores(query_tokens)
        doc_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)

        # Create snippets from top results
        snippets = []
        for i, doc_idx in enumerate(doc_indices[: cfg.bm25_k]):
            if scores[doc_idx] > 0:
                doc_id = f"bm25_doc_{doc_idx}"
                snippet = Snippet(
                    id=doc_id,
                    text=f"BM25 result {i+1} (score: {scores[doc_idx]:.3f})",
                    score=float(scores[doc_idx]),
                    citation=f"bm25://{doc_id}",
                )
                snippets.append(snippet)

        logger.info(f"BM25 search returned {len(snippets)} results")
        return snippets

    except ImportError:
        logger.warning("rank-bm25 not available, BM25 search disabled")
        return []
    except Exception as e:
        logger.error(f"BM25 search failed: {e}")
        return []


async def _get_bm25_index():
    """Get or create BM25 index from corpus."""
    try:
        # Check if index exists in memory cache
        if hasattr(_get_bm25_index, "_cached_index"):
            return _get_bm25_index._cached_index

        # Load corpus from vector store or file
        corpus = await _load_bm25_corpus()
        if not corpus:
            return None

        # Tokenize corpus
        tokenized_corpus = [_tokenize_text(doc) for doc in corpus]

        # Create BM25 index
        bm25_index = BM25Okapi(tokenized_corpus)

        # Cache the index
        _get_bm25_index._cached_index = bm25_index
        return bm25_index

    except Exception as e:
        logger.error(f"Failed to create BM25 index: {e}")
        return None


async def _load_bm25_corpus():
    """Load corpus for BM25 indexing."""
    try:
        # Try to load from vector store first
        if ContextStore is not None:
            store = ContextStore()
            # Get all documents from vector store
            # This is a simplified implementation - adjust based on actual ContextStore API
            return []

        # Fallback: load from file if available
        corpus_path = "data/bm25_corpus.txt"
        try:
            with open(corpus_path, "r", encoding="utf-8") as f:
                return [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            logger.info(f"BM25 corpus file not found: {corpus_path}")
            return []

    except Exception as e:
        logger.error(f"Failed to load BM25 corpus: {e}")
        return []


def _tokenize_text(text: str) -> List[str]:
    """Simple tokenization for BM25."""
    if not text:
        return []

    # Convert to lowercase and split on whitespace/punctuation
    tokens = re.findall(r"\b\w+\b", text.lower())
    # Filter out very short tokens
    return [token for token in tokens if len(token) > 2]


@time_retriever("graph_paths")
async def graph_paths(query: str, cfg: RetrievalConfig) -> List[Snippet]:
    """Graph path search using Neo4j."""
    try:
        from opsvi_auto_forge.infrastructure.memory.graph.neo4j_client import (
            Neo4jClient,
        )

        neo4j_client = Neo4jClient()

        # Extract entities from query (simplified)
        entities = _extract_entities(query)

        snippets = []
        for entity in entities[:3]:  # Limit to top 3 entities
            # Find paths from entity to other nodes
            paths = await _find_entity_paths(neo4j_client, entity, cfg.paths_top_k)

            for path in paths:
                snippet = Snippet(
                    id=f"graph_{hashlib.md5(str(path).encode()).hexdigest()[:8]}",
                    text=f"Path: {' -> '.join(path['nodes'])}",
                    score=path["score"],
                    citation=f"graph://{entity}",
                )
                snippets.append(snippet)

        logger.info(f"Graph search returned {len(snippets)} snippets")
        return snippets

    except Exception as e:
        logger.warning(f"Graph search failed (Neo4j not available): {e}")
        # Return empty results instead of hanging
        return []


@time_retriever("web")
async def web_search(query: str, cfg: RetrievalConfig) -> List[Snippet]:
    """Web search for enrichment."""
    try:
        # TODO: Implement web search integration
        # For now, return empty results
        logger.info("Web search not implemented")
        return []

    except Exception as e:
        logger.error(f"Web search failed: {e}")
        return []


def _extract_entities(query: str) -> List[str]:
    """Extract potential entities from query."""
    # Simple entity extraction - split on common delimiters
    entities = []
    for word in query.split():
        # Remove common words and punctuation
        clean_word = word.strip(".,!?;:").lower()
        if len(clean_word) > 3 and clean_word not in [
            "the",
            "and",
            "for",
            "with",
            "from",
        ]:
            entities.append(clean_word)
    return entities


async def _find_entity_paths(
    neo4j_client: Neo4jClient, entity: str, top_k: int
) -> List[dict]:
    """Find graph paths from entity to other nodes."""
    try:
        # Cypher query to find paths from entity
        query = """
        MATCH (start)-[r*1..3]-(end)
        WHERE toLower(start.name) CONTAINS $entity
           OR toLower(end.name) CONTAINS $entity
        RETURN start.name as start_node,
               end.name as end_node,
               length(r) as path_length,
               1.0 / (length(r) + 1) as score
        ORDER BY score DESC
        LIMIT $top_k
        """

        results = await neo4j_client.run_query(
            query, {"entity": entity.lower(), "top_k": top_k}
        )

        paths = []
        for record in results:
            path = {
                "nodes": [record["start_node"], record["end_node"]],
                "edges": [f"path_{record['path_length']}"],
                "score": record["score"],
            }
            paths.append(path)

        return paths

    except Exception as e:
        logger.warning(f"Failed to find entity paths (Neo4j not available): {e}")
        return []
