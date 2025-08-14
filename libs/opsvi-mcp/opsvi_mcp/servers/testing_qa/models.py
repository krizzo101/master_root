"""
Data models for Testing & QA MCP Server
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Any, Union
from datetime import datetime


class TestType(Enum):
    """Types of tests supported"""

    UNIT = "unit"
    INTEGRATION = "integration"
    E2E = "e2e"
    PERFORMANCE = "performance"
    LOAD = "load"
    MUTATION = "mutation"
    SMOKE = "smoke"
    REGRESSION = "regression"
    SECURITY = "security"


class TestStatus(Enum):
    """Test execution status"""

    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"
    FLAKY = "flaky"


class Language(Enum):
    """Supported programming languages"""

    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    CSHARP = "csharp"
    GO = "go"
    RUST = "rust"
    CPP = "cpp"


class CoverageType(Enum):
    """Types of code coverage"""

    LINE = "line"
    BRANCH = "branch"
    FUNCTION = "function"
    STATEMENT = "statement"


@dataclass
class TestCase:
    """Represents a single test case"""

    id: str
    name: str
    type: TestType
    description: str
    code: str
    language: Language
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class TestResult:
    """Result of a test execution"""

    test_id: str
    status: TestStatus
    duration: float  # seconds
    started_at: datetime
    finished_at: datetime
    output: Optional[str] = None
    error: Optional[str] = None
    stack_trace: Optional[str] = None
    assertions: Dict[str, bool] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[str] = field(
        default_factory=list
    )  # paths to screenshots, logs, etc.
    retry_count: int = 0


@dataclass
class CoverageReport:
    """Code coverage report"""

    file_path: str
    language: Language
    coverage_type: CoverageType
    covered_lines: int
    total_lines: int
    coverage_percentage: float
    uncovered_lines: List[int] = field(default_factory=list)
    branch_coverage: Optional[Dict[str, Any]] = None
    function_coverage: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class PerformanceMetrics:
    """Performance test metrics"""

    test_id: str
    response_time_avg: float  # ms
    response_time_min: float
    response_time_max: float
    response_time_p50: float
    response_time_p95: float
    response_time_p99: float
    throughput: float  # requests per second
    error_rate: float  # percentage
    cpu_usage: float  # percentage
    memory_usage: float  # MB
    network_io: float  # MB/s
    disk_io: float  # MB/s
    custom_metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class LoadTestResult:
    """Load test execution result"""

    test_id: str
    virtual_users: int
    ramp_up_time: int  # seconds
    duration: int  # seconds
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time: float  # ms
    peak_response_time: float
    requests_per_second: float
    error_rate: float
    concurrent_users_peak: int
    bandwidth_used: float  # MB
    scenarios: List[Dict[str, Any]] = field(default_factory=list)
    timeline_metrics: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class MutationTestResult:
    """Mutation testing result"""

    file_path: str
    language: Language
    total_mutants: int
    killed_mutants: int
    survived_mutants: int
    timeout_mutants: int
    no_coverage_mutants: int
    mutation_score: float  # percentage
    mutant_details: List[Dict[str, Any]] = field(default_factory=list)
    execution_time: float  # seconds


@dataclass
class TestSuite:
    """Collection of test cases"""

    id: str
    name: str
    description: str
    test_cases: List[TestCase]
    language: Language
    type: TestType
    setup_code: Optional[str] = None
    teardown_code: Optional[str] = None
    configuration: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class TestGenerationRequest:
    """Request for test generation"""

    source_code: str
    language: Language
    test_type: TestType
    framework: Optional[str] = None
    include_edge_cases: bool = True
    include_negative_tests: bool = True
    coverage_target: float = 80.0
    context_files: List[str] = field(default_factory=list)
    custom_requirements: Optional[str] = None


@dataclass
class TestGenerationResponse:
    """Response from test generation"""

    test_suite: TestSuite
    estimated_coverage: float
    generation_time: float  # seconds
    suggestions: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class TestAnalysis:
    """Analysis of test suite quality"""

    total_tests: int
    test_distribution: Dict[TestType, int]
    coverage_summary: Dict[CoverageType, float]
    flaky_tests: List[str]
    slow_tests: List[Dict[str, Any]]
    test_dependencies: Dict[str, List[str]]
    maintainability_score: float
    recommendations: List[str]
    risk_areas: List[Dict[str, Any]]


@dataclass
class QAReport:
    """Comprehensive QA report"""

    project_id: str
    timestamp: datetime
    test_results: List[TestResult]
    coverage_reports: List[CoverageReport]
    performance_metrics: Optional[PerformanceMetrics] = None
    load_test_results: Optional[LoadTestResult] = None
    mutation_test_results: List[MutationTestResult] = field(default_factory=list)
    test_analysis: Optional[TestAnalysis] = None
    overall_status: TestStatus = TestStatus.PENDING
    quality_score: float = 0.0  # 0-100
    summary: Dict[str, Any] = field(default_factory=dict)

    def calculate_quality_score(self) -> float:
        """Calculate overall quality score based on various metrics"""
        score = 0.0
        weights = {
            "test_pass_rate": 0.3,
            "coverage": 0.25,
            "performance": 0.15,
            "mutation_score": 0.15,
            "maintainability": 0.15,
        }

        # Calculate test pass rate
        if self.test_results:
            passed = sum(1 for r in self.test_results if r.status == TestStatus.PASSED)
            test_pass_rate = (passed / len(self.test_results)) * 100
            score += test_pass_rate * weights["test_pass_rate"]

        # Calculate average coverage
        if self.coverage_reports:
            avg_coverage = sum(
                r.coverage_percentage for r in self.coverage_reports
            ) / len(self.coverage_reports)
            score += avg_coverage * weights["coverage"]

        # Include performance score if available
        if self.performance_metrics and self.performance_metrics.error_rate is not None:
            perf_score = max(0, 100 - self.performance_metrics.error_rate)
            score += perf_score * weights["performance"]

        # Include mutation score if available
        if self.mutation_test_results:
            avg_mutation = sum(
                r.mutation_score for r in self.mutation_test_results
            ) / len(self.mutation_test_results)
            score += avg_mutation * weights["mutation_score"]

        # Include maintainability score if available
        if self.test_analysis and self.test_analysis.maintainability_score:
            score += (
                self.test_analysis.maintainability_score * weights["maintainability"]
            )

        self.quality_score = min(100, max(0, score))
        return self.quality_score
