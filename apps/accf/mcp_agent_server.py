import asyncio
import logging
from typing import Any, Dict, List

from capabilities.challenge_agent import ChallengeAgent
from capabilities.check_me_agent import CheckMeAgent
from capabilities.collaboration_agent import CollaborationAgent
from capabilities.consult_agent import ConsultAgent
from capabilities.critique_agent import CritiqueAgent
from capabilities.documentation_agent import DocumentationAgent
from capabilities.documentation_bundle_agent import (
    DocumentationBundleAgent,
)
from capabilities.knowledge_agent import KnowledgeAgent
from capabilities.memory_agent import MemoryAgent
from capabilities.research_agent import ResearchAgent
from capabilities.self_reflection_agent import SelfReflectionAgent
from capabilities.testing_agent import TestingAgent
from shared.mcp.mcp_server_template import BaseTool, MCPServerTemplate, TextContent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ACCF_MCP")

# print(f"[ACCF MCP] mcp_agent_server.py VERSION=2024-07-01 WORKDIR={os.getcwd()} PYTHON={os.environ.get('PYTHONPATH','')} OPENAI_API_KEY={'set' if os.environ.get('OPENAI_API_KEY') else 'unset'}")

# --- Tool Wrappers ---


class MemoryAgentTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="memory",
            description="Memory agent tool.",
            input_schema={
                "type": "object",
                "properties": {"prompt": {"type": "string"}},
                "required": ["prompt"],
            },
        )
        self.agent = MemoryAgent()

    async def execute(self, arguments: Dict[str, Any]) -> List[TextContent]:
        print(
            f"[ACCF MCP] MemoryAgentTool.execute VERSION=2024-07-01 arguments={arguments}"
        )
        result = self.agent.answer(arguments["prompt"])
        return [TextContent(type="text", text=str(result))]


class KnowledgeAgentTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="knowledge",
            description="Knowledge agent tool.",
            input_schema={
                "type": "object",
                "properties": {"prompt": {"type": "string"}},
                "required": ["prompt"],
            },
        )
        self.agent = KnowledgeAgent()

    async def execute(self, arguments: Dict[str, Any]) -> List[TextContent]:
        print(
            f"[ACCF MCP] KnowledgeAgentTool.execute VERSION=2024-07-01 arguments={arguments}"
        )
        result = self.agent.answer(arguments["prompt"])
        return [TextContent(type="text", text=str(result))]


class TestingAgentTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="testing",
            description="Testing agent tool.",
            input_schema={
                "type": "object",
                "properties": {"prompt": {"type": "string"}},
                "required": ["prompt"],
            },
        )
        self.agent = TestingAgent()

    async def execute(self, arguments: Dict[str, Any]) -> List[TextContent]:
        print(
            f"[ACCF MCP] TestingAgentTool.execute VERSION=2024-07-01 arguments={arguments}"
        )
        result = self.agent.test(arguments["prompt"])
        return [TextContent(type="text", text=str(result))]


class ResearchAgentTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="research",
            description="Research agent tool with full multi-source research capabilities including web search, academic papers, and technical documentation.",
            input_schema={
                "type": "object",
                "properties": {"question": {"type": "string"}},
                "required": ["question"],
            },
        )
        self.agent = ResearchAgent()

    async def execute(self, arguments: Dict[str, Any]) -> List[TextContent]:
        print(
            f"[ACCF MCP] ResearchAgentTool.execute VERSION=2024-07-01 arguments={arguments}"
        )
        # Use the full research pipeline instead of static canned answers
        result = self.agent.answer_question_with_external_tools(arguments["question"])
        return [TextContent(type="text", text=str(result))]


class DocumentationAgentTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="documentation",
            description="Documentation agent tool.",
            input_schema={
                "type": "object",
                "properties": {"prompt": {"type": "string"}},
                "required": ["prompt"],
            },
        )
        self.agent = DocumentationAgent()

    async def execute(self, arguments: Dict[str, Any]) -> List[TextContent]:
        print(
            f"[ACCF MCP] DocumentationAgentTool.execute VERSION=2024-07-01 arguments={arguments}"
        )
        result = self.agent.generate(arguments["prompt"])
        return [TextContent(type="text", text=str(result))]


class ConsultAgentTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="consult",
            description="Expert prompt engineer for generating detailed, actionable prompts for GPT-4.1 development agents. Leverages o3's reasoning capabilities to create comprehensive prompts that guide GPT-4.1 agents through complex development tasks.",
            input_schema={
                "type": "object",
                "properties": {
                    "prompt": {"type": "string"},
                    "session_id": {"type": "string"},
                    "file_paths": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of absolute file paths to attach to the request",
                    },
                    "artifact_type": {
                        "type": "string",
                        "enum": [
                            "answer",
                            "plan",
                            "code",
                            "prompt",
                            "test",
                            "doc",
                            "diagram",
                            "query",
                            "rule",
                            "config",
                            "schema",
                            "workflow",
                            "docker",
                            "env",
                        ],
                        "description": "Optional artifact type for targeted output generation",
                    },
                    "iterate": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 3,
                        "description": "Number of iterations to improve the response (1-3). Each iteration reviews and enhances the previous response.",
                    },
                    "critic_enabled": {
                        "type": "boolean",
                        "description": "Enable critic/reviewer agent to check response quality. Uses fast model to catch major errors and issues.",
                    },
                    "model": {
                        "type": "string",
                        "enum": [
                            "o4-mini",
                            "o3",
                            "gpt-4.1-mini",
                            "gpt-4.1",
                            "gpt-4.1-nano",
                        ],
                        "description": "OpenAI model to use for the consult request. Only approved models are accepted per @953-openai-api-standards.mdc",
                    },
                },
                "required": ["prompt"],
            },
        )
        self.agent = ConsultAgent()

    async def execute(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """
        Execute Architect agent for generating detailed, actionable prompts for GPT-4.1 development agents.
        Analyzes user requests and creates comprehensive prompts optimized for GPT-4.1's capabilities and limitations.
        Supports file analysis and maintains session context for ongoing prompt engineering discussions.
        """
        prompt = arguments["prompt"]
        session_id = arguments.get("session_id", "default")
        file_paths = arguments.get("file_paths", None)
        artifact_type = arguments.get("artifact_type", None)
        iterate = arguments.get("iterate", None)
        critic_enabled = arguments.get("critic_enabled", False)
        model = arguments.get("model", None)  # Default to None to use agent's default

        result = self.agent.answer(
            prompt,
            session_id=session_id,
            file_paths=file_paths,
            artifact_type=artifact_type,
            iterate=iterate,
            critic_enabled=critic_enabled,
            model=model,
        )

        # Include debug details in the response
        response_text = result.get("result", "")
        if result.get("details"):
            response_text += "\n\n=== DEBUG DETAILS ===\n"
            for detail in result["details"]:
                response_text += f"- {detail}\n"
            response_text += "=== END DEBUG DETAILS ===\n"

        return [TextContent(type="text", text=response_text)]


class ChallengeAgentTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="challenge",
            description="Challenge agent tool.",
            input_schema={
                "type": "object",
                "properties": {"prompt": {"type": "string"}},
                "required": ["prompt"],
            },
        )
        self.agent = ChallengeAgent()

    async def execute(self, arguments: Dict[str, Any]) -> List[TextContent]:
        result = self.agent.answer(arguments["prompt"])
        return [TextContent(type="text", text=str(result))]


class CritiqueAgentTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="critique",
            description="Critique agent tool.",
            input_schema={
                "type": "object",
                "properties": {"prompt": {"type": "string"}},
                "required": ["prompt"],
            },
        )
        self.agent = CritiqueAgent()

    async def execute(self, arguments: Dict[str, Any]) -> List[TextContent]:
        result = self.agent.answer(arguments["prompt"])
        return [TextContent(type="text", text=str(result))]


class CheckMeAgentTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="check_me",
            description="CheckMe agent tool.",
            input_schema={
                "type": "object",
                "properties": {
                    "prompt": {"type": "string"},
                    "session_id": {"type": "string"},
                },
                "required": ["prompt"],
            },
        )
        self.agent = CheckMeAgent()

    async def execute(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """
        Execute CheckMeAgent with session support. If session_id is not provided, use 'default'.
        """
        prompt = arguments["prompt"]
        session_id = arguments.get("session_id", "default")
        result = self.agent.answer(prompt, session_id=session_id)
        return [TextContent(type="text", text=str(result))]


class CollaborationAgentTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="collaboration",
            description="Collaboration agent tool.",
            input_schema={
                "type": "object",
                "properties": {"message": {"type": "object"}},
                "required": ["message"],
            },
        )
        self.agent = CollaborationAgent()

    async def execute(self, arguments: Dict[str, Any]) -> List[TextContent]:
        result = self.agent.collaborate(arguments["message"])
        return [TextContent(type="text", text=str(result))]


class SelfReflectionAgentTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="self_reflection",
            description="Self-Reflection agent tool.",
            input_schema={
                "type": "object",
                "properties": {"context": {"type": "object"}},
                "required": ["context"],
            },
        )
        self.agent = SelfReflectionAgent()

    async def execute(self, arguments: Dict[str, Any]) -> List[TextContent]:
        result = self.agent.reflect(arguments["context"])
        return [TextContent(type="text", text=str(result))]


class DocsBundleAgentTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="docs_bundle",
            description="Documentation bundle generator tool.",
            input_schema={
                "type": "object",
                "properties": {
                    "prompt": {"type": "string"},
                    "mode": {"type": "string", "enum": ["parallel", "sequential"]},
                },
                "required": ["prompt", "mode"],
            },
        )
        self.agent = DocumentationBundleAgent()

    async def execute(self, arguments: Dict[str, Any]) -> List[TextContent]:
        prompt = arguments["prompt"]
        mode = arguments.get("mode", "parallel")
        bundle = await self.agent.generate_docs_bundle(prompt, mode)
        return [TextContent(type="text", text=bundle.json())]


# --- Server Startup ---

# Check if specific agent type is requested via environment variable
import os

agent_type = os.getenv("AGENT_TYPE", "").lower()

if agent_type == "consult":
    # Only expose the consult agent for o3_agent MCP server
    tools = [ConsultAgentTool()]
    server_name = "ACCF Consult Agent MCP Server"
else:
    # Expose all agents for collab_agents MCP server
    tools = [
        MemoryAgentTool(),
        KnowledgeAgentTool(),
        TestingAgentTool(),
        ResearchAgentTool(),
        DocumentationAgentTool(),
        ConsultAgentTool(),
        ChallengeAgentTool(),
        CritiqueAgentTool(),
        CheckMeAgentTool(),
        CollaborationAgentTool(),
        SelfReflectionAgentTool(),
        DocsBundleAgentTool(),
    ]
    server_name = "ACCF Agent Team MCP Server"


async def main():
    server = MCPServerTemplate(name=server_name, tools=tools)
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())

print(
    "[ACCF MCP] mcp_agent_server.py loaded. If you see this, script reached end of file."
)
