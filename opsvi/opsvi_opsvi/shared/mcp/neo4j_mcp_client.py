#!/usr/bin/env python3
"""
Neo4j MCP Client - Knowledge Base Queries via MCP

This script provides a Python interface to the Neo4j MCP server for knowledge base queries.
Uses the connection details from .cursor/mcp.json configuration.

## Prerequisites

```bash
# Install MCP Python SDK
pip install "mcp[cli]"

# Install Neo4j MCP server
uvx mcp-neo4j-cypher
```

## Configuration

Connection details are read from .cursor/mcp.json:
- Server: neo4j-mcp
- URL: bolt://localhost:7687
- User: neo4j
- Password: oamatdbtest

## Features

- Execute read-only Cypher queries
- Get database schema information
- Search for nodes and relationships
- Extract knowledge for agent workflows
"""

import asyncio
import json
import logging
import os
import sys
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# MCP imports
try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    from mcp.types import CallToolResult, TextContent
except ImportError:
    print("Error: MCP Python SDK not installed.")
    print("Install with: pip install 'mcp[cli]'")
    sys.exit(1)


# Custom exceptions
class Neo4jMCPError(Exception):
    """Base exception for Neo4j MCP related errors."""

    pass


@dataclass
class QueryResult:
    """Result from Neo4j query operation."""

    query: str
    success: bool = True
    data: list[dict[str, Any]] = None
    error: str = ""
    count: int = 0

    def __post_init__(self):
        if self.data is None:
            self.data = []
        self.count = len(self.data)

    def __str__(self) -> str:
        return f"Query: {self.query[:50]}... - {self.count} results"


