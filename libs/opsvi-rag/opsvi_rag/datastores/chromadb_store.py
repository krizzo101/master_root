"""
ChromaDB Vector Store for OPSVI-RAG

Implements vector-based storage and retrieval using ChromaDB.
Supports multiple embedding functions, hybrid search, and advanced querying.
"""

import json
import logging
import uuid
from typing import Any

from pydantic import BaseModel, Field

try:
    import chromadb
    from chromadb.config import Settings
    from chromadb.utils.embedding_functions import (
        CohereEmbeddingFunction,
        HuggingFaceEmbeddingFunction,
        OpenAIEmbeddingFunction,
        SentenceTransformerEmbeddingFunction,
    )
except ImportError as e:
    raise ImportError("chromadb package required. Install with: pip install chromadb") from e

from ..base import BaseDatastore, Document, SearchFilter, SearchResult

logger = logging.getLogger(__name__)


class ChromaDBConfig(BaseModel):
    """Configuration for ChromaDB connection."""

    # Connection settings
    client_type: str = Field(
        default="persistent", description="Client type: persistent, http, or ephemeral"
    )
    persist_directory: str | None = Field(
        default="./chroma_db", description="Directory for persistent storage"
    )
    host: str | None = Field(default="localhost", description="Host for HTTP client")
    port: int | None = Field(default=8000, description="Port for HTTP client")
    ssl: bool = Field(default=False, description="Use SSL for HTTP client")
    headers: dict[str, str] | None = Field(
        default=None, description="Headers for HTTP client"
    )

    # Collection settings
    collection_name: str = Field(
        default="opsvi_documents", description="ChromaDB collection name"
    )

    # Embedding settings
    embedding_function_type: str = Field(
        default="sentence_transformer", description="Type of embedding function"
    )
    embedding_model: str = Field(
        default="all-MiniLM-L6-v2", description="Embedding model name"
    )
    api_key: str | None = Field(
        default=None, description="API key for hosted embedding services"
    )

    # Search settings
    similarity_metric: str = Field(default="cosine", description="Similarity metric")
    max_results: int = Field(default=100, description="Maximum results per query")

    # Advanced settings
    hnsw_space: str = Field(default="cosine", description="HNSW space for vector index")
    hnsw_construction_ef: int = Field(
        default=200, description="HNSW construction ef parameter"
    )
    hnsw_m: int = Field(default=16, description="HNSW M parameter")


