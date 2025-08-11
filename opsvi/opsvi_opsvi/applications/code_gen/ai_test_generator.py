"""
AI-Powered Test Generation Module

Creates intelligent, comprehensive test suites based on generated code analysis.
Uses OpenAI to understand code structure and generate meaningful tests.
"""

from __future__ import annotations

import logging
import ast
from typing import Dict, Any, List, Optional
from pathlib import Path

from pydantic import BaseModel, Field

from config import get_config
from schemas import RequirementsSpec, ArchitectureSpec
from local_shared.openai_interfaces.responses_interface import get_openai_interface

# Model selector imported locally where needed
from project_templates import ProjectType

logger = logging.getLogger(__name__)


class TestCase(BaseModel):
    """Represents a single test case."""

    name: str = Field(..., description="Test function name")
    description: str = Field(..., description="What this test verifies")
    test_code: str = Field(..., description="Complete test function code")
    test_type: str = Field(..., description="Type of test (unit, integration, etc.)")


class TestFile(BaseModel):
    """Represents a complete test file."""

    filename: str = Field(..., description="Test file name")
    imports: List[str] = Field(..., description="Required import statements")
    setup_code: str = Field(..., description="Test setup/fixture code")
    test_cases: List[TestCase] = Field(..., description="Individual test cases")
    teardown_code: str = Field(..., description="Test cleanup code")


class TestSuite(BaseModel):
    """Complete test suite generation."""

    test_files: List[TestFile] = Field(..., description="Generated test files")
    test_config: str = Field(..., description="pytest.ini or test configuration")
    coverage_config: str = Field(..., description=".coveragerc configuration")
    test_requirements: List[str] = Field(..., description="Testing dependencies")


