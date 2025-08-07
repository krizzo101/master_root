"""
SQLite Datastore for OPSVI-RAG

Implements local file-based storage using SQLite with FTS5 for hybrid search.
Supports vector embeddings, JSON metadata, and full-text search capabilities.
"""

import asyncio
import json
import logging
import uuid
from pathlib import Path
from typing import Any

import numpy as np
from pydantic import BaseModel, Field

try:
    import aiosqlite
except ImportError as e:
    raise ImportError("aiosqlite package required. Install with: pip install aiosqlite") from e

from ..base import BaseDatastore, Document, SearchFilter, SearchResult

logger = logging.getLogger(__name__)


class SQLiteConfig(BaseModel):
    """Configuration for SQLite datastore."""

    # Database settings
    database_path: str = Field(
        default="./rag_database.db", description="Path to SQLite database file"
    )
    connection_timeout: float = Field(
        default=30.0, description="Connection timeout in seconds"
    )
    max_connections: int = Field(
        default=10, description="Maximum number of connections in pool"
    )

    # Performance settings
    journal_mode: str = Field(
        default="WAL", description="Journal mode (WAL, DELETE, TRUNCATE)"
    )
    synchronous: str = Field(
        default="NORMAL", description="Synchronous mode (OFF, NORMAL, FULL)"
    )
    cache_size: int = Field(default=50000, description="Cache size in pages")
    temp_store: str = Field(default="memory", description="Temporary storage location")
    mmap_size: int = Field(
        default=268435456, description="Memory-mapped I/O size (256MB)"
    )
    page_size: int = Field(default=4096, description="Database page size")

    # Search settings
    fts_enabled: bool = Field(default=True, description="Enable full-text search")
    vector_search_enabled: bool = Field(
        default=True, description="Enable vector similarity search"
    )
    embedding_dimension: int = Field(
        default=1536, description="Expected embedding dimension"
    )
    similarity_threshold: float = Field(
        default=0.0, description="Minimum similarity threshold"
    )

    # Indexing settings
    create_indexes: bool = Field(default=True, description="Create performance indexes")
    auto_vacuum: str = Field(default="incremental", description="Auto vacuum mode")


class SQLiteVectorSearch:
    """Vector similarity search implementation for SQLite."""

    def __init__(self, conn: aiosqlite.Connection):
        self.conn = conn
        self._register_functions()

    def _register_functions(self):
        """Register custom SQLite functions for vector operations."""
        # Note: aiosqlite doesn't support create_function directly
        # These would need to be registered on the connection
        pass

    @staticmethod
    def cosine_similarity(a_bytes: bytes, b_bytes: bytes) -> float:
        """Calculate cosine similarity between two embedding vectors."""
        if not a_bytes or not b_bytes:
            return 0.0

        try:
            a = np.frombuffer(a_bytes, dtype=np.float32)
            b = np.frombuffer(b_bytes, dtype=np.float32)

            dot_product = np.dot(a, b)
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)

            if norm_a == 0 or norm_b == 0:
                return 0.0

            return float(dot_product / (norm_a * norm_b))
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0

    @staticmethod
    def euclidean_distance(a_bytes: bytes, b_bytes: bytes) -> float:
        """Calculate Euclidean distance between two embedding vectors."""
        if not a_bytes or not b_bytes:
            return float("inf")

        try:
            a = np.frombuffer(a_bytes, dtype=np.float32)
            b = np.frombuffer(b_bytes, dtype=np.float32)

            return float(np.linalg.norm(a - b))
        except Exception as e:
            logger.error(f"Error calculating Euclidean distance: {e}")
            return float("inf")


