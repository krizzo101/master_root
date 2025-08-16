#!/usr/bin/env python3
"""
ArXiv MCP Client for Academic Paper Research

This module provides a client for interacting with the ArXiv MCP server
to search, download, and read academic papers.
"""

import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


@dataclass
class ArXivPaper:
    """Represents an ArXiv paper with metadata."""

    title: str
    summary: str
    authors: list[str]
    links: list[str]
    pdf_url: str
    paper_id: str | None = None


class ArXivMCPClient:
    """Client for interacting with the ArXiv MCP server."""

    def __init__(self, server_name: str = "research_papers"):
        """Initialize the ArXiv MCP client.

        Args:
            server_name: Name of the MCP server to connect to
        """
        self.server_name = server_name
        self.logger = logging.getLogger(__name__)

    @asynccontextmanager
    async def _get_mcp_session(self):
        """Create and manage MCP session with ArXiv server."""
        config_path = Path(".cursor/mcp.json")
        if not config_path.exists():
            raise FileNotFoundError(f"MCP config file not found: {config_path}")

        with open(config_path) as f:
            config = json.load(f)

        arxiv_config = config.get("mcpServers", {}).get("research_papers", {})
        if not arxiv_config:
            raise ValueError("research_papers server not found in MCP configuration")

        server_params = StdioServerParameters(
            command=arxiv_config.get("command", "python"),
            args=arxiv_config.get("args", ["-m", "arxiv_mcp_server"]),
            env={**os.environ, **arxiv_config.get("env", {})},
        )

        try:
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    # Initialize the connection
                    await session.initialize()
                    self.logger.debug("ArXiv MCP session initialized successfully")
                    yield session
        except Exception as e:
            self.logger.error(f"Failed to establish ArXiv MCP session: {e}")
            raise Exception(f"Failed to connect to ArXiv MCP server: {e}")

    async def connect(self):
        """Connect to the ArXiv MCP server."""
        # This method is kept for compatibility but not used in the current implementation
        pass

    async def disconnect(self):
        """Disconnect from the ArXiv MCP server."""
        # This method is kept for compatibility but not used in the current implementation
        pass

    async def search_papers(
        self,
        query: str,
        max_results: int = 10,
        categories: list[str] | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[ArXivPaper]:
        """Search for papers on ArXiv.

        Args:
            query: Search query string
            max_results: Maximum number of results to return
            categories: List of ArXiv categories to filter by (e.g., ['cs.AI', 'cs.LG'])
            date_from: Start date in YYYY-MM-DD format
            date_to: End date in YYYY-MM-DD format

        Returns:
            List of ArXivPaper objects
        """
        try:
            arguments = {"query": query, "max_results": max_results}

            if categories:
                arguments["categories"] = categories
            if date_from:
                arguments["date_from"] = date_from
            if date_to:
                arguments["date_to"] = date_to

            async with self._get_mcp_session() as session:
                result = await session.call_tool("search_papers", arguments)

            if not result.content:
                self.logger.warning("No search results returned")
                return []

            # Parse the search results
            papers = []
            for content in result.content:
                if hasattr(content, "text"):
                    try:
                        data = json.loads(content.text)
                        if isinstance(data, dict) and "papers" in data:
                            for paper_data in data["papers"]:
                                paper = ArXivPaper(
                                    title=paper_data.get("title", ""),
                                    summary=paper_data.get("summary", ""),
                                    authors=paper_data.get("authors", []),
                                    links=paper_data.get("links", []),
                                    pdf_url=paper_data.get("pdf_url", ""),
                                    paper_id=paper_data.get("paper_id"),
                                )
                                papers.append(paper)
                    except json.JSONDecodeError as e:
                        self.logger.error(f"Failed to parse search results: {e}")
                        continue

            self.logger.info(f"Found {len(papers)} papers for query: {query}")
            return papers

        except Exception as e:
            self.logger.error(f"Error searching papers: {e}")
            raise

    async def download_paper(self, paper_id: str) -> dict[str, Any]:
        """Download a paper by its ArXiv ID.

        Args:
            paper_id: ArXiv paper ID (e.g., '2501.10120')

        Returns:
            Dictionary containing download status and metadata
        """
        try:
            arguments = {"paper_id": paper_id}

            async with self._get_mcp_session() as session:
                result = await session.call_tool("download_paper", arguments)

            if not result.content:
                self.logger.warning(f"No download result for paper {paper_id}")
                return {"success": False, "error": "No download result"}

            # Parse the download result
            for content in result.content:
                if hasattr(content, "text"):
                    try:
                        data = json.loads(content.text)
                        self.logger.info(
                            f"Downloaded paper {paper_id}: {data.get('success', False)}"
                        )
                        return data
                    except json.JSONDecodeError as e:
                        self.logger.error(f"Failed to parse download result: {e}")
                        continue

            return {"success": False, "error": "Failed to parse download result"}

        except Exception as e:
            self.logger.error(f"Error downloading paper {paper_id}: {e}")
            raise

    async def read_paper(self, paper_id: str) -> dict[str, Any]:
        """Read a downloaded paper by its ArXiv ID.

        Args:
            paper_id: ArXiv paper ID (e.g., '2501.10120')

        Returns:
            Dictionary containing paper content and metadata
        """
        try:
            arguments = {"paper_id": paper_id}

            async with self._get_mcp_session() as session:
                result = await session.call_tool("read_paper", arguments)

            if not result.content:
                self.logger.warning(f"No read result for paper {paper_id}")
                return {"success": False, "error": "No read result"}

            # Parse the read result
            for content in result.content:
                if hasattr(content, "text"):
                    try:
                        data = json.loads(content.text)
                        self.logger.info(
                            f"Read paper {paper_id}: {data.get('success', False)}"
                        )
                        return data
                    except json.JSONDecodeError as e:
                        self.logger.error(f"Failed to parse read result: {e}")
                        continue

            return {"success": False, "error": "Failed to parse read result"}

        except Exception as e:
            self.logger.error(f"Error reading paper {paper_id}: {e}")
            raise

    async def list_papers(self) -> dict[str, Any]:
        """List all available papers.

        Returns:
            Dictionary containing list of papers and metadata
        """
        try:
            arguments = {"random_string": "list"}

            async with self._get_mcp_session() as session:
                result = await session.call_tool("list_papers", arguments)

            if not result.content:
                self.logger.warning("No list result returned")
                return {"success": False, "error": "No list result"}

            # Parse the list result
            for content in result.content:
                if hasattr(content, "text"):
                    try:
                        data = json.loads(content.text)
                        self.logger.info(
                            f"Listed papers: {data.get('total_papers', 0)} total"
                        )
                        return data
                    except json.JSONDecodeError as e:
                        self.logger.error(f"Failed to parse list result: {e}")
                        continue

            return {"success": False, "error": "Failed to parse list result"}

        except Exception as e:
            self.logger.error(f"Error listing papers: {e}")
            raise


async def main():
    """Example usage of the ArXiv MCP client."""
    async with ArXivMCPClient() as client:
        # Search for papers
        papers = await client.search_papers("large language models", max_results=5)
        print(f"Found {len(papers)} papers")

        for paper in papers:
            print(f"Title: {paper.title}")
            print(f"Authors: {', '.join(paper.authors)}")
            print(f"PDF URL: {paper.pdf_url}")
            print("---")


if __name__ == "__main__":
    asyncio.run(main())
