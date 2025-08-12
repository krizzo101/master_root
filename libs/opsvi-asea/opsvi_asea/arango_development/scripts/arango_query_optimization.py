#!/usr/bin/env python3
"""
ArangoDB Query Optimization & Caching Implementation
===================================================

Addresses the "low" query optimization effectiveness identified in monitoring:
1. Analyzes current query patterns and index usage
2. Implements optimized query patterns
3. Creates result caching layer
4. Validates performance improvements
"""

import json
import logging
import time
import hashlib
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from arango import ArangoClient

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ArangoQueryOptimizer:
    """Query optimization and caching implementation for ArangoDB"""

    def __init__(self):
        """Initialize with database connection and cache storage"""
        self.client = ArangoClient(hosts="http://127.0.0.1:8529")
        self.db = self.client.db(
            "asea_prod_db", username="root", password="arango_dev_password"
        )
        self.query_cache = {}
        self.cache_stats = {"hits": 0, "misses": 0, "total_queries": 0, "cache_size": 0}
        self.optimization_results = {
            "index_analysis": {},
            "query_optimizations": [],
            "caching_performance": {},
            "recommendations": [],
        }

    def analyze_index_usage(self) -> Dict[str, Any]:
        """Analyze current index usage patterns"""
        logger.info("Analyzing index usage patterns...")

        # Get all collections and their indexes
        collections = self.db.collections()
        index_analysis = {}

        for collection in collections:
            if collection["name"].startswith("_"):
                continue  # Skip system collections

            coll_obj = self.db.collection(collection["name"])
            indexes = coll_obj.indexes()

            # Analyze index types and usage
            index_types = {}
            for idx in indexes:
                idx_type = idx.get("type", "unknown")
                index_types[idx_type] = index_types.get(idx_type, 0) + 1

            # Get collection statistics
            try:
                stats = coll_obj.statistics()
                doc_count = stats.get("count", 0)
            except:
                doc_count = 0

            index_analysis[collection["name"]] = {
                "total_indexes": len(indexes),
                "index_types": index_types,
                "document_count": doc_count,
                "indexes_per_document": len(indexes) / max(doc_count, 1),
                "index_details": [
                    {
                        "type": idx.get("type"),
                        "fields": idx.get("fields", []),
                        "unique": idx.get("unique", False),
                        "sparse": idx.get("sparse", False),
                    }
                    for idx in indexes
                ],
            }

        logger.info(f"Analyzed {len(index_analysis)} collections")
        return index_analysis

    def identify_slow_queries(self) -> List[Dict[str, Any]]:
        """Identify and analyze slow query patterns"""
        logger.info("Identifying slow query patterns...")

        # Common query patterns that might be slow
        test_queries = [
            {
                "name": "unindexed_filter",
                "query": 'FOR doc IN entities FILTER doc.description LIKE "%learning%" RETURN doc',
                "issue": "Full text search without proper index",
            },
            {
                "name": "complex_join_without_index",
                "query": """
                    FOR entity IN entities
                        FOR rel IN knowledge_relationships
                            FILTER rel._from == entity._id
                            FOR target IN entities
                                FILTER target._id == rel._to
                                RETURN {entity: entity, target: target}
                """,
                "issue": "Complex join without optimized index usage",
            },
            {
                "name": "large_sort_without_index",
                "query": "FOR doc IN entities SORT doc.created DESC LIMIT 10 RETURN doc",
                "issue": "Sorting on non-indexed field",
            },
            {
                "name": "graph_traversal_without_limits",
                "query": """
                    FOR v IN entities
                        FOR related IN 1..5 OUTBOUND v knowledge_relationships
                            RETURN {source: v._key, target: related._key}
                """,
                "issue": "Deep traversal without proper limits",
            },
        ]

        slow_query_analysis = []

        for test in test_queries:
            try:
                # Analyze query execution plan
                explain_result = self.db.aql.explain(test["query"])
                plan = explain_result.get("plan", {})

                # Execute query and measure time
                start_time = time.time()
                result = self.db.aql.execute(test["query"])
                list(result)  # Consume results
                execution_time = time.time() - start_time

                analysis = {
                    "query_name": test["name"],
                    "potential_issue": test["issue"],
                    "execution_time": execution_time,
                    "estimated_cost": plan.get("estimatedCost", 0),
                    "estimated_items": plan.get("estimatedNrItems", 0),
                    "rules_applied": plan.get("rules", []),
                    "nodes": len(plan.get("nodes", [])),
                    "optimization_needed": execution_time > 0.05
                    or plan.get("estimatedCost", 0) > 100,
                }

                slow_query_analysis.append(analysis)
                logger.info(
                    f"Analyzed {test['name']}: {execution_time:.4f}s, cost: {plan.get('estimatedCost', 0):.2f}"
                )

            except Exception as e:
                logger.error(f"Failed to analyze query {test['name']}: {e}")
                slow_query_analysis.append(
                    {
                        "query_name": test["name"],
                        "error": str(e),
                        "optimization_needed": True,
                    }
                )

        return slow_query_analysis

    def create_optimized_indexes(self) -> List[Dict[str, Any]]:
        """Create optimized indexes based on analysis"""
        logger.info("Creating optimized indexes...")

        optimization_actions = []

        # Optimize entities collection
        try:
            entities_coll = self.db.collection("entities")

            # Index for type filtering (frequently used)
            entities_coll.add_hash_index(["type"], sparse=True)
            optimization_actions.append(
                {
                    "collection": "entities",
                    "index_type": "hash",
                    "fields": ["type"],
                    "purpose": "Optimize type-based filtering",
                }
            )

            # Index for category filtering
            entities_coll.add_hash_index(["category"], sparse=True)
            optimization_actions.append(
                {
                    "collection": "entities",
                    "index_type": "hash",
                    "fields": ["category"],
                    "purpose": "Optimize category-based filtering",
                }
            )

            # Index for relevance sorting
            entities_coll.add_skiplist_index(["relevance"], sparse=True)
            optimization_actions.append(
                {
                    "collection": "entities",
                    "index_type": "skiplist",
                    "fields": ["relevance"],
                    "purpose": "Optimize relevance-based sorting",
                }
            )

            # Compound index for type + category
            entities_coll.add_hash_index(["type", "category"], sparse=True)
            optimization_actions.append(
                {
                    "collection": "entities",
                    "index_type": "hash",
                    "fields": ["type", "category"],
                    "purpose": "Optimize compound filtering",
                }
            )

        except Exception as e:
            logger.error(f"Failed to optimize entities indexes: {e}")

        # Optimize intelligence_analytics collection
        try:
            analytics_coll = self.db.collection("intelligence_analytics")

            # Index for confidence-based queries
            analytics_coll.add_skiplist_index(["confidence"], sparse=True)
            optimization_actions.append(
                {
                    "collection": "intelligence_analytics",
                    "index_type": "skiplist",
                    "fields": ["confidence"],
                    "purpose": "Optimize confidence-based filtering and sorting",
                }
            )

        except Exception as e:
            logger.error(f"Failed to optimize analytics indexes: {e}")

        # Optimize knowledge_relationships for better joins
        try:
            rel_coll = self.db.collection("knowledge_relationships")

            # Index for relationship type filtering
            rel_coll.add_hash_index(["type"], sparse=True)
            optimization_actions.append(
                {
                    "collection": "knowledge_relationships",
                    "index_type": "hash",
                    "fields": ["type"],
                    "purpose": "Optimize relationship type filtering",
                }
            )

            # Index for strength-based queries
            rel_coll.add_skiplist_index(["strength"], sparse=True)
            optimization_actions.append(
                {
                    "collection": "knowledge_relationships",
                    "index_type": "skiplist",
                    "fields": ["strength"],
                    "purpose": "Optimize strength-based filtering and sorting",
                }
            )

        except Exception as e:
            logger.error(f"Failed to optimize relationships indexes: {e}")

        logger.info(f"Created {len(optimization_actions)} optimized indexes")
        return optimization_actions

    def implement_query_cache(self, ttl_seconds: int = 300) -> Dict[str, Any]:
        """Implement query result caching with TTL"""
        logger.info(f"Implementing query cache with {ttl_seconds}s TTL...")

        def cached_query(
            query: str,
            bind_vars: Optional[Dict] = None,
            cache_key: Optional[str] = None,
        ) -> Any:
            """Execute query with caching"""
            # Generate cache key
            if cache_key is None:
                cache_content = query + str(bind_vars or {})
                cache_key = hashlib.md5(cache_content.encode()).hexdigest()

            # Check cache
            current_time = time.time()
            if cache_key in self.query_cache:
                cached_result, timestamp = self.query_cache[cache_key]
                if current_time - timestamp < ttl_seconds:
                    self.cache_stats["hits"] += 1
                    self.cache_stats["total_queries"] += 1
                    return cached_result
                else:
                    # Expired cache entry
                    del self.query_cache[cache_key]

            # Cache miss - execute query
            self.cache_stats["misses"] += 1
            self.cache_stats["total_queries"] += 1

            result = self.db.aql.execute(query, bind_vars=bind_vars)
            result_data = list(result)

            # Store in cache
            self.query_cache[cache_key] = (result_data, current_time)
            self.cache_stats["cache_size"] = len(self.query_cache)

            return result_data

        # Store the cached_query function for use
        self.cached_query = cached_query

        return {
            "cache_implementation": "in_memory_ttl",
            "ttl_seconds": ttl_seconds,
            "initial_cache_size": 0,
            "status": "implemented",
        }

    def create_optimized_query_patterns(self) -> List[Dict[str, Any]]:
        """Create optimized versions of common query patterns"""
        logger.info("Creating optimized query patterns...")

        optimized_patterns = [
            {
                "name": "optimized_entity_search",
                "description": "Fast entity search with proper indexing",
                "original_pattern": "FOR doc IN entities FILTER doc.type == @type RETURN doc",
                "optimized_query": """
                    FOR doc IN entities
                        FILTER doc.type == @type
                        SORT doc.relevance DESC
                        LIMIT @limit
                        RETURN {
                            id: doc._id,
                            title: doc.title,
                            type: doc.type,
                            category: doc.category,
                            relevance: doc.relevance
                        }
                """,
                "improvements": [
                    "Added relevance sorting",
                    "Limited result set",
                    "Reduced returned fields",
                ],
            },
            {
                "name": "optimized_relationship_analysis",
                "description": "Efficient relationship traversal with strength filtering",
                "original_pattern": "FOR v IN entities FOR r IN knowledge_relationships FILTER r._from == v._id RETURN r",
                "optimized_query": """
                    FOR vertex IN entities
                        FILTER vertex.type == @vertex_type
                        LIMIT @vertex_limit
                        FOR edge IN knowledge_relationships
                            FILTER edge._from == vertex._id AND edge.strength >= @min_strength
                            SORT edge.strength DESC
                            LIMIT @edge_limit
                            RETURN {
                                source: vertex._key,
                                target: edge._to,
                                relationship_type: edge.type,
                                strength: edge.strength
                            }
                """,
                "improvements": [
                    "Strength-based filtering",
                    "Type-based vertex filtering",
                    "Proper limits",
                    "Strength sorting",
                ],
            },
            {
                "name": "optimized_graph_centrality",
                "description": "Efficient centrality calculation with limits",
                "original_pattern": "FOR v IN entities LET c = LENGTH(FOR r IN knowledge_relationships FILTER r._from == v._id OR r._to == v._id RETURN r) RETURN {v, c}",
                "optimized_query": """
                    FOR vertex IN entities
                        FILTER vertex.type IN @allowed_types
                        LET outbound = LENGTH(
                            FOR edge IN knowledge_relationships
                                FILTER edge._from == vertex._id AND edge.strength >= @min_strength
                                RETURN edge
                        )
                        LET inbound = LENGTH(
                            FOR edge IN knowledge_relationships
                                FILTER edge._to == vertex._id AND edge.strength >= @min_strength
                                RETURN edge
                        )
                        LET centrality = outbound + inbound
                        FILTER centrality >= @min_connections
                        SORT centrality DESC
                        LIMIT @limit
                        RETURN {
                            entity: vertex._key,
                            entity_type: vertex.type,
                            outbound_connections: outbound,
                            inbound_connections: inbound,
                            centrality_score: centrality
                        }
                """,
                "improvements": [
                    "Type filtering",
                    "Strength filtering",
                    "Minimum connection threshold",
                    "Proper sorting and limits",
                ],
            },
            {
                "name": "optimized_search_with_analytics",
                "description": "Combined search and analytics with caching",
                "original_pattern": "FOR doc IN knowledge_search_view SEARCH ... RETURN doc",
                "optimized_query": """
                    FOR doc IN knowledge_search_view
                        SEARCH PHRASE(doc.content, @search_term, "knowledge_text_analyzer") OR
                               PHRASE(doc.title, @search_term, "text_en")
                        FILTER doc.relevance >= @min_relevance
                        SORT TFIDF(doc) DESC
                        LIMIT @limit
                        LET entity = DOCUMENT(doc._id)
                        LET connections = LENGTH(
                            FOR edge IN knowledge_relationships
                                FILTER edge._from == doc._id OR edge._to == doc._id
                                RETURN edge
                        )
                        RETURN {
                            id: doc._id,
                            collection: PARSE_IDENTIFIER(doc._id).collection,
                            title: doc.title,
                            content_preview: LEFT(doc.content, 200),
                            relevance: doc.relevance,
                            search_score: TFIDF(doc),
                            connection_count: connections,
                            combined_score: TFIDF(doc) + (connections * 0.1)
                        }
                """,
                "improvements": [
                    "Multi-field search",
                    "Relevance filtering",
                    "Connection enrichment",
                    "Combined scoring",
                ],
            },
        ]

        # Test each optimized pattern
        pattern_results = []

        for pattern in optimized_patterns:
            try:
                # Test with sample parameters
                test_params = self._get_test_params_for_pattern(pattern["name"])

                start_time = time.time()
                result = self.db.aql.execute(
                    pattern["optimized_query"], bind_vars=test_params
                )
                data = list(result)
                execution_time = time.time() - start_time

                pattern_result = {
                    "pattern_name": pattern["name"],
                    "description": pattern["description"],
                    "test_execution_time": execution_time,
                    "test_result_count": len(data),
                    "improvements": pattern["improvements"],
                    "status": "validated",
                    "sample_result": data[:2] if data else None,
                }

                pattern_results.append(pattern_result)
                logger.info(
                    f"✓ {pattern['name']}: {execution_time:.4f}s, {len(data)} results"
                )

            except Exception as e:
                pattern_results.append(
                    {
                        "pattern_name": pattern["name"],
                        "description": pattern["description"],
                        "status": "failed",
                        "error": str(e),
                    }
                )
                logger.error(f"✗ {pattern['name']} failed: {e}")

        return pattern_results

    def _get_test_params_for_pattern(self, pattern_name: str) -> Dict[str, Any]:
        """Get test parameters for query patterns"""
        param_sets = {
            "optimized_entity_search": {"type": "concept", "limit": 10},
            "optimized_relationship_analysis": {
                "vertex_type": "concept",
                "vertex_limit": 5,
                "min_strength": 0.5,
                "edge_limit": 10,
            },
            "optimized_graph_centrality": {
                "allowed_types": ["concept", "methodology"],
                "min_strength": 0.3,
                "min_connections": 1,
                "limit": 10,
            },
            "optimized_search_with_analytics": {
                "search_term": "machine learning",
                "min_relevance": 0.5,
                "limit": 5,
            },
        }

        return param_sets.get(pattern_name, {})

    def test_caching_performance(self) -> Dict[str, Any]:
        """Test caching performance improvements"""
        logger.info("Testing caching performance...")

        # Test queries for caching
        test_queries = [
            {
                "name": "frequent_entity_lookup",
                "query": "FOR doc IN entities FILTER doc.type == @type SORT doc.relevance DESC LIMIT 10 RETURN doc",
                "params": {"type": "concept"},
            },
            {
                "name": "common_search",
                "query": """
                    FOR doc IN knowledge_search_view
                        SEARCH PHRASE(doc.content, @term, "knowledge_text_analyzer")
                        LIMIT 5
                        RETURN {id: doc._id, title: doc.title, score: TFIDF(doc)}
                """,
                "params": {"term": "intelligence"},
            },
        ]

        caching_results = []

        for test in test_queries:
            # Test without cache (first run)
            start_time = time.time()
            result = self.db.aql.execute(test["query"], bind_vars=test["params"])
            list(result)
            uncached_time = time.time() - start_time

            # Test with cache (second run)
            start_time = time.time()
            cached_result = self.cached_query(test["query"], test["params"])
            cached_time = time.time() - start_time

            # Test cache hit (third run)
            start_time = time.time()
            cached_hit_result = self.cached_query(test["query"], test["params"])
            cache_hit_time = time.time() - start_time

            improvement = (
                ((uncached_time - cache_hit_time) / uncached_time * 100)
                if uncached_time > 0
                else 0
            )

            caching_result = {
                "query_name": test["name"],
                "uncached_time": uncached_time,
                "cached_miss_time": cached_time,
                "cache_hit_time": cache_hit_time,
                "performance_improvement": improvement,
                "cache_effectiveness": cache_hit_time < uncached_time,
            }

            caching_results.append(caching_result)
            logger.info(
                f"✓ {test['name']}: {improvement:.1f}% improvement with caching"
            )

        return {
            "caching_tests": caching_results,
            "cache_stats": self.cache_stats,
            "overall_improvement": sum(
                r["performance_improvement"] for r in caching_results
            )
            / len(caching_results)
            if caching_results
            else 0,
        }

    def generate_optimization_recommendations(self) -> List[str]:
        """Generate specific optimization recommendations"""
        recommendations = []

        # Based on index analysis
        index_analysis = self.optimization_results.get("index_analysis", {})
        for collection_name, analysis in index_analysis.items():
            if analysis["document_count"] > 100 and analysis["total_indexes"] < 3:
                recommendations.append(
                    f"Consider adding more indexes to {collection_name} (only {analysis['total_indexes']} indexes for {analysis['document_count']} documents)"
                )

        # Based on query patterns
        if hasattr(self, "cache_stats") and self.cache_stats["total_queries"] > 0:
            hit_rate = (
                self.cache_stats["hits"] / self.cache_stats["total_queries"] * 100
            )
            if hit_rate < 50:
                recommendations.append(
                    f"Cache hit rate is low ({hit_rate:.1f}%) - consider increasing cache TTL or identifying more cacheable queries"
                )

        # General recommendations
        recommendations.extend(
            [
                "Implement query result pagination for large result sets",
                "Use LIMIT clauses in all production queries to prevent resource exhaustion",
                "Monitor query execution plans regularly to identify optimization opportunities",
                "Consider implementing query statistics collection for trend analysis",
                "Use compound indexes for frequently combined filter conditions",
                "Implement query timeout limits for long-running operations",
            ]
        )

        return recommendations

    def run_comprehensive_optimization(self) -> Dict[str, Any]:
        """Run comprehensive query optimization analysis and implementation"""
        logger.info("Running comprehensive query optimization...")

        try:
            # Phase 1: Analysis
            logger.info("Phase 1: Index Usage Analysis")
            self.optimization_results["index_analysis"] = self.analyze_index_usage()

            logger.info("Phase 2: Slow Query Identification")
            slow_queries = self.identify_slow_queries()

            # Phase 2: Optimization
            logger.info("Phase 3: Index Optimization")
            index_optimizations = self.create_optimized_indexes()

            logger.info("Phase 4: Caching Implementation")
            caching_impl = self.implement_query_cache()

            logger.info("Phase 5: Optimized Query Patterns")
            self.optimization_results[
                "query_optimizations"
            ] = self.create_optimized_query_patterns()

            # Phase 3: Validation
            logger.info("Phase 6: Caching Performance Testing")
            self.optimization_results[
                "caching_performance"
            ] = self.test_caching_performance()

            logger.info("Phase 7: Recommendation Generation")
            self.optimization_results[
                "recommendations"
            ] = self.generate_optimization_recommendations()

            # Summary
            optimization_summary = {
                "optimization_timestamp": datetime.now().isoformat(),
                "phases_completed": 7,
                "indexes_analyzed": len(self.optimization_results["index_analysis"]),
                "indexes_created": len(index_optimizations),
                "slow_queries_identified": len(
                    [q for q in slow_queries if q.get("optimization_needed")]
                ),
                "query_patterns_optimized": len(
                    self.optimization_results["query_optimizations"]
                ),
                "caching_implemented": True,
                "cache_hit_rate": self.cache_stats["hits"]
                / max(self.cache_stats["total_queries"], 1)
                * 100,
                "recommendations_generated": len(
                    self.optimization_results["recommendations"]
                ),
                "overall_status": "completed",
            }

            self.optimization_results["summary"] = optimization_summary
            self.optimization_results["slow_queries"] = slow_queries
            self.optimization_results["index_optimizations"] = index_optimizations
            self.optimization_results["caching_implementation"] = caching_impl

            logger.info("Comprehensive optimization completed successfully")
            return self.optimization_results

        except Exception as e:
            logger.error(f"Optimization failed: {e}")
            self.optimization_results["error"] = str(e)
            return self.optimization_results