class ChromaDBStore(BaseDatastore):
    """ChromaDB-based vector store for RAG applications."""

    def __init__(self, config: ChromaDBConfig):
        super().__init__()
        self.config = config
        self.client: chromadb.Client | None = None
        self.collection: chromadb.Collection | None = None
        self.embedding_function = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize ChromaDB client and collection."""
        if self._initialized:
            return

        try:
            # Create client based on type
            if self.config.client_type == "persistent":
                settings = Settings(
                    persist_directory=self.config.persist_directory,
                    chroma_db_impl="duckdb+parquet",
                )
                self.client = chromadb.PersistentClient(
                    path=self.config.persist_directory, settings=settings
                )
            elif self.config.client_type == "http":
                self.client = chromadb.HttpClient(
                    host=self.config.host,
                    port=self.config.port,
                    ssl=self.config.ssl,
                    headers=self.config.headers or {},
                )
            elif self.config.client_type == "ephemeral":
                self.client = chromadb.EphemeralClient()
            else:
                raise ValueError(f"Unknown client type: {self.config.client_type}")

            # Setup embedding function
            self._setup_embedding_function()

            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=self.config.collection_name,
                embedding_function=self.embedding_function,
                metadata={
                    "hnsw:space": self.config.hnsw_space,
                    "hnsw:construction_ef": self.config.hnsw_construction_ef,
                    "hnsw:M": self.config.hnsw_m,
                },
            )

            self._initialized = True
            logger.info(
                f"ChromaDB store initialized with collection: {self.config.collection_name}"
            )

        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB store: {e}")
            raise

    def _setup_embedding_function(self) -> None:
        """Setup the embedding function based on configuration."""
        if self.config.embedding_function_type == "openai":
            if not self.config.api_key:
                raise ValueError("OpenAI API key required for OpenAI embeddings")
            self.embedding_function = OpenAIEmbeddingFunction(
                api_key=self.config.api_key, model_name=self.config.embedding_model
            )
        elif self.config.embedding_function_type == "sentence_transformer":
            self.embedding_function = SentenceTransformerEmbeddingFunction(
                model_name=self.config.embedding_model
            )
        elif self.config.embedding_function_type == "cohere":
            if not self.config.api_key:
                raise ValueError("Cohere API key required for Cohere embeddings")
            self.embedding_function = CohereEmbeddingFunction(
                api_key=self.config.api_key, model_name=self.config.embedding_model
            )
        elif self.config.embedding_function_type == "huggingface":
            if not self.config.api_key:
                raise ValueError(
                    "HuggingFace API key required for HuggingFace embeddings"
                )
            self.embedding_function = HuggingFaceEmbeddingFunction(
                api_key=self.config.api_key, model_name=self.config.embedding_model
            )
        else:
            # Default to sentence transformers
            self.embedding_function = SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )

    async def add_document(self, document: Document) -> str:
        """Add a document to the ChromaDB collection."""
        if not self._initialized:
            await self.initialize()

        try:
            # Generate ID if not provided
            doc_id = document.id or str(uuid.uuid4())

            # Prepare metadata (ChromaDB requires string values for metadata)
            metadata = self._prepare_metadata(document.metadata)

            # Add to collection
            self.collection.add(
                documents=[document.content],
                metadatas=[metadata],
                ids=[doc_id],
                embeddings=[document.embedding] if document.embedding else None,
            )

            logger.debug(f"Added document {doc_id} to ChromaDB collection")
            return doc_id

        except Exception as e:
            logger.error(f"Failed to add document: {e}")
            raise

    async def add_documents(self, documents: list[Document]) -> list[str]:
        """Add multiple documents to the collection efficiently."""
        if not self._initialized:
            await self.initialize()

        if not documents:
            return []

        try:
            # Prepare batch data
            doc_ids = [doc.id or str(uuid.uuid4()) for doc in documents]
            contents = [doc.content for doc in documents]
            metadatas = [self._prepare_metadata(doc.metadata) for doc in documents]
            embeddings = [doc.embedding for doc in documents if doc.embedding]

            # Add batch to collection
            self.collection.add(
                documents=contents,
                metadatas=metadatas,
                ids=doc_ids,
                embeddings=embeddings if embeddings else None,
            )

            logger.info(f"Added {len(documents)} documents to ChromaDB collection")
            return doc_ids

        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            raise

    def _prepare_metadata(
        self, metadata: dict[str, Any]
    ) -> dict[str, str | int | float | bool]:
        """Prepare metadata for ChromaDB (convert complex types to strings)."""
        prepared = {}
        for key, value in metadata.items():
            if isinstance(value, str | int | float | bool):
                prepared[key] = value
            elif isinstance(value, list | dict):
                prepared[key] = json.dumps(value)
            else:
                prepared[key] = str(value)
        return prepared

    def _restore_metadata(self, metadata: dict[str, Any]) -> dict[str, Any]:
        """Restore metadata from ChromaDB format."""
        restored = {}
        for key, value in metadata.items():
            if isinstance(value, str) and (
                value.startswith("[") or value.startswith("{")
            ):
                try:
                    restored[key] = json.loads(value)
                except json.JSONDecodeError:
                    restored[key] = value
            else:
                restored[key] = value
        return restored

    async def update_document(self, document_id: str, document: Document) -> None:
        """Update an existing document."""
        if not self._initialized:
            await self.initialize()

        try:
            # ChromaDB doesn't have direct update, so we delete and re-add
            await self.delete_document(document_id)

            # Create new document with same ID
            document.id = document_id
            await self.add_document(document)

            logger.debug(f"Updated document {document_id}")

        except Exception as e:
            logger.error(f"Failed to update document {document_id}: {e}")
            raise

    async def delete_document(self, document_id: str) -> None:
        """Delete a document from the collection."""
        if not self._initialized:
            await self.initialize()

        try:
            self.collection.delete(ids=[document_id])
            logger.debug(f"Deleted document {document_id}")

        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {e}")
            raise

    async def get_document(self, document_id: str) -> Document | None:
        """Retrieve a document by ID."""
        if not self._initialized:
            await self.initialize()

        try:
            results = self.collection.get(
                ids=[document_id], include=["documents", "metadatas", "embeddings"]
            )

            if results["ids"]:
                metadata = self._restore_metadata(results["metadatas"][0])
                embedding = results["embeddings"][0] if results["embeddings"] else None

                return Document(
                    id=results["ids"][0],
                    content=results["documents"][0],
                    metadata=metadata,
                    embedding=embedding,
                )

            return None

        except Exception as e:
            logger.error(f"Failed to get document {document_id}: {e}")
            raise

    async def search(
        self,
        query: str,
        query_embedding: list[float] | None = None,
        filters: SearchFilter | None = None,
        limit: int = 10,
        search_type: str = "semantic",
    ) -> list[SearchResult]:
        """Search documents in the collection."""
        if not self._initialized:
            await self.initialize()

        try:
            # Prepare query parameters
            where_clause = None
            where_document_clause = None

            if filters:
                where_clause = self._build_where_clause(filters)
                if filters.content_filter:
                    where_document_clause = {"$contains": filters.content_filter}

            # Perform search based on type
            if search_type == "semantic" or (
                search_type == "hybrid" and not query_embedding
            ):
                # Use query text for semantic search
                results = self.collection.query(
                    query_texts=[query],
                    n_results=min(limit, self.config.max_results),
                    where=where_clause,
                    where_document=where_document_clause,
                    include=["documents", "metadatas", "distances", "embeddings"],
                )
            elif search_type == "vector" and query_embedding:
                # Use query embedding for vector search
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=min(limit, self.config.max_results),
                    where=where_clause,
                    where_document=where_document_clause,
                    include=["documents", "metadatas", "distances", "embeddings"],
                )
            elif search_type == "hybrid" and query_embedding:
                # Combine semantic and vector search
                return await self._hybrid_search(query, query_embedding, filters, limit)
            else:
                # Fallback to semantic search
                results = self.collection.query(
                    query_texts=[query],
                    n_results=min(limit, self.config.max_results),
                    where=where_clause,
                    where_document=where_document_clause,
                    include=["documents", "metadatas", "distances", "embeddings"],
                )

            # Convert to SearchResult objects
            search_results = []
            for i in range(len(results["ids"][0])):
                metadata = self._restore_metadata(results["metadatas"][0][i])
                embedding = (
                    results["embeddings"][0][i] if results["embeddings"] else None
                )

                # Convert distance to similarity score (ChromaDB returns distances)
                distance = results["distances"][0][i]
                score = 1.0 / (1.0 + distance) if distance >= 0 else 1.0

                search_result = SearchResult(
                    document=Document(
                        id=results["ids"][0][i],
                        content=results["documents"][0][i],
                        metadata=metadata,
                        embedding=embedding,
                    ),
                    score=score,
                    metadata={
                        "search_type": search_type,
                        "distance": distance,
                        "query": query,
                    },
                )
                search_results.append(search_result)

            return search_results

        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise

    async def _hybrid_search(
        self,
        query: str,
        query_embedding: list[float],
        filters: SearchFilter | None,
        limit: int,
        text_weight: float = 0.5,
        vector_weight: float = 0.5,
    ) -> list[SearchResult]:
        """Perform hybrid search combining text and vector search."""
        # Get results from both search types
        text_results = await self.search(query, None, filters, limit * 2, "semantic")
        vector_results = await self.search(
            None, query_embedding, filters, limit * 2, "vector"
        )

        # Combine results with weighted scoring
        combined_scores = {}

        # Add text search scores
        for result in text_results:
            doc_id = result.document.id
            combined_scores[doc_id] = {
                "document": result.document,
                "text_score": result.score,
                "vector_score": 0.0,
            }

        # Add vector search scores
        for result in vector_results:
            doc_id = result.document.id
            if doc_id in combined_scores:
                combined_scores[doc_id]["vector_score"] = result.score
            else:
                combined_scores[doc_id] = {
                    "document": result.document,
                    "text_score": 0.0,
                    "vector_score": result.score,
                }

        # Calculate combined scores and create final results
        final_results = []
        for _doc_id, scores in combined_scores.items():
            combined_score = (
                text_weight * scores["text_score"]
                + vector_weight * scores["vector_score"]
            )

            search_result = SearchResult(
                document=scores["document"],
                score=combined_score,
                metadata={
                    "search_type": "hybrid",
                    "text_score": scores["text_score"],
                    "vector_score": scores["vector_score"],
                    "query": query,
                },
            )
            final_results.append(search_result)

        # Sort by combined score and return top results
        final_results.sort(key=lambda x: x.score, reverse=True)
        return final_results[:limit]

    def _build_where_clause(self, filters: SearchFilter) -> dict[str, Any] | None:
        """Build ChromaDB where clause from SearchFilter."""
        if not filters.metadata:
            return None

        where_clause = {}
        for key, value in filters.metadata.items():
            if isinstance(value, dict):
                # Handle operators like {"$gte": 2023}
                where_clause[key] = value
            elif isinstance(value, list):
                # Handle list values with $in operator
                where_clause[key] = {"$in": value}
            else:
                # Simple equality
                where_clause[key] = {"$eq": value}

        return where_clause

    async def count_documents(self, filters: SearchFilter | None = None) -> int:
        """Count documents matching filters."""
        if not self._initialized:
            await self.initialize()

        try:
            where_clause = None
            if filters:
                where_clause = self._build_where_clause(filters)

            # ChromaDB doesn't have a direct count method, so we query and count
            results = self.collection.get(where=where_clause, include=["documents"])

            return len(results["ids"])

        except Exception as e:
            logger.error(f"Failed to count documents: {e}")
            return 0

    async def list_documents(
        self, offset: int = 0, limit: int = 100, filters: SearchFilter | None = None
    ) -> list[Document]:
        """List documents with pagination."""
        if not self._initialized:
            await self.initialize()

        try:
            where_clause = None
            if filters:
                where_clause = self._build_where_clause(filters)

            # Get all matching documents (ChromaDB doesn't support offset/limit directly)
            results = self.collection.get(
                where=where_clause, include=["documents", "metadatas", "embeddings"]
            )

            # Apply manual pagination
            start_idx = offset
            end_idx = min(offset + limit, len(results["ids"]))

            documents = []
            for i in range(start_idx, end_idx):
                if i < len(results["ids"]):
                    metadata = self._restore_metadata(results["metadatas"][i])
                    embedding = (
                        results["embeddings"][i] if results["embeddings"] else None
                    )

                    documents.append(
                        Document(
                            id=results["ids"][i],
                            content=results["documents"][i],
                            metadata=metadata,
                            embedding=embedding,
                        )
                    )

            return documents

        except Exception as e:
            logger.error(f"Failed to list documents: {e}")
            return []

    async def similarity_search(
        self, query_embedding: list[float], limit: int = 10, threshold: float = 0.0
    ) -> list[SearchResult]:
        """Perform pure vector similarity search."""
        if not self._initialized:
            await self.initialize()

        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=min(limit, self.config.max_results),
                include=["documents", "metadatas", "distances", "embeddings"],
            )

            search_results = []
            for i in range(len(results["ids"][0])):
                distance = results["distances"][0][i]
                score = 1.0 / (1.0 + distance) if distance >= 0 else 1.0

                # Apply threshold filter
                if score >= threshold:
                    metadata = self._restore_metadata(results["metadatas"][0][i])
                    embedding = (
                        results["embeddings"][0][i] if results["embeddings"] else None
                    )

                    search_result = SearchResult(
                        document=Document(
                            id=results["ids"][0][i],
                            content=results["documents"][0][i],
                            metadata=metadata,
                            embedding=embedding,
                        ),
                        score=score,
                        metadata={
                            "search_type": "similarity",
                            "distance": distance,
                            "threshold": threshold,
                        },
                    )
                    search_results.append(search_result)

            return search_results

        except Exception as e:
            logger.error(f"Similarity search failed: {e}")
            raise

    async def get_collection_info(self) -> dict[str, Any]:
        """Get information about the collection."""
        if not self._initialized:
            await self.initialize()

        try:
            count = self.collection.count()

            return {
                "name": self.config.collection_name,
                "count": count,
                "embedding_function": self.config.embedding_function_type,
                "embedding_model": self.config.embedding_model,
                "similarity_metric": self.config.similarity_metric,
            }

        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            return {}

    async def reset_collection(self) -> None:
        """Reset (delete all documents from) the collection."""
        if not self._initialized:
            await self.initialize()

        try:
            # Delete the collection and recreate it
            self.client.delete_collection(name=self.config.collection_name)

            self.collection = self.client.create_collection(
                name=self.config.collection_name,
                embedding_function=self.embedding_function,
                metadata={
                    "hnsw:space": self.config.hnsw_space,
                    "hnsw:construction_ef": self.config.hnsw_construction_ef,
                    "hnsw:M": self.config.hnsw_m,
                },
            )

            logger.info(f"Reset collection: {self.config.collection_name}")

        except Exception as e:
            logger.error(f"Failed to reset collection: {e}")
            raise

    async def close(self) -> None:
        """Close the ChromaDB connection."""
        # ChromaDB doesn't require explicit connection closing for most clients
        self._initialized = False
        logger.info("ChromaDB store closed")
