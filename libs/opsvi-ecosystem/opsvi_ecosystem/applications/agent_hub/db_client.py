#!/usr/bin/env python3
"""
Database client for Agent Hub that communicates with cognitive_tools MCP server via stdio.
This uses subprocess to directly communicate with the MCP server over JSON-RPC.
"""

import json
import os
from queue import Empty, Queue
import subprocess
import threading
import time
from typing import Any, Dict, Optional
import uuid

from src.shared.interfaces.database.arango_interface import (
    DirectArangoDB as ArangoInterface,
)

# Path to the cognitive_tools MCP server
COGNITIVE_TOOLS_MCP_PATH = os.getenv(
    "COGNITIVE_TOOLS_MCP_PATH",
    "/home/opsvi/agent_world/src/shared/database/mcp_consolidated_server.py",
)

# Python interpreter path
PYTHON_PATH = os.getenv("PYTHON_PATH", "/home/opsvi/miniconda/bin/python")

# Environment variables for the MCP server
MCP_ENV = {
    "PYTHONPATH": "/home/opsvi/agent_world/src/shared/database/core",
    "ARANGO_URL": "http://127.0.0.1:8550",
    "ARANGO_DB": "_system",
    "ARANGO_USERNAME": "root",
    "ARANGO_PASSWORD": "change_me",
    "AGENT_IDE_MODE": "true",
    "COLLECTIONS_MAPPING": "agent_ide",
}

# Instantiate a global DirectArangoDB client using environment variables
_db = ArangoInterface(
    host=os.getenv("ARANGO_URL", "http://127.0.0.1:8550"),
    database=os.getenv("ARANGO_DB", "_system"),
    username=os.getenv("ARANGO_USERNAME", "root"),
    password=os.getenv("ARANGO_PASSWORD", "change_me"),
)


def search(**kwargs):
    """Directly proxy to DirectArangoDB search (AQL or helper methods)"""
    # Example: kwargs could be {"aql": "FOR d IN ...", ...} or use a helper
    if "aql" in kwargs:
        try:
            cursor = _db.db.aql.execute(
                kwargs["aql"], bind_vars=kwargs.get("bind_vars", {})
            )
            return {"success": True, "results": list(cursor)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    # Add more helper routing as needed
    return {"success": False, "error": "No valid search parameters provided"}


def modify(operation, collection, **kwargs):
    """Directly proxy to DirectArangoDB for insert/update/delete/upsert"""
    try:
        if operation == "insert":
            return _db.db.collection(collection).insert(kwargs["document"])
        elif operation == "update":
            return _db.db.collection(collection).update(kwargs["document"])
        elif operation == "delete":
            return _db.db.collection(collection).delete(kwargs["key"])
        elif operation == "upsert":
            # Upsert logic: try update, else insert
            key = kwargs["document"].get("_key")
            coll = _db.db.collection(collection)
            if key and coll.has(key):
                return coll.update(kwargs["document"])
            else:
                return coll.insert(kwargs["document"])
        else:
            return {"success": False, "error": f"Unknown operation: {operation}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def manage(action, **kwargs):
    """Directly proxy to DirectArangoDB for management actions"""
    try:
        if action == "collection_info":
            coll = _db.db.collection(kwargs["collection"])
            return coll.properties()
        elif action == "health":
            # Simple health check: list collections
            return {"success": True, "collections": _db.list_collections()}
        elif action == "count":
            coll = _db.db.collection(kwargs["collection"])
            return {"success": True, "count": coll.count()}
        elif action == "exists":
            coll = _db.db.collection(kwargs["collection"])
            key = kwargs.get("key")
            return {"success": True, "exists": coll.has(key)}
        elif action == "create_collection":
            return _db.create_collection(kwargs["name"], edge=kwargs.get("edge", False))
        else:
            return {"success": False, "error": f"Unknown action: {action}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


class MCPDatabaseClient:
    """Simple subprocess-based MCP client for cognitive_tools communication"""

    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.response_queue = Queue()
        self.reader_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    def _start_process(self):
        """Start the MCP server process"""
        if self.process is None or self.process.poll() is not None:
            env = {**os.environ, **MCP_ENV}
            self.process = subprocess.Popen(
                [PYTHON_PATH, COGNITIVE_TOOLS_MCP_PATH],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
            )

            # Start output reader thread
            if self.reader_thread is None or not self.reader_thread.is_alive():
                self.reader_thread = threading.Thread(
                    target=self._read_output, daemon=True
                )
                self.reader_thread.start()

            # Send initialization
            self._send_init()

    def _read_output(self):
        """Read output from MCP server in background thread"""
        while self.process and self.process.poll() is None:
            try:
                line = self.process.stdout.readline()
                if line:
                    line = line.strip()
                    if line:
                        try:
                            response = json.loads(line)
                            self.response_queue.put(response)
                        except json.JSONDecodeError:
                            # Skip non-JSON lines (initialization messages, etc.)
                            pass
            except Exception:
                break

    def _send_init(self):
        """Send MCP initialization"""
        init_msg = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "initialize",
            "params": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}},
        }
        self._send_message(init_msg)

        # Send initialized notification
        initialized_msg = {"jsonrpc": "2.0", "method": "notifications/initialized"}
        self._send_message(initialized_msg)

    def _send_message(self, message: Dict[str, Any]):
        """Send a message to MCP server"""
        if self.process and self.process.stdin:
            json.dump(message, self.process.stdin)
            self.process.stdin.write("\n")
            self.process.stdin.flush()

    def _wait_for_response(
        self, request_id: str, timeout: float = 10.0
    ) -> Dict[str, Any]:
        """Wait for response with specific ID"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = self.response_queue.get(timeout=0.1)
                if response.get("id") == request_id:
                    return response
                # Put it back if it's not our response
                self.response_queue.put(response)
            except Empty:
                continue

        return {"error": "Timeout waiting for response"}

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool via MCP"""
        with self._lock:
            try:
                self._start_process()

                request_id = str(uuid.uuid4())
                request = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "method": "tools/call",
                    "params": {"name": tool_name, "arguments": arguments},
                }

                self._send_message(request)
                response = self._wait_for_response(request_id)

                if "error" in response:
                    return {"error": response["error"], "success": False}

                # Extract result from MCP response
                result = response.get("result", {})
                if "content" in result:
                    content = result["content"]
                    if content and len(content) > 0:
                        text_content = content[0].get("text", "")
                        try:
                            return json.loads(text_content)
                        except json.JSONDecodeError:
                            return {
                                "error": "Invalid JSON in response",
                                "raw": text_content,
                            }

                return result

            except Exception as e:
                return {"error": str(e), "success": False}

    def close(self):
        """Clean up resources"""
        if self.process:
            self.process.terminate()
            self.process.wait()
            self.process = None


# Global client instance
_client = MCPDatabaseClient()


# Synchronous wrapper functions for compatibility with existing code
def search(**kwargs) -> Dict[str, Any]:
    """Proxy to arango_search"""
    return _client.call_tool("arango_search", kwargs)


def modify(**kwargs) -> Dict[str, Any]:
    """Proxy to arango_modify"""
    return _client.call_tool("arango_modify", kwargs)


def manage(**kwargs) -> Dict[str, Any]:
    """Proxy to arango_manage"""
    return _client.call_tool("arango_manage", kwargs)


def test_connection() -> Dict[str, Any]:
    """Test the MCP connection"""
    try:
        result = manage(action="health")
        print(f"Connection test result: {result}")
        return result
    except Exception as e:
        print(f"Connection test failed: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    # Test the connection
    result = test_connection()
    _client.close()
