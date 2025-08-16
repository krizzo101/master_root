"""
Enhanced OPSVI-RAG Demo

Demonstrates the new Neo4j, ChromaDB, and SQLite integrations with
performance monitoring and hybrid search capabilities.
"""

import asyncio
import logging

import numpy as np

from opsvi_rag.analytics.performance import (
    PerformanceConfig,
    PerformanceMonitor,
    profile_datastore_operation,
    profile_search,
    set_performance_monitor,
)
from opsvi_rag.base import Document
from opsvi_rag.utils.datastore_factory import (
    DatastoreFactory,
    create_chromadb_store,
    create_neo4j_store,
    create_sqlite_store,
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def demo_chromadb_integration():
    """Demonstrate ChromaDB integration with various embedding functions."""
    logger.info("=== ChromaDB Integration Demo ===")

    # Create ChromaDB store with Sentence Transformers
    chromadb_store = create_chromadb_store(
        persist_directory="./demo_chroma_db",
        collection_name="demo_collection",
        embedding_function_type="sentence_transformer",
        embedding_model="all-MiniLM-L6-v2",
    )

    await chromadb_store.initialize()

    # Sample documents
    documents = [
        Document(
            content="Machine learning is a subset of artificial intelligence that focuses on algorithms.",
            metadata={"category": "AI", "topic": "machine_learning", "year": 2024},
        ),
        Document(
            content="Neural networks are computational models inspired by biological neural networks.",
            metadata={"category": "AI", "topic": "neural_networks", "year": 2024},
        ),
        Document(
            content="Natural language processing enables computers to understand human language.",
            metadata={"category": "AI", "topic": "nlp", "year": 2024},
        ),
        Document(
            content="Vector databases store and search high-dimensional vectors efficiently.",
            metadata={"category": "Database", "topic": "vector_search", "year": 2024},
        ),
    ]

    # Add documents with performance profiling
    async with profile_datastore_operation(
        "add_documents", "chromadb", document_count=len(documents)
    ):
        doc_ids = await chromadb_store.add_documents(documents)
        logger.info(f"Added {len(doc_ids)} documents to ChromaDB")

    # Perform various searches
    search_queries = [
        ("artificial intelligence", "semantic"),
        ("machine learning algorithms", "semantic"),
        ("vector search", "semantic"),
    ]

    for query, search_type in search_queries:
        async with profile_search(query, search_type, "chromadb") as profiler:
            results = await chromadb_store.search(
                query, limit=3, search_type=search_type
            )
            profiler.metadata["results_count"] = len(results)

            logger.info(f"Query: '{query}' - Found {len(results)} results")
            for i, result in enumerate(results):
                logger.info(
                    f"  {i+1}. Score: {result.score:.3f} - {result.document.content[:50]}..."
                )

    # Get collection info
    info = await chromadb_store.get_collection_info()
    logger.info(f"ChromaDB Collection Info: {info}")

    await chromadb_store.close()


async def demo_sqlite_integration():
    """Demonstrate SQLite integration with FTS5 and hybrid search."""
    logger.info("=== SQLite Integration Demo ===")

    # Create SQLite store with FTS5 enabled
    sqlite_store = create_sqlite_store(
        database_path="./demo_rag.db",
        fts_enabled=True,
        vector_search_enabled=True,
        embedding_dimension=384,
    )

    await sqlite_store.initialize()

    # Sample documents with embeddings (mock embeddings for demo)
    import numpy as np

    documents = [
        Document(
            content="Graph databases excel at handling complex relationships between entities.",
            metadata={"category": "Database", "topic": "graph_db", "year": 2025},
            embedding=np.random.rand(384).tolist(),
        ),
        Document(
            content="Full-text search enables fast text-based queries across large document collections.",
            metadata={"category": "Search", "topic": "full_text", "year": 2025},
            embedding=np.random.rand(384).tolist(),
        ),
        Document(
            content="Hybrid search combines vector similarity with keyword matching for better results.",
            metadata={"category": "Search", "topic": "hybrid_search", "year": 2025},
            embedding=np.random.rand(384).tolist(),
        ),
        Document(
            content="SQLite provides ACID transactions and supports JSON operations natively.",
            metadata={"category": "Database", "topic": "sqlite", "year": 2025},
            embedding=np.random.rand(384).tolist(),
        ),
    ]

    # Add documents
    async with profile_datastore_operation(
        "add_documents", "sqlite", document_count=len(documents)
    ):
        doc_ids = await sqlite_store.add_documents(documents)
        logger.info(f"Added {len(doc_ids)} documents to SQLite")

    # Test different search types
    search_tests = [
        ("database transactions", "fulltext", "Full-text search"),
        ("graph relationships", "fulltext", "Full-text search"),
        ("search vector", "vector", "Vector search"),
        ("database search", "hybrid", "Hybrid search"),
    ]

    for query, search_type, description in search_tests:
        query_embedding = (
            np.random.rand(384).tolist()
            if search_type in ["vector", "hybrid"]
            else None
        )

        async with profile_search(query, search_type, "sqlite") as profiler:
            results = await sqlite_store.search(
                query=query,
                query_embedding=query_embedding,
                limit=3,
                search_type=search_type,
            )
            profiler.metadata["results_count"] = len(results)

            logger.info(
                f"{description} - Query: '{query}' - Found {len(results)} results"
            )
            for i, result in enumerate(results):
                logger.info(
                    f"  {i+1}. Score: {result.score:.3f} - {result.document.content[:50]}..."
                )

    # Get database statistics
    stats = await sqlite_store.get_database_stats()
    logger.info(f"SQLite Database Stats: {stats}")

    await sqlite_store.close()


async def demo_neo4j_integration():
    """Demonstrate Neo4j integration with GraphRAG capabilities."""
    logger.info("=== Neo4j Integration Demo ===")

    try:
        # Create Neo4j store (requires Neo4j server running)
        neo4j_store = create_neo4j_store(
            uri="bolt://localhost:7687",
            username="neo4j",
            password="password",  # Change to your Neo4j password
        )

        await neo4j_store.initialize()

        # Sample documents with entities and concepts
        documents = [
            Document(
                content="OpenAI developed ChatGPT using transformer architecture and reinforcement learning.",
                metadata={
                    "category": "AI",
                    "entities": [
                        {"name": "OpenAI", "type": "ORGANIZATION", "confidence": 0.95},
                        {"name": "ChatGPT", "type": "PRODUCT", "confidence": 0.98},
                    ],
                    "concepts": [
                        {
                            "name": "transformer architecture",
                            "category": "TECHNOLOGY",
                            "relevance": 0.9,
                        },
                        {
                            "name": "reinforcement learning",
                            "category": "TECHNIQUE",
                            "relevance": 0.8,
                        },
                    ],
                },
                embedding=np.random.rand(1536).tolist(),
            ),
            Document(
                content="Neo4j is a graph database that uses Cypher query language for data retrieval.",
                metadata={
                    "category": "Database",
                    "entities": [
                        {"name": "Neo4j", "type": "PRODUCT", "confidence": 0.98},
                        {"name": "Cypher", "type": "LANGUAGE", "confidence": 0.95},
                    ],
                    "concepts": [
                        {
                            "name": "graph database",
                            "category": "TECHNOLOGY",
                            "relevance": 0.95,
                        },
                        {
                            "name": "query language",
                            "category": "TECHNIQUE",
                            "relevance": 0.8,
                        },
                    ],
                },
                embedding=np.random.rand(1536).tolist(),
            ),
        ]

        # Add documents and create knowledge graph
        async with profile_datastore_operation("create_knowledge_graph", "neo4j"):
            graph_stats = await neo4j_store.create_knowledge_graph(
                documents=documents,
                extract_entities=True,
                extract_relationships=True,
                similarity_threshold=0.7,
            )
            logger.info(f"Created knowledge graph: {graph_stats}")

        # Test different GraphRAG search strategies
        search_strategies = [
            ("transformer architecture", "hybrid", "Hybrid search"),
            ("OpenAI ChatGPT", "graph_traversal", "Graph traversal"),
            ("database technology", "community", "Community search"),
        ]

        for query, search_type, description in search_strategies:
            query_embedding = np.random.rand(1536).tolist()

            try:
                async with profile_search(query, search_type, "neo4j") as profiler:
                    if search_type == "graph_traversal":
                        # For graph traversal, we need to specify entities
                        from opsvi_rag.base import SearchFilter

                        filters = SearchFilter(
                            metadata={"entities": ["OpenAI", "Neo4j"]}
                        )
                        results = await neo4j_store.search(
                            query=query,
                            query_embedding=query_embedding,
                            filters=filters,
                            limit=3,
                            search_type=search_type,
                        )
                    else:
                        results = await neo4j_store.search(
                            query=query,
                            query_embedding=query_embedding,
                            limit=3,
                            search_type=search_type,
                        )

                    profiler.metadata["results_count"] = len(results)

                    logger.info(
                        f"{description} - Query: '{query}' - Found {len(results)} results"
                    )
                    for i, result in enumerate(results):
                        logger.info(
                            f"  {i+1}. Score: {result.score:.3f} - {result.document.content[:50]}..."
                        )
            except Exception as e:
                logger.warning(f"Search strategy '{search_type}' failed: {e}")

        await neo4j_store.close()

    except Exception as e:
        logger.warning(f"Neo4j demo skipped (server not available): {e}")


async def demo_multi_datastore():
    """Demonstrate multi-datastore setup for comprehensive RAG."""
    logger.info("=== Multi-Datastore Demo ===")

    # Note: Individual stores can be created as needed for specific operations

    # Create multi-datastore
    multi_store = DatastoreFactory.create_multi_datastore(
        configs={
            "sqlite": {
                "type": "sqlite",
                "database_path": "./multi_demo.db",
                "fts_enabled": True,
            },
            "chromadb": {
                "type": "chromadb",
                "persist_directory": "./multi_chroma",
                "collection_name": "multi_demo",
            },
        },
        primary="sqlite",
    )

    await multi_store.initialize()

    # Add document to all datastores
    document = Document(
        content="Multi-datastore architecture provides redundancy and specialized capabilities.",
        metadata={"category": "Architecture", "topic": "multi_store", "year": 2025},
    )

    replication_results = await multi_store.replicate_to_all(document)
    logger.info(f"Replicated document to: {replication_results}")

    # Search across all datastores
    search_results = await multi_store.search_all("multi-datastore architecture")

    for datastore_name, results in search_results.items():
        logger.info(f"Results from {datastore_name}: {len(results)} documents")
        for i, result in enumerate(results[:2]):  # Show top 2 results
            logger.info(
                f"  {i+1}. Score: {result.score:.3f} - {result.document.content[:50]}..."
            )

    await multi_store.close()


async def demo_performance_monitoring():
    """Demonstrate performance monitoring capabilities."""
    logger.info("=== Performance Monitoring Demo ===")

    # Get performance statistics
    monitor = PerformanceMonitor(config=PerformanceConfig())
    if monitor:
        # Get recent statistics
        search_stats = await monitor.get_search_statistics(time_window_minutes=30)
        datastore_stats = await monitor.get_datastore_statistics(time_window_minutes=30)

        logger.info("=== Search Performance Statistics ===")
        logger.info(f"Total searches: {search_stats.get('total_searches', 0)}")
        logger.info(f"Success rate: {search_stats.get('success_rate', 0):.2%}")
        logger.info(
            f"Average execution time: {search_stats.get('execution_time', {}).get('mean_ms', 0):.2f}ms"
        )
        logger.info(
            f"95th percentile: {search_stats.get('execution_time', {}).get('p95_ms', 0):.2f}ms"
        )

        logger.info("=== Datastore Performance Statistics ===")
        logger.info(f"Total operations: {datastore_stats.get('total_operations', 0)}")
        logger.info(f"Success rate: {datastore_stats.get('success_rate', 0):.2%}")
        logger.info(
            f"Average execution time: {datastore_stats.get('execution_time', {}).get('mean_ms', 0):.2f}ms"
        )

        # Get performance summary
        summary = await monitor.get_performance_summary()
        logger.info(f"System health: {summary['system_health']['overall_health']}")

        # Clean up old metrics
        await monitor.cleanup_old_metrics()
    else:
        logger.info("Performance monitoring not enabled")


async def main():
    """Main demo function."""
    logger.info("Starting Enhanced OPSVI-RAG Demo")

    # Setup performance monitoring
    perf_config = PerformanceConfig(
        enable_metrics=True, slow_query_threshold_ms=500.0, enable_alerts=True
    )
    monitor = PerformanceMonitor(perf_config)
    set_performance_monitor(monitor)

    try:
        # Run all demos
        await demo_chromadb_integration()
        await demo_sqlite_integration()
        await demo_neo4j_integration()
        await demo_multi_datastore()
        await demo_performance_monitoring()

    except Exception as e:
        logger.error(f"Demo failed: {e}")

    logger.info("Enhanced OPSVI-RAG Demo completed")


if __name__ == "__main__":
    asyncio.run(main())
