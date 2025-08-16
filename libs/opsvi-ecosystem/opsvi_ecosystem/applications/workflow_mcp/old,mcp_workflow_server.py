import asyncio
import json
import logging
import os
import sys
import traceback
from typing import Any

from src.applications.workflow_mcp.agent_runner import EmbeddedAgentRunner
from src.applications.workflow_mcp.db import WorkflowDB

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
# Add FileHandler to log to /tmp/workflow_mcp.log for persistent troubleshooting
file_handler = logging.FileHandler("/tmp/workflow_mcp.log")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(
    logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
)
logging.getLogger().addHandler(file_handler)
logger = logging.getLogger("workflow_mcp_jsonrpc")

db = WorkflowDB()
agent_runner = EmbeddedAgentRunner()

# Define the absolute project root for all file operations
PROJECT_ROOT = "/home/opsvi/agent_world"


# --- Helper: Load file from disk ---
def load_file(path: str) -> str | None:
    try:
        with open(os.path.join(PROJECT_ROOT, path), encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to load file {path}: {e}")
        return None


# --- Helper: Load workflow and all supporting files ---
def load_workflow_and_context(workflow_id: str | None = None) -> dict[str, Any]:
    context = {}
    if workflow_id:
        # Load workflow and files from ArangoDB
        wf_doc = db.get_workflow(workflow_id)
        if not wf_doc.get("success") or not wf_doc.get("document"):
            return {"error": f"Workflow {workflow_id} not found in DB"}
        workflow = wf_doc["document"]
        context["workflow_yaml"] = workflow.get("yaml") or workflow.get("spec")
        # Load supporting files (agent_profile, template, docs, etc.)
        for key in [
            "agent_profile",
            "output_template",
            "research_reference",
            "documentation",
        ]:
            if workflow.get(key):
                context[key] = workflow[key]
    else:
        # Load default workflow_generation workflow and all referenced files from disk
        context["workflow_yaml"] = load_file(
            ".cursor/workflows/workflow_generation.yml"
        )
        context["agent_profile"] = load_file(
            ".cursor/profiles/workflow_generation_agent_profile.yml"
        )
        context["output_template"] = load_file(
            ".cursor/templates/workflow_generation_output_template.yml"
        )
        context["research_reference_template"] = load_file(
            ".cursor/templates/research_reference_template.md"
        )
        context["documentation_template"] = load_file(
            "docs/standards/workflow_generation_workflow.md"
        )
    return context


# --- Main agentic workflow tool ---
async def agentic_workflow_tool(
    prompt: str, workflow_id: str | None = None
) -> dict[str, Any]:
    context = load_workflow_and_context(workflow_id)
    if "error" in context:
        return {"success": False, "error": context["error"]}
    # Run the agent with all context
    agent_input = {
        "prompt": prompt,
        "workflow_yaml": context.get("workflow_yaml"),
        "agent_profile": context.get("agent_profile"),
        "output_template": context.get("output_template"),
        "research_reference_template": context.get("research_reference_template"),
        "documentation_template": context.get("documentation_template"),
    }
    agent_result = agent_runner.run_workflow(agent_input, {})
    # Parse outputs (expecting YAML, profile, template, docs, etc. as strings)
    outputs = agent_result.get("result", {})
    # Save all outputs to ArangoDB, register workflow
    workflow_doc = {
        "name": prompt[:64],
        "yaml": outputs.get("workflow_yaml") or agent_input["workflow_yaml"],
        "agent_profile": outputs.get("agent_profile") or agent_input["agent_profile"],
        "output_template": outputs.get("output_template")
        or agent_input["output_template"],
        "research_reference": outputs.get("research_reference"),
        "documentation": outputs.get("documentation"),
        "created_at": agent_result.get("created_at"),
        "metadata": {"source": "agentic_workflow_tool", "prompt": prompt},
    }
    wf_save = db.create_workflow(workflow_doc)
    workflow_id = None
    if wf_save.get("success") and wf_save.get("results"):
        workflow_id = wf_save["results"][0].get("_key")
    return {
        "success": True,
        "workflow_id": workflow_id,
        "outputs": outputs,
        "logs": agent_result.get("logs"),
    }


# --- MCP Tool Registry ---
TOOLS = [
    {
        "name": "agentic_workflow_tool",
        "description": "Generate or execute a workflow using the workflow_generation workflow and all supporting files. Input: prompt (required), workflow_id (optional).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "Prompt or use case for workflow generation/execution.",
                },
                "workflow_id": {
                    "type": "string",
                    "description": "Workflow ID to reuse (optional).",
                },
            },
            "required": ["prompt"],
        },
    },
    # Retain CRUD/listing tools for workflows and runs
    {
        "name": "get_workflow",
        "description": "Get a workflow by ID.",
        "inputSchema": {
            "type": "object",
            "properties": {"workflow_id": {"type": "string"}},
            "required": ["workflow_id"],
        },
    },
    {
        "name": "list_workflows",
        "description": "List workflows.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "skip": {"type": "integer", "default": 0},
                "limit": {"type": "integer", "default": 50},
            },
        },
    },
    {
        "name": "delete_workflow",
        "description": "Delete a workflow by ID.",
        "inputSchema": {
            "type": "object",
            "properties": {"workflow_id": {"type": "string"}},
            "required": ["workflow_id"],
        },
    },
]


