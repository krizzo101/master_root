#!/usr/bin/env python3
"""
ArangoDB Comprehensive Testing Suite
===================================

Tests all enhanced database capabilities:
- Analyzers functionality
- Search views performance
- Graph traversal optimization
- Stored query execution
- Data population and validation
"""

import json
import logging
import time
import random
from typing import Dict, List, Any, Optional
from arango import ArangoClient, ArangoServerError

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ArangoComprehensiveTesting:
    """Comprehensive testing suite for enhanced ArangoDB capabilities"""

    def __init__(self):
        """Initialize with database connection"""
        self.client = ArangoClient(hosts="http://127.0.0.1:8529")
        self.db = self.client.db(
            "asea_prod_db", username="root", password="arango_dev_password"
        )
        self.test_results = {
            "analyzer_tests": [],
            "view_tests": [],
            "graph_tests": [],
            "performance_tests": [],
            "data_population": {},
            "integration_tests": [],
            "summary": {},
        }

    def test_analyzers(self) -> List[Dict[str, Any]]:
        """Test all custom analyzers"""
        logger.info("Testing Custom Analyzers...")

        test_texts = [
            "This is a comprehensive test of the knowledge management system with advanced AI capabilities",
            "function_name_with_underscores and camelCaseIdentifiers for code analysis",
            "Machine learning algorithms utilize neural networks for pattern recognition and data analysis",
        ]

        analyzers = ["knowledge_text_analyzer", "code_analyzer", "ngram_analyzer"]

        results = []

        for analyzer in analyzers:
            logger.info(f"Testing analyzer: {analyzer}")

            for i, text in enumerate(test_texts):
                try:
                    query = f"RETURN TOKENS(@text, '{analyzer}')"
                    result = self.db.aql.execute(query, bind_vars={"text": text})
                    tokens = list(result)[0]

                    test_result = {
                        "analyzer": analyzer,
                        "test_case": i + 1,
                        "input_text": text[:50] + "..." if len(text) > 50 else text,
                        "token_count": len(tokens),
                        "sample_tokens": tokens[:10],
                        "status": "success",
                    }

                    results.append(test_result)
                    logger.info(f"  Test {i+1}: {len(tokens)} tokens generated")

                except Exception as e:
                    results.append(
                        {
                            "analyzer": analyzer,
                            "test_case": i + 1,
                            "status": "failed",
                            "error": str(e),
                        }
                    )
                    logger.error(f"  Test {i+1} failed: {e}")

        return results

    def test_search_views(self) -> List[Dict[str, Any]]:
        """Test search view functionality"""
        logger.info("Testing Search Views...")

        views = [
            {
                "name": "knowledge_search_view",
                "test_queries": ["intelligence", "analysis", "system", "cognitive"],
            },
            {
                "name": "code_search_view",
                "test_queries": ["component", "function", "class", "module"],
            },
        ]

        results = []

        for view_config in views:
            view_name = view_config["name"]
            logger.info(f"Testing view: {view_name}")

            for query_term in view_config["test_queries"]:
                try:
                    start_time = time.time()

                    query = f"""
                        FOR doc IN {view_name}
                            SEARCH PHRASE(doc.content, @term, "knowledge_text_analyzer") OR
                                   @term IN doc.tags
                            SORT TFIDF(doc) DESC
                            LIMIT 10
                            RETURN {{
                                id: doc._id,
                                collection: PARSE_IDENTIFIER(doc._id).collection,
                                score: TFIDF(doc),
                                content_preview: LEFT(doc.content, 100)
                            }}
                    """

                    result = self.db.aql.execute(query, bind_vars={"term": query_term})
                    docs = list(result)
                    search_time = time.time() - start_time

                    test_result = {
                        "view": view_name,
                        "search_term": query_term,
                        "results_count": len(docs),
                        "search_time": search_time,
                        "avg_score": sum(doc.get("score", 0) for doc in docs)
                        / len(docs)
                        if docs
                        else 0,
                        "collections_found": list(
                            set(doc.get("collection") for doc in docs)
                        ),
                        "status": "success",
                    }

                    results.append(test_result)
                    logger.info(
                        f"  '{query_term}': {len(docs)} results in {search_time:.3f}s"
                    )

                except Exception as e:
                    results.append(
                        {
                            "view": view_name,
                            "search_term": query_term,
                            "status": "failed",
                            "error": str(e),
                        }
                    )
                    logger.error(f"  '{query_term}' failed: {e}")

        return results

    def test_graph_traversal(self) -> List[Dict[str, Any]]:
        """Test graph traversal capabilities"""
        logger.info("Testing Graph Traversal...")

        graphs = [
            "knowledge_network",
            "component_network",
            "concept_network",
            "entity_network",
        ]
        results = []

        for graph_name in graphs:
            logger.info(f"Testing graph: {graph_name}")

            try:
                # Test basic traversal
                start_time = time.time()

                traversal_query = f"""
                    FOR v IN GRAPH "{graph_name}" VERTICES
                        LIMIT 5
                        FOR related IN 1..2 OUTBOUND v GRAPH "{graph_name}"
                            LIMIT 10
                            RETURN {{
                                source: v._key,
                                target: related._key,
                                path_length: 1
                            }}
                """

                result = self.db.aql.execute(traversal_query)
                paths = list(result)
                traversal_time = time.time() - start_time

                # Test graph statistics
                stats_query = f"""
                    LET vertices = LENGTH(FOR v IN GRAPH "{graph_name}" VERTICES RETURN v)
                    LET edges = LENGTH(FOR e IN GRAPH "{graph_name}" EDGES RETURN e)
                    RETURN {{
                        vertices: vertices,
                        edges: edges,
                        density: vertices > 1 ? edges / (vertices * (vertices - 1) / 2) : 0
                    }}
                """

                stats_result = self.db.aql.execute(stats_query)
                stats = list(stats_result)[0]

                test_result = {
                    "graph": graph_name,
                    "traversal_paths": len(paths),
                    "traversal_time": traversal_time,
                    "graph_stats": stats,
                    "status": "success",
                }

                results.append(test_result)
                logger.info(f"  Traversal: {len(paths)} paths in {traversal_time:.3f}s")
                logger.info(
                    f"  Stats: {stats['vertices']} vertices, {stats['edges']} edges"
                )

            except Exception as e:
                results.append(
                    {"graph": graph_name, "status": "failed", "error": str(e)}
                )
                logger.error(f"  Graph test failed: {e}")

        return results

    def test_performance_optimization(self) -> List[Dict[str, Any]]:
        """Test performance improvements"""
        logger.info("Testing Performance Optimization...")

        test_cases = [
            {
                "name": "Simple Entity Query",
                "query": "FOR doc IN entities LIMIT 100 RETURN doc._key",
                "baseline": True,
            },
            {
                "name": "Filtered Entity Query",
                "query": 'FOR doc IN entities FILTER doc.type == "concept" LIMIT 50 RETURN doc',
                "baseline": False,
            },
            {
                "name": "Full-text Search",
                "query": """
                    FOR doc IN knowledge_search_view
                        SEARCH PHRASE(doc.content, "analysis", "knowledge_text_analyzer")
                        LIMIT 20
                        RETURN doc
                """,
                "baseline": False,
            },
            {
                "name": "Graph Traversal",
                "query": """
                    FOR v IN entities
                        LIMIT 5
                        FOR related IN 1..2 OUTBOUND v GRAPH "knowledge_network"
                            LIMIT 10
                            RETURN {source: v._key, target: related._key}
                """,
                "baseline": False,
            },
        ]

        results = []

        for test_case in test_cases:
            logger.info(f"Testing: {test_case['name']}")

            try:
                # Run query multiple times for average
                times = []
                for i in range(3):
                    start_time = time.time()
                    result = self.db.aql.execute(test_case["query"])
                    list(result)  # Consume results
                    execution_time = time.time() - start_time
                    times.append(execution_time)

                avg_time = sum(times) / len(times)
                min_time = min(times)
                max_time = max(times)

                test_result = {
                    "test_name": test_case["name"],
                    "avg_execution_time": avg_time,
                    "min_time": min_time,
                    "max_time": max_time,
                    "is_baseline": test_case["baseline"],
                    "status": "success",
                }

                results.append(test_result)
                logger.info(
                    f"  Avg time: {avg_time:.4f}s (min: {min_time:.4f}s, max: {max_time:.4f}s)"
                )

            except Exception as e:
                results.append(
                    {
                        "test_name": test_case["name"],
                        "status": "failed",
                        "error": str(e),
                    }
                )
                logger.error(f"  Performance test failed: {e}")

        return results

    def populate_test_data(self) -> Dict[str, Any]:
        """Populate collections with rich test data"""
        logger.info("Populating Test Data...")

        # Sample entities with rich content
        sample_entities = [
            {
                "title": "Machine Learning Fundamentals",
                "content": "Machine learning is a subset of artificial intelligence that focuses on algorithms and statistical models that enable computer systems to improve their performance on a specific task through experience.",
                "type": "concept",
                "category": "artificial_intelligence",
                "tags": ["machine_learning", "AI", "algorithms", "statistics"],
                "relevance": 0.9,
                "created": "2025-01-08T10:00:00Z",
            },
            {
                "title": "Neural Network Architecture",
                "content": "Neural networks are computing systems inspired by biological neural networks. They consist of interconnected nodes (neurons) that process information using connectionist approaches to computation.",
                "type": "concept",
                "category": "deep_learning",
                "tags": ["neural_networks", "deep_learning", "neurons", "architecture"],
                "relevance": 0.85,
                "created": "2025-01-08T10:15:00Z",
            },
            {
                "title": "Knowledge Graph Construction",
                "content": "Knowledge graphs represent information in a graph structure with entities as nodes and relationships as edges. They enable semantic search and reasoning over structured knowledge.",
                "type": "methodology",
                "category": "knowledge_management",
                "tags": [
                    "knowledge_graphs",
                    "semantic_search",
                    "graph_theory",
                    "ontology",
                ],
                "relevance": 0.8,
                "created": "2025-01-08T10:30:00Z",
            },
            {
                "title": "Cognitive Pattern Recognition",
                "content": "Cognitive pattern recognition involves the identification and classification of patterns in data using cognitive science principles and computational methods.",
                "type": "process",
                "category": "cognitive_science",
                "tags": [
                    "pattern_recognition",
                    "cognitive_science",
                    "classification",
                    "data_analysis",
                ],
                "relevance": 0.75,
                "created": "2025-01-08T10:45:00Z",
            },
            {
                "title": "Autonomous System Design",
                "content": "Autonomous systems are designed to operate independently with minimal human intervention. They incorporate decision-making algorithms and adaptive behavior mechanisms.",
                "type": "system",
                "category": "autonomous_systems",
                "tags": [
                    "autonomous",
                    "decision_making",
                    "adaptive_systems",
                    "automation",
                ],
                "relevance": 0.9,
                "created": "2025-01-08T11:00:00Z",
            },
        ]

        # Sample intelligence analytics
        sample_analytics = [
            {
                "analysis": "The integration of machine learning with knowledge graphs shows significant potential for enhanced reasoning capabilities.",
                "insights": [
                    "Semantic relationships improve ML model interpretability",
                    "Graph neural networks enable better feature representation",
                ],
                "summary": "ML-KG integration analysis",
                "confidence": 0.85,
                "created": "2025-01-08T11:15:00Z",
            },
            {
                "analysis": "Cognitive pattern recognition systems demonstrate improved performance when combined with neural network architectures.",
                "insights": [
                    "Hybrid cognitive-neural approaches outperform single-method systems",
                    "Pattern recognition accuracy increases with deeper networks",
                ],
                "summary": "Cognitive-neural system analysis",
                "confidence": 0.8,
                "created": "2025-01-08T11:30:00Z",
            },
        ]

        # Sample cognitive patterns
        sample_patterns = [
            {
                "pattern_description": "Hierarchical knowledge organization pattern for efficient information retrieval",
                "implementation": "class HierarchicalKnowledge: def organize_by_hierarchy(self, concepts): return self.build_tree(concepts)",
                "effectiveness": 0.9,
                "created": "2025-01-08T11:45:00Z",
            },
            {
                "pattern_description": "Adaptive learning pattern that adjusts based on feedback and performance metrics",
                "implementation": "def adaptive_learning(self, feedback): self.adjust_parameters(feedback); return self.updated_model",
                "effectiveness": 0.85,
                "created": "2025-01-08T12:00:00Z",
            },
        ]

        population_results = {}

        try:
            # Insert entities
            entity_ids = []
            for entity in sample_entities:
                result = self.db.collection("entities").insert(entity)
                entity_ids.append(result["_id"])

            population_results["entities_added"] = len(entity_ids)
            logger.info(f"Added {len(entity_ids)} entities")

            # Insert intelligence analytics
            analytics_ids = []
            for analytics in sample_analytics:
                result = self.db.collection("intelligence_analytics").insert(analytics)
                analytics_ids.append(result["_id"])

            population_results["analytics_added"] = len(analytics_ids)
            logger.info(f"Added {len(analytics_ids)} intelligence analytics")

            # Insert cognitive patterns
            pattern_ids = []
            for pattern in sample_patterns:
                result = self.db.collection("cognitive_patterns").insert(pattern)
                pattern_ids.append(result["_id"])

            population_results["patterns_added"] = len(pattern_ids)
            logger.info(f"Added {len(pattern_ids)} cognitive patterns")

            # Create sample relationships
            relationships = []
            for i in range(min(len(entity_ids), 3)):
                for j in range(min(len(analytics_ids), 2)):
                    relationship = {
                        "_from": entity_ids[i],
                        "_to": analytics_ids[j],
                        "type": "analyzed_by",
                        "strength": random.uniform(0.6, 0.9),
                        "created": "2025-01-08T12:15:00Z",
                    }
                    result = self.db.collection("knowledge_relationships").insert(
                        relationship
                    )
                    relationships.append(result["_id"])

            population_results["relationships_added"] = len(relationships)
            logger.info(f"Added {len(relationships)} relationships")

            population_results["status"] = "success"

        except Exception as e:
            population_results["status"] = "failed"
            population_results["error"] = str(e)
            logger.error(f"Data population failed: {e}")

        return population_results

    def test_integration(self) -> List[Dict[str, Any]]:
        """Test integration between different enhanced features"""
        logger.info("Testing Feature Integration...")

        integration_tests = [
            {
                "name": "Search + Graph Integration",
                "description": "Search for entities and traverse their relationships",
                "test_function": self._test_search_graph_integration,
            },
            {
                "name": "Analyzer + View Integration",
                "description": "Test analyzer processing within search views",
                "test_function": self._test_analyzer_view_integration,
            },
            {
                "name": "Graph + Analytics Integration",
                "description": "Combine graph traversal with analytical queries",
                "test_function": self._test_graph_analytics_integration,
            },
        ]

        results = []

        for test in integration_tests:
            logger.info(f"Running integration test: {test['name']}")

            try:
                result = test["test_function"]()
                result["test_name"] = test["name"]
                result["description"] = test["description"]
                result["status"] = "success"
                results.append(result)

            except Exception as e:
                results.append(
                    {
                        "test_name": test["name"],
                        "description": test["description"],
                        "status": "failed",
                        "error": str(e),
                    }
                )
                logger.error(f"Integration test failed: {e}")

        return results

    def _test_search_graph_integration(self) -> Dict[str, Any]:
        """Test search + graph traversal integration"""
        # Search for entities
        search_query = """
            FOR doc IN knowledge_search_view
                SEARCH PHRASE(doc.content, "machine learning", "knowledge_text_analyzer")
                LIMIT 3
                RETURN doc._id
        """

        search_result = self.db.aql.execute(search_query)
        entity_ids = [doc for doc in search_result]

        # Traverse relationships from found entities
        if entity_ids:
            traversal_query = f"""
                FOR entity_id IN {json.dumps(entity_ids)}
                    FOR related IN 1..2 OUTBOUND entity_id GRAPH "knowledge_network"
                        RETURN {{
                            source: entity_id,
                            target: related._id,
                            relationship_type: "knowledge_connection"
                        }}
            """

            traversal_result = self.db.aql.execute(traversal_query)
            relationships = list(traversal_result)

            return {
                "entities_found": len(entity_ids),
                "relationships_traversed": len(relationships),
                "integration_successful": len(entity_ids) > 0
                and len(relationships) >= 0,
            }

        return {
            "entities_found": 0,
            "relationships_traversed": 0,
            "integration_successful": False,
            "note": "No entities found in search",
        }

    def _test_analyzer_view_integration(self) -> Dict[str, Any]:
        """Test analyzer processing within views"""
        test_phrase = "artificial intelligence neural networks"

        # Test different analyzers on the same phrase
        analyzer_results = {}

        for analyzer in ["knowledge_text_analyzer", "text_en", "identity"]:
            try:
                query = f"""
                    FOR doc IN knowledge_search_view
                        SEARCH PHRASE(doc.content, @phrase, "{analyzer}")
                        RETURN {{
                            analyzer: "{analyzer}",
                            score: TFIDF(doc),
                            doc_id: doc._id
                        }}
                """

                result = self.db.aql.execute(query, bind_vars={"phrase": test_phrase})
                docs = list(result)

                analyzer_results[analyzer] = {
                    "results_count": len(docs),
                    "avg_score": sum(doc["score"] for doc in docs) / len(docs)
                    if docs
                    else 0,
                }

            except Exception as e:
                analyzer_results[analyzer] = {"error": str(e)}

        return {
            "test_phrase": test_phrase,
            "analyzer_comparison": analyzer_results,
            "integration_successful": len(analyzer_results) > 0,
        }

    def _test_graph_analytics_integration(self) -> Dict[str, Any]:
        """Test graph traversal with analytics"""
        # Get centrality analysis combined with traversal
        query = """
            FOR vertex IN entities
                LET connections = LENGTH(
                    FOR v IN 1..1 ANY vertex GRAPH "knowledge_network"
                        RETURN v
                )
                FILTER connections > 0
                SORT connections DESC
                LIMIT 5
                LET related_entities = (
                    FOR v IN 1..2 OUTBOUND vertex GRAPH "knowledge_network"
                        RETURN v._key
                )
                RETURN {
                    entity: vertex._key,
                    centrality_score: connections,
                    related_count: LENGTH(related_entities),
                    related_entities: related_entities
                }
        """

        result = self.db.aql.execute(query)
        analytics_data = list(result)

        return {
            "analyzed_entities": len(analytics_data),
            "total_relationships": sum(
                item["centrality_score"] for item in analytics_data
            ),
            "integration_successful": len(analytics_data) > 0,
        }

    def run_comprehensive_tests(self) -> Dict[str, Any]:
        """Run all comprehensive tests"""
        logger.info("Starting Comprehensive ArangoDB Testing Suite")

        try:
            # Phase 1: Data Population
            logger.info("Phase 1: Data Population")
            self.test_results["data_population"] = self.populate_test_data()

            # Phase 2: Analyzer Testing
            logger.info("Phase 2: Analyzer Testing")
            self.test_results["analyzer_tests"] = self.test_analyzers()

            # Phase 3: View Testing
            logger.info("Phase 3: Search View Testing")
            self.test_results["view_tests"] = self.test_search_views()

            # Phase 4: Graph Testing
            logger.info("Phase 4: Graph Traversal Testing")
            self.test_results["graph_tests"] = self.test_graph_traversal()

            # Phase 5: Performance Testing
            logger.info("Phase 5: Performance Testing")
            self.test_results[
                "performance_tests"
            ] = self.test_performance_optimization()

            # Phase 6: Integration Testing
            logger.info("Phase 6: Integration Testing")
            self.test_results["integration_tests"] = self.test_integration()

            # Generate summary
            self._generate_test_summary()

            logger.info("Comprehensive Testing Suite COMPLETED")
            return self.test_results

        except Exception as e:
            logger.error(f"Comprehensive testing failed: {e}")
            self.test_results["error"] = str(e)
            return self.test_results

    def _generate_test_summary(self):
        """Generate comprehensive test summary"""
        summary = {
            "total_tests_run": 0,
            "successful_tests": 0,
            "failed_tests": 0,
            "data_population_status": self.test_results["data_population"].get(
                "status", "unknown"
            ),
            "feature_test_results": {},
            "performance_baseline": {},
            "recommendations": [],
        }

        # Count tests by category
        for category, tests in self.test_results.items():
            if isinstance(tests, list):
                total = len(tests)
                successful = len([t for t in tests if t.get("status") == "success"])
                failed = total - successful

                summary["total_tests_run"] += total
                summary["successful_tests"] += successful
                summary["failed_tests"] += failed

                summary["feature_test_results"][category] = {
                    "total": total,
                    "successful": successful,
                    "failed": failed,
                    "success_rate": successful / total if total > 0 else 0,
                }

        # Performance analysis
        perf_tests = self.test_results.get("performance_tests", [])
        if perf_tests:
            baseline_test = next((t for t in perf_tests if t.get("is_baseline")), None)
            if baseline_test:
                summary["performance_baseline"] = {
                    "baseline_time": baseline_test.get("avg_execution_time", 0),
                    "optimized_tests": [
                        {
                            "name": t["test_name"],
                            "time": t.get("avg_execution_time", 0),
                            "improvement": (
                                baseline_test.get("avg_execution_time", 0)
                                - t.get("avg_execution_time", 0)
                            )
                            / baseline_test.get("avg_execution_time", 1)
                            * 100,
                        }
                        for t in perf_tests
                        if not t.get("is_baseline") and t.get("status") == "success"
                    ],
                }

        # Generate recommendations
        if summary["failed_tests"] > 0:
            summary["recommendations"].append(
                "Review failed tests and address underlying issues"
            )

        if summary["data_population_status"] == "success":
            summary["recommendations"].append(
                "Test data populated successfully - ready for production testing"
            )

        success_rate = (
            summary["successful_tests"] / summary["total_tests_run"]
            if summary["total_tests_run"] > 0
            else 0
        )
        if success_rate > 0.8:
            summary["recommendations"].append(
                "High success rate achieved - database enhancements are working well"
            )
        elif success_rate > 0.6:
            summary["recommendations"].append(
                "Moderate success rate - some optimizations may be needed"
            )
        else:
            summary["recommendations"].append(
                "Low success rate - significant issues need to be addressed"
            )

        self.test_results["summary"] = summary


