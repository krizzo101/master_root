#!/usr/bin/env python3
"""
MCP Server for Cognitive Database Interface
Provides agent-friendly database operations without AQL syntax complexity
"""

import asyncio
import json
import sys
import logging
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager

# Add core module to path
sys.path.append("/home/opsvi/asea/development/cognitive_interface/core")

from cognitive_database import CognitiveDatabase

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CognitiveMCPServer:
    """MCP Server wrapper for cognitive database operations"""

    def __init__(self):
        self.db = CognitiveDatabase()

    async def handle_tool_call(
        self, name: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle MCP tool calls"""

        try:
            if name == "cognitive_find_memories_about":
                topic = arguments.get("topic", "")
                importance_threshold = arguments.get("importance_threshold", 0.7)
                limit = arguments.get("limit", 10)

                results = self.db.find_memories_about(
                    topic=topic, importance_threshold=importance_threshold, limit=limit
                )

                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(
                                {
                                    "success": True,
                                    "results": results,
                                    "operation": name,
                                },
                                indent=2,
                                default=str,
                            ),
                        }
                    ]
                }

            elif name == "cognitive_get_foundational_memories":
                min_quality = arguments.get("min_quality", 0.8)
                results = self.db.get_foundational_memories(min_quality=min_quality)

                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(
                                {
                                    "success": True,
                                    "results": results,
                                    "operation": name,
                                },
                                indent=2,
                                default=str,
                            ),
                        }
                    ]
                }

            elif name == "cognitive_get_concepts_by_domain":
                domain = arguments.get("domain", "")
                min_quality = arguments.get("min_quality", 0.7)

                results = self.db.get_concepts_by_domain(
                    domain=domain, min_quality=min_quality
                )

                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(
                                {
                                    "success": True,
                                    "results": results,
                                    "operation": name,
                                },
                                indent=2,
                                default=str,
                            ),
                        }
                    ]
                }

            elif name == "cognitive_get_startup_context":
                results = self.db.get_startup_context()

                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(
                                {
                                    "success": True,
                                    "results": results,
                                    "operation": name,
                                },
                                indent=2,
                                default=str,
                            ),
                        }
                    ]
                }

            elif name == "cognitive_assess_system_health":
                results = self.db.assess_system_health()

                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(
                                {
                                    "success": True,
                                    "results": results,
                                    "operation": name,
                                },
                                indent=2,
                                default=str,
                            ),
                        }
                    ]
                }

            elif name == "cognitive_get_memories_by_type":
                memory_type = arguments.get("memory_type", "")
                limit = arguments.get("limit", 20)

                results = self.db.get_memories_by_type(
                    memory_type=memory_type, limit=limit
                )

                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(
                                {
                                    "success": True,
                                    "results": results,
                                    "operation": name,
                                },
                                indent=2,
                                default=str,
                            ),
                        }
                    ]
                }

            else:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(
                                {
                                    "success": False,
                                    "error": f"Unknown tool: {name}",
                                    "available_tools": [
                                        "cognitive_find_memories_about",
                                        "cognitive_get_foundational_memories",
                                        "cognitive_get_concepts_by_domain",
                                        "cognitive_get_startup_context",
                                        "cognitive_assess_system_health",
                                        "cognitive_get_memories_by_type",
                                    ],
                                },
                                indent=2,
                            ),
                        }
                    ]
                }

        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(
                            {
                                "success": False,
                                "error": str(e),
                                "error_type": type(e).__name__,
                                "operation": name,
                            },
                            indent=2,
                        ),
                    }
                ]
            }

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP JSONRPC requests"""

        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")

        try:
            if method == "initialize":
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {
                            "name": "cognitive-database",
                            "version": "1.0.0",
                        },
                    },
                }

            elif method == "tools/list":
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "tools": [
                            {
                                "name": "cognitive_find_memories_about",
                                "description": "Find memories related to a specific topic",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "topic": {
                                            "type": "string",
                                            "description": "Topic to search for",
                                        },
                                        "importance_threshold": {
                                            "type": "number",
                                            "default": 0.7,
                                        },
                                        "limit": {"type": "integer", "default": 10},
                                    },
                                    "required": ["topic"],
                                },
                            },
                            {
                                "name": "cognitive_get_foundational_memories",
                                "description": "Get foundational memories for agent startup",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "min_quality": {
                                            "type": "number",
                                            "default": 0.8,
                                        }
                                    },
                                },
                            },
                            {
                                "name": "cognitive_get_concepts_by_domain",
                                "description": "Get cognitive concepts by domain",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "domain": {
                                            "type": "string",
                                            "description": "Domain to filter by",
                                        },
                                        "min_quality": {
                                            "type": "number",
                                            "default": 0.7,
                                        },
                                    },
                                    "required": ["domain"],
                                },
                            },
                            {
                                "name": "cognitive_get_startup_context",
                                "description": "Get complete startup context for agents",
                                "inputSchema": {"type": "object", "properties": {}},
                            },
                            {
                                "name": "cognitive_assess_system_health",
                                "description": "Assess cognitive database system health",
                                "inputSchema": {"type": "object", "properties": {}},
                            },
                            {
                                "name": "cognitive_get_memories_by_type",
                                "description": "Get memories filtered by type",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "memory_type": {
                                            "type": "string",
                                            "description": "Type of memory to filter by",
                                        },
                                        "limit": {"type": "integer", "default": 20},
                                    },
                                    "required": ["memory_type"],
                                },
                            },
                        ]
                    },
                }

            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})

                result = await self.handle_tool_call(tool_name, arguments)

                return {"jsonrpc": "2.0", "id": request_id, "result": result}

            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32601, "message": f"Method not found: {method}"},
                }

        except Exception as e:
            logger.error(f"Request handling failed: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32603, "message": f"Internal error: {str(e)}"},
            }


async def main():
    """Main MCP server loop"""
    server = CognitiveMCPServer()

    # Command line interface for testing
    if len(sys.argv) > 1:
        method = sys.argv[1]
        params = {}

        # Parse simple key=value arguments
        for arg in sys.argv[2:]:
            if "=" in arg:
                key, value = arg.split("=", 1)
                # Try to convert to appropriate type
                try:
                    if value.isdigit():
                        params[key] = int(value)
                    elif value.replace(".", "").isdigit():
                        params[key] = float(value)
                    else:
                        params[key] = value
                except:
                    params[key] = value

        # Simulate MCP tool call
        result = await server.handle_tool_call(f"cognitive_{method}", params)
        print(result["content"][0]["text"])
        return

    # MCP JSONRPC server mode
    logger.info("Starting Cognitive Database MCP Server")

    try:
        while True:
            line = await asyncio.get_event_loop().run_in_executor(
                None, sys.stdin.readline
            )
            if not line:
                break

            try:
                request = json.loads(line.strip())
                response = await server.handle_request(request)
                print(json.dumps(response))
                sys.stdout.flush()
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received: {line}")
            except Exception as e:
                logger.error(f"Error processing request: {e}")

    except KeyboardInterrupt:
        logger.info("Server shutdown")
    except Exception as e:
        logger.error(f"Server error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
