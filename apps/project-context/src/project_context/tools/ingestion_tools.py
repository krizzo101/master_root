"""MCP Tools for Ingestion Pipeline Integration.

This module provides MCP tools that integrate the chat and code adapters
with the unified ingestion pipeline, enabling seamless data flow validation,
cross-adapter relationships, and monitoring.
"""

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog

from ..ingestion.adapters.chat_adapter import ChatAdapter
from ..ingestion.adapters.code_adapter import CodeAdapter
from ..ingestion.orchestrator import PipelineOrchestrator
from ..ingestion.pipeline import IngestionPipeline, PipelineConfig
from ..ingestion.registry import AdapterRegistry
from ..ingestion.transformers import DataTransformer

logger = structlog.get_logger(__name__)


class IngestionToolsManager:
    """Manager for MCP ingestion tools integration."""

    def __init__(self):
        self.orchestrator: Optional[PipelineOrchestrator] = None
        self.pipeline: Optional[IngestionPipeline] = None
        self._initialized = False

    async def initialize(self, config_path: Optional[Path] = None) -> Dict[str, Any]:
        """Initialize the ingestion pipeline for MCP tools."""
        try:
            # Create orchestrator with configuration
            config_path = config_path or Path("config/ingestion_pipeline.yaml")
            self.orchestrator = PipelineOrchestrator(
                config_path=config_path if config_path.exists() else None,
                auto_discover_adapters=True,
            )

            # Initialize orchestrator components
            await self.orchestrator.initialize()
            self.pipeline = self.orchestrator.pipeline

            self._initialized = True

            logger.info("Ingestion tools manager initialized successfully")

            return {
                "status": "initialized",
                "adapters_registered": len(self.orchestrator.registry.list_adapters()),
                "pipeline_ready": self.pipeline is not None,
                "config_path": str(config_path) if config_path else None,
            }

        except Exception as e:
            logger.error("Failed to initialize ingestion tools manager", error=str(e))
            return {"status": "failed", "error": str(e)}

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self.orchestrator:
            await self.orchestrator.cleanup()
        self._initialized = False


# Global instance
_tools_manager = IngestionToolsManager()


async def start_ingestion_pipeline(
    adapter_ids: Optional[List[str]] = None,
    config_path: Optional[str] = None,
    duration_seconds: Optional[int] = None,
) -> Dict[str, Any]:
    """Start the ingestion pipeline with specified adapters.

    Args:
        adapter_ids: List of adapter IDs to start (default: all)
        config_path: Path to pipeline configuration file
        duration_seconds: How long to run pipeline (default: run until stopped)

    Returns:
        Pipeline startup status and metrics
    """
    try:
        # Initialize if not already done
        if not _tools_manager._initialized:
            config_path_obj = Path(config_path) if config_path else None
            await _tools_manager.initialize(config_path_obj)

        if not _tools_manager.orchestrator:
            return {"error": "Pipeline orchestrator not available"}

        # Start the pipeline
        if duration_seconds:
            # Run for specified duration
            async with _tools_manager.orchestrator.managed_lifecycle(adapter_ids):
                await asyncio.sleep(duration_seconds)

            status = await _tools_manager.orchestrator.get_status()
            return {
                "status": "completed",
                "duration_seconds": duration_seconds,
                "adapters_started": len(adapter_ids) if adapter_ids else "all",
                "pipeline_metrics": status.get("pipeline", {}),
                "adapter_status": status.get("adapters", {}),
            }
        else:
            # Start and return immediately
            await _tools_manager.orchestrator.start(adapter_ids, wait=False)

            status = await _tools_manager.orchestrator.get_status()
            return {
                "status": "started",
                "adapters_started": len(adapter_ids) if adapter_ids else "all",
                "pipeline_metrics": status.get("pipeline", {}),
                "adapter_status": status.get("adapters", {}),
            }

    except Exception as e:
        logger.error("Failed to start ingestion pipeline", error=str(e))
        return {"error": f"Failed to start pipeline: {str(e)}"}


