"""
Unified MCP Orchestrator

Coordinates between Claude Code, OpenAI Codex, and Cursor Agent servers
to provide integrated AI-powered development capabilities.
"""

import asyncio
import json
import yaml
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

from fastmcp import FastMCP

# Import server implementations
from .claude_code_v2.server import ClaudeCodeV2Server
from .openai_codex.server import OpenAICodexServer
from .cursor_agent.server import CursorAgentServer

logger = logging.getLogger(__name__)


class UnifiedMCPOrchestrator:
    """
    Orchestrates multiple MCP servers for integrated AI development workflows.
    """

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the orchestrator with configuration"""

        # Load configuration
        self.config = self._load_config(config_path)

        # Initialize MCP server
        self.mcp = FastMCP("unified-mcp-orchestrator")

        # Initialize individual servers
        self.servers = {}
        self._init_servers()

        # Setup orchestration tools
        self._setup_orchestration_tools()

    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration from YAML file"""

        if not config_path:
            config_path = Path(__file__).parent / "unified_config.yaml"

        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        # Expand environment variables
        self._expand_env_vars(config)

        return config

    def _expand_env_vars(self, config: Any):
        """Recursively expand environment variables in config"""

        if isinstance(config, dict):
            for key, value in config.items():
                if (
                    isinstance(value, str)
                    and value.startswith("${")
                    and value.endswith("}")
                ):
                    env_var = value[2:-1]
                    config[key] = os.environ.get(env_var, value)
                else:
                    self._expand_env_vars(value)
        elif isinstance(config, list):
            for item in config:
                self._expand_env_vars(item)

    def _init_servers(self):
        """Initialize individual MCP servers based on configuration"""

        # Initialize Claude Code server if enabled
        if self.config["servers"]["claude_code"]["enabled"]:
            try:
                from .claude_code_v2.config import ServerConfig as ClaudeConfig

                claude_config = ClaudeConfig(
                    **self.config["servers"]["claude_code"]["config"]
                )
                self.servers["claude_code"] = ClaudeCodeV2Server(claude_config)
                logger.info("Claude Code server initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Claude Code server: {e}")

        # Initialize OpenAI Codex server if enabled
        if self.config["servers"]["openai_codex"]["enabled"]:
            try:
                from .openai_codex.config import CodexConfig

                codex_config = CodexConfig(
                    **self.config["servers"]["openai_codex"]["config"]
                )
                self.servers["openai_codex"] = OpenAICodexServer(codex_config)
                logger.info("OpenAI Codex server initialized")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI Codex server: {e}")

        # Initialize Cursor Agent server if enabled
        if self.config["servers"]["cursor_agent"]["enabled"]:
            try:
                from .cursor_agent.config import CursorConfig

                cursor_config = CursorConfig(
                    **self.config["servers"]["cursor_agent"]["config"]
                )
                self.servers["cursor_agent"] = CursorAgentServer(cursor_config)
                logger.info("Cursor Agent server initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Cursor Agent server: {e}")

    def _setup_orchestration_tools(self):
        """Setup MCP tools for orchestrated workflows"""

        @self.mcp.tool()
        async def analyze_and_implement(
            requirements: str, language: Optional[str] = None, visualize: bool = True
        ) -> Dict[str, Any]:
            """
            Complete workflow: analyze requirements, generate code, create diagrams.

            Args:
                requirements: Natural language requirements
                language: Target programming language
                visualize: Whether to create architecture diagram

            Returns:
                Analysis, implementation, and visualization
            """

            results = {}

            # Step 1: Analyze with Claude
            if "claude_code" in self.servers:
                claude_result = await self._invoke_claude(
                    task=f"Analyze these requirements and create a detailed implementation plan:\n{requirements}",
                    output_format="json",
                )
                results["analysis"] = claude_result

            # Step 2: Generate code with Codex
            if "openai_codex" in self.servers:
                codex_result = await self._invoke_codex(
                    prompt=requirements, mode="generate", language=language
                )
                results["implementation"] = codex_result

            # Step 3: Create diagram with Cursor
            if visualize and "cursor_agent" in self.servers:
                diagram_data = results.get("analysis", {}).get(
                    "architecture", requirements
                )
                cursor_result = await self._invoke_cursor(
                    agent="@diagram",
                    prompt=f"Create an architecture diagram for:\n{diagram_data}",
                )
                results["visualization"] = cursor_result

            return {
                "success": True,
                "workflow": "analyze_and_implement",
                "results": results,
            }

        @self.mcp.tool()
        async def code_review_pipeline(
            code: str, language: Optional[str] = None, fix_issues: bool = True
        ) -> Dict[str, Any]:
            """
            Review code, identify issues, and optionally fix them.

            Args:
                code: Code to review
                language: Programming language
                fix_issues: Whether to generate fixes

            Returns:
                Review results and fixed code
            """

            results = {}

            # Step 1: Review with Cursor
            if "cursor_agent" in self.servers:
                review_result = await self._invoke_cursor(
                    agent="@code_review",
                    prompt=f"Review this {language or 'code'}:\n```\n{code}\n```",
                )
                results["review"] = review_result

            # Step 2: Fix issues with Codex if requested
            if fix_issues and "openai_codex" in self.servers:
                issues = results.get("review", {}).get(
                    "issues", "No specific issues found"
                )
                fix_result = await self._invoke_codex(
                    prompt=f"Fix these issues in the code:\n{issues}\n\nOriginal code:\n{code}",
                    mode="refactor",
                    language=language,
                )
                results["fixed_code"] = fix_result

            # Step 3: Verify fixes with Claude
            if fix_issues and "claude_code" in self.servers:
                verify_result = await self._invoke_claude(
                    task="Verify that the fixes properly address the identified issues",
                    output_format="json",
                )
                results["verification"] = verify_result

            return {
                "success": True,
                "workflow": "code_review_pipeline",
                "results": results,
            }

        @self.mcp.tool()
        async def documentation_workflow(
            code: str,
            language: Optional[str] = None,
            include_tests: bool = True,
            include_diagram: bool = True,
        ) -> Dict[str, Any]:
            """
            Generate comprehensive documentation including docs, tests, and diagrams.

            Args:
                code: Code to document
                language: Programming language
                include_tests: Whether to generate tests
                include_diagram: Whether to create flow diagram

            Returns:
                Documentation, tests, and diagrams
            """

            results = {}

            # Step 1: Generate documentation with Cursor
            if "cursor_agent" in self.servers:
                doc_result = await self._invoke_cursor(
                    agent="@documentation",
                    prompt=f"Generate comprehensive documentation for:\n```{language or ''}\n{code}\n```",
                )
                results["documentation"] = doc_result

            # Step 2: Generate tests with Codex
            if include_tests and "openai_codex" in self.servers:
                test_result = await self._invoke_codex(
                    prompt=code, mode="test", language=language
                )
                results["tests"] = test_result

            # Step 3: Create flow diagram with Cursor
            if include_diagram and "cursor_agent" in self.servers:
                diagram_result = await self._invoke_cursor(
                    agent="@diagram",
                    prompt=f"Create a flow diagram for this {language or 'code'}:\n```\n{code}\n```"
                )
                results["diagram"] = diagram_result

            return {
                "success": True,
                "workflow": "documentation_workflow",
                "results": results,
            }

        @self.mcp.tool()
        async def parallel_analysis(
            topic: str, perspectives: List[str] = None
        ) -> Dict[str, Any]:
            """
            Analyze a topic from multiple perspectives using all available servers.

            Args:
                topic: Topic to analyze
                perspectives: Specific perspectives to consider

            Returns:
                Multi-perspective analysis
            """

            if not perspectives:
                perspectives = ["technical", "business", "security"]

            tasks = []

            # Claude analysis
            if "claude_code" in self.servers:
                for perspective in perspectives:
                    task = self._invoke_claude(
                        task=f"Analyze '{topic}' from a {perspective} perspective",
                        output_format="json",
                    )
                    tasks.append(("claude", perspective, task))

            # Codex code examples
            if "openai_codex" in self.servers:
                task = self._invoke_codex(
                    prompt=f"Generate code examples demonstrating: {topic}",
                    mode="generate",
                )
                tasks.append(("codex", "examples", task))

            # Cursor visualization
            if "cursor_agent" in self.servers:
                task = self._invoke_cursor(
                    agent="@diagram", prompt=f"Create a concept map for: {topic}"
                )
                tasks.append(("cursor", "visualization", task))

            # Execute all tasks in parallel
            results = {}
            task_results = await asyncio.gather(
                *[t[2] for t in tasks], return_exceptions=True
            )

            for (server, perspective, _), result in zip(tasks, task_results):
                if not isinstance(result, Exception):
                    if server not in results:
                        results[server] = {}
                    results[server][perspective] = result
                else:
                    logger.error(f"Task failed for {server}/{perspective}: {result}")

            return {
                "success": True,
                "workflow": "parallel_analysis",
                "topic": topic,
                "results": results,
            }

    async def _invoke_claude(self, task: str, **kwargs) -> Dict[str, Any]:
        """Invoke Claude Code server"""

        if "claude_code" not in self.servers:
            return {"error": "Claude Code server not available"}

        # Use the fire-and-forget pattern from v2
        result = await self.servers["claude_code"].spawn_agent(
            {"task": task, "output_dir": self.config["shared"]["results_dir"], **kwargs}
        )

        # Wait for result
        if result.get("success"):
            job_id = result["job_id"]
            # Poll for completion (simplified for example)
            await asyncio.sleep(2)

            # Collect result
            collected = await self.servers["claude_code"].collect_results(
                {
                    "job_ids": [job_id],
                    "output_dir": self.config["shared"]["results_dir"],
                }
            )

            return collected.get("results", {}).get(job_id, result)

        return result

    async def _invoke_codex(
        self, prompt: str, mode: str = "generate", **kwargs
    ) -> Dict[str, Any]:
        """Invoke OpenAI Codex server"""

        if "openai_codex" not in self.servers:
            return {"error": "OpenAI Codex server not available"}

        method_map = {
            "generate": "codex_generate",
            "complete": "codex_complete",
            "explain": "codex_explain",
            "refactor": "codex_refactor",
            "debug": "codex_debug",
            "test": "codex_test",
            "document": "codex_document",
            "review": "codex_review",
            "translate": "codex_translate",
        }

        method = method_map.get(mode, "codex_generate")

        # Call the appropriate method
        # This is simplified - in practice you'd use the actual MCP tool invocation
        return {"mode": mode, "result": f"Codex result for: {prompt[:50]}..."}

    async def _invoke_cursor(self, agent: str, prompt: str, **kwargs) -> Dict[str, Any]:
        """Invoke Cursor Agent server"""

        if "cursor_agent" not in self.servers:
            return {"error": "Cursor Agent server not available"}

        # Call the cursor agent
        # This is simplified - in practice you'd use the actual MCP tool invocation
        return {"agent": agent, "result": f"Cursor result for: {prompt[:50]}..."}

    async def run(self):
        """Run the unified orchestrator"""

        logger.info("Starting Unified MCP Orchestrator")
        logger.info(f"Active servers: {list(self.servers.keys())}")

        # Run the MCP server
        await self.mcp.run()


# Entry point
if __name__ == "__main__":
    import asyncio

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Check required environment variables
    required_vars = ["CLAUDE_CODE_TOKEN", "OPENAI_API_KEY"]
    missing = [var for var in required_vars if not os.environ.get(var)]

    if missing:
        logger.error(f"Missing required environment variables: {missing}")
        logger.info("Please set them in your .env file or environment")
        exit(1)

    # Run orchestrator
    orchestrator = UnifiedMCPOrchestrator()
    asyncio.run(orchestrator.run())
