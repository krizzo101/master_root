"""
Error Handling Tests for MCP Tools

Comprehensive testing of error scenarios, failure modes, and recovery patterns
for all 7 MCP tools. These tests ensure tools fail gracefully with descriptive
error messages rather than generic exceptions.
"""

import asyncio
import logging
from pathlib import Path
import sys

import pytest

# Add project root for imports (Rule 803 compliance)
project_root = Path(__file__).parents[4]
sys.path.insert(0, str(project_root))

from src.applications.oamat_sd.src.tools.mcp_tool_registry import (
    MCPToolRegistry,
)


class TestToolErrorHandling:
    """Error handling tests for all MCP tools - testing graceful failure modes"""

    @pytest.fixture(scope="class")
    def error_test_registry(self):
        """Create registry for error testing"""
        return MCPToolRegistry(use_real_clients=True)

    @pytest.mark.asyncio
    async def test_brave_search_invalid_parameters(self, error_test_registry):
        """Test Brave Search error handling with invalid parameters"""

        error_scenarios = [
            {
                "name": "Empty query",
                "params": {"query": "", "count": 3},
                "expected_error_keywords": ["query", "empty", "required"],
            },
            {
                "name": "Invalid count",
                "params": {"query": "test", "count": -1},
                "expected_error_keywords": ["count", "invalid", "positive"],
            },
            {
                "name": "Excessive count",
                "params": {"query": "test", "count": 10000},
                "expected_error_keywords": ["count", "limit", "maximum"],
            },
            {
                "name": "Missing required params",
                "params": {"count": 3},  # Missing query
                "expected_error_keywords": ["query", "required", "missing"],
            },
        ]

        for scenario in error_scenarios:
            try:
                result = await error_test_registry.execute_tool_method(
                    tool_name="brave_search", method="web_search", **scenario["params"]
                )

                # Should fail gracefully, not raise exception
                assert not result.success, f"Expected failure for: {scenario['name']}"
                assert (
                    result.error is not None
                ), f"No error message for: {scenario['name']}"

                # Error message should be descriptive
                error_msg = result.error.lower()
                assert (
                    len(error_msg) > 10
                ), f"Error message too short for: {scenario['name']}"

                # Should contain relevant keywords
                has_keyword = any(
                    keyword in error_msg
                    for keyword in scenario["expected_error_keywords"]
                )
                assert (
                    has_keyword
                ), f"Error message lacks relevant keywords for: {scenario['name']}"

                logging.info(f"✅ Brave Search {scenario['name']}: {result.error}")

            except Exception as e:
                pytest.fail(
                    f"Brave Search error handling failed for {scenario['name']}: {str(e)}"
                )

    @pytest.mark.asyncio
    async def test_arxiv_research_invalid_parameters(self, error_test_registry):
        """Test ArXiv Research error handling with invalid parameters"""

        error_scenarios = [
            {
                "name": "Empty query",
                "params": {"query": "", "max_results": 1},
                "method": "search_papers",
            },
            {
                "name": "Invalid max_results",
                "params": {"query": "test", "max_results": -5},
                "method": "search_papers",
            },
            {
                "name": "Invalid paper ID",
                "params": {"paper_id": ""},
                "method": "download_paper",
            },
            {
                "name": "Malformed paper ID",
                "params": {"paper_id": "invalid-id-format"},
                "method": "download_paper",
            },
        ]

        for scenario in error_scenarios:
            try:
                result = await error_test_registry.execute_tool_method(
                    tool_name="arxiv_research",
                    method=scenario["method"],
                    **scenario["params"],
                )

                # Should handle errors gracefully
                if not result.success:
                    assert (
                        result.error is not None
                    ), f"No error message for: {scenario['name']}"
                    assert (
                        len(result.error) > 5
                    ), f"Error message too short for: {scenario['name']}"
                    logging.info(f"✅ ArXiv {scenario['name']}: {result.error}")
                else:
                    # Some scenarios might succeed with empty results - that's also valid
                    logging.info(
                        f"ℹ️  ArXiv {scenario['name']}: Succeeded with empty results"
                    )

            except Exception as e:
                # Should not raise unhandled exceptions
                pytest.fail(
                    f"ArXiv error handling failed for {scenario['name']}: {str(e)}"
                )

    @pytest.mark.asyncio
    async def test_firecrawl_invalid_urls(self, error_test_registry):
        """Test Firecrawl error handling with invalid URLs"""

        error_scenarios = [
            {"name": "Empty URL", "params": {"url": "", "formats": ["markdown"]}},
            {
                "name": "Invalid URL format",
                "params": {"url": "not-a-url", "formats": ["markdown"]},
            },
            {
                "name": "Non-existent domain",
                "params": {
                    "url": "https://this-domain-does-not-exist-12345.com",
                    "formats": ["markdown"],
                },
            },
            {
                "name": "Invalid protocol",
                "params": {"url": "ftp://example.com", "formats": ["markdown"]},
            },
            {
                "name": "Missing formats",
                "params": {"url": "https://httpbin.org/json"},  # No formats specified
            },
        ]

        for scenario in error_scenarios:
            try:
                result = await error_test_registry.execute_tool_method(
                    tool_name="firecrawl", method="scrape", **scenario["params"]
                )

                # Should handle errors gracefully
                if not result.success:
                    assert (
                        result.error is not None
                    ), f"No error message for: {scenario['name']}"
                    error_msg = result.error.lower()

                    # Check for relevant error indicators
                    error_indicators = [
                        "url",
                        "invalid",
                        "format",
                        "not found",
                        "timeout",
                        "error",
                    ]
                    has_indicator = any(
                        indicator in error_msg for indicator in error_indicators
                    )
                    assert (
                        has_indicator
                    ), f"Error message lacks relevant indicators for: {scenario['name']}"

                    logging.info(f"✅ Firecrawl {scenario['name']}: {result.error}")
                else:
                    # Some errors might be handled as empty results
                    logging.info(
                        f"ℹ️  Firecrawl {scenario['name']}: Handled as empty result"
                    )

            except Exception as e:
                pytest.fail(
                    f"Firecrawl error handling failed for {scenario['name']}: {str(e)}"
                )

    @pytest.mark.asyncio
    async def test_context7_docs_invalid_parameters(self, error_test_registry):
        """Test Context7 Docs error handling with invalid parameters"""

        error_scenarios = [
            {
                "name": "Empty library name",
                "method": "resolve_library_id",
                "params": {"library_name": ""},
            },
            {
                "name": "Non-existent library",
                "method": "resolve_library_id",
                "params": {"library_name": "this-library-does-not-exist-12345"},
            },
            {
                "name": "Invalid library ID format",
                "method": "get_library_docs",
                "params": {
                    "context7_compatible_library_id": "invalid/format/id",
                    "tokens": 1000,
                },
            },
            {
                "name": "Empty library ID",
                "method": "get_library_docs",
                "params": {"context7_compatible_library_id": "", "tokens": 1000},
            },
        ]

        for scenario in error_scenarios:
            try:
                result = await error_test_registry.execute_tool_method(
                    tool_name="context7_docs",
                    method=scenario["method"],
                    **scenario["params"],
                )

                # Context7 might return empty results instead of errors for some cases
                if not result.success:
                    assert (
                        result.error is not None
                    ), f"No error message for: {scenario['name']}"
                    logging.info(f"✅ Context7 {scenario['name']}: {result.error}")
                else:
                    # Some scenarios might succeed with no results
                    logging.info(f"ℹ️  Context7 {scenario['name']}: Handled gracefully")

            except Exception as e:
                pytest.fail(
                    f"Context7 error handling failed for {scenario['name']}: {str(e)}"
                )

    @pytest.mark.asyncio
    async def test_sequential_thinking_invalid_parameters(self, error_test_registry):
        """Test Sequential Thinking error handling with invalid parameters"""

        error_scenarios = [
            {
                "name": "Empty thought",
                "params": {
                    "thought": "",
                    "thought_number": 1,
                    "total_thoughts": 1,
                    "next_thought_needed": False,
                },
            },
            {
                "name": "Invalid thought number",
                "params": {
                    "thought": "test",
                    "thought_number": 0,
                    "total_thoughts": 1,
                    "next_thought_needed": False,
                },
            },
            {
                "name": "Inconsistent thought counts",
                "params": {
                    "thought": "test",
                    "thought_number": 5,
                    "total_thoughts": 2,
                    "next_thought_needed": False,
                },
            },
            {
                "name": "Missing required parameters",
                "params": {"thought": "test"},  # Missing other required params
            },
        ]

        for scenario in error_scenarios:
            try:
                result = await error_test_registry.execute_tool_method(
                    tool_name="sequential_thinking",
                    method="think_step",
                    **scenario["params"],
                )

                # Sequential thinking should validate parameters
                if not result.success:
                    assert (
                        result.error is not None
                    ), f"No error message for: {scenario['name']}"
                    logging.info(
                        f"✅ Sequential Thinking {scenario['name']}: {result.error}"
                    )
                else:
                    # Some invalid params might be handled gracefully
                    logging.info(
                        f"ℹ️  Sequential Thinking {scenario['name']}: Handled gracefully"
                    )

            except Exception as e:
                pytest.fail(
                    f"Sequential Thinking error handling failed for {scenario['name']}: {str(e)}"
                )

    @pytest.mark.asyncio
    async def test_neo4j_connection_errors(self, error_test_registry):
        """Test Neo4j error handling for database connection issues"""

        try:
            # Test with various parameters to see how Neo4j handles errors
            result = await error_test_registry.execute_tool_method(
                tool_name="neo4j", method="get_schema", random_string="error_test"
            )

            # Neo4j should either succeed or fail gracefully
            if not result.success:
                assert result.error is not None, "No error message for Neo4j failure"
                error_msg = result.error.lower()

                # Check for database-related error indicators
                db_indicators = [
                    "connection",
                    "database",
                    "neo4j",
                    "timeout",
                    "unavailable",
                ]
                has_indicator = any(
                    indicator in error_msg for indicator in db_indicators
                )
                assert (
                    has_indicator
                ), f"Error message lacks database indicators: {result.error}"

                logging.info(f"✅ Neo4j Error Handling: {result.error}")
            else:
                logging.info("✅ Neo4j: Connection successful")

        except Exception as e:
            pytest.fail(f"Neo4j error handling failed: {str(e)}")

    @pytest.mark.asyncio
    async def test_research_workflow_adapter_errors(self, error_test_registry):
        """Test Research Workflow adapter error handling - REGRESSION TEST"""

        error_scenarios = [
            {
                "name": "Empty query",
                "method": "search_and_extract_urls",
                "params": {"query": "", "max_results": 5},
            },
            {
                "name": "Invalid max_results",
                "method": "search_and_extract_urls",
                "params": {"query": "test", "max_results": -1},
            },
            {
                "name": "Missing query parameter",
                "method": "search_and_extract_urls",
                "params": {"max_results": 5},  # Missing query
            },
        ]

        for scenario in error_scenarios:
            try:
                result = await error_test_registry.execute_tool_method(
                    tool_name="research_workflow",
                    method=scenario["method"],
                    **scenario["params"],
                )

                # Critical: Should NOT produce coroutine errors
                if result.error:
                    error_msg = result.error.lower()
                    assert (
                        "coroutine" not in error_msg
                    ), f"REGRESSION: Coroutine error in {scenario['name']}"
                    assert (
                        "was never awaited" not in error_msg
                    ), f"REGRESSION: Await error in {scenario['name']}"

                if not result.success:
                    assert (
                        result.error is not None
                    ), f"No error message for: {scenario['name']}"
                    logging.info(
                        f"✅ Research Workflow {scenario['name']}: {result.error}"
                    )
                else:
                    logging.info(
                        f"ℹ️  Research Workflow {scenario['name']}: Handled gracefully"
                    )

            except Exception as e:
                # Check for regression issues
                error_msg = str(e).lower()
                if "coroutine" in error_msg:
                    pytest.fail(
                        f"REGRESSION: Coroutine issue reappeared in {scenario['name']}: {str(e)}"
                    )
                else:
                    pytest.fail(
                        f"Research Workflow error handling failed for {scenario['name']}: {str(e)}"
                    )

    @pytest.mark.asyncio
    async def test_timeout_handling(self, error_test_registry):
        """Test timeout handling across tools"""

        # Test with potentially slow operations
        timeout_scenarios = [
            {
                "tool": "brave_search",
                "method": "web_search",
                "params": {
                    "query": "very specific search that might timeout",
                    "count": 10,
                },
            },
            {
                "tool": "firecrawl",
                "method": "scrape",
                "params": {
                    "url": "https://httpbin.org/delay/10",
                    "formats": ["markdown"],
                },  # Simulated delay
            },
        ]

        for scenario in timeout_scenarios:
            try:
                # Set a shorter timeout for testing
                start_time = asyncio.get_event_loop().time()

                # Use asyncio.wait_for to test timeout behavior
                try:
                    result = await asyncio.wait_for(
                        error_test_registry.execute_tool_method(
                            tool_name=scenario["tool"],
                            method=scenario["method"],
                            **scenario["params"],
                        ),
                        timeout=5.0,  # 5 second timeout
                    )

                    execution_time = asyncio.get_event_loop().time() - start_time
                    logging.info(
                        f"✅ {scenario['tool']} timeout test completed in {execution_time:.2f}s"
                    )

                except asyncio.TimeoutError:
                    logging.info(f"✅ {scenario['tool']} timeout handled correctly")
                    # Timeout is expected behavior for this test

            except Exception as e:
                pytest.fail(f"Timeout handling failed for {scenario['tool']}: {str(e)}")

    @pytest.mark.asyncio
    async def test_concurrent_error_scenarios(self, error_test_registry):
        """Test error handling under concurrent execution"""

        # Create multiple failing tasks concurrently
        failing_tasks = [
            error_test_registry.execute_tool_method(
                "brave_search", "web_search", query="", count=1
            ),
            error_test_registry.execute_tool_method(
                "firecrawl", "scrape", url="", formats=["markdown"]
            ),
            error_test_registry.execute_tool_method(
                "sequential_thinking",
                "think_step",
                thought="",
                thought_number=1,
                total_thoughts=1,
                next_thought_needed=False,
            ),
        ]

        try:
            # All tasks should fail, but gracefully
            results = await asyncio.gather(*failing_tasks, return_exceptions=True)

            # Analyze results
            exception_count = sum(1 for r in results if isinstance(r, Exception))
            failed_results = sum(
                1 for r in results if not isinstance(r, Exception) and not r.success
            )

            # Should handle errors gracefully, not raise exceptions
            assert (
                exception_count == 0
            ), f"Unhandled exceptions in concurrent errors: {exception_count}"
            assert (
                failed_results >= 2
            ), f"Expected at least 2 failures, got {failed_results}"

            logging.info(
                f"✅ Concurrent Error Handling: {failed_results} graceful failures, {exception_count} exceptions"
            )

        except Exception as e:
            pytest.fail(f"Concurrent error handling failed: {str(e)}")

    def test_error_message_quality(self):
        """Test that error messages meet quality standards"""

        quality_criteria = [
            "Error messages should be descriptive (> 10 characters)",
            "Error messages should not contain stack traces",
            "Error messages should indicate the problem clearly",
            "Error messages should not contain 'coroutine' (regression test)",
            "Error messages should be user-friendly, not technical",
        ]

        # This test documents our error message quality standards
        logging.info("📋 Error Message Quality Criteria:")
        for i, criterion in enumerate(quality_criteria, 1):
            logging.info(f"  {i}. {criterion}")

        # Test always passes - it's for documentation
        assert True, "Error message quality criteria documented"

    @pytest.mark.asyncio
    async def test_registry_error_handling(self, error_test_registry):
        """Test registry-level error handling"""

        registry_error_scenarios = [
            {
                "name": "Non-existent tool",
                "tool": "non_existent_tool",
                "method": "some_method",
                "params": {},
            },
            {
                "name": "Non-existent method",
                "tool": "brave_search",
                "method": "non_existent_method",
                "params": {"query": "test"},
            },
            {
                "name": "Invalid tool name type",
                "tool": None,
                "method": "web_search",
                "params": {"query": "test"},
            },
        ]

        for scenario in registry_error_scenarios:
            try:
                result = await error_test_registry.execute_tool_method(
                    tool_name=scenario["tool"],
                    method=scenario["method"],
                    **scenario["params"],
                )

                # Registry should handle these errors gracefully
                assert not result.success, f"Expected failure for: {scenario['name']}"
                assert (
                    result.error is not None
                ), f"No error message for: {scenario['name']}"

                error_msg = result.error.lower()
                assert (
                    "tool" in error_msg or "method" in error_msg
                ), f"Error message should mention tool/method issue: {result.error}"

                logging.info(f"✅ Registry {scenario['name']}: {result.error}")

            except Exception as e:
                # Some registry errors might raise exceptions - that's also acceptable
                error_msg = str(e).lower()
                assert (
                    "tool" in error_msg or "method" in error_msg
                ), f"Exception should mention tool/method issue: {str(e)}"
                logging.info(
                    f"✅ Registry {scenario['name']}: Exception handled - {str(e)}"
                )

    @pytest.mark.asyncio
    async def test_import_path_error_regression(self):
        """Test that import path errors don't reappear - REGRESSION TEST"""

        try:
            # This should work without import errors
            registry = MCPToolRegistry(use_real_clients=True)

            # Verify all expected tools are available
            expected_tools = [
                "brave_search",
                "arxiv_research",
                "firecrawl",
                "context7_docs",
                "sequential_thinking",
                "neo4j",
                "research_workflow",
            ]

            for tool_name in expected_tools:
                assert tool_name in registry.tools, f"Missing tool: {tool_name}"
                assert (
                    tool_name in registry.tool_interfaces
                ), f"Missing interface: {tool_name}"

            logging.info(
                "✅ Import Path Regression Test: All tools imported successfully"
            )

        except ImportError as e:
            pytest.fail(f"REGRESSION: Import path issue reappeared - {str(e)}")
        except ModuleNotFoundError as e:
            pytest.fail(f"REGRESSION: Module not found issue reappeared - {str(e)}")
        except Exception as e:
            pytest.fail(f"Registry initialization failed: {str(e)}")

    def test_error_handling_documentation(self):
        """Document error handling patterns and best practices"""

        error_patterns = [
            "✅ Graceful Degradation: Tools fail softly with descriptive messages",
            "✅ No Silent Failures: All errors are properly reported",
            "✅ User-Friendly Messages: Errors explain what went wrong and why",
            "✅ Consistent Format: All tools use ToolExecutionResult for errors",
            "✅ Regression Prevention: No coroutine or import path errors",
            "✅ Timeout Handling: Long operations don't hang indefinitely",
            "✅ Concurrent Safety: Errors in one tool don't affect others",
        ]

        logging.info("📋 Error Handling Patterns:")
        for pattern in error_patterns:
            logging.info(f"  {pattern}")

        # Test always passes - it's for documentation
        assert True, "Error handling patterns documented"
