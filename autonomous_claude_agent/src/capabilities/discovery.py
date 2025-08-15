"""
Capability Discovery - Finds and analyzes available tools and capabilities
"""

import asyncio
import importlib
import inspect
import json
import os
import subprocess
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class Capability:
    """Represents a discovered capability"""

    name: str
    type: str  # 'mcp_tool', 'python_module', 'cli_tool', 'api', 'library'
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    requirements: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    cost: float = 0.0  # Estimated resource cost
    success_rate: float = 1.0
    last_used: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    available: bool = True


class CapabilityDiscovery:
    """Discovers and catalogs available capabilities"""

    def __init__(self):
        self.discovered_capabilities = {}
        self.discovery_cache = {}
        self.unavailable_capabilities = set()

    async def discover_initial_capabilities(self) -> Dict[str, Capability]:
        """Discover all initially available capabilities"""

        logger.info("Starting capability discovery...")

        capabilities = {}

        # Discover different types of capabilities in parallel
        tasks = [
            self.discover_mcp_tools(),
            self.discover_python_modules(),
            self.discover_cli_tools(),
            self.discover_system_capabilities(),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Discovery failed: {result}")
            else:
                capabilities.update(result)

        self.discovered_capabilities = capabilities
        logger.info(f"Discovered {len(capabilities)} capabilities")

        return capabilities

    async def discover_mcp_tools(self) -> Dict[str, Capability]:
        """Discover available MCP tools"""

        capabilities = {}

        try:
            # Check for MCP configuration
            mcp_config_path = Path.home() / ".mcp" / "mcp.json"

            if mcp_config_path.exists():
                with open(mcp_config_path) as f:
                    mcp_config = json.load(f)

                for server_name, server_config in mcp_config.get("servers", {}).items():
                    capability = Capability(
                        name=f"mcp_{server_name}",
                        type="mcp_tool",
                        description=f"MCP server: {server_name}",
                        metadata={"server_config": server_config},
                        available=True,
                    )
                    capabilities[capability.name] = capability

            # Check for known MCP tools
            known_mcp_tools = [
                ("claude-code", "Claude Code execution via MCP"),
                ("firecrawl", "Web scraping and search"),
                ("time", "Time and date utilities"),
                ("git", "Git version control"),
                ("shell_exec", "Shell command execution"),
            ]

            for tool_name, description in known_mcp_tools:
                if self._check_mcp_tool_available(tool_name):
                    capability = Capability(
                        name=f"mcp_{tool_name}",
                        type="mcp_tool",
                        description=description,
                        available=True,
                    )
                    capabilities[capability.name] = capability

        except Exception as e:
            logger.error(f"Failed to discover MCP tools: {e}")

        return capabilities

    async def discover_python_modules(self) -> Dict[str, Capability]:
        """Discover available Python modules"""

        capabilities = {}

        # Check for common useful modules
        modules_to_check = [
            ("numpy", "Numerical computing"),
            ("pandas", "Data manipulation"),
            ("requests", "HTTP requests"),
            ("beautifulsoup4", "HTML parsing"),
            ("pytest", "Testing framework"),
            ("asyncio", "Asynchronous programming"),
            ("sqlite3", "Database operations"),
            ("json", "JSON handling"),
            ("re", "Regular expressions"),
            ("pathlib", "Path operations"),
        ]

        for module_name, description in modules_to_check:
            try:
                module = importlib.import_module(module_name.split(".")[0])

                capability = Capability(
                    name=f"python_{module_name}",
                    type="python_module",
                    description=description,
                    metadata={"version": getattr(module, "__version__", "unknown")},
                    available=True,
                )

                # Extract functions if possible
                try:
                    functions = [
                        name
                        for name in dir(module)
                        if not name.startswith("_") and callable(getattr(module, name))
                    ]
                    capability.metadata["functions"] = functions[:20]  # Limit to 20
                except:
                    pass

                capabilities[capability.name] = capability

            except ImportError:
                logger.debug(f"Module {module_name} not available")
                self.unavailable_capabilities.add(f"python_{module_name}")

        return capabilities

    async def discover_cli_tools(self) -> Dict[str, Capability]:
        """Discover available CLI tools"""

        capabilities = {}

        # Common CLI tools to check
        cli_tools = [
            ("git", "Version control"),
            ("python", "Python interpreter"),
            ("pip", "Python package manager"),
            ("npm", "Node package manager"),
            ("docker", "Container management"),
            ("curl", "HTTP client"),
            ("wget", "File downloader"),
            ("jq", "JSON processor"),
            ("grep", "Text search"),
            ("sed", "Stream editor"),
            ("awk", "Text processing"),
            ("make", "Build automation"),
        ]

        for tool_name, description in cli_tools:
            if await self._check_cli_tool(tool_name):
                capability = Capability(
                    name=f"cli_{tool_name}",
                    type="cli_tool",
                    description=description,
                    available=True,
                )

                # Get version if possible
                try:
                    version = await self._get_tool_version(tool_name)
                    capability.metadata["version"] = version
                except:
                    pass

                capabilities[capability.name] = capability

        return capabilities

    async def discover_system_capabilities(self) -> Dict[str, Capability]:
        """Discover system-level capabilities"""

        capabilities = {}

        # File system operations
        capabilities["sys_filesystem"] = Capability(
            name="sys_filesystem",
            type="system",
            description="File system operations (read, write, delete)",
            available=True,
        )

        # Network capabilities
        capabilities["sys_network"] = Capability(
            name="sys_network",
            type="system",
            description="Network operations (HTTP, sockets)",
            available=True,
        )

        # Process management
        capabilities["sys_process"] = Capability(
            name="sys_process",
            type="system",
            description="Process and thread management",
            available=True,
        )

        # Memory management
        import psutil

        if psutil:
            capabilities["sys_monitoring"] = Capability(
                name="sys_monitoring",
                type="system",
                description="System resource monitoring",
                metadata={"psutil_version": psutil.__version__},
                available=True,
            )

        return capabilities

    async def discover_new_capability(self, hint: str) -> Optional[Capability]:
        """Try to discover a new capability based on a hint"""

        logger.info(f"Attempting to discover capability: {hint}")

        # Check if it's a Python module
        try:
            module = importlib.import_module(hint)
            capability = Capability(
                name=f"python_{hint}",
                type="python_module",
                description=f"Python module: {hint}",
                available=True,
            )
            self.discovered_capabilities[capability.name] = capability
            return capability
        except ImportError:
            pass

        # Check if it's a CLI tool
        if await self._check_cli_tool(hint):
            capability = Capability(
                name=f"cli_{hint}", type="cli_tool", description=f"CLI tool: {hint}", available=True
            )
            self.discovered_capabilities[capability.name] = capability
            return capability

        # Check if it can be installed
        install_methods = await self._find_installation_method(hint)
        if install_methods:
            capability = Capability(
                name=f"pending_{hint}",
                type="pending",
                description=f"Can be installed: {hint}",
                requirements=install_methods,
                available=False,
            )
            return capability

        logger.warning(f"Could not discover capability: {hint}")
        return None

    async def analyze_capability_gaps(self, goal: str) -> List[str]:
        """Identify missing capabilities for a goal"""

        gaps = []

        # Analyze goal keywords
        goal_lower = goal.lower()

        # Check for web-related needs
        if any(word in goal_lower for word in ["web", "scrape", "search", "browse"]):
            if "mcp_firecrawl" not in self.discovered_capabilities:
                gaps.append("web_scraping")
            if "python_beautifulsoup4" not in self.discovered_capabilities:
                gaps.append("html_parsing")

        # Check for data processing needs
        if any(word in goal_lower for word in ["data", "analyze", "process", "csv"]):
            if "python_pandas" not in self.discovered_capabilities:
                gaps.append("data_processing")
            if "python_numpy" not in self.discovered_capabilities:
                gaps.append("numerical_computing")

        # Check for testing needs
        if any(word in goal_lower for word in ["test", "validate", "verify"]):
            if "python_pytest" not in self.discovered_capabilities:
                gaps.append("testing_framework")

        # Check for ML/AI needs
        if any(word in goal_lower for word in ["ml", "machine learning", "ai", "neural"]):
            gaps.append("machine_learning_framework")

        return gaps

    def _check_mcp_tool_available(self, tool_name: str) -> bool:
        """Check if an MCP tool is available"""

        # In production, would actually check MCP availability
        # For now, return True for known tools
        known_tools = ["claude-code", "firecrawl", "time", "git"]
        return tool_name in known_tools

    async def _check_cli_tool(self, tool_name: str) -> bool:
        """Check if a CLI tool is available"""

        try:
            result = subprocess.run(["which", tool_name], capture_output=True, text=True, timeout=2)
            return result.returncode == 0
        except:
            return False

    async def _get_tool_version(self, tool_name: str) -> str:
        """Get version of a CLI tool"""

        version_flags = ["--version", "-v", "version", "-V"]

        for flag in version_flags:
            try:
                result = subprocess.run(
                    [tool_name, flag], capture_output=True, text=True, timeout=2
                )
                if result.returncode == 0:
                    # Extract version from output
                    output = result.stdout.strip()
                    if output:
                        return output.split("\n")[0]
            except:
                continue

        return "unknown"

    async def _find_installation_method(self, package: str) -> List[str]:
        """Find ways to install a package"""

        methods = []

        # Check pip
        try:
            result = subprocess.run(
                ["pip", "search", package], capture_output=True, text=True, timeout=5
            )
            if package in result.stdout:
                methods.append(f"pip install {package}")
        except:
            pass

        # Check npm
        try:
            result = subprocess.run(
                ["npm", "search", package, "--json"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                methods.append(f"npm install {package}")
        except:
            pass

        # Check apt (Linux)
        if os.path.exists("/usr/bin/apt"):
            methods.append(f"apt install {package}")

        # Check brew (macOS)
        if os.path.exists("/usr/local/bin/brew"):
            methods.append(f"brew install {package}")

        return methods

    def get_capability_summary(self) -> Dict[str, Any]:
        """Get summary of discovered capabilities"""

        by_type = {}
        for cap in self.discovered_capabilities.values():
            if cap.type not in by_type:
                by_type[cap.type] = []
            by_type[cap.type].append(cap.name)

        return {
            "total": len(self.discovered_capabilities),
            "by_type": by_type,
            "available": len([c for c in self.discovered_capabilities.values() if c.available]),
            "unavailable": len(self.unavailable_capabilities),
        }
