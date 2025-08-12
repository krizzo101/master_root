"""
MCP Tool Registry for OAMAT System

This module provides comprehensive MCP tool registration, discovery, and management
capabilities for the OAMAT system. It enables automatic tool discovery, intelligent
routing, capability mapping, and dynamic tool orchestration.

Features:
- Automatic MCP tool discovery and registration
- Intelligent tool routing based on query analysis
- Capability mapping and tool classification
- Dynamic tool orchestration and chaining
- Performance monitoring and analytics
- Tool availability and health checking
"""

import asyncio
import logging

# MCP client imports with path resolution
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

# Ensure project root is in sys.path for MCP client imports
current_file = Path(__file__).resolve()
project_root = current_file.parents[4]  # Navigate to project root (agent_world)
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Debug path information

logger = logging.getLogger(__name__)
logger.debug(f"Current file: {current_file}")
logger.debug(f"Project root calculated: {project_root}")
logger.debug(f"Python path includes project root: {str(project_root) in sys.path}")


def import_mcp_clients():
    """Import MCP clients with proper error handling"""
    try:
        from src.shared.mcp.arxiv_mcp_client import ArxivMCPClient
        from src.shared.mcp.brave_mcp_search import BraveMCPSearch
        from src.shared.mcp.context7_mcp_client import Context7MCPClient
        from src.shared.mcp.firecrawl_mcp_client import FirecrawlMCPClient
        from src.shared.mcp.neo4j_mcp_client import Neo4jMCPClient
        from src.shared.mcp.sequential_thinking_mcp_client import (
            SequentialThinkingMCPClient,
        )

        return True, {
            "BraveMCPSearch": BraveMCPSearch,
            "ArxivMCPClient": ArxivMCPClient,
            "FirecrawlMCPClient": FirecrawlMCPClient,
            "Context7MCPClient": Context7MCPClient,
            "SequentialThinkingMCPClient": SequentialThinkingMCPClient,
            "Neo4jMCPClient": Neo4jMCPClient,
        }
    except ImportError as e:
        logging.warning(f"MCP clients import failed: {e}")
        return False, {}


# Try to import MCP clients
MCP_CLIENTS_AVAILABLE, MCP_CLIENTS = import_mcp_clients()

# Make clients available at module level for backward compatibility
if MCP_CLIENTS_AVAILABLE:
    BraveMCPSearch = MCP_CLIENTS["BraveMCPSearch"]
    ArxivMCPClient = MCP_CLIENTS["ArxivMCPClient"]
    FirecrawlMCPClient = MCP_CLIENTS["FirecrawlMCPClient"]
    Context7MCPClient = MCP_CLIENTS["Context7MCPClient"]
    SequentialThinkingMCPClient = MCP_CLIENTS["SequentialThinkingMCPClient"]
    Neo4jMCPClient = MCP_CLIENTS["Neo4jMCPClient"]
else:
    BraveMCPSearch = None
    ArxivMCPClient = None
    FirecrawlMCPClient = None
    Context7MCPClient = None
    SequentialThinkingMCPClient = None
    Neo4jMCPClient = None


class ToolCategory(Enum):
    """Categories for MCP tools"""

    WEB_SEARCH = "web_search"
    ACADEMIC_RESEARCH = "academic_research"
    WEB_SCRAPING = "web_scraping"
    TECHNICAL_DOCS = "technical_docs"
    REASONING = "reasoning"
    KNOWLEDGE_BASE = "knowledge_base"
    DATA_PROCESSING = "data_processing"
    CONTENT_GENERATION = "content_generation"


class ToolCapability(Enum):
    """Specific capabilities that tools can provide"""

    SEARCH = "search"
    SCRAPE = "scrape"
    EXTRACT = "extract"
    ANALYZE = "analyze"
    SYNTHESIZE = "synthesize"
    TRANSLATE = "translate"
    SUMMARIZE = "summarize"
    VALIDATE = "validate"
    MONITOR = "monitor"
    TRANSFORM = "transform"