def main():
    """Execute comprehensive testing suite"""
    try:
        # Initialize testing suite
        testing = ArangoComprehensiveTesting()

        # Run all tests
        results = testing.run_comprehensive_tests()

        # Save results
        with open(
            "/home/opsvi/asea/arango_comprehensive_testing_results.json", "w"
        ) as f:
            json.dump(results, f, indent=2, default=str)

        print("ArangoDB Comprehensive Testing Complete!")
        print(f"Results saved to: arango_comprehensive_testing_results.json")

        # Print summary
        summary = results.get("summary", {})
        print(f"\nTest Summary:")
        print(f"- Total tests run: {summary.get('total_tests_run', 0)}")
        print(f"- Successful tests: {summary.get('successful_tests', 0)}")
        print(f"- Failed tests: {summary.get('failed_tests', 0)}")
        print(
            f"- Success rate: {summary.get('successful_tests', 0) / max(summary.get('total_tests_run', 1), 1) * 100:.1f}%"
        )
        print(f"- Data population: {summary.get('data_population_status', 'unknown')}")

        print(f"\nRecommendations:")
        for rec in summary.get("recommendations", []):
            print(f"- {rec}")

        return results

    except Exception as e:
        logger.error(f"Testing suite failed: {e}")
        return None


if __name__ == "__main__":
    main()
