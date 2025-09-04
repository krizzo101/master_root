#!/usr/bin/env python3
"""
Chat Data Quality Validation Script
Comprehensive validation of imported chat data quality standards
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import structlog
from project_context.db.connections import get_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = structlog.get_logger(__name__)


class ChatDataQualityValidator:
    """Validates the quality of imported chat data against defined standards."""

    def __init__(self):
        self.db = None
        self.validation_results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "PENDING",
            "quality_score": 0,
            "metrics": {},
            "issues": [],
            "recommendations": [],
        }

    async def initialize(self):
        """Initialize database connection."""
        try:
            self.db = await get_db()
            logger.info("Database connection established")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            self.validation_results["status"] = "CONNECTION_FAILED"
            return False

    async def validate_data_integrity(self) -> Dict[str, Any]:
        """Validate basic data integrity and completeness."""
        logger.info("Validating data integrity...")

        integrity_metrics = {
            "total_context_items": 0,
            "chat_items": 0,
            "unique_sessions": 0,
            "date_range": None,
            "completeness_score": 0,
        }

        try:
            # Get total context items
            total_query = "SELECT COUNT(*) as total FROM context_items"
            total_result = await self.db.fetch_one(total_query)
            integrity_metrics["total_context_items"] = (
                total_result["total"] if total_result else 0
            )

            # Get chat-specific items
            chat_query = """
                SELECT COUNT(*) as chat_total,
                       COUNT(DISTINCT session_id) as unique_sessions,
                       MIN(timestamp) as earliest,
                       MAX(timestamp) as latest
                FROM context_items
                WHERE adapter_id LIKE '%chat%' OR source_type = 'chat'
            """
            chat_result = await self.db.fetch_one(chat_query)
            if chat_result:
                integrity_metrics["chat_items"] = chat_result["chat_total"] or 0
                integrity_metrics["unique_sessions"] = (
                    chat_result["unique_sessions"] or 0
                )
                if chat_result["earliest"] and chat_result["latest"]:
                    integrity_metrics["date_range"] = {
                        "earliest": chat_result["earliest"].isoformat(),
                        "latest": chat_result["latest"].isoformat(),
                    }

            # Calculate completeness score
            if integrity_metrics["total_context_items"] > 0:
                integrity_metrics["completeness_score"] = min(
                    100,
                    (
                        integrity_metrics["chat_items"]
                        / max(1, integrity_metrics["total_context_items"])
                    )
                    * 100,
                )

            logger.info("Data integrity validation complete", **integrity_metrics)
            return integrity_metrics

        except Exception as e:
            logger.error(f"Data integrity validation failed: {e}")
            self.validation_results["issues"].append(
                {
                    "type": "DATA_INTEGRITY_ERROR",
                    "message": str(e),
                    "severity": "CRITICAL",
                }
            )
            return integrity_metrics

    async def validate_entity_extraction(self) -> Dict[str, Any]:
        """Validate entity extraction accuracy and coverage."""
        logger.info("Validating entity extraction...")

        entity_metrics = {
            "total_entities": 0,
            "entity_types": {},
            "extraction_rate": 0,
            "quality_indicators": {},
        }

        try:
            # Get entity statistics
            entity_query = """
                SELECT
                    entity_type,
                    COUNT(*) as count,
                    COUNT(DISTINCT item_id) as items_with_entities
                FROM context_item_entities cie
                JOIN context_items ci ON cie.item_id = ci.id
                WHERE ci.adapter_id LIKE '%chat%' OR ci.source_type = 'chat'
                GROUP BY entity_type
                ORDER BY count DESC
            """
            entity_results = await self.db.fetch_many(entity_query)

            total_entities = 0
            for result in entity_results:
                entity_type = result["entity_type"]
                count = result["count"]
                entity_metrics["entity_types"][entity_type] = count
                total_entities += count

            entity_metrics["total_entities"] = total_entities

            # Calculate extraction rate
            if entity_metrics.get("total_entities", 0) > 0:
                chat_items = self.validation_results.get("metrics", {}).get(
                    "chat_items", 1
                )
                entity_metrics["extraction_rate"] = (
                    total_entities / max(1, chat_items)
                ) * 100

            # Quality indicators
            entity_metrics["quality_indicators"] = {
                "has_code_entities": "code" in entity_metrics["entity_types"],
                "has_file_entities": "file_path" in entity_metrics["entity_types"],
                "has_url_entities": "url" in entity_metrics["entity_types"],
                "entity_diversity": len(entity_metrics["entity_types"]),
            }

            logger.info("Entity extraction validation complete", **entity_metrics)
            return entity_metrics

        except Exception as e:
            logger.error(f"Entity extraction validation failed: {e}")
            self.validation_results["issues"].append(
                {
                    "type": "ENTITY_EXTRACTION_ERROR",
                    "message": str(e),
                    "severity": "HIGH",
                }
            )
            return entity_metrics

    async def validate_embedding_quality(self) -> Dict[str, Any]:
        """Validate embedding generation and quality."""
        logger.info("Validating embedding quality...")

        embedding_metrics = {
            "items_with_embeddings": 0,
            "embedding_coverage": 0,
            "embedding_dimensions": None,
            "quality_score": 0,
        }

        try:
            # Check embedding coverage
            embedding_query = """
                SELECT
                    COUNT(*) as total_chat_items,
                    COUNT(embedding) as items_with_embeddings,
                    AVG(array_length(embedding, 1)) as avg_dimensions
                FROM context_items
                WHERE adapter_id LIKE '%chat%' OR source_type = 'chat'
            """
            embedding_result = await self.db.fetch_one(embedding_query)

            if embedding_result:
                total_items = embedding_result["total_chat_items"] or 0
                with_embeddings = embedding_result["items_with_embeddings"] or 0

                embedding_metrics["items_with_embeddings"] = with_embeddings
                embedding_metrics["embedding_dimensions"] = int(
                    embedding_result["avg_dimensions"] or 0
                )

                if total_items > 0:
                    embedding_metrics["embedding_coverage"] = (
                        with_embeddings / total_items
                    ) * 100

                # Quality score based on coverage
                if embedding_metrics["embedding_coverage"] >= 95:
                    embedding_metrics["quality_score"] = 100
                elif embedding_metrics["embedding_coverage"] >= 90:
                    embedding_metrics["quality_score"] = 85
                elif embedding_metrics["embedding_coverage"] >= 80:
                    embedding_metrics["quality_score"] = 70
                else:
                    embedding_metrics["quality_score"] = 50

            logger.info("Embedding quality validation complete", **embedding_metrics)
            return embedding_metrics

        except Exception as e:
            logger.error(f"Embedding quality validation failed: {e}")
            self.validation_results["issues"].append(
                {
                    "type": "EMBEDDING_QUALITY_ERROR",
                    "message": str(e),
                    "severity": "HIGH",
                }
            )
            return embedding_metrics

    async def validate_performance_metrics(self) -> Dict[str, Any]:
        """Validate system performance and throughput metrics."""
        logger.info("Validating performance metrics...")

        performance_metrics = {
            "database_size": 0,
            "index_usage": {},
            "query_performance": {},
            "estimated_throughput": 0,
        }

        try:
            # Database size
            size_query = """
                SELECT pg_size_pretty(pg_total_relation_size('context_items')) as table_size,
                       pg_size_pretty(pg_database_size(current_database())) as db_size
            """
            size_result = await self.db.fetch_one(size_query)
            if size_result:
                performance_metrics["database_size"] = {
                    "table_size": size_result["table_size"],
                    "database_size": size_result["db_size"],
                }

            # Index usage statistics
            index_query = """
                SELECT schemaname, tablename, indexname, idx_tup_read, idx_tup_fetch
                FROM pg_stat_user_indexes
                WHERE tablename = 'context_items'
                ORDER BY idx_tup_read DESC
                LIMIT 5
            """
            index_results = await self.db.fetch_many(index_query)
            performance_metrics["index_usage"] = [dict(row) for row in index_results]

            # Basic query performance test
            import time

            start_time = time.time()

            test_query = """
                SELECT COUNT(*), MAX(timestamp)
                FROM context_items
                WHERE adapter_id LIKE '%chat%'
            """
            await self.db.fetch_one(test_query)

            query_time = time.time() - start_time
            performance_metrics["query_performance"] = {
                "sample_query_time_ms": round(query_time * 1000, 2),
                "estimated_qps": round(1 / max(query_time, 0.001), 2),
            }

            logger.info(
                "Performance metrics validation complete", **performance_metrics
            )
            return performance_metrics

        except Exception as e:
            logger.error(f"Performance metrics validation failed: {e}")
            self.validation_results["issues"].append(
                {
                    "type": "PERFORMANCE_METRICS_ERROR",
                    "message": str(e),
                    "severity": "MEDIUM",
                }
            )
            return performance_metrics

    async def test_semantic_search(self) -> Dict[str, Any]:
        """Test semantic search functionality."""
        logger.info("Testing semantic search functionality...")

        search_metrics = {
            "search_functional": False,
            "sample_results": 0,
            "search_quality": 0,
        }

        try:
            # Test basic similarity search if embeddings exist
            search_query = """
                SELECT id, title, content,
                       embedding <-> (SELECT embedding FROM context_items WHERE embedding IS NOT NULL LIMIT 1) as distance
                FROM context_items
                WHERE embedding IS NOT NULL
                  AND (adapter_id LIKE '%chat%' OR source_type = 'chat')
                ORDER BY distance
                LIMIT 5
            """

            search_results = await self.db.fetch_many(search_query)

            if search_results:
                search_metrics["search_functional"] = True
                search_metrics["sample_results"] = len(search_results)
                search_metrics["search_quality"] = (
                    85 if len(search_results) >= 3 else 60
                )

            logger.info("Semantic search test complete", **search_metrics)
            return search_metrics

        except Exception as e:
            logger.error(f"Semantic search test failed: {e}")
            self.validation_results["issues"].append(
                {
                    "type": "SEMANTIC_SEARCH_ERROR",
                    "message": str(e),
                    "severity": "MEDIUM",
                }
            )
            return search_metrics

    async def run_full_validation(self) -> Dict[str, Any]:
        """Run complete data quality validation suite."""
        logger.info("Starting comprehensive chat data quality validation...")

        if not await self.initialize():
            return self.validation_results

        # Run all validation components
        integrity_metrics = await self.validate_data_integrity()
        entity_metrics = await self.validate_entity_extraction()
        embedding_metrics = await self.validate_embedding_quality()
        performance_metrics = await self.validate_performance_metrics()
        search_metrics = await self.test_semantic_search()

        # Aggregate results
        self.validation_results["metrics"] = {
            "data_integrity": integrity_metrics,
            "entity_extraction": entity_metrics,
            "embedding_quality": embedding_metrics,
            "performance": performance_metrics,
            "semantic_search": search_metrics,
        }

        # Calculate overall quality score
        scores = []

        # Data integrity score (40% weight)
        if integrity_metrics["chat_items"] > 0:
            scores.append(min(100, integrity_metrics["completeness_score"]) * 0.4)

        # Entity extraction score (25% weight)
        if entity_metrics["extraction_rate"] > 0:
            entity_score = min(100, entity_metrics["extraction_rate"])
            scores.append(entity_score * 0.25)

        # Embedding quality score (25% weight)
        scores.append(embedding_metrics["quality_score"] * 0.25)

        # Search functionality score (10% weight)
        search_score = 100 if search_metrics["search_functional"] else 0
        scores.append(search_score * 0.10)

        overall_score = sum(scores) if scores else 0
        self.validation_results["quality_score"] = round(overall_score, 2)

        # Determine status
        if overall_score >= 95:
            self.validation_results["status"] = "EXCELLENT"
        elif overall_score >= 85:
            self.validation_results["status"] = "GOOD"
        elif overall_score >= 75:
            self.validation_results["status"] = "ACCEPTABLE"
        elif overall_score >= 60:
            self.validation_results["status"] = "NEEDS_IMPROVEMENT"
        else:
            self.validation_results["status"] = "POOR"

        # Generate recommendations
        await self.generate_recommendations()

        logger.info(
            "Validation complete",
            status=self.validation_results["status"],
            quality_score=self.validation_results["quality_score"],
        )

        return self.validation_results

    async def generate_recommendations(self):
        """Generate recommendations based on validation results."""
        recommendations = []
        metrics = self.validation_results["metrics"]

        # Data integrity recommendations
        integrity = metrics.get("data_integrity", {})
        if integrity.get("chat_items", 0) == 0:
            recommendations.append(
                {
                    "type": "CRITICAL",
                    "area": "Data Import",
                    "message": "No chat data found. Import process may have failed or not been executed.",
                    "action": "Verify and re-run chat import process",
                }
            )
        elif integrity.get("completeness_score", 0) < 80:
            recommendations.append(
                {
                    "type": "HIGH",
                    "area": "Data Completeness",
                    "message": f"Data completeness score is {integrity.get('completeness_score', 0):.1f}%",
                    "action": "Review import logs and verify source data accessibility",
                }
            )

        # Entity extraction recommendations
        entities = metrics.get("entity_extraction", {})
        if entities.get("extraction_rate", 0) < 50:
            recommendations.append(
                {
                    "type": "HIGH",
                    "area": "Entity Extraction",
                    "message": f"Low entity extraction rate: {entities.get('extraction_rate', 0):.1f}%",
                    "action": "Review entity extraction configuration and patterns",
                }
            )

        # Embedding recommendations
        embeddings = metrics.get("embedding_quality", {})
        if embeddings.get("embedding_coverage", 0) < 95:
            recommendations.append(
                {
                    "type": "MEDIUM",
                    "area": "Embedding Coverage",
                    "message": f"Embedding coverage is {embeddings.get('embedding_coverage', 0):.1f}%",
                    "action": "Check embedding generation service and retry failed items",
                }
            )

        # Search functionality recommendations
        search = metrics.get("semantic_search", {})
        if not search.get("search_functional", False):
            recommendations.append(
                {
                    "type": "HIGH",
                    "area": "Semantic Search",
                    "message": "Semantic search functionality not working",
                    "action": "Verify vector similarity extension and embedding dimensions",
                }
            )

        self.validation_results["recommendations"] = recommendations


async def main():
    """Main validation execution."""
    print("🔍 Starting Chat Data Quality Validation...")
    print("=" * 60)

    validator = ChatDataQualityValidator()
    results = await validator.run_full_validation()

    # Generate report
    report_file = (
        f"chat_data_quality_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )

    with open(report_file, "w") as f:
        json.dump(results, f, indent=2, default=str)

    # Print summary
    print(f"\n📊 VALIDATION RESULTS")
    print(f"Status: {results['status']}")
    print(f"Overall Quality Score: {results['quality_score']}/100")
    print(f"Issues Found: {len(results['issues'])}")
    print(f"Recommendations: {len(results['recommendations'])}")

    # Print key metrics
    if results["metrics"]:
        integrity = results["metrics"].get("data_integrity", {})
        print(f"\n📈 KEY METRICS")
        print(f"Total Context Items: {integrity.get('total_context_items', 0):,}")
        print(f"Chat Items: {integrity.get('chat_items', 0):,}")
        print(f"Unique Sessions: {integrity.get('unique_sessions', 0):,}")

        entities = results["metrics"].get("entity_extraction", {})
        print(f"Total Entities: {entities.get('total_entities', 0):,}")
        print(f"Entity Types: {len(entities.get('entity_types', {}))}")

        embeddings = results["metrics"].get("embedding_quality", {})
        print(f"Embedding Coverage: {embeddings.get('embedding_coverage', 0):.1f}%")

    # Print critical issues
    critical_issues = [i for i in results["issues"] if i.get("severity") == "CRITICAL"]
    if critical_issues:
        print(f"\n🚨 CRITICAL ISSUES:")
        for issue in critical_issues:
            print(f"  - {issue['message']}")

    # Print recommendations
    if results["recommendations"]:
        print(f"\n💡 TOP RECOMMENDATIONS:")
        for rec in results["recommendations"][:3]:
            print(f"  - [{rec['type']}] {rec['area']}: {rec['action']}")

    print(f"\n📄 Full report saved to: {report_file}")
    print("\n✅ Chat data quality validation complete!")

    return results


if __name__ == "__main__":
    asyncio.run(main())