@dataclass
class ToolMetadata:
    """Metadata for registered MCP tools"""

    name: str
    category: ToolCategory
    capabilities: list[ToolCapability]
    description: str
    client_class: str
    available_methods: list[str] = field(default_factory=list)
    rate_limits: dict[str, int] = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)
    cost_per_call: float = 0.0
    avg_response_time: float = 0.0
    success_rate: float = 1.0
    last_health_check: datetime | None = None
    health_status: str = "unknown"
    usage_count: int = 0
    error_count: int = 0


@dataclass
class ToolExecutionResult:
    """Result from tool execution with comprehensive metadata"""

    success: bool
    data: Any
    tool_name: str
    method_name: str
    execution_time: float
    timestamp: datetime
    error_message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    cost_incurred: float = 0.0
    tokens_used: int = 0


class MCPToolRegistry:
    """
    Comprehensive MCP tool registry with automatic discovery and intelligent routing
    """

    def __init__(
        self, config_path: str = "src/applications/oamat/config/mcp_config.yaml"
    ):
        import sys
        from datetime import datetime

        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(
            f"[{timestamp}] 🔍 DEBUG: MCPToolRegistry.__init__ starting with config_path: {config_path}"
        )
        sys.stdout.flush()

        self.logger = logging.getLogger(self.__class__.__name__)
        self.config_path = config_path

        # Registry storage
        self.registered_tools: dict[str, ToolMetadata] = {}
        self.tool_instances: dict[str, Any] = {}
        self.tool_chains: dict[str, list[str]] = {}

        # Performance tracking
        self.execution_history: list[ToolExecutionResult] = []
        self.performance_metrics: dict[str, dict] = {}

        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(
            f"[{timestamp}] 🔍 DEBUG: MCPToolRegistry basic setup complete, loading config..."
        )
        sys.stdout.flush()

        # Configuration
        self.config = self._load_config()

        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(
            f"[{timestamp}] ✅ DEBUG: Config loaded, setting up registry parameters..."
        )
        sys.stdout.flush()

        self.auto_discovery_enabled = True
        self.health_check_interval = timedelta(hours=1)

        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] 🔍 DEBUG: About to initialize registry...")
        sys.stdout.flush()

        # Initialize registry
        self._initialize_registry()

        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(
            f"[{timestamp}] 🎉 DEBUG: MCPToolRegistry initialization COMPLETELY finished!"
        )
        sys.stdout.flush()

    def _load_config(self) -> dict:
        """Load MCP configuration"""
        try:
            import yaml

            with open(self.config_path) as f:
                config = yaml.safe_load(f)
                return config
        except Exception as e:
            self.logger.warning(f"Failed to load MCP config: {e}")
            return {}

    def _initialize_registry(self):
        """Initialize the tool registry with automatic discovery"""
        import sys
        from datetime import datetime

        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] 🔍 DEBUG: _initialize_registry() starting...")
        sys.stdout.flush()

        self.logger.info("Initializing MCP tool registry")

        if self.auto_discovery_enabled:
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            print(
                f"[{timestamp}] 🔍 DEBUG: Auto-discovery enabled, calling _discover_and_register_tools()..."
            )
            sys.stdout.flush()

            self._discover_and_register_tools()

            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            print(f"[{timestamp}] ✅ DEBUG: Tool discovery completed")
            sys.stdout.flush()

        # Load predefined tool chains
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] 🔍 DEBUG: Loading tool chains...")
        sys.stdout.flush()

        self._load_tool_chains()

        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] ✅ DEBUG: Tool chains loaded")
        sys.stdout.flush()

        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(
            f"[{timestamp}] 🎉 DEBUG: Registry initialized with {len(self.registered_tools)} tools"
        )
        sys.stdout.flush()

        self.logger.info(
            f"Registry initialized with {len(self.registered_tools)} tools"
        )

    def _discover_and_register_tools(self):
        """Automatically discover and register available MCP tools"""
        import sys
        from datetime import datetime

        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] 🔍 DEBUG: _discover_and_register_tools() starting...")
        sys.stdout.flush()

        # Define tool discovery mappings
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] 🔍 DEBUG: Defining tool discovery mappings...")
        sys.stdout.flush()

        tool_discovery_map = {
            "brave.search": {
                "class": BraveMCPSearch if MCP_CLIENTS_AVAILABLE else None,
                "category": ToolCategory.WEB_SEARCH,
                "capabilities": [ToolCapability.SEARCH],
                "methods": [
                    "search",
                    "image_search",
                    "news_search",
                    "video_search",
                    "local_search",
                ],
                "description": "Comprehensive web search using Brave Search API",
            },
            "arxiv.research": {
                "class": ArxivMCPClient if MCP_CLIENTS_AVAILABLE else None,
                "category": ToolCategory.ACADEMIC_RESEARCH,
                "capabilities": [ToolCapability.SEARCH, ToolCapability.EXTRACT],
                "methods": [
                    "search_papers",
                    "download_paper",
                    "read_paper",
                    "list_papers",
                ],
                "description": "Academic paper search and retrieval from ArXiv",
            },
            "firecrawl.scraping": {
                "class": FirecrawlMCPClient if MCP_CLIENTS_AVAILABLE else None,
                "category": ToolCategory.WEB_SCRAPING,
                "capabilities": [ToolCapability.SCRAPE, ToolCapability.EXTRACT],
                "methods": ["scrape", "crawl", "check_crawl_status", "search"],
                "description": "Advanced web scraping and content extraction",
            },
            "context7.docs": {
                "class": Context7MCPClient if MCP_CLIENTS_AVAILABLE else None,
                "category": ToolCategory.TECHNICAL_DOCS,
                "capabilities": [ToolCapability.SEARCH, ToolCapability.EXTRACT],
                "methods": ["resolve_library_id", "get_library_docs"],
                "description": "Technical documentation access and retrieval",
            },
            "thinking.sequential": {
                "class": SequentialThinkingMCPClient if MCP_CLIENTS_AVAILABLE else None,
                "category": ToolCategory.REASONING,
                "capabilities": [ToolCapability.ANALYZE, ToolCapability.SYNTHESIZE],
                "methods": ["sequential_thinking", "think_step"],
                "description": "Structured reasoning and problem-solving",
            },
            "neo4j.database": {
                "class": Neo4jMCPClient if MCP_CLIENTS_AVAILABLE else None,
                "category": ToolCategory.KNOWLEDGE_BASE,
                "capabilities": [ToolCapability.SEARCH, ToolCapability.EXTRACT],
                "methods": [
                    "mcp_neo4j-mcp_read_neo4j_cypher",
                    "mcp_neo4j-mcp_get_neo4j_schema",
                ],
                "description": "Knowledge base queries via Neo4j",
            },
        }

        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(
            f"[{timestamp}] ✅ DEBUG: Tool discovery mappings created, MCP_CLIENTS_AVAILABLE: {MCP_CLIENTS_AVAILABLE}"
        )
        sys.stdout.flush()

        # Register discovered tools
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] 🔍 DEBUG: Starting tool registration loop...")
        sys.stdout.flush()

        for tool_name, tool_info in tool_discovery_map.items():
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            print(f"[{timestamp}] 🔍 DEBUG: Processing tool: {tool_name}")
            sys.stdout.flush()

            if tool_info["class"] is not None:
                timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                print(
                    f"[{timestamp}] 🔍 DEBUG: Registering tool {tool_name} with class {tool_info['class'].__name__}"
                )
                sys.stdout.flush()

                try:
                    self._register_tool(
                        name=tool_name,
                        category=tool_info["category"],
                        capabilities=tool_info["capabilities"],
                        description=tool_info["description"],
                        client_class=tool_info["class"].__name__,
                        available_methods=tool_info["methods"],
                    )

                    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                    print(
                        f"[{timestamp}] ✅ DEBUG: Successfully registered tool: {tool_name}"
                    )
                    sys.stdout.flush()

                except Exception as e:
                    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                    print(
                        f"[{timestamp}] ❌ DEBUG: Failed to register tool {tool_name}: {e}"
                    )
                    sys.stdout.flush()
            else:
                timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                print(
                    f"[{timestamp}] ⚠️ DEBUG: Tool {tool_name} not available - client class is None"
                )
                sys.stdout.flush()

                self.logger.warning(
                    f"Tool {tool_name} not available - client class not found"
                )

        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] 🎉 DEBUG: Tool registration loop completed successfully!")
        sys.stdout.flush()

    def _register_tool(
        self,
        name: str,
        category: ToolCategory,
        capabilities: list[ToolCapability],
        description: str,
        client_class: str,
        available_methods: list[str],
        **kwargs,
    ):
        """Register a tool in the registry"""

        # Get rate limits from config
        rate_limits = (
            self.config.get("mcp_clients", {}).get(name, {}).get("rate_limits", {})
        )

        tool_metadata = ToolMetadata(
            name=name,
            category=category,
            capabilities=capabilities,
            description=description,
            client_class=client_class,
            available_methods=available_methods,
            rate_limits=rate_limits,
            **kwargs,
        )

        self.registered_tools[name] = tool_metadata
        self.logger.info(f"Registered tool: {name} ({category.value})")

    def _load_tool_chains(self):
        """Load predefined tool chains from configuration"""
        tool_chains_config = self.config.get("tool_chains", {})

        for chain_name, chain_config in tool_chains_config.items():
            tools = chain_config.get("tools", [])
            tool_names = [tool["client"] for tool in tools]
            self.tool_chains[chain_name] = tool_names
            self.logger.info(
                f"Loaded tool chain: {chain_name} with {len(tool_names)} tools"
            )

    async def get_tool_instance(self, tool_name: str) -> Any | None:
        """Get or create tool instance"""
        if tool_name not in self.registered_tools:
            self.logger.error(f"Tool {tool_name} not registered")
            return None

        # Return cached instance if available
        if tool_name in self.tool_instances:
            return self.tool_instances[tool_name]

        # Create new instance
        try:
            tool_metadata = self.registered_tools[tool_name]

            # Import and instantiate the client class
            if tool_name == "brave.search" and MCP_CLIENTS_AVAILABLE:
                instance = BraveMCPSearch()
            elif tool_name == "arxiv.research" and MCP_CLIENTS_AVAILABLE:
                instance = ArxivMCPClient()
            elif tool_name == "firecrawl.scraping" and MCP_CLIENTS_AVAILABLE:
                instance = FirecrawlMCPClient()
            elif tool_name == "context7.docs" and MCP_CLIENTS_AVAILABLE:
                instance = Context7MCPClient()
            elif tool_name == "thinking.sequential" and MCP_CLIENTS_AVAILABLE:
                instance = SequentialThinkingMCPClient()
            elif tool_name == "neo4j.database" and MCP_CLIENTS_AVAILABLE:
                instance = Neo4jMCPClient()
            else:
                self.logger.error(f"Unknown tool or client not available: {tool_name}")
                return None

            self.tool_instances[tool_name] = instance
            self.logger.info(f"Created instance for tool: {tool_name}")
            return instance

        except Exception as e:
            self.logger.error(f"Failed to create instance for {tool_name}: {e}")
            return None

    def execute_tool(
        self, tool_name: str, method_name: str, arguments: dict[str, Any]
    ) -> ToolExecutionResult:
        """Synchronous wrapper for executing a tool method."""
        try:
            # Check if we're already in an event loop
            try:
                loop = asyncio.get_running_loop()
                # If we're in an event loop, create a task
                import concurrent.futures

                # Create a new event loop in a separate thread
                def run_in_thread():
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        return new_loop.run_until_complete(
                            self._execute_tool_async(tool_name, method_name, arguments)
                        )
                    finally:
                        new_loop.close()

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(run_in_thread)
                    return future.result()

            except RuntimeError:
                # No event loop running, use asyncio.run
                return asyncio.run(
                    self._execute_tool_async(tool_name, method_name, arguments)
                )
        except Exception as e:
            # Handle cases where an event loop is already running, etc.
            self.logger.error(
                f"Error running async tool '{tool_name}' from sync wrapper: {e}"
            )
            return ToolExecutionResult(
                success=False,
                data=None,
                tool_name=tool_name,
                method_name=method_name,
                execution_time=0.0,
                timestamp=datetime.now(),
                error_message=str(e),
            )

    async def _execute_tool_async(
        self, tool_name: str, method_name: str, arguments: dict[str, Any]
    ) -> ToolExecutionResult:
        """Execute a tool method with comprehensive tracking"""
        start_time = datetime.now()

        try:
            # Get tool instance
            tool_instance = await self.get_tool_instance(tool_name)
            if not tool_instance:
                return ToolExecutionResult(
                    success=False,
                    data=None,
                    tool_name=tool_name,
                    method_name=method_name,
                    execution_time=0.0,
                    timestamp=start_time,
                    error_message=f"Tool {tool_name} not available",
                )

            # Check if method exists
            if not hasattr(tool_instance, method_name):
                return ToolExecutionResult(
                    success=False,
                    data=None,
                    tool_name=tool_name,
                    method_name=method_name,
                    execution_time=0.0,
                    timestamp=start_time,
                    error_message=f"Method {method_name} not found on {tool_name}",
                )

            # Execute method
            method = getattr(tool_instance, method_name)

            # Handle both sync and async methods
            if asyncio.iscoroutinefunction(method):
                result = await method(**arguments)
            else:
                result = method(**arguments)

            execution_time = (datetime.now() - start_time).total_seconds()

            # Create successful result
            execution_result = ToolExecutionResult(
                success=True,
                data=result,
                tool_name=tool_name,
                method_name=method_name,
                execution_time=execution_time,
                timestamp=start_time,
            )

            # Update tool statistics
            self._update_tool_stats(tool_name, True, execution_time)

            # Store execution history
            self.execution_history.append(execution_result)

            return execution_result

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()

            execution_result = ToolExecutionResult(
                success=False,
                data=None,
                tool_name=tool_name,
                method_name=method_name,
                execution_time=execution_time,
                timestamp=start_time,
                error_message=str(e),
            )

            # Update tool statistics
            self._update_tool_stats(tool_name, False, execution_time)

            # Store execution history
            self.execution_history.append(execution_result)

            self.logger.error(f"Tool execution failed: {tool_name}.{method_name} - {e}")
            return execution_result

    def _update_tool_stats(self, tool_name: str, success: bool, execution_time: float):
        """Update tool performance statistics"""
        if tool_name not in self.registered_tools:
            return

        tool_metadata = self.registered_tools[tool_name]
        tool_metadata.usage_count += 1

        if success:
            # Update average response time
            if tool_metadata.avg_response_time == 0:
                tool_metadata.avg_response_time = execution_time
            else:
                tool_metadata.avg_response_time = (
                    tool_metadata.avg_response_time * (tool_metadata.usage_count - 1)
                    + execution_time
                ) / tool_metadata.usage_count
        else:
            tool_metadata.error_count += 1

        # Update success rate
        tool_metadata.success_rate = (
            tool_metadata.usage_count - tool_metadata.error_count
        ) / tool_metadata.usage_count

    async def intelligent_tool_selection(
        self, query: str, task_type: str = "general", max_tools: int = 3
    ) -> list[tuple[str, str, float]]:
        """
        Intelligently select tools based on query analysis

        Returns:
            List of tuples: (tool_name, recommended_method, confidence_score)
        """
        recommendations = []
        query_lower = query.lower()

        # Analyze query for different tool categories
        analysis_rules = {
            # Academic research indicators
            "academic": {
                "keywords": [
                    "paper",
                    "research",
                    "study",
                    "academic",
                    "arxiv",
                    "journal",
                    "publication",
                ],
                "tools": [("arxiv_research", "search_papers", 0.9)],
            },
            # Web search indicators
            "web_search": {
                "keywords": [
                    "search",
                    "find",
                    "look up",
                    "what is",
                    "information about",
                ],
                "tools": [("brave_search", "web_search", 0.8)],
            },
            # Technical documentation
            "technical_docs": {
                "keywords": [
                    "api",
                    "documentation",
                    "docs",
                    "library",
                    "framework",
                    "tutorial",
                    "guide",
                ],
                "tools": [("context7_docs", "resolve_library_id", 0.8)],
            },
            # Web scraping needs
            "scraping": {
                "keywords": [
                    "scrape",
                    "extract",
                    "crawl",
                    "website",
                    "web page",
                    "content from",
                ],
                "tools": [("firecrawl_scraping", "scrape", 0.9)],
            },
            # Complex reasoning
            "reasoning": {
                "keywords": [
                    "analyze",
                    "think",
                    "reason",
                    "solve",
                    "strategy",
                    "approach",
                    "how to",
                ],
                "tools": [("thinking.sequential", "sequential_thinking", 0.8)],
            },
            # Knowledge base queries
            "knowledge_base": {
                "keywords": ["database", "knowledge", "stored", "existing", "previous"],
                "tools": [("neo4j.database", "read_neo4j_cypher", 0.7)],
            },
        }

        # Score tools based on query analysis
        for category, rules in analysis_rules.items():
            keyword_matches = sum(
                1 for keyword in rules["keywords"] if keyword in query_lower
            )

            if keyword_matches > 0:
                for tool_name, method, base_confidence in rules["tools"]:
                    if tool_name in self.registered_tools:
                        # Adjust confidence based on keyword matches and tool performance
                        tool_metadata = self.registered_tools[tool_name]
                        performance_factor = tool_metadata.success_rate
                        keyword_factor = min(
                            keyword_matches / len(rules["keywords"]), 1.0
                        )

                        final_confidence = (
                            base_confidence
                            * performance_factor
                            * (0.5 + 0.5 * keyword_factor)
                        )

                        recommendations.append((tool_name, method, final_confidence))

        # Add general fallback tools if no specific matches
        if not recommendations:
            if "brave_search" in self.registered_tools:
                recommendations.append(("brave_search", "web_search", 0.6))

        # Sort by confidence and return top recommendations
        recommendations.sort(key=lambda x: x[2], reverse=True)
        return recommendations[:max_tools]

    async def execute_tool_chain(
        self, chain_name: str, initial_data: dict[str, Any]
    ) -> list[ToolExecutionResult]:
        """Execute a predefined tool chain"""
        if chain_name not in self.tool_chains:
            self.logger.error(f"Tool chain {chain_name} not found")
            return []

        chain_tools = self.tool_chains[chain_name]
        results = []
        current_data = initial_data.copy()

        self.logger.info(
            f"Executing tool chain: {chain_name} with {len(chain_tools)} tools"
        )

        for tool_name in chain_tools:
            # Determine method based on tool and data
            method_name = self._infer_method_for_tool(tool_name, current_data)

            # Execute tool
            result = await self.execute_tool(tool_name, method_name, current_data)
            results.append(result)

            # Use result for next tool if successful
            if result.success and result.data:
                current_data["previous_result"] = result.data

        return results

    def _infer_method_for_tool(self, tool_name: str, data: dict[str, Any]) -> str:
        """Infer the best method to use for a tool based on available data"""
        if tool_name not in self.registered_tools:
            return "unknown"

        tool_metadata = self.registered_tools[tool_name]
        available_methods = tool_metadata.available_methods

        # Simple heuristics for method selection
        if "query" in data:
            if "search" in available_methods:
                return "search"
            elif "web_search" in available_methods:
                return "web_search"
            elif "search_papers" in available_methods:
                return "search_papers"

        # Return first available method as fallback
        return available_methods[0] if available_methods else "unknown"

    async def health_check_tools(self) -> dict[str, bool]:
        """Perform health checks on all registered tools"""
        health_status = {}

        for tool_name in self.registered_tools.keys():
            try:
                # Simple health check - try to get instance
                instance = await self.get_tool_instance(tool_name)
                if instance:
                    health_status[tool_name] = True
                    self.registered_tools[tool_name].health_status = "healthy"
                else:
                    health_status[tool_name] = False
                    self.registered_tools[tool_name].health_status = "unhealthy"

                self.registered_tools[tool_name].last_health_check = datetime.now()

            except Exception as e:
                health_status[tool_name] = False
                self.registered_tools[tool_name].health_status = f"error: {e}"
                self.logger.warning(f"Health check failed for {tool_name}: {e}")

        return health_status

    def get_tool_analytics(self) -> dict[str, Any]:
        """Get comprehensive analytics about tool usage and performance"""
        analytics = {
            "total_tools": len(self.registered_tools),
            "total_executions": len(self.execution_history),
            "tools_by_category": {},
            "performance_summary": {},
            "recent_activity": [],
            "error_analysis": {},
        }

        # Tools by category
        for tool_name, metadata in self.registered_tools.items():
            category = metadata.category.value
            if category not in analytics["tools_by_category"]:
                analytics["tools_by_category"][category] = []
            analytics["tools_by_category"][category].append(tool_name)

        # Performance summary
        for tool_name, metadata in self.registered_tools.items():
            analytics["performance_summary"][tool_name] = {
                "usage_count": metadata.usage_count,
                "success_rate": metadata.success_rate,
                "avg_response_time": metadata.avg_response_time,
                "error_count": metadata.error_count,
                "health_status": metadata.health_status,
            }

        # Recent activity (last 10 executions)
        recent_executions = sorted(
            self.execution_history, key=lambda x: x.timestamp, reverse=True
        )[:10]
        analytics["recent_activity"] = [
            {
                "tool": exec.tool_name,
                "method": exec.method_name,
                "success": exec.success,
                "execution_time": exec.execution_time,
                "timestamp": exec.timestamp.isoformat(),
            }
            for exec in recent_executions
        ]

        # Error analysis
        failed_executions = [
            exec for exec in self.execution_history if not exec.success
        ]
        error_counts = {}
        for exec in failed_executions:
            tool = exec.tool_name
            if tool not in error_counts:
                error_counts[tool] = 0
            error_counts[tool] += 1

        analytics["error_analysis"] = error_counts

        return analytics

    def list_available_tools(self) -> dict[str, dict[str, Any]]:
        """List all available tools with their metadata"""
        return {
            name: {
                "category": metadata.category.value,
                "capabilities": [cap.value for cap in metadata.capabilities],
                "description": metadata.description,
                "methods": metadata.available_methods,
                "success_rate": metadata.success_rate,
                "avg_response_time": metadata.avg_response_time,
                "health_status": metadata.health_status,
            }
            for name, metadata in self.registered_tools.items()
        }

    def get_tools_by_capability(self, capability: ToolCapability) -> list[str]:
        """Get tools that have a specific capability"""
        return [
            name
            for name, metadata in self.registered_tools.items()
            if capability in metadata.capabilities
        ]

    async def cleanup(self):
        """Cleanup registry resources"""
        try:
            # Clear tool instances
            self.tool_instances.clear()

            # Clear execution history (keep recent for analytics)
            if len(self.execution_history) > 1000:
                self.execution_history = self.execution_history[-500:]

            self.logger.info("MCP tool registry cleaned up")

        except Exception as e:
            self.logger.error(f"Registry cleanup failed: {e}")


# Factory function for easy integration
def create_mcp_tool_registry(config_path: str = None) -> MCPToolRegistry:
    """
    Factory function to create MCP tool registry

    Args:
        config_path: Optional path to MCP configuration file

    Returns:
        MCPToolRegistry instance
    """
    import sys
    from datetime import datetime

    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] 🔍 DEBUG: create_mcp_tool_registry() called")
    sys.stdout.flush()

    if config_path is None:
        config_path = "src/applications/oamat/config/mcp_config.yaml"

    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(
        f"[{timestamp}] 🔍 DEBUG: About to create MCPToolRegistry with config_path: {config_path}"
    )
    sys.stdout.flush()

    try:
        registry = MCPToolRegistry(config_path=config_path)

        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] ✅ DEBUG: MCPToolRegistry created successfully")
        sys.stdout.flush()

        return registry
    except Exception as e:
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] ❌ DEBUG: MCPToolRegistry creation failed: {e}")
        sys.stdout.flush()
        raise


# Utility functions
def get_available_tool_categories() -> list[str]:
    """Get list of available tool categories"""
    return [category.value for category in ToolCategory]


def get_available_capabilities() -> list[str]:
    """Get list of available tool capabilities"""
    return [capability.value for capability in ToolCapability]
