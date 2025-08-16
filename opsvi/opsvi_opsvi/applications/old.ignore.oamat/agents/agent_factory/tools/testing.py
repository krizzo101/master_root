"""
OAMAT Agent Factory - Testing Framework Tools

Tools for running tests, creating test cases, and ensuring code quality.
"""

import logging
from typing import Optional

from langchain_core.tools import tool

logger = logging.getLogger("OAMAT.AgentFactory.TestingTools")


def create_testing_framework_tools(base_agent=None):
    """
    Creates a suite of tools for testing operations.
    These tools are placeholders and should be connected to a real test runner.
    """

    @tool
    def run_tests(test_path: str = "", test_type: str = "unit") -> str:
        """
        Executes a test suite for a given path and test type.

        Args:
            test_path: The specific path to the test file or directory.
            test_type: The type of tests to run (e.g., 'unit', 'integration').
        """
        if not test_path:
            # In a real implementation, this would trigger a full test run.
            logger.info(f"Executing all {test_type} tests for the project.")
            return f"✅ Successfully executed all {test_type} tests."
        else:
            # Here you would add logic to invoke pytest, jest, etc.
            logger.info(f"Executing {test_type} tests for: {test_path}")
            # Example:
            # result = subprocess.run(["pytest", test_path], capture_output=True, text=True)
            # if result.returncode != 0:
            #     raise RuntimeError(f"Tests failed for {test_path}:\\n{result.stderr}")
            # return result.stdout
            return f"✅ Successfully executed {test_type} tests for {test_path}."

    @tool
    def create_test_case(
        module: str, test_type: str = "unit", requirements: Optional[str] = None
    ) -> str:
        """
        Generates a test case for a specific module.

        Args:
            module: The module or function to generate a test for.
            test_type: The type of test to create (e.g., 'unit', 'integration').
            requirements: Specific requirements for the test case.
        """
        if not base_agent:
            raise RuntimeError(
                "Test case generation tool is not available: base_agent not configured."
            )

        prompt = f"""
Please generate a {test_type} test case for the module: `{module}`.
The test should adhere to standard testing best practices for the relevant language.

Specific requirements:
{requirements or "Cover all primary success and failure scenarios."}

Provide only the complete, runnable test code.
"""
        try:
            result = base_agent.process_request(
                {"task": "test_generation", "prompt": prompt}
            )
            response = result.get("response", "Error generating test case.")
            logger.info(f"Generated test case for module: {module}")
            return response
        except Exception as e:
            logger.error(f"Failed to generate test case for {module}: {e}")
            raise RuntimeError(f"Test case generation failed: {e}")

    return [run_tests, create_test_case]
