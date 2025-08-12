"""
Execution Engine Module

Handles tool execution, parallel coordination, and result management.
Extracted from mcp_tool_registry.py for better modularity.
"""

import asyncio
import concurrent.futures
import logging
import time
from typing import Any

from src.applications.oamat_sd.src.config.config_manager import ConfigManager
from src.applications.oamat_sd.src.models.tool_models import (
    ParallelExecutionResult,
    ToolExecutionResult,
)


class ToolExecutionEngine:
    """Handles tool execution and parallel coordination"""

    def __init__(self, tool_manager, health_monitor):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.tool_manager = tool_manager
        self.health_monitor = health_monitor
        self.parallel_executor = concurrent.futures.ThreadPoolExecutor(max_workers=6)

        # Enhanced logging integration
        try:
            from src.applications.oamat_sd.src.sd_logging.logger_factory import (
                get_logger_factory,
            )

            self.enhanced_logger = get_logger_factory()
        except ImportError:
            self.enhanced_logger = None
            self.logger.warning(
                "Enhanced logging not available, using standard logging"
            )

    async def execute_tool_method(
        self, tool_name: str, method: str, **kwargs
    ) -> ToolExecutionResult:
        """Execute a specific method on a tool with enhanced functionality"""
        start_time = time.time()
        correlation_id = f"{tool_name}_{method}_{int(start_time * 1000)}"

        # Enhanced logging: Log tool execution start
        if self.enhanced_logger:
            self.enhanced_logger.log_tool_execution(
                tool_name=tool_name,
                method=method,
                parameters=kwargs,
                correlation_id=correlation_id,
                execution_stage="start",
            )

        self.logger.info(f"🔧 Executing {tool_name}.{method} with args: {kwargs}")

        try:
            # Check tool availability
            if not self.tool_manager.check_tool_availability(tool_name):
                error_msg = f"Tool {tool_name} is not available"
                self.logger.error(error_msg)
                result = ToolExecutionResult(
                    tool_name=tool_name,
                    method=method,
                    success=False,
                    error=error_msg,
                    execution_time=time.time() - start_time,
                )

                # Enhanced logging: Log failure
                if self.enhanced_logger:
                    self.enhanced_logger.log_tool_execution(
                        tool_name=tool_name,
                        method=method,
                        correlation_id=correlation_id,
                        execution_stage="error",
                        error_message=error_msg,
                    )

                return result

            # Get tool interface
            tool_interface = self.tool_manager.get_tool_interface(tool_name)

            # Execute the method based on tool type
            if tool_name == "brave_search":
                result_data = await self._execute_brave_search(
                    tool_interface, method, **kwargs
                )
            elif tool_name == "arxiv_research":
                result_data = await self._execute_arxiv_research(
                    tool_interface, method, **kwargs
                )
            elif tool_name == "firecrawl":
                result_data = await self._execute_firecrawl(
                    tool_interface, method, **kwargs
                )
            elif tool_name == "context7_docs":
                result_data = await self._execute_context7_docs(
                    tool_interface, method, **kwargs
                )
            elif tool_name == "sequential_thinking":
                result_data = await self._execute_sequential_thinking(
                    tool_interface, method, **kwargs
                )
            elif tool_name == "neo4j":
                result_data = await self._execute_neo4j(
                    tool_interface, method, **kwargs
                )
            elif tool_name == "research_workflow":
                result_data = await self._execute_research_workflow(
                    tool_interface, method, **kwargs
                )
            else:
                raise ValueError(f"Unknown tool: {tool_name}")

            execution_time = time.time() - start_time

            # Update tool metrics
            self.health_monitor.record_execution_success(tool_name, execution_time)

            result = ToolExecutionResult(
                tool_name=tool_name,
                method=method,
                success=True,
                result=result_data,
                execution_time=execution_time,
            )

            # Enhanced logging: Log success
            if self.enhanced_logger:
                self.enhanced_logger.log_tool_execution(
                    tool_name=tool_name,
                    method=method,
                    correlation_id=correlation_id,
                    execution_stage="success",
                    execution_time_ms=execution_time * 1000,
                    result_size=len(str(result_data)),
                )

            self.logger.info(
                f"✅ {tool_name}.{method} completed successfully in {execution_time:.2f}s"
            )
            return result

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)

            # Update tool metrics
            self.health_monitor.record_execution_failure(tool_name, error_msg)

            result = ToolExecutionResult(
                tool_name=tool_name,
                method=method,
                success=False,
                error=error_msg,
                execution_time=execution_time,
            )

            # Enhanced logging: Log failure
            if self.enhanced_logger:
                self.enhanced_logger.log_tool_execution(
                    tool_name=tool_name,
                    method=method,
                    correlation_id=correlation_id,
                    execution_stage="error",
                    error_message=error_msg,
                    execution_time_ms=execution_time * 1000,
                )

            self.logger.error(
                f"❌ {tool_name}.{method} failed after {execution_time:.2f}s: {error_msg}"
            )
            return result

    async def execute_tools_parallel(
        self, tool_requests: list[dict[str, Any]]
    ) -> ParallelExecutionResult:
        """Execute multiple tool methods in parallel"""
        start_time = time.time()

        self.logger.info(f"🚀 Starting parallel execution of {len(tool_requests)} tools")

        # Execute all tools in parallel
        tasks = [
            self.execute_tool_method(
                req["tool_name"], req["method"], **req.get("params", {})
            )
            for req in tool_requests
        ]

        # Execute tasks using as_completed instead of gather
        results = []
        for completed_task in asyncio.as_completed(tasks):
            try:
                result = await completed_task
                results.append(result)
            except Exception as e:
                results.append(e)

        # Process results and handle exceptions
        execution_results = []
        failed_executions = []

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Handle exceptions from gather
                failed_result = ToolExecutionResult(
                    tool_name=tool_requests[i]["tool_name"],
                    method=tool_requests[i]["method"],
                    success=False,
                    error=str(result),
                    execution_time=0.0,
                )
                execution_results.append(failed_result)
                failed_executions.append(failed_result)
            else:
                execution_results.append(result)
                if not result.success:
                    failed_executions.append(result)

        total_time = time.time() - start_time
        success_rate = (len(execution_results) - len(failed_executions)) / len(
            execution_results
        )

        parallel_result = ParallelExecutionResult(
            results=execution_results,
            total_time=total_time,
            success_rate=success_rate,
            failed_executions=failed_executions,
        )

        self.logger.info(
            f"✅ Parallel execution completed in {total_time:.2f}s. "
            f"Success rate: {success_rate:.2%} ({len(execution_results) - len(failed_executions)}/{len(execution_results)})"
        )

        return parallel_result

    # Tool-specific execution methods
    async def _execute_brave_search(
        self, interface, method: str, **kwargs
    ) -> dict[str, Any]:
        """Execute Brave Search operations"""
        if method == "search":
            return await interface.web_search(
                kwargs["query"]
                if "query" in kwargs
                else ConfigManager().tools.defaults.empty_query_value,
                **kwargs,
            )
        elif method == "news_search":
            return await interface.news_search(
                kwargs["query"]
                if "query" in kwargs
                else ConfigManager().tools.defaults.empty_query_value,
                **kwargs,
            )
        elif method == "video_search":
            return await interface.video_search(
                kwargs["query"]
                if "query" in kwargs
                else ConfigManager().tools.defaults.empty_query_value,
                **kwargs,
            )
        elif method == "image_search":
            return await interface.image_search(
                kwargs["query"]
                if "query" in kwargs
                else ConfigManager().tools.defaults.empty_query_value,
                **kwargs,
            )
        elif method == "local_search":
            return await interface.local_search(
                kwargs["query"]
                if "query" in kwargs
                else ConfigManager().tools.defaults.empty_query_value,
                **kwargs,
            )
        else:
            raise ValueError(f"Unknown Brave Search method: {method}")

    async def _execute_arxiv_research(
        self, interface, method: str, **kwargs
    ) -> dict[str, Any]:
        """Execute ArXiv Research operations"""
        if method == "search_papers":
            return await interface.search_papers(
                kwargs["query"]
                if "query" in kwargs
                else ConfigManager().tools.defaults.empty_query_value,
                **kwargs,
            )
        elif method == "download_paper":
            return await interface.download_paper(kwargs.get("paper_id", ""), **kwargs)
        elif method == "list_papers":
            return await interface.list_papers(**kwargs)
        elif method == "read_paper":
            return await interface.read_paper(kwargs.get("paper_id", ""), **kwargs)
        elif method == "search_and_ingest":
            return await self._arxiv_search_and_ingest(interface, **kwargs)
        else:
            raise ValueError(f"Unknown ArXiv Research method: {method}")

    async def _execute_firecrawl(
        self, interface, method: str, **kwargs
    ) -> dict[str, Any]:
        """Execute Firecrawl operations"""
        if method == "scrape":
            return await interface.scrape(kwargs.get("url", ""), **kwargs)
        elif method == "map":
            return await interface.map(kwargs.get("url", ""), **kwargs)
        elif method == "crawl":
            return await interface.crawl(kwargs.get("url", ""), **kwargs)
        elif method == "search":
            return await interface.search(
                kwargs["query"]
                if "query" in kwargs
                else ConfigManager().tools.defaults.empty_query_value,
                **kwargs,
            )
        elif method == "extract":
            return await interface.extract(kwargs.get("urls", []), **kwargs)
        elif method == "generate_llmstxt":
            return await interface.generate_llmstxt(kwargs.get("url", ""), **kwargs)
        else:
            raise ValueError(f"Unknown Firecrawl method: {method}")

    async def _execute_context7_docs(
        self, interface, method: str, **kwargs
    ) -> dict[str, Any]:
        """Execute Context7 Docs operations"""
        if method == "resolve_library_id":
            return await interface.resolve_library_id(
                kwargs.get("library_name", ""), **kwargs
            )
        elif method == "get_library_docs":
            return await interface.get_library_docs(
                kwargs.get("library_id", ""), **kwargs
            )
        else:
            raise ValueError(f"Unknown Context7 Docs method: {method}")

    async def _execute_sequential_thinking(
        self, interface, method: str, **kwargs
    ) -> dict[str, Any]:
        """Execute Sequential Thinking operations"""
        if method == "think_step" or method == "solve_problem":
            return await interface.think(kwargs.get("problem", ""), **kwargs)
        elif method == "get_session_summary":
            return await interface.get_session_summary(**kwargs)
        else:
            raise ValueError(f"Unknown Sequential Thinking method: {method}")

    async def _execute_neo4j(self, interface, method: str, **kwargs) -> dict[str, Any]:
        """Execute Neo4j operations"""
        if method == "get_schema":
            return await interface.get_schema(**kwargs)
        elif method == "read_cypher":
            return await interface.read_cypher(
                kwargs["query"]
                if "query" in kwargs
                else ConfigManager().tools.defaults.empty_query_value,
                **kwargs,
            )
        elif method == "write_cypher":
            return await interface.write_cypher(
                kwargs["query"]
                if "query" in kwargs
                else ConfigManager().tools.defaults.empty_query_value,
                **kwargs,
            )
        else:
            raise ValueError(f"Unknown Neo4j method: {method}")

    async def _execute_research_workflow(
        self, interface, method: str, **kwargs
    ) -> dict[str, Any]:
        """Execute Research Workflow operations"""
        if method == "search_and_present":
            return await self._research_search_and_present(interface, **kwargs)
        elif method == "scrape_selected":
            return await self._research_scrape_selected(interface, **kwargs)
        elif method == "complete_research":
            return await self._research_complete_workflow(interface, **kwargs)
        elif method == "search_and_extract_urls":
            urls = await interface.search_and_extract_urls(
                kwargs["query"]
                if "query" in kwargs
                else ConfigManager().tools.defaults.empty_query_value,
                kwargs["max_results"]
                if "max_results" in kwargs
                else ConfigManager().tools.defaults.max_results,
            )
            return {
                "urls": [
                    {"url": u.url, "title": u.title, "relevance": u.relevance_score}
                    for u in urls
                ]
            }
        elif method == "present_urls_for_selection":
            urls = kwargs.get("urls", [])
            return {
                "presentation": interface.present_urls_for_selection(urls, len(urls))
            }
        else:
            raise ValueError(f"Unknown Research Workflow method: {method}")

    # Helper methods for complex operations
    async def _arxiv_search_and_ingest(self, interface, **kwargs) -> dict[str, Any]:
        """Search ArXiv papers and ingest them for context"""
        query = (
            kwargs["query"]
            if "query" in kwargs
            else ConfigManager().tools.defaults.empty_query_value
        )
        max_papers = kwargs.get("max_papers", 5)

        if not query:
            raise ValueError("query is required for ArXiv search and ingest")

        # Search for papers
        search_result = await interface.search_papers(query, max_results=max_papers)

        if not search_result.get("papers"):
            return {
                "success": False,
                "error": f"No papers found for query: '{query}'",
                "query": query,
                "papers_found": 0,
            }

        # Real implementation - download and ingest papers
        papers_info = []
        downloaded_count = 0
        ingested_count = 0

        for paper in search_result["papers"][:max_papers]:
            paper_id = paper.get("id")
            paper_info = {
                "id": paper_id,
                "title": paper.get("title"),
                "authors": paper.get("authors", []),
                "abstract": paper.get("abstract", ""),
                "downloaded": False,
                "ingested": False,
            }

            # Attempt to download paper
            try:
                download_result = await arxiv_interface.download_paper(paper_id)
                if download_result.get("success"):
                    paper_info["downloaded"] = True
                    downloaded_count += 1

                    # Attempt to read/ingest paper content
                    read_result = await arxiv_interface.read_paper(paper_id)
                    if read_result.get("success"):
                        paper_info["ingested"] = True
                        paper_info["content"] = read_result.get("content", "")
                        ingested_count += 1
            except Exception as e:
                paper_info["error"] = str(e)

            papers_info.append(paper_info)

        return {
            "success": True,
            "query": query,
            "papers_found": len(search_result["papers"]),
            "papers_downloaded": downloaded_count,
            "papers_ingested": ingested_count,
            "papers": papers_info,
            "total_content_chars": 0,
            "ingestion_summary": f"Found {len(papers_info)} papers for context",
        }

    async def _research_search_and_present(self, interface, **kwargs) -> dict[str, Any]:
        """Search multiple sources and present URLs for agent selection"""
        query = (
            kwargs["query"]
            if "query" in kwargs
            else ConfigManager().tools.defaults.empty_query_value
        )
        max_results = (
            kwargs["max_results"]
            if "max_results" in kwargs
            else ConfigManager().tools.defaults.max_results
        )

        if not query:
            raise ValueError("query is required for research search")

        try:
            urls = await interface.search_and_extract_urls(query, max_results)

            if not urls:
                return {
                    "success": False,
                    "error": f"No URLs found for query: '{query}'",
                    "query": query,
                    "urls_found": 0,
                }

            presentation = interface.present_urls_for_selection(urls, max_results)

            return {
                "success": True,
                "query": query,
                "urls_found": len(urls),
                "presentation": presentation,
                "urls": [
                    {"url": u.url, "title": u.title, "relevance": u.relevance_score}
                    for u in urls
                ],
            }

        except Exception as e:
            return {"success": False, "error": str(e), "query": query, "urls_found": 0}

    async def _research_scrape_selected(self, interface, **kwargs) -> dict[str, Any]:
        """Scrape agent-selected URLs and compile research report"""
        query = (
            kwargs["query"]
            if "query" in kwargs
            else ConfigManager().tools.defaults.empty_query_value
        )
        selected_indices = kwargs.get("selected_indices", [])
        max_results = (
            kwargs["max_results"]
            if "max_results" in kwargs
            else ConfigManager().tools.defaults.max_results
        )

        if not query:
            raise ValueError("query is required for research scraping")

        if not selected_indices:
            raise ValueError("selected_indices must be provided")

        try:
            urls = await interface.search_and_extract_urls(query, max_results)

            if not urls:
                return {
                    "success": False,
                    "error": f"No URLs found for query: '{query}'",
                    "query": query,
                }

            results = await interface.scrape_selected_urls(urls, selected_indices)
            report = interface.compile_research_report(
                query, urls, selected_indices, results
            )
            formatted_report = interface.format_research_report(report)

            return {
                "success": True,
                "query": query,
                "urls_scraped": len(selected_indices),
                "successful_scrapes": len([r for r in results if r.success]),
                "report": formatted_report,
                "raw_results": results,
            }

        except Exception as e:
            return {"success": False, "error": str(e), "query": query}

    async def _research_complete_workflow(self, interface, **kwargs) -> dict[str, Any]:
        """Complete auto-workflow with intelligent URL selection and scraping"""
        query = (
            kwargs["query"]
            if "query" in kwargs
            else ConfigManager().tools.defaults.empty_query_value
        )
        max_results = (
            kwargs["max_results"]
            if "max_results" in kwargs
            else ConfigManager().tools.defaults.max_results
        )
        auto_select_top = kwargs.get("auto_select_top", 3)

        if not query:
            raise ValueError("query is required for complete research workflow")

        try:
            urls = await interface.search_and_extract_urls(query, max_results)

            if not urls:
                return {
                    "success": False,
                    "error": f"No URLs found for query: '{query}'",
                    "query": query,
                    "urls_found": 0,
                }

            selected_indices = list(range(1, min(auto_select_top + 1, len(urls) + 1)))
            results = await interface.scrape_selected_urls(urls, selected_indices)
            report = interface.compile_research_report(
                query, urls, selected_indices, results
            )
            formatted_report = interface.format_research_report(report)

            return {
                "success": True,
                "query": query,
                "urls_found": len(urls),
                "urls_scraped": len(selected_indices),
                "successful_scrapes": len([r for r in results if r.success]),
                "auto_selected_indices": selected_indices,
                "report": formatted_report,
            }

        except Exception as e:
            return {"success": False, "error": str(e), "query": query, "urls_found": 0}
