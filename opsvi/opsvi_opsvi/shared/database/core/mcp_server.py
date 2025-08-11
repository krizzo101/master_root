"""
MCP Server for Cognitive Database Interface
Provides agent-friendly tools without AQL complexity
"""

import asyncio
import json
import logging
from typing import Any, Dict, List

from cognitive_database import CognitiveDatabase
from mcp.server import Server
from mcp.types import TextContent, Tool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize server
server = Server("cognitive_query")

# Initialize database connection (lazy loaded)
db = None


def get_db():
    """Get database connection (lazy initialization)"""
    global db
    if db is None:
        db = CognitiveDatabase()
    return db


@server.list_tools()
async def list_tools() -> List[Tool]:
    """List available cognitive query tools"""
    return [
        Tool(
            name="find_memories_about",
            description="Find memories related to a specific topic. Returns memories containing the topic in title or content, filtered by importance.",
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "Topic to search for in memories",
                    },
                    "importance_threshold": {
                        "type": "number",
                        "description": "Minimum importance score (0.0-1.0)",
                        "default": 0.7,
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 10,
                    },
                },
                "required": ["topic"],
            },
        ),
        Tool(
            name="get_foundational_memories",
            description="Get high-quality foundational memories that are essential for agent operation",
            inputSchema={
                "type": "object",
                "properties": {
                    "min_quality": {
                        "type": "number",
                        "description": "Minimum quality score (0.0-1.0)",
                        "default": 0.8,
                    }
                },
            },
        ),
        Tool(
            name="get_concepts_by_domain",
            description="Get cognitive concepts filtered by domain (e.g., 'operational', 'database', 'development')",
            inputSchema={
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "Domain to filter concepts by",
                    },
                    "min_quality": {
                        "type": "number",
                        "description": "Minimum quality score (0.0-1.0)",
                        "default": 0.7,
                    },
                },
                "required": ["domain"],
            },
        ),
        Tool(
            name="get_startup_context",
            description="Get essential startup context including foundational memories and operational concepts",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="assess_system_health",
            description="Comprehensive assessment of cognitive database health including collection counts and scores",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls"""

    try:
        database = get_db()

        if name == "find_memories_about":
            topic = arguments["topic"]
            importance_threshold = arguments.get("importance_threshold", 0.7)
            limit = arguments.get("limit", 10)

            results = database.find_memories_about(topic, importance_threshold, limit)

            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "tool": "find_memories_about",
                            "topic": topic,
                            "results_count": len(results),
                            "results": results,
                        },
                        indent=2,
                    ),
                )
            ]

        elif name == "get_foundational_memories":
            min_quality = arguments.get("min_quality", 0.8)

            results = database.get_foundational_memories(min_quality)

            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "tool": "get_foundational_memories",
                            "results_count": len(results),
                            "results": results,
                        },
                        indent=2,
                    ),
                )
            ]

        elif name == "get_concepts_by_domain":
            domain = arguments["domain"]
            min_quality = arguments.get("min_quality", 0.7)

            results = database.get_concepts_by_domain(domain, min_quality)

            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "tool": "get_concepts_by_domain",
                            "domain": domain,
                            "results_count": len(results),
                            "results": results,
                        },
                        indent=2,
                    ),
                )
            ]

        elif name == "get_startup_context":
            results = database.get_startup_context()

            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {"tool": "get_startup_context", "results": results}, indent=2
                    ),
                )
            ]

        elif name == "assess_system_health":
            results = database.assess_system_health()

            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {"tool": "assess_system_health", "results": results}, indent=2
                    ),
                )
            ]

        else:
            return [
                TextContent(
                    type="text", text=json.dumps({"error": f"Unknown tool: {name}"})
                )
            ]

    except Exception as e:
        logger.error(f"Tool execution failed: {e}")
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "error": f"Tool execution failed: {str(e)}",
                        "tool": name,
                        "arguments": arguments,
                    }
                ),
            )
        ]


async def main():
    """Main function to run MCP server"""

    # Import mcp.server.stdio for STDIO transport
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream, write_stream, server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
