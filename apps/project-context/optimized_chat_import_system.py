#!/usr/bin/env python3
"""
Complete Performance Optimization System for Chat Import
Integrates all performance optimizations into a production-ready system
"""

import asyncio
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog

from src.project_context.ingestion.adapters.chat_adapter import ChatAdapter
from src.project_context.ingestion.adaptive_batch_processor import (
    create_enhanced_batch_processor,
)
from src.project_context.ingestion.optimized_database_enhanced import (
    create_optimized_database,
)

# Import our optimization components
from src.project_context.ingestion.performance_cache import (
    get_cache_manager,
    initialize_caches,
)
from src.project_context.ingestion.performance_monitor import (
    get_performance_monitor,
    initialize_performance_monitoring,
)

logger = structlog.get_logger(__name__)


class OptimizedChatImportSystem:
    """Production-ready chat import system with comprehensive performance optimization."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the optimized chat import system."""
        self.config = config
        self.database_url = config.get(
            "database_url",
            "postgresql://opsvi:opsvi_secure_password@localhost:5432/unified_context",
        )

        # Core components
        self.cache_manager = None
        self.database_pool = None
        self.batch_optimizer = None
        self.index_manager = None
        self.batch_processor = None
        self.performance_monitor = None
        self.chat_adapter = None

        # State tracking
        self.is_initialized = False
        self.is_running = False
        self.start_time = None
        self.total_processed = 0
        self.total_errors = 0

    async def initialize(self) -> Dict[str, Any]:
        """Initialize all optimization components."""
        logger.info("Initializing optimized chat import system")
        init_start = time.time()

        try:
            # Step 1: Initialize caching system
            logger.info("Initializing performance caches")
            self.cache_manager = await initialize_caches()

            # Step 2: Initialize optimized database
            logger.info("Initializing optimized database components")
            (
                self.database_pool,
                self.batch_optimizer,
                self.index_manager,
            ) = await create_optimized_database(
                database_url=self.database_url,
                cache_manager=self.cache_manager,
                min_connections=20,
                max_connections=100,
                command_timeout=300,
            )

            # Step 3: Create performance indexes
            logger.info("Creating performance-optimized database indexes")
            index_results = await self.index_manager.create_performance_indexes()
            logger.info(
                "Index creation completed",
                created=len(index_results.get("created_indexes", [])),
                failed=len(index_results.get("failed_indexes", [])),
            )

            # Step 4: Update table statistics
            await self.index_manager.analyze_table_statistics()

            # Step 5: Initialize batch processor
            logger.info("Initializing enhanced batch processor")
            self.batch_processor = await create_enhanced_batch_processor(
                cache_manager=self.cache_manager,
                initial_batch_size=200,  # Increased for better throughput
                max_parallel_batches=8,  # Increased parallelism
            )

            # Step 6: Initialize performance monitoring
            logger.info("Starting performance monitoring")
            self.performance_monitor = await initialize_performance_monitoring(
                database_pool=self.database_pool,
                cache_manager=self.cache_manager,
                batch_processor=self.batch_processor,
                collection_interval=3.0,  # More frequent monitoring
            )

            # Step 7: Initialize chat adapter with optimized config
            logger.info("Initializing optimized chat adapter")
            adapter_config = self._create_optimized_adapter_config()
            self.chat_adapter = ChatAdapter(adapter_config)
            await self.chat_adapter.initialize()

            # Step 8: Warm up caches
            logger.info("Warming up caches")
            await self._warmup_system_caches()

            init_duration = time.time() - init_start
            self.is_initialized = True

            return {
                "status": "success",
                "initialization_duration": init_duration,
                "components_initialized": [
                    "cache_manager",
                    "database_pool",
                    "batch_optimizer",
                    "index_manager",
                    "batch_processor",
                    "performance_monitor",
                    "chat_adapter",
                ],
                "database_indexes": index_results,
                "ready_for_production": True,
            }

        except Exception as e:
            logger.error("Failed to initialize optimized system", error=str(e))
            return {
                "status": "failed",
                "error": str(e),
                "initialization_duration": time.time() - init_start,
            }

    def _create_optimized_adapter_config(self):
        """Create optimized configuration for chat adapter."""
        from src.project_context.ingestion.base_adapter import AdapterConfig, BatchMode

        return AdapterConfig(
            adapter_id="optimized_chat",
            source_type="chat",
            batch_mode=BatchMode.STREAMING,
            batch_size=500,  # Larger batches for better throughput
            generate_embeddings=True,
            generate_summaries=False,
            extract_relationships=True,
            skip_duplicates=True,
            source_config={
                "input_format": "jsonl",
                "file_patterns": ["*.jsonl", "*.json"],
                "watch_directories": ["/home/opsvi/master_root/chat_logs"],
                "extract_entities": True,
                "entity_extraction_config": {
                    "enable_url_detection": True,
                    "enable_code_detection": True,
                    "enable_mention_detection": True,
                    "enable_issue_detection": True,
                    "enable_tech_keyword_detection": True,
                    "enable_email_detection": True,
                    "enable_file_path_detection": True,
                    "enable_command_detection": True,
                    "enable_timestamp_detection": True,
                    "enable_named_entity_recognition": False,  # Disabled for performance
                    "max_entities_per_type": 100,
                },
                "embedding_config": {
                    "service": "sentence_transformers",
                    "model": "all-MiniLM-L6-v2",
                    "max_tokens": 8192,
                    "batch_size": 64,  # Increased for better throughput
                },
                "relationship_detection_config": {
                    "enable_entity_relationships": True,
                    "enable_content_similarity": True,
                    "enable_actor_relationships": True,
                    "similarity_threshold": 0.3,
                    "entity_overlap_threshold": 0.4,
                },
                "checkpoint_directory": "/tmp/optimized_chat_checkpoints",
                "max_checkpoint_hashes": 50000,  # Larger deduplication cache
            },
        )

    async def _warmup_system_caches(self):
        """Warm up system caches with recent data."""
        try:
            # Get recent sessions for cache warmup
            recent_sessions_query = """
                SELECT DISTINCT session_id
                FROM context_items
                WHERE source_type = 'chat'
                  AND timestamp > NOW() - INTERVAL '7 days'
                LIMIT 100
            """

            sessions = await self.database_pool.execute_query(
                recent_sessions_query, use_cache=False
            )
            session_ids = [row["session_id"] for row in sessions if row["session_id"]]

            # Common queries to pre-cache
            common_queries = [
                ("SELECT COUNT(*) FROM context_items WHERE source_type = 'chat'", ()),
                (
                    "SELECT COUNT(DISTINCT session_id) FROM context_items WHERE source_type = 'chat'",
                    (),
                ),
                (
                    """SELECT source_type, COUNT(*) as count
                       FROM context_items
                       GROUP BY source_type""",
                    (),
                ),
            ]

            await self.cache_manager.warmup_caches(session_ids[:10], common_queries)
            logger.info(
                "Cache warmup completed", sessions=len(session_ids), queries=len(common_queries)
            )

        except Exception as e:
            logger.warning("Cache warmup failed", error=str(e))

    async def execute_optimized_import(
        self, source_path: Optional[str] = None, target_items: Optional[int] = None
    ) -> Dict[str, Any]:
        """Execute optimized chat import with full performance monitoring."""

        if not self.is_initialized:
            return {"error": "System not initialized"}

        if self.is_running:
            return {"error": "Import already running"}

        logger.info("Starting optimized chat import execution")
        self.is_running = True
        self.start_time = datetime.utcnow()

        try:
            # Configure source path if provided
            if source_path:
                self.chat_adapter.config.source_config["watch_directories"] = [source_path]

            # Start processing with performance monitoring
            processing_results = await self._execute_processing_pipeline(target_items)

            # Generate comprehensive report
            final_report = await self._generate_completion_report(processing_results)

            return final_report

        except Exception as e:
            logger.error("Optimized import execution failed", error=str(e))
            return {
                "status": "failed",
                "error": str(e),
                "processing_duration": (datetime.utcnow() - self.start_time).total_seconds(),
            }
        finally:
            self.is_running = False

    async def _execute_processing_pipeline(self, target_items: Optional[int]) -> Dict[str, Any]:
        """Execute the main processing pipeline with optimization."""
        processed_count = 0
        error_count = 0
        batch_count = 0

        # Fetch items from chat adapter
        async for raw_items in self._fetch_items_in_batches():
            if target_items and processed_count >= target_items:
                break

            batch_start = time.time()

            # Transform items using chat adapter
            transformed_items = []
            for raw_item in raw_items:
                try:
                    transformed_item = await self.chat_adapter.transform_item(raw_item)
                    if transformed_item:  # Skip duplicates/None items
                        transformed_items.append(transformed_item)
                except Exception as e:
                    logger.warning("Item transformation failed", error=str(e))
                    error_count += 1

            if not transformed_items:
                continue

            # Process batch with enhanced processor
            batch_results = await self.batch_processor.process_chat_items(
                transformed_items, self.chat_adapter
            )

            # Store in database using optimized batch inserter
            storage_results = await self._store_items_optimized(transformed_items)

            # Update statistics
            processed_count += batch_results.get("processed", 0)
            error_count += batch_results.get("errors", 0) + storage_results.get("errors", 0)
            batch_count += 1

            # Update performance monitor
            self.performance_monitor.update_processing_stats(
                items_processed=batch_results.get("processed", 0),
                items_failed=batch_results.get("errors", 0),
            )

            batch_duration = time.time() - batch_start
            logger.info(
                "Batch processed",
                batch_size=len(transformed_items),
                processed=batch_results.get("processed", 0),
                errors=batch_results.get("errors", 0),
                duration=batch_duration,
                total_processed=processed_count,
            )

        return {
            "total_processed": processed_count,
            "total_errors": error_count,
            "total_batches": batch_count,
            "processing_duration": (datetime.utcnow() - self.start_time).total_seconds(),
        }

    async def _fetch_items_in_batches(self):
        """Fetch items from chat adapter in optimized batches."""
        current_batch = []
        batch_size = 1000  # Large fetch batches

        async for item in self.chat_adapter.fetch_items():
            current_batch.append(item)

            if len(current_batch) >= batch_size:
                yield current_batch
                current_batch = []

        # Yield remaining items
        if current_batch:
            yield current_batch

    async def _store_items_optimized(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Store items using optimized database insertion."""
        try:
            # Convert to format expected by batch inserter
            db_items = []
            for item in items:
                db_item = {
                    "source_type": item.source_type,
                    "source_id": item.source_id,
                    "title": item.title,
                    "content": item.content,
                    "file_path": item.file_path,
                    "line_start": item.line_start,
                    "line_end": item.line_end,
                    "entity_type": item.entity_type,
                    "timestamp": item.timestamp,
                    "content_hash": item.content_hash,
                    "actor_id": item.actor_id,
                    "actor_type": item.actor_type,
                    "session_id": item.session_id,
                    "project_id": item.project_id,
                    "language": item.language,
                    "source_data": item.source_data,
                    "metrics": item.metrics,
                    "tags": item.tags,
                    "embedding": item.embedding,
                }
                db_items.append(db_item)

            # Use optimized batch inserter
            result = await self.batch_optimizer.insert_context_items_batch(db_items)
            return result

        except Exception as e:
            logger.error("Optimized storage failed", error=str(e))
            return {"inserted": 0, "errors": len(items)}

    async def _generate_completion_report(
        self, processing_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate comprehensive completion report."""
        end_time = datetime.utcnow()
        total_duration = (end_time - self.start_time).total_seconds()

        # Get final performance metrics
        performance_metrics = self.performance_monitor.get_current_performance()
        performance_trends = self.performance_monitor.get_performance_trends(window_minutes=60)
        performance_alerts = self.performance_monitor.get_performance_alerts()

        # Get component statistics
        cache_stats = self.cache_manager.get_comprehensive_stats()
        database_stats = await self.database_pool.get_connection_stats()
        batch_stats = self.batch_processor.get_comprehensive_stats()
        insertion_stats = self.batch_optimizer.get_insertion_stats()

        # Calculate performance summary
        total_processed = processing_results.get("total_processed", 0)
        items_per_second = total_processed / max(0.1, total_duration)

        # Performance rating
        if items_per_second >= 500:
            performance_rating = "excellent"
        elif items_per_second >= 200:
            performance_rating = "good"
        elif items_per_second >= 100:
            performance_rating = "acceptable"
        else:
            performance_rating = "needs_improvement"

        comprehensive_report = {
            "execution_summary": {
                "status": "completed",
                "start_time": self.start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "total_duration_seconds": total_duration,
                "total_items_processed": total_processed,
                "total_errors": processing_results.get("total_errors", 0),
                "total_batches": processing_results.get("total_batches", 0),
                "items_per_second": items_per_second,
                "performance_rating": performance_rating,
            },
            "performance_metrics": performance_metrics,
            "performance_trends": performance_trends,
            "performance_alerts": performance_alerts,
            "component_statistics": {
                "cache_performance": cache_stats,
                "database_performance": database_stats,
                "batch_processing": batch_stats,
                "database_insertion": insertion_stats,
            },
            "optimization_effectiveness": {
                "cache_hit_rate_pct": cache_stats.get("embedding_cache", {}).get(
                    "memory_hit_rate_pct", 0
                ),
                "database_connection_efficiency": database_stats.get("pool_size", 0),
                "batch_processing_efficiency": 100 - batch_stats.get("error_rate_pct", 0),
                "insertion_throughput": insertion_stats.get("average_items_per_second", 0),
            },
            "recommendations": self._generate_optimization_recommendations(
                performance_metrics, cache_stats, database_stats, batch_stats
            ),
        }

        # Save detailed report
        report_file = (
            f"chat_import_performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        await self.performance_monitor.export_metrics_report(report_file)
        comprehensive_report["detailed_report_file"] = report_file

        return comprehensive_report

    def _generate_optimization_recommendations(
        self,
        performance_metrics: Dict[str, Any],
        cache_stats: Dict[str, Any],
        database_stats: Dict[str, Any],
        batch_stats: Dict[str, Any],
    ) -> List[Dict[str, str]]:
        """Generate optimization recommendations based on performance data."""
        recommendations = []

        # Cache performance recommendations
        embedding_cache = cache_stats.get("embedding_cache", {})
        hit_rate = embedding_cache.get("memory_hit_rate_pct", 0)

        if hit_rate < 70:
            recommendations.append(
                {
                    "category": "caching",
                    "priority": "high",
                    "recommendation": "Increase embedding cache size or TTL to improve hit rate",
                    "current_value": f"{hit_rate:.1f}%",
                    "target_value": ">80%",
                }
            )

        # Database performance recommendations
        avg_query_duration = database_stats.get("average_query_duration_ms", 0)
        if avg_query_duration > 100:
            recommendations.append(
                {
                    "category": "database",
                    "priority": "medium",
                    "recommendation": "Consider additional database indexes or query optimization",
                    "current_value": f"{avg_query_duration:.1f}ms",
                    "target_value": "<50ms",
                }
            )

        # Batch processing recommendations
        error_rate = batch_stats.get("error_rate_pct", 0)
        if error_rate > 2:
            recommendations.append(
                {
                    "category": "processing",
                    "priority": "high",
                    "recommendation": "Investigate and address batch processing errors",
                    "current_value": f"{error_rate:.1f}%",
                    "target_value": "<1%",
                }
            )

        # Throughput recommendations
        items_per_second = batch_stats.get("overall_items_per_second", 0)
        if items_per_second < 200:
            recommendations.append(
                {
                    "category": "throughput",
                    "priority": "medium",
                    "recommendation": "Consider increasing batch sizes or parallel processing",
                    "current_value": f"{items_per_second:.1f} items/sec",
                    "target_value": ">300 items/sec",
                }
            )

        if not recommendations:
            recommendations.append(
                {
                    "category": "general",
                    "priority": "info",
                    "recommendation": "System performance is optimal - continue monitoring",
                    "current_value": "All metrics within acceptable ranges",
                    "target_value": "Maintain current performance",
                }
            )

        return recommendations

    async def get_real_time_status(self) -> Dict[str, Any]:
        """Get real-time system status and performance."""
        if not self.is_initialized:
            return {"status": "not_initialized"}

        current_performance = self.performance_monitor.get_current_performance()
        alerts = self.performance_monitor.get_performance_alerts()

        # System health check
        health_checks = {
            "database_pool": "healthy" if self.database_pool else "failed",
            "cache_manager": "healthy" if self.cache_manager else "failed",
            "batch_processor": "healthy" if self.batch_processor else "failed",
            "performance_monitor": "healthy" if self.performance_monitor else "failed",
        }

        overall_health = (
            "healthy"
            if all(status == "healthy" for status in health_checks.values())
            else "degraded"
        )

        return {
            "system_status": {
                "overall_health": overall_health,
                "is_running": self.is_running,
                "initialization_status": "initialized"
                if self.is_initialized
                else "not_initialized",
                "component_health": health_checks,
            },
            "current_performance": current_performance,
            "active_alerts": alerts,
            "runtime_info": {
                "start_time": self.start_time.isoformat() if self.start_time else None,
                "total_processed": self.total_processed,
                "total_errors": self.total_errors,
            },
        }

    async def shutdown(self):
        """Gracefully shutdown the optimization system."""
        logger.info("Shutting down optimized chat import system")

        if self.performance_monitor:
            await self.performance_monitor.stop_collection()

        if self.chat_adapter:
            await self.chat_adapter.cleanup()

        if self.database_pool:
            await self.database_pool.close()

        if self.cache_manager:
            await self.cache_manager.cleanup_old_data()

        logger.info("Optimization system shutdown completed")


async def main():
    """Main execution function for the optimized chat import system."""

    # Configuration
    config = {
        "database_url": "postgresql://opsvi:opsvi_secure_password@localhost:5432/unified_context",
        "source_path": "/home/opsvi/master_root/chat_logs.db",
        "target_items": None,  # Process all items
        "log_level": "INFO",
    }

    # Setup logging
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    logger.info("Starting complete performance optimization system")

    try:
        # Initialize system
        system = OptimizedChatImportSystem(config)

        # Initialize all components
        init_result = await system.initialize()
        if init_result.get("status") != "success":
            logger.error("System initialization failed", result=init_result)
            return 1

        logger.info(
            "System initialized successfully",
            duration=init_result.get("initialization_duration"),
            components=len(init_result.get("components_initialized", [])),
        )

        # Execute optimized import
        execution_result = await system.execute_optimized_import(
            source_path=config.get("source_path"), target_items=config.get("target_items")
        )

        # Print results
        if execution_result.get("status") == "completed":
            summary = execution_result["execution_summary"]
            logger.info(
                "Import completed successfully",
                items_processed=summary["total_items_processed"],
                duration=summary["total_duration_seconds"],
                throughput=summary["items_per_second"],
                rating=summary["performance_rating"],
            )

            print("\n🎉 OPTIMIZED CHAT IMPORT COMPLETED SUCCESSFULLY!")
            print(f"📊 Items Processed: {summary['total_items_processed']:,}")
            print(f"⚡ Throughput: {summary['items_per_second']:.1f} items/second")
            print(f"⏱️  Duration: {summary['total_duration_seconds']:.1f} seconds")
            print(f"🏆 Performance Rating: {summary['performance_rating'].upper()}")
            print(f"📄 Report: {execution_result.get('detailed_report_file', 'N/A')}")

            # Print recommendations
            recommendations = execution_result.get("recommendations", [])
            if recommendations:
                print(f"\n📋 OPTIMIZATION RECOMMENDATIONS:")
                for i, rec in enumerate(recommendations, 1):
                    print(f"{i}. [{rec['category'].upper()}] {rec['recommendation']}")
                    print(f"   Current: {rec['current_value']} | Target: {rec['target_value']}")

        else:
            logger.error("Import execution failed", result=execution_result)
            return 1

        # Shutdown gracefully
        await system.shutdown()
        return 0

    except Exception as e:
        logger.error("Complete performance optimization failed", error=str(e))
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