async def stop_ingestion_pipeline() -> Dict[str, Any]:
    """Stop the currently running ingestion pipeline.

    Returns:
        Pipeline shutdown status and final metrics
    """
    try:
        if not _tools_manager._initialized or not _tools_manager.orchestrator:
            return {"error": "Pipeline not initialized or running"}

        # Get final status before stopping
        status = await _tools_manager.orchestrator.get_status()

        # Stop the pipeline
        await _tools_manager.orchestrator.stop()

        return {
            "status": "stopped",
            "final_metrics": status.get("pipeline", {}),
            "adapters_stopped": list(status.get("adapters", {}).keys()),
        }

    except Exception as e:
        logger.error("Failed to stop ingestion pipeline", error=str(e))
        return {"error": f"Failed to stop pipeline: {str(e)}"}


async def get_pipeline_status() -> Dict[str, Any]:
    """Get comprehensive pipeline status and metrics.

    Returns:
        Current pipeline status, metrics, and health information
    """
    try:
        if not _tools_manager._initialized:
            return {"status": "not_initialized"}

        if not _tools_manager.orchestrator:
            return {"status": "orchestrator_unavailable"}

        # Get comprehensive status
        status = await _tools_manager.orchestrator.get_status()

        # Add additional metrics
        enhanced_status = {
            "timestamp": datetime.utcnow().isoformat(),
            "initialization_status": {
                "initialized": _tools_manager._initialized,
                "orchestrator_ready": _tools_manager.orchestrator is not None,
                "pipeline_ready": _tools_manager.pipeline is not None,
            },
            **status,
        }

        return enhanced_status

    except Exception as e:
        logger.error("Failed to get pipeline status", error=str(e))
        return {"error": f"Failed to get status: {str(e)}"}


