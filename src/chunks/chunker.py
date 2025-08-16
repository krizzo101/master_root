
import tiktoken


def chunk_text(text: str, tokens_per_chunk: int = 300, overlap: int = 50) -> list[str]:
    enc = tiktoken.get_encoding("cl100k_base")
    tokens = enc.encode(text)
    chunks: list[str] = []
    step = tokens_per_chunk - overlap
    for i in range(0, len(tokens), step):
        chunk_tokens = tokens[i : i + tokens_per_chunk]
        chunks.append(enc.decode(chunk_tokens))
    return chunks
