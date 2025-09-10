#!/usr/bin/env python3
"""
RAG Evaluation System - Benchmarks and quality metrics
"""

import json
import logging
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, List, Tuple

import numpy as np

from apps.knowledge_system.hybrid_search import HybridSearch, SearchResult

logger = logging.getLogger(__name__)


@dataclass
class EvaluationQuery:
    """Test query with expected results"""

    query: str
    expected_sources: List[str]  # Expected source files/patterns
    expected_types: List[str]  # Expected knowledge types
    strategy: str = "hybrid"
    min_relevance_score: float = 0.5


@dataclass
class EvaluationResult:
    """Results from a single evaluation"""

    query: str
    strategy: str
    precision: float  # How many results were relevant
    recall: float  # How many relevant items were found
    f1_score: float
    latency_ms: float
    top_results: List[str]
    relevance_scores: List[float]
    timestamp: str


class RAGEvaluator:
    """Evaluate RAG system quality"""

    def __init__(self):
        self.search = HybridSearch()
        self.results_log = []

        # Define benchmark queries
        self.benchmarks = [
            EvaluationQuery(
                query="OpenAI streaming API examples",
                expected_sources=["streaming.py", "examples", "api.md"],
                expected_types=["CODE", "DOCUMENTATION"],
                strategy="hybrid",
            ),
            EvaluationQuery(
                query="error handling in Python",
                expected_sources=[".py", "error", "exception"],
                expected_types=["CODE"],
                strategy="graph",
            ),
            EvaluationQuery(
                query="authentication setup",
                expected_sources=["auth", "api", "token"],
                expected_types=["DOCUMENTATION", "CODE"],
                strategy="vector",
            ),
            EvaluationQuery(
                query="async await patterns",
                expected_sources=["async", "await", ".py"],
                expected_types=["CODE"],
                strategy="hybrid",
            ),
            EvaluationQuery(
                query="configuration files JSON",
                expected_sources=[".json", "config"],
                expected_types=["CONFIGURATION"],
                strategy="vector",
            ),
            EvaluationQuery(
                query="multi-agent systems",
                expected_sources=["multi-agent", "structured"],
                expected_types=["REFERENCE", "DOCUMENTATION"],
                strategy="hybrid",
            ),
            EvaluationQuery(
                query="API rate limiting",
                expected_sources=["rate", "limit", "api"],
                expected_types=["DOCUMENTATION"],
                strategy="graph",
            ),
            EvaluationQuery(
                query="websocket connections",
                expected_sources=["websocket", "ws", "realtime"],
                expected_types=["CODE", "DOCUMENTATION"],
                strategy="hybrid",
            ),
        ]

    def evaluate_query(
        self, eval_query: EvaluationQuery, limit: int = 10
    ) -> EvaluationResult:
        """Evaluate a single query"""

        # Measure latency
        start_time = time.time()
        results = self.search.search(
            query=eval_query.query,
            limit=limit,
            strategy=eval_query.strategy,
            expand_depth=1,
        )
        latency_ms = (time.time() - start_time) * 1000

        # Calculate relevance
        relevant_results = []
        relevance_scores = []

        for result in results:
            relevance = self._calculate_relevance(result, eval_query)
            relevance_scores.append(relevance)
            if relevance >= eval_query.min_relevance_score:
                relevant_results.append(result)

        # Calculate metrics
        precision = len(relevant_results) / len(results) if results else 0

        # Estimate recall (hard without knowing total relevant items)
        # Use heuristic: if we found items matching all expected patterns, recall is high
        patterns_found = set()
        for result in relevant_results:
            for pattern in eval_query.expected_sources:
                if pattern.lower() in result.source.lower():
                    patterns_found.add(pattern)

        recall = (
            len(patterns_found) / len(eval_query.expected_sources)
            if eval_query.expected_sources
            else 0
        )

        # F1 score
        f1_score = (
            2 * (precision * recall) / (precision + recall)
            if (precision + recall) > 0
            else 0
        )

        return EvaluationResult(
            query=eval_query.query,
            strategy=eval_query.strategy,
            precision=precision,
            recall=recall,
            f1_score=f1_score,
            latency_ms=latency_ms,
            top_results=[r.source for r in results[:5]],
            relevance_scores=relevance_scores[:5],
            timestamp=datetime.now().isoformat(),
        )

    def _calculate_relevance(
        self, result: SearchResult, eval_query: EvaluationQuery
    ) -> float:
        """Calculate relevance score for a result"""

        relevance = 0.0
        weights = {"source_match": 0.4, "type_match": 0.3, "score": 0.3}

        # Check source patterns
        source_matches = 0
        for pattern in eval_query.expected_sources:
            if pattern.lower() in result.source.lower():
                source_matches += 1

        if eval_query.expected_sources:
            relevance += weights["source_match"] * (
                source_matches / len(eval_query.expected_sources)
            )

        # Check type match
        if result.knowledge_type in eval_query.expected_types:
            relevance += weights["type_match"]

        # Use the search score
        relevance += weights["score"] * result.combined_score

        return min(relevance, 1.0)

    def run_benchmarks(self) -> Dict[str, Any]:
        """Run all benchmark queries"""

        print("Running RAG Evaluation Benchmarks")
        print("=" * 60)

        results = []
        total_precision = 0
        total_recall = 0
        total_f1 = 0
        total_latency = 0

        for i, benchmark in enumerate(self.benchmarks, 1):
            print(f"\n{i}. Query: '{benchmark.query}'")
            print(f"   Strategy: {benchmark.strategy}")

            result = self.evaluate_query(benchmark)
            results.append(result)

            total_precision += result.precision
            total_recall += result.recall
            total_f1 += result.f1_score
            total_latency += result.latency_ms

            print(f"   Precision: {result.precision:.2%}")
            print(f"   Recall: {result.recall:.2%}")
            print(f"   F1 Score: {result.f1_score:.2f}")
            print(f"   Latency: {result.latency_ms:.1f}ms")
            print(
                f"   Top result: {result.top_results[0] if result.top_results else 'None'}"
            )

        # Calculate averages
        n = len(self.benchmarks)
        summary = {
            "total_queries": n,
            "avg_precision": total_precision / n,
            "avg_recall": total_recall / n,
            "avg_f1_score": total_f1 / n,
            "avg_latency_ms": total_latency / n,
            "timestamp": datetime.now().isoformat(),
            "results": [asdict(r) for r in results],
        }

        print("\n" + "=" * 60)
        print("EVALUATION SUMMARY")
        print("=" * 60)
        print(f"Average Precision: {summary['avg_precision']:.2%}")
        print(f"Average Recall: {summary['avg_recall']:.2%}")
        print(f"Average F1 Score: {summary['avg_f1_score']:.2f}")
        print(f"Average Latency: {summary['avg_latency_ms']:.1f}ms")

        # Save results
        self.save_results(summary)

        return summary

    def save_results(self, summary: Dict):
        """Save evaluation results to file"""

        filename = f"evaluation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = f"/home/opsvi/master_root/apps/knowledge_system/{filename}"

        with open(filepath, "w") as f:
            json.dump(summary, f, indent=2)

        print(f"\nResults saved to: {filename}")

    def compare_strategies(self) -> Dict[str, Any]:
        """Compare different search strategies"""

        print("\nComparing Search Strategies")
        print("=" * 60)

        test_queries = [
            "OpenAI API usage",
            "error handling patterns",
            "configuration setup",
        ]

        strategies = ["vector", "graph", "hybrid"]
        comparison = {}

        for query in test_queries:
            print(f"\nQuery: '{query}'")
            comparison[query] = {}

            for strategy in strategies:
                eval_query = EvaluationQuery(
                    query=query,
                    expected_sources=[],  # Don't check specific sources
                    expected_types=[],
                    strategy=strategy,
                )

                result = self.evaluate_query(eval_query, limit=5)

                comparison[query][strategy] = {
                    "latency_ms": result.latency_ms,
                    "top_score": result.relevance_scores[0]
                    if result.relevance_scores
                    else 0,
                    "top_result": result.top_results[0]
                    if result.top_results
                    else "None",
                }

                print(
                    f"  {strategy}: {result.latency_ms:.1f}ms, "
                    f"top score: {comparison[query][strategy]['top_score']:.3f}"
                )

        return comparison

    def measure_performance(self, iterations: int = 10) -> Dict[str, Any]:
        """Measure system performance"""

        print(f"\nMeasuring Performance ({iterations} iterations)")
        print("=" * 60)

        query = "OpenAI streaming API"
        latencies = {"vector": [], "graph": [], "hybrid": []}

        for strategy in latencies.keys():
            print(f"\nTesting {strategy} strategy...")

            for i in range(iterations):
                start = time.time()
                self.search.search(query, limit=5, strategy=strategy)
                latency = (time.time() - start) * 1000
                latencies[strategy].append(latency)

                if (i + 1) % 5 == 0:
                    print(f"  Iteration {i+1}: {latency:.1f}ms")

        # Calculate statistics
        stats = {}
        for strategy, times in latencies.items():
            stats[strategy] = {
                "mean_ms": np.mean(times),
                "std_ms": np.std(times),
                "min_ms": np.min(times),
                "max_ms": np.max(times),
                "p50_ms": np.percentile(times, 50),
                "p95_ms": np.percentile(times, 95),
            }

        print("\nPerformance Statistics:")
        for strategy, stat in stats.items():
            print(f"\n{strategy.upper()}:")
            print(f"  Mean: {stat['mean_ms']:.1f}ms ± {stat['std_ms']:.1f}ms")
            print(f"  Range: {stat['min_ms']:.1f}ms - {stat['max_ms']:.1f}ms")
            print(f"  P50: {stat['p50_ms']:.1f}ms, P95: {stat['p95_ms']:.1f}ms")

        return stats

    def close(self):
        """Clean up"""
        self.search.close()


if __name__ == "__main__":
    evaluator = RAGEvaluator()

    try:
        # Run benchmarks
        summary = evaluator.run_benchmarks()

        # Compare strategies
        # comparison = evaluator.compare_strategies()

        # Measure performance
        # perf_stats = evaluator.measure_performance(iterations=5)

    finally:
        evaluator.close()
