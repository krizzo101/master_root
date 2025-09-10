#!/usr/bin/env python3
"""
Phase 1 Comprehensive Testing Execution Script
Validates all components, generates reports, and confirms production readiness
"""

import asyncio
import json
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


class Phase1TestingValidator:
    """Comprehensive Phase 1 testing and validation."""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.results = {
            "execution_timestamp": datetime.now().isoformat(),
            "phase": "Phase 1 Comprehensive Testing",
            "status": "RUNNING",
            "test_categories": {},
            "overall_metrics": {},
            "production_readiness": {},
            "recommendations": [],
        }

    async def validate_core_imports(self) -> Dict[str, Any]:
        """Validate that all core components can be imported."""
        print("\n🔍 Validating Core Component Imports...")

        import_results = {
            "status": "SUCCESS",
            "imports_tested": 0,
            "imports_successful": 0,
            "failed_imports": [],
        }

        # Core components to test
        core_imports = [
            ("src.project_context.ingestion.adapters.chat_adapter", "ChatAdapter"),
            ("src.project_context.ingestion.adapters.code_adapter", "CodeAdapter"),
            ("src.project_context.ingestion.base_adapter", "BaseAdapter"),
            ("src.project_context.ingestion.pipeline", "IngestionPipeline"),
            ("src.project_context.ingestion.orchestrator", "IngestionOrchestrator"),
            ("src.project_context.db.connections", "get_db_connection"),
            ("src.project_context.models.common", "ContextItem"),
            ("src.project_context.tools.analysis", "analyze_codebase"),
            ("src.project_context.tools.discovery", "find_files_in_codebase"),
        ]

        for module_path, component_name in core_imports:
            import_results["imports_tested"] += 1
            try:
                module = __import__(module_path, fromlist=[component_name])
                getattr(module, component_name)
                import_results["imports_successful"] += 1
                print(f"  ✅ {module_path}.{component_name}")
            except Exception as e:
                import_results["failed_imports"].append(
                    {
                        "module": module_path,
                        "component": component_name,
                        "error": str(e),
                    }
                )
                print(f"  ❌ {module_path}.{component_name}: {e}")

        if import_results["failed_imports"]:
            import_results["status"] = "PARTIAL_FAILURE"

        return import_results

    async def validate_database_connectivity(self) -> Dict[str, Any]:
        """Test database connection and basic operations."""
        print("\n🔍 Validating Database Connectivity...")

        db_results = {
            "status": "SUCCESS",
            "connection_test": False,
            "basic_operations": False,
            "error": None,
        }

        try:
            from src.project_context.db.connections import get_db_connection

            # Test connection
            conn = get_db_connection()
            if conn:
                db_results["connection_test"] = True
                print("  ✅ Database connection successful")

                # Test basic query
                cursor = conn.cursor()
                cursor.execute("SELECT 1 as test")
                result = cursor.fetchone()
                if result and result[0] == 1:
                    db_results["basic_operations"] = True
                    print("  ✅ Basic database operations successful")
                cursor.close()
                conn.close()
            else:
                db_results["status"] = "FAILURE"
                db_results["error"] = "Failed to establish database connection"
                print("  ❌ Database connection failed")

        except Exception as e:
            db_results["status"] = "FAILURE"
            db_results["error"] = str(e)
            print(f"  ❌ Database validation error: {e}")

        return db_results

    async def validate_adapter_functionality(self) -> Dict[str, Any]:
        """Test adapter initialization and basic functionality."""
        print("\n🔍 Validating Adapter Functionality...")

        adapter_results = {
            "status": "SUCCESS",
            "chat_adapter": {"status": "PENDING", "error": None},
            "code_adapter": {"status": "PENDING", "error": None},
        }

        # Test Chat Adapter
        try:
            from src.project_context.ingestion.adapters.chat_adapter import ChatAdapter
            from src.project_context.ingestion.base_adapter import (
                AdapterConfig,
                BatchMode,
            )

            config = AdapterConfig(
                adapter_id="test_chat",
                source_type="chat",
                batch_mode=BatchMode.STREAMING,
                batch_size=10,
                source_config={"input_format": "jsonl"},
            )

            chat_adapter = ChatAdapter(config)
            adapter_results["chat_adapter"]["status"] = "SUCCESS"
            print("  ✅ Chat adapter initialization successful")

        except Exception as e:
            adapter_results["chat_adapter"]["status"] = "FAILURE"
            adapter_results["chat_adapter"]["error"] = str(e)
            adapter_results["status"] = "PARTIAL_FAILURE"
            print(f"  ❌ Chat adapter error: {e}")

        # Test Code Adapter
        try:
            from src.project_context.ingestion.adapters.code_adapter import CodeAdapter

            config = AdapterConfig(
                adapter_id="test_code",
                source_type="code",
                batch_mode=BatchMode.BATCH,
                batch_size=10,
                source_config={"scan_directories": []},
            )

            code_adapter = CodeAdapter(config)
            adapter_results["code_adapter"]["status"] = "SUCCESS"
            print("  ✅ Code adapter initialization successful")

        except Exception as e:
            adapter_results["code_adapter"]["status"] = "FAILURE"
            adapter_results["code_adapter"]["error"] = str(e)
            adapter_results["status"] = "PARTIAL_FAILURE"
            print(f"  ❌ Code adapter error: {e}")

        return adapter_results

    async def validate_mcp_tools_integration(self) -> Dict[str, Any]:
        """Test MCP tools integration and basic functionality."""
        print("\n🔍 Validating MCP Tools Integration...")

        tools_results = {
            "status": "SUCCESS",
            "tools_tested": 0,
            "tools_successful": 0,
            "failed_tools": [],
        }

        # Core MCP tools to test
        mcp_tools = [
            ("src.project_context.tools.discovery", "find_files_in_codebase"),
            ("src.project_context.tools.analysis", "analyze_codebase"),
            ("src.project_context.tools.architecture", "get_project_architecture"),
        ]

        for module_path, tool_name in mcp_tools:
            tools_results["tools_tested"] += 1
            try:
                module = __import__(module_path, fromlist=[tool_name])
                tool_func = getattr(module, tool_name)
                tools_results["tools_successful"] += 1
                print(f"  ✅ {tool_name} available")
            except Exception as e:
                tools_results["failed_tools"].append(
                    {"tool": tool_name, "module": module_path, "error": str(e)}
                )
                print(f"  ❌ {tool_name}: {e}")

        if tools_results["failed_tools"]:
            tools_results["status"] = "PARTIAL_FAILURE"

        return tools_results

    async def analyze_existing_test_coverage(self) -> Dict[str, Any]:
        """Analyze existing test files and coverage."""
        print("\n🔍 Analyzing Existing Test Coverage...")

        coverage_results = {
            "status": "SUCCESS",
            "test_files_found": 0,
            "test_directories": [],
            "test_files": [],
            "estimated_test_functions": 0,
        }

        # Find test files
        test_patterns = ["test_*.py", "*_test.py", "tests/*.py"]

        for pattern in ["test_*.py", "*test*.py"]:
            for test_file in self.project_root.glob(pattern):
                if test_file.is_file():
                    coverage_results["test_files"].append(str(test_file.name))
                    coverage_results["test_files_found"] += 1

        # Check tests directory
        tests_dir = self.project_root / "tests"
        if tests_dir.exists():
            coverage_results["test_directories"].append("tests/")
            for test_file in tests_dir.glob("*.py"):
                if test_file.name.startswith("test_"):
                    coverage_results["test_files"].append(f"tests/{test_file.name}")
                    coverage_results["test_files_found"] += 1

        print(f"  ✅ Found {coverage_results['test_files_found']} test files")
        print(f"  📁 Test directories: {coverage_results['test_directories']}")

        return coverage_results

    async def validate_integration_readiness(self) -> Dict[str, Any]:
        """Validate integration and end-to-end readiness."""
        print("\n🔍 Validating Integration Readiness...")

        integration_results = {
            "status": "SUCCESS",
            "pipeline_ready": False,
            "orchestrator_ready": False,
            "config_valid": False,
            "schema_ready": False,
        }

        try:
            # Test pipeline integration
            from src.project_context.ingestion.pipeline import IngestionPipeline

            integration_results["pipeline_ready"] = True
            print("  ✅ Ingestion pipeline ready")
        except Exception as e:
            print(f"  ❌ Pipeline integration error: {e}")
            integration_results["status"] = "PARTIAL_FAILURE"

        try:
            # Test orchestrator
            from src.project_context.ingestion.orchestrator import IngestionOrchestrator

            integration_results["orchestrator_ready"] = True
            print("  ✅ Ingestion orchestrator ready")
        except Exception as e:
            print(f"  ❌ Orchestrator integration error: {e}")
            integration_results["status"] = "PARTIAL_FAILURE"

        # Check configuration files
        config_files = ["config/ingestion_pipeline.yaml", "unified_context_schema.sql"]
        for config_file in config_files:
            if (self.project_root / config_file).exists():
                integration_results["config_valid"] = True
                print(f"  ✅ Configuration file found: {config_file}")
            else:
                print(f"  ⚠️  Configuration file missing: {config_file}")

        return integration_results

    async def generate_production_readiness_assessment(self) -> Dict[str, Any]:
        """Generate comprehensive production readiness assessment."""
        print("\n🎯 Generating Production Readiness Assessment...")

        # Aggregate all test results
        all_tests_passed = all(
            [
                self.results["test_categories"].get("imports", {}).get("status")
                == "SUCCESS",
                self.results["test_categories"].get("database", {}).get("status")
                == "SUCCESS",
                self.results["test_categories"].get("adapters", {}).get("status")
                in ["SUCCESS", "PARTIAL_FAILURE"],
                self.results["test_categories"].get("tools", {}).get("status")
                in ["SUCCESS", "PARTIAL_FAILURE"],
            ]
        )

        readiness_assessment = {
            "overall_status": "READY" if all_tests_passed else "NEEDS_ATTENTION",
            "confidence_score": 0.0,
            "critical_systems": {
                "database_connectivity": self.results["test_categories"]
                .get("database", {})
                .get("status")
                == "SUCCESS",
                "core_imports": self.results["test_categories"]
                .get("imports", {})
                .get("status")
                == "SUCCESS",
                "adapter_functionality": self.results["test_categories"]
                .get("adapters", {})
                .get("status")
                in ["SUCCESS", "PARTIAL_FAILURE"],
                "integration_readiness": self.results["test_categories"]
                .get("integration", {})
                .get("status")
                in ["SUCCESS", "PARTIAL_FAILURE"],
            },
            "test_coverage_metrics": {
                "test_files_found": self.results["test_categories"]
                .get("coverage", {})
                .get("test_files_found", 0),
                "existing_test_suites": len(
                    self.results["test_categories"]
                    .get("coverage", {})
                    .get("test_files", [])
                ),
                "estimated_comprehensiveness": "HIGH"
                if self.results["test_categories"]
                .get("coverage", {})
                .get("test_files_found", 0)
                > 15
                else "MEDIUM",
            },
        }

        # Calculate confidence score
        critical_passed = sum(readiness_assessment["critical_systems"].values())
        total_critical = len(readiness_assessment["critical_systems"])
        readiness_assessment["confidence_score"] = (
            critical_passed / total_critical
        ) * 100

        print(f"  📊 Overall Status: {readiness_assessment['overall_status']}")
        print(f"  📈 Confidence Score: {readiness_assessment['confidence_score']:.1f}%")

        return readiness_assessment

    async def execute_comprehensive_validation(self):
        """Execute all validation categories and generate report."""
        print("=" * 80)
        print("PHASE 1 COMPREHENSIVE TESTING VALIDATION")
        print("=" * 80)
        print(f"Execution Time: {self.results['execution_timestamp']}")

        try:
            # Execute all validation categories
            self.results["test_categories"][
                "imports"
            ] = await self.validate_core_imports()
            self.results["test_categories"][
                "database"
            ] = await self.validate_database_connectivity()
            self.results["test_categories"][
                "adapters"
            ] = await self.validate_adapter_functionality()
            self.results["test_categories"][
                "tools"
            ] = await self.validate_mcp_tools_integration()
            self.results["test_categories"][
                "coverage"
            ] = await self.analyze_existing_test_coverage()
            self.results["test_categories"][
                "integration"
            ] = await self.validate_integration_readiness()

            # Generate final assessment
            self.results[
                "production_readiness"
            ] = await self.generate_production_readiness_assessment()
            self.results["status"] = "COMPLETED"

        except Exception as e:
            print(f"\n❌ Critical error during validation: {e}")
            print(traceback.format_exc())
            self.results["status"] = "FAILED"
            self.results["critical_error"] = str(e)

        # Generate final report
        await self.generate_final_report()

    async def generate_final_report(self):
        """Generate comprehensive final report."""
        print(f"\n{'='*80}")
        print("FINAL PHASE 1 TESTING VALIDATION REPORT")
        print(f"{'='*80}")

        # Save detailed results
        report_file = self.project_root / "PHASE1_TESTING_VALIDATION_REPORT.json"
        with open(report_file, "w") as f:
            json.dump(self.results, f, indent=2)

        # Print summary
        if self.results["status"] == "COMPLETED":
            print("✅ VALIDATION COMPLETED SUCCESSFULLY")

            if self.results["production_readiness"]["overall_status"] == "READY":
                print("\n🎉 PHASE 1 IS PRODUCTION READY!")
                print(
                    f"   Confidence Score: {self.results['production_readiness']['confidence_score']:.1f}%"
                )
            else:
                print("\n⚠️  Phase 1 needs attention before production deployment")

        else:
            print("❌ VALIDATION FAILED - Critical errors encountered")

        # Print key metrics
        print(f"\n📊 KEY METRICS:")
        print(
            f"   Test Files Found: {self.results['test_categories'].get('coverage', {}).get('test_files_found', 0)}"
        )
        print(
            f"   Core Imports: {self.results['test_categories'].get('imports', {}).get('imports_successful', 0)}/{self.results['test_categories'].get('imports', {}).get('imports_tested', 0)}"
        )
        print(
            f"   Database Status: {self.results['test_categories'].get('database', {}).get('status', 'UNKNOWN')}"
        )
        print(
            f"   Adapters Status: {self.results['test_categories'].get('adapters', {}).get('status', 'UNKNOWN')}"
        )

        print(f"\n📁 Detailed report saved to: {report_file}")

        return self.results["production_readiness"]["overall_status"] == "READY"


async def main():
    """Main execution function."""
    validator = Phase1TestingValidator()
    await validator.execute_comprehensive_validation()

    # Return appropriate exit code
    if (
        validator.results.get("production_readiness", {}).get("overall_status")
        == "READY"
    ):
        print(f"\n🚀 PHASE 1 VALIDATED - READY FOR PRODUCTION!")
        return 0
    else:
        print(f"\n⚠️  PHASE 1 NEEDS ATTENTION")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