def main():
    """Execute comprehensive query optimization"""
    try:
        # Initialize optimizer
        optimizer = ArangoQueryOptimizer()

        # Run comprehensive optimization
        results = optimizer.run_comprehensive_optimization()

        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"/home/opsvi/asea/arango_optimization_results_{timestamp}.json"

        with open(filename, "w") as f:
            json.dump(results, f, indent=2, default=str)

        print("ArangoDB Query Optimization Complete!")
        print(f"Results saved to: {filename}")

        # Print summary
        summary = results.get("summary", {})
        print(f"\nOptimization Summary:")
        print(f"- Phases completed: {summary.get('phases_completed', 0)}/7")
        print(f"- Collections analyzed: {summary.get('indexes_analyzed', 0)}")
        print(f"- Indexes created: {summary.get('indexes_created', 0)}")
        print(
            f"- Query patterns optimized: {summary.get('query_patterns_optimized', 0)}"
        )
        print(f"- Cache hit rate: {summary.get('cache_hit_rate', 0):.1f}%")
        print(f"- Status: {summary.get('overall_status', 'unknown')}")

        # Print key recommendations
        recommendations = results.get("recommendations", [])
        if recommendations:
            print(f"\nKey Recommendations:")
            for i, rec in enumerate(recommendations[:5], 1):
                print(f"{i}. {rec}")

        return results

    except Exception as e:
        logger.error(f"Query optimization failed: {e}")
        return None


if __name__ == "__main__":
    main()
