"""
Cursor Agent MCP Server Implementation

Provides programmatic access to Cursor IDE agents through MCP tools.
"""

import asyncio
import json
import os
import subprocess
import uuid
import time
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
import logging
import websockets
import aiofiles
from datetime import datetime

from fastmcp import FastMCP

from .config import CursorConfig
from .models import (
    AgentRequest,
    AgentResponse,
    DiagramRequest,
    AgentJob,
    CursorAgent,
    AgentType,
    DiagramType,
    CommunicationMethod,
)

logger = logging.getLogger(__name__)


class CursorAgentServer:
    """MCP Server for Cursor IDE agent interactions"""

    def __init__(self, config: Optional[CursorConfig] = None):
        self.config = config or CursorConfig()
        self.mcp = FastMCP("cursor-agent-server")
        self.active_jobs: Dict[str, AgentJob] = {}
        self.websocket_connection = None

        # Setup MCP tools
        self._setup_tools()

        # Initialize communication method
        self._init_communication()

    def _init_communication(self):
        """Initialize the communication method with Cursor"""

        if self.config.communication_method == "file":
            # Setup file watcher
            os.makedirs(self.config.file_watch_dir, exist_ok=True)
            os.makedirs(self.config.output_dir, exist_ok=True)
        elif self.config.communication_method == "pipe" and os.name != "nt":
            # Create named pipe if it doesn't exist
            if not os.path.exists(self.config.pipe_path):
                os.mkfifo(self.config.pipe_path)

    def _setup_tools(self):
        """Register MCP tools for Cursor agent operations"""

        @self.mcp.tool()
        async def invoke_cursor_agent(
            agent: str,
            prompt: str,
            context: Optional[Dict[str, Any]] = None,
            files: Optional[List[str]] = None,
            timeout: Optional[int] = None,
        ) -> Dict[str, Any]:
            """
            Invoke a Cursor IDE agent programmatically.

            Args:
                agent: Agent name (e.g., "@diagram", "@code_review")
                prompt: Prompt for the agent
                context: Additional context data
                files: Files to include as context
                timeout: Timeout in seconds

            Returns:
                Agent response with results
            """

            # Check if agent is allowed
            if not self.config.is_agent_allowed(agent):
                return {"success": False, "error": f"Agent {agent} is not allowed"}

            request = AgentRequest(
                agent=agent,
                prompt=prompt,
                context=context,
                files=files,
                timeout=timeout or self.config.agent_timeout,
                request_id=str(uuid.uuid4()),
            )

            response = await self._invoke_agent(request)
            return response.dict()

        @self.mcp.tool()
        async def create_diagram(
            data: Union[str, Dict, List],
            diagram_type: str = "auto",
            title: Optional[str] = None,
            theme: str = "high-contrast",
            format: str = "mermaid",
        ) -> Dict[str, Any]:
            """
            Create a diagram using Cursor's @diagram agent.

            Args:
                data: Data to visualize
                diagram_type: Type of diagram (auto, flowchart, sequence, etc.)
                title: Diagram title
                theme: Visual theme
                format: Output format (mermaid, svg, png)

            Returns:
                Diagram code and optionally rendered output
            """

            diagram_request = DiagramRequest(
                data=data,
                diagram_type=DiagramType(diagram_type),
                title=title,
                theme=theme,
                format=format,
            )

            # Build prompt for diagram agent
            prompt = self._build_diagram_prompt(diagram_request)

            request = AgentRequest(
                agent="@diagram",
                prompt=prompt,
                diagram_type=diagram_request.diagram_type,
                diagram_theme=diagram_request.theme,
                output_format=format,
                context={"diagram_request": diagram_request.dict()},
            )

            response = await self._invoke_agent(request)
            return response.dict()

        @self.mcp.tool()
        async def review_code(
            code: str,
            language: Optional[str] = None,
            focus_areas: Optional[List[str]] = None,
            files: Optional[List[str]] = None,
        ) -> Dict[str, Any]:
            """
            Review code using Cursor's @code_review agent.

            Args:
                code: Code to review
                language: Programming language
                focus_areas: Areas to focus on (security, performance, etc.)
                files: Related files for context

            Returns:
                Code review feedback
            """

            prompt = f"""Review this {language or 'code'}:
            
```{language or ''}
{code}
```

Focus areas: {', '.join(focus_areas) if focus_areas else 'general quality'}"""

            request = AgentRequest(
                agent="@code_review",
                prompt=prompt,
                files=files,
                context={"language": language, "focus_areas": focus_areas},
            )

            response = await self._invoke_agent(request)
            return response.dict()

        @self.mcp.tool()
        async def generate_documentation(
            code: str,
            language: Optional[str] = None,
            doc_style: str = "markdown",
            files: Optional[List[str]] = None,
        ) -> Dict[str, Any]:
            """
            Generate documentation using Cursor's @documentation agent.

            Args:
                code: Code to document
                language: Programming language
                doc_style: Documentation style (markdown, jsdoc, docstring)
                files: Related files for context

            Returns:
                Generated documentation
            """

            prompt = f"""Generate {doc_style} documentation for this {language or 'code'}:
            
```{language or ''}
{code}
```"""

            request = AgentRequest(
                agent="@documentation",
                prompt=prompt,
                files=files,
                context={"language": language, "style": doc_style},
            )

            response = await self._invoke_agent(request)
            return response.dict()

        @self.mcp.tool()
        async def invoke_custom_agent(
            agent_name: str,
            prompt: str,
            custom_prompt_file: Optional[str] = None,
            context: Optional[Dict[str, Any]] = None,
        ) -> Dict[str, Any]:
            """
            Invoke a custom Cursor agent from .cursor/prompts directory.

            Args:
                agent_name: Name of custom agent (without @ prefix)
                prompt: Prompt for the agent
                custom_prompt_file: Path to custom prompt file
                context: Additional context

            Returns:
                Agent response
            """

            # Load custom prompt if provided
            custom_prompt = None
            if custom_prompt_file:
                prompt_path = Path(self.config.custom_agents_dir) / custom_prompt_file
                if prompt_path.exists():
                    with open(prompt_path, "r") as f:
                        custom_prompt = f.read()

            agent = CursorAgent(
                name=f"@{agent_name}",
                type=AgentType.CUSTOM,
                description=f"Custom agent: {agent_name}",
                custom_prompt=custom_prompt,
            )

            request = AgentRequest(agent=agent.name, prompt=prompt, context=context)

            response = await self._invoke_agent(request)
            return response.dict()

        @self.mcp.tool()
        async def list_available_agents() -> Dict[str, Any]:
            """
            List all available Cursor agents.

            Returns:
                List of available agents with descriptions
            """

            agents = []

            # Add default agents
            for agent_name in self.config.default_agents:
                if self.config.is_agent_allowed(agent_name):
                    agents.append(
                        {"name": agent_name, "type": "default", "available": True}
                    )

            # Add custom agents from prompts directory
            prompts_dir = Path(self.config.custom_agents_dir)
            if prompts_dir.exists():
                for prompt_file in prompts_dir.glob("*.md"):
                    agent_name = f"@{prompt_file.stem}"
                    if self.config.is_agent_allowed(agent_name):
                        agents.append(
                            {
                                "name": agent_name,
                                "type": "custom",
                                "file": str(prompt_file),
                                "available": True,
                            }
                        )

            return {"success": True, "agents": agents, "total": len(agents)}

        @self.mcp.tool()
        async def get_agent_status(job_id: str) -> Dict[str, Any]:
            """
            Get status of an async agent invocation.

            Args:
                job_id: Job ID from async invocation

            Returns:
                Job status and results if complete
            """

            if job_id in self.active_jobs:
                job = self.active_jobs[job_id]
                return {
                    "success": True,
                    "job_id": job_id,
                    "status": job.status,
                    "agent": job.agent,
                    "created_at": job.created_at.isoformat(),
                    "completed_at": job.completed_at.isoformat()
                    if job.completed_at
                    else None,
                    "response": job.response.dict() if job.response else None,
                }

            # Check for completed job in output directory
            output_file = Path(self.config.output_dir) / f"{job_id}.json"
            if output_file.exists():
                with open(output_file, "r") as f:
                    data = json.load(f)
                    return {
                        "success": True,
                        "job_id": job_id,
                        "status": "completed",
                        "response": data,
                    }

            return {"success": False, "error": f"Job {job_id} not found"}

    async def _invoke_agent(self, request: AgentRequest) -> AgentResponse:
        """Invoke a Cursor agent using configured communication method"""

        start_time = time.time()

        try:
            if self.config.communication_method == CommunicationMethod.WEBSOCKET:
                response = await self._invoke_via_websocket(request)
            elif self.config.communication_method == CommunicationMethod.FILE:
                response = await self._invoke_via_file(request)
            elif self.config.communication_method == CommunicationMethod.PIPE:
                response = await self._invoke_via_pipe(request)
            else:  # CLI
                response = await self._invoke_via_cli(request)

            response.execution_time = time.time() - start_time
            return response

        except Exception as e:
            logger.error(f"Failed to invoke agent {request.agent}: {e}")
            return AgentResponse(
                success=False,
                agent=request.agent,
                error=str(e),
                execution_time=time.time() - start_time,
                request_id=request.request_id,
            )

    async def _invoke_via_websocket(self, request: AgentRequest) -> AgentResponse:
        """Invoke agent via WebSocket connection"""

        uri = f"ws://{self.config.websocket_host}:{self.config.websocket_port}/cursor-agent"

        try:
            async with websockets.connect(uri) as websocket:
                # Send request
                await websocket.send(
                    json.dumps({"action": "invoke_agent", "request": request.dict()})
                )

                # Wait for response with timeout
                response_data = await asyncio.wait_for(
                    websocket.recv(),
                    timeout=request.timeout or self.config.agent_timeout,
                )

                response = json.loads(response_data)
                return AgentResponse(**response)

        except asyncio.TimeoutError:
            raise Exception(f"Agent invocation timed out after {request.timeout}s")
        except Exception as e:
            raise Exception(f"WebSocket communication failed: {e}")

    async def _invoke_via_file(self, request: AgentRequest) -> AgentResponse:
        """Invoke agent via file-based communication"""

        job_id = request.request_id or str(uuid.uuid4())

        # Write request file
        request_file = Path(self.config.file_watch_dir) / f"{job_id}_request.json"
        async with aiofiles.open(request_file, "w") as f:
            await f.write(json.dumps(request.dict(), indent=2))

        # Create job for tracking
        job = AgentJob(
            job_id=job_id,
            agent=request.agent,
            status="pending",
            request=request,
            output_file=str(Path(self.config.output_dir) / f"{job_id}_response.json"),
        )
        self.active_jobs[job_id] = job

        # Poll for response
        response_file = Path(self.config.output_dir) / f"{job_id}_response.json"
        timeout = request.timeout or self.config.agent_timeout
        start_time = time.time()

        while time.time() - start_time < timeout:
            if response_file.exists():
                async with aiofiles.open(response_file, "r") as f:
                    data = json.loads(await f.read())
                    response = AgentResponse(**data)

                    # Update job
                    job.status = "completed"
                    job.response = response
                    job.completed_at = datetime.now()

                    # Cleanup request file
                    request_file.unlink(missing_ok=True)

                    return response

            await asyncio.sleep(1)

        # Timeout
        job.status = "timeout"
        raise Exception(f"Agent invocation timed out after {timeout}s")

    async def _invoke_via_pipe(self, request: AgentRequest) -> AgentResponse:
        """Invoke agent via named pipe"""

        if os.name == "nt":
            raise Exception("Named pipes not supported on Windows")

        # Write to pipe
        pipe_data = json.dumps({"action": "invoke_agent", "request": request.dict()})

        async with aiofiles.open(self.config.pipe_path, "w") as pipe:
            await pipe.write(pipe_data)

        # Read response from response pipe
        response_pipe = f"{self.config.pipe_path}_response"
        if not os.path.exists(response_pipe):
            os.mkfifo(response_pipe)

        async with aiofiles.open(response_pipe, "r") as pipe:
            response_data = await asyncio.wait_for(
                pipe.read(), timeout=request.timeout or self.config.agent_timeout
            )

            response = json.loads(response_data)
            return AgentResponse(**response)

    async def _invoke_via_cli(self, request: AgentRequest) -> AgentResponse:
        """Invoke agent via Cursor CLI"""

        # Build CLI command
        cmd = [self.config.cursor_executable]

        if self.config.cursor_profile:
            cmd.extend(["--profile", self.config.cursor_profile])

        cmd.extend(["--chat", request.agent, request.prompt])

        # Add context files if provided
        if request.files:
            for file in request.files[: self.config.max_context_files]:
                cmd.extend(["--file", file])

        # Execute command
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=request.workspace or self.config.cursor_workspace,
        )

        # Wait for completion with timeout
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=request.timeout or self.config.agent_timeout,
            )

            if process.returncode == 0:
                return AgentResponse(
                    success=True,
                    agent=request.agent,
                    result=stdout.decode(),
                    request_id=request.request_id,
                )
            else:
                return AgentResponse(
                    success=False,
                    agent=request.agent,
                    error=stderr.decode(),
                    request_id=request.request_id,
                )

        except asyncio.TimeoutError:
            process.kill()
            raise Exception(f"CLI invocation timed out")

    def _build_diagram_prompt(self, diagram_request: DiagramRequest) -> str:
        """Build prompt for diagram agent"""

        prompt_parts = []

        if diagram_request.title:
            prompt_parts.append(f"Create a diagram titled: {diagram_request.title}")
        else:
            prompt_parts.append("Create a diagram for the following:")

        # Add data
        if isinstance(diagram_request.data, str):
            prompt_parts.append(diagram_request.data)
        else:
            prompt_parts.append(json.dumps(diagram_request.data, indent=2))

        # Add requirements
        requirements = []

        if diagram_request.diagram_type != DiagramType.AUTO:
            requirements.append(f"Type: {diagram_request.diagram_type.value}")

        if diagram_request.high_contrast:
            requirements.append("Use high contrast colors (WCAG AAA)")

        if diagram_request.color_blind_safe:
            requirements.append("Use color-blind safe palette")

        if diagram_request.alt_text:
            requirements.append(f"Alt text: {diagram_request.alt_text}")

        if requirements:
            prompt_parts.append("\nRequirements:")
            prompt_parts.extend([f"- {req}" for req in requirements])

        return "\n".join(prompt_parts)

    async def run(self):
        """Run the MCP server"""
        await self.mcp.run()


# Entry point for running as standalone server
if __name__ == "__main__":
    import asyncio

    server = CursorAgentServer()
    asyncio.run(server.run())
