from src.chunks.chunker import chunk_text


def test_chunker_basic():
    text = "a " * 1000
    chunks = chunk_text(text, tokens_per_chunk=100, overlap=10)
    assert len(chunks) > 0
    # Ensure no chunk is empty
    assert all(len(c.strip()) > 0 for c in chunks)
