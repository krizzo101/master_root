"""
Consolidated ArangoDB MCP Server
Provides 3 agent-friendly tools that eliminate AQL complexity:
- arango_search: All search/query operations
- arango_modify: All CRUD operations
- arango_manage: All admin operations
"""

import asyncio
import json
import logging
import os

# Import our consolidated database class
import sys
from typing import Any

from mcp.server import Server
from mcp.types import TextContent, Tool

sys.path.append(os.path.join(os.path.dirname(__file__), "core"))
from shared.interfaces.database.consolidated_arango import ConsolidatedArangoDB

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP server
server = Server("consolidated_arango")

# Database connection (lazy loaded)
db = None


def get_db():
    """Get database connection with lazy initialization"""
    global db
    if db is None:
        db = ConsolidatedArangoDB()
    return db


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List the 3 consolidated ArangoDB tools"""
    return [
        Tool(
            name="arango_search",
            description="""Search/query operations with type-based routing. Eliminates AQL complexity.
            search_types: content, tags, date_range, type, recent, id""",
            inputSchema={
                "type": "object",
                "properties": {
                    "search_type": {
                        "type": "string",
                        "enum": [
                            "content",
                            "tags",
                            "date_range",
                            "type",
                            "recent",
                            "quality",
                            "related",
                            "id",
                        ],
                        "description": "Type of search to perform",
                    },
                    "collection": {
                        "type": "string",
                        "description": "Collection name to search in",
                    },
                    # Content search parameters
                    "content": {
                        "type": "string",
                        "description": "Text to search for (content search)",
                    },
                    "fields": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Specific fields to search in (optional)",
                    },
                    # Tag search parameters
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Tags to search for (tag search)",
                    },
                    "match_all": {
                        "type": "boolean",
                        "description": "Whether all tags must match (true) or any tag (false)",
                        "default": False,
                    },
                    # Date range parameters
                    "start_date": {
                        "type": "string",
                        "description": "Start date (ISO format) for date range search",
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date (ISO format) for date range search",
                    },
                    "date_field": {
                        "type": "string",
                        "description": "Date field name to use",
                        "default": "created",
                    },
                    # Type search parameters
                    "document_type": {
                        "type": "string",
                        "description": "Document type to filter by",
                    },
                    # General parameters
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results",
                        "default": 20,
                    },
                    # Quality search parameters
                    "min_quality": {
                        "type": "number",
                        "description": "Minimum quality score",
                    },
                    "quality_field": {
                        "type": "string",
                        "description": "Quality field name",
                        "default": "quality_score",
                    },
                    # Recent search parameters
                    "hours": {
                        "type": "integer",
                        "description": "Number of hours back for recent search",
                        "default": 24,
                    },
                    # Related search parameters
                    "reference_id": {
                        "type": "string",
                        "description": "Reference document ID for related search",
                    },
                    "relationship_type": {
                        "type": "string",
                        "description": "Type of relationship to filter by (optional)",
                    },
                    # ID search parameters
                    "document_id": {
                        "type": "string",
                        "description": "Document ID for direct lookup",
                    },
                },
                "required": ["search_type", "collection"],
            },
        ),
        Tool(
            name="arango_modify",
            description="""CRUD operations with operation-based routing. Eliminates AQL complexity.
            operations: insert, update, delete, upsert""",
            inputSchema={
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["insert", "update", "delete", "upsert"],
                        "description": "Type of modification operation",
                    },
                    "collection": {
                        "type": "string",
                        "description": "Collection name to modify",
                    },
                    # Insert/upsert parameters
                    "document": {
                        "type": "object",
                        "description": "Document data for insert/upsert operations",
                    },
                    "validate_schema": {
                        "type": "boolean",
                        "description": "Whether to validate document schema",
                        "default": True,
                    },
                    # Update/delete parameters
                    "key": {
                        "type": "string",
                        "description": "Document key for update/delete by key",
                    },
                    "criteria": {
                        "type": "object",
                        "description": "Criteria object for update/delete by conditions",
                    },
                    # Update parameters
                    "updates": {
                        "type": "object",
                        "description": "Update data for update operations",
                    },
                    "upsert": {
                        "type": "boolean",
                        "description": "Whether to create if not exists during update",
                        "default": False,
                    },
                    # Delete parameters
                    "confirm": {
                        "type": "boolean",
                        "description": "Confirmation required for delete operations",
                        "default": False,
                    },
                    # Upsert parameters
                    "match_fields": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Fields to match for upsert operations",
                    },
                },
                "required": ["operation", "collection"],
            },
        ),
        Tool(
            name="arango_manage",
            description="""Admin/management operations with action-based routing. Eliminates AQL complexity.
            actions: collection_info, backup, health, count, exists, create_collection""",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "collection_info",
                            "health",
                            "count",
                            "exists",
                            "create_collection",
                        ],
                        "description": "Type of management action (backup temporarily disabled)",
                    },
                    # Collection-specific parameters
                    "collection": {
                        "type": "string",
                        "description": "Collection name for collection-specific actions",
                    },
                    # Backup parameters
                    "collections": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of collections to backup (optional, defaults to all)",
                    },
                    "output_dir": {
                        "type": "string",
                        "description": "Output directory for backup",
                        "default": "./backup",
                    },
                    # Count/exists parameters
                    "criteria": {
                        "type": "object",
                        "description": "Criteria for count/exists operations",
                    },
                    # Create collection parameters
                    "name": {
                        "type": "string",
                        "description": "Name for new collection",
                    },
                    "collection_type": {
                        "type": "string",
                        "enum": ["document", "edge"],
                        "description": "Type of collection to create",
                        "default": "document",
                    },
                },
                "required": ["action"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle consolidated tool calls"""

    # Filter out agent-added parameters that our tools don't support
    AGENT_PARAMS_TO_IGNORE = {"explanation", "description", "reason", "context"}

    try:
        database = get_db()

        if name == "arango_search":
            search_type = arguments["search_type"]
            collection = arguments["collection"]

            # Remove tool-specific params and agent-added params, pass the rest
            search_params = {
                k: v
                for k, v in arguments.items()
                if k not in ["search_type", "collection"]
                and k not in AGENT_PARAMS_TO_IGNORE
            }

            result = database.search(search_type, collection, **search_params)

            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "tool": "arango_search",
                            "search_type": search_type,
                            "collection": collection,
                            "result": result,
                        },
                        indent=2,
                    ),
                )
            ]

        elif name == "arango_modify":
            operation = arguments["operation"]
            collection = arguments["collection"]

            # Remove tool-specific params and agent-added params, pass the rest
            modify_params = {
                k: v
                for k, v in arguments.items()
                if k not in ["operation", "collection"]
                and k not in AGENT_PARAMS_TO_IGNORE
            }

            result = database.modify(operation, collection, **modify_params)

            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "tool": "arango_modify",
                            "operation": operation,
                            "collection": collection,
                            "result": result,
                        },
                        indent=2,
                    ),
                )
            ]

        elif name == "arango_manage":
            action = arguments["action"]

            # Remove tool-specific param and agent-added params, pass the rest
            manage_params = {
                k: v
                for k, v in arguments.items()
                if k != "action" and k not in AGENT_PARAMS_TO_IGNORE
            }

            result = database.manage(action, **manage_params)

            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {"tool": "arango_manage", "action": action, "result": result},
                        indent=2,
                    ),
                )
            ]

        else:
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "error": f"Unknown tool: {name}",
                            "available_tools": [
                                "arango_search",
                                "arango_modify",
                                "arango_manage",
                            ],
                        }
                    ),
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
    """Main function to run consolidated MCP server"""

    # Import stdio transport
    from mcp.server.stdio import stdio_server

    logger.info("Starting Consolidated ArangoDB MCP Server")

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream, write_stream, server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
