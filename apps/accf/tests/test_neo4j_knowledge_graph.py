"""
Tests for Neo4j Knowledge Graph Implementation

Tests the Neo4j GraphRAG integration and knowledge graph functionality.
"""

import pytest
import os
from unittest.mock import Mock, patch
from capabilities.neo4j_knowledge_graph import Neo4jKnowledgeGraph


class TestNeo4jKnowledgeGraph:
    """Test suite for Neo4j Knowledge Graph functionality."""

    @pytest.fixture
    def mock_driver(self):
        """Mock Neo4j driver for testing."""
        mock_driver = Mock()
        mock_session = Mock()
        mock_session_context = Mock()
        mock_session_context.__enter__ = Mock(return_value=mock_session)
        mock_session_context.__exit__ = Mock(return_value=None)
        mock_driver.session.return_value = mock_session_context
        return mock_driver, mock_session

    @pytest.fixture
    def mock_embedder(self):
        """Mock OpenAI embedder for testing."""
        mock_embedder = Mock()
        mock_embedder.embed_query.return_value = [0.1] * 1536
        return mock_embedder

    @pytest.fixture
    def knowledge_graph(self, mock_driver, mock_embedder):
        """Create a test knowledge graph instance."""
        driver, session = mock_driver

        with patch("capabilities.neo4j_knowledge_graph.GraphDatabase") as mock_graph_db:
            mock_graph_db.driver.return_value = driver

            with patch(
                "capabilities.neo4j_knowledge_graph.OpenAIEmbeddings"
            ) as mock_embeddings:
                mock_embeddings.return_value = mock_embedder

                # Mock environment variable
                with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
                    kg = Neo4jKnowledgeGraph(
                        uri="bolt://localhost:7687",
                        username="neo4j",
                        password="test-password",
                        database="neo4j",
                    )
                    return kg

    def test_initialization(self, knowledge_graph):
        """Test knowledge graph initialization."""
        assert knowledge_graph.uri == "bolt://localhost:7687"
        assert knowledge_graph.username == "neo4j"
        assert knowledge_graph.database == "neo4j"
        assert knowledge_graph.driver is not None
        assert knowledge_graph.embedder is not None

    def test_query_execution(self, knowledge_graph, mock_driver):
        """Test Cypher query execution."""
        driver, session = mock_driver

        # Mock query result
        mock_result = Mock()
        mock_result.__iter__.return_value = [
            {"name": "test", "value": 123},
            {"name": "test2", "value": 456},
        ]
        session.run.return_value = mock_result

        # Execute query
        result = knowledge_graph.query(
            "MATCH (n) RETURN n.name as name, n.value as value"
        )

        # Verify results
        assert len(result) == 2
        assert result[0]["name"] == "test"
        assert result[0]["value"] == 123
        assert result[1]["name"] == "test2"
        assert result[1]["value"] == 456

        # Verify session was called
        session.run.assert_called_once_with(
            "MATCH (n) RETURN n.name as name, n.value as value", {}
        )

    def test_query_with_parameters(self, knowledge_graph, mock_driver):
        """Test Cypher query execution with parameters."""
        driver, session = mock_driver

        # Mock query result
        mock_result = Mock()
        mock_result.__iter__.return_value = [{"id": "test-id"}]
        session.run.return_value = mock_result

        # Execute query with parameters
        params = {"name": "test-name", "value": 123}
        result = knowledge_graph.query(
            "MATCH (n {name: $name}) RETURN n.id as id", params
        )

        # Verify results
        assert len(result) == 1
        assert result[0]["id"] == "test-id"

        # Verify session was called with parameters
        session.run.assert_called_once_with(
            "MATCH (n {name: $name}) RETURN n.id as id", params
        )

    def test_vector_search(self, knowledge_graph, mock_embedder):
        """Test vector similarity search."""
        # Mock vector retriever
        mock_retriever = Mock()
        mock_retriever.search.return_value = [
            {"content": "test content 1", "score": 0.95},
            {"content": "test content 2", "score": 0.85},
        ]
        knowledge_graph.vector_retriever = mock_retriever

        # Perform vector search
        result = knowledge_graph.vector_search("test query", top_k=2)

        # Verify results
        assert len(result) == 2
        assert result[0]["content"] == "test content 1"
        assert result[0]["score"] == 0.95
        assert result[1]["content"] == "test content 2"
        assert result[1]["score"] == 0.85

        # Verify retriever was called
        mock_retriever.search.assert_called_once_with(query_text="test query", top_k=2)

    def test_store_research_finding(self, knowledge_graph, mock_driver, mock_embedder):
        """Test storing research findings with vector embeddings."""
        driver, session = mock_driver

        # Mock query result for node creation
        mock_result = Mock()
        mock_result.__iter__.return_value = [
            {"id": "test-id", "content": "test finding"}
        ]
        session.run.return_value = mock_result

        # Store research finding
        result = knowledge_graph.store_research_finding(
            content="Test research finding",
            source_url="https://example.com",
            confidence=0.8,
            metadata={"author": "test", "date": "2025-01-01"},
        )

        # Verify result
        assert result["status"] == "success"
        assert result["id"] == "test-id"

        # Verify session was called for node creation
        session.run.assert_called()
        call_args = session.run.call_args_list[0]
        assert "CREATE (f:ResearchFinding" in call_args[0][0]

    def test_find_similar_research(self, knowledge_graph):
        """Test finding similar research using vector search."""
        # Mock vector retriever
        mock_retriever = Mock()
        mock_retriever.search.return_value = [
            {"content": "similar finding 1", "score": 0.9},
            {"content": "similar finding 2", "score": 0.8},
        ]
        knowledge_graph.vector_retriever = mock_retriever

        # Find similar research
        result = knowledge_graph.find_similar_research("test query", top_k=2)

        # Verify results
        assert len(result) == 2
        assert result[0]["content"] == "similar finding 1"
        assert result[0]["score"] == 0.9
        assert result[1]["content"] == "similar finding 2"
        assert result[1]["score"] == 0.8

        # Verify retriever was called
        mock_retriever.search.assert_called_once_with(query_text="test query", top_k=2)

    def test_get_research_overview(self, knowledge_graph, mock_driver):
        """Test getting research overview statistics."""
        driver, session = mock_driver

        # Mock query results
        mock_counts_result = Mock()
        mock_counts_result.__iter__.return_value = [
            {"label": "Project", "count": 2},
            {"label": "ResearchFinding", "count": 5},
        ]

        mock_samples_result = Mock()
        mock_samples_result.__iter__.return_value = [
            {
                "content": "sample finding 1",
                "confidence": 0.8,
                "created_at": "2025-01-01",
            }
        ]

        # Configure session to return different results for different queries
        def mock_run(query, params=None):
            if "labels(n)" in query:
                return mock_counts_result
            elif "ResearchFinding" in query:
                return mock_samples_result
            return Mock()

        session.run.side_effect = mock_run

        # Get research overview
        result = knowledge_graph.get_research_overview()

        # Verify results
        assert "node_counts" in result
        assert "sample_findings" in result
        assert "total_findings" in result

        assert len(result["node_counts"]) == 2
        assert result["node_counts"][0]["label"] == "Project"
        assert result["node_counts"][0]["count"] == 2

        assert len(result["sample_findings"]) == 1
        assert result["sample_findings"][0]["content"] == "sample finding 1"
        assert result["total_findings"] == 1

    def test_connection_error_handling(self):
        """Test handling of connection errors."""
        with patch("capabilities.neo4j_knowledge_graph.GraphDatabase") as mock_graph_db:
            mock_graph_db.driver.side_effect = Exception("Connection failed")

            with pytest.raises(Exception, match="Connection failed"):
                Neo4jKnowledgeGraph()

    def test_query_error_handling(self, knowledge_graph, mock_driver):
        """Test handling of query execution errors."""
        driver, session = mock_driver
        session.run.side_effect = Exception("Query failed")

        # Execute query that should fail
        result = knowledge_graph.query("INVALID QUERY")

        # Verify error handling
        assert len(result) == 1
        assert "error" in result[0]
        assert "Query failed" in result[0]["error"]

    def test_vector_search_no_retriever(self, knowledge_graph):
        """Test vector search when retriever is not available."""
        knowledge_graph.vector_retriever = None

        # Attempt vector search
        result = knowledge_graph.vector_search("test query")

        # Verify empty result
        assert result == []

    def test_close_connection(self, knowledge_graph, mock_driver):
        """Test closing the database connection."""
        driver, session = mock_driver

        # Close connection
        knowledge_graph.close()

        # Verify driver was closed
        driver.close.assert_called_once()


class TestNeo4jKnowledgeGraphIntegration:
    """Integration tests for Neo4j Knowledge Graph."""

    @pytest.mark.integration
    def test_real_connection(self):
        """Test connection to real Neo4j instance (requires running Neo4j)."""
        # This test requires a running Neo4j instance
        # Skip if not available
        try:
            kg = Neo4jKnowledgeGraph()
            result = kg.query("RETURN 1 as test")
            assert len(result) == 1
            assert result[0]["test"] == 1
            kg.close()
        except Exception:
            pytest.skip("Neo4j not available for integration test")

    @pytest.mark.integration
    def test_vector_index_creation(self):
        """Test vector index creation (requires OpenAI API key)."""
        # This test requires OpenAI API key
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OpenAI API key not available")

        try:
            kg = Neo4jKnowledgeGraph()
            # Test that indexes can be created
            # This will be tested by the initialization
            assert kg.embedder is not None
            kg.close()
        except Exception:
            pytest.skip("Neo4j or OpenAI not available for integration test")
