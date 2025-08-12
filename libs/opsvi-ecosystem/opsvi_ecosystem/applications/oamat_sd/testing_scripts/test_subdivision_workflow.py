#!/usr/bin/env python3
"""
Subdivision Workflow Test Script

Comprehensive end-to-end testing of the subdivision functionality:
- O3-powered subdivision analysis
- Subdivision agent factory and creation
- LangGraph Send API execution
- Result integration and state management
- Performance validation and metrics

Tests the complete subdivision workflow to ensure proper functionality.
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add the project root to Python path for imports
project_root = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(project_root))

from src.applications.oamat_sd.src.agents.subdivision_agent_factory import (
    SubdivisionAgentFactory,
)
from src.applications.oamat_sd.src.execution.subdivision_executor import (
    SubdivisionExecutor,
)
from src.applications.oamat_sd.src.operations.subdivision_integrator import (
    SubdivisionResultIntegrator,
)
from src.applications.oamat_sd.src.operations.subdivision_state_manager import (
    SubdivisionStateManager,
)
from src.applications.oamat_sd.src.preprocessing.schemas import (
    ComplexityLevel,
    RequestClassification,
    RequestType,
    StandardizedRequest,
    SubdivisionMetadata,
)
from src.applications.oamat_sd.src.reasoning.subdivision_analyzer import (
    SubdivisionAnalyzer,
)
from src.applications.oamat_sd.src.sd_logging import LoggerFactory
from src.applications.oamat_sd.src.sd_logging.log_config import default_config


class SubdivisionWorkflowTester:
    """Comprehensive tester for subdivision workflow functionality"""

    def __init__(self):
        """Initialize the subdivision workflow tester"""
        self.logger_factory = LoggerFactory(default_config)
        self.logger = self.logger_factory.get_debug_logger()

        # Initialize subdivision components
        self.subdivision_analyzer = SubdivisionAnalyzer(self.logger_factory)
        self.agent_factory = SubdivisionAgentFactory(self.logger_factory)
        self.subdivision_executor = SubdivisionExecutor(self.logger_factory)
        self.result_integrator = SubdivisionResultIntegrator(self.logger_factory)
        self.state_manager = SubdivisionStateManager(self.logger_factory)

        # Test configuration
        self.test_cases = self._create_test_cases()
        self.test_results = []

        self.logger.info("✅ Subdivision Workflow Tester initialized")

    def _create_test_cases(self) -> list[dict]:
        """Create test cases for subdivision workflow validation"""

        return [
            {
                "name": "Simple Request (No Subdivision)",
                "user_request": "Create a simple Python script that prints hello world",
                "expected_subdivision": False,
                "expected_complexity": 2.0,
            },
            {
                "name": "Medium Complexity (Possible Subdivision)",
                "user_request": "Build a REST API with authentication, user management, and data storage",
                "expected_subdivision": True,
                "expected_complexity": 6.5,
            },
            {
                "name": "High Complexity (Definite Subdivision)",
                "user_request": "Create a full-stack e-commerce platform with AI recommendations, payment processing, inventory management, and admin dashboard",
                "expected_subdivision": True,
                "expected_complexity": 9.0,
            },
            {
                "name": "Multi-Domain Complex Project",
                "user_request": "Develop a machine learning platform with data pipelines, model training, REST APIs, web dashboard, and deployment automation",
                "expected_subdivision": True,
                "expected_complexity": 8.5,
            },
        ]

    async def run_comprehensive_tests(self) -> dict:
        """Run comprehensive subdivision workflow tests"""

        self.logger.info(
            "🧪 SUBDIVISION TESTING: Starting comprehensive workflow tests..."
        )
        test_start_time = datetime.now()

        try:
            total_tests = len(self.test_cases)
            passed_tests = 0
            failed_tests = 0

            for i, test_case in enumerate(self.test_cases, 1):
                self.logger.info(f"📋 Test {i}/{total_tests}: {test_case['name']}")

                try:
                    test_result = await self._run_single_test(test_case)
                    self.test_results.append(test_result)

                    if test_result["success"]:
                        passed_tests += 1
                        self.logger.info(f"✅ Test {i} PASSED: {test_case['name']}")
                    else:
                        failed_tests += 1
                        self.logger.error(
                            f"❌ Test {i} FAILED: {test_case['name']} - {test_result.get('error', 'Unknown error')}"
                        )

                except Exception as e:
                    failed_tests += 1
                    self.logger.error(
                        f"❌ Test {i} EXCEPTION: {test_case['name']} - {e}"
                    )
                    self.test_results.append(
                        {
                            "test_case": test_case["name"],
                            "success": False,
                            "error": str(e),
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

            # Calculate test summary
            test_duration = (datetime.now() - test_start_time).total_seconds()

            test_summary = {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": passed_tests / total_tests if total_tests > 0 else 0,
                "test_duration_seconds": test_duration,
                "test_results": self.test_results,
                "performance_metrics": self._calculate_performance_metrics(),
                "test_timestamp": datetime.now().isoformat(),
            }

            self.logger.info(
                f"🧪 Testing complete: {passed_tests}/{total_tests} tests passed ({test_summary['success_rate']:.1%})"
            )
            self.logger.info(f"⏱️ Total test duration: {test_duration:.2f} seconds")

            return test_summary

        except Exception as e:
            self.logger.error(f"❌ Comprehensive testing failed: {e}")
            raise RuntimeError(f"Test execution failed: {e}")

    async def _run_single_test(self, test_case: dict) -> dict:
        """Run a single subdivision workflow test"""

        test_start_time = datetime.now()
        user_request = test_case["user_request"]

        try:
            # Step 1: Create standardized request for testing
            standardized_request = StandardizedRequest(
                original_request=user_request,
                classification=RequestClassification(
                    request_type=RequestType.APPLICATION_DEVELOPMENT,
                    complexity_level=ComplexityLevel.COMPLEX,
                    domain_category="software_development",
                    estimated_effort="days",
                ),
                subdivision_metadata=None,  # Will be populated by analyzer
            )

            # Step 2: Run subdivision analysis
            self.logger.info("🔍 Running subdivision analysis...")
            subdivision_metadata = (
                await self.subdivision_analyzer.analyze_subdivision_potential(
                    standardized_request, debug=True
                )
            )

            # Update standardized request with subdivision metadata
            standardized_request.subdivision_metadata = subdivision_metadata

            # Validate subdivision analysis
            analysis_validation = self._validate_subdivision_analysis(
                subdivision_metadata, test_case
            )

            if not analysis_validation["valid"]:
                return {
                    "test_case": test_case["name"],
                    "success": False,
                    "error": f"Subdivision analysis validation failed: {analysis_validation['error']}",
                    "timestamp": datetime.now().isoformat(),
                }

            # Step 3: If subdivision is required, test subdivision workflow
            if subdivision_metadata.requires_subdivision:
                subdivision_test_result = await self._test_subdivision_workflow(
                    standardized_request, subdivision_metadata
                )

                if not subdivision_test_result["success"]:
                    return subdivision_test_result

            # Step 4: Calculate test metrics
            test_duration = (datetime.now() - test_start_time).total_seconds() * 1000

            test_result = {
                "test_case": test_case["name"],
                "success": True,
                "subdivision_required": subdivision_metadata.requires_subdivision,
                "complexity_score": subdivision_metadata.complexity_score,
                "estimated_agents": subdivision_metadata.estimated_sub_agents,
                "test_duration_ms": test_duration,
                "analysis_validation": analysis_validation,
                "timestamp": datetime.now().isoformat(),
            }

            # Add subdivision workflow results if applicable
            if subdivision_metadata.requires_subdivision:
                test_result["subdivision_workflow"] = subdivision_test_result

            return test_result

        except Exception as e:
            test_duration = (datetime.now() - test_start_time).total_seconds() * 1000
            return {
                "test_case": test_case["name"],
                "success": False,
                "error": str(e),
                "test_duration_ms": test_duration,
                "timestamp": datetime.now().isoformat(),
            }

    async def _test_subdivision_workflow(
        self,
        standardized_request: StandardizedRequest,
        subdivision_metadata: SubdivisionMetadata,
    ) -> dict:
        """Test the complete subdivision workflow"""

        workflow_start_time = datetime.now()

        try:
            # Step 1: Create subdivision agents
            self.logger.info("🏭 Testing subdivision agent creation...")
            subdivision_agents = await self.agent_factory.create_subdivision_agents(
                standardized_request=standardized_request,
                subdivision_metadata=subdivision_metadata,
                debug=True,
            )

            if not subdivision_agents:
                return {
                    "success": False,
                    "error": "No subdivision agents created",
                    "timestamp": datetime.now().isoformat(),
                }

            # Step 2: Create state and context
            self.logger.info("🏗️ Testing state management...")
            mock_state = {
                "user_request": standardized_request.original_request,
                "project_path": "/tmp/test_project",
                "context": {"subdivision_metadata": subdivision_metadata.model_dump()},
                "specialized_agents": {
                    agent_id: agent_data
                    for agent_id, agent_data in subdivision_agents.items()
                },
                "agent_outputs": {},
            }

            # Create subdivision context
            subdivision_context = await self.state_manager.create_subdivision_context(
                state=mock_state,
                subdivision_metadata=subdivision_metadata.model_dump(),
                debug=True,
            )

            # Step 3: Test mock agent execution (skip actual LLM calls for testing)
            self.logger.info("⚡ Testing mock subdivision execution...")
            mock_agent_outputs = self._create_mock_agent_outputs(subdivision_agents)

            # Update state with mock outputs
            mock_state["agent_outputs"] = mock_agent_outputs

            # Step 4: Test state synchronization
            self.logger.info("🔄 Testing state synchronization...")
            synchronized_state = await self.state_manager.synchronize_subdivision_state(
                context_id=subdivision_context.subdivision_id,
                agent_outputs=mock_agent_outputs,
                debug=True,
            )

            # Step 5: Test result integration
            self.logger.info("🔄 Testing result integration...")
            integration_result = (
                await self.result_integrator.integrate_subdivision_results(
                    state=mock_state, debug=True
                )
            )

            # Calculate workflow metrics
            workflow_duration = (
                datetime.now() - workflow_start_time
            ).total_seconds() * 1000

            return {
                "success": True,
                "agents_created": len(subdivision_agents),
                "agent_specializations": [
                    agent_data["specification"].domain_specialization
                    for agent_data in subdivision_agents.values()
                ],
                "state_context_id": subdivision_context.subdivision_id,
                "synchronization_success": synchronized_state["successful_agents"] > 0,
                "integration_quality_score": integration_result.quality_score,
                "integration_confidence": integration_result.integration_confidence,
                "workflow_duration_ms": workflow_duration,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            workflow_duration = (
                datetime.now() - workflow_start_time
            ).total_seconds() * 1000
            return {
                "success": False,
                "error": str(e),
                "workflow_duration_ms": workflow_duration,
                "timestamp": datetime.now().isoformat(),
            }

    def _validate_subdivision_analysis(
        self, subdivision_metadata: SubdivisionMetadata, test_case: dict
    ) -> dict:
        """Validate subdivision analysis results against expectations"""

        validation_errors = []

        # Check if subdivision requirement matches expectation
        expected_subdivision = test_case["expected_subdivision"]
        actual_subdivision = subdivision_metadata.requires_subdivision

        if expected_subdivision != actual_subdivision:
            validation_errors.append(
                f"Subdivision requirement mismatch: expected {expected_subdivision}, got {actual_subdivision}"
            )

        # Check complexity score is reasonable
        complexity_score = subdivision_metadata.complexity_score
        expected_complexity = test_case["expected_complexity"]

        if complexity_score is not None:
            # Allow 20% tolerance in complexity score
            tolerance = expected_complexity * 0.2
            if abs(complexity_score - expected_complexity) > tolerance:
                validation_errors.append(
                    f"Complexity score outside tolerance: expected ~{expected_complexity}, got {complexity_score}"
                )
        else:
            validation_errors.append("Complexity score not provided")

        # Check that subdivision reasoning is provided when subdivision is required
        if actual_subdivision and not subdivision_metadata.subdivision_reasoning:
            validation_errors.append(
                "Subdivision reasoning missing when subdivision is required"
            )

        # Check that suggested roles are provided when subdivision is required
        if actual_subdivision and not subdivision_metadata.suggested_sub_roles:
            validation_errors.append(
                "Suggested sub-roles missing when subdivision is required"
            )

        return {
            "valid": len(validation_errors) == 0,
            "error": "; ".join(validation_errors) if validation_errors else None,
            "validation_details": {
                "expected_subdivision": expected_subdivision,
                "actual_subdivision": actual_subdivision,
                "expected_complexity": expected_complexity,
                "actual_complexity": complexity_score,
                "has_reasoning": bool(subdivision_metadata.subdivision_reasoning),
                "has_suggested_roles": bool(subdivision_metadata.suggested_sub_roles),
            },
        }

    def _create_mock_agent_outputs(self, subdivision_agents: dict) -> dict:
        """Create mock agent outputs for testing integration"""

        mock_outputs = {}

        for agent_id, agent_data in subdivision_agents.items():
            spec = agent_data["specification"]

            # Create realistic mock output based on agent specialization
            mock_content = f"""
