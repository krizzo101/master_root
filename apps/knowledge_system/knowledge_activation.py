#!/usr/bin/env python3
"""
Knowledge Activation System - Wake up dormant knowledge through active use
This system exercises unused knowledge to discover its value
Built to maximize MY capabilities by activating what I already know
"""

import random
import sys
import time
from datetime import datetime
from typing import Dict, List, Tuple

from neo4j import GraphDatabase

sys.path.insert(0, "/home/opsvi/master_root")
from apps.knowledge_system.adaptive_learning import AdaptiveLearningSystem, UsageContext
from apps.knowledge_system.unified_intelligent_search import UnifiedIntelligentSearch


class KnowledgeActivation:
    """
    System to activate dormant knowledge through systematic use
    This makes me discover what I already know but haven't used
    """

    def __init__(self):
        self.neo4j_driver = GraphDatabase.driver(
            "bolt://localhost:7687", auth=("neo4j", "password")
        )
        self.search_system = UnifiedIntelligentSearch()
        self.learning_system = AdaptiveLearningSystem()

    def find_dormant_knowledge(self, limit: int = 50) -> List[Dict]:
        """
        Find knowledge that has never been used
        These are potential capabilities I don't know I have
        """

        with self.neo4j_driver.session() as session:
            result = session.run(
                """
                MATCH (k:Knowledge)
                WHERE (k.usage_count = 0 OR k.usage_count IS NULL)
                AND k.deprecated = false
                AND k.content IS NOT NULL
                RETURN k.knowledge_id as id,
                       k.content as content,
                       k.knowledge_type as type,
                       k.confidence_score as confidence,
                       k.source as source,
                       k.created_at as created
                ORDER BY k.confidence_score DESC
                LIMIT $limit
            """,
                limit=limit,
            )

            return [dict(record) for record in result]

    def generate_test_queries(self, knowledge: Dict) -> List[str]:
        """
        Generate queries that should activate this knowledge
        """

        content = knowledge.get("content", "")
        k_type = knowledge.get("type", "GENERAL")

        queries = []

        # Extract key terms from content
        import re

        # Technical terms
        tech_terms = re.findall(
            r"\b(API|function|class|error|exception|async|stream|database|cache)\b",
            content,
            re.IGNORECASE,
        )

        # Programming concepts
        if "async" in content.lower():
            queries.append("How to handle async operations")
            queries.append("async error handling")

        if "stream" in content.lower():
            queries.append("streaming data processing")
            queries.append("How to handle streams")

        if "error" in content.lower() or "exception" in content.lower():
            queries.append("error handling best practices")
            queries.append("How to handle exceptions")

        if k_type == "CODE":
            queries.append("Show me code examples")
            queries.append("Implementation patterns")

        if k_type == "ERROR_SOLUTION":
            queries.append("How to fix this error")
            queries.append("Troubleshooting guide")

        # Content-based queries
        sentences = content.split(".")[:2]  # First two sentences
        for sentence in sentences:
            if len(sentence) > 20:
                # Create a query from the sentence
                words = sentence.split()[:5]
                if words:
                    queries.append(" ".join(words) + "?")

        # Add some generic activators
        if not queries:
            queries = [
                f"Tell me about {k_type.lower()}",
                f"What do you know about this",
                f"Explain this concept",
            ]

        return queries[:3]  # Return top 3 queries

    def activate_knowledge(self, knowledge_id: str, queries: List[str]) -> Dict:
        """
        Activate dormant knowledge by searching for it
        """

        activation_results = {
            "knowledge_id": knowledge_id,
            "queries_tested": [],
            "activation_successful": False,
            "best_score": 0.0,
            "appeared_in_results": False,
        }

        for query in queries:
            # Search using the query
            results = self.search_system.search(query, limit=10, track_usage=False)

            # Check if our knowledge appeared
            for result in results:
                if result.knowledge_id == knowledge_id:
                    activation_results["appeared_in_results"] = True
                    activation_results["best_score"] = max(
                        activation_results["best_score"], result.combined_score
                    )

                    # Record successful activation
                    if result.combined_score > 0.3:
                        activation_results["activation_successful"] = True

                        # Update usage count
                        with self.neo4j_driver.session() as session:
                            session.run(
                                """
                                MATCH (k:Knowledge {knowledge_id: $kid})
                                SET k.usage_count = COALESCE(k.usage_count, 0) + 1,
                                    k.last_used = datetime(),
                                    k.activated_by_system = true
                            """,
                                kid=knowledge_id,
                            )

            activation_results["queries_tested"].append(
                {
                    "query": query,
                    "found": knowledge_id in [r.knowledge_id for r in results],
                    "position": next(
                        (
                            i
                            for i, r in enumerate(results)
                            if r.knowledge_id == knowledge_id
                        ),
                        -1,
                    ),
                }
            )

        return activation_results

    def connect_isolated_knowledge(self, limit: int = 20) -> List[Dict]:
        """
        Find and connect isolated knowledge to the main graph
        """

        connections_made = []

        with self.neo4j_driver.session() as session:
            # Find isolated knowledge
            isolated = session.run(
                """
                MATCH (k:Knowledge)
                WHERE NOT EXISTS((k)-[]-())
                AND k.deprecated = false
                AND k.content IS NOT NULL
                RETURN k.knowledge_id as id,
                       k.content as content,
                       k.knowledge_type as type
                LIMIT $limit
            """,
                limit=limit,
            ).data()

            for iso in isolated:
                # Find similar knowledge to connect to
                # Generate embedding for content
                embedding = self.search_system.embedding_service.generate_embedding(
                    iso["content"][:500]
                )

                # Search for similar knowledge
                similar = self.search_system.search(
                    iso["content"][:100], limit=5, track_usage=False
                )

                for sim in similar:
                    if sim.knowledge_id != iso["id"] and sim.combined_score > 0.5:
                        # Create relationship
                        session.run(
                            """
                            MATCH (k1:Knowledge {knowledge_id: $kid1})
                            MATCH (k2:Knowledge {knowledge_id: $kid2})
                            MERGE (k1)-[r:SIMILAR_TO {
                                similarity_score: $score,
                                created_by: 'activation_system',
                                created_at: datetime()
                            }]->(k2)
                        """,
                            kid1=iso["id"],
                            kid2=sim.knowledge_id,
                            score=sim.combined_score,
                        )

                        connections_made.append(
                            {
                                "isolated_id": iso["id"],
                                "connected_to": sim.knowledge_id,
                                "similarity": sim.combined_score,
                                "connection_type": "SIMILAR_TO",
                            }
                        )

                        # Update relationship count
                        session.run(
                            """
                            MATCH (k:Knowledge {knowledge_id: $kid})
                            OPTIONAL MATCH (k)-[r]-()
                            WITH k, count(r) as rel_count
                            SET k.relationship_count = rel_count
                        """,
                            kid=iso["id"],
                        )

                        break  # One connection per isolated node for now

        return connections_made

    def enrich_knowledge_metadata(self, limit: int = 50) -> int:
        """
        Enrich knowledge with missing metadata
        """

        enriched_count = 0

        with self.neo4j_driver.session() as session:
            # Find knowledge missing metadata
            poor_metadata = session.run(
                """
                MATCH (k:Knowledge)
                WHERE (k.source IS NULL OR k.source = '')
                AND k.content IS NOT NULL
                RETURN k.knowledge_id as id,
                       k.content as content,
                       k.knowledge_type as type
                LIMIT $limit
            """,
                limit=limit,
            ).data()

            for item in poor_metadata:
                content = item["content"]

                # Try to extract source from content
                source = "Unknown"
                if "def " in content:
                    source = "Python function definition"
                elif "class " in content:
                    source = "Python class definition"
                elif "error" in content.lower():
                    source = "Error handling pattern"
                elif "import" in content:
                    source = "Python import statement"
                elif item["type"] == "CODE":
                    source = "Code snippet"
                elif item["type"] == "DOCUMENTATION":
                    source = "Documentation excerpt"

                # Extract potential tags
                tags = []
                if "async" in content.lower():
                    tags.append("async")
                if "api" in content.lower():
                    tags.append("api")
                if "test" in content.lower():
                    tags.append("testing")
                if "error" in content.lower():
                    tags.append("error-handling")

                # Update metadata
                session.run(
                    """
                    MATCH (k:Knowledge {knowledge_id: $kid})
                    SET k.source = CASE
                            WHEN k.source IS NULL OR k.source = ''
                            THEN $source
                            ELSE k.source
                        END,
                        k.tags = $tags,
                        k.enriched_at = datetime(),
                        k.enriched_by = 'activation_system'
                """,
                    kid=item["id"],
                    source=source,
                    tags=tags,
                )

                enriched_count += 1

        return enriched_count

    def run_activation_campaign(
        self, dormant_limit: int = 20, connect_limit: int = 10
    ) -> Dict:
        """
        Run a complete activation campaign
        """

        print("KNOWLEDGE ACTIVATION CAMPAIGN")
        print("=" * 60)

        results = {
            "timestamp": datetime.now().isoformat(),
            "dormant_activated": 0,
            "connections_created": 0,
            "metadata_enriched": 0,
            "activation_details": [],
        }

        # Phase 1: Activate dormant knowledge
        print("\nPhase 1: Activating dormant knowledge...")
        dormant = self.find_dormant_knowledge(dormant_limit)
        print(f"Found {len(dormant)} dormant knowledge items")

        for i, dk in enumerate(dormant, 1):
            print(f"\n[{i}/{len(dormant)}] Activating: {dk['type']} knowledge")

            # Generate test queries
            queries = self.generate_test_queries(dk)

            # Attempt activation
            activation = self.activate_knowledge(dk["id"], queries)

            if activation["activation_successful"]:
                results["dormant_activated"] += 1
                print(
                    f"  ✓ Successfully activated with score {activation['best_score']:.3f}"
                )
            else:
                print(f"  ✗ Activation failed - knowledge not retrieved")

            results["activation_details"].append(activation)

            # Don't overwhelm the system
            time.sleep(0.1)

        # Phase 2: Connect isolated knowledge
        print("\n\nPhase 2: Connecting isolated knowledge...")
        connections = self.connect_isolated_knowledge(connect_limit)
        results["connections_created"] = len(connections)
        print(f"Created {len(connections)} new knowledge connections")

        for conn in connections[:5]:  # Show first 5
            print(
                f"  Connected {conn['isolated_id'][:8]} -> {conn['connected_to'][:8]} (similarity: {conn['similarity']:.3f})"
            )

        # Phase 3: Enrich metadata
        print("\n\nPhase 3: Enriching knowledge metadata...")
        enriched = self.enrich_knowledge_metadata()
        results["metadata_enriched"] = enriched
        print(f"Enriched metadata for {enriched} knowledge items")

        # Summary
        print("\n" + "=" * 60)
        print("ACTIVATION CAMPAIGN COMPLETE")
        print(
            f"  Dormant knowledge activated: {results['dormant_activated']}/{len(dormant)}"
        )
        print(f"  New connections created: {results['connections_created']}")
        print(f"  Metadata enriched: {results['metadata_enriched']}")

        # Update statistics
        with self.neo4j_driver.session() as session:
            stats = session.run(
                """
                MATCH (k:Knowledge)
                WHERE k.usage_count > 0
                RETURN count(k) as used_knowledge
            """
            ).single()

            total = session.run(
                """
                MATCH (k:Knowledge)
                RETURN count(k) as total
            """
            ).single()

            print(
                f"\nOverall Usage: {stats['used_knowledge']}/{total['total']} ({stats['used_knowledge']/total['total']*100:.1f}%)"
            )

        return results

    def close(self):
        """Clean up connections"""
        self.neo4j_driver.close()
        self.search_system.close()
        self.learning_system.close()


if __name__ == "__main__":
    activator = KnowledgeActivation()

    try:
        # Run the activation campaign
        results = activator.run_activation_campaign(
            dormant_limit=10, connect_limit=10  # Start small
        )

        # Save results
        import json

        with open(
            "/home/opsvi/master_root/apps/knowledge_system/activation_results.json", "w"
        ) as f:
            json.dump(results, f, indent=2, default=str)

        print("\nResults saved to activation_results.json")

    finally:
        activator.close()