def list_tools() -> list[dict[str, Any]]:
    logger.debug("list_tools called, returning %d tools", len(TOOLS))
    return TOOLS


async def handle_tool_call(name: str, arguments: dict[str, Any]) -> Any:
    logger.debug(f"handle_tool_call: {name} with arguments: {arguments}")
    try:
        if name == "agentic_workflow_tool":
            return await agentic_workflow_tool(
                arguments["prompt"], arguments.get("workflow_id")
            )
        elif name == "get_workflow":
            return db.get_workflow(arguments["workflow_id"])
        elif name == "list_workflows":
            return db.list_workflows(
                skip=arguments.get("skip", 0), limit=arguments.get("limit", 50)
            )
        elif name == "delete_workflow":
            return db.delete_workflow(arguments["workflow_id"])
        else:
            logger.error(f"Unknown tool: {name}")
            return {"success": False, "error": f"Unknown tool: {name}"}
    except Exception as e:
        logger.error(
            f"Exception in handle_tool_call for {name}: {e}\n{traceback.format_exc()}"
        )
        return {"success": False, "error": str(e), "trace": traceback.format_exc()}


async def handle_request(request: dict[str, Any]) -> dict[str, Any]:
    method = request.get("method")
    params = request.get("params", {})
    request_id = request.get("id")
    logger.debug(f"handle_request: method={method}, params={params}, id={request_id}")
    try:
        if method == "initialize":
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {
                        "name": "workflow-mcp",
                        "version": "2.0.0",
                    },
                },
            }
        elif method == "tools/list":
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"tools": TOOLS},
            }
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            logger.debug(f"Dispatching to handle_tool_call: {tool_name}")
            result = await handle_tool_call(tool_name, arguments)
            response = {"jsonrpc": "2.0", "id": request_id, "result": result}
        else:
            logger.error(f"Unknown method: {method}")
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"},
            }
        logger.debug(f"Sending response: {response}")
        return response
    except Exception as e:
        logger.error(f"Error processing request: {e}\n{traceback.format_exc()}")
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}",
                "trace": traceback.format_exc(),
            },
        }


async def main():
    logger.info(
        "Starting Workflow MCP JSON-RPC server (async stdio mode) with DEBUG logging"
    )
    try:
        while True:
            line = await asyncio.get_event_loop().run_in_executor(
                None, sys.stdin.readline
            )
            if not line:
                break
            logger.debug(f"Raw input line: {line.rstrip()}")
            try:
                request = json.loads(line.strip())
                logger.debug(f"Parsed JSON request: {request}")
                response = await handle_request(request)
                print(json.dumps(response))
                sys.stdout.flush()
            except Exception as e:
                logger.error(f"Failed to process input: {e}\n{traceback.format_exc()}")
    except KeyboardInterrupt:
        logger.info("Workflow MCP server stopped by user.")


if __name__ == "__main__":
    asyncio.run(main())
