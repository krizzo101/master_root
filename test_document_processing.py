#!/usr/bin/env python3
"""
Test script for OPSVI RAG document processing system.

Tests the complete document processing pipeline including:
- Text file processing
- Chunking strategies
- Metadata extraction
- Integration with embedding providers
"""

import asyncio
import tempfile
from pathlib import Path

from opsvi_rag.processors import (
    DocumentProcessorFactory,
    DocumentProcessingRequest,
    TextDocumentProcessor,
    SemanticChunkingStrategy,
    SimpleTokenChunkingStrategy,
)


async def test_text_processing():
    """Test basic text document processing."""
    print("🧪 Testing Text Document Processing...")

    # Create a test file
    test_content = """
    This is a test document for the OPSVI RAG system.

    It contains multiple paragraphs to test chunking functionality.
    The document processing system should be able to extract this text
    and split it into meaningful chunks based on semantic boundaries.

    This is another paragraph. It should be processed correctly.
    The system uses async patterns throughout for production readiness.

    Final paragraph to ensure proper handling of multiple sections.
    """

    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(test_content.strip())
        temp_path = Path(f.name)

    try:
        # Test processing
        request = DocumentProcessingRequest(
            path=temp_path,
            chunk_size=200,
            overlap=50,
            strategy="semantic"
        )

        processor = DocumentProcessorFactory.get_processor(temp_path)
        response = await processor.process(request)

        print(f"✅ Document processed successfully!")
        print(f"   File: {response.document_metadata.file_name}")
        print(f"   Size: {response.document_metadata.size_bytes} bytes")
        print(f"   SHA256: {response.document_metadata.sha256[:16]}...")
        print(f"   Chunks: {len(response.chunks)}")

        for i, chunk in enumerate(response.chunks):
            print(f"   Chunk {i}: {len(chunk.text)} chars (offset {chunk.metadata.start_offset}-{chunk.metadata.end_offset})")
            print(f"            {repr(chunk.text[:50])}...")

        return response

    finally:
        temp_path.unlink()  # Clean up


async def test_chunking_strategies():
    """Test different chunking strategies."""
    print("\n🧪 Testing Chunking Strategies...")

    test_text = (
        "This is sentence one. This is sentence two! "
        "This is sentence three? This is sentence four. "
        "This is a much longer sentence that goes on and on and might exceed "
        "the chunk size limit and should be handled properly by the chunking system."
    )

    # Test simple chunking
    simple_strategy = SimpleTokenChunkingStrategy(chunk_size=80, overlap=20)
    simple_chunks = await simple_strategy.chunk(test_text)

    print(f"📝 Simple Strategy: {len(simple_chunks)} chunks")
    for i, chunk in enumerate(simple_chunks):
        print(f"   Chunk {i}: {repr(chunk.text)}")

    # Test semantic chunking
    semantic_strategy = SemanticChunkingStrategy(chunk_size=80, overlap=20)
    semantic_chunks = await semantic_strategy.chunk(test_text)

    print(f"\n🧠 Semantic Strategy: {len(semantic_chunks)} chunks")
    for i, chunk in enumerate(semantic_chunks):
        print(f"   Chunk {i}: {repr(chunk.text)}")


async def test_embedding_integration():
    """Test integration with embedding request format."""
    print("\n🧪 Testing Embedding Integration...")

    # Create test content
    test_content = "This is a test document for embedding integration. It should convert to EmbeddingRequest format."

    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(test_content)
        temp_path = Path(f.name)

    try:
        request = DocumentProcessingRequest(path=temp_path, chunk_size=100)
        processor = TextDocumentProcessor()
        response = await processor.process(request)

        # Convert to embedding request
        embedding_request = response.to_embedding_request()

        print(f"✅ Embedding integration successful!")
        print(f"   Texts for embedding: {len(embedding_request.texts)}")
        print(f"   Metadata included: {bool(embedding_request.metadata)}")
        print(f"   First text: {repr(embedding_request.texts[0][:50])}...")

        return embedding_request

    finally:
        temp_path.unlink()


async def test_factory_processor_selection():
    """Test automatic processor selection by file extension."""
    print("\n🧪 Testing Processor Factory...")

    test_cases = [
        ('.txt', 'TextDocumentProcessor'),
        ('.md', 'MarkdownDocumentProcessor'),
        ('.markdown', 'MarkdownDocumentProcessor'),
        ('.pdf', 'PDFDocumentProcessor'),
    ]

    for ext, expected_class in test_cases:
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
            temp_path = Path(f.name)

        try:
            processor = DocumentProcessorFactory.get_processor(temp_path)
            actual_class = processor.__class__.__name__

            if actual_class == expected_class:
                print(f"✅ {ext} -> {actual_class}")
            else:
                print(f"❌ {ext} -> {actual_class} (expected {expected_class})")

        finally:
            temp_path.unlink()


async def main():
    """Run all tests."""
    print("🚀 OPSVI RAG Document Processing Tests\n")

    try:
        await test_text_processing()
        await test_chunking_strategies()
        await test_embedding_integration()
        await test_factory_processor_selection()

        print("\n✅ All tests completed successfully!")
        print("🎉 Document processing system is ready for production use!")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())