class Neo4jMCPClient:
    """
    Client for interacting with Neo4j MCP server.

    This client provides high-level methods for knowledge base queries
    using Neo4j through MCP.
    """

    def __init__(self, mcp_config_path: str | None = None, debug: bool = False):
        """
        Initialize the Neo4j MCP client.

        Args:
            mcp_config_path: Path to mcp.json config file
            debug: Enable debug logging
        """
        self.mcp_config_path = mcp_config_path or ".cursor/mcp.json"
        self.debug = debug

        # Setup logging
        logging.basicConfig(
            level=logging.DEBUG if debug else logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger(__name__)

    @asynccontextmanager
    async def _get_session(self):
        """Create and manage an MCP session with Neo4j server."""
        # Load server configuration
        config_path = Path(self.mcp_config_path)
        if not config_path.exists():
            raise FileNotFoundError(f"MCP config file not found: {config_path}")

        with open(config_path) as f:
            config = json.load(f)

        neo4j_config = config.get("mcpServers", {}).get("neo4j-mcp", {})
        if not neo4j_config:
            raise ValueError("Neo4j MCP server not found in MCP configuration")

        # Server parameters for stdio connection
        server_params = StdioServerParameters(
            command=neo4j_config.get("command", "uvx"),
            args=neo4j_config.get(
                "args",
                [
                    "mcp-neo4j-cypher",
                    "--db-url",
                    "bolt://localhost:7687",
                    "--user",
                    "neo4j",
                    "--password",
                    "oamatdbtest",
                ],
            ),
            env={**os.environ, **neo4j_config.get("env", {})},
        )

        try:
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    self.logger.debug("Neo4j MCP session initialized")
                    yield session
        except Exception as e:
            self.logger.error(f"Failed to establish MCP session: {e}")
            raise Neo4jMCPError(f"Failed to connect to Neo4j MCP server: {e}")

    async def get_schema(self) -> QueryResult:
        """Get the database schema information."""
        self.logger.info("Getting Neo4j database schema")

        async with self._get_session() as session:
            try:
                result = await session.call_tool(
                    "mcp_neo4j-mcp_get_neo4j_schema", {"random_string": "schema"}
                )

                if result.content:
                    content = result.content[0]
                    if isinstance(content, TextContent):
                        try:
                            data = json.loads(content.text)
                            return QueryResult(
                                query="SCHEMA",
                                success=True,
                                data=[data] if isinstance(data, dict) else data,
                            )
                        except json.JSONDecodeError:
                            return QueryResult(
                                query="SCHEMA",
                                success=True,
                                data=[{"schema": content.text}],
                            )

                return QueryResult(
                    query="SCHEMA", success=False, error="No schema data received"
                )

            except Exception as e:
                self.logger.error(f"Schema query failed: {e}")
                return QueryResult(query="SCHEMA", success=False, error=str(e))

    async def read_query(
        self, query: str, params: dict[str, Any] | None = None
    ) -> QueryResult:
        """Execute a read-only Cypher query."""
        if not query.strip():
            raise ValueError("Query cannot be empty")

        self.logger.info(f"Executing read query: {query[:100]}...")

        async with self._get_session() as session:
            try:
                arguments = {"query": query}
                if params:
                    arguments["params"] = params

                result = await session.call_tool(
                    "mcp_neo4j-mcp_read_neo4j_cypher", arguments
                )

                if result.content:
                    content = result.content[0]
                    if isinstance(content, TextContent):
                        try:
                            data = json.loads(content.text)
                            return QueryResult(
                                query=query,
                                success=True,
                                data=data if isinstance(data, list) else [data],
                            )
                        except json.JSONDecodeError:
                            return QueryResult(
                                query=query,
                                success=True,
                                data=[{"result": content.text}],
                            )

                return QueryResult(query=query, success=False, error="No data received")

            except Exception as e:
                self.logger.error(f"Read query failed: {e}")
                return QueryResult(query=query, success=False, error=str(e))

    async def search_nodes(
        self,
        label: str = None,
        property_name: str = None,
        property_value: str = None,
        limit: int = 10,
    ) -> QueryResult:
        """Search for nodes by label and/or properties."""
        query_parts = ["MATCH (n"]
        params = {}

        if label:
            query_parts[0] += f":{label}"

        query_parts.append(")")

        where_conditions = []
        if property_name and property_value:
            where_conditions.append(f"n.{property_name} CONTAINS $prop_value")
            params["prop_value"] = property_value

        if where_conditions:
            query_parts.append("WHERE " + " AND ".join(where_conditions))

        query_parts.append(f"RETURN n LIMIT {limit}")
        query = " ".join(query_parts)

        return await self.read_query(query, params)

    async def search_relationships(
        self, rel_type: str = None, limit: int = 10
    ) -> QueryResult:
        """Search for relationships by type."""
        if rel_type:
            query = f"MATCH ()-[r:{rel_type}]-() RETURN r LIMIT {limit}"
        else:
            query = f"MATCH ()-[r]-() RETURN r LIMIT {limit}"

        return await self.read_query(query)

    async def find_connected_nodes(
        self, node_id: str, max_depth: int = 2
    ) -> QueryResult:
        """Find nodes connected to a specific node."""
        query = f"""
        MATCH (start)
        WHERE id(start) = $node_id
        MATCH (start)-[*1..{max_depth}]-(connected)
        RETURN DISTINCT connected
        LIMIT 50
        """
        params = {"node_id": int(node_id)}
        return await self.read_query(query, params)

    async def search_by_text(
        self, search_text: str, properties: list[str] = None, limit: int = 10
    ) -> QueryResult:
        """Search nodes by text content in specified properties."""
        if not properties:
            properties = ["name", "title", "description", "content"]

        conditions = []
        for prop in properties:
            conditions.append(f"n.{prop} CONTAINS $search_text")

        query = f"""
        MATCH (n)
        WHERE {' OR '.join(conditions)}
        RETURN n
        LIMIT {limit}
        """
        params = {"search_text": search_text}
        return await self.read_query(query, params)


# Utility functions
async def quick_search(search_text: str, **kwargs) -> QueryResult:
    """Quick text search in the knowledge base."""
    client = Neo4jMCPClient()
    return await client.search_by_text(search_text, **kwargs)


async def get_kb_schema() -> QueryResult:
    """Quick schema retrieval."""
    client = Neo4jMCPClient()
    return await client.get_schema()


# Command line interface
async def main():
    """Command line interface for Neo4j MCP client."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Neo4j MCP Client - Knowledge Base Queries",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Get database schema
  python neo4j_mcp_client.py schema

  # Search for nodes
  python neo4j_mcp_client.py search "machine learning" --limit 5

  # Execute custom query
  python neo4j_mcp_client.py query "MATCH (n:Agent) RETURN n LIMIT 5"
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Schema command
    schema_parser = subparsers.add_parser("schema", help="Get database schema")

    # Search command
    search_parser = subparsers.add_parser("search", help="Search nodes by text")
    search_parser.add_argument("text", help="Text to search for")
    search_parser.add_argument("--limit", type=int, default=10, help="Maximum results")
    search_parser.add_argument(
        "--properties", nargs="+", help="Properties to search in"
    )

    # Query command
    query_parser = subparsers.add_parser("query", help="Execute custom Cypher query")
    query_parser.add_argument("cypher", help="Cypher query to execute")

    # Global options
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--config", help="Path to mcp.json config file")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        client = Neo4jMCPClient(mcp_config_path=args.config, debug=args.debug)

        if args.command == "schema":
            result = await client.get_schema()
            if result.success:
                print("✅ Database Schema:")
                print("=" * 50)
                for item in result.data:
                    print(json.dumps(item, indent=2))
            else:
                print(f"❌ Error: {result.error}")

        elif args.command == "search":
            result = await client.search_by_text(
                args.text, properties=args.properties, limit=args.limit
            )
            if result.success:
                print(f"✅ Found {result.count} results for: '{args.text}'")
                print("=" * 50)
                for i, item in enumerate(result.data, 1):
                    print(f"{i}. {json.dumps(item, indent=2)}")
            else:
                print(f"❌ Error: {result.error}")

        elif args.command == "query":
            result = await client.read_query(args.cypher)
            if result.success:
                print(f"✅ Query executed successfully - {result.count} results")
                print("=" * 50)
                for item in result.data:
                    print(json.dumps(item, indent=2))
            else:
                print(f"❌ Error: {result.error}")

    except KeyboardInterrupt:
        print("\nOperation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
