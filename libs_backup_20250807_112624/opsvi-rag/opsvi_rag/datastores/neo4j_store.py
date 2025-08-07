"""
Neo4j Graph Database Store for OPSVI-RAG

Implements graph-based storage and retrieval for RAG systems using Neo4j.
Supports GraphRAG patterns, knowledge graph construction, and hybrid search.
"""

import json
import logging
from typing import Any

from pydantic import BaseModel, Field

try:
    from neo4j import AsyncDriver, AsyncGraphDatabase, Driver
    from neo4j.exceptions import Neo4jError
except ImportError as e:
    raise ImportError("neo4j package required. Install with: pip install neo4j") from e

from ..base import BaseDatastore, Document, SearchFilter, SearchResult

logger = logging.getLogger(__name__)


class Neo4jConfig(BaseModel):
    """Configuration for Neo4j connection."""

    uri: str = Field(
        default="bolt://localhost:7687", description="Neo4j connection URI"
    )
    username: str = Field(default="neo4j", description="Neo4j username")
    password: str = Field(description="Neo4j password")
    database: str = Field(default="neo4j", description="Neo4j database name")
    max_connection_lifetime: int = Field(
        default=1800, description="Max connection lifetime in seconds"
    )
    max_connection_pool_size: int = Field(
        default=50, description="Max connection pool size"
    )
    encrypted: bool = Field(default=True, description="Use encrypted connection")
    trust: str = Field(
        default="TRUST_SYSTEM_CA_SIGNED_CERTIFICATES", description="Trust policy"
    )

    # Graph-specific settings
    vector_index_name: str = Field(
        default="document_embeddings", description="Vector index name"
    )
    text_index_name: str = Field(default="document_text", description="Text index name")
    embedding_dimension: int = Field(
        default=1536, description="Embedding vector dimension"
    )
    similarity_metric: str = Field(
        default="cosine", description="Similarity metric for vector search"
    )


class GraphRAGRetriever:
    """Advanced retrieval strategies for GraphRAG."""

    def __init__(self, driver: Driver | AsyncDriver):
        self.driver = driver

    async def vector_similarity_search(
        self,
        query_embedding: list[float],
        k: int = 10,
        index_name: str = "document_embeddings",
    ) -> list[dict[str, Any]]:
        """Perform vector similarity search."""
        async with self.driver.session() as session:
            result = await session.run(
                """
                CALL db.index.vector.queryNodes($index_name, $k, $query_embedding)
                YIELD node, score
                MATCH (node:Document)
                RETURN node.id as id,
                       node.content as content,
                       node.metadata as metadata,
                       score
                ORDER BY score DESC
            """,
                index_name=index_name,
                k=k,
                query_embedding=query_embedding,
            )

            return [dict(record) async for record in result]

    async def keyword_search(
        self, query: str, k: int = 10, index_name: str = "document_text"
    ) -> list[dict[str, Any]]:
        """Perform keyword-based search."""
        async with self.driver.session() as session:
            result = await session.run(
                """
                CALL db.index.fulltext.queryNodes($index_name, $query)
                YIELD node, score
                MATCH (node:Document)
                RETURN node.id as id,
                       node.content as content,
                       node.metadata as metadata,
                       score
                ORDER BY score DESC
                LIMIT $k
            """,
                index_name=index_name,
                query=query,
                k=k,
            )

            return [dict(record) async for record in result]

    async def hybrid_search(
        self,
        query: str,
        query_embedding: list[float],
        k: int = 10,
        text_weight: float = 0.5,
        vector_weight: float = 0.5,
    ) -> list[dict[str, Any]]:
        """Combine vector and text search with weighted scoring."""
        # Get results from both search methods
        vector_results = await self.vector_similarity_search(query_embedding, k * 2)
        keyword_results = await self.keyword_search(query, k * 2)

        # Combine and re-rank results
        combined_scores = {}

        # Add vector scores
        for result in vector_results:
            doc_id = result["id"]
            combined_scores[doc_id] = {
                "content": result["content"],
                "metadata": result["metadata"],
                "vector_score": result["score"],
                "text_score": 0.0,
            }

        # Add text scores
        for result in keyword_results:
            doc_id = result["id"]
            if doc_id in combined_scores:
                combined_scores[doc_id]["text_score"] = result["score"]
            else:
                combined_scores[doc_id] = {
                    "content": result["content"],
                    "metadata": result["metadata"],
                    "vector_score": 0.0,
                    "text_score": result["score"],
                }

        # Calculate combined scores
        final_results = []
        for doc_id, scores in combined_scores.items():
            combined_score = (
                vector_weight * scores["vector_score"]
                + text_weight * scores["text_score"]
            )
            final_results.append(
                {
                    "id": doc_id,
                    "content": scores["content"],
                    "metadata": scores["metadata"],
                    "score": combined_score,
                    "vector_score": scores["vector_score"],
                    "text_score": scores["text_score"],
                }
            )

        # Sort by combined score and return top k
        final_results.sort(key=lambda x: x["score"], reverse=True)
        return final_results[:k]

    async def graph_traversal_search(
        self,
        start_entities: list[str],
        relationship_types: list[str] | None = None,
        max_depth: int = 3,
        k: int = 10,
    ) -> list[dict[str, Any]]:
        """Perform graph traversal from starting entities."""
        rel_filter = ""
        if relationship_types:
            rel_types = "|".join(relationship_types)
            rel_filter = f":{rel_types}"

        async with self.driver.session() as session:
            result = await session.run(
                f"""
                MATCH (start:Entity)
                WHERE start.name IN $start_entities
                MATCH path = (start)-[{rel_filter}*1..{max_depth}]-(doc:Document)
                WITH doc, length(path) as path_length,
                     collect(DISTINCT [n IN nodes(path) WHERE n:Entity | n.name]) as entities
                RETURN doc.id as id,
                       doc.content as content,
                       doc.metadata as metadata,
                       path_length,
                       entities,
                       1.0 / path_length as relevance_score
                ORDER BY relevance_score DESC
                LIMIT $k
            """,
                start_entities=start_entities,
                k=k,
            )

            return [dict(record) async for record in result]

    async def community_search(
        self,
        query_embedding: list[float],
        community_algorithm: str = "louvain",
        k: int = 10,
    ) -> list[dict[str, Any]]:
        """Search within detected communities for better context."""
        async with self.driver.session() as session:
            # First, detect communities
            await session.run(
                f"""
                CALL gds.{community_algorithm}.write('document_graph', {{
                    writeProperty: 'community'
                }})
            """
            )

            # Then search within communities
            result = await session.run(
                """
                CALL db.index.vector.queryNodes($index_name, $k, $query_embedding)
                YIELD node, score
                MATCH (node:Document)
                MATCH (node)-[:RELATED_TO*1..2]-(related:Document)
                WHERE node.community = related.community
                WITH node, score, collect(DISTINCT related) as community_docs
                RETURN node.id as id,
                       node.content as content,
                       node.metadata as metadata,
                       score,
                       [doc IN community_docs | {id: doc.id, content: doc.content}] as context
                ORDER BY score DESC
                LIMIT $k
            """,
                index_name="document_embeddings",
                k=k,
                query_embedding=query_embedding,
            )

            return [dict(record) async for record in result]


