#!/usr/bin/env python3
"""
ArangoDB Performance Monitor
===========================

Monitors and tracks performance of enhanced ArangoDB capabilities:
- Search view performance
- Graph traversal optimization
- Query execution metrics
- Resource utilization tracking
- Performance trend analysis
"""

import json
import logging
import time
import statistics
from datetime import datetime
from typing import Dict, List, Any
from arango import ArangoClient

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ArangoPerformanceMonitor:
    """Performance monitoring and optimization for enhanced ArangoDB"""

    def __init__(self):
        """Initialize with database connection"""
        self.client = ArangoClient(hosts="http://127.0.0.1:8529")
        self.db = self.client.db(
            "asea_prod_db", username="root", password="arango_dev_password"
        )
        self.performance_metrics = {
            "search_performance": [],
            "graph_performance": [],
            "analyzer_performance": [],
            "query_optimization": [],
            "resource_utilization": [],
            "trends": {},
        }

    def monitor_search_performance(self) -> Dict[str, Any]:
        """Monitor search view performance across different patterns"""
        logger.info("Monitoring search view performance...")

        search_tests = [
            {
                "name": "simple_content_search",
                "query": """
                    FOR doc IN knowledge_search_view
                        SEARCH PHRASE(doc.content, @term, "knowledge_text_analyzer")
                        SORT TFIDF(doc) DESC
                        LIMIT 10
                        RETURN {id: doc._id, score: TFIDF(doc)}
                """,
                "params": {"term": "machine learning"},
                "expected_complexity": "low",
            },
            {
                "name": "multi_field_search",
                "query": """
                    FOR doc IN knowledge_search_view
                        SEARCH PHRASE(doc.content, @term, "knowledge_text_analyzer") OR
                               PHRASE(doc.title, @term, "text_en")
                        SORT TFIDF(doc) DESC
                        LIMIT 20
                        RETURN {id: doc._id, score: TFIDF(doc), collection: PARSE_IDENTIFIER(doc._id).collection}
                """,
                "params": {"term": "neural network"},
                "expected_complexity": "medium",
            },
            {
                "name": "complex_analyzer_search",
                "query": """
                    FOR doc IN knowledge_search_view
                        SEARCH ANALYZER(BOOST(PHRASE(doc.content, @term), 2.0), "knowledge_text_analyzer") OR
                               ANALYZER(PHRASE(doc.content, @term), "ngram_analyzer")
                        SORT TFIDF(doc) DESC
                        LIMIT 15
                        RETURN {id: doc._id, score: TFIDF(doc)}
                """,
                "params": {"term": "intelligence"},
                "expected_complexity": "high",
            },
        ]

        performance_results = []

        for test in search_tests:
            # Run multiple iterations for statistical accuracy
            execution_times = []
            result_counts = []

            for iteration in range(5):
                try:
                    start_time = time.time()
                    result = self.db.aql.execute(
                        test["query"], bind_vars=test["params"]
                    )
                    docs = list(result)
                    execution_time = time.time() - start_time

                    execution_times.append(execution_time)
                    result_counts.append(len(docs))

                except Exception as e:
                    logger.error(
                        f"Search test {test['name']} iteration {iteration} failed: {e}"
                    )
                    continue

            if execution_times:
                performance_result = {
                    "test_name": test["name"],
                    "complexity": test["expected_complexity"],
                    "iterations": len(execution_times),
                    "avg_execution_time": statistics.mean(execution_times),
                    "min_execution_time": min(execution_times),
                    "max_execution_time": max(execution_times),
                    "std_deviation": statistics.stdev(execution_times)
                    if len(execution_times) > 1
                    else 0,
                    "avg_result_count": statistics.mean(result_counts),
                    "performance_score": self._calculate_performance_score(
                        execution_times, result_counts
                    ),
                    "timestamp": datetime.now().isoformat(),
                }

                performance_results.append(performance_result)
                logger.info(
                    f"✓ {test['name']}: {performance_result['avg_execution_time']:.4f}s avg, {performance_result['avg_result_count']:.1f} results"
                )

        return {
            "category": "search_performance",
            "tests": performance_results,
            "summary": self._summarize_performance(performance_results),
        }

    def monitor_graph_performance(self) -> Dict[str, Any]:
        """Monitor graph traversal and analysis performance"""
        logger.info("Monitoring graph traversal performance...")

        graph_tests = [
            {
                "name": "simple_traversal",
                "query": """
                    FOR v IN entities
                        LIMIT 5
                        FOR related IN 1..2 OUTBOUND v knowledge_relationships
                            LIMIT 10
                            RETURN {source: v._key, target: related._key}
                """,
                "expected_complexity": "low",
            },
            {
                "name": "named_graph_traversal",
                "query": """
                    FOR v IN entities
                        LIMIT 3
                        FOR related IN 1..3 OUTBOUND v GRAPH "knowledge_network"
                            LIMIT 15
                            RETURN {source: v._key, target: related._key, depth: 1}
                """,
                "expected_complexity": "medium",
            },
            {
                "name": "centrality_calculation",
                "query": """
                    FOR vertex IN entities
                        LIMIT 20
                        LET connections = LENGTH(
                            FOR v IN 1..1 ANY vertex knowledge_relationships
                                RETURN v
                        )
                        FILTER connections > 0
                        SORT connections DESC
                        LIMIT 10
                        RETURN {entity: vertex._key, connections: connections}
                """,
                "expected_complexity": "high",
            },
        ]

        performance_results = []

        for test in graph_tests:
            execution_times = []
            result_counts = []

            for iteration in range(
                3
            ):  # Fewer iterations for graph tests (more expensive)
                try:
                    start_time = time.time()
                    result = self.db.aql.execute(test["query"])
                    data = list(result)
                    execution_time = time.time() - start_time

                    execution_times.append(execution_time)
                    result_counts.append(len(data))

                except Exception as e:
                    logger.error(
                        f"Graph test {test['name']} iteration {iteration} failed: {e}"
                    )
                    continue

            if execution_times:
                performance_result = {
                    "test_name": test["name"],
                    "complexity": test["expected_complexity"],
                    "iterations": len(execution_times),
                    "avg_execution_time": statistics.mean(execution_times),
                    "min_execution_time": min(execution_times),
                    "max_execution_time": max(execution_times),
                    "std_deviation": statistics.stdev(execution_times)
                    if len(execution_times) > 1
                    else 0,
                    "avg_result_count": statistics.mean(result_counts),
                    "performance_score": self._calculate_performance_score(
                        execution_times, result_counts
                    ),
                    "timestamp": datetime.now().isoformat(),
                }

                performance_results.append(performance_result)
                logger.info(
                    f"✓ {test['name']}: {performance_result['avg_execution_time']:.4f}s avg, {performance_result['avg_result_count']:.1f} results"
                )

        return {
            "category": "graph_performance",
            "tests": performance_results,
            "summary": self._summarize_performance(performance_results),
        }

    def monitor_analyzer_performance(self) -> Dict[str, Any]:
        """Monitor text analyzer performance"""
        logger.info("Monitoring analyzer performance...")

        test_texts = [
            "Short text for analysis",
            "This is a medium-length text that contains various technical terms like machine learning, neural networks, and artificial intelligence for comprehensive analysis.",
            "This is a much longer text that simulates complex content analysis scenarios with extensive vocabulary including advanced concepts such as deep learning architectures, natural language processing, knowledge graph construction, semantic search optimization, cognitive pattern recognition, autonomous system design, multi-modal database integration, and sophisticated analytics capabilities that would typically be found in comprehensive technical documentation or research papers.",
        ]

        analyzers = [
            "knowledge_text_analyzer",
            "code_analyzer",
            "ngram_analyzer",
            "text_en",
        ]

        performance_results = []

        for analyzer in analyzers:
            for i, text in enumerate(test_texts):
                execution_times = []
                token_counts = []

                for iteration in range(5):
                    try:
                        start_time = time.time()
                        query = f"RETURN TOKENS(@text, '{analyzer}')"
                        result = self.db.aql.execute(query, bind_vars={"text": text})
                        tokens = list(result)[0]
                        execution_time = time.time() - start_time

                        execution_times.append(execution_time)
                        token_counts.append(len(tokens))

                    except Exception as e:
                        logger.error(
                            f"Analyzer test {analyzer} text {i} iteration {iteration} failed: {e}"
                        )
                        continue

                if execution_times:
                    performance_result = {
                        "analyzer": analyzer,
                        "text_length": len(text),
                        "text_complexity": ["short", "medium", "long"][i],
                        "iterations": len(execution_times),
                        "avg_execution_time": statistics.mean(execution_times),
                        "avg_token_count": statistics.mean(token_counts),
                        "tokens_per_second": statistics.mean(token_counts)
                        / statistics.mean(execution_times),
                        "performance_score": self._calculate_analyzer_performance_score(
                            execution_times, token_counts
                        ),
                        "timestamp": datetime.now().isoformat(),
                    }

                    performance_results.append(performance_result)

        logger.info(
            f"Completed analyzer performance testing: {len(performance_results)} test combinations"
        )

        return {
            "category": "analyzer_performance",
            "tests": performance_results,
            "summary": self._summarize_analyzer_performance(performance_results),
        }

    def monitor_query_optimization(self) -> Dict[str, Any]:
        """Monitor query optimization and caching effectiveness"""
        logger.info("Monitoring query optimization...")

        optimization_tests = [
            {
                "name": "index_utilization",
                "query": """
                    FOR doc IN entities
                        FILTER doc.type == @type AND doc.category == @category
                        SORT doc.relevance DESC
                        LIMIT 10
                        RETURN doc
                """,
                "params": {"type": "concept", "category": "artificial_intelligence"},
                "optimization_type": "index_filtering",
            },
            {
                "name": "join_optimization",
                "query": """
                    FOR entity IN entities
                        FILTER entity.type == @type
                        FOR rel IN knowledge_relationships
                            FILTER rel._from == entity._id
                            FOR target IN entities
                                FILTER target._id == rel._to
                                LIMIT 5
                                RETURN {source: entity, target: target, relationship: rel}
                """,
                "params": {"type": "concept"},
                "optimization_type": "join_performance",
            },
        ]

        performance_results = []

        for test in optimization_tests:
            # Test with and without explain to measure optimization impact
            execution_times = []
            plan_costs = []

            for iteration in range(3):
                try:
                    # Get execution plan
                    explain_result = self.db.aql.explain(
                        test["query"], bind_vars=test["params"]
                    )
                    estimated_cost = explain_result.get("plan", {}).get(
                        "estimatedCost", 0
                    )
                    plan_costs.append(estimated_cost)

                    # Execute query
                    start_time = time.time()
                    result = self.db.aql.execute(
                        test["query"], bind_vars=test["params"]
                    )
                    data = list(result)
                    execution_time = time.time() - start_time
                    execution_times.append(execution_time)

                except Exception as e:
                    logger.error(
                        f"Optimization test {test['name']} iteration {iteration} failed: {e}"
                    )
                    continue

            if execution_times:
                performance_result = {
                    "test_name": test["name"],
                    "optimization_type": test["optimization_type"],
                    "iterations": len(execution_times),
                    "avg_execution_time": statistics.mean(execution_times),
                    "avg_estimated_cost": statistics.mean(plan_costs),
                    "cost_to_time_ratio": statistics.mean(plan_costs)
                    / statistics.mean(execution_times)
                    if statistics.mean(execution_times) > 0
                    else 0,
                    "optimization_score": self._calculate_optimization_score(
                        execution_times, plan_costs
                    ),
                    "timestamp": datetime.now().isoformat(),
                }

                performance_results.append(performance_result)
                logger.info(
                    f"✓ {test['name']}: {performance_result['avg_execution_time']:.4f}s, cost: {performance_result['avg_estimated_cost']:.2f}"
                )

        return {
            "category": "query_optimization",
            "tests": performance_results,
            "summary": self._summarize_optimization_performance(performance_results),
        }

    def _calculate_performance_score(
        self, execution_times: List[float], result_counts: List[int]
    ) -> float:
        """Calculate normalized performance score"""
        if not execution_times:
            return 0.0

        avg_time = statistics.mean(execution_times)
        avg_results = statistics.mean(result_counts)
        consistency = 1 - (
            statistics.stdev(execution_times) / avg_time if avg_time > 0 else 0
        )

        # Score: higher is better (more results per second, more consistent)
        throughput_score = avg_results / avg_time if avg_time > 0 else 0
        performance_score = (throughput_score * 0.7) + (consistency * 0.3)

        return performance_score

    def _calculate_analyzer_performance_score(
        self, execution_times: List[float], token_counts: List[int]
    ) -> float:
        """Calculate analyzer-specific performance score"""
        if not execution_times:
            return 0.0

        avg_time = statistics.mean(execution_times)
        avg_tokens = statistics.mean(token_counts)

        # Score based on tokens processed per second
        tokens_per_second = avg_tokens / avg_time if avg_time > 0 else 0
        return tokens_per_second

    def _calculate_optimization_score(
        self, execution_times: List[float], plan_costs: List[float]
    ) -> float:
        """Calculate query optimization effectiveness score"""
        if not execution_times or not plan_costs:
            return 0.0

        avg_time = statistics.mean(execution_times)
        avg_cost = statistics.mean(plan_costs)

        # Score: lower cost and time is better
        efficiency_score = (
            100 / (avg_time * avg_cost) if (avg_time * avg_cost) > 0 else 0
        )
        return efficiency_score

    def _summarize_performance(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize performance test results"""
        if not results:
            return {"status": "no_data"}

        avg_times = [r["avg_execution_time"] for r in results]
        performance_scores = [r["performance_score"] for r in results]

        return {
            "total_tests": len(results),
            "overall_avg_time": statistics.mean(avg_times),
            "fastest_test": min(avg_times),
            "slowest_test": max(avg_times),
            "avg_performance_score": statistics.mean(performance_scores),
            "performance_consistency": 1
            - (statistics.stdev(avg_times) / statistics.mean(avg_times))
            if statistics.mean(avg_times) > 0
            else 0,
        }

    def _summarize_analyzer_performance(
        self, results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Summarize analyzer performance results"""
        if not results:
            return {"status": "no_data"}

        analyzer_summary = {}
        for result in results:
            analyzer = result["analyzer"]
            if analyzer not in analyzer_summary:
                analyzer_summary[analyzer] = {
                    "tests": 0,
                    "total_tokens_per_second": 0,
                    "avg_execution_time": 0,
                }

            analyzer_summary[analyzer]["tests"] += 1
            analyzer_summary[analyzer]["total_tokens_per_second"] += result[
                "tokens_per_second"
            ]
            analyzer_summary[analyzer]["avg_execution_time"] += result[
                "avg_execution_time"
            ]

        # Calculate averages
        for analyzer in analyzer_summary:
            tests = analyzer_summary[analyzer]["tests"]
            analyzer_summary[analyzer]["avg_tokens_per_second"] = (
                analyzer_summary[analyzer]["total_tokens_per_second"] / tests
            )
            analyzer_summary[analyzer]["avg_execution_time"] = (
                analyzer_summary[analyzer]["avg_execution_time"] / tests
            )

        return {
            "analyzers_tested": len(analyzer_summary),
            "analyzer_performance": analyzer_summary,
            "best_performer": max(
                analyzer_summary.keys(),
                key=lambda x: analyzer_summary[x]["avg_tokens_per_second"],
            )
            if analyzer_summary
            else None,
        }

    def _summarize_optimization_performance(
        self, results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Summarize query optimization results"""
        if not results:
            return {"status": "no_data"}

        optimization_scores = [r["optimization_score"] for r in results]
        execution_times = [r["avg_execution_time"] for r in results]

        return {
            "total_optimization_tests": len(results),
            "avg_optimization_score": statistics.mean(optimization_scores),
            "avg_execution_time": statistics.mean(execution_times),
            "optimization_effectiveness": "high"
            if statistics.mean(optimization_scores) > 50
            else "medium"
            if statistics.mean(optimization_scores) > 20
            else "low",
        }

    def generate_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        logger.info("Generating comprehensive performance report...")

        report = {
            "report_timestamp": datetime.now().isoformat(),
            "monitoring_results": {},
            "performance_trends": {},
            "recommendations": [],
            "system_health": {},
        }

        # Run all monitoring tests
        try:
            report["monitoring_results"]["search"] = self.monitor_search_performance()
            report["monitoring_results"]["graph"] = self.monitor_graph_performance()
            report["monitoring_results"][
                "analyzers"
            ] = self.monitor_analyzer_performance()
            report["monitoring_results"][
                "optimization"
            ] = self.monitor_query_optimization()

            # Generate overall assessment
            report["system_health"] = self._assess_system_health(
                report["monitoring_results"]
            )

            # Generate recommendations
            report["recommendations"] = self._generate_recommendations(
                report["monitoring_results"]
            )

            logger.info("Performance report generated successfully")

        except Exception as e:
            logger.error(f"Performance report generation failed: {e}")
            report["error"] = str(e)

        return report

    def _assess_system_health(
        self, monitoring_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess overall system health based on monitoring results"""
        health_metrics = {
            "search_health": "unknown",
            "graph_health": "unknown",
            "analyzer_health": "unknown",
            "optimization_health": "unknown",
            "overall_health": "unknown",
        }

        # Assess search health
        search_summary = monitoring_results.get("search", {}).get("summary", {})
        if search_summary.get("overall_avg_time", 999) < 0.01:  # < 10ms average
            health_metrics["search_health"] = "excellent"
        elif search_summary.get("overall_avg_time", 999) < 0.05:  # < 50ms average
            health_metrics["search_health"] = "good"
        elif search_summary.get("overall_avg_time", 999) < 0.1:  # < 100ms average
            health_metrics["search_health"] = "fair"
        else:
            health_metrics["search_health"] = "poor"

        # Assess graph health
        graph_summary = monitoring_results.get("graph", {}).get("summary", {})
        if graph_summary.get("overall_avg_time", 999) < 0.02:  # < 20ms average
            health_metrics["graph_health"] = "excellent"
        elif graph_summary.get("overall_avg_time", 999) < 0.1:  # < 100ms average
            health_metrics["graph_health"] = "good"
        elif graph_summary.get("overall_avg_time", 999) < 0.2:  # < 200ms average
            health_metrics["graph_health"] = "fair"
        else:
            health_metrics["graph_health"] = "poor"

        # Assess analyzer health
        analyzer_summary = monitoring_results.get("analyzers", {}).get("summary", {})
        if analyzer_summary.get("best_performer"):
            health_metrics["analyzer_health"] = "good"
        else:
            health_metrics["analyzer_health"] = "unknown"

        # Assess optimization health
        opt_summary = monitoring_results.get("optimization", {}).get("summary", {})
        opt_effectiveness = opt_summary.get("optimization_effectiveness", "unknown")
        health_metrics["optimization_health"] = opt_effectiveness

        # Overall health assessment
        health_scores = {"excellent": 4, "good": 3, "fair": 2, "poor": 1, "unknown": 0}

        total_score = sum(
            health_scores.get(health, 0)
            for health in health_metrics.values()
            if health != "unknown"
        )
        max_possible = len([h for h in health_metrics.values() if h != "unknown"]) * 4

        if max_possible > 0:
            overall_ratio = total_score / max_possible
            if overall_ratio > 0.8:
                health_metrics["overall_health"] = "excellent"
            elif overall_ratio > 0.6:
                health_metrics["overall_health"] = "good"
            elif overall_ratio > 0.4:
                health_metrics["overall_health"] = "fair"
            else:
                health_metrics["overall_health"] = "poor"

        return health_metrics

    def _generate_recommendations(
        self, monitoring_results: Dict[str, Any]
    ) -> List[str]:
        """Generate performance optimization recommendations"""
        recommendations = []

        # Search performance recommendations
        search_summary = monitoring_results.get("search", {}).get("summary", {})
        if search_summary.get("overall_avg_time", 0) > 0.05:
            recommendations.append(
                "Consider optimizing search view configurations for better performance"
            )

        # Graph performance recommendations
        graph_summary = monitoring_results.get("graph", {}).get("summary", {})
        if graph_summary.get("overall_avg_time", 0) > 0.1:
            recommendations.append(
                "Graph traversal queries may benefit from additional indexing"
            )

        # Analyzer performance recommendations
        analyzer_summary = monitoring_results.get("analyzers", {}).get("summary", {})
        if analyzer_summary.get("best_performer"):
            best = analyzer_summary["best_performer"]
            recommendations.append(
                f"Consider using {best} analyzer for optimal text processing performance"
            )

        # Optimization recommendations
        opt_summary = monitoring_results.get("optimization", {}).get("summary", {})
        if opt_summary.get("optimization_effectiveness") == "low":
            recommendations.append(
                "Query optimization effectiveness is low - review index usage and query patterns"
            )

        # General recommendations
        recommendations.extend(
            [
                "Monitor performance trends over time to identify degradation patterns",
                "Consider implementing query result caching for frequently accessed data",
                "Regularly update database statistics for optimal query planning",
            ]
        )

        return recommendations


def main():
    """Execute performance monitoring"""
    try:
        # Initialize performance monitor
        monitor = ArangoPerformanceMonitor()

        # Generate comprehensive performance report
        report = monitor.generate_performance_report()

        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"/home/opsvi/asea/arango_performance_report_{timestamp}.json"

        with open(filename, "w") as f:
            json.dump(report, f, indent=2, default=str)

        print("ArangoDB Performance Monitoring Complete!")
        print(f"Report saved to: {filename}")

        # Print summary
        system_health = report.get("system_health", {})
        print("\nSystem Health Summary:")
        print(f"- Overall Health: {system_health.get('overall_health', 'unknown')}")
        print(f"- Search Performance: {system_health.get('search_health', 'unknown')}")
        print(f"- Graph Performance: {system_health.get('graph_health', 'unknown')}")
        print(
            f"- Analyzer Performance: {system_health.get('analyzer_health', 'unknown')}"
        )
        print(
            f"- Query Optimization: {system_health.get('optimization_health', 'unknown')}"
        )

        # Print key recommendations
        recommendations = report.get("recommendations", [])
        if recommendations:
            print("\nKey Recommendations:")
            for i, rec in enumerate(recommendations[:5], 1):
                print(f"{i}. {rec}")

        return report

    except Exception as e:
        logger.error(f"Performance monitoring failed: {e}")
        return None


if __name__ == "__main__":
    main()