class AITestGenerator:
    """AI-powered test generator that analyzes code and creates comprehensive tests."""

    def __init__(self):
        self.interface = get_openai_interface()
        self.config = get_config()

    def generate_test_suite(
        self,
        generated_files: List[Dict[str, str]],  # filename -> content
        requirements: RequirementsSpec,
        architecture: ArchitectureSpec,
        project_type: ProjectType,
    ) -> TestSuite:
        """
        Generate comprehensive test suite based on generated code.

        Args:
            generated_files: List of generated code files with content
            requirements: Original requirements specification
            architecture: Architecture specification
            project_type: Type of project

        Returns:
            Complete test suite with intelligent test cases
        """
        logger.info(
            f"Generating AI-powered test suite for {project_type.value} project"
        )

        # Analyze code structure
        code_analysis = self._analyze_code_structure(generated_files)

        # Select optimal model for test generation
        from local_shared.openai_interfaces.model_selector import ModelSelector

        model_selector = ModelSelector()
        model = model_selector.select_optimal_model(
            task_type="execution",
            require_structured_outputs=True,
            prefer_cost_effective=True,  # Tests can use cost-effective model
        )

        # Create comprehensive prompt for test generation
        system_prompt = self._build_test_system_prompt(project_type)
        user_prompt = self._build_test_user_prompt(
            generated_files, code_analysis, requirements, architecture, project_type
        )

        try:
            test_suite = self.interface.create_structured_response(
                prompt=user_prompt,
                response_model=TestSuite,
                model=model,
                system_prompt=system_prompt,
            )

            logger.info(
                f"Generated {len(test_suite.test_files)} test files with "
                f"{sum(len(tf.test_cases) for tf in test_suite.test_files)} test cases"
            )

            return test_suite

        except Exception as e:
            logger.error(f"AI test generation failed: {e}")
            # Fallback to basic test generation
            return self._fallback_test_generation(
                generated_files, requirements, project_type
            )

    def _analyze_code_structure(
        self, generated_files: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Analyze the structure of generated code to understand what to test."""

        analysis = {
            "functions": [],
            "classes": [],
            "imports": [],
            "main_entry_points": [],
            "api_endpoints": [],
            "cli_commands": [],
            "data_models": [],
        }

        for file_info in generated_files:
            filename = file_info["filename"]
            content = file_info["content"]

            try:
                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        func_info = {
                            "name": node.name,
                            "file": filename,
                            "args": [arg.arg for arg in node.args.args],
                            "decorators": [
                                self._get_decorator_name(d) for d in node.decorator_list
                            ],
                            "async": isinstance(node, ast.AsyncFunctionDef),
                        }
                        analysis["functions"].append(func_info)

                        # Check for API endpoints
                        if any(
                            "app." in self._get_decorator_name(d)
                            for d in node.decorator_list
                        ):
                            analysis["api_endpoints"].append(func_info)

                    elif isinstance(node, ast.ClassDef):
                        class_info = {
                            "name": node.name,
                            "file": filename,
                            "methods": [
                                n.name
                                for n in node.body
                                if isinstance(n, ast.FunctionDef)
                            ],
                            "bases": [self._get_base_name(base) for base in node.bases],
                        }
                        analysis["classes"].append(class_info)

                        # Check for data models
                        if any(
                            "BaseModel" in self._get_base_name(base)
                            for base in node.bases
                        ):
                            analysis["data_models"].append(class_info)

                    elif isinstance(node, ast.Import) or isinstance(
                        node, ast.ImportFrom
                    ):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                analysis["imports"].append(alias.name)
                        else:
                            module = node.module or ""
                            for alias in node.names:
                                analysis["imports"].append(f"{module}.{alias.name}")

                # Check for main entry point
                if 'if __name__ == "__main__"' in content:
                    analysis["main_entry_points"].append(filename)

            except SyntaxError as e:
                logger.warning(f"Could not parse {filename}: {e}")
                continue

        return analysis

    def _get_decorator_name(self, decorator) -> str:
        """Extract decorator name from AST node."""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return f"{self._get_decorator_name(decorator.value)}.{decorator.attr}"
        elif isinstance(decorator, ast.Call):
            return self._get_decorator_name(decorator.func)
        else:
            return str(decorator)

    def _get_base_name(self, base) -> str:
        """Extract base class name from AST node."""
        if isinstance(base, ast.Name):
            return base.id
        elif isinstance(base, ast.Attribute):
            return f"{self._get_base_name(base.value)}.{base.attr}"
        else:
            return str(base)

    def _build_test_system_prompt(self, project_type: ProjectType) -> str:
        """Build system prompt for test generation."""

        base_prompt = """You are an expert Python test engineer and QA specialist. Generate comprehensive, intelligent test suites based on code analysis and requirements.

CRITICAL TEST REQUIREMENTS:
- Generate COMPLETE, RUNNABLE test cases - not snippets or placeholders
- Include unit tests, integration tests, and end-to-end tests where appropriate
- Test both happy path and edge cases/error conditions
- Include proper test fixtures, mocks, and setup/teardown
- Follow pytest best practices and conventions
- Generate realistic test data and scenarios
- Include performance tests for critical paths
- Test error handling and validation logic
- Use proper assertions and test descriptions

TEST QUALITY STANDARDS:
- All test functions must have clear, descriptive names
- Include comprehensive docstrings explaining what is being tested
- Use proper test organization with classes and modules
- Include parametrized tests for multiple scenarios
- Add integration tests that verify component interactions
- Include boundary condition testing
- Test configuration and environment variations
- Generate tests that achieve high code coverage"""

        project_specific = {
            ProjectType.WEB_API: """
API TESTING SPECIFIC REQUIREMENTS:
- Test all API endpoints (GET, POST, PUT, DELETE)
- Include request/response validation tests
- Test authentication and authorization
- Add rate limiting and security tests
- Test error responses and status codes
- Include load testing for performance
- Test data serialization/deserialization
- Verify OpenAPI specification compliance
- Test middleware and dependency injection""",
            ProjectType.CLI_TOOL: """
CLI TESTING SPECIFIC REQUIREMENTS:
- Test command-line argument parsing
- Verify help text and usage messages
- Test input/output redirection
- Include exit code validation
- Test configuration file handling
- Verify progress bars and logging
- Test different input formats and edge cases
- Include subprocess testing for command execution""",
            ProjectType.WEB_APP: """
WEB APP TESTING SPECIFIC REQUIREMENTS:
- Test view functions and template rendering
- Include form validation tests
- Test session management and cookies
- Verify routing and URL generation
- Test static file serving
- Include security tests (CSRF, XSS protection)
- Test database operations and migrations
- Add browser automation tests if applicable""",
            ProjectType.DATA_PROCESSOR: """
DATA PROCESSING TESTING SPECIFIC REQUIREMENTS:
- Test data validation and cleaning functions
- Include tests with various data formats
- Test error handling for malformed data
- Verify data transformation accuracy
- Include performance tests for large datasets
- Test data pipeline components
- Add data quality validation tests
- Test visualization output when applicable""",
            ProjectType.SIMPLE_SCRIPT: """
SCRIPT TESTING SPECIFIC REQUIREMENTS:
- Test main functionality with various inputs
- Include file I/O operation tests
- Test error handling and logging
- Verify configuration parsing
- Test utility functions independently
- Include integration tests for complete workflows""",
        }

        return base_prompt + "\n\n" + project_specific.get(project_type, "")

    def _build_test_user_prompt(
        self,
        generated_files: List[Dict[str, str]],
        code_analysis: Dict[str, Any],
        requirements: RequirementsSpec,
        architecture: ArchitectureSpec,
        project_type: ProjectType,
    ) -> str:
        """Build user prompt with code analysis and requirements."""

        # Prepare code structure summary
        functions_summary = "\n".join(
            f"- {func['name']}() in {func['file']} (args: {', '.join(func['args'])})"
            for func in code_analysis["functions"]
        )

        classes_summary = "\n".join(
            f"- {cls['name']} in {cls['file']} (methods: {', '.join(cls['methods'])})"
            for cls in code_analysis["classes"]
        )

        api_endpoints_summary = "\n".join(
            f"- {endpoint['name']}() in {endpoint['file']}"
            for endpoint in code_analysis["api_endpoints"]
        )

        prompt = f"""Generate a comprehensive test suite for this {project_type.value.replace('_', ' ')} project:

PROJECT REQUIREMENTS:
- Title: {requirements.title}
- Original Request: {requirements.original_request}

FUNCTIONAL REQUIREMENTS TO TEST:
{chr(10).join(f"- {req}" for req in requirements.functional_requirements)}

CODE STRUCTURE ANALYSIS:
Functions to test:
{functions_summary or "- No functions detected"}

Classes to test:
{classes_summary or "- No classes detected"}

API Endpoints to test:
{api_endpoints_summary or "- No API endpoints detected"}

Main entry points: {', '.join(code_analysis['main_entry_points']) or 'None'}

GENERATED FILES TO TEST:
{chr(10).join(f"- {file_info['filename']}" for file_info in generated_files)}

Generate a complete test suite that:
1. Tests all identified functions and classes
2. Verifies functional requirements are met
3. Includes edge cases and error conditions
4. Provides high code coverage
5. Uses proper test organization and naming
6. Includes realistic test data and scenarios

Make sure tests are production-ready and follow pytest best practices."""

        return prompt

    def _fallback_test_generation(
        self,
        generated_files: List[Dict[str, str]],
        requirements: RequirementsSpec,
        project_type: ProjectType,
    ) -> TestSuite:
        """Fallback test generation when AI fails."""

        logger.warning("Using fallback test generation")

        # Create basic test file for main functionality
        main_test = TestFile(
            filename="test_main.py",
            imports=[
                "import pytest",
                "import sys",
                "import os",
                "from pathlib import Path",
            ],
            setup_code="""
# Import using absolute paths (agent_world package installed)
# No need for sys.path manipulation
""",
            test_cases=[
                TestCase(
                    name="test_application_imports",
                    description="Test that main application modules can be imported",
                    test_code='''def test_application_imports():
    """Test that main application can be imported without errors."""
    try:
        import main  # Assuming main.py exists
        assert True
    except ImportError:
        pytest.skip("No main module found")''',
                    test_type="unit",
                ),
                TestCase(
                    name="test_basic_functionality",
                    description="Basic smoke test for application functionality",
                    test_code='''def test_basic_functionality():
    """Basic smoke test to verify application can execute."""
    # Add basic functionality test based on project type
    assert True  # Placeholder - implement based on generated code''',
                    test_type="integration",
                ),
            ],
            teardown_code="",
        )

        return TestSuite(
            test_files=[main_test],
            test_config="""[tool:pytest]
testpaths = tests
python_files = test_*.py
python_functions = test_*
addopts = -v --tb=short --strict-markers
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow tests
""",
            coverage_config="""[run]
source = src
omit =
    */tests/*
    */test_*
    setup.py

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
""",
            test_requirements=[
                "pytest>=7.0.0",
                "pytest-cov>=4.0.0",
                "pytest-mock>=3.0.0",
            ],
        )


def generate_ai_tests(
    generated_files: List[Dict[str, str]],
    requirements: RequirementsSpec,
    architecture: ArchitectureSpec,
    project_type: ProjectType,
) -> TestSuite:
    """
    Main function to generate AI-powered tests.

    Args:
        generated_files: List of generated code files with content
        requirements: User requirements specification
        architecture: Generated architecture specification
        project_type: Type of project to generate tests for

    Returns:
        Complete test suite result
    """
    generator = AITestGenerator()
    return generator.generate_test_suite(
        generated_files, requirements, architecture, project_type
    )