class SQLiteStore(BaseDatastore):
    """SQLite-based datastore with FTS5 and vector search capabilities."""

    def __init__(self, config: SQLiteConfig):
        super().__init__()
        self.config = config
        self.connection_pool: list[aiosqlite.Connection] = []
        self.pool_lock = asyncio.Lock()
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize SQLite database and connection pool."""
        if self._initialized:
            return

        try:
            # Create database directory if it doesn't exist
            db_path = Path(self.config.database_path)
            db_path.parent.mkdir(parents=True, exist_ok=True)

            # Initialize connection pool
            for _ in range(self.config.max_connections):
                conn = await aiosqlite.connect(
                    self.config.database_path, timeout=self.config.connection_timeout
                )
                conn.row_factory = aiosqlite.Row
                await self._configure_connection(conn)
                self.connection_pool.append(conn)

            # Setup database schema
            async with self._get_connection() as conn:
                await self._setup_schema(conn)
                await self._setup_indexes(conn)
                if self.config.vector_search_enabled:
                    await self._register_vector_functions(conn)

            self._initialized = True
            logger.info(f"SQLite store initialized: {self.config.database_path}")

        except Exception as e:
            logger.error(f"Failed to initialize SQLite store: {e}")
            raise

    async def _configure_connection(self, conn: aiosqlite.Connection) -> None:
        """Configure SQLite connection with performance optimizations."""
        pragmas = [
            f"PRAGMA journal_mode={self.config.journal_mode}",
            f"PRAGMA synchronous={self.config.synchronous}",
            f"PRAGMA cache_size={self.config.cache_size}",
            f"PRAGMA temp_store={self.config.temp_store}",
            f"PRAGMA mmap_size={self.config.mmap_size}",
            f"PRAGMA page_size={self.config.page_size}",
            f"PRAGMA auto_vacuum={self.config.auto_vacuum}",
            "PRAGMA foreign_keys=ON",
            "PRAGMA optimize",
        ]

        for pragma in pragmas:
            await conn.execute(pragma)
        await conn.commit()

    async def _get_connection(self):
        """Get a connection from the pool."""
        async with self.pool_lock:
            if self.connection_pool:
                return self.connection_pool.pop()
            else:
                # Create new connection if pool is empty
                conn = await aiosqlite.connect(
                    self.config.database_path, timeout=self.config.connection_timeout
                )
                conn.row_factory = aiosqlite.Row
                await self._configure_connection(conn)
                return conn

    async def _return_connection(self, conn: aiosqlite.Connection) -> None:
        """Return a connection to the pool."""
        async with self.pool_lock:
            if len(self.connection_pool) < self.config.max_connections:
                self.connection_pool.append(conn)
            else:
                await conn.close()

    async def _setup_schema(self, conn: aiosqlite.Connection) -> None:
        """Setup database schema."""
        schema_sql = """
        -- Main documents table
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            content TEXT NOT NULL,
            title TEXT,
            metadata JSONB,
            embeddings BLOB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Document statistics table
        CREATE TABLE IF NOT EXISTS document_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            total_documents INTEGER DEFAULT 0,
            total_size_bytes INTEGER DEFAULT 0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Search history table for analytics
        CREATE TABLE IF NOT EXISTS search_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            search_type TEXT NOT NULL,
            results_count INTEGER,
            execution_time_ms REAL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """

        # Create FTS5 virtual table if enabled
        if self.config.fts_enabled:
            fts_sql = """
            -- FTS5 virtual table for full-text search
            CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
                content,
                title,
                content='documents',
                content_rowid='rowid'
            );

            -- Triggers to keep FTS in sync
            CREATE TRIGGER IF NOT EXISTS documents_ai AFTER INSERT ON documents BEGIN
                INSERT INTO documents_fts(rowid, content, title)
                VALUES (NEW.rowid, NEW.content, COALESCE(NEW.title, ''));
            END;

            CREATE TRIGGER IF NOT EXISTS documents_ad AFTER DELETE ON documents BEGIN
                INSERT INTO documents_fts(documents_fts, rowid, content, title)
                VALUES('delete', OLD.rowid, OLD.content, COALESCE(OLD.title, ''));
            END;

            CREATE TRIGGER IF NOT EXISTS documents_au AFTER UPDATE ON documents BEGIN
                INSERT INTO documents_fts(documents_fts, rowid, content, title)
                VALUES('delete', OLD.rowid, OLD.content, COALESCE(OLD.title, ''));
                INSERT INTO documents_fts(rowid, content, title)
                VALUES (NEW.rowid, NEW.content, COALESCE(NEW.title, ''));
            END;
            """
            schema_sql += fts_sql

        await conn.executescript(schema_sql)
        await conn.commit()

    async def _setup_indexes(self, conn: aiosqlite.Connection) -> None:
        """Create performance indexes."""
        if not self.config.create_indexes:
            return

        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_documents_updated_at ON documents(updated_at)",
            "CREATE INDEX IF NOT EXISTS idx_search_history_timestamp ON search_history(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_search_history_query ON search_history(query)",
        ]

        for index_sql in indexes:
            try:
                await conn.execute(index_sql)
            except Exception as e:
                logger.warning(f"Failed to create index: {e}")

        await conn.commit()

    async def _register_vector_functions(self, conn: aiosqlite.Connection) -> None:
        """Register custom functions for vector operations."""
        # Note: This is a simplified approach. In practice, you might want to use
        # a more sophisticated vector search implementation or extensions
        try:
            await conn.create_function(
                "cosine_similarity", 2, SQLiteVectorSearch.cosine_similarity
            )
            await conn.create_function(
                "euclidean_distance", 2, SQLiteVectorSearch.euclidean_distance
            )
        except Exception as e:
            logger.warning(f"Failed to register vector functions: {e}")

    async def add_document(self, document: Document) -> str:
        """Add a document to the SQLite database."""
        if not self._initialized:
            await self.initialize()

        conn = await self._get_connection()
        try:
            doc_id = document.id or str(uuid.uuid4())

            # Prepare embedding data
            embedding_bytes = None
            if document.embedding:
                embedding_array = np.array(document.embedding, dtype=np.float32)
                embedding_bytes = embedding_array.tobytes()

            # Insert document
            await conn.execute(
                """
                INSERT OR REPLACE INTO documents
                (id, content, title, metadata, embeddings, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
                (
                    doc_id,
                    document.content,
                    document.metadata.get("title", ""),
                    json.dumps(document.metadata),
                    embedding_bytes,
                ),
            )

            await conn.commit()
            logger.debug(f"Added document {doc_id} to SQLite database")
            return doc_id

        except Exception as e:
            logger.error(f"Failed to add document: {e}")
            raise
        finally:
            await self._return_connection(conn)

    async def add_documents(self, documents: list[Document]) -> list[str]:
        """Add multiple documents efficiently."""
        if not self._initialized:
            await self.initialize()

        if not documents:
            return []

        conn = await self._get_connection()
        try:
            doc_ids = []
            document_data = []

            for doc in documents:
                doc_id = doc.id or str(uuid.uuid4())
                doc_ids.append(doc_id)

                # Prepare embedding data
                embedding_bytes = None
                if doc.embedding:
                    embedding_array = np.array(doc.embedding, dtype=np.float32)
                    embedding_bytes = embedding_array.tobytes()

                document_data.append(
                    (
                        doc_id,
                        doc.content,
                        doc.metadata.get("title", ""),
                        json.dumps(doc.metadata),
                        embedding_bytes,
                    )
                )

            # Batch insert
            await conn.executemany(
                """
                INSERT OR REPLACE INTO documents
                (id, content, title, metadata, embeddings, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
                document_data,
            )

            await conn.commit()
            logger.info(f"Added {len(documents)} documents to SQLite database")
            return doc_ids

        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            raise
        finally:
            await self._return_connection(conn)

    async def update_document(self, document_id: str, document: Document) -> None:
        """Update an existing document."""
        if not self._initialized:
            await self.initialize()

        conn = await self._get_connection()
        try:
            # Prepare embedding data
            embedding_bytes = None
            if document.embedding:
                embedding_array = np.array(document.embedding, dtype=np.float32)
                embedding_bytes = embedding_array.tobytes()

            await conn.execute(
                """
                UPDATE documents
                SET content = ?, title = ?, metadata = ?, embeddings = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """,
                (
                    document.content,
                    document.metadata.get("title", ""),
                    json.dumps(document.metadata),
                    embedding_bytes,
                    document_id,
                ),
            )

            await conn.commit()
            logger.debug(f"Updated document {document_id}")

        except Exception as e:
            logger.error(f"Failed to update document {document_id}: {e}")
            raise
        finally:
            await self._return_connection(conn)

    async def delete_document(self, document_id: str) -> None:
        """Delete a document from the database."""
        if not self._initialized:
            await self.initialize()

        conn = await self._get_connection()
        try:
            await conn.execute("DELETE FROM documents WHERE id = ?", (document_id,))
            await conn.commit()
            logger.debug(f"Deleted document {document_id}")

        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {e}")
            raise
        finally:
            await self._return_connection(conn)

    async def get_document(self, document_id: str) -> Document | None:
        """Retrieve a document by ID."""
        if not self._initialized:
            await self.initialize()

        conn = await self._get_connection()
        try:
            cursor = await conn.execute(
                """
                SELECT id, content, metadata, embeddings
                FROM documents
                WHERE id = ?
            """,
                (document_id,),
            )

            row = await cursor.fetchone()
            if row:
                metadata = json.loads(row["metadata"]) if row["metadata"] else {}

                # Restore embedding
                embedding = None
                if row["embeddings"]:
                    embedding = np.frombuffer(
                        row["embeddings"], dtype=np.float32
                    ).tolist()

                return Document(
                    id=row["id"],
                    content=row["content"],
                    metadata=metadata,
                    embedding=embedding,
                )

            return None

        except Exception as e:
            logger.error(f"Failed to get document {document_id}: {e}")
            raise
        finally:
            await self._return_connection(conn)

    async def search(
        self,
        query: str,
        query_embedding: list[float] | None = None,
        filters: SearchFilter | None = None,
        limit: int = 10,
        search_type: str = "hybrid",
    ) -> list[SearchResult]:
        """Search documents using various methods."""
        if not self._initialized:
            await self.initialize()

        start_time = asyncio.get_event_loop().time()

        try:
            if search_type == "fulltext" and self.config.fts_enabled:
                results = await self._fulltext_search(query, filters, limit)
            elif (
                search_type == "vector"
                and query_embedding
                and self.config.vector_search_enabled
            ):
                results = await self._vector_search(query_embedding, filters, limit)
            elif search_type == "hybrid" and query_embedding:
                results = await self._hybrid_search(
                    query, query_embedding, filters, limit
                )
            else:
                # Fallback to simple text search
                results = await self._simple_search(query, filters, limit)

            # Log search for analytics
            execution_time = (asyncio.get_event_loop().time() - start_time) * 1000
            await self._log_search(query, search_type, len(results), execution_time)

            return results

        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise

    async def _fulltext_search(
        self, query: str, filters: SearchFilter | None, limit: int
    ) -> list[SearchResult]:
        """Perform full-text search using FTS5."""
        conn = await self._get_connection()
        try:
            # Build FTS query
            fts_query = self._build_fts_query(query)

            cursor = await conn.execute(
                """
                SELECT
                    d.id,
                    d.content,
                    d.metadata,
                    d.embeddings,
                    snippet(documents_fts, 0, '<mark>', '</mark>', '...', 32) as snippet,
                    bm25(documents_fts) as rank
                FROM documents_fts
                JOIN documents d ON d.rowid = documents_fts.rowid
                WHERE documents_fts MATCH ?
                ORDER BY rank
                LIMIT ?
            """,
                (fts_query, limit),
            )

            results = []
            async for row in cursor:
                metadata = json.loads(row["metadata"]) if row["metadata"] else {}
                embedding = None
                if row["embeddings"]:
                    embedding = np.frombuffer(
                        row["embeddings"], dtype=np.float32
                    ).tolist()

                # Convert BM25 rank to similarity score
                score = max(0.0, min(1.0, 1.0 / (1.0 + abs(row["rank"]))))

                search_result = SearchResult(
                    document=Document(
                        id=row["id"],
                        content=row["content"],
                        metadata=metadata,
                        embedding=embedding,
                    ),
                    score=score,
                    metadata={
                        "search_type": "fulltext",
                        "snippet": row["snippet"],
                        "bm25_rank": row["rank"],
                        "query": query,
                    },
                )
                results.append(search_result)

            return results

        finally:
            await self._return_connection(conn)

    async def _vector_search(
        self, query_embedding: list[float], filters: SearchFilter | None, limit: int
    ) -> list[SearchResult]:
        """Perform vector similarity search."""
        conn = await self._get_connection()
        try:
            query_bytes = np.array(query_embedding, dtype=np.float32).tobytes()

            cursor = await conn.execute(
                """
                SELECT
                    id,
                    content,
                    metadata,
                    embeddings,
                    cosine_similarity(embeddings, ?) as similarity
                FROM documents
                WHERE embeddings IS NOT NULL
                  AND similarity > ?
                ORDER BY similarity DESC
                LIMIT ?
            """,
                (query_bytes, self.config.similarity_threshold, limit),
            )

            results = []
            async for row in cursor:
                metadata = json.loads(row["metadata"]) if row["metadata"] else {}
                embedding = None
                if row["embeddings"]:
                    embedding = np.frombuffer(
                        row["embeddings"], dtype=np.float32
                    ).tolist()

                search_result = SearchResult(
                    document=Document(
                        id=row["id"],
                        content=row["content"],
                        metadata=metadata,
                        embedding=embedding,
                    ),
                    score=row["similarity"],
                    metadata={"search_type": "vector", "similarity": row["similarity"]},
                )
                results.append(search_result)

            return results

        finally:
            await self._return_connection(conn)

    async def _hybrid_search(
        self,
        query: str,
        query_embedding: list[float],
        filters: SearchFilter | None,
        limit: int,
        text_weight: float = 0.5,
        vector_weight: float = 0.5,
    ) -> list[SearchResult]:
        """Perform hybrid search combining FTS and vector search."""
        # Get results from both search methods
        fts_results = await self._fulltext_search(query, filters, limit * 2)
        vector_results = await self._vector_search(query_embedding, filters, limit * 2)

        # Combine and re-rank results
        combined_scores = {}

        # Add FTS scores
        for result in fts_results:
            doc_id = result.document.id
            combined_scores[doc_id] = {
                "document": result.document,
                "text_score": result.score,
                "vector_score": 0.0,
                "metadata": result.metadata,
            }

        # Add vector scores
        for result in vector_results:
            doc_id = result.document.id
            if doc_id in combined_scores:
                combined_scores[doc_id]["vector_score"] = result.score
            else:
                combined_scores[doc_id] = {
                    "document": result.document,
                    "text_score": 0.0,
                    "vector_score": result.score,
                    "metadata": result.metadata,
                }

        # Calculate combined scores
        final_results = []
        for _doc_id, scores in combined_scores.items():
            combined_score = (
                text_weight * scores["text_score"]
                + vector_weight * scores["vector_score"]
            )

            metadata = scores["metadata"]
            metadata.update(
                {
                    "search_type": "hybrid",
                    "text_score": scores["text_score"],
                    "vector_score": scores["vector_score"],
                    "combined_score": combined_score,
                    "query": query,
                }
            )

            search_result = SearchResult(
                document=scores["document"], score=combined_score, metadata=metadata
            )
            final_results.append(search_result)

        # Sort by combined score and return top results
        final_results.sort(key=lambda x: x.score, reverse=True)
        return final_results[:limit]

    async def _simple_search(
        self, query: str, filters: SearchFilter | None, limit: int
    ) -> list[SearchResult]:
        """Perform simple LIKE-based text search."""
        conn = await self._get_connection()
        try:
            cursor = await conn.execute(
                """
                SELECT id, content, metadata, embeddings
                FROM documents
                WHERE content LIKE ?
                ORDER BY created_at DESC
                LIMIT ?
            """,
                (f"%{query}%", limit),
            )

            results = []
            async for row in cursor:
                metadata = json.loads(row["metadata"]) if row["metadata"] else {}
                embedding = None
                if row["embeddings"]:
                    embedding = np.frombuffer(
                        row["embeddings"], dtype=np.float32
                    ).tolist()

                # Simple relevance scoring based on query occurrence
                content_lower = row["content"].lower()
                query_lower = query.lower()
                score = content_lower.count(query_lower) / max(len(content_lower), 1)
                score = min(1.0, score * 100)  # Normalize and cap at 1.0

                search_result = SearchResult(
                    document=Document(
                        id=row["id"],
                        content=row["content"],
                        metadata=metadata,
                        embedding=embedding,
                    ),
                    score=score,
                    metadata={"search_type": "simple", "query": query},
                )
                results.append(search_result)

            return results

        finally:
            await self._return_connection(conn)

    def _build_fts_query(self, query: str) -> str:
        """Build FTS5 query from user query."""
        # Simple query building - can be enhanced with more sophisticated parsing
        # Handle phrase queries, AND/OR operators, etc.
        query = query.strip()

        # If query contains quotes, treat as phrase search
        if '"' in query:
            return query

        # Split into terms and create OR query
        terms = query.split()
        if len(terms) > 1:
            return " OR ".join(f'"{term}"' for term in terms)

        return f'"{query}"'

    async def _log_search(
        self, query: str, search_type: str, results_count: int, execution_time_ms: float
    ) -> None:
        """Log search for analytics."""
        conn = await self._get_connection()
        try:
            await conn.execute(
                """
                INSERT INTO search_history (query, search_type, results_count, execution_time_ms)
                VALUES (?, ?, ?, ?)
            """,
                (query, search_type, results_count, execution_time_ms),
            )
            await conn.commit()
        except Exception as e:
            logger.warning(f"Failed to log search: {e}")
        finally:
            await self._return_connection(conn)

    async def count_documents(self, filters: SearchFilter | None = None) -> int:
        """Count documents matching filters."""
        if not self._initialized:
            await self.initialize()

        conn = await self._get_connection()
        try:
            cursor = await conn.execute("SELECT COUNT(*) as count FROM documents")
            row = await cursor.fetchone()
            return row["count"] if row else 0
        finally:
            await self._return_connection(conn)

    async def list_documents(
        self, offset: int = 0, limit: int = 100, filters: SearchFilter | None = None
    ) -> list[Document]:
        """List documents with pagination."""
        if not self._initialized:
            await self.initialize()

        conn = await self._get_connection()
        try:
            cursor = await conn.execute(
                """
                SELECT id, content, metadata, embeddings
                FROM documents
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """,
                (limit, offset),
            )

            documents = []
            async for row in cursor:
                metadata = json.loads(row["metadata"]) if row["metadata"] else {}
                embedding = None
                if row["embeddings"]:
                    embedding = np.frombuffer(
                        row["embeddings"], dtype=np.float32
                    ).tolist()

                documents.append(
                    Document(
                        id=row["id"],
                        content=row["content"],
                        metadata=metadata,
                        embedding=embedding,
                    )
                )

            return documents

        finally:
            await self._return_connection(conn)

    async def get_database_stats(self) -> dict[str, Any]:
        """Get database statistics."""
        if not self._initialized:
            await self.initialize()

        conn = await self._get_connection()
        try:
            # Document count
            cursor = await conn.execute("SELECT COUNT(*) as count FROM documents")
            doc_count = (await cursor.fetchone())["count"]

            # Database size
            cursor = await conn.execute(
                "SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()"
            )
            db_size = (await cursor.fetchone())["size"]

            # Search statistics
            cursor = await conn.execute(
                """
                SELECT
                    COUNT(*) as total_searches,
                    AVG(execution_time_ms) as avg_execution_time,
                    MAX(execution_time_ms) as max_execution_time
                FROM search_history
                WHERE timestamp > datetime('now', '-24 hours')
            """
            )
            search_stats = await cursor.fetchone()

            return {
                "document_count": doc_count,
                "database_size_bytes": db_size,
                "total_searches_24h": search_stats["total_searches"] or 0,
                "avg_execution_time_ms": search_stats["avg_execution_time"] or 0,
                "max_execution_time_ms": search_stats["max_execution_time"] or 0,
                "fts_enabled": self.config.fts_enabled,
                "vector_search_enabled": self.config.vector_search_enabled,
            }

        finally:
            await self._return_connection(conn)

    async def optimize_database(self) -> None:
        """Optimize database performance."""
        if not self._initialized:
            await self.initialize()

        conn = await self._get_connection()
        try:
            # Run SQLite optimization
            await conn.execute("PRAGMA optimize")

            # Rebuild FTS index if enabled
            if self.config.fts_enabled:
                await conn.execute(
                    "INSERT INTO documents_fts(documents_fts) VALUES('rebuild')"
                )

            # Vacuum if needed
            cursor = await conn.execute("PRAGMA freelist_count")
            free_pages = (await cursor.fetchone())[0]
            if free_pages > 1000:  # If more than 1000 free pages
                await conn.execute("PRAGMA incremental_vacuum")

            await conn.commit()
            logger.info("Database optimization completed")

        finally:
            await self._return_connection(conn)

    async def close(self) -> None:
        """Close all connections in the pool."""
        async with self.pool_lock:
            for conn in self.connection_pool:
                await conn.close()
            self.connection_pool.clear()

        self._initialized = False
        logger.info("SQLite store closed")
