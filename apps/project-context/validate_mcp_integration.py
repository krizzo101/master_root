#!/usr/bin/env python3
"""
MCP Integration Validation Script

This script validates the integration between chat and code adapters
with the MCP server framework, ensuring all components work together
seamlessly.
"""

import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Dict, List

import structlog

# Add project to path
sys.path.append(str(Path(__file__).parent / "src"))

from project_context.tools.ingestion_tools import (
    _tools_manager,
    analyze_cross_adapter_relationships,
    get_integration_health_report,
    get_pipeline_status,
    start_ingestion_pipeline,
    stop_ingestion_pipeline,
    test_end_to_end_pipeline,
    validate_adapter_integration,
)

logger = structlog.get_logger(__name__)


class MCPIntegrationValidator:
    """Comprehensive MCP integration validation."""

    def __init__(self):
        self.results = {
            "validation_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "tests_run": [],
            "passed_tests": 0,
            "failed_tests": 0,
            "warnings": [],
            "recommendations": [],
        }

    async def run_all_validations(self) -> Dict:
        """Run all validation tests."""
        print("🚀 Starting MCP Integration Validation")
        print("=" * 50)

        # Test 1: Tools Manager Initialization
        await self._test_tools_manager_init()

        # Test 2: Individual Adapter Validation
        await self._test_individual_adapters()

        # Test 3: Pipeline Integration
        await self._test_pipeline_integration()

        # Test 4: Cross-Adapter Relationships
        await self._test_cross_adapter_relationships()

        # Test 5: End-to-End Pipeline Test
        await self._test_end_to_end_pipeline()

        # Test 6: Health Reporting
        await self._test_health_reporting()

        # Test 7: MCP Server Integration
        await self._test_mcp_server_integration()

        # Generate final report
        self._generate_final_report()

        return self.results

    async def _test_tools_manager_init(self):
        """Test tools manager initialization."""
        test_name = "Tools Manager Initialization"
        print(f"\n🔧 Testing: {test_name}")

        try:
            # Test initialization
            config_path = Path("config/ingestion_pipeline.yaml")
            result = await _tools_manager.initialize(config_path)

            if result.get("status") == "initialized":
                self._record_pass(test_name, "Tools manager initialized successfully")
                print(f"  ✅ {test_name} - PASSED")
                print(
                    f"     Adapters registered: {result.get('adapters_registered', 0)}"
                )
            else:
                self._record_fail(
                    test_name,
                    f"Initialization failed: {result.get('error', 'Unknown error')}",
                )

        except Exception as e:
            self._record_fail(test_name, f"Exception during initialization: {str(e)}")

    async def _test_individual_adapters(self):
        """Test individual adapter validation."""
        test_name = "Individual Adapter Validation"
        print(f"\n🔍 Testing: {test_name}")

        adapters_to_test = ["chat", "code", "git", "error"]
        adapter_results = {}

        for adapter_id in adapters_to_test:
            try:
                print(f"  Testing adapter: {adapter_id}")
                result = await validate_adapter_integration(
                    adapter_id, test_items_count=3
                )

                adapter_results[adapter_id] = result

                if result.get("summary", {}).get("overall_status") in [
                    "pass",
                    "partial",
                ]:
                    print(f"    ✅ {adapter_id} - {result['summary']['overall_status']}")
                else:
                    print(
                        f"    ❌ {adapter_id} - {result.get('summary', {}).get('overall_status', 'failed')}"
                    )
                    self._record_warning(
                        f"Adapter {adapter_id} validation issues detected"
                    )

            except Exception as e:
                print(f"    ❌ {adapter_id} - Exception: {str(e)}")
                self._record_fail(f"{test_name} - {adapter_id}", str(e))

        # Overall adapter validation assessment
        successful_adapters = sum(
            1
            for result in adapter_results.values()
            if result.get("summary", {}).get("overall_status") in ["pass", "partial"]
        )

        if successful_adapters >= len(adapters_to_test) * 0.75:  # 75% success rate
            self._record_pass(
                test_name,
                f"{successful_adapters}/{len(adapters_to_test)} adapters validated",
            )
        else:
            self._record_fail(
                test_name,
                f"Only {successful_adapters}/{len(adapters_to_test)} adapters validated successfully",
            )

    async def _test_pipeline_integration(self):
        """Test pipeline integration."""
        test_name = "Pipeline Integration"
        print(f"\n⚙️ Testing: {test_name}")

        try:
            # Test pipeline startup
            print("  Starting pipeline...")
            start_result = await start_ingestion_pipeline(
                adapter_ids=["chat", "code"], duration_seconds=15  # Short test run
            )

            if start_result.get("status") == "completed":
                print("  ✅ Pipeline started and ran successfully")

                # Check final metrics
                metrics = start_result.get("pipeline_metrics", {})
                items_processed = metrics.get("total_items_ingested", 0)

                if items_processed > 0:
                    print(f"  ✅ Pipeline processed {items_processed} items")
                    self._record_pass(
                        test_name,
                        f"Pipeline processed {items_processed} items in test run",
                    )
                else:
                    print("  ⚠️ Pipeline ran but processed no items")
                    self._record_warning("Pipeline processed no items during test run")
                    self._record_pass(
                        test_name, "Pipeline startup and operation successful"
                    )
            else:
                self._record_fail(
                    test_name,
                    f"Pipeline startup failed: {start_result.get('error', 'Unknown error')}",
                )

        except Exception as e:
            self._record_fail(test_name, f"Pipeline integration test failed: {str(e)}")

    async def _test_cross_adapter_relationships(self):
        """Test cross-adapter relationship analysis."""
        test_name = "Cross-Adapter Relationships"
        print(f"\n🔗 Testing: {test_name}")

        try:
            result = await analyze_cross_adapter_relationships(time_window_hours=1)

            if "error" not in result:
                adapters_analyzed = len(result.get("adapters_analyzed", []))
                relationship_patterns = len(result.get("relationship_patterns", {}))

                print(f"  ✅ Analyzed {adapters_analyzed} adapters")
                print(f"  ✅ Identified {relationship_patterns} relationship patterns")

                self._record_pass(
                    test_name,
                    f"Cross-adapter analysis completed for {adapters_analyzed} adapters",
                )
            else:
                self._record_fail(
                    test_name, f"Relationship analysis failed: {result['error']}"
                )

        except Exception as e:
            self._record_fail(
                test_name, f"Cross-adapter relationship test failed: {str(e)}"
            )

    async def _test_end_to_end_pipeline(self):
        """Test end-to-end pipeline functionality."""
        test_name = "End-to-End Pipeline Test"
        print(f"\n🔄 Testing: {test_name}")

        try:
            result = await test_end_to_end_pipeline(adapters_to_test=["chat", "code"])

            overall_status = result.get("overall_status", "unknown")

            if overall_status in ["pass", "partial_pass"]:
                phases_completed = result.get("metrics", {}).get("phases_completed", 0)
                total_phases = result.get("metrics", {}).get("total_phases", 0)

                print(f"  ✅ End-to-end test: {overall_status}")
                print(f"  ✅ Completed {phases_completed}/{total_phases} test phases")

                self._record_pass(
                    test_name,
                    f"End-to-end test {overall_status}: {phases_completed}/{total_phases} phases",
                )
            else:
                issues = len(result.get("issues_found", []))
                self._record_fail(
                    test_name, f"End-to-end test failed with {issues} issues"
                )

        except Exception as e:
            self._record_fail(test_name, f"End-to-end pipeline test failed: {str(e)}")

    async def _test_health_reporting(self):
        """Test health reporting functionality."""
        test_name = "Health Reporting"
        print(f"\n🏥 Testing: {test_name}")

        try:
            result = await get_integration_health_report()

            if "error" not in result:
                health_score = result.get("overall_health_score", 0)
                active_adapters = result.get("system_overview", {}).get(
                    "active_adapters", 0
                )

                print(f"  ✅ Health report generated")
                print(f"  📊 Health score: {health_score}/100")
                print(f"  📊 Active adapters: {active_adapters}")

                if health_score >= 50:
                    self._record_pass(
                        test_name,
                        f"Health reporting working, score: {health_score}/100",
                    )
                else:
                    self._record_warning(f"Health score is low: {health_score}/100")
                    self._record_pass(
                        test_name,
                        "Health reporting functional but indicates system issues",
                    )
            else:
                self._record_fail(
                    test_name, f"Health report generation failed: {result['error']}"
                )

        except Exception as e:
            self._record_fail(test_name, f"Health reporting test failed: {str(e)}")

    async def _test_mcp_server_integration(self):
        """Test MCP server integration."""
        test_name = "MCP Server Integration"
        print(f"\n🌐 Testing: {test_name}")

        try:
            # Test that we can import and use the MCP tools
            from fastmcp import FastMCP
            from project_context.tools import register_all_tools

            # Create a test MCP instance
            test_mcp = FastMCP(name="test-integration", version="0.1.0")

            # Try to register tools
            registered_tools = register_all_tools(test_mcp)

            print(f"  ✅ MCP server integration working")
            print(f"  📝 Registered {len(registered_tools)} tools")

            # Check for ingestion tools specifically
            ingestion_tools = [
                tool
                for tool in registered_tools
                if "pipeline" in tool or "adapter" in tool
            ]

            if len(ingestion_tools) >= 6:  # We should have at least 6 ingestion tools
                print(f"  ✅ Ingestion tools integrated: {len(ingestion_tools)} tools")
                self._record_pass(
                    test_name,
                    f"MCP integration successful with {len(ingestion_tools)} ingestion tools",
                )
            else:
                self._record_warning(
                    f"Expected more ingestion tools, found: {len(ingestion_tools)}"
                )
                self._record_pass(
                    test_name, f"MCP integration working but may be incomplete"
                )

        except Exception as e:
            self._record_fail(
                test_name, f"MCP server integration test failed: {str(e)}"
            )

    def _record_pass(self, test_name: str, details: str):
        """Record a passed test."""
        self.results["tests_run"].append(
            {"test": test_name, "status": "PASS", "details": details}
        )
        self.results["passed_tests"] += 1

    def _record_fail(self, test_name: str, error: str):
        """Record a failed test."""
        self.results["tests_run"].append(
            {"test": test_name, "status": "FAIL", "error": error}
        )
        self.results["failed_tests"] += 1
        print(f"  ❌ {test_name} - FAILED: {error}")

    def _record_warning(self, message: str):
        """Record a warning."""
        self.results["warnings"].append(message)
        print(f"  ⚠️ WARNING: {message}")

    def _generate_final_report(self):
        """Generate final validation report."""
        print(f"\n" + "=" * 50)
        print("📋 VALIDATION SUMMARY")
        print("=" * 50)

        total_tests = self.results["passed_tests"] + self.results["failed_tests"]
        success_rate = (
            (self.results["passed_tests"] / total_tests) * 100 if total_tests > 0 else 0
        )

        print(f"Tests Run: {total_tests}")
        print(f"Passed: {self.results['passed_tests']}")
        print(f"Failed: {self.results['failed_tests']}")
        print(f"Warnings: {len(self.results['warnings'])}")
        print(f"Success Rate: {success_rate:.1f}%")

        # Generate recommendations
        recommendations = []

        if self.results["failed_tests"] > 0:
            recommendations.append(
                "Address failed tests before deploying to production"
            )

        if len(self.results["warnings"]) > 3:
            recommendations.append("Review and resolve system warnings")

        if success_rate < 80:
            recommendations.append(
                "Success rate below 80% - significant improvements needed"
            )
        elif success_rate < 95:
            recommendations.append(
                "Minor improvements recommended for better reliability"
            )
        else:
            recommendations.append("System integration is excellent!")

        self.results["recommendations"] = recommendations

        print(f"\n📝 RECOMMENDATIONS:")
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec}")

        # Overall status
        if success_rate >= 90 and self.results["failed_tests"] == 0:
            print(f"\n🎉 OVERALL STATUS: EXCELLENT")
            print("The MCP integration is working perfectly!")
        elif success_rate >= 80:
            print(f"\n✅ OVERALL STATUS: GOOD")
            print("The MCP integration is working well with minor issues.")
        elif success_rate >= 60:
            print(f"\n⚠️ OVERALL STATUS: NEEDS IMPROVEMENT")
            print(
                "The MCP integration has significant issues that should be addressed."
            )
        else:
            print(f"\n❌ OVERALL STATUS: POOR")
            print("The MCP integration requires major fixes before use.")


async def main():
    """Main validation function."""
    validator = MCPIntegrationValidator()

    try:
        results = await validator.run_all_validations()

        # Save results to file
        output_file = Path("mcp_integration_validation_report.json")
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)

        print(f"\n📁 Detailed report saved to: {output_file}")

        # Exit with appropriate code
        if results["failed_tests"] == 0:
            sys.exit(0)  # Success
        else:
            sys.exit(1)  # Failures detected

    except Exception as e:
        print(f"\n💥 CRITICAL ERROR: Validation script failed: {str(e)}")
        sys.exit(2)

    finally:
        # Cleanup
        try:
            await _tools_manager.cleanup()
        except:
            pass


if __name__ == "__main__":
    asyncio.run(main())
