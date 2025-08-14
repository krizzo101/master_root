"""
Configuration for Testing & QA MCP Server
"""

import os
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from pathlib import Path


@dataclass
class TestingConfig:
    """Configuration for Testing & QA operations"""

    # Test Generation Configuration
    test_frameworks: Dict[str, str] = field(default_factory=lambda: {
        "python": os.environ.get("TEST_FRAMEWORK_PYTHON", "pytest"),
        "javascript": os.environ.get("TEST_FRAMEWORK_JS", "jest"),
        "typescript": os.environ.get("TEST_FRAMEWORK_TS", "jest")
    })
    
    # Coverage Configuration
    coverage_enabled: bool = os.environ.get("COVERAGE_ENABLED", "true").lower() == "true"
    coverage_threshold: float = float(os.environ.get("COVERAGE_THRESHOLD", "80.0"))
    coverage_report_format: str = os.environ.get("COVERAGE_FORMAT", "html,json,lcov")
    coverage_output_dir: str = os.environ.get("COVERAGE_OUTPUT_DIR", "./coverage")
    
    # Performance Testing Configuration
    perf_test_duration: int = int(os.environ.get("PERF_TEST_DURATION", "60"))  # seconds
    perf_test_iterations: int = int(os.environ.get("PERF_TEST_ITERATIONS", "100"))
    perf_test_warmup: int = int(os.environ.get("PERF_TEST_WARMUP", "10"))
    perf_metrics: List[str] = field(default_factory=lambda: [
        "response_time", "throughput", "cpu_usage", "memory_usage", "error_rate"
    ])
    
    # Load Testing Configuration
    load_test_users: int = int(os.environ.get("LOAD_TEST_USERS", "100"))
    load_test_ramp_up: int = int(os.environ.get("LOAD_TEST_RAMP_UP", "30"))  # seconds
    load_test_duration: int = int(os.environ.get("LOAD_TEST_DURATION", "300"))  # seconds
    load_test_think_time: float = float(os.environ.get("LOAD_TEST_THINK_TIME", "1.0"))
    
    # Test Types Configuration
    test_types: Dict[str, bool] = field(default_factory=lambda: {
        "unit": os.environ.get("ENABLE_UNIT_TESTS", "true").lower() == "true",
        "integration": os.environ.get("ENABLE_INTEGRATION_TESTS", "true").lower() == "true",
        "e2e": os.environ.get("ENABLE_E2E_TESTS", "true").lower() == "true",
        "mutation": os.environ.get("ENABLE_MUTATION_TESTS", "false").lower() == "true",
        "performance": os.environ.get("ENABLE_PERF_TESTS", "true").lower() == "true",
        "load": os.environ.get("ENABLE_LOAD_TESTS", "false").lower() == "true"
    })
    
    # Mutation Testing Configuration
    mutation_operators: List[str] = field(default_factory=lambda: [
        "arithmetic", "comparison", "logical", "assignment", "return"
    ])
    mutation_timeout: int = int(os.environ.get("MUTATION_TIMEOUT", "10"))  # seconds per mutation
    mutation_threshold: float = float(os.environ.get("MUTATION_THRESHOLD", "75.0"))
    
    # Test Generation Configuration
    test_generation_model: str = os.environ.get("TEST_GEN_MODEL", "gpt-4")
    test_generation_style: str = os.environ.get("TEST_GEN_STYLE", "comprehensive")
    include_edge_cases: bool = os.environ.get("INCLUDE_EDGE_CASES", "true").lower() == "true"
    include_negative_tests: bool = os.environ.get("INCLUDE_NEGATIVE_TESTS", "true").lower() == "true"
    
    # Reporting Configuration
    report_format: str = os.environ.get("REPORT_FORMAT", "json,html,junit")
    report_output_dir: str = os.environ.get("REPORT_OUTPUT_DIR", "./test-reports")
    report_include_logs: bool = os.environ.get("REPORT_INCLUDE_LOGS", "true").lower() == "true"
    report_include_screenshots: bool = os.environ.get("REPORT_INCLUDE_SCREENSHOTS", "false").lower() == "true"
    
    # Execution Configuration
    parallel_execution: bool = os.environ.get("PARALLEL_EXECUTION", "true").lower() == "true"
    max_parallel_jobs: int = int(os.environ.get("MAX_PARALLEL_JOBS", "4"))
    test_timeout: int = int(os.environ.get("TEST_TIMEOUT", "300"))  # seconds
    retry_failed_tests: int = int(os.environ.get("RETRY_FAILED_TESTS", "2"))
    
    # Cache Configuration
    cache_test_results: bool = os.environ.get("CACHE_TEST_RESULTS", "true").lower() == "true"
    cache_dir: str = os.environ.get("TEST_CACHE_DIR", "/tmp/testing_qa_cache")
    cache_ttl: int = int(os.environ.get("TEST_CACHE_TTL", "3600"))  # seconds
    
    # Analysis Configuration
    analyze_flaky_tests: bool = os.environ.get("ANALYZE_FLAKY_TESTS", "true").lower() == "true"
    flaky_test_threshold: int = int(os.environ.get("FLAKY_TEST_THRESHOLD", "3"))
    analyze_test_dependencies: bool = os.environ.get("ANALYZE_DEPENDENCIES", "true").lower() == "true"
    
    # Integration Configuration
    ci_integration: str = os.environ.get("CI_INTEGRATION", "github")  # github, gitlab, jenkins
    notification_channels: List[str] = field(default_factory=lambda: 
        os.environ.get("NOTIFICATION_CHANNELS", "console,file").split(",")
    )
    
    def __post_init__(self):
        """Validate and initialize configuration"""
        # Create necessary directories
        for dir_path in [self.coverage_output_dir, self.report_output_dir, self.cache_dir]:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
        
        # Validate thresholds
        if not 0 <= self.coverage_threshold <= 100:
            raise ValueError("Coverage threshold must be between 0 and 100")
        
        if not 0 <= self.mutation_threshold <= 100:
            raise ValueError("Mutation threshold must be between 0 and 100")
        
        # Validate test frameworks
        valid_frameworks = {
            "python": ["pytest", "unittest", "nose2"],
            "javascript": ["jest", "mocha", "jasmine", "vitest"],
            "typescript": ["jest", "mocha", "jasmine", "vitest"]
        }
        
        for lang, framework in self.test_frameworks.items():
            if lang in valid_frameworks and framework not in valid_frameworks[lang]:
                raise ValueError(f"Invalid test framework '{framework}' for {lang}")