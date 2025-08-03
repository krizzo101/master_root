"""
Neo4j Vector Search Implementation.

This module provides vector search capabilities for the ACCF Research Agent
using Neo4j's vector search features.
"""

from neo4j import AsyncGraphDatabase
import numpy as np
from typing import List, Dict, Any, Optional
import logging


class Neo4jVectorSearch:
    """Neo4j Vector Search implementation for ACCF Research Agent."""

    def __init__(self, uri: str, user: str, password: str, database: str = "neo4j"):
        """Initialize Neo4j vector search."""
        self.driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
        self.database = database
        self.logger = logging.getLogger(__name__)
        self.logger.info("Neo4j Vector Search initialized")

    async def create_vector_index(
        self,
        index_name: str = "embeddings",
        label: str = "Text",
        property: str = "embedding",
        dimensions: int = 1536,
        similarity: str = "cosine",
    ):
        """Create a vector index for embeddings."""
        try:
            async with self.driver.session(database=self.database) as session:
                # Check if index already exists
                result = await session.run(
                    """
                    SHOW INDEXES
                    YIELD name, type, labelsOrTypes, properties
                    WHERE name = $index_name
                """,
                    index_name=index_name,
                )

                if not await result.single():
                    # Create the vector index
                    await session.run(
                        f"""
                        CALL db.index.vector.createNodeIndex(
                            '{index_name}', '{label}', '{property}',
                            {dimensions}, '{similarity}'
                        )
                    """
                    )
                    self.logger.info(f"Created vector index: {index_name}")
                else:
                    self.logger.info(f"Vector index {index_name} already exists")

        except Exception as e:
            self.logger.error(f"Error creating vector index: {e}")
            raise

    async def vector_search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        index_name: str = "embeddings",
    ) -> List[Dict[str, Any]]:
        """Perform vector search using embeddings."""
        try:
            async with self.driver.session(database=self.database) as session:
                result = await session.run(
                    f"""
                    CALL db.index.vector.queryNodes('{index_name}', $top_k, $embedding)
                    YIELD node, score
                    RETURN node.text as text, score, node.id as id
                    ORDER BY score DESC
                """,
                    top_k=top_k,
                    embedding=query_embedding,
                )

                records = [record.data() for record in result]
                self.logger.info(f"Vector search returned {len(records)} results")
                return records

        except Exception as e:
            self.logger.error(f"Error in vector search: {e}")
            return []

    async def store_embedding(
        self, text: str, embedding: List[float], node_id: Optional[str] = None
    ) -> bool:
        """Store text with its embedding in Neo4j."""
        try:
            async with self.driver.session(database=self.database) as session:
                if node_id:
                    # Update existing node
                    await session.run(
                        """
                        MATCH (n:Text {id: $node_id})
                        SET n.text = $text, n.embedding = $embedding
                    """,
                        node_id=node_id,
                        text=text,
                        embedding=embedding,
                    )
                else:
                    # Create new node
                    await session.run(
                        """
                        CREATE (n:Text {text: $text, embedding: $embedding})
                    """,
                        text=text,
                        embedding=embedding,
                    )

                self.logger.info(f"Stored embedding for text: {text[:50]}...")
                return True

        except Exception as e:
            self.logger.error(f"Error storing embedding: {e}")
            return False

    async def batch_store_embeddings(
        self, texts: List[str], embeddings: List[List[float]]
    ) -> bool:
        """Store multiple texts with their embeddings in batch."""
        try:
            async with self.driver.session(database=self.database) as session:
                # Use UNWIND for efficient batch insertion
                data = [
                    {"text": text, "embedding": embedding}
                    for text, embedding in zip(texts, embeddings)
                ]

                await session.run(
                    """
                    UNWIND $data as item
                    CREATE (n:Text {text: item.text, embedding: item.embedding})
                """,
                    data=data,
                )

                self.logger.info(f"Batch stored {len(texts)} embeddings")
                return True

        except Exception as e:
            self.logger.error(f"Error in batch store: {e}")
            return False

    async def delete_embedding(self, node_id: str) -> bool:
        """Delete an embedding node by ID."""
        try:
            async with self.driver.session(database=self.database) as session:
                result = await session.run(
                    """
                    MATCH (n:Text {id: $node_id})
                    DELETE n
                    RETURN count(n) as deleted
                """,
                    node_id=node_id,
                )

                deleted = await result.single()
                if deleted and deleted["deleted"] > 0:
                    self.logger.info(f"Deleted embedding node: {node_id}")
                    return True
                else:
                    self.logger.warning(f"Node not found: {node_id}")
                    return False

        except Exception as e:
            self.logger.error(f"Error deleting embedding: {e}")
            return False

    async def get_embedding_stats(self) -> Dict[str, Any]:
        """Get statistics about stored embeddings."""
        try:
            async with self.driver.session(database=self.database) as session:
                result = await session.run(
                    """
                    MATCH (n:Text)
                    RETURN count(n) as total_nodes,
                           count(n.embedding) as nodes_with_embeddings
                """
                )

                stats = await result.single()
                return {
                    "total_nodes": stats["total_nodes"],
                    "nodes_with_embeddings": stats["nodes_with_embeddings"],
                    "database": self.database,
                }

        except Exception as e:
            self.logger.error(f"Error getting stats: {e}")
            return {"error": str(e)}

    async def close(self):
        """Close the Neo4j driver connection."""
        await self.driver.close()
        self.logger.info("Neo4j Vector Search connection closed")