class Neo4jStore(BaseDatastore):
    """Neo4j-based datastore for graph-enhanced RAG."""

    def __init__(self, config: Neo4jConfig):
        super().__init__()
        self.config = config
        self.driver: AsyncDriver | None = None
        self.retriever: GraphRAGRetriever | None = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize Neo4j connection and setup indexes."""
        if self._initialized:
            return

        try:
            self.driver = AsyncGraphDatabase.driver(
                self.config.uri,
                auth=(self.config.username, self.config.password),
                max_connection_lifetime=self.config.max_connection_lifetime,
                max_connection_pool_size=self.config.max_connection_pool_size,
                encrypted=self.config.encrypted,
                trust=self.config.trust,
            )

            # Verify connection
            await self.driver.verify_connectivity()

            # Setup retriever
            self.retriever = GraphRAGRetriever(self.driver)

            # Create indexes and constraints
            await self._setup_schema()

            self._initialized = True
            logger.info("Neo4j store initialized successfully")

        except Neo4jError as e:
            logger.error(f"Failed to initialize Neo4j store: {e}")
            raise

    async def _setup_schema(self) -> None:
        """Setup Neo4j schema, indexes, and constraints."""
        async with self.driver.session(database=self.config.database) as session:
            # Create constraints
            constraints = [
                "CREATE CONSTRAINT document_id IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE",
                "CREATE CONSTRAINT entity_name IF NOT EXISTS FOR (e:Entity) REQUIRE e.name IS UNIQUE",
                "CREATE CONSTRAINT concept_name IF NOT EXISTS FOR (c:Concept) REQUIRE c.name IS UNIQUE",
            ]

            for constraint in constraints:
                try:
                    await session.run(constraint)
                except Neo4jError as e:
                    if "already exists" not in str(e):
                        logger.warning(f"Failed to create constraint: {e}")

            # Create vector index for embeddings
            try:
                await session.run(
                    f"""
                    CREATE VECTOR INDEX {self.config.vector_index_name} IF NOT EXISTS
                    FOR (d:Document) ON (d.embedding)
                    OPTIONS {{
                        indexConfig: {{
                            `vector.dimensions`: {self.config.embedding_dimension},
                            `vector.similarity_function`: '{self.config.similarity_metric}'
                        }}
                    }}
                """
                )
            except Neo4jError as e:
                if "already exists" not in str(e):
                    logger.warning(f"Failed to create vector index: {e}")

            # Create full-text index
            try:
                await session.run(
                    f"""
                    CREATE FULLTEXT INDEX {self.config.text_index_name} IF NOT EXISTS
                    FOR (d:Document) ON EACH [d.content, d.title]
                """
                )
            except Neo4jError as e:
                if "already exists" not in str(e):
                    logger.warning(f"Failed to create fulltext index: {e}")

    async def add_document(self, document: Document) -> str:
        """Add a document to the graph database."""
        if not self._initialized:
            await self.initialize()

        async with self.driver.session(database=self.config.database) as session:
            # Create document node
            result = await session.run(
                """
                CREATE (d:Document {
                    id: $id,
                    content: $content,
                    title: $title,
                    metadata: $metadata,
                    embedding: $embedding,
                    created_at: datetime(),
                    updated_at: datetime()
                })
                RETURN d.id as id
            """,
                id=document.id,
                content=document.content,
                title=document.metadata.get("title", ""),
                metadata=json.dumps(document.metadata),
                embedding=document.embedding if document.embedding else [],
            )

            doc_id = await result.single()

            # Extract and create entities/concepts if metadata contains them
            if "entities" in document.metadata:
                await self._create_entities(
                    session, document.id, document.metadata["entities"]
                )

            if "concepts" in document.metadata:
                await self._create_concepts(
                    session, document.id, document.metadata["concepts"]
                )

            return doc_id["id"]

    async def _create_entities(
        self, session, doc_id: str, entities: list[dict[str, Any]]
    ) -> None:
        """Create entity nodes and relationships."""
        for entity in entities:
            await session.run(
                """
                MERGE (e:Entity {name: $name})
                ON CREATE SET e.type = $type, e.created_at = datetime()
                WITH e
                MATCH (d:Document {id: $doc_id})
                MERGE (d)-[:MENTIONS {confidence: $confidence}]->(e)
            """,
                name=entity.get("name"),
                type=entity.get("type", "UNKNOWN"),
                doc_id=doc_id,
                confidence=entity.get("confidence", 1.0),
            )

    async def _create_concepts(
        self, session, doc_id: str, concepts: list[dict[str, Any]]
    ) -> None:
        """Create concept nodes and relationships."""
        for concept in concepts:
            await session.run(
                """
                MERGE (c:Concept {name: $name})
                ON CREATE SET c.category = $category, c.created_at = datetime()
                WITH c
                MATCH (d:Document {id: $doc_id})
                MERGE (d)-[:RELATES_TO {relevance: $relevance}]->(c)
            """,
                name=concept.get("name"),
                category=concept.get("category", "GENERAL"),
                doc_id=doc_id,
                relevance=concept.get("relevance", 1.0),
            )

    async def update_document(self, document_id: str, document: Document) -> None:
        """Update an existing document."""
        if not self._initialized:
            await self.initialize()

        async with self.driver.session(database=self.config.database) as session:
            await session.run(
                """
                MATCH (d:Document {id: $doc_id})
                SET d.content = $content,
                    d.title = $title,
                    d.metadata = $metadata,
                    d.embedding = $embedding,
                    d.updated_at = datetime()
            """,
                doc_id=document_id,
                content=document.content,
                title=document.metadata.get("title", ""),
                metadata=json.dumps(document.metadata),
                embedding=document.embedding if document.embedding else [],
            )

    async def delete_document(self, document_id: str) -> None:
        """Delete a document and its relationships."""
        if not self._initialized:
            await self.initialize()

        async with self.driver.session(database=self.config.database) as session:
            await session.run(
                """
                MATCH (d:Document {id: $doc_id})
                DETACH DELETE d
            """,
                doc_id=document_id,
            )

    async def get_document(self, document_id: str) -> Document | None:
        """Retrieve a document by ID."""
        if not self._initialized:
            await self.initialize()

        async with self.driver.session(database=self.config.database) as session:
            result = await session.run(
                """
                MATCH (d:Document {id: $doc_id})
                RETURN d.id as id, d.content as content, d.metadata as metadata, d.embedding as embedding
            """,
                doc_id=document_id,
            )

            record = await result.single()
            if record:
                metadata = json.loads(record["metadata"]) if record["metadata"] else {}
                return Document(
                    id=record["id"],
                    content=record["content"],
                    metadata=metadata,
                    embedding=record["embedding"],
                )
            return None

    async def search(
        self,
        query: str,
        query_embedding: list[float] | None = None,
        filters: SearchFilter | None = None,
        limit: int = 10,
        search_type: str = "hybrid",
    ) -> list[SearchResult]:
        """Search documents using various GraphRAG strategies."""
        if not self._initialized:
            await self.initialize()

        results = []

        try:
            if search_type == "vector" and query_embedding:
                raw_results = await self.retriever.vector_similarity_search(
                    query_embedding, k=limit
                )
            elif search_type == "keyword":
                raw_results = await self.retriever.keyword_search(query, k=limit)
            elif search_type == "hybrid" and query_embedding:
                raw_results = await self.retriever.hybrid_search(
                    query, query_embedding, k=limit
                )
            elif (
                search_type == "graph_traversal"
                and filters
                and filters.metadata.get("entities")
            ):
                raw_results = await self.retriever.graph_traversal_search(
                    filters.metadata["entities"], k=limit
                )
            elif search_type == "community" and query_embedding:
                raw_results = await self.retriever.community_search(
                    query_embedding, k=limit
                )
            else:
                # Fallback to keyword search
                raw_results = await self.retriever.keyword_search(query, k=limit)

            # Convert to SearchResult objects
            for result in raw_results:
                metadata = (
                    json.loads(result["metadata"])
                    if isinstance(result["metadata"], str)
                    else result.get("metadata", {})
                )

                search_result = SearchResult(
                    document=Document(
                        id=result["id"], content=result["content"], metadata=metadata
                    ),
                    score=result.get("score", 0.0),
                    metadata={
                        "search_type": search_type,
                        "vector_score": result.get("vector_score"),
                        "text_score": result.get("text_score"),
                        "context": result.get("context", []),
                    },
                )
                results.append(search_result)

        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise

        return results

    async def count_documents(self, filters: SearchFilter | None = None) -> int:
        """Count documents matching filters."""
        if not self._initialized:
            await self.initialize()

        async with self.driver.session(database=self.config.database) as session:
            result = await session.run("MATCH (d:Document) RETURN count(d) as count")
            record = await result.single()
            return record["count"] if record else 0

    async def list_documents(
        self, offset: int = 0, limit: int = 100, filters: SearchFilter | None = None
    ) -> list[Document]:
        """List documents with pagination."""
        if not self._initialized:
            await self.initialize()

        async with self.driver.session(database=self.config.database) as session:
            result = await session.run(
                """
                MATCH (d:Document)
                RETURN d.id as id, d.content as content, d.metadata as metadata, d.embedding as embedding
                ORDER BY d.created_at DESC
                SKIP $offset
                LIMIT $limit
            """,
                offset=offset,
                limit=limit,
            )

            documents = []
            async for record in result:
                metadata = json.loads(record["metadata"]) if record["metadata"] else {}
                documents.append(
                    Document(
                        id=record["id"],
                        content=record["content"],
                        metadata=metadata,
                        embedding=record["embedding"],
                    )
                )

            return documents

    async def create_knowledge_graph(
        self,
        documents: list[Document],
        extract_entities: bool = True,
        extract_relationships: bool = True,
        similarity_threshold: float = 0.8,
    ) -> dict[str, Any]:
        """Create a knowledge graph from documents."""
        if not self._initialized:
            await self.initialize()

        async with self.driver.session(database=self.config.database) as session:
            # Add all documents first
            for doc in documents:
                await self.add_document(doc)

            # Create similarity relationships between documents
            if similarity_threshold > 0:
                await session.run(
                    """
                    MATCH (d1:Document), (d2:Document)
                    WHERE d1.id < d2.id AND d1.embedding IS NOT NULL AND d2.embedding IS NOT NULL
                    WITH d1, d2, gds.similarity.cosine(d1.embedding, d2.embedding) as similarity
                    WHERE similarity > $threshold
                    MERGE (d1)-[:SIMILAR_TO {similarity: similarity}]->(d2)
                """,
                    threshold=similarity_threshold,
                )

            # Get graph statistics
            stats_result = await session.run(
                """
                MATCH (d:Document)
                OPTIONAL MATCH (d)-[:MENTIONS]->(e:Entity)
                OPTIONAL MATCH (d)-[:RELATES_TO]->(c:Concept)
                OPTIONAL MATCH (d)-[:SIMILAR_TO]-(similar:Document)
                RETURN count(DISTINCT d) as documents,
                       count(DISTINCT e) as entities,
                       count(DISTINCT c) as concepts,
                       count(DISTINCT similar) as similar_docs
            """
            )

            stats = await stats_result.single()
            return {
                "documents": stats["documents"],
                "entities": stats["entities"],
                "concepts": stats["concepts"],
                "similar_documents": stats["similar_docs"],
            }

    async def close(self) -> None:
        """Close the Neo4j connection."""
        if self.driver:
            await self.driver.close()
            self._initialized = False