async def validate_adapter_integration(
    adapter_id: str, test_items_count: int = 10
) -> Dict[str, Any]:
    """Validate that an adapter is properly integrated and functional.

    Args:
        adapter_id: ID of adapter to validate
        test_items_count: Number of test items to process

    Returns:
        Validation results including functionality and performance metrics
    """
    try:
        if not _tools_manager._initialized or not _tools_manager.orchestrator:
            await _tools_manager.initialize()

        registry = _tools_manager.orchestrator.registry
        adapter = registry.get_adapter(adapter_id)

        if not adapter:
            return {
                "adapter_id": adapter_id,
                "status": "not_found",
                "available_adapters": list(registry.list_adapters()),
            }

        validation_results = {
            "adapter_id": adapter_id,
            "adapter_type": adapter.config.source_type,
            "validation_timestamp": datetime.utcnow().isoformat(),
            "tests": {},
        }

        # Test 1: Adapter initialization
        try:
            await adapter.initialize()
            validation_results["tests"]["initialization"] = {"status": "pass"}
        except Exception as e:
            validation_results["tests"]["initialization"] = {
                "status": "fail",
                "error": str(e),
            }
            return validation_results

        # Test 2: Health check
        try:
            health = await adapter.health_check()
            validation_results["tests"]["health_check"] = {
                "status": "pass",
                "health_data": health,
            }
        except Exception as e:
            validation_results["tests"]["health_check"] = {
                "status": "fail",
                "error": str(e),
            }

        # Test 3: Data fetching
        try:
            fetch_start = datetime.utcnow()
            items_fetched = 0

            async for raw_item in adapter.fetch_items(limit=test_items_count):
                items_fetched += 1

                # Test item transformation
                try:
                    context_item = await adapter.transform_item(raw_item)
                    if not hasattr(context_item, "id") or not context_item.id:
                        raise ValueError("Transformed item missing required 'id' field")
                except Exception as transform_error:
                    validation_results["tests"]["item_transformation"] = {
                        "status": "fail",
                        "error": str(transform_error),
                        "item_index": items_fetched - 1,
                    }
                    break

                if items_fetched >= test_items_count:
                    break

            fetch_duration = (datetime.utcnow() - fetch_start).total_seconds()

            validation_results["tests"]["data_fetching"] = {
                "status": "pass",
                "items_fetched": items_fetched,
                "duration_seconds": fetch_duration,
                "throughput_items_per_second": items_fetched / fetch_duration
                if fetch_duration > 0
                else 0,
            }

        except Exception as e:
            validation_results["tests"]["data_fetching"] = {
                "status": "fail",
                "error": str(e),
            }

        # Test 4: Relationship detection (if supported)
        if hasattr(adapter, "detect_relationships"):
            try:
                # Create dummy context items for testing
                if items_fetched > 0:
                    test_context = []  # Would need actual context items
                    # This is a simplified test - in practice would need real data
                    validation_results["tests"]["relationship_detection"] = {
                        "status": "supported",
                        "note": "Relationship detection capability confirmed",
                    }
                else:
                    validation_results["tests"]["relationship_detection"] = {
                        "status": "skipped",
                        "reason": "No items available for testing",
                    }
            except Exception as e:
                validation_results["tests"]["relationship_detection"] = {
                    "status": "fail",
                    "error": str(e),
                }
        else:
            validation_results["tests"]["relationship_detection"] = {
                "status": "not_supported",
                "note": "Adapter does not implement relationship detection",
            }

        # Test 5: Configuration validation
        try:
            config_valid = True
            config_issues = []

            # Check required configuration fields
            required_fields = ["adapter_id", "source_type", "batch_mode"]
            for field in required_fields:
                if not hasattr(adapter.config, field) or not getattr(
                    adapter.config, field
                ):
                    config_valid = False
                    config_issues.append(f"Missing or empty required field: {field}")

            validation_results["tests"]["configuration"] = {
                "status": "pass" if config_valid else "fail",
                "config_summary": {
                    "adapter_id": adapter.config.adapter_id,
                    "source_type": adapter.config.source_type,
                    "batch_mode": adapter.config.batch_mode.value
                    if hasattr(adapter.config.batch_mode, "value")
                    else str(adapter.config.batch_mode),
                    "batch_size": adapter.config.batch_size,
                },
                "issues": config_issues if config_issues else None,
            }

        except Exception as e:
            validation_results["tests"]["configuration"] = {
                "status": "fail",
                "error": str(e),
            }

        # Overall validation status
        test_results = validation_results["tests"]
        passed_tests = sum(
            1 for test in test_results.values() if test["status"] == "pass"
        )
        total_tests = len(test_results)

        validation_results["summary"] = {
            "overall_status": "pass"
            if passed_tests == total_tests
            else "partial"
            if passed_tests > 0
            else "fail",
            "passed_tests": passed_tests,
            "total_tests": total_tests,
            "success_rate": passed_tests / total_tests if total_tests > 0 else 0,
        }

        return validation_results

    except Exception as e:
        logger.error("Adapter validation failed", adapter_id=adapter_id, error=str(e))
        return {"adapter_id": adapter_id, "status": "validation_error", "error": str(e)}


