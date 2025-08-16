"""
mcp_workflow_server.py

MCP server for workflow generation, registration, management, and execution.
- Prefect-based dynamic workflow execution
- ArangoDB for all supporting documents
- SharedLogger for logging
- MCP client registry/factory for extensibility
"""

import asyncio
import importlib
import os
from pathlib import Path
import sys
import tempfile
from typing import Any, Dict, List, Type

# --- Ensure project root is in sys.path for src.shared imports ---
project_root = Path(__file__).resolve().parents[3]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from mcp.types import TextContent

from src.shared.interfaces.database.arango_interface import DirectArangoDB
from src.shared.logging.shared_logger import SharedLogger
from src.shared.mcp.arxiv_mcp_client import ArxivMCPClient

# Import MCP clients
from src.shared.mcp.brave_mcp_search import BraveMCPSearch
from src.shared.mcp.context7_mcp_client import Context7MCPClient
from src.shared.mcp.firecrawl_mcp_client import FirecrawlMCPClient
from src.shared.mcp.mcp_server_template import (
    BaseTool,
    MCPServerTemplate,
)

# --- MCP Client Registry/Factory ---


class MCPClientRegistry:
    """
    Registry/factory for MCP server clients (Brave, Firecrawl, Context7, Arxiv, etc.).
    Allows dynamic loading and instantiation of MCP clients.
    """

    def __init__(self):
        self._registry: Dict[str, Type] = {}

    def register(self, name: str, client_cls: Type) -> None:
        self._registry[name] = client_cls

    def get(self, name: str, *args, **kwargs):
        if name not in self._registry:
            raise ValueError(f"MCP client '{name}' not registered.")
        return self._registry[name](*args, **kwargs)

    def available(self) -> List[str]:
        return list(self._registry.keys())


# --- Tool Handlers ---


class GenerateWorkflowTool(BaseTool):
    """
    Tool: generate_workflow
    Generate and register a new workflow from a prompt.
    """

    def __init__(
        self, db: DirectArangoDB, logger: SharedLogger, mcp_registry: MCPClientRegistry
    ):
        super().__init__(
            name="generate_workflow",
            description="Generate and register a new workflow from a prompt.",
            input_schema={
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "Workflow generation prompt.",
                    }
                },
                "required": ["prompt"],
            },
        )
        self.db = db
        self.logger = logger
        self.mcp_registry = mcp_registry

    async def execute(self, arguments: Dict[str, Any]) -> List[Any]:
        self.logger.debug(
            f"[generate_workflow] execute called with arguments: {arguments}"
        )
        self.validate_input(arguments)
        prompt = arguments["prompt"]
        self.logger.info(f"[generate_workflow] Prompt: {prompt}")
        templates = self.db.find_documents(
            "workflow_templates", {"type": "output_template"}
        )
        profiles = self.db.find_documents("workflow_profiles", {})
        workflow_code = f"""# Generated Prefect workflow\n# Prompt: {prompt}\nfrom prefect import flow\n@flow\ndef generated_flow():\n    print('Workflow generated from prompt: {prompt}')\n"""
        workflow_doc = {
            "type": "workflow",
            "workflow_name": f"workflow_{abs(hash(prompt)) % 100000}",
            "version": "2024-07-01",
            "code": workflow_code,
            "prompt": prompt,
        }
        self.logger.debug(f"[generate_workflow] Inserting workflow_doc: {workflow_doc}")
        result = self.db.batch_insert("workflows", [workflow_doc])
        if not result.get("success"):
            self.logger.error(f"Failed to insert workflow: {result}")
            return [
                TextContent(
                    type="text",
                    text=f"ERROR: Failed to register workflow. Details: {result}",
                )
            ]
        self.logger.info(f"Workflow registered: {workflow_doc['workflow_name']}")
        self.logger.debug(
            f"[generate_workflow] execute returning workflow_doc: {workflow_doc}"
        )
        # Return the full workflow document in a formatted block
        return [
            TextContent(
                type="text",
                text=(
                    f"SUCCESS: Workflow registered.\n"
                    f"Name: {workflow_doc['workflow_name']}\n"
                    f"Version: {workflow_doc['version']}\n"
                    f"Prompt: {workflow_doc['prompt']}\n"
                    f"Code:\n\n" + f"""```python\n{workflow_doc['code']}\n```"""
                ),
            )
        ]


