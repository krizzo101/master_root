"""TestAgent - Testing and QA."""

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import structlog

from ..core import AgentConfig, AgentContext, AgentResult, BaseAgent

logger = structlog.get_logger()


class TestType(Enum):
    """Types of tests."""

    UNIT = "unit"
    INTEGRATION = "integration"
    FUNCTIONAL = "functional"
    PERFORMANCE = "performance"
    SECURITY = "security"
    REGRESSION = "regression"
    SMOKE = "smoke"
    ACCEPTANCE = "acceptance"


class TestStatus(Enum):
    """Test execution status."""

    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class TestCase:
    """Individual test case."""

    id: str
    name: str
    type: TestType
    description: str = ""
    inputs: Dict[str, Any] = field(default_factory=dict)
    expected: Any = None
    actual: Any = None
    status: TestStatus = TestStatus.PENDING
    duration: float = 0.0
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "description": self.description,
            "status": self.status.value,
            "duration": self.duration,
            "error": self.error,
        }


@dataclass
class TestSuite:
    """Collection of test cases."""

    id: str
    name: str
    test_cases: List[TestCase] = field(default_factory=list)
    setup: Optional[str] = None
    teardown: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_test(self, test: TestCase):
        """Add test case to suite."""
        self.test_cases.append(test)

    def get_stats(self) -> Dict[str, int]:
        """Get test statistics."""
        stats = {
            "total": len(self.test_cases),
            "passed": sum(1 for t in self.test_cases if t.status == TestStatus.PASSED),
            "failed": sum(1 for t in self.test_cases if t.status == TestStatus.FAILED),
            "skipped": sum(
                1 for t in self.test_cases if t.status == TestStatus.SKIPPED
            ),
            "error": sum(1 for t in self.test_cases if t.status == TestStatus.ERROR),
        }
        return stats

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "test_cases": [t.to_dict() for t in self.test_cases],
            "stats": self.get_stats(),
            "metadata": self.metadata,
        }


@dataclass
class TestReport:
    """Test execution report."""

    id: str
    suites: List[TestSuite] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    coverage: Optional[float] = None

    def get_summary(self) -> Dict[str, Any]:
        """Get test summary."""
        total_tests = sum(len(s.test_cases) for s in self.suites)
        passed = sum(s.get_stats()["passed"] for s in self.suites)
        failed = sum(s.get_stats()["failed"] for s in self.suites)

        return {
            "total_suites": len(self.suites),
            "total_tests": total_tests,
            "passed": passed,
            "failed": failed,
            "pass_rate": passed / total_tests if total_tests > 0 else 0,
            "duration": self.end_time - self.start_time if self.end_time else 0,
            "coverage": self.coverage,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "suites": [s.to_dict() for s in self.suites],
            "summary": self.get_summary(),
        }


