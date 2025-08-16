"""
Embedding Module
Provides functions to generate embedding vectors for text artifacts using OpenAI, with token-based chunking and error handling.
"""

import logging
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.applications.agentic_doc_manager.graph_manager import enqueue_embedding_job
from src.shared.openai_interfaces.embeddings_interface import OpenAIEmbeddingsInterface

# Try to import tiktoken for token counting
try:
    import tiktoken

    enc = tiktoken.get_encoding("cl100k_base")

    def split_to_token_chunks(text, limit=8192):
        tokens = enc.encode(text)
        if len(tokens) <= limit:
            return [text]
        # Split into chunks, but never send a chunk > limit
        chunks = []
        for i in range(0, len(tokens), limit):
            chunk_tokens = tokens[i : i + limit]
            if len(chunk_tokens) > limit:
                logging.warning(
                    f"A chunk for embedding exceeds {limit} tokens and will be skipped."
                )
                continue
            chunks.append(enc.decode(chunk_tokens))
        return chunks

except ImportError:

    def split_to_token_chunks(text, limit=8192):
        raise RuntimeError(
            "tiktoken is required for robust token-based chunking. Please install tiktoken."
        )


EMBEDDING_ENABLED = os.getenv("EMBEDDING_ENABLED", "false").lower() == "true"


def embed_text(text, path=None, chunk=None):
    """
    Generate an embedding vector for the input text using OpenAIEmbeddingsInterface.
    If embedding is disabled, enqueue the job for later processing.
    """
    if not EMBEDDING_ENABLED:
        enqueue_embedding_job(path or "unknown", text, chunk)
        logging.info(f"Embedding disabled. Enqueued job for {path or 'unknown'}.")
        return []
    embeddings_client = OpenAIEmbeddingsInterface()
    embeddings = []
    for chunk_text in split_to_token_chunks(text, 8192):
        try:
            response = embeddings_client.create_embedding(
                input_text=chunk_text, model="text-embedding-ada-002"
            )
            embeddings.append(response["data"][0]["embedding"])
        except Exception as e:
            logging.error(f"Embedding failed for chunk: {e}")
    return embeddings


def embed_all(artifacts):
    """
    Embed all artifacts using OpenAIEmbeddingsInterface or enqueue if disabled.
    Splits large artifacts into chunks and logs skipped ones.
    Returns list of (path, embedding) pairs for all chunks.
    """
    results = []
    for path, content in artifacts:
        try:
            chunk_embeddings = embed_text(content, path=path)
        except RuntimeError as e:
            logging.error(f"Artifact {path} skipped: {e}")
            continue
        if not EMBEDDING_ENABLED:
            # All jobs enqueued, nothing to return
            continue
        if not chunk_embeddings:
            logging.warning(f"Artifact {path} skipped (embedding failed or too large).")
            continue
        for i, emb in enumerate(chunk_embeddings):
            results.append(
                (f"{path}#chunk{i+1}" if len(chunk_embeddings) > 1 else path, emb)
            )
    return results


if __name__ == "__main__":
    from src.applications.agentic_doc_manager.ingestion import ingest_all

    artifacts = ingest_all()
    embeddings = embed_all(artifacts[:2])  # Limit for quick test
    print(f"Embedded {len(embeddings)} artifact chunks.")
    print("Sample:", embeddings[0] if embeddings else "No embeddings.")