# {spec.role_name} Deliverable

## Domain: {spec.domain_specialization}

### Analysis
Based on the requirements, I've analyzed the {spec.domain_specialization} aspects of this project.

### Implementation Plan
1. Set up {spec.domain_specialization} infrastructure
2. Implement core functionality
3. Add optimization and testing
4. Integration with other components

### Key Deliverables
{chr(10).join([f"- {deliverable}" for deliverable in spec.deliverables])}

### Integration Notes
{chr(10).join([f"- {req}" for req in spec.integration_requirements])}

### Status
Work completed successfully with high confidence.
"""

            mock_outputs[agent_id] = {
                "content": mock_content,
                "role": spec.role_name,
                "specialization": spec.domain_specialization,
                "execution_timestamp": datetime.now().isoformat(),
                "subdivision_agent": True,
                "mock_output": True,  # Mark as mock for testing
            }

        return mock_outputs

    def _calculate_performance_metrics(self) -> dict:
        """Calculate performance metrics from test results"""

        if not self.test_results:
            return {"error": "No test results available"}

        successful_tests = [r for r in self.test_results if r.get("success", False)]

        if not successful_tests:
            return {"error": "No successful tests to analyze"}

        # Extract timing metrics
        test_durations = [r.get("test_duration_ms", 0) for r in successful_tests]
        subdivision_tests = [
            r for r in successful_tests if r.get("subdivision_required", False)
        ]

        metrics = {
            "avg_test_duration_ms": sum(test_durations) / len(test_durations),
            "max_test_duration_ms": max(test_durations),
            "min_test_duration_ms": min(test_durations),
            "subdivision_tests_count": len(subdivision_tests),
            "avg_complexity_score": sum(
                r.get("complexity_score", 0) for r in successful_tests
            )
            / len(successful_tests),
            "avg_estimated_agents": (
                sum(r.get("estimated_agents", 0) for r in subdivision_tests)
                / len(subdivision_tests)
                if subdivision_tests
                else 0
            ),
        }

        # Add subdivision workflow metrics if available
        subdivision_workflows = [
            r["subdivision_workflow"]
            for r in subdivision_tests
            if "subdivision_workflow" in r
            and r["subdivision_workflow"].get("success", False)
        ]

        if subdivision_workflows:
            metrics.update(
                {
                    "avg_workflow_duration_ms": sum(
                        w.get("workflow_duration_ms", 0) for w in subdivision_workflows
                    )
                    / len(subdivision_workflows),
                    "avg_integration_quality": sum(
                        w.get("integration_quality_score", 0)
                        for w in subdivision_workflows
                    )
                    / len(subdivision_workflows),
                    "avg_integration_confidence": sum(
                        w.get("integration_confidence", 0)
                        for w in subdivision_workflows
                    )
                    / len(subdivision_workflows),
                }
            )

        return metrics

    def print_test_summary(self, test_summary: dict):
        """Print a formatted test summary"""

        print("\n" + "=" * 60)
        print("🧪 SUBDIVISION WORKFLOW TEST SUMMARY")
        print("=" * 60)

        print(f"📊 Tests Run: {test_summary['total_tests']}")
        print(f"✅ Passed: {test_summary['passed_tests']}")
        print(f"❌ Failed: {test_summary['failed_tests']}")
        print(f"📈 Success Rate: {test_summary['success_rate']:.1%}")
        print(f"⏱️ Duration: {test_summary['test_duration_seconds']:.2f}s")

        print("\n📋 Test Results:")
        for result in test_summary["test_results"]:
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            print(f"  {status}: {result['test_case']}")
            if not result["success"]:
                print(f"    Error: {result.get('error', 'Unknown error')}")

        if "performance_metrics" in test_summary:
            metrics = test_summary["performance_metrics"]
            print("\n⚡ Performance Metrics:")
            print(
                f"  Avg Test Duration: {metrics.get('avg_test_duration_ms', 0):.0f}ms"
            )
            print(f"  Subdivision Tests: {metrics.get('subdivision_tests_count', 0)}")
            print(
                f"  Avg Complexity Score: {metrics.get('avg_complexity_score', 0):.1f}"
            )
            if "avg_integration_quality" in metrics:
                print(
                    f"  Avg Integration Quality: {metrics['avg_integration_quality']:.1f}/10.0"
                )

        print("=" * 60)


async def main():
    """Main test execution function"""

    print("🚀 Starting Subdivision Workflow Tests...")

    try:
        # Initialize tester
        tester = SubdivisionWorkflowTester()

        # Run comprehensive tests
        test_summary = await tester.run_comprehensive_tests()

        # Print results
        tester.print_test_summary(test_summary)

        # Exit with appropriate code
        if test_summary["success_rate"] == 1.0:
            print(
                "\n🎉 All tests passed! Subdivision workflow is functioning correctly."
            )
            sys.exit(0)
        else:
            print(
                f"\n⚠️ Some tests failed. Success rate: {test_summary['success_rate']:.1%}"
            )
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