class ListWorkflowsTool(BaseTool):
    """
    Tool: list_workflows
    List all registered/generated workflows.
    """

    def __init__(self, db: DirectArangoDB, logger: SharedLogger):
        super().__init__(
            name="list_workflows",
            description="List all registered/generated workflows.",
            input_schema={"type": "object", "properties": {}, "required": []},
        )
        self.db = db
        self.logger = logger

    async def execute(self, arguments: Dict[str, Any]) -> List[Any]:
        self.logger.debug(
            f"[list_workflows] execute called with arguments: {arguments}"
        )
        self.logger.info("[list_workflows] Listing workflows.")
        docs = self.db.find_documents("workflows", {})
        if not docs.get("success"):
            self.logger.error(f"Failed to list workflows: {docs}")
            return [
                TextContent(
                    type="text",
                    text=f"ERROR: Failed to list workflows. Details: {docs}",
                )
            ]
        workflows = docs.get("documents", [])
        if not workflows:
            self.logger.debug("[list_workflows] No workflows found.")
            return [TextContent(type="text", text="No workflows found.")]
        # Build a table of workflows with name, version, prompt, and code snippet
        table = [
            "| Name | Version | Prompt | Code Snippet |",
            "|------|---------|--------|--------------|",
        ]
        for wf in workflows:
            code_snippet = wf.get("code", "").split("\n")[0:2]
            code_snippet = "<br/>".join(code_snippet)
            table.append(
                f"| {wf.get('workflow_name','')} | {wf.get('version','')} | {wf.get('prompt','')[:32]} | {code_snippet} |"
            )
        self.logger.debug(
            f"[list_workflows] Returning table with {len(workflows)} workflows."
        )
        return [TextContent(type="text", text="\n".join(table))]


class DeleteWorkflowTool(BaseTool):
    """
    Tool: delete_workflow
    Delete a registered/generated workflow by name/id.
    """

    def __init__(self, db: DirectArangoDB, logger: SharedLogger):
        super().__init__(
            name="delete_workflow",
            description="Delete a registered/generated workflow by name/id.",
            input_schema={
                "type": "object",
                "properties": {
                    "workflow_id": {
                        "type": "string",
                        "description": "Workflow name or ID.",
                    }
                },
                "required": ["workflow_id"],
            },
        )
        self.db = db
        self.logger = logger

    async def execute(self, arguments: Dict[str, Any]) -> List[Any]:
        self.logger.debug(
            f"[delete_workflow] execute called with arguments: {arguments}"
        )
        self.validate_input(arguments)
        workflow_id = arguments["workflow_id"]
        # Try to fetch workflow before deletion for metadata
        docs = self.db.find_documents("workflows", {"workflow_name": workflow_id})
        workflow = None
        if docs.get("success") and docs.get("documents"):
            workflow = docs["documents"][0]
        else:
            docs_by_key = self.db.find_documents("workflows", {"_key": workflow_id})
            if docs_by_key.get("success") and docs_by_key.get("documents"):
                workflow = docs_by_key["documents"][0]
        self.logger.debug(f"[delete_workflow] Deleting workflow: {workflow_id}")
        result = self.db.delete_document("workflows", workflow_id)
        if not result.get("success") and workflow:
            # Try deleting by _key if not already done
            key = workflow.get("_key")
            if key:
                result = self.db.delete_document("workflows", key)
        if not result.get("success"):
            self.logger.error(f"Failed to delete workflow: {result}")
            return [
                TextContent(
                    type="text",
                    text=f"ERROR: Failed to delete workflow. Details: {result}",
                )
            ]
        self.logger.info(f"Workflow deleted: {workflow_id}")
        self.logger.debug(
            f"[delete_workflow] execute returning metadata for workflow: {workflow_id}"
        )
        # Return deleted workflow metadata if available
        if workflow:
            return [
                TextContent(
                    type="text",
                    text=(
                        f"SUCCESS: Workflow deleted.\n"
                        f"Name: {workflow.get('workflow_name')}\n"
                        f"Prompt: {workflow.get('prompt')}\n"
                        f"Version: {workflow.get('version')}"
                    ),
                )
            ]
        else:
            return [
                TextContent(
                    type="text", text=f"SUCCESS: Workflow deleted: {workflow_id}"
                )
            ]


