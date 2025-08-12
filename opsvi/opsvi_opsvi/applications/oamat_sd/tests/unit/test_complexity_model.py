"""
Unit Tests for Complexity Model - REAL IMPLEMENTATION TESTING

Tests the actual 6-factor complexity analysis engine using real implementations
instead of mocks. This provides genuine TDD validation of working code.
"""

import sys
from pathlib import Path

import pytest

# Add project root for imports (Rule 803 compliance)
project_root = Path(__file__).parents[3]
sys.path.insert(0, str(project_root))

# REAL IMPORTS - No mocking (TDD Compliance)
from oamat_sd.src.agents.complexity_model import ComplexityModel
from oamat_sd.src.models.data_models import RequestInput


class TestComplexityModelReal:
    """Test suite for 6-factor complexity model using REAL implementation"""

    @pytest.fixture
    def complexity_model(self):
        """Create REAL complexity model instance for testing"""
        # ✅ REAL IMPLEMENTATION - No mocking
        return ComplexityModel()

    @pytest.fixture
    def simple_request(self):
        """Simple request for testing"""
        return RequestInput(
            content="Create a Python script that prints hello world",
            name="hello_world",
            description="Simple hello world script",
        )

    @pytest.fixture
    def complex_request(self):
        """Complex request for testing"""
        return RequestInput(
            content="Build a full-stack e-commerce platform with microservices, authentication, payment processing, and real-time analytics",
            name="ecommerce_platform",
            description="Complete enterprise e-commerce solution",
        )

    def test_factor_analysis_simple_request(self, complexity_model, simple_request):
        """Test factor analysis for simple requests using REAL implementation"""
        # Test REAL complexity analysis
        result = complexity_model.analyze_factors(simple_request)

        # Validate REAL results
        assert result is not None
        assert hasattr(result, "factors")
        assert hasattr(result, "overall_score")

        # Test actual factor scoring
        factors = result.factors
        assert all(1 <= score <= 10 for score in factors.to_dict().values())

        # Simple requests should have lower scores
        assert factors.scope.score <= 5
        assert result.overall_score <= 50

    def test_factor_analysis_complex_request(self, complexity_model, complex_request):
        """Test factor analysis for complex requests using REAL implementation"""
        # Test REAL complexity analysis
        result = complexity_model.analyze_factors(complex_request)

        # Validate REAL results
        assert result is not None
        assert hasattr(result, "factors")
        assert hasattr(result, "overall_score")

        # Test actual factor scoring
        factors = result.factors
        assert all(1 <= score <= 10 for score in factors.to_dict().values())

        # Complex requests should have higher scores
        assert factors.scope.score >= 7
        assert result.overall_score >= 70

    def test_complexity_analysis_comprehensive(self, complexity_model):
        """Test comprehensive complexity analysis with various request types"""
        test_cases = [
            ("Write a function to add two numbers", "simple"),
            ("Create a REST API with database integration", "medium"),
            ("Build a distributed machine learning pipeline", "complex"),
        ]

        for request_content, expected_complexity in test_cases:
            request = RequestInput(
                content=request_content, name="test_request", description="Test request"
            )

            result = complexity_model.analyze_factors(request)

            # Validate REAL complexity analysis
            assert result is not None
            assert result.overall_score > 0

            # Verify complexity categorization matches expectations
            if expected_complexity == "simple":
                assert result.overall_score <= 40
            elif expected_complexity == "medium":
                assert 40 < result.overall_score <= 70
            else:  # complex
                assert result.overall_score > 70

    def test_execution_strategy_determination(self, complexity_model):
        """Test execution strategy determination using REAL implementation"""
        simple_request = RequestInput(
            content="Print hello world", name="simple_task", description="Basic task"
        )

        complex_request = RequestInput(
            content="Build enterprise microservices platform",
            name="complex_platform",
            description="Enterprise solution",
        )

        # Test REAL strategy determination
        simple_result = complexity_model.analyze_factors(simple_request)
        complex_result = complexity_model.analyze_factors(complex_request)

        # Validate different strategies for different complexity levels
        assert simple_result.execution_strategy != complex_result.execution_strategy
        assert simple_result.overall_score < complex_result.overall_score

    def test_factor_boundaries(self, complexity_model):
        """Test factor score boundaries using REAL implementation"""
        request = RequestInput(
            content="Test request",
            name="boundary_test",
            description="Testing factor boundaries",
        )

        result = complexity_model.analyze_factors(request)

        # Validate REAL factor boundaries
        factors_dict = result.factors.to_dict()
        for factor_name, score in factors_dict.items():
            assert (
                1 <= score <= 10
            ), f"Factor {factor_name} score {score} outside valid range [1,10]"

    def test_complexity_score_calculation(self, complexity_model):
        """Test overall complexity score calculation using REAL implementation"""
        request = RequestInput(
            content="Create a web application",
            name="web_app",
            description="Web application development",
        )

        result = complexity_model.analyze_factors(request)

        # Validate REAL score calculation
        assert 0 <= result.overall_score <= 100
        assert isinstance(result.overall_score, (int, float))

    def test_factor_consistency(self, complexity_model):
        """Test factor analysis consistency using REAL implementation"""
        request = RequestInput(
            content="Build a mobile app",
            name="mobile_app",
            description="Mobile application",
        )

        # Run REAL analysis multiple times
        results = [complexity_model.analyze_factors(request) for _ in range(3)]

        # Results should be consistent (within reasonable variance for AI-based analysis)
        scores = [result.overall_score for result in results]
        variance = max(scores) - min(scores)
        assert variance <= 20  # Allow some variance for AI-based analysis

    def test_edge_cases(self, complexity_model):
        """Test edge cases using REAL implementation"""
        edge_cases = [
            RequestInput(
                content="Simple minimal test case",
                name="minimal",
                description="Minimal test case",
            ),
            RequestInput(
                content="x" * 10000,
                name="very_long",
                description="Very long request description",
            ),
        ]

        for request in edge_cases:
            # REAL implementation should handle edge cases gracefully
            try:
                result = complexity_model.analyze_factors(request)
                assert result is not None
                assert 0 <= result.overall_score <= 100
            except Exception as e:
                # If exception occurs, it should be a meaningful validation error
                assert isinstance(e, (ValueError, TypeError))
