"""
Agent Discovery Infrastructure
Implements Agent Protocol, ANS (Agent Name Service), and service registry
for AI agent discovery and inter-agent communication.

Based on OWASP ANS v1.0 and Agent Protocol standards.
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)


# Agent Protocol Models (standardized schemas)
class TaskInput(BaseModel):
    input: str | None = None
    additional_input: dict[str, Any] | None = {}


class Task(BaseModel):
    task_id: str
    input: str | None = None
    additional_input: dict[str, Any] | None = {}
    artifacts: list[dict] = []
    steps: list[dict] = []
    created_at: str
    status: str = "created"


class StepInput(BaseModel):
    input: str | None = None
    additional_input: dict[str, Any] | None = {}


class Step(BaseModel):
    task_id: str
    step_id: str
    input: str | None = None
    additional_input: dict[str, Any] | None = {}
    name: str | None = None
    status: str = "created"
    output: str | None = None
    additional_output: dict[str, Any] | None = {}
    artifacts: list[dict] = []
    is_last: bool = False
    created_at: str


class AgentCapability(BaseModel):
    """Describes agent capabilities for discovery"""

    name: str
    description: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    tags: list[str] = []
    version: str = "1.0"


class AgentManifest(BaseModel):
    """Agent service manifest for discovery"""

    agent_id: str
    name: str
    description: str
    version: str
    provider: str
    protocol: str = "agent-protocol"
    endpoints: dict[str, str]
    capabilities: list[AgentCapability]
    authentication: dict[str, Any] = {}
    metadata: dict[str, Any] = {}


class AgentDiscoveryService:
    """Service for agent discovery, registration, and protocol compliance"""

    def __init__(self, app: FastAPI):
        self.app = app
        self.tasks: dict[str, Task] = {}
        self.steps: dict[str, dict[str, Step]] = {}  # task_id -> step_id -> step
        self.agent_registry: dict[str, AgentManifest] = {}
        self.setup_routes()

    def setup_routes(self):
        """Setup Agent Protocol compliant endpoints"""

        # Agent Protocol Core Endpoints
        @self.app.post("/ap/v1/agent/tasks")
        async def create_task(task_input: TaskInput) -> Task:
            """Create new task (Agent Protocol standard)"""
            task_id = str(uuid.uuid4())
            task = Task(
                task_id=task_id,
                input=task_input.input,
                additional_input=task_input.additional_input,
                created_at=datetime.now(timezone.utc).isoformat(),
            )
            self.tasks[task_id] = task
            self.steps[task_id] = {}

            logger.info(f"Created task {task_id}")
            return task

        @self.app.get("/ap/v1/agent/tasks/{task_id}")
        async def get_task(task_id: str) -> Task:
            """Get task details"""
            if task_id not in self.tasks:
                raise HTTPException(status_code=404, detail="Task not found")
            return self.tasks[task_id]

        @self.app.get("/ap/v1/agent/tasks")
        async def list_tasks(current_page: int = 1, page_size: int = 10):
            """List all tasks"""
            start = (current_page - 1) * page_size
            end = start + page_size
            task_list = list(self.tasks.values())[start:end]
            return {
                "tasks": task_list,
                "pagination": {
                    "current_page": current_page,
                    "page_size": page_size,
                    "total": len(self.tasks),
                },
            }

        @self.app.post("/ap/v1/agent/tasks/{task_id}/steps")
        async def create_step(task_id: str, step_input: StepInput) -> Step:
            """Execute step in task"""
            if task_id not in self.tasks:
                raise HTTPException(status_code=404, detail="Task not found")

            # Get the original task to inherit its additional_input
            task = self.tasks[task_id]

            # Merge task's additional_input with step's additional_input
            # Step input takes precedence over task input for same keys
            merged_additional_input = {
                **task.additional_input,
                **step_input.additional_input,
            }

            step_id = str(uuid.uuid4())
            step = Step(
                task_id=task_id,
                step_id=step_id,
                input=step_input.input,
                additional_input=merged_additional_input,
                created_at=datetime.now(timezone.utc).isoformat(),
            )

            # Delegate to our agent hub
            try:
                result = await self._execute_agent_step(task_id, step)
                step.output = result.get("output", "Step completed")
                step.status = "completed"
                step.is_last = result.get("is_last", True)
            except Exception as e:
                step.output = f"Error: {str(e)}"
                step.status = "failed"
                step.is_last = True

            self.steps[task_id][step_id] = step
            return step

        @self.app.get("/ap/v1/agent/tasks/{task_id}/steps")
        async def list_steps(task_id: str, current_page: int = 1, page_size: int = 10):
            """List steps for task"""
            if task_id not in self.tasks:
                raise HTTPException(status_code=404, detail="Task not found")

            steps = list(self.steps[task_id].values())
            start = (current_page - 1) * page_size
            end = start + page_size
            return {
                "steps": steps[start:end],
                "pagination": {
                    "current_page": current_page,
                    "page_size": page_size,
                    "total": len(steps),
                },
            }

        @self.app.get("/ap/v1/agent/tasks/{task_id}/steps/{step_id}")
        async def get_step(task_id: str, step_id: str) -> Step:
            """Get step details"""
            if task_id not in self.tasks:
                raise HTTPException(status_code=404, detail="Task not found")
            if step_id not in self.steps[task_id]:
                raise HTTPException(status_code=404, detail="Step not found")
            return self.steps[task_id][step_id]

        # Service Discovery Endpoints
        @self.app.get("/discovery/manifest")
        async def get_agent_manifest() -> AgentManifest:
            """Get agent service manifest for discovery"""
            return self._generate_manifest()

        @self.app.get("/discovery/capabilities")
        async def get_capabilities() -> list[AgentCapability]:
            """List agent capabilities"""
            return self._get_capabilities()

        @self.app.post("/discovery/register")
        async def register_agent(manifest: AgentManifest):
            """Register agent in local registry"""
            self.agent_registry[manifest.agent_id] = manifest
            return {"status": "registered", "agent_id": manifest.agent_id}

        @self.app.get("/discovery/agents")
        async def list_agents() -> list[AgentManifest]:
            """List known agents"""
            return list(self.agent_registry.values())

        @self.app.get("/discovery/agents/search")
        async def search_agents(
            capability: str | None = None,
            protocol: str | None = None,
            provider: str | None = None,
        ) -> list[AgentManifest]:
            """Search agents by capabilities"""
            agents = list(self.agent_registry.values())

            if capability:
                agents = [
                    a
                    for a in agents
                    if any(capability.lower() in c.name.lower() for c in a.capabilities)
                ]
            if protocol:
                agents = [a for a in agents if a.protocol == protocol]
            if provider:
                agents = [a for a in agents if a.provider == provider]

            return agents

        # ANS (Agent Name Service) Endpoints
        @self.app.get("/ans/resolve/{ans_name}")
        async def resolve_ans_name(ans_name: str):
            """Resolve ANS name to agent endpoint"""
            # ANS format: protocol://capability.provider.version.extension
            # Example: agent-protocol://codeGeneration.AgentHub.v1.0
            try:
                parts = ans_name.split("://")
                if len(parts) != 2:
                    raise ValueError("Invalid ANS format")

                protocol, name_parts = parts
                capability, provider, version = name_parts.split(".")[:3]

                # Return our manifest if we match
                manifest = self._generate_manifest()
                if (
                    manifest.protocol == protocol
                    and manifest.provider == provider
                    and any(
                        capability.lower() in c.name.lower()
                        for c in manifest.capabilities
                    )
                ):
                    return {
                        "ans_name": ans_name,
                        "agent_id": manifest.agent_id,
                        "endpoints": manifest.endpoints,
                        "capabilities": [c.dict() for c in manifest.capabilities],
                        "verified": True,
                    }

                raise HTTPException(status_code=404, detail="Agent not found")
            except Exception as e:
                raise HTTPException(
                    status_code=400, detail=f"Invalid ANS name: {str(e)}"
                )

    async def _execute_agent_step(self, task_id: str, step: Step) -> dict[str, Any]:
        """Execute step using our agent hub with capability-based routing"""
        input_text = step.input or ""

        # Get capability from additional_input for proper routing
        capability = step.additional_input.get("capability", "")

        # DEBUG: Log routing information
        print(f"[DEBUG] Routing - Input: {input_text[:50]}...")
        print(f"[DEBUG] Routing - Capability: '{capability}'")
        print(
            f"[DEBUG] Routing - Additional Input Keys: {list(step.additional_input.keys())}"
        )

        # Capability-based routing (replaces primitive string matching)
        CAPABILITY_ROUTING = {
            "codeGeneration": "dev_agent.generate_feature",
            "securityAudit": "sentinel.audit_patch",
            "knowledgeExtraction": "kb_updater.digest_research",
            "dependencyAnalysis": "graph_analyst.predict_links",
            "qualityAssurance": "quality_curator.vector_healthcheck",
            "contextBuilder": "context_builder.get_context",
            "ruleSynthesizer": "rule_synthesizer.synthesize_rules",
            "knowledgeOnboarding": "knowledge_onboarding.get_briefing",
            "memoryManager": "memory_manager.store_memory",
            "preferenceTracker": "preference_tracker.capture_preference",
            "insightSynthesizer": "insight_synthesizer.consolidate",
        }

        # Route based on capability, fallback to string matching for backwards compatibility
        if capability and capability in CAPABILITY_ROUTING:
            method = CAPABILITY_ROUTING[capability]
            print(
                f"[DEBUG] Routing - Using capability routing: {capability} -> {method}"
            )
        elif "code" in input_text.lower() or "generate" in input_text.lower():
            method = "dev_agent.generate_feature"
            print(f"[DEBUG] Routing - Using string matching for code: -> {method}")
        elif "security" in input_text.lower() or "audit" in input_text.lower():
            method = "sentinel.audit_patch"
            print(f"[DEBUG] Routing - Using string matching for security: -> {method}")
        else:
            method = "kb_updater.digest_research"
            print(f"[DEBUG] Routing - Using default fallback: -> {method}")

        print(f"[DEBUG] Final method selected: {method}")

        # Map additional_input to proper agent parameters based on capability
        if capability == "codeGeneration" or method == "dev_agent.generate_feature":
            params = {
                "spec": step.additional_input.get("feature_description", input_text),
                "repo_state_hash": step.additional_input.get("repo_hash", "default"),
            }
        elif capability == "securityAudit" or method == "sentinel.audit_patch":
            params = {
                "diff": step.additional_input.get(
                    "git_diff", step.additional_input.get("code", input_text)
                ),
                "rule_ids": step.additional_input.get(
                    "compliance_rules", step.additional_input.get("rules", [])
                ),
            }
        elif capability == "contextBuilder" or method == "context_builder.get_context":
            params = {
                "topic": step.additional_input.get("topic", input_text),
                "include_collections": step.additional_input.get(
                    "include_collections", ["rules", "heuristics", "research_docs"]
                ),
            }
        elif (
            capability == "dependencyAnalysis"
            or method == "graph_analyst.predict_links"
        ):
            params = {
                "module_ids": step.additional_input.get(
                    "module_ids", [step.additional_input.get("module_path", "default")]
                )
            }
        elif (
            capability == "qualityAssurance"
            or method == "quality_curator.vector_healthcheck"
        ):
            params = {
                "collection": step.additional_input.get(
                    "target_collection", "research_docs"
                ),
                "threshold": step.additional_input.get("quality_threshold", 0.8),
            }
        elif (
            capability == "ruleSynthesizer"
            or method == "rule_synthesizer.synthesize_rules"
        ):
            params = {
                "use_case": step.additional_input.get("use_case", input_text),
                "mode": step.additional_input.get("mode", "curated_list"),
            }
        elif (
            capability == "knowledgeOnboarding"
            or method == "knowledge_onboarding.get_briefing"
        ):
            params = {"scope": step.additional_input.get("scope", "comprehensive")}
        elif capability == "memoryManager" or method == "memory_manager.store_memory":
            params = {
                "content": step.additional_input.get("content", input_text),
                "memory_type": step.additional_input.get("memory_type", "general"),
                "context": step.additional_input.get("context", ""),
                "tags": step.additional_input.get("tags", []),
            }
        elif (
            capability == "preferenceTracker"
            or method == "preference_tracker.capture_preference"
        ):
            params = {
                "preference_text": step.additional_input.get(
                    "preference_text", input_text
                ),
                "context": step.additional_input.get("context", ""),
                "evidence": step.additional_input.get("evidence", ""),
            }
        elif (
            capability == "insightSynthesizer"
            or method == "insight_synthesizer.consolidate"
        ):
            params = {
                "topic": step.additional_input.get("topic", input_text),
                "merge_threshold": step.additional_input.get("merge_threshold", 0.8),
            }
        else:
            # Default to research extraction
            params = {
                "doc_ids": step.additional_input.get("doc_ids", [str(uuid.uuid4())])
            }

        # Call our agent hub
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8003/rpc",
                json={"jsonrpc": "2.0", "method": method, "params": params, "id": 1},
            )

            if response.status_code == 200:
                result = response.json()
                return {
                    "output": json.dumps(result.get("result", {}), indent=2),
                    "is_last": True,
                }
            else:
                return {"output": f"Agent hub error: {response.text}", "is_last": True}

    def _generate_manifest(self) -> AgentManifest:
        """Generate agent manifest for service discovery"""
        return AgentManifest(
            agent_id="agent-hub-001",
            name="AI Agent Hub",
            description="Multi-agent system with 5 specialized AI agents",
            version="1.0.0",
            provider="AgentHub",
            protocol="agent-protocol",
            endpoints={
                "base": "http://localhost:8003",
                "rpc": "http://localhost:8003/rpc",
                "agent_protocol": "http://localhost:8003/ap/v1/agent",
                "discovery": "http://localhost:8003/discovery",
                "ans": "http://localhost:8003/ans",
                "health": "http://localhost:8003/health",
            },
            capabilities=self._get_capabilities(),
            authentication={"type": "none", "required": False},
            metadata={
                "created": datetime.now(timezone.utc).isoformat(),
                "supported_protocols": ["agent-protocol", "json-rpc", "rest"],
                "ans_names": [
                    "agent-protocol://codeGeneration.AgentHub.v1.0",
                    "agent-protocol://securityAudit.AgentHub.v1.0",
                    "agent-protocol://knowledgeExtraction.AgentHub.v1.0",
                    "agent-protocol://dependencyAnalysis.AgentHub.v1.0",
                    "agent-protocol://qualityAssurance.AgentHub.v1.0",
                ],
            },
        )

    def _get_capabilities(self) -> list[AgentCapability]:
        """Get list of agent capabilities"""
        return [
            AgentCapability(
                name="codeGeneration",
                description="Generate code patches and features with git integration",
                input_schema={
                    "type": "object",
                    "properties": {
                        "feature_description": {"type": "string"},
                        "requirements": {"type": "string"},
                    },
                    "required": ["feature_description"],
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "branch_name": {"type": "string"},
                        "files": {"type": "array"},
                        "git_patch": {"type": "string"},
                    },
                },
                tags=["development", "code", "git"],
                version="1.0",
            ),
            AgentCapability(
                name="securityAudit",
                description="Security compliance auditing and vulnerability analysis",
                input_schema={
                    "type": "object",
                    "properties": {
                        "git_diff": {"type": "string"},
                        "compliance_rules": {"type": "array"},
                    },
                    "required": ["git_diff"],
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "compliance_score": {"type": "number"},
                        "vulnerabilities": {"type": "array"},
                        "recommendations": {"type": "array"},
                    },
                },
                tags=["security", "compliance", "audit"],
                version="1.0",
            ),
            AgentCapability(
                name="knowledgeExtraction",
                description="Extract heuristics and insights from research documents",
                input_schema={
                    "type": "object",
                    "properties": {"doc_ids": {"type": "array"}},
                    "required": ["doc_ids"],
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "heuristics": {"type": "array"},
                        "insights": {"type": "array"},
                    },
                },
                tags=["research", "knowledge", "extraction"],
                version="1.0",
            ),
            AgentCapability(
                name="dependencyAnalysis",
                description="Analyze and predict module dependencies and relationships",
                input_schema={
                    "type": "object",
                    "properties": {
                        "module_path": {"type": "string"},
                        "analysis_depth": {"type": "number"},
                    },
                    "required": ["module_path"],
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "dependencies": {"type": "array"},
                        "relationships": {"type": "array"},
                        "predictions": {"type": "array"},
                    },
                },
                tags=["analysis", "dependencies", "architecture"],
                version="1.0",
            ),
            AgentCapability(
                name="qualityAssurance",
                description="Vector health checks and quality curation",
                input_schema={
                    "type": "object",
                    "properties": {
                        "quality_threshold": {"type": "number"},
                        "target_collection": {"type": "string"},
                    },
                    "required": ["quality_threshold"],
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "health_score": {"type": "number"},
                        "recommendations": {"type": "array"},
                        "actions_needed": {"type": "array"},
                    },
                },
                tags=["quality", "health", "maintenance"],
                version="1.0",
            ),
            # AI Assistant Enhancement Agents
            AgentCapability(
                name="contextBuilder",
                description="Build comprehensive context by querying knowledge database",
                input_schema={
                    "type": "object",
                    "properties": {
                        "topic": {"type": "string"},
                        "include_collections": {"type": "array"},
                    },
                    "required": ["topic"],
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "context_brief": {"type": "object"},
                        "confidence_score": {"type": "number"},
                        "collections_queried": {"type": "array"},
                    },
                },
                tags=["context", "knowledge", "assistant", "enhancement"],
                version="1.0",
            ),
            AgentCapability(
                name="ruleSynthesizer",
                description="Find and synthesize relevant rules for specific use cases",
                input_schema={
                    "type": "object",
                    "properties": {
                        "use_case": {"type": "string"},
                        "mode": {"type": "string"},
                    },
                    "required": ["use_case"],
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "synthesis_mode": {"type": "string"},
                        "curated_rules": {"type": "array"},
                        "custom_rule": {"type": "object"},
                        "confidence_score": {"type": "number"},
                    },
                },
                tags=["rules", "synthesis", "guidelines", "assistant"],
                version="1.0",
            ),
            AgentCapability(
                name="knowledgeOnboarding",
                description="Comprehensive knowledge briefing for AI assistant onboarding",
                input_schema={
                    "type": "object",
                    "properties": {
                        "scope": {"type": "string"},
                    },
                    "required": [],
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "briefing": {"type": "object"},
                        "briefing_completeness": {"type": "number"},
                        "recommendations": {"type": "array"},
                    },
                },
                tags=["onboarding", "briefing", "knowledge", "assistant"],
                version="1.0",
            ),
            AgentCapability(
                name="memoryManager",
                description="Store and retrieve insights, memories, and learned patterns",
                input_schema={
                    "type": "object",
                    "properties": {
                        "content": {"type": "string"},
                        "memory_type": {"type": "string"},
                        "context": {"type": "string"},
                        "tags": {"type": "array"},
                        "query": {"type": "string"},
                        "min_relevance": {"type": "number"},
                    },
                    "required": [],
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "operation": {"type": "string"},
                        "stored_memory": {"type": "object"},
                        "retrieved_memories": {"type": "array"},
                        "success": {"type": "boolean"},
                    },
                },
                tags=["memory", "storage", "retrieval", "learning"],
                version="1.0",
            ),
            AgentCapability(
                name="preferenceTracker",
                description="Capture, organize, and apply user preferences",
                input_schema={
                    "type": "object",
                    "properties": {
                        "preference_text": {"type": "string"},
                        "context": {"type": "string"},
                        "evidence": {"type": "string"},
                        "return_reasoning": {"type": "boolean"},
                    },
                    "required": [],
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "operation": {"type": "string"},
                        "captured_preferences": {"type": "array"},
                        "applicable_preferences": {"type": "array"},
                        "recommendations": {"type": "array"},
                    },
                },
                tags=["preferences", "personalization", "tracking", "user"],
                version="1.0",
            ),
            AgentCapability(
                name="insightSynthesizer",
                description="Consolidate related insights into unified knowledge",
                input_schema={
                    "type": "object",
                    "properties": {
                        "topic": {"type": "string"},
                        "merge_threshold": {"type": "number"},
                    },
                    "required": ["topic"],
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "synthesized_insight": {"type": "object"},
                        "relationships_found": {"type": "array"},
                        "optimization_actions": {"type": "array"},
                        "knowledge_quality_improvement": {"type": "object"},
                    },
                },
                tags=["synthesis", "consolidation", "knowledge", "optimization"],
                version="1.0",
            ),
        ]


def setup_agent_discovery(app: FastAPI) -> AgentDiscoveryService:
    """Initialize agent discovery service"""
    return AgentDiscoveryService(app)
