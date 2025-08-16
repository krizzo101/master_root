#!/usr/bin/env python3
"""
Test semantic search capabilities with the knowledge base.
"""

import json
from neo4j import GraphDatabase
from mcp_knowledge_tools_v2 import SemanticSearchTool, SimilarKnowledgeTool

# Neo4j connection
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "password"


def test_semantic_search():
    """Test various semantic search scenarios."""
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    test_queries = [
        ("How to fix Neo4j property type errors", "semantic"),
        ("context intelligence architecture", "semantic"),
        ("Python import error solution", "hybrid"),
        ("knowledge system", "keyword"),
    ]
    
    print("=" * 60)
    print("SEMANTIC SEARCH TESTS")
    print("=" * 60)
    
    for query_text, search_type in test_queries:
        print(f"\n🔍 Query: '{query_text}' (Type: {search_type})")
        print("-" * 40)
        
        # Generate the search query
        search_tool = SemanticSearchTool()
        result = search_tool.execute(
            query_text=query_text,
            search_type=search_type,
            limit=3,
            min_similarity=0.3
        )
        
        # Execute the query
        with driver.session() as session:
            records = session.run(result["query"], **result["params"])
            results = list(records)
            
            if results:
                for i, record in enumerate(results, 1):
                    print(f"\n  {i}. {record.get('type', 'N/A')} (relevance: {record.get('relevance', 0):.3f})")
                    content = record.get('content', '')
                    if len(content) > 100:
                        content = content[:100] + "..."
                    print(f"     Content: {content}")
                    print(f"     Confidence: {record.get('confidence', 0):.2f}")
            else:
                print("  No results found")
    
    # Test finding similar knowledge
    print("\n" + "=" * 60)
    print("SIMILARITY SEARCH TEST")
    print("=" * 60)
    
    # Get a knowledge entry with embedding
    with driver.session() as session:
        result = session.run("""
            MATCH (k:Knowledge)
            WHERE k.embedding IS NOT NULL AND k.knowledge_id IS NOT NULL
            RETURN k.knowledge_id as id, k.content as content
            LIMIT 1
        """)
        reference = list(result)
        
        if reference:
            ref_id = reference[0]['id']
            ref_content = reference[0]['content']
            
            print(f"\n📌 Reference: {ref_content[:80]}...")
            print(f"   ID: {ref_id}")
            print("\n🔗 Similar knowledge:")
            
            # Find similar
            similar_tool = SimilarKnowledgeTool()
            sim_result = similar_tool.execute(
                knowledge_id=ref_id,
                limit=3,
                min_similarity=0.3
            )
            
            sim_records = session.run(sim_result["query"], **sim_result["params"])
            similar = list(sim_records)
            
            if similar:
                for i, record in enumerate(similar, 1):
                    print(f"\n  {i}. Similarity: {record.get('similarity', 0):.3f}")
                    content = record.get('content', '')
                    if len(content) > 80:
                        content = content[:80] + "..."
                    print(f"     {content}")
            else:
                print("  No similar entries found")
    
    driver.close()
    
    print("\n" + "=" * 60)
    print("✅ Semantic search tests completed!")


if __name__ == "__main__":
    test_semantic_search()