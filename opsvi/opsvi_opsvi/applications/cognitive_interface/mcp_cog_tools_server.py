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
from typing import Any, Dict, List

from src.shared.interfaces.database.consolidated_arango import ConsolidatedArangoDB
from src.shared.mcp.mcp_server_template import BaseTool, MCPServerTemplate, TextContent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cog_tools_mcp")

# Initialize MCP server
db = None

print("[COG TOOLS MCP] mcp_cog_tools_server.py LOADED")


def get_db():
    """Get database connection with lazy initialization"""
    global db
    if db is None:
        db = ConsolidatedArangoDB()
    return db


class ArangoSearchTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="arango_search",
            description="""Search/query operations with type-based routing. Eliminates AQL complexity.\nsearch_types: content, tags, date_range, type, recent, id""",
            input_schema={
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
                    "content": {
                        "type": "string",
                        "description": "Text to search for (content search)",
                    },
                    "fields": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Specific fields to search in (optional)",
                    },
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
                    "document_type": {
                        "type": "string",
                        "description": "Document type to filter by",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results",
                        "default": 20,
                    },
                    "min_quality": {
                        "type": "number",
                        "description": "Minimum quality score",
                    },
                    "quality_field": {
                        "type": "string",
                        "description": "Quality field name",
                        "default": "quality_score",
                    },
                    "hours": {
                        "type": "integer",
                        "description": "Number of hours back for recent search",
                        "default": 24,
                    },
                    "reference_id": {
                        "type": "string",
                        "description": "Reference document ID for related search",
                    },
                    "relationship_type": {
                        "type": "string",
                        "description": "Type of relationship to filter by (optional)",
                    },
                    "document_id": {
                        "type": "string",
                        "description": "Document ID for direct lookup",
                    },
                },
                "required": ["search_type", "collection"],
            },
        )

    async def execute(self, arguments: Dict[str, Any]) -> List[TextContent]:
        database = get_db()
        search_type = arguments["search_type"]
        collection = arguments["collection"]
        AGENT_PARAMS_TO_IGNORE = {"explanation", "description", "reason", "context"}
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


class ArangoModifyTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="arango_modify",
            description="""CRUD operations with operation-based routing. Eliminates AQL complexity.\noperations: insert, update, delete, upsert""",
            input_schema={
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
                    "document": {
                        "type": "object",
                        "description": "Document data for insert/upsert operations",
                    },
                    "validate_schema": {
                        "type": "boolean",
                        "description": "Whether to validate document schema",
                        "default": True,
                    },
                    "key": {
                        "type": "string",
                        "description": "Document key for update/delete by key",
                    },
                    "criteria": {
                        "type": "object",
                        "description": "Criteria object for update/delete by conditions",
                    },
                    "updates": {
                        "type": "object",
                        "description": "Update data for update operations",
                    },
                    "upsert": {
                        "type": "boolean",
                        "description": "Whether to create if not exists during update",
                        "default": False,
                    },
                    "confirm": {
                        "type": "boolean",
                        "description": "Confirmation required for delete operations",
                        "default": False,
                    },
                    "match_fields": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Fields to match for upsert operations",
                    },
                },
                "required": ["operation", "collection"],
            },
        )

    async def execute(self, arguments: Dict[str, Any]) -> List[TextContent]:
        database = get_db()
        operation = arguments["operation"]
        collection = arguments["collection"]
        AGENT_PARAMS_TO_IGNORE = {"explanation", "description", "reason", "context"}
        modify_params = {
            k: v
            for k, v in arguments.items()
            if k not in ["operation", "collection"] and k not in AGENT_PARAMS_TO_IGNORE
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


class ArangoManageTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="arango_manage",
            description="""Admin/management operations with action-based routing. Eliminates AQL complexity.\nactions: collection_info, backup, health, count, exists, create_collection""",
            input_schema={
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
                    "collection": {
                        "type": "string",
                        "description": "Collection name for collection-specific actions",
                    },
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
                    "criteria": {
                        "type": "object",
                        "description": "Criteria for count/exists operations",
                    },
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
        )

    async def execute(self, arguments: Dict[str, Any]) -> List[TextContent]:
        database = get_db()
        action = arguments["action"]
        AGENT_PARAMS_TO_IGNORE = {"explanation", "description", "reason", "context"}
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


tools = [ArangoSearchTool(), ArangoModifyTool(), ArangoManageTool()]


async def main():
    print("[COG TOOLS MCP] main() starting...")
    logger.info("[COG TOOLS MCP] Starting Consolidated ArangoDB MCP Server")
    print(f"[COG TOOLS MCP] Registering tools: {[t.name for t in tools]}")
    server = MCPServerTemplate(name="consolidated_arango", tools=tools)
    await server.run()
    print("[COG TOOLS MCP] server.run() completed")


if __name__ == "__main__":
    print("[COG TOOLS MCP] __main__ entrypoint reached. Running main()...")
    asyncio.run(main())
