#!/usr/bin/env python3
"""
ArangoDB Testing Fixes
======================

Fixes the identified issues in our comprehensive testing:
1. View search syntax corrections
2. Graph traversal syntax corrections
3. Optimized query patterns
"""

import json
import logging
import time
from arango import ArangoClient

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ArangoTestingFixes:
    """Fix and validate ArangoDB enhanced features"""

    def __init__(self):
        """Initialize with database connection"""
        self.client = ArangoClient(hosts="http://127.0.0.1:8529")
        self.db = self.client.db(
            "asea_prod_db", username="root", password="arango_dev_password"
        )

    def fix_and_test_views(self):
        """Fix and test search view functionality"""
        logger.info("Fixing and testing search views...")

        # Corrected view search queries
        test_queries = [
            {
                "name": "Simple content search",
                "query": """
                    FOR doc IN knowledge_search_view
                        SEARCH PHRASE(doc.content, @term, "knowledge_text_analyzer")
                        SORT TFIDF(doc) DESC
                        LIMIT 5
                        RETURN {
                            id: doc._id,
                            collection: PARSE_IDENTIFIER(doc._id).collection,
                            score: TFIDF(doc),
                            content_preview: LEFT(doc.content, 100)
                        }
                """,
                "term": "machine learning",
            },
            {
                "name": "Title search",
                "query": """
                    FOR doc IN knowledge_search_view
                        SEARCH PHRASE(doc.title, @term, "text_en")
                        SORT TFIDF(doc) DESC
                        LIMIT 5
                        RETURN {
                            id: doc._id,
                            title: doc.title,
                            score: TFIDF(doc)
                        }
                """,
                "term": "Neural Network",
            },
            {
                "name": "Multi-field search",
                "query": """
                    FOR doc IN knowledge_search_view
                        SEARCH PHRASE(doc.content, @term, "knowledge_text_analyzer") OR
                               PHRASE(doc.title, @term, "text_en")
                        SORT TFIDF(doc) DESC
                        LIMIT 5
                        RETURN {
                            id: doc._id,
                            collection: PARSE_IDENTIFIER(doc._id).collection,
                            title: doc.title,
                            score: TFIDF(doc)
                        }
                """,
                "term": "intelligence",
            },
        ]

        results = []

        for test in test_queries:
            try:
                start_time = time.time()
                result = self.db.aql.execute(
                    test["query"], bind_vars={"term": test["term"]}
                )
                docs = list(result)
                search_time = time.time() - start_time

                test_result = {
                    "test_name": test["name"],
                    "search_term": test["term"],
                    "results_count": len(docs),
                    "search_time": search_time,
                    "sample_results": docs[:3],
                    "status": "success",
                }

                results.append(test_result)
                logger.info(
                    f"✓ {test['name']}: {len(docs)} results in {search_time:.3f}s"
                )

            except Exception as e:
                results.append(
                    {
                        "test_name": test["name"],
                        "search_term": test["term"],
                        "status": "failed",
                        "error": str(e),
                    }
                )
                logger.error(f"✗ {test['name']} failed: {e}")

        return results

    def fix_and_test_graphs(self):
        """Fix and test graph traversal functionality"""
        logger.info("Fixing and testing graph traversal...")

        # Corrected graph traversal queries
        test_queries = [
            {
                "name": "Basic graph traversal",
                "query": """
                    FOR v IN entities
                        LIMIT 3
                        FOR related IN 1..2 OUTBOUND v knowledge_relationships
                            LIMIT 5
                            RETURN {
                                source: v._key,
                                target: related._key,
                                source_type: v.type,
                                target_type: related.type
                            }
                """,
            },
            {
                "name": "Named graph traversal",
                "query": """
                    FOR v IN entities
                        LIMIT 3
                        FOR related IN 1..2 OUTBOUND v GRAPH "knowledge_network"
                            LIMIT 5
                            RETURN {
                                source: v._key,
                                target: related._key,
                                path_length: 1
                            }
                """,
            },
            {
                "name": "Graph statistics",
                "query": """
                    LET vertices = LENGTH(entities)
                    LET edges = LENGTH(knowledge_relationships)
                    RETURN {
                        graph: "knowledge_network",
                        vertices: vertices,
                        edges: edges,
                        density: vertices > 1 ? edges / (vertices * (vertices - 1) / 2) : 0
                    }
                """,
            },
        ]

        results = []

        for test in test_queries:
            try:
                start_time = time.time()
                result = self.db.aql.execute(test["query"])
                data = list(result)
                execution_time = time.time() - start_time

                test_result = {
                    "test_name": test["name"],
                    "results_count": len(data),
                    "execution_time": execution_time,
                    "sample_results": data[:3],
                    "status": "success",
                }

                results.append(test_result)
                logger.info(
                    f"✓ {test['name']}: {len(data)} results in {execution_time:.3f}s"
                )

            except Exception as e:
                results.append(
                    {"test_name": test["name"], "status": "failed", "error": str(e)}
                )
                logger.error(f"✗ {test['name']} failed: {e}")

        return results

    def test_enhanced_search_patterns(self):
        """Test enhanced search patterns with our populated data"""
        logger.info("Testing enhanced search patterns...")

        # Test patterns that should work with our populated data
        test_patterns = [
            {
                "name": "Fuzzy search with ngram analyzer",
                "query": """
                    FOR doc IN knowledge_search_view
                        SEARCH ANALYZER(BOOST(PHRASE(doc.content, @term), 2.0), "ngram_analyzer")
                        SORT TFIDF(doc) DESC
                        LIMIT 3
                        RETURN {
                            id: doc._id,
                            title: doc.title,
                            score: TFIDF(doc),
                            content: LEFT(doc.content, 150)
                        }
                """,
                "term": "learning",
            },
            {
                "name": "Combined analyzer search",
                "query": """
                    FOR doc IN knowledge_search_view
                        SEARCH PHRASE(doc.content, @term, "knowledge_text_analyzer") OR
                               PHRASE(doc.content, @term, "text_en")
                        SORT TFIDF(doc) DESC
                        LIMIT 5
                        RETURN {
                            id: doc._id,
                            collection: PARSE_IDENTIFIER(doc._id).collection,
                            score: TFIDF(doc)
                        }
                """,
                "term": "neural",
            },
            {
                "name": "Category-based search",
                "query": """
                    FOR doc IN entities
                        FILTER doc.category == @category
                        SORT doc.relevance DESC
                        LIMIT 5
                        RETURN {
                            id: doc._id,
                            title: doc.title,
                            category: doc.category,
                            relevance: doc.relevance
                        }
                """,
                "category": "artificial_intelligence",
            },
        ]

        results = []

        for test in test_patterns:
            try:
                start_time = time.time()
                bind_vars = {
                    k: v for k, v in test.items() if k not in ["name", "query"]
                }
                result = self.db.aql.execute(test["query"], bind_vars=bind_vars)
                data = list(result)
                execution_time = time.time() - start_time

                test_result = {
                    "test_name": test["name"],
                    "results_count": len(data),
                    "execution_time": execution_time,
                    "sample_results": data,
                    "status": "success",
                }

                results.append(test_result)
                logger.info(
                    f"✓ {test['name']}: {len(data)} results in {execution_time:.3f}s"
                )

            except Exception as e:
                results.append(
                    {"test_name": test["name"], "status": "failed", "error": str(e)}
                )
                logger.error(f"✗ {test['name']} failed: {e}")

        return results

    def test_centrality_analysis(self):
        """Test centrality analysis with corrected queries"""
        logger.info("Testing centrality analysis...")

        try:
            # Corrected centrality query
            query = """
                FOR vertex IN entities
                    LET outbound_connections = LENGTH(
                        FOR v IN 1..1 OUTBOUND vertex knowledge_relationships
                            RETURN v
                    )
                    LET inbound_connections = LENGTH(
                        FOR v IN 1..1 INBOUND vertex knowledge_relationships
                            RETURN v
                    )
                    LET total_connections = outbound_connections + inbound_connections
                    FILTER total_connections > 0
                    SORT total_connections DESC
                    LIMIT 10
                    RETURN {
                        entity: vertex,
                        outbound_connections: outbound_connections,
                        inbound_connections: inbound_connections,
                        total_connections: total_connections,
                        centrality_score: total_connections
                    }
            """

            start_time = time.time()
            result = self.db.aql.execute(query)
            centrality_data = list(result)
            execution_time = time.time() - start_time

            logger.info(
                f"✓ Centrality analysis: {len(centrality_data)} entities analyzed in {execution_time:.3f}s"
            )

            return {
                "test_name": "Centrality Analysis",
                "entities_analyzed": len(centrality_data),
                "execution_time": execution_time,
                "top_entities": centrality_data[:5],
                "status": "success",
            }

        except Exception as e:
            logger.error(f"✗ Centrality analysis failed: {e}")
            return {
                "test_name": "Centrality Analysis",
                "status": "failed",
                "error": str(e),
            }

    def validate_all_enhancements(self):
        """Validate all database enhancements are working"""
        logger.info("Validating all database enhancements...")

        validation_results = {
            "analyzers": self._validate_analyzers(),
            "views": self._validate_views(),
            "graphs": self._validate_graphs(),
            "indexes": self._validate_indexes(),
            "collections": self._validate_collections(),
        }

        return validation_results

    def _validate_analyzers(self):
        """Validate all custom analyzers exist and work"""
        try:
            analyzers = self.db.analyzers()
            custom_analyzers = [
                a
                for a in analyzers
                if a["name"]
                in ["knowledge_text_analyzer", "code_analyzer", "ngram_analyzer"]
            ]

            # Test each analyzer
            test_results = []
            for analyzer in custom_analyzers:
                try:
                    query = f"RETURN TOKENS('test text', '{analyzer['name']}')"
                    result = self.db.aql.execute(query)
                    tokens = list(result)[0]
                    test_results.append(
                        {
                            "analyzer": analyzer["name"],
                            "status": "working",
                            "token_count": len(tokens),
                        }
                    )
                except Exception as e:
                    test_results.append(
                        {
                            "analyzer": analyzer["name"],
                            "status": "failed",
                            "error": str(e),
                        }
                    )

            return {
                "total_analyzers": len(custom_analyzers),
                "analyzer_tests": test_results,
                "status": "validated",
            }

        except Exception as e:
            return {"status": "failed", "error": str(e)}

    def _validate_views(self):
        """Validate all search views exist and are functional"""
        try:
            views = self.db.views()
            custom_views = [
                v
                for v in views
                if v["name"] in ["knowledge_search_view", "code_search_view"]
            ]

            view_tests = []
            for view in custom_views:
                try:
                    query = f"FOR doc IN {view['name']} LIMIT 1 RETURN doc"
                    result = self.db.aql.execute(query)
                    docs = list(result)
                    view_tests.append(
                        {
                            "view": view["name"],
                            "status": "accessible",
                            "has_data": len(docs) > 0,
                        }
                    )
                except Exception as e:
                    view_tests.append(
                        {"view": view["name"], "status": "failed", "error": str(e)}
                    )

            return {
                "total_views": len(custom_views),
                "view_tests": view_tests,
                "status": "validated",
            }

        except Exception as e:
            return {"status": "failed", "error": str(e)}

    def _validate_graphs(self):
        """Validate all named graphs exist and are functional"""
        try:
            graphs = self.db.graphs()
            graph_names = [g["name"] for g in graphs]
            expected_graphs = [
                "knowledge_network",
                "component_network",
                "concept_network",
                "entity_network",
            ]

            graph_tests = []
            for graph_name in expected_graphs:
                if graph_name in graph_names:
                    try:
                        # Test basic graph access
                        query = (
                            f'FOR v IN GRAPH "{graph_name}" VERTICES LIMIT 1 RETURN v'
                        )
                        result = self.db.aql.execute(query)
                        vertices = list(result)

                        graph_tests.append(
                            {
                                "graph": graph_name,
                                "status": "accessible",
                                "has_vertices": len(vertices) > 0,
                            }
                        )
                    except Exception as e:
                        graph_tests.append(
                            {"graph": graph_name, "status": "failed", "error": str(e)}
                        )
                else:
                    graph_tests.append({"graph": graph_name, "status": "missing"})

            return {
                "expected_graphs": len(expected_graphs),
                "found_graphs": len(
                    [g for g in graph_tests if g["status"] == "accessible"]
                ),
                "graph_tests": graph_tests,
                "status": "validated",
            }

        except Exception as e:
            return {"status": "failed", "error": str(e)}

    def _validate_indexes(self):
        """Validate performance indexes are in place"""
        try:
            edge_collections = [
                "knowledge_relationships",
                "component_relationships",
                "concept_relations",
                "relations",
            ]
            index_summary = []

            for collection_name in edge_collections:
                try:
                    collection = self.db.collection(collection_name)
                    indexes = collection.indexes()

                    # Count different types of indexes
                    index_types = {}
                    for idx in indexes:
                        idx_type = idx.get("type", "unknown")
                        index_types[idx_type] = index_types.get(idx_type, 0) + 1

                    index_summary.append(
                        {
                            "collection": collection_name,
                            "total_indexes": len(indexes),
                            "index_types": index_types,
                            "status": "validated",
                        }
                    )

                except Exception as e:
                    index_summary.append(
                        {
                            "collection": collection_name,
                            "status": "failed",
                            "error": str(e),
                        }
                    )

            return {
                "collections_checked": len(edge_collections),
                "index_summary": index_summary,
                "status": "validated",
            }

        except Exception as e:
            return {"status": "failed", "error": str(e)}

    def _validate_collections(self):
        """Validate key collections have data"""
        try:
            key_collections = [
                "entities",
                "intelligence_analytics",
                "cognitive_patterns",
                "knowledge_relationships",
            ]
            collection_summary = []

            for collection_name in key_collections:
                try:
                    collection = self.db.collection(collection_name)
                    count = collection.count()

                    collection_summary.append(
                        {
                            "collection": collection_name,
                            "document_count": count,
                            "has_data": count > 0,
                            "status": "validated",
                        }
                    )

                except Exception as e:
                    collection_summary.append(
                        {
                            "collection": collection_name,
                            "status": "failed",
                            "error": str(e),
                        }
                    )

            return {
                "collections_checked": len(key_collections),
                "collection_summary": collection_summary,
                "total_documents": sum(
                    c.get("document_count", 0) for c in collection_summary
                ),
                "status": "validated",
            }

        except Exception as e:
            return {"status": "failed", "error": str(e)}

    def run_comprehensive_fixes_and_tests(self):
        """Run all fixes and comprehensive tests"""
        logger.info("Running comprehensive fixes and validation tests...")

        results = {
            "validation": self.validate_all_enhancements(),
            "view_fixes": self.fix_and_test_views(),
            "graph_fixes": self.fix_and_test_graphs(),
            "enhanced_search": self.test_enhanced_search_patterns(),
            "centrality_analysis": self.test_centrality_analysis(),
            "timestamp": time.time(),
        }

        # Generate summary
        total_tests = 0
        successful_tests = 0

        for category, tests in results.items():
            if isinstance(tests, list):
                total_tests += len(tests)
                successful_tests += len(
                    [t for t in tests if t.get("status") == "success"]
                )
            elif isinstance(tests, dict) and tests.get("status") in [
                "success",
                "validated",
            ]:
                total_tests += 1
                successful_tests += 1

        results["summary"] = {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "success_rate": successful_tests / total_tests if total_tests > 0 else 0,
            "status": "completed",
        }

        logger.info(
            f"Comprehensive testing completed: {successful_tests}/{total_tests} tests successful"
        )

        return results


def main():
    """Execute comprehensive fixes and testing"""
    try:
        # Initialize testing fixes
        testing = ArangoTestingFixes()

        # Run all fixes and tests
        results = testing.run_comprehensive_fixes_and_tests()

        # Save results
        with open("/home/opsvi/asea/arango_testing_fixes_results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)

        print("ArangoDB Testing Fixes Complete!")
        print("Results saved to: arango_testing_fixes_results.json")

        # Print summary
        summary = results.get("summary", {})
        print("\nFixed Test Summary:")
        print(f"- Total tests: {summary.get('total_tests', 0)}")
        print(f"- Successful tests: {summary.get('successful_tests', 0)}")
        print(f"- Success rate: {summary.get('success_rate', 0) * 100:.1f}%")

        # Print validation summary
        validation = results.get("validation", {})
        print("\nValidation Summary:")
        for component, result in validation.items():
            status = result.get("status", "unknown")
            print(f"- {component}: {status}")

        return results

    except Exception as e:
        logger.error(f"Testing fixes failed: {e}")
        return None


if __name__ == "__main__":
    main()
