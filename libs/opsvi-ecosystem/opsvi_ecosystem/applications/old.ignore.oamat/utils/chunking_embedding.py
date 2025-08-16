import logging
import os

import openai
import tiktoken

logging.basicConfig(level=logging.DEBUG, format="[%(levelname)s] %(message)s")


# Stub for OpenAI embedding API call
def get_openai_embedding(text: str) -> list[float]:
    try:
        model = os.environ.get("OAMAT_EMBEDDING_MODEL", "text-embedding-3-small")
        if not model:
            logging.error(
                "No embedding model specified. Set OAMAT_EMBEDDING_MODEL or use default."
            )
            return [0.0] * 1536

        # Debug logging
        logging.info(
            f"Getting embedding for text of length: {len(text) if text else 0}"
        )
        if not text or len(text.strip()) == 0:
            logging.warning("Empty or whitespace-only text provided for embedding")
            return [0.0] * 1536

        # Clean text for API
        clean_text = text.strip()
        if len(clean_text) > 8000:  # Truncate very long text
            clean_text = clean_text[:8000]
            logging.warning("Text truncated to 8000 characters for embedding")

        response = openai.embeddings.create(input=clean_text, model=model)
        return response.data[0].embedding
    except Exception:
        logging.error("OpenAI embedding error:", exc_info=True)
        return [0.0] * 1536  # Return a dummy embedding for stub/demo mode


def chunk_text(text: str, chunk_size: int = 1500, overlap: int = 200) -> list[str]:
    """
    Split text into chunks of chunk_size tokens with overlap.
    """
    enc = tiktoken.get_encoding("cl100k_base")
    tokens = enc.encode(text)
    chunks = []
    start = 0
    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_text = enc.decode(chunk_tokens)
        chunks.append(chunk_text)
        if end == len(tokens):
            break
        start += chunk_size - overlap
    return chunks


def chunk_and_embed_document(text: str) -> list[dict]:
    """
    Chunk text and embed each chunk. Returns list of dicts with 'text' and 'embedding'.
    """
    chunk_texts = chunk_text(text)
    result = []
    for chunk in chunk_texts:
        embedding = get_openai_embedding(chunk)
        result.append({"text": chunk, "embedding": embedding})
    return result
