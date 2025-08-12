"""
Integration Tests for Real MCP Tool Execution

Comprehensive testing of all 7 MCP tools using REAL implementations to prove:
1. Real API calls are happening (network latency evidence)
2. All tools return actual data structures
3. Error handling works correctly
4. Performance meets expectations
5. Recent fixes (coroutine, imports) stay resolved

This test suite follows the "NO MOCKING" philosophy - testing real implementations only.
"""

import asyncio
import logging
import sys
import time
from pathlib import Path

import pytest

# Add project root for imports (Rule 803 compliance)
project_root = Path(__file__).parents[4]
sys.path.insert(0, str(project_root))

from src.applications.oamat_sd.src.tools.mcp_tool_registry import (
    MCPToolRegistry,
)


class TestRealToolExecution:
    """Integration tests for real MCP tool execution - NO MOCKS"""

    @pytest.fixture(scope="class")
    def real_registry(self):
        """Create REAL MCP tool registry instance"""
        # Force real clients, never mocks
        return MCPToolRegistry(use_real_clients=True)

    @pytest.fixture
    def performance_tracker(self):
        """Track execution times to prove real API calls"""
        return {"execution_times": [], "start_time": None}

    @pytest.mark.asyncio
    @pytest.mark.network
    async def test_brave_search_real_execution(
        self, real_registry, performance_tracker
    ):
        """Test Brave Search with real API calls and timing validation"""
        performance_tracker["start_time"] = time.time()

        try:
            result = await real_registry.execute_tool_method(
                tool_name="brave_search",
                method="web_search",
                query="python testing frameworks",
                count=3,
            )

            execution_time = time.time() - performance_tracker["start_time"]
            performance_tracker["execution_times"].append(execution_time)

            # Validate real execution indicators
            assert result.success, f"Brave search failed: {result.error}"
            assert (
                execution_time > 0.3
            ), f"Too fast ({execution_time:.2f}s) - might be mocked"
            assert (
                execution_time < 10.0
            ), f"Too slow ({execution_time:.2f}s) - possible timeout"

            # Validate real data structure
            assert result.result is not None
            result_str = str(result.result)
            assert any(
                indicator in result_str.lower()
                for indicator in ["http", "www", "search", "results"]
            ), "Missing web search indicators"

            # Validate response contains actual URLs
            import re

            urls = re.findall(r'https?://[^\s<>"\[\]{}|\\^`]+', result_str)
            assert len(urls) > 0, "No URLs found in search results"

            logging.info(
                f"✅ Brave Search: {execution_time:.2f}s, {len(urls)} URLs found"
            )

        except Exception as e:
            pytest.fail(f"Brave Search real execution failed: {str(e)}")

    @pytest.mark.asyncio
    @pytest.mark.network
    @pytest.mark.slow
    async def test_arxiv_research_real_execution(
        self, real_registry, performance_tracker
    ):
        """Test ArXiv Research with real paper search and timing validation"""
        performance_tracker["start_time"] = time.time()

        try:
            result = await real_registry.execute_tool_method(
                tool_name="arxiv_research",
                method="search_papers",
                query="machine learning optimization",
                max_results=2,
                categories=["cs.LG"],
            )

            execution_time = time.time() - performance_tracker["start_time"]
            performance_tracker["execution_times"].append(execution_time)

            # ArXiv calls should be slower due to API complexity
            assert result.success, f"ArXiv search failed: {result.error}"
            assert (
                execution_time > 0.5
            ), f"Too fast ({execution_time:.2f}s) - might be mocked"
            assert (
                execution_time < 15.0
            ), f"Too slow ({execution_time:.2f}s) - possible timeout"

            # Validate real ArXiv data structure
            assert result.result is not None
            result_str = str(result.result)
            assert any(
                indicator in result_str.lower()
                for indicator in ["arxiv", "paper", "abstract", "author"]
            ), "Missing ArXiv indicators"

            logging.info(
                f"✅ ArXiv Research: {execution_time:.2f}s, real paper data returned"
            )

        except Exception as e:
            pytest.fail(f"ArXiv Research real execution failed: {str(e)}")

    @pytest.mark.asyncio
    @pytest.mark.network
    async def test_firecrawl_real_execution(self, real_registry, performance_tracker):
        """Test Firecrawl with real web scraping and timing validation"""
        performance_tracker["start_time"] = time.time()

        try:
            # Use a reliable test URL
            result = await real_registry.execute_tool_method(
                tool_name="firecrawl",
                method="scrape",
                url="https://httpbin.org/json",
                formats=["markdown"],
            )

            execution_time = time.time() - performance_tracker["start_time"]
            performance_tracker["execution_times"].append(execution_time)

            # Firecrawl should show network latency
            assert result.success, f"Firecrawl scraping failed: {result.error}"
            assert (
                execution_time > 0.4
            ), f"Too fast ({execution_time:.2f}s) - might be mocked"
            assert (
                execution_time < 12.0
            ), f"Too slow ({execution_time:.2f}s) - possible timeout"

            # Validate real scraped content
            assert result.result is not None
            result_str = str(result.result)
            assert len(result_str) > 50, "Scraped content too short"

            logging.info(f"✅ Firecrawl: {execution_time:.2f}s, real content scraped")

        except Exception as e:
            pytest.fail(f"Firecrawl real execution failed: {str(e)}")

    @pytest.mark.asyncio
    @pytest.mark.network
    async def test_context7_docs_real_execution(
        self, real_registry, performance_tracker
    ):
        """Test Context7 with real documentation retrieval and timing validation"""
        performance_tracker["start_time"] = time.time()

        try:
            # First resolve a library ID
            resolve_result = await real_registry.execute_tool_method(
                tool_name="context7_docs",
                method="resolve_library_id",
                library_name="react",
            )

            assert (
                resolve_result.success
            ), f"Library resolution failed: {resolve_result.error}"

            # Then get documentation
            docs_result = await real_registry.execute_tool_method(
                tool_name="context7_docs",
                method="get_library_docs",
                context7_compatible_library_id="/facebook/react",
                topic="hooks",
                tokens=5000,
            )

            execution_time = time.time() - performance_tracker["start_time"]
            performance_tracker["execution_times"].append(execution_time)

            # Context7 should show API call latency
            assert (
                docs_result.success
            ), f"Documentation retrieval failed: {docs_result.error}"
            assert (
                execution_time > 0.3
            ), f"Too fast ({execution_time:.2f}s) - might be mocked"
            assert (
                execution_time < 8.0
            ), f"Too slow ({execution_time:.2f}s) - possible timeout"

            # Validate real documentation content
            assert docs_result.result is not None
            result_str = str(docs_result.result)
            assert any(
                indicator in result_str.lower()
                for indicator in ["react", "hook", "component", "documentation"]
            ), "Missing documentation indicators"

            logging.info(f"✅ Context7 Docs: {execution_time:.2f}s, real docs retrieved")

        except Exception as e:
            pytest.fail(f"Context7 Docs real execution failed: {str(e)}")

    @pytest.mark.asyncio
    async def test_sequential_thinking_real_execution(
        self, real_registry, performance_tracker
    ):
        """Test Sequential Thinking with real reasoning and timing validation"""
        performance_tracker["start_time"] = time.time()

        try:
            result = await real_registry.execute_tool_method(
                tool_name="sequential_thinking",
                method="think_step",
                thought="Let me analyze the benefits of test-driven development",
                thought_number=1,
                total_thoughts=3,
                next_thought_needed=True,
            )

            execution_time = time.time() - performance_tracker["start_time"]
            performance_tracker["execution_times"].append(execution_time)

            # Sequential thinking processes should take measurable time
            assert result.success, f"Sequential thinking failed: {result.error}"
            assert (
                execution_time > 0.1
            ), f"Too fast ({execution_time:.2f}s) - might be mocked"
            assert (
                execution_time < 15.0
            ), f"Too slow ({execution_time:.2f}s) - possible timeout"

            # Validate reasoning result structure
            assert result.result is not None
            result_str = str(result.result)
            assert len(result_str) > 20, "Thinking result too short"

            logging.info(
                f"✅ Sequential Thinking: {execution_time:.2f}s, real reasoning completed"
            )

        except Exception as e:
            pytest.fail(f"Sequential Thinking real execution failed: {str(e)}")

    @pytest.mark.asyncio
    async def test_neo4j_real_execution(self, real_registry, performance_tracker):
        """Test Neo4j with real database operations and timing validation"""
        performance_tracker["start_time"] = time.time()

        try:
            # Test schema retrieval first
            result = await real_registry.execute_tool_method(
                tool_name="neo4j", method="get_schema", random_string="test"
            )

            execution_time = time.time() - performance_tracker["start_time"]
            performance_tracker["execution_times"].append(execution_time)

            # Database operations should show connection latency
            assert result.success, f"Neo4j schema retrieval failed: {result.error}"
            assert (
                execution_time > 0.05
            ), f"Too fast ({execution_time:.2f}s) - might be mocked"
            assert (
                execution_time < 5.0
            ), f"Too slow ({execution_time:.2f}s) - possible timeout"

            # Validate database response structure
            assert result.result is not None

            logging.info(f"✅ Neo4j: {execution_time:.2f}s, real database connection")

        except Exception as e:
            pytest.fail(f"Neo4j real execution failed: {str(e)}")

    @pytest.mark.asyncio
    @pytest.mark.network
    async def test_research_workflow_adapter_execution(
        self, real_registry, performance_tracker
    ):
        """Test Research Workflow adapter with real execution - CRITICAL REGRESSION TEST"""
        performance_tracker["start_time"] = time.time()

        try:
            # This tests the RegistryAdapter that fixed coroutine issues
            result = await real_registry.execute_tool_method(
                tool_name="research_workflow",
                method="search_and_extract_urls",
                query="python web frameworks",
                max_results=5,
            )

            execution_time = time.time() - performance_tracker["start_time"]
            performance_tracker["execution_times"].append(execution_time)

            # Should NOT produce coroutine errors anymore
            assert result.success, f"Research workflow failed: {result.error}"
            assert "coroutine" not in str(
                result.error or ""
            ), "Coroutine issue detected!"
            assert (
                execution_time > 0.3
            ), f"Too fast ({execution_time:.2f}s) - might be mocked"

            # Validate adapter properly handled the execution
            assert result.result is not None
            result_str = str(result.result)
            assert len(result_str) > 10, "Research workflow result too short"

            logging.info(
                f"✅ Research Workflow: {execution_time:.2f}s, adapter working correctly"
            )

        except Exception as e:
            # Specifically check for coroutine-related errors
            error_msg = str(e).lower()
            if "coroutine" in error_msg:
                pytest.fail(f"REGRESSION: Coroutine issue reappeared - {str(e)}")
            else:
                pytest.fail(f"Research Workflow adapter execution failed: {str(e)}")

    @pytest.mark.asyncio
    async def test_parallel_tool_execution(self, real_registry):
        """Test concurrent execution of multiple tools - integration stress test"""
        start_time = time.time()

        try:
            # Execute multiple tools concurrently
            tasks = [
                real_registry.execute_tool_method(
                    "brave_search", "web_search", query="test query 1", count=2
                ),
                real_registry.execute_tool_method(
                    "sequential_thinking",
                    "think_step",
                    thought="Think about testing",
                    thought_number=1,
                    total_thoughts=2,
                    next_thought_needed=False,
                ),
                real_registry.execute_tool_method(
                    "neo4j", "get_schema", random_string="parallel_test"
                ),
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)
            total_time = time.time() - start_time

            # Validate parallel execution worked
            successful_results = [
                r for r in results if not isinstance(r, Exception) and r.success
            ]
            assert (
                len(successful_results) >= 2
            ), f"Too many parallel execution failures: {results}"

            # Parallel execution should be faster than sequential
            assert total_time < 10.0, f"Parallel execution too slow: {total_time:.2f}s"

            logging.info(
                f"✅ Parallel Execution: {total_time:.2f}s, {len(successful_results)}/3 succeeded"
            )

        except Exception as e:
            pytest.fail(f"Parallel tool execution failed: {str(e)}")

    def test_performance_evidence_analysis(self, performance_tracker):
        """Analyze execution times to prove real API calls vs mocks"""
        times = performance_tracker["execution_times"]

        if not times:
            pytest.skip("No execution times recorded")

        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)

        # Evidence-based validation
        assert min_time > 0.05, f"Minimum time {min_time:.3f}s suggests mocking"
        assert avg_time > 0.2, f"Average time {avg_time:.2f}s suggests mocking"
        assert max_time < 20.0, f"Maximum time {max_time:.2f}s suggests timeouts"

        # Log performance evidence
        logging.info(
            f"📊 Performance Evidence - Min: {min_time:.2f}s, Avg: {avg_time:.2f}s, Max: {max_time:.2f}s"
        )
        logging.info("✅ Times consistent with real API calls (not mocks)")

    @pytest.mark.asyncio
    async def test_import_path_regression(self, real_registry):
        """Test that import path fixes remain stable - REGRESSION TEST"""
        try:
            # This should work without import errors due to enhanced project root detection
            registry_2 = MCPToolRegistry(use_real_clients=True)

            # Verify all tools initialized
            assert (
                len(registry_2.tools) == 7
            ), f"Expected 7 tools, got {len(registry_2.tools)}"

            # Test that we can access tool interfaces
            for tool_name in ["brave_search", "arxiv_research", "firecrawl"]:
                assert (
                    tool_name in registry_2.tool_interfaces
                ), f"Missing tool interface: {tool_name}"

            logging.info(
                "✅ Import Path Regression Test: All tools initialized correctly"
            )

        except ImportError as e:
            pytest.fail(f"REGRESSION: Import path issue reappeared - {str(e)}")
        except Exception as e:
            pytest.fail(f"Import path regression test failed: {str(e)}")

    @pytest.mark.asyncio
    async def test_error_handling_invalid_parameters(self, real_registry):
        """Test error handling with invalid parameters"""
        try:
            # Test with invalid parameters
            result = await real_registry.execute_tool_method(
                tool_name="brave_search",
                method="web_search",
                query="",  # Empty query
                count=-1,  # Invalid count
            )

            # Should handle gracefully with descriptive error
            assert not result.success, "Should fail with invalid parameters"
            assert result.error is not None, "Error message should be provided"
            assert len(result.error) > 10, "Error message should be descriptive"

            logging.info(f"✅ Error Handling: {result.error}")

        except Exception as e:
            pytest.fail(f"Error handling test failed: {str(e)}")

    @pytest.mark.asyncio
    async def test_tool_metadata_accuracy(self, real_registry):
        """Test that tool metadata matches actual capabilities"""
        for tool_name, metadata in real_registry.tools.items():
            # Verify tool interface exists
            assert (
                tool_name in real_registry.tool_interfaces
            ), f"Missing interface for {tool_name}"

            # Verify methods are available
            tool_interface = real_registry.tool_interfaces[tool_name]
            assert tool_interface is not None, f"Tool interface is None for {tool_name}"

            # Verify basic tool properties
            assert metadata.name == tool_name
            assert len(metadata.methods) > 0, f"No methods defined for {tool_name}"
            assert metadata.description, f"No description for {tool_name}"

            logging.info(
                f"✅ {tool_name}: {len(metadata.methods)} methods, {metadata.category}"
            )

    @pytest.mark.asyncio
    async def test_all_tools_basic_functionality(self, real_registry):
        """Smoke test - verify all 7 tools can execute at least one method"""
        tool_test_cases = {
            "brave_search": ("web_search", {"query": "test", "count": 1}),
            "arxiv_research": ("search_papers", {"query": "test", "max_results": 1}),
            "firecrawl": ("scrape", {"url": "https://httpbin.org/json"}),
            "context7_docs": ("resolve_library_id", {"library_name": "python"}),
            "sequential_thinking": (
                "think_step",
                {
                    "thought": "test",
                    "thought_number": 1,
                    "total_thoughts": 1,
                    "next_thought_needed": False,
                },
            ),
            "neo4j": ("get_schema", {"random_string": "test"}),
            "research_workflow": (
                "search_and_extract_urls",
                {"query": "test", "max_results": 1},
            ),
        }

        results = {}
        for tool_name, (method, params) in tool_test_cases.items():
            try:
                result = await real_registry.execute_tool_method(
                    tool_name, method, **params
                )
                results[tool_name] = result.success
                if result.success:
                    logging.info(f"✅ {tool_name}.{method}: Working")
                else:
                    logging.warning(
                        f"⚠️  {tool_name}.{method}: Failed - {result.error}"
                    )
            except Exception as e:
                results[tool_name] = False
                logging.error(f"❌ {tool_name}.{method}: Exception - {str(e)}")

        # At least 5 out of 7 tools should work (allowing for network issues)
        successful_tools = sum(results.values())
        assert successful_tools >= 5, f"Too many tool failures: {results}"

        logging.info(f"📊 Tool Functionality: {successful_tools}/7 tools working")