class RunWorkflowTool(BaseTool):
    """
    Tool: run_workflow
    Execute a registered/generated workflow (by name/id, with parameters).
    """

    def __init__(
        self, db: DirectArangoDB, logger: SharedLogger, mcp_registry: MCPClientRegistry
    ):
        super().__init__(
            name="run_workflow",
            description="Execute a registered/generated workflow (by name/id, with parameters).",
            input_schema={
                "type": "object",
                "properties": {
                    "workflow_id": {
                        "type": "string",
                        "description": "Workflow name or ID.",
                    },
                    "parameters": {
                        "type": "object",
                        "description": "Parameters for the workflow.",
                    },
                },
                "required": ["workflow_id"],
            },
        )
        self.db = db
        self.logger = logger
        self.mcp_registry = mcp_registry

    async def execute(self, arguments: Dict[str, Any]) -> List[Any]:
        self.logger.debug(f"[run_workflow] execute called with arguments: {arguments}")
        self.validate_input(arguments)
        workflow_id = arguments["workflow_id"]
        parameters = arguments.get("parameters", {})
        # Try by workflow_name first
        docs = self.db.find_documents("workflows", {"workflow_name": workflow_id})
        workflow = None
        if docs.get("success") and docs.get("documents"):
            workflow = docs["documents"][0]
        else:
            # Try by _key if not found by name
            docs_by_key = self.db.find_documents("workflows", {"_key": workflow_id})
            if docs_by_key.get("success") and docs_by_key.get("documents"):
                workflow = docs_by_key["documents"][0]
        if not workflow:
            self.logger.error(f"Workflow not found: {workflow_id}")
            return [
                TextContent(
                    type="text", text=f"ERROR: Workflow not found: {workflow_id}"
                )
            ]
        code = workflow.get("code")
        if not code:
            self.logger.error(f"No code found for workflow: {workflow_id}")
            return [
                TextContent(
                    type="text",
                    text=f"ERROR: No code found for workflow: {workflow_id}",
                )
            ]
        self.logger.debug(f"[run_workflow] Executing workflow code for: {workflow_id}")
        with tempfile.TemporaryDirectory() as tmpdir:
            module_path = Path(tmpdir) / "generated_workflow.py"
            with open(module_path, "w") as f:
                f.write(code)
            sys.path.insert(0, str(tmpdir))
            try:
                module = importlib.import_module("generated_workflow")
                importlib.reload(module)
                flow_func = getattr(module, "generated_flow", None)
                if not flow_func:
                    self.logger.error("No 'generated_flow' found in workflow module.")
                    return [
                        TextContent(
                            type="text",
                            text="ERROR: No 'generated_flow' found in workflow module.",
                        )
                    ]
                self.logger.debug(
                    f"[run_workflow] Calling generated_flow with parameters: {parameters}"
                )
                result = flow_func(**parameters) if parameters else flow_func()
                exec_log = {
                    "workflow_id": workflow_id,
                    "parameters": parameters,
                    "result": str(result),
                }
                self.db.batch_insert("workflow_logs", [exec_log])
                self.logger.info(f"Workflow executed: {workflow_id}")
                self.logger.debug(f"[run_workflow] Execution result: {result}")
                # Return code and execution result
                return [
                    TextContent(
                        type="text",
                        text=(
                            f"SUCCESS: Workflow executed.\n"
                            f"Name: {workflow.get('workflow_name')}\n"
                            f"Prompt: {workflow.get('prompt')}\n"
                            f"Code:\n\n"
                            + f"""```python\n{code}\n```"""
                            + f"\nResult: {result}"
                        ),
                    )
                ]
            except Exception as e:
                self.logger.error(f"Workflow execution failed: {e}")
                return [
                    TextContent(
                        type="text", text=f"ERROR: Workflow execution failed: {e}"
                    )
                ]
            finally:
                sys.path.pop(0)


# --- Main MCP Workflow Server ---


def main():
    # Initialize logger with file/console options from env vars
    log_to_file = os.getenv("LOG_TO_FILE", "false").lower() == "true"
    log_file = os.getenv("LOG_FILE", "workflow_mcp.log")
    log_rotation = None
    if os.getenv("LOG_ROTATION_MAXBYTES"):
        log_rotation = {
            "maxBytes": int(os.getenv("LOG_ROTATION_MAXBYTES")),
            "backupCount": int(os.getenv("LOG_ROTATION_BACKUPCOUNT", 5)),
        }
    elif os.getenv("LOG_ROTATION_WHEN"):
        log_rotation = {
            "when": os.getenv("LOG_ROTATION_WHEN"),
            "backupCount": int(os.getenv("LOG_ROTATION_BACKUPCOUNT", 7)),
        }
    logger = SharedLogger(
        name="workflow_mcp",
        level=os.getenv("LOG_LEVEL", "INFO"),
        log_to_console=True,
        log_to_file=log_to_file,
        log_file=log_file,
        rotation=log_rotation,
    )
    # Initialize DB
    db = DirectArangoDB()
    # Initialize MCP client registry
    mcp_registry = MCPClientRegistry()
    # Register available MCP clients
    mcp_registry.register("brave", BraveMCPSearch)
    mcp_registry.register("firecrawl", FirecrawlMCPClient)
    mcp_registry.register("context7", Context7MCPClient)
    mcp_registry.register("arxiv", ArxivMCPClient)
    # Register tools
    tools = [
        GenerateWorkflowTool(db, logger, mcp_registry),
        ListWorkflowsTool(db, logger),
        DeleteWorkflowTool(db, logger),
        RunWorkflowTool(db, logger, mcp_registry),
    ]
    # Start MCP server
    server = MCPServerTemplate(name="workflow_mcp_server", tools=tools)
    asyncio.run(server.run())


if __name__ == "__main__":
    main()
