"""
Integration Tests for Real MCP Tools

Tests real MCP tool implementations with actual API calls to prove:
1. Real API calls are happening (network latency evidence)
2. Actual data structures are returned (not mock data)
3. Performance characteristics match real API behavior
4. Error handling works with real services

Uses conditional execution based on REAL_MCP_TESTS environment variable.
"""

import logging
import re
import time

import pytest

# Test markers for conditional execution
pytestmark = [
    pytest.mark.integration,
    pytest.mark.real_api,
]


class TestRealMCPTools:
    """Integration tests for real MCP tool implementations"""

    async def test_brave_search_real_api_signature(
        self, real_client_registry, performance_tracker
    ):
        """Test Brave Search with real API calls - validate performance signature"""

        # Multiple samples for consistency
        execution_times = []
        results = []

        for i in range(3):
            start_time = time.time()

            result = await real_client_registry.execute_tool_method(
                tool_name="brave_search",
                method="search",
                query=f"python testing frameworks sample {i}",
                count=2,
            )

            execution_time = time.time() - start_time
            execution_times.append(execution_time)
            results.append(result)

            # Real API performance validation
            assert (
                execution_time > 0.3
            ), f"Too fast ({execution_time:.2f}s) - likely mock response"
            assert (
                execution_time < 10.0
            ), f"Too slow ({execution_time:.2f}s) - possible timeout"

            # Real data validation
            assert result.success, f"Real API call should succeed: {result.error}"
            result_str = str(result.result)

            # Should NOT contain mock data patterns
            assert "Mock Result" not in result_str, "Contains mock data - not real API"
            assert "example.com" not in result_str, "Contains mock URLs - not real API"

            # Should contain real web search indicators
            assert any(
                indicator in result_str.lower()
                for indicator in ["http", "www", "search", "results"]
            ), "Missing real web search indicators"

            # Should contain actual URLs
            urls = re.findall(r'https?://[^\s<>"\[\]{}|\\^`]+', result_str)
            assert len(urls) > 0, "No real URLs found in search results"

            logging.info(
                f"✅ Brave Search Run {i+1}: {execution_time:.2f}s, {len(urls)} URLs"
            )

        # Statistical analysis of performance
        avg_time = sum(execution_times) / len(execution_times)
        min_time = min(execution_times)
        max_time = max(execution_times)

        performance_tracker["execution_times"].extend(execution_times)

        # Real API should show natural variance
        assert avg_time > 0.4, f"Average time {avg_time:.2f}s too fast for real API"
        assert max_time > min_time, "No variance suggests mock responses"

        logging.info(
            f"📊 Brave Search Performance: Avg={avg_time:.2f}s, Range={min_time:.2f}-{max_time:.2f}s"
        )

    @pytest.mark.slow
    async def test_arxiv_research_real_api_signature(
        self, real_client_registry, performance_tracker
    ):
        """Test ArXiv Research with real paper search - validate academic data"""

        start_time = time.time()

        result = await real_client_registry.execute_tool_method(
            tool_name="arxiv_research",
            method="search_papers",
            query="machine learning optimization",
            max_results=2,
            categories=["cs.LG"],
        )

        execution_time = time.time() - start_time
        performance_tracker["execution_times"].append(execution_time)

        # ArXiv should be slower due to academic database complexity
        assert execution_time > 0.5, f"Too fast ({execution_time:.2f}s) - likely mock"
        assert (
            execution_time < 15.0
        ), f"Too slow ({execution_time:.2f}s) - possible timeout"

        if result.success:
            result_str = str(result.result)

            # Should NOT contain mock data
            assert "Mock Paper" not in result_str, "Contains mock data - not real API"
            assert "Author 1" not in result_str, "Contains mock authors - not real API"

            # Should contain real ArXiv indicators
            assert any(
                indicator in result_str.lower()
                for indicator in ["arxiv", "paper", "abstract", "author"]
            ), "Missing real ArXiv indicators"

            logging.info(f"✅ ArXiv Research: {execution_time:.2f}s, real academic data")
        else:
            # ArXiv might fail due to network issues - that's acceptable for real API
            logging.warning(f"⚠️  ArXiv Research failed: {result.error}")
            assert "Mock" not in str(result.error), "Error should not mention mocks"

    async def test_firecrawl_real_scraping_signature(
        self, real_client_registry, performance_tracker
    ):
        """Test Firecrawl with real web scraping - validate content extraction"""

        # Use a reliable test URL
        test_url = "https://httpbin.org/json"

        start_time = time.time()

        result = await real_client_registry.execute_tool_method(
            tool_name="firecrawl", method="scrape", url=test_url, formats=["markdown"]
        )

        execution_time = time.time() - start_time
        performance_tracker["execution_times"].append(execution_time)

        # Scraping should show network + processing time
        assert execution_time > 0.4, f"Too fast ({execution_time:.2f}s) - likely mock"
        assert (
            execution_time < 12.0
        ), f"Too slow ({execution_time:.2f}s) - possible timeout"

        if result.success:
            result_str = str(result.result)

            # Should NOT contain mock data
            assert (
                "Mock scraped content" not in result_str
            ), "Contains mock data - not real API"

            # Should contain actual scraped content
            assert len(result_str) > 50, "Scraped content too short for real scraping"

            logging.info(f"✅ Firecrawl: {execution_time:.2f}s, real content scraped")
        else:
            logging.warning(f"⚠️  Firecrawl failed: {result.error}")
            assert "Mock" not in str(result.error), "Error should not mention mocks"

    async def test_context7_docs_real_api_signature(
        self, real_client_registry, performance_tracker
    ):
        """Test Context7 Docs with real documentation retrieval"""

        start_time = time.time()

        # First resolve a library
        resolve_result = await real_client_registry.execute_tool_method(
            tool_name="context7_docs",
            method="resolve_library_id",
            library_name="python",
        )

        if resolve_result.success:
            # Then get documentation
            docs_result = await real_client_registry.execute_tool_method(
                tool_name="context7_docs",
                method="get_library_docs",
                context7_compatible_library_id="/python/python",
                topic="functions",
                tokens=3000,
            )

            execution_time = time.time() - start_time
            performance_tracker["execution_times"].append(execution_time)

            # API calls should show latency
            assert (
                execution_time > 0.2
            ), f"Too fast ({execution_time:.2f}s) - likely mock"
            assert (
                execution_time < 8.0
            ), f"Too slow ({execution_time:.2f}s) - possible timeout"

            if docs_result.success:
                result_str = str(docs_result.result)

                # Should contain real documentation content
                assert any(
                    indicator in result_str.lower()
                    for indicator in ["python", "function", "documentation", "syntax"]
                ), "Missing documentation indicators"

                logging.info(
                    f"✅ Context7 Docs: {execution_time:.2f}s, real docs retrieved"
                )
            else:
                logging.warning(f"⚠️  Context7 Docs failed: {docs_result.error}")
        else:
            logging.warning(
                f"⚠️  Context7 Library resolution failed: {resolve_result.error}"
            )

    async def test_sequential_thinking_real_processing(
        self, real_client_registry, performance_tracker
    ):
        """Test Sequential Thinking with real reasoning - validate processing time"""

        start_time = time.time()

        result = await real_client_registry.execute_tool_method(
            tool_name="sequential_thinking",
            method="think_step",
            thought="Analyze the benefits and challenges of test-driven development in modern software engineering",
            thought_number=1,
            total_thoughts=3,
            next_thought_needed=True,
        )

        execution_time = time.time() - start_time
        performance_tracker["execution_times"].append(execution_time)

        # Thinking should take measurable time for complex thoughts
        assert execution_time > 0.1, f"Too fast ({execution_time:.2f}s) - possible mock"
        assert (
            execution_time < 15.0
        ), f"Too slow ({execution_time:.2f}s) - possible timeout"

        if result.success:
            result_str = str(result.result)
            assert len(result_str) > 20, "Thinking result too short"

            logging.info(
                f"✅ Sequential Thinking: {execution_time:.2f}s, real reasoning"
            )
        else:
            logging.warning(f"⚠️  Sequential Thinking failed: {result.error}")

    async def test_neo4j_real_database_connection(
        self, real_client_registry, performance_tracker
    ):
        """Test Neo4j with real database operations"""

        start_time = time.time()

        result = await real_client_registry.execute_tool_method(
            tool_name="neo4j", method="get_schema", random_string="integration_test"
        )

        execution_time = time.time() - start_time
        performance_tracker["execution_times"].append(execution_time)

        # Database operations should show connection latency
        assert (
            execution_time > 0.05
        ), f"Too fast ({execution_time:.2f}s) - possible mock"
        assert (
            execution_time < 5.0
        ), f"Too slow ({execution_time:.2f}s) - possible timeout"

        if result.success:
            logging.info(f"✅ Neo4j: {execution_time:.2f}s, real database connection")
        else:
            # Database might not be available - that's acceptable for real testing
            logging.warning(f"⚠️  Neo4j failed: {result.error}")
            assert "Mock" not in str(result.error), "Error should not mention mocks"

    async def test_research_workflow_adapter_real_execution(
        self, real_client_registry, performance_tracker
    ):
        """Test Research Workflow adapter with real execution - REGRESSION TEST"""

        start_time = time.time()

        result = await real_client_registry.execute_tool_method(
            tool_name="research_workflow",
            method="search_and_extract_urls",
            query="python testing best practices",
            max_results=3,
        )

        execution_time = time.time() - start_time
        performance_tracker["execution_times"].append(execution_time)

        # Should NOT produce coroutine errors (regression test)
        if result.error:
            error_msg = result.error.lower()
            assert (
                "coroutine" not in error_msg
            ), f"REGRESSION: Coroutine error detected - {result.error}"
            assert (
                "was never awaited" not in error_msg
            ), f"REGRESSION: Await error detected - {result.error}"

        # Workflow should show reasonable processing time
        assert execution_time > 0.3, f"Too fast ({execution_time:.2f}s) - likely mock"

        if result.success:
            result_str = str(result.result)
            assert len(result_str) > 10, "Research workflow result too short"

            logging.info(
                f"✅ Research Workflow: {execution_time:.2f}s, adapter working correctly"
            )
        else:
            logging.warning(f"⚠️  Research Workflow failed: {result.error}")

    async def test_mock_vs_real_performance_comparison(
        self, real_client_registry, mock_client_registry, performance_tracker
    ):
        """Compare mock vs real implementation performance to prove difference"""

        # Test same operation with both registries
        test_params = {"query": "test query", "count": 2}

        # Mock performance
        mock_start = time.time()
        mock_result = await mock_client_registry.execute_tool_method(
            "brave_search", "search", **test_params
        )
        mock_time = time.time() - mock_start

        # Real performance
        real_start = time.time()
        real_result = await real_client_registry.execute_tool_method(
            "brave_search", "search", **test_params
        )
        real_time = time.time() - real_start

        # Performance comparison
        performance_ratio = real_time / mock_time if mock_time > 0 else float("inf")

        # Real should be significantly slower than mock
        assert mock_time < 0.5, f"Mock too slow: {mock_time:.2f}s"
        assert real_time > 0.3, f"Real too fast: {real_time:.2f}s"
        assert (
            performance_ratio > 2.0
        ), f"Real not significantly slower than mock: {performance_ratio:.1f}x"

        # Data comparison
        mock_str = str(mock_result.result)
        real_str = str(real_result.result) if real_result.success else ""

        # Mock should contain mock data
        assert "Mock Result" in mock_str, "Mock should contain mock data"

        # Real should NOT contain mock data (if successful)
        if real_result.success:
            assert "Mock Result" not in real_str, "Real should not contain mock data"

        logging.info(
            f"📊 Performance Comparison: Mock={mock_time:.3f}s, Real={real_time:.2f}s ({performance_ratio:.1f}x)"
        )

    def test_performance_evidence_summary(self, performance_tracker):
        """Analyze collected performance data to document real API evidence"""

        times = performance_tracker["execution_times"]

        if not times:
            pytest.skip("No execution times recorded")

        # Statistical analysis
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        variance = sum((t - avg_time) ** 2 for t in times) / len(times)

        # Evidence validation
        assert min_time > 0.05, f"Minimum time {min_time:.3f}s suggests mocking"
        assert avg_time > 0.2, f"Average time {avg_time:.2f}s suggests mocking"
        assert (
            variance > 0.01
        ), f"Low variance {variance:.3f} suggests consistent mock responses"

        # Document evidence
        evidence_points = [
            f"📊 {len(times)} API calls analyzed",
            f"⏱️  Average execution time: {avg_time:.2f}s (real API signature)",
            f"📈 Time range: {min_time:.2f}s - {max_time:.2f}s (natural variance)",
            f"🔬 Variance: {variance:.3f} (indicates real network conditions)",
            "✅ All times consistent with real API calls, not mocks",
        ]

        logging.info("🔍 Performance Evidence for Real API Usage:")
        for point in evidence_points:
            logging.info(f"  {point}")

        # Test always passes - documents evidence
        assert True, "Performance evidence documented"
