#!/usr/bin/env python3
"""
MCP Tool wrapper for Project Intelligence Reader

This provides a native MCP tool interface to the proj_intel_reader,
making it trivial for agents to access project intelligence data
without needing to use Bash commands.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastmcp.tools import tool


class ProjectIntelligenceTool:
    """MCP Tool wrapper for project intelligence access."""

    def __init__(self):
        self.reader_script = Path(
            "/home/opsvi/master_root/scripts/proj_intel_reader.py"
        )
        if not self.reader_script.exists():
            raise FileNotFoundError(f"Reader script not found at {self.reader_script}")

    def _run_reader(self, args: List[str]) -> Dict[str, Any]:
        """Run the reader script and return JSON output."""
        cmd = [sys.executable, str(self.reader_script)] + args
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            # Try to parse as JSON
            try:
                return {"success": True, "data": json.loads(result.stdout)}
            except json.JSONDecodeError:
                # Return as text if not JSON
                return {"success": True, "text": result.stdout}

        except subprocess.CalledProcessError as e:
            return {"success": False, "error": e.stderr or str(e)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @tool
    async def proj_intel_read_bytes(self, offset: int, size: int) -> Dict[str, Any]:
        """
        Read exact byte range from project intelligence JSONL.

        Args:
            offset: Byte offset to start reading from
            size: Number of bytes to read

        Returns:
            The JSON data at the specified byte range
        """
        args = ["--action", "read-bytes", "--offset", str(offset), "--size", str(size)]
        return self._run_reader(args)

    @tool
    async def proj_intel_read_path(
        self, path: str, format: str = "json"
    ) -> Dict[str, Any]:
        """
        Read all project intelligence items for a specific file path.

        Args:
            path: The file path to query (e.g., "src/main.py")
            format: Output format - "json" or "summary"

        Returns:
            All intelligence items related to the file
        """
        args = ["--action", "read-by-path", "--path", path, "--format", format]
        return self._run_reader(args)

    @tool
    async def proj_intel_read_collector(
        self, collector: str, limit: Optional[int] = None, format: str = "summary"
    ) -> Dict[str, Any]:
        """
        Stream items from a specific collector.

        Available collectors:
        - FileElementsCollector: Functions, classes, imports per file
        - AgentArchitectureCollector: Agent/class definitions
        - EntryPointsCollector: CLI and module entry points
        - DependenciesCollector: Import dependencies
        - ApiEndpointsCollector: HTTP endpoints
        - DataModelsCollector: Pydantic/SQLAlchemy models
        - ConfigEnvCollector: Config files and env vars
        - TestsTopologyCollector: Test files

        Args:
            collector: Name of the collector
            limit: Maximum number of items to return
            format: Output format - "json" or "summary"

        Returns:
            Items from the specified collector
        """
        args = [
            "--action",
            "read-collector",
            "--collector",
            collector,
            "--format",
            format,
        ]
        if limit:
            args.extend(["--limit", str(limit)])
        return self._run_reader(args)

    @tool
    async def proj_intel_file_elements(
        self, limit: Optional[int] = None, format: str = "summary"
    ) -> Dict[str, Any]:
        """
        Get file elements (functions, classes, imports) efficiently.

        Args:
            limit: Maximum number of files to return
            format: Output format - "json" or "summary"

        Returns:
            File element statistics
        """
        args = ["--action", "file-elements", "--format", format]
        if limit:
            args.extend(["--limit", str(limit)])
        return self._run_reader(args)

    @tool
    async def proj_intel_agents(
        self, limit: Optional[int] = None, format: str = "summary"
    ) -> Dict[str, Any]:
        """
        Get agent/class architecture information.

        Args:
            limit: Maximum number of agents to return
            format: Output format - "json" or "summary"

        Returns:
            Agent architecture information
        """
        args = ["--action", "agents", "--format", format]
        if limit:
            args.extend(["--limit", str(limit)])
        return self._run_reader(args)


# Initialize the tool instance
proj_intel_tool = ProjectIntelligenceTool()

# Export the tools
__all__ = [
    "proj_intel_read_bytes",
    "proj_intel_read_path",
    "proj_intel_read_collector",
    "proj_intel_file_elements",
    "proj_intel_agents",
]

# Make tools available at module level
proj_intel_read_bytes = proj_intel_tool.proj_intel_read_bytes
proj_intel_read_path = proj_intel_tool.proj_intel_read_path
proj_intel_read_collector = proj_intel_tool.proj_intel_read_collector
proj_intel_file_elements = proj_intel_tool.proj_intel_file_elements
proj_intel_agents = proj_intel_tool.proj_intel_agents
