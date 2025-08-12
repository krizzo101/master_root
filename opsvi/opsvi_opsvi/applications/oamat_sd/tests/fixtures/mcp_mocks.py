"""
Mock Framework for MCP Tools

Provides comprehensive mocks for all MCP tools used in Smart Decomposition system.
These mocks simulate real tool behavior for reliable testing without external dependencies.
"""

import time
from dataclasses import dataclass
from typing import Any
from unittest.mock import MagicMock


@dataclass
class ToolExecution:
    """Record of tool execution for testing validation"""

    timestamp: float
    method: str
    params: dict[str, Any]
    response: dict[str, Any]


class MCPToolMock:
    """Base class for MCP tool mocks with execution tracking"""

    def __init__(self, tool_name: str, responses: dict[str, Any]):
        self.tool_name = tool_name
        self.responses = responses
        self.call_history: list[ToolExecution] = []
        self.failure_rate = 0.0  # For simulating failures

    async def execute(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        """Mock tool execution with predefined responses"""
        timestamp = time.time()

        # Simulate failure if configured
        if self.failure_rate > 0 and time.time() % 1 < self.failure_rate:
            response = {"success": False, "error": f"Simulated failure for {method}"}
        elif method in self.responses:
            response = self.responses[method].copy()
            # Add dynamic elements to make responses more realistic
            if "timestamp" not in response:
                response["timestamp"] = timestamp
        else:
            response = {
                "success": False,
                "error": f"Mock method {method} not configured",
            }

        # Record execution
        execution = ToolExecution(timestamp, method, params, response)
        self.call_history.append(execution)

        return response

    def reset_history(self):
        """Reset call history for clean testing"""
        self.call_history.clear()

    def get_call_count(self, method: str | None = None) -> int:
        """Get number of calls for specific method or all methods"""
        if method is None:
            return len(self.call_history)
        return len([call for call in self.call_history if call.method == method])


class BraveSearchMock(MCPToolMock):
    """Mock for Brave Search tool with realistic web search responses"""

    def __init__(self):
        responses = {
            "web_search": {
                "success": True,
                "results": [
                    {
                        "title": "Python Web Frameworks Comparison 2024",
                        "url": "https://example.com/python-frameworks-2024",
                        "snippet": "Comprehensive comparison of Django, FastAPI, Flask, and other Python frameworks. Performance benchmarks and feature analysis.",
                        "ranking": 1,
                    },
                    {
                        "title": "FastAPI vs Django: Which to Choose?",
                        "url": "https://example.com/fastapi-vs-django",
                        "snippet": "In-depth analysis of FastAPI and Django for modern web development. Pros, cons, and use cases.",
                        "ranking": 2,
                    },
                    {
                        "title": "Flask Tutorial and Best Practices",
                        "url": "https://example.com/flask-tutorial",
                        "snippet": "Complete Flask tutorial with best practices for building scalable web applications.",
                        "ranking": 3,
                    },
                ],
                "query_info": {
                    "query": "Python web frameworks",
                    "total_results": 156789,
                    "search_time": 0.15,
                },
            },
            "news_search": {
                "success": True,
                "results": [
                    {
                        "title": "Python 3.12 Released with Performance Improvements",
                        "url": "https://example.com/python-3-12-news",
                        "snippet": "Python 3.12 brings significant performance improvements and new features...",
                        "published_date": "2024-01-15",
                        "source": "Python News",
                    }
                ],
            },
        }
        super().__init__("brave_search", responses)


class ArxivMock(MCPToolMock):
    """Mock for ArXiv research tool with academic paper responses"""

    def __init__(self):
        responses = {
            "search_papers": {
                "success": True,
                "papers": [
                    {
                        "title": "Performance Analysis of Modern Web Frameworks",
                        "authors": ["Smith, J.", "Doe, A.", "Johnson, M."],
                        "abstract": "This paper presents a comprehensive performance analysis of modern web frameworks including Django, FastAPI, and Flask. We benchmark throughput, latency, and resource usage across various workloads...",
                        "arxiv_id": "2024.0001",
                        "published_date": "2024-01-10",
                        "categories": ["cs.SE", "cs.PF"],
                        "pdf_url": "https://arxiv.org/pdf/2024.0001.pdf",
                    },
                    {
                        "title": "Scalability Patterns in Python Web Applications",
                        "authors": ["Davis, R.", "Wilson, K."],
                        "abstract": "We investigate scalability patterns and architectural decisions in Python web applications. Our study covers microservices, async programming, and deployment strategies...",
                        "arxiv_id": "2024.0002",
                        "published_date": "2024-01-05",
                        "categories": ["cs.DC", "cs.SE"],
                        "pdf_url": "https://arxiv.org/pdf/2024.0002.pdf",
                    },
                ],
                "query_info": {
                    "query": "web frameworks python",
                    "total_found": 47,
                    "search_time": 0.8,
                },
            },
            "download_paper": {
                "success": True,
                "paper_id": "2024.0001",
                "content": "Mock paper content for testing purposes...",
                "metadata": {"pages": 12, "format": "pdf", "size_mb": 2.3},
            },
        }
        super().__init__("arxiv_research", responses)


class FirecrawlMock(MCPToolMock):
    """Mock for Firecrawl web scraping tool"""

    def __init__(self):
        responses = {
            "scrape": {
                "success": True,
                "content": {
                    "title": "Django vs FastAPI: Complete Comparison",
                    "text": "Django and FastAPI are two of the most popular Python web frameworks. Django is a high-level framework that encourages rapid development, while FastAPI is a modern framework focused on API development with automatic documentation...",
                    "links": [
                        "https://djangoproject.com",
                        "https://fastapi.tiangolo.com",
                    ],
                    "images": [
                        "https://example.com/django-logo.png",
                        "https://example.com/fastapi-logo.png",
                    ],
                },
                "metadata": {
                    "url": "https://example.com/django-vs-fastapi",
                    "status_code": 200,
                    "content_type": "text/html",
                    "scrape_time": 1.2,
                },
            },
            "extract": {
                "success": True,
                "extracted_data": {
                    "frameworks": [
                        {"name": "Django", "type": "Full-stack", "performance": "Good"},
                        {
                            "name": "FastAPI",
                            "type": "API-focused",
                            "performance": "Excellent",
                        },
                        {
                            "name": "Flask",
                            "type": "Microframework",
                            "performance": "Good",
                        },
                    ]
                },
            },
        }
        super().__init__("firecrawl_scraping", responses)


class Context7Mock(MCPToolMock):
    """Mock for Context7 technical documentation tool"""

    def __init__(self):
        responses = {
            "get_docs": {
                "success": True,
                "documentation": {
                    "library": "fastapi",
                    "version": "0.104.1",
                    "sections": [
                        {
                            "title": "Getting Started",
                            "content": "FastAPI is a modern, fast (high-performance), web framework for building APIs with Python 3.7+ based on standard Python type hints...",
                            "examples": [
                                {
                                    "title": "Basic API",
                                    "code": 'from fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get("/")\ndef read_root():\n    return {"Hello": "World"}',
                                }
                            ],
                        }
                    ],
                },
                "metadata": {"last_updated": "2024-01-15", "completeness": 0.95},
            },
            "search_docs": {
                "success": True,
                "results": [
                    {
                        "title": "Authentication in FastAPI",
                        "content": "FastAPI provides several ways to handle authentication...",
                        "relevance": 0.92,
                    }
                ],
            },
        }
        super().__init__("context7_docs", responses)


class SequentialThinkingMock(MCPToolMock):
    """Mock for Sequential Thinking reasoning tool"""

    def __init__(self):
        responses = {
            "think": {
                "success": True,
                "reasoning_chain": [
                    {
                        "step": 1,
                        "thought": "To compare Python web frameworks, I need to consider performance, ease of use, community support, and specific use cases.",
                        "confidence": 0.9,
                    },
                    {
                        "step": 2,
                        "thought": "Django is best for full-stack applications with rapid development needs, while FastAPI excels at API development with automatic documentation.",
                        "confidence": 0.85,
                    },
                    {
                        "step": 3,
                        "thought": "Flask offers maximum flexibility but requires more setup. For a small team, FastAPI might be the best choice due to its modern features and excellent performance.",
                        "confidence": 0.8,
                    },
                ],
                "conclusion": "Based on the analysis, FastAPI is recommended for a small team due to its modern architecture, excellent performance, automatic documentation, and growing ecosystem.",
                "confidence": 0.85,
            }
        }
        super().__init__("sequential_thinking", responses)


class Neo4jMock(MCPToolMock):
    """Mock for Neo4j database tool"""

    def __init__(self):
        responses = {
            "query": {
                "success": True,
                "results": [
                    {
                        "framework": "FastAPI",
                        "relationships": [
                            "supports_async",
                            "has_automatic_docs",
                            "uses_pydantic",
                        ],
                        "properties": {
                            "performance_score": 9.2,
                            "learning_curve": "moderate",
                            "community_size": "growing",
                        },
                    }
                ],
                "query_time": 0.05,
            },
            "store": {"success": True, "nodes_created": 3, "relationships_created": 5},
        }
        super().__init__("neo4j_database", responses)


class MCPRegistryMock:
    """Mock for entire MCP tool registry with all operational tools"""

    def __init__(self):
        self.tools = {
            "brave_search": BraveSearchMock(),
            "arxiv_research": ArxivMock(),
            "firecrawl_scraping": FirecrawlMock(),
            "context7_docs": Context7Mock(),
            "sequential_thinking": SequentialThinkingMock(),
            "neo4j_database": Neo4jMock(),
        }
        self.registered_tools = {
            name: MagicMock(
                name=name,
                category="intelligence",
                description=f"Mock {name} tool",
                available_methods=list(tool.responses.keys()),
            )
            for name, tool in self.tools.items()
        }

    def get_tool(self, tool_name: str) -> MCPToolMock:
        """Get specific tool mock"""
        return self.tools.get(tool_name)

    def list_tools(self) -> list[str]:
        """List all available tool names"""
        return list(self.tools.keys())

    async def execute_tool(
        self, tool_name: str, method: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute tool method with parameters"""
        if tool_name not in self.tools:
            return {"success": False, "error": f"Tool {tool_name} not found"}

        tool = self.tools[tool_name]
        return await tool.execute(method, params)

    def reset_all_histories(self):
        """Reset call history for all tools"""
        for tool in self.tools.values():
            tool.reset_history()

    def get_total_calls(self) -> int:
        """Get total number of calls across all tools"""
        return sum(len(tool.call_history) for tool in self.tools.values())

    def set_failure_rate(self, tool_name: str, failure_rate: float):
        """Set failure rate for specific tool to test error handling"""
        if tool_name in self.tools:
            self.tools[tool_name].failure_rate = failure_rate