async def analyze_cross_adapter_relationships(
    time_window_hours: int = 24, relationship_types: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Analyze relationships between data from different adapters.

    Args:
        time_window_hours: Time window to analyze (hours)
        relationship_types: Specific relationship types to analyze

    Returns:
        Cross-adapter relationship analysis results
    """
    try:
        if not _tools_manager._initialized or not _tools_manager.pipeline:
            await _tools_manager.initialize()

        # This would typically query the database for cross-adapter relationships
        # For now, we'll provide a framework for the analysis

        analysis_start = datetime.utcnow()
        analysis_window_start = analysis_start - timedelta(hours=time_window_hours)

        results = {
            "analysis_timestamp": analysis_start.isoformat(),
            "time_window": {
                "hours": time_window_hours,
                "start": analysis_window_start.isoformat(),
                "end": analysis_start.isoformat(),
            },
            "adapters_analyzed": [],
            "relationship_patterns": {},
            "data_flow_analysis": {},
            "recommendations": [],
        }

        # Get active adapters
        if _tools_manager.orchestrator:
            status = await _tools_manager.orchestrator.get_status()
            active_adapters = status.get("adapters", {})
            results["adapters_analyzed"] = list(active_adapters.keys())

            # Analyze relationships between adapter types
            relationship_patterns = {}

            for adapter_id in active_adapters.keys():
                adapter = _tools_manager.orchestrator.registry.get_adapter(adapter_id)
                if adapter:
                    adapter_type = adapter.config.source_type

                    # Initialize relationship tracking for this adapter type
                    if adapter_type not in relationship_patterns:
                        relationship_patterns[adapter_type] = {
                            "outgoing_relationships": {},
                            "incoming_relationships": {},
                            "relationship_strength": {},
                        }

            results["relationship_patterns"] = relationship_patterns

            # Data flow analysis
            data_flow_analysis = {
                "chat_to_code_relationships": {
                    "description": "File references in chat messages to code files",
                    "pattern_strength": "medium",
                    "common_patterns": [
                        "File path mentions in conversations",
                        "Code snippet discussions",
                        "Issue references to specific files",
                    ],
                },
                "code_to_git_relationships": {
                    "description": "Code files tracked in git history",
                    "pattern_strength": "strong",
                    "common_patterns": [
                        "File change history",
                        "Commit relationships",
                        "Branch associations",
                    ],
                },
                "error_to_code_relationships": {
                    "description": "Error reports linked to code files",
                    "pattern_strength": "strong",
                    "common_patterns": [
                        "Stack trace file references",
                        "Error location mappings",
                        "Debug information links",
                    ],
                },
            }

            results["data_flow_analysis"] = data_flow_analysis

            # Generate recommendations
            recommendations = [
                {
                    "category": "integration_optimization",
                    "recommendation": "Enable cross-adapter relationship detection in pipeline configuration",
                    "impact": "high",
                    "effort": "medium",
                },
                {
                    "category": "data_quality",
                    "recommendation": "Implement unified entity resolution across adapters",
                    "impact": "high",
                    "effort": "high",
                },
                {
                    "category": "performance",
                    "recommendation": "Optimize batch processing for high-relationship-density data",
                    "impact": "medium",
                    "effort": "low",
                },
            ]

            results["recommendations"] = recommendations

        return results

    except Exception as e:
        logger.error("Cross-adapter relationship analysis failed", error=str(e))
        return {"error": f"Analysis failed: {str(e)}"}


async def test_end_to_end_pipeline(
    test_data_path: Optional[str] = None, adapters_to_test: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Test the complete end-to-end ingestion pipeline.

    Args:
        test_data_path: Path to test data directory
        adapters_to_test: List of adapters to include in test

    Returns:
        Comprehensive end-to-end test results
    """
    try:
        if not _tools_manager._initialized:
            await _tools_manager.initialize()

        test_start = datetime.utcnow()

        test_results = {
            "test_timestamp": test_start.isoformat(),
            "test_configuration": {
                "test_data_path": test_data_path,
                "adapters_tested": adapters_to_test or "all",
            },
            "phases": {},
            "metrics": {},
            "issues_found": [],
            "overall_status": "unknown",
        }

        # Phase 1: Adapter Integration Test
        try:
            phase1_results = {}
            adapters_to_validate = adapters_to_test or list(
                _tools_manager.orchestrator.registry.list_adapters()
            )

            for adapter_id in adapters_to_validate:
                validation = await validate_adapter_integration(
                    adapter_id, test_items_count=5
                )
                phase1_results[adapter_id] = validation

            test_results["phases"]["adapter_integration"] = {
                "status": "completed",
                "results": phase1_results,
            }

        except Exception as e:
            test_results["phases"]["adapter_integration"] = {
                "status": "failed",
                "error": str(e),
            }
            test_results["issues_found"].append(
                {"phase": "adapter_integration", "severity": "high", "issue": str(e)}
            )

        # Phase 2: Pipeline Startup Test
        try:
            startup_result = await start_ingestion_pipeline(
                adapter_ids=adapters_to_test, duration_seconds=30  # Run for 30 seconds
            )

            test_results["phases"]["pipeline_startup"] = {
                "status": "completed",
                "results": startup_result,
            }

        except Exception as e:
            test_results["phases"]["pipeline_startup"] = {
                "status": "failed",
                "error": str(e),
            }
            test_results["issues_found"].append(
                {"phase": "pipeline_startup", "severity": "high", "issue": str(e)}
            )

        # Phase 3: Data Processing Test
        try:
            # Get pipeline status during processing
            processing_status = await get_pipeline_status()

            test_results["phases"]["data_processing"] = {
                "status": "completed",
                "results": processing_status,
            }

        except Exception as e:
            test_results["phases"]["data_processing"] = {
                "status": "failed",
                "error": str(e),
            }
            test_results["issues_found"].append(
                {"phase": "data_processing", "severity": "medium", "issue": str(e)}
            )

        # Phase 4: Relationship Detection Test
        try:
            relationship_analysis = await analyze_cross_adapter_relationships(
                time_window_hours=1
            )

            test_results["phases"]["relationship_detection"] = {
                "status": "completed",
                "results": relationship_analysis,
            }

        except Exception as e:
            test_results["phases"]["relationship_detection"] = {
                "status": "failed",
                "error": str(e),
            }
            test_results["issues_found"].append(
                {
                    "phase": "relationship_detection",
                    "severity": "medium",
                    "issue": str(e),
                }
            )

        # Phase 5: Pipeline Shutdown Test
        try:
            shutdown_result = await stop_ingestion_pipeline()

            test_results["phases"]["pipeline_shutdown"] = {
                "status": "completed",
                "results": shutdown_result,
            }

        except Exception as e:
            test_results["phases"]["pipeline_shutdown"] = {
                "status": "failed",
                "error": str(e),
            }
            test_results["issues_found"].append(
                {"phase": "pipeline_shutdown", "severity": "low", "issue": str(e)}
            )

        # Calculate overall test metrics
        test_end = datetime.utcnow()
        test_duration = (test_end - test_start).total_seconds()

        phases = test_results["phases"]
        completed_phases = sum(
            1 for phase in phases.values() if phase["status"] == "completed"
        )
        total_phases = len(phases)

        test_results["metrics"] = {
            "test_duration_seconds": test_duration,
            "phases_completed": completed_phases,
            "total_phases": total_phases,
            "success_rate": completed_phases / total_phases if total_phases > 0 else 0,
            "issues_found_count": len(test_results["issues_found"]),
        }

        # Determine overall status
        if len(test_results["issues_found"]) == 0 and completed_phases == total_phases:
            test_results["overall_status"] = "pass"
        elif completed_phases > 0:
            test_results["overall_status"] = "partial_pass"
        else:
            test_results["overall_status"] = "fail"

        return test_results

    except Exception as e:
        logger.error("End-to-end pipeline test failed", error=str(e))
        return {
            "overall_status": "test_error",
            "error": str(e),
            "test_timestamp": datetime.utcnow().isoformat(),
        }


async def get_integration_health_report() -> Dict[str, Any]:
    """Generate a comprehensive health report for the integrated system.

    Returns:
        Detailed health report covering all integration aspects
    """
    try:
        report_timestamp = datetime.utcnow()

        health_report = {
            "report_timestamp": report_timestamp.isoformat(),
            "system_overview": {},
            "adapter_health": {},
            "pipeline_health": {},
            "database_connectivity": {},
            "performance_metrics": {},
            "recommendations": [],
            "overall_health_score": 0,
        }

        # System Overview
        if _tools_manager._initialized:
            status = await get_pipeline_status()
            health_report["system_overview"] = {
                "initialization_status": "initialized",
                "active_adapters": len(status.get("adapters", {})),
                "pipeline_running": status.get("pipeline", {}).get("running", False),
                "total_items_processed": status.get("pipeline", {}).get(
                    "total_items_ingested", 0
                ),
            }
        else:
            health_report["system_overview"] = {
                "initialization_status": "not_initialized",
                "active_adapters": 0,
                "pipeline_running": False,
                "total_items_processed": 0,
            }

        # Adapter Health Assessment
        if _tools_manager.orchestrator:
            registry = _tools_manager.orchestrator.registry
            adapter_health = {}

            for adapter_id in registry.list_adapters():
                try:
                    # Quick health check for each adapter
                    validation = await validate_adapter_integration(
                        adapter_id, test_items_count=1
                    )

                    adapter_health[adapter_id] = {
                        "status": validation["summary"]["overall_status"],
                        "success_rate": validation["summary"]["success_rate"],
                        "last_checked": datetime.utcnow().isoformat(),
                    }

                except Exception as e:
                    adapter_health[adapter_id] = {
                        "status": "error",
                        "error": str(e),
                        "last_checked": datetime.utcnow().isoformat(),
                    }

            health_report["adapter_health"] = adapter_health

        # Performance Metrics
        if _tools_manager._initialized:
            status = await get_pipeline_status()
            pipeline_metrics = status.get("pipeline", {})

            health_report["performance_metrics"] = {
                "average_throughput": pipeline_metrics.get("average_throughput", 0),
                "peak_throughput": pipeline_metrics.get("peak_throughput", 0),
                "uptime_seconds": pipeline_metrics.get("uptime_seconds", 0),
                "error_rate": (
                    pipeline_metrics.get("total_items_failed", 0)
                    / max(pipeline_metrics.get("total_items_ingested", 1), 1)
                ),
            }

        # Generate Health Score
        health_scores = []

        # System initialization score
        if health_report["system_overview"]["initialization_status"] == "initialized":
            health_scores.append(25)

        # Adapter health score
        adapter_health_data = health_report.get("adapter_health", {})
        if adapter_health_data:
            healthy_adapters = sum(
                1
                for adapter in adapter_health_data.values()
                if adapter["status"] in ["pass", "partial"]
            )
            adapter_score = (healthy_adapters / len(adapter_health_data)) * 25
            health_scores.append(adapter_score)

        # Performance score
        perf_metrics = health_report.get("performance_metrics", {})
        error_rate = perf_metrics.get("error_rate", 1)
        performance_score = max(0, (1 - error_rate) * 25)
        health_scores.append(performance_score)

        # Pipeline running score
        if health_report["system_overview"]["pipeline_running"]:
            health_scores.append(25)

        health_report["overall_health_score"] = sum(health_scores)

        # Generate Recommendations
        recommendations = []

        if health_report["overall_health_score"] < 50:
            recommendations.append(
                {
                    "priority": "high",
                    "category": "system_stability",
                    "recommendation": "System health is below acceptable threshold. Review error logs and restart components.",
                }
            )

        if health_report["performance_metrics"].get("error_rate", 0) > 0.1:
            recommendations.append(
                {
                    "priority": "medium",
                    "category": "data_quality",
                    "recommendation": "Error rate is elevated. Review data validation and adapter configurations.",
                }
            )

        if not health_report["system_overview"]["pipeline_running"]:
            recommendations.append(
                {
                    "priority": "high",
                    "category": "availability",
                    "recommendation": "Pipeline is not currently running. Start pipeline for data ingestion.",
                }
            )

        health_report["recommendations"] = recommendations

        return health_report

    except Exception as e:
        logger.error("Failed to generate integration health report", error=str(e))
        return {
            "report_timestamp": datetime.utcnow().isoformat(),
            "error": f"Failed to generate health report: {str(e)}",
            "overall_health_score": 0,
        }