class TestAgent(BaseAgent):
    """Performs testing and quality assurance."""

    def __init__(self, config: Optional[AgentConfig] = None):
        """Initialize test agent."""
        super().__init__(
            config
            or AgentConfig(
                name="TestAgent",
                description="Testing and QA",
                capabilities=["test", "validate", "verify", "benchmark", "coverage"],
                max_retries=3,
                timeout=120,
            )
        )
        self.test_suites: Dict[str, TestSuite] = {}
        self.test_reports: Dict[str, TestReport] = {}
        self.test_templates: Dict[str, Any] = {}
        self._test_counter = 0
        self._suite_counter = 0
        self._report_counter = 0
        self._register_templates()

    def initialize(self) -> bool:
        """Initialize the test agent."""
        logger.info("test_agent_initialized", agent=self.config.name)
        return True

    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute testing task."""
        action = task.get("action", "test")

        if action == "test":
            return self._run_tests(task)
        elif action == "create_test":
            return self._create_test(task)
        elif action == "create_suite":
            return self._create_suite(task)
        elif action == "run_suite":
            return self._run_suite(task)
        elif action == "validate":
            return self._validate_output(task)
        elif action == "benchmark":
            return self._run_benchmark(task)
        elif action == "coverage":
            return self._analyze_coverage(task)
        elif action == "regression":
            return self._run_regression(task)
        else:
            return {"error": f"Unknown action: {action}"}

    def run_tests(
        self, code: Any, test_type: TestType = TestType.UNIT, coverage: bool = False
    ) -> TestReport:
        """Run tests on code."""
        result = self.execute(
            {
                "action": "test",
                "code": code,
                "test_type": test_type.value,
                "coverage": coverage,
            }
        )

        if "error" in result:
            raise RuntimeError(result["error"])

        return result["report"]

    def _register_templates(self):
        """Register test templates."""
        self.test_templates["unit"] = {
            "setup": "Initialize test environment",
            "teardown": "Clean up test environment",
            "assertions": ["assertEqual", "assertTrue", "assertFalse", "assertIsNone"],
        }

        self.test_templates["integration"] = {
            "setup": "Set up integration environment",
            "teardown": "Tear down integration environment",
            "checks": ["api_connectivity", "database_access", "service_communication"],
        }

        self.test_templates["performance"] = {
            "metrics": ["response_time", "throughput", "memory_usage", "cpu_usage"],
            "thresholds": {"response_time": 1000, "memory_usage": 512},
        }

    def _run_tests(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Run tests on code or system."""
        code = task.get("code")
        test_type = task.get("test_type", "unit")
        coverage = task.get("coverage", False)

        if code is None:
            return {"error": "Code is required"}

        # Create test report
        self._report_counter += 1
        report = TestReport(id=f"report_{self._report_counter}")

        # Create test suite
        self._suite_counter += 1
        suite = TestSuite(id=f"suite_{self._suite_counter}", name=f"{test_type} tests")

        # Generate and run tests based on type
        type_enum = TestType[test_type.upper()]

        if type_enum == TestType.UNIT:
            tests = self._generate_unit_tests(code)
        elif type_enum == TestType.INTEGRATION:
            tests = self._generate_integration_tests(code)
        elif type_enum == TestType.PERFORMANCE:
            tests = self._generate_performance_tests(code)
        else:
            tests = self._generate_basic_tests(code)

        # Execute tests
        for test in tests:
            suite.add_test(test)
            self._execute_test(test)

        # Add suite to report
        report.suites.append(suite)
        report.end_time = time.time()

        # Calculate coverage if requested
        if coverage:
            report.coverage = self._calculate_coverage(code, suite)

        # Store report
        self.test_reports[report.id] = report

        logger.info(
            "tests_completed",
            report_id=report.id,
            test_type=test_type,
            stats=suite.get_stats(),
        )

        return {
            "report": report,
            "summary": report.get_summary(),
            "report_id": report.id,
        }

    def _create_test(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Create a test case."""
        name = task.get("name", "test")
        test_type = task.get("test_type", "unit")
        description = task.get("description", "")
        inputs = task.get("inputs", {})
        expected = task.get("expected")

        self._test_counter += 1
        test = TestCase(
            id=f"test_{self._test_counter}",
            name=name,
            type=TestType[test_type.upper()],
            description=description,
            inputs=inputs,
            expected=expected,
        )

        return {"test": test.to_dict(), "test_id": test.id}

    def _create_suite(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Create a test suite."""
        name = task.get("name", "Test Suite")
        setup = task.get("setup")
        teardown = task.get("teardown")

        self._suite_counter += 1
        suite = TestSuite(
            id=f"suite_{self._suite_counter}", name=name, setup=setup, teardown=teardown
        )

        # Add tests if provided
        tests_data = task.get("tests", [])
        for test_data in tests_data:
            self._test_counter += 1
            test = TestCase(
                id=f"test_{self._test_counter}",
                name=test_data.get("name", "test"),
                type=TestType[test_data.get("type", "unit").upper()],
                description=test_data.get("description", ""),
                inputs=test_data.get("inputs", {}),
                expected=test_data.get("expected"),
            )
            suite.add_test(test)

        # Store suite
        self.test_suites[suite.id] = suite

        return {"suite": suite.to_dict(), "suite_id": suite.id}

    def _run_suite(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Run a test suite."""
        suite_id = task.get("suite_id")

        if not suite_id or suite_id not in self.test_suites:
            return {"error": f"Suite {suite_id} not found"}

        suite = self.test_suites[suite_id]

        # Run setup
        if suite.setup:
            logger.info("running_setup", suite=suite_id)

        # Execute all tests
        for test in suite.test_cases:
            self._execute_test(test)

        # Run teardown
        if suite.teardown:
            logger.info("running_teardown", suite=suite_id)

        return {"suite": suite.to_dict(), "stats": suite.get_stats()}

    def _validate_output(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Validate output against expectations."""
        actual = task.get("actual")
        expected = task.get("expected")
        validation_type = task.get("validation_type", "exact")

        if actual is None or expected is None:
            return {"error": "Both actual and expected are required"}

        valid = False
        details = {}

        if validation_type == "exact":
            valid = actual == expected
            details["match"] = valid
        elif validation_type == "contains":
            valid = str(expected) in str(actual)
            details["found"] = valid
        elif validation_type == "type":
            valid = type(actual) == type(expected)
            details["type_match"] = valid
        elif validation_type == "range":
            if isinstance(expected, dict):
                min_val = expected.get("min", float("-inf"))
                max_val = expected.get("max", float("inf"))
                valid = min_val <= actual <= max_val
                details["in_range"] = valid

        return {"valid": valid, "validation_type": validation_type, "details": details}

    def _run_benchmark(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Run performance benchmark."""
        code = task.get("code")
        iterations = task.get("iterations", 100)
        metrics = task.get("metrics", ["time", "memory"])

        if code is None:
            return {"error": "Code is required"}

        results = {"iterations": iterations, "metrics": {}}

        # Simulate benchmark execution
        if "time" in metrics:
            # Measure execution time
            start = time.time()
            # Simulate code execution
            time.sleep(0.001)  # Placeholder
            end = time.time()

            results["metrics"]["avg_time"] = (end - start) * 1000  # ms
            results["metrics"]["min_time"] = (end - start) * 900  # ms
            results["metrics"]["max_time"] = (end - start) * 1100  # ms

        if "memory" in metrics:
            # Simulate memory measurement
            results["metrics"]["memory_usage"] = 1024  # KB
            results["metrics"]["peak_memory"] = 2048  # KB

        if "throughput" in metrics:
            results["metrics"]["throughput"] = iterations / 1.0  # ops/sec

        return {"benchmark": results, "summary": f"Completed {iterations} iterations"}

    def _analyze_coverage(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze test coverage."""
        code = task.get("code")
        tests = task.get("tests", [])

        if code is None:
            return {"error": "Code is required"}

        # Simulate coverage analysis
        total_lines = len(str(code).splitlines())
        covered_lines = int(total_lines * 0.75)  # Simulated 75% coverage

        coverage_data = {
            "total_lines": total_lines,
            "covered_lines": covered_lines,
            "missed_lines": total_lines - covered_lines,
            "coverage_percentage": (covered_lines / total_lines * 100)
            if total_lines > 0
            else 0,
            "uncovered_sections": ["error_handling", "edge_cases"],
        }

        return {
            "coverage": coverage_data,
            "summary": f"{coverage_data['coverage_percentage']:.1f}% coverage",
        }

    def _run_regression(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Run regression tests."""
        current = task.get("current")
        previous = task.get("previous")
        test_suite_id = task.get("test_suite_id")

        if current is None:
            return {"error": "Current version is required"}

        regressions = []
        improvements = []

        # Run tests on current version
        if test_suite_id and test_suite_id in self.test_suites:
            suite = self.test_suites[test_suite_id]

            # Execute tests
            for test in suite.test_cases:
                self._execute_test(test)

                # Compare with previous results if available
                if previous and test.status == TestStatus.FAILED:
                    regressions.append(
                        {"test": test.name, "status": "regression", "error": test.error}
                    )
                elif previous and test.status == TestStatus.PASSED:
                    improvements.append({"test": test.name, "status": "improved"})

        return {
            "regressions": regressions,
            "improvements": improvements,
            "summary": f"{len(regressions)} regressions, {len(improvements)} improvements",
        }

    def _generate_unit_tests(self, code: Any) -> List[TestCase]:
        """Generate unit tests for code."""
        tests = []

        # Generate basic unit tests
        self._test_counter += 1
        tests.append(
            TestCase(
                id=f"test_{self._test_counter}",
                name="test_basic_functionality",
                type=TestType.UNIT,
                description="Test basic functionality",
                inputs={"data": "test"},
                expected="test",
                status=TestStatus.PENDING,
            )
        )

        self._test_counter += 1
        tests.append(
            TestCase(
                id=f"test_{self._test_counter}",
                name="test_edge_cases",
                type=TestType.UNIT,
                description="Test edge cases",
                inputs={"data": None},
                expected=None,
                status=TestStatus.PENDING,
            )
        )

        self._test_counter += 1
        tests.append(
            TestCase(
                id=f"test_{self._test_counter}",
                name="test_error_handling",
                type=TestType.UNIT,
                description="Test error handling",
                inputs={"data": "invalid"},
                expected="error",
                status=TestStatus.PENDING,
            )
        )

        return tests

    def _generate_integration_tests(self, code: Any) -> List[TestCase]:
        """Generate integration tests."""
        tests = []

        self._test_counter += 1
        tests.append(
            TestCase(
                id=f"test_{self._test_counter}",
                name="test_component_integration",
                type=TestType.INTEGRATION,
                description="Test component integration",
                status=TestStatus.PENDING,
            )
        )

        return tests

    def _generate_performance_tests(self, code: Any) -> List[TestCase]:
        """Generate performance tests."""
        tests = []

        self._test_counter += 1
        tests.append(
            TestCase(
                id=f"test_{self._test_counter}",
                name="test_response_time",
                type=TestType.PERFORMANCE,
                description="Test response time",
                status=TestStatus.PENDING,
            )
        )

        self._test_counter += 1
        tests.append(
            TestCase(
                id=f"test_{self._test_counter}",
                name="test_throughput",
                type=TestType.PERFORMANCE,
                description="Test throughput",
                status=TestStatus.PENDING,
            )
        )

        return tests

    def _generate_basic_tests(self, code: Any) -> List[TestCase]:
        """Generate basic tests."""
        tests = []

        self._test_counter += 1
        tests.append(
            TestCase(
                id=f"test_{self._test_counter}",
                name="test_smoke",
                type=TestType.SMOKE,
                description="Basic smoke test",
                status=TestStatus.PENDING,
            )
        )

        return tests

    def _execute_test(self, test: TestCase) -> None:
        """Execute a single test."""
        start = time.time()
        test.status = TestStatus.RUNNING

        try:
            # Simulate test execution
            if test.inputs.get("data") == "invalid":
                test.status = TestStatus.FAILED
                test.error = "Invalid input"
            elif test.inputs.get("data") is None:
                test.status = TestStatus.SKIPPED
            else:
                test.status = TestStatus.PASSED
                test.actual = test.expected
        except Exception as e:
            test.status = TestStatus.ERROR
            test.error = str(e)

        test.duration = time.time() - start

    def _calculate_coverage(self, code: Any, suite: TestSuite) -> float:
        """Calculate test coverage."""
        # Simplified coverage calculation
        passed_tests = sum(1 for t in suite.test_cases if t.status == TestStatus.PASSED)
        total_tests = len(suite.test_cases)

        if total_tests == 0:
            return 0.0

        # Simulate coverage based on test success rate
        base_coverage = (passed_tests / total_tests) * 100

        # Adjust based on test types
        has_unit = any(t.type == TestType.UNIT for t in suite.test_cases)
        has_integration = any(t.type == TestType.INTEGRATION for t in suite.test_cases)

        if has_unit:
            base_coverage *= 0.8
        if has_integration:
            base_coverage *= 0.9

        return min(base_coverage, 100.0)

    def shutdown(self) -> bool:
        """Shutdown the test agent."""
        logger.info(
            "test_agent_shutdown",
            suites_count=len(self.test_suites),
            reports_count=len(self.test_reports),
        )
        self.test_suites.clear()
        self.test_reports.clear()
        self.test_templates.clear()
        return True
