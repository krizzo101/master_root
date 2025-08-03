#!/usr/bin/env python3
"""
Demo script for Neo4j Vector Search functionality

This script demonstrates the vector search capabilities of the Neo4j Knowledge Graph
implementation using the GraphRAG library.
"""

import os
import sys
from capabilities.neo4j_knowledge_graph import Neo4jKnowledgeGraph


def demo_vector_search():
    """Demonstrate vector search functionality."""
    print("=== Neo4j Vector Search Demo ===\n")

    try:
        # Initialize knowledge graph
        print("1. Initializing Neo4j Knowledge Graph...")
        kg = Neo4jKnowledgeGraph()
        print("✓ Knowledge graph initialized successfully\n")

        # Test basic query
        print("2. Testing basic Cypher query...")
        result = kg.query("RETURN 1 as test")
        print(f"✓ Query result: {result}\n")

        # Store sample research findings
        print("3. Storing sample research findings...")
        sample_findings = [
            {
                "content": "Neo4j GraphRAG provides excellent vector search capabilities for knowledge graphs",
                "source_url": "https://neo4j.com/graphrag",
                "confidence": 0.9,
                "metadata": {"topic": "graph databases", "year": 2025},
            },
            {
                "content": "Vector search in Neo4j enables semantic similarity matching for research content",
                "source_url": "https://neo4j.com/vector-search",
                "confidence": 0.85,
                "metadata": {"topic": "vector search", "year": 2025},
            },
            {
                "content": "Multi-agent systems benefit from knowledge graph integration for context awareness",
                "source_url": "https://example.com/multi-agent",
                "confidence": 0.8,
                "metadata": {"topic": "multi-agent systems", "year": 2025},
            },
        ]

        for finding in sample_findings:
            result = kg.store_research_finding(**finding)
            print(f"✓ Stored finding: {finding['content'][:50]}...")

        print(f"✓ All {len(sample_findings)} findings stored successfully\n")

        # Test vector search
        print("4. Testing vector similarity search...")
        search_queries = [
            "What are the benefits of vector search?",
            "How do knowledge graphs work?",
            "Tell me about multi-agent systems",
        ]

        for query in search_queries:
            print(f"\nSearching for: '{query}'")
            results = kg.find_similar_research(query, top_k=2)

            if results:
                print(f"Found {len(results)} similar findings:")
                for i, result in enumerate(results, 1):
                    print(f"  {i}. Score: {result.get('score', 'N/A'):.3f}")
                    print(f"     Content: {result.get('content', 'N/A')[:80]}...")
            else:
                print("No similar findings found")

        print("\n5. Getting research overview...")
        overview = kg.get_research_overview()
        print(f"✓ Node counts: {overview.get('node_counts', [])}")
        print(f"✓ Total findings: {overview.get('total_findings', 0)}")

        # Test with evidence
        print("\n6. Testing evidence-based search...")
        evidence_result = kg.answer_with_evidence("vector search capabilities")
        print(f"✓ Evidence search result: {evidence_result.get('answer', 'No answer')}")

        print("\n=== Demo completed successfully! ===")

    except Exception as e:
        print(f"❌ Demo failed: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure Neo4j is running on bolt://localhost:7687")
        print("2. Check that OPENAI_API_KEY is set in environment")
        print("3. Verify Neo4j credentials in .cursor/mcp.json")
        return False

    finally:
        # Clean up
        try:
            kg.close()
            print("✓ Database connection closed")
        except:
            pass

    return True


def demo_schema_verification():
    """Verify the database schema and constraints."""
    print("\n=== Schema Verification ===\n")

    try:
        kg = Neo4jKnowledgeGraph()

        # Check node labels
        print("1. Checking node labels...")
        labels = kg.query("CALL db.labels() YIELD label RETURN label")
        print(f"✓ Found labels: {[row['label'] for row in labels]}")

        # Check relationship types
        print("\n2. Checking relationship types...")
        relationships = kg.query(
            "CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType"
        )
        print(
            f"✓ Found relationships: {[row['relationshipType'] for row in relationships]}"
        )

        # Check constraints
        print("\n3. Checking constraints...")
        constraints = kg.query("SHOW CONSTRAINTS")
        print(f"✓ Found {len(constraints)} constraints")

        # Check existing data
        print("\n4. Checking existing data...")
        project_count = kg.query("MATCH (p:Project) RETURN count(p) as count")[0][
            "count"
        ]
        run_count = kg.query("MATCH (r:Run) RETURN count(r) as count")[0]["count"]
        task_count = kg.query("MATCH (t:Task) RETURN count(t) as count")[0]["count"]
        decision_count = kg.query("MATCH (d:Decision) RETURN count(d) as count")[0][
            "count"
        ]

        print(f"✓ Projects: {project_count}")
        print(f"✓ Runs: {run_count}")
        print(f"✓ Tasks: {task_count}")
        print(f"✓ Decisions: {decision_count}")

        print("\n=== Schema verification completed! ===")

    except Exception as e:
        print(f"❌ Schema verification failed: {e}")
        return False

    finally:
        try:
            kg.close()
        except:
            pass

    return True


if __name__ == "__main__":
    print("Neo4j Vector Search Demo")
    print("=" * 50)

    # Check environment
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Warning: OPENAI_API_KEY not set. Vector search will be limited.")
        print("   Set OPENAI_API_KEY environment variable for full functionality.\n")

    # Run demos
    success1 = demo_schema_verification()
    success2 = demo_vector_search()

    if success1 and success2:
        print("\n🎉 All demos completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Some demos failed. Check the output above for details.")
        sys.exit(1)
