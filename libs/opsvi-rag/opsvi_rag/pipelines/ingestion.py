"""
Document ingestion pipeline implementation.

Provides end-to-end document ingestion with processing, embedding,
and storage in vector databases.
"""

from __future__ import annotations

from opsvi_foundation import get_logger
from pydantic import Field

from ..embeddings import BaseEmbeddingProvider
from ..storage import BaseVectorStore, Document
from .base import (
    BaseRAGPipeline,
    PipelineConfig,
    PipelineResult,
    PipelineStage,
)


class IngestionConfig(PipelineConfig):
    """Configuration for document ingestion pipeline."""

    pipeline_name: str = Field(
        default="document_ingestion", description="Pipeline name"
    )

    # Processing settings
    chunk_size: int = Field(
        default=1000, description="Document chunk size in characters"
    )
    chunk_overlap: int = Field(default=200, description="Overlap between chunks")
    max_chunks_per_document: int = Field(
        default=100, description="Maximum chunks per document"
    )

    # Embedding settings
    batch_size: int = Field(
        default=50, description="Batch size for embedding generation"
    )

    # Storage settings
    overwrite_existing: bool = Field(
        default=False, description="Overwrite existing documents"
    )

    class Config:
        extra = "allow"


class IngestionPipeline(BaseRAGPipeline):
    """
    Document ingestion pipeline implementation.

    Provides end-to-end document ingestion with processing, embedding,
    and storage in vector databases.
    """

    def __init__(
        self,
        config: IngestionConfig,
        embedding_provider: BaseEmbeddingProvider,
        vector_store: BaseVectorStore,
        **kwargs,
    ):
        """Initialize the ingestion pipeline."""
        super().__init__(config, **kwargs)
        self.config = config
        self.embedding_provider = embedding_provider
        self.vector_store = vector_store
        self.logger = get_logger(__name__)

    async def execute(self, documents: list[Document], **kwargs) -> PipelineResult:
        """
        Execute the document ingestion pipeline.

        Args:
            documents: List of documents to ingest
            **kwargs: Additional pipeline arguments

        Returns:
            Pipeline execution result

        Raises:
            PipelineError: If ingestion fails
        """
        try:
            self._start_pipeline()

            # Stage 1: Validation
            self._set_stage(PipelineStage.VALIDATION)
            validated_docs = await self._validate_documents(documents)
            self._add_stage_result(
                "validation", {"validated_count": len(validated_docs)}
            )

            # Stage 2: Processing
            self._set_stage(PipelineStage.PROCESSING)
            processed_docs = await self._process_documents(validated_docs)
            self._add_stage_result(
                "processing", {"processed_count": len(processed_docs)}
            )

            # Stage 3: Embedding generation
            self._set_stage(PipelineStage.PROCESSING)
            embedded_docs = await self._generate_embeddings(processed_docs)
            self._add_stage_result("embedding", {"embedded_count": len(embedded_docs)})

            # Stage 4: Storage
            self._set_stage(PipelineStage.STORAGE)
            stored_ids = await self._store_documents(embedded_docs)
            self._add_stage_result(
                "storage", {"stored_count": len(stored_ids), "stored_ids": stored_ids}
            )

            return self._end_pipeline(True)

        except Exception as e:
            error_msg = f"Ingestion pipeline failed: {e}"
            self.logger.error(error_msg)
            return self._end_pipeline(False, error_msg)

    async def _validate_documents(self, documents: list[Document]) -> list[Document]:
        """Validate documents before processing."""
        validated = []

        for doc in documents:
            # Basic validation
            if not doc.content or not doc.content.strip():
                self.logger.warning(f"Skipping document {doc.id}: empty content")
                continue

            if len(doc.content) < 10:  # Minimum content length
                self.logger.warning(f"Skipping document {doc.id}: content too short")
                continue

            validated.append(doc)

        self.logger.info(
            f"Validated {len(validated)} out of {len(documents)} documents"
        )
        return validated

    async def _process_documents(self, documents: list[Document]) -> list[Document]:
        """Process documents (chunking, cleaning, etc.)."""
        processed = []

        for doc in documents:
            # Simple text cleaning
            cleaned_content = self._clean_text(doc.content)

            # Chunk the document
            chunks = self._chunk_text(cleaned_content)

            # Create chunk documents
            for i, chunk in enumerate(chunks):
                chunk_doc = Document(
                    content=chunk,
                    metadata=doc.metadata.copy(),
                )
                chunk_doc.metadata.custom_fields["chunk_index"] = i
                chunk_doc.metadata.custom_fields["total_chunks"] = len(chunks)
                chunk_doc.metadata.custom_fields["original_document_id"] = doc.id

                processed.append(chunk_doc)

        self.logger.info(
            f"Processed {len(documents)} documents into {len(processed)} chunks"
        )
        return processed

    async def _generate_embeddings(self, documents: list[Document]) -> list[Document]:
        """Generate embeddings for documents."""
        embedded = []

        # Process in batches
        for i in range(0, len(documents), self.config.batch_size):
            batch = documents[i : i + self.config.batch_size]

            # Extract text content
            texts = [doc.content for doc in batch]

            # Generate embeddings
            embeddings = await self.embedding_provider.embed_texts(texts)

            # Add embeddings to documents
            for doc, embedding in zip(batch, embeddings, strict=False):
                doc.embedding = embedding
                embedded.append(doc)

        self.logger.info(f"Generated embeddings for {len(embedded)} documents")
        return embedded

    async def _store_documents(self, documents: list[Document]) -> list[str]:
        """Store documents in the vector store."""
        if not documents:
            return []

        # Store documents
        stored_ids = await self.vector_store.add_documents(documents)

        self.logger.info(f"Stored {len(stored_ids)} documents in vector store")
        return stored_ids

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        # Remove extra whitespace
        text = " ".join(text.split())

        # Basic text cleaning (can be extended)
        return text.strip()

    def _chunk_text(self, text: str) -> list[str]:
        """Chunk text into smaller pieces."""
        if len(text) <= self.config.chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + self.config.chunk_size

            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings
                for i in range(end, max(start, end - 100), -1):
                    if text[i] in ".!?":
                        end = i + 1
                        break

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            # Move start position with overlap
            start = end - self.config.chunk_overlap
            if start >= len(text):
                break

        # Limit number of chunks per document
        if len(chunks) > self.config.max_chunks_per_document:
            chunks = chunks[: self.config.max_chunks_per_document]
            self.logger.warning(
                f"Limited document to {self.config.max_chunks_per_document} chunks"
            )

        return chunks

    async def health_check(self) -> bool:
        """Perform a health check on the ingestion pipeline."""
        try:
            # Check embedding provider
            if not await self.embedding_provider.health_check():
                return False

            # Check vector store
            if not await self.vector_store.health_check():
                return False

            return True
        except Exception as e:
            self.logger.warning(f"Ingestion pipeline health check failed: {e}")
            return False
