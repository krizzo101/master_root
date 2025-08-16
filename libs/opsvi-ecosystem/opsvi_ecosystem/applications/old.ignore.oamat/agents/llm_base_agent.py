import json
import logging
from typing import Any

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, ConfigDict, Field

from src.shared.mcp.neo4j_mcp_client import Neo4jMCPClient as Neo4jClient

logger = logging.getLogger(__name__)


class WorkflowSchema(BaseModel):
    """Schema for workflow generation structured response"""

    model_config = ConfigDict(extra="forbid")
    workflow: str = Field(description="JSON string of the workflow nodes and edges")
    reasoning: str = Field(description="Explanation of the workflow design decisions")


class AnalysisSchema(BaseModel):
    """Schema for request analysis structured response"""

    model_config = ConfigDict(extra="forbid")
    primary_intent: str = Field(description="Main goal or objective")
    secondary_intents: list[str] = Field(description="Additional goals or benefits")
    complexity: str = Field(
        description="Complexity level: simple|moderate|complex|enterprise"
    )
    required_capabilities: list[str] = Field(description="Specific capabilities needed")
    workflow_strategy: str = Field(
        description="Workflow execution strategy: linear|parallel|adaptive|iterative|hybrid|sdlc"
    )
    recommended_agents: list[str] = Field(description="Optimal agent sequence")
    required_tools: list[str] = Field(description="Essential tools for success")
    estimated_phases: int = Field(description="Number of workflow phases")
    uncertainty_factors: list[str] = Field(
        description="Factors that could change approach"
    )
    clarification_questions: list[str] = Field(
        description="Questions to reduce uncertainty"
    )
    risk_factors: list[str] = Field(description="Potential risks or challenges")
    success_probability: float = Field(description="Probability of success (0.0-1.0)")
    confidence_score: float = Field(description="Confidence in analysis (0.0-1.0)")


class KnowledgeResponse(BaseModel):
    """Standard response for knowledge storage operations"""

    model_config = ConfigDict(extra="forbid")
    success: bool
    results: list[Any] = Field(default_factory=list)
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class LLMBaseAgent:
    """Base agent class with OpenAI LLM integration and structured responses"""

    def __init__(
        self,
        agent_name: str,
        role: str,
        expertise: list[str],
        model: str = "o3-mini",
        temperature: float = 0.7,
        neo4j_uri: str | None = None,
        neo4j_user: str | None = None,
        neo4j_password: str | None = None,
    ):
        """
        Initializes the LLMBaseAgent.
        Connects to OpenAI and optionally to Neo4j if credentials are provided.
        """
        self.agent_name = agent_name
        self.role = role
        self.expertise = expertise
        self.model = model

        # Use OpenAI Responses API with structured responses - no fallbacks
        # O3 models don't support temperature parameter
        llm_kwargs = {"model": model}
        if "o3" not in model:
            llm_kwargs["temperature"] = temperature

        self.llm = ChatOpenAI(**llm_kwargs)

        if neo4j_uri and neo4j_user and neo4j_password:
            self.neo4j_client = Neo4jClient(
                uri=neo4j_uri, user=neo4j_user, password=neo4j_password
            )
        else:
            self.neo4j_client = None

    def store_knowledge(
        self,
        content: str,
        source: str,
        knowledge_type: str | None = None,
        metadata: dict | None = None,
        repo_id: str | None = None,
        check_similarity: bool = True,
        document_type: str | None = None,
    ) -> KnowledgeResponse:
        """
        Stores knowledge content in the Neo4j database as Document and Chunk nodes.
        This is a real implementation that replaces the mock version.
        """
        if metadata is None:
            metadata = {}

        if not self.neo4j_client or not self.neo4j_client.check_connection():
            raise ConnectionError("Neo4j connection failed or client not configured.")

        # Create a Document node for the file
        doc_node = self.neo4j_client.add_document(
            path=source, source=source, repo_id=repo_id, metadata=metadata
        )
        doc_id = doc_node["doc_id"]

        # For simplicity, we'll treat the whole file content as a single chunk.
        # A more advanced implementation would split it into smaller chunks.
        chunk_node = self.neo4j_client.add_chunk(
            doc_id=doc_id, text=content, metadata={"source": source}
        )

        # If it's code, create a Code node as well
        if knowledge_type == "code" and "file_id" in metadata:
            self.neo4j_client.add_code(
                path=source,
                content=content,
                repo_id=repo_id,
                file_id=metadata["file_id"],
            )

        return KnowledgeResponse(
            success=True,
            results=[{"doc_id": doc_id, "chunk_id": chunk_node["chunk_id"]}],
            metadata={"source": source},
        )

    def _get_neo4j_client(self) -> Neo4jClient:
        """Provides access to the Neo4j client instance."""
        return self.neo4j_client

    def llm_call(
        self,
        messages: list[BaseMessage],
        response_format: BaseModel | None = None,
        **kwargs,
    ) -> Any:
        """
        Make an LLM call with structured response format (no fallbacks)

        Args:
            messages: List of LangChain messages
            response_format: Pydantic model for structured response
            **kwargs: Additional parameters

        Returns:
            AI response with structured parsing if response_format provided
        """
        import time
        from datetime import datetime

        api_logger = logging.getLogger("oamat.api")

        # Log API call initiation
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        message_content = ""
        if messages:
            for msg in messages:
                if hasattr(msg, "content"):
                    message_content += (
                        f"[{type(msg).__name__}] {str(msg.content)[:200]}...\n"
                    )

        # USER-FRIENDLY LOGGING: Start model call
        try:
            from src.applications.oamat.main import OAMATMain

            # Try to get UserLogger from global context (if available)
            user_logger = getattr(OAMATMain, "_current_user_logger", None)
            if user_logger:
                purpose = (
                    "code generation"
                    if "code" in self.role.lower()
                    else (
                        "planning"
                        if "manager" in self.role.lower()
                        or "planner" in self.role.lower()
                        else (
                            "analysis"
                            if "reviewer" in self.role.lower()
                            or "tester" in self.role.lower()
                            else "task execution"
                        )
                    )
                )
                user_logger.start_model_call(self.model, purpose, self.agent_name)
        except Exception:
            # Silent fallback if UserLogger not available
            pass

        api_call_log = f"""
========================================
🔗 OPENAI API CALL
========================================
TIMESTAMP: {timestamp}
AGENT: {self.agent_name}
MODEL: {self.model}
STRUCTURED_OUTPUT: {response_format.__name__ if response_format else "None"}
MESSAGE_COUNT: {len(messages)}
KWARGS: {kwargs}
MESSAGE_PREVIEW:
{message_content}
========================================
"""
        api_logger.info(api_call_log)

        start_time = time.time()

        try:
            if response_format:
                # Bind the LLM to the specific Pydantic model for this call
                structured_llm = self.llm.with_structured_output(response_format)
                response = structured_llm.invoke(messages, **kwargs)
            else:
                # Regular text response
                response = self.llm.invoke(messages, **kwargs)

            # Log successful API response
            end_time = time.time()
            duration = end_time - start_time

            # USER-FRIENDLY LOGGING: Complete model call
            try:
                if user_logger:
                    user_logger.complete_model_call(self.model, duration, success=True)
            except Exception:
                pass

            response_content = ""
            if hasattr(response, "content"):
                response_content = (
                    str(response.content)[:500] + "..."
                    if len(str(response.content)) > 500
                    else str(response.content)
                )
            elif hasattr(response, "model_dump_json"):
                response_content = (
                    response.model_dump_json()[:500] + "..."
                    if len(response.model_dump_json()) > 500
                    else response.model_dump_json()
                )
            else:
                response_content = (
                    str(response)[:500] + "..."
                    if len(str(response)) > 500
                    else str(response)
                )

            success_log = f"""
========================================
✅ OPENAI API RESPONSE
========================================
TIMESTAMP: {datetime.now().strftime("%H:%M:%S.%f")[:-3]}
AGENT: {self.agent_name}
DURATION: {duration:.3f}s
RESPONSE_TYPE: {type(response).__name__}
RESPONSE_PREVIEW:
{response_content}
========================================
"""
            api_logger.info(success_log)

            return response

        except Exception as e:
            # Log error and re-raise
            end_time = time.time()
            duration = end_time - start_time

            # USER-FRIENDLY LOGGING: Failed model call
            try:
                if user_logger:
                    user_logger.complete_model_call(self.model, duration, success=False)
            except Exception:
                pass

            error_log = f"""
========================================
❌ OPENAI API ERROR
========================================
TIMESTAMP: {datetime.now().strftime("%H:%M:%S.%f")[:-3]}
AGENT: {self.agent_name}
DURATION: {duration:.3f}s
ERROR: {str(e)}
========================================
"""
            api_logger.error(error_log)
            raise

    def generate_workflow(
        self, user_request: str, context: str | None = None
    ) -> dict[str, Any]:
        """
        Generate workflow using structured responses

        Args:
            user_request: The user's request
            context: Optional context information

        Returns:
            Dict containing workflow and reasoning
        """
        prompt = f"""
        Generate a comprehensive workflow for: {user_request}

        {f"Context: {context}" if context else ""}

        Create a detailed workflow with specific nodes and edges in JSON format.
        Each node should have: id, type, name, description, dependencies
        Each edge should connect nodes logically.

        Provide clear reasoning for your workflow design decisions.
        """

        messages = [
            SystemMessage(
                content=f"You are {self.agent_name}, a {self.role} expert in {', '.join(self.expertise)}. Generate structured workflows with clear reasoning."
            ),
            HumanMessage(content=prompt),
        ]

        # Use structured response format - this will enforce JSON schema validation
        result = self.llm_call(messages, response_format=WorkflowSchema)

        if isinstance(result, WorkflowSchema):
            # Let JSONDecodeError propagate if parsing fails
            workflow_data = json.loads(result.workflow)
            return {
                "workflow": workflow_data,
                "reasoning": result.reasoning,
                "success": True,
            }
        else:
            raise ValueError("Structured response format not received")

    def execute_task(self, task: str, context: dict[str, Any] | None = None) -> str:
        """
        Execute a specific task

        Args:
            task: Task description
            context: Optional context data

        Returns:
            Task execution result
        """
        context_str = ""
        if context:
            context_str = f"Context: {json.dumps(context, indent=2)}"

        prompt = f"""
        Execute this task: {task}

        {context_str}

        As {self.agent_name} ({self.role}), provide a detailed response based on your expertise in {', '.join(self.expertise)}.
        """

        messages = [
            SystemMessage(
                content=f"You are {self.agent_name}, a {self.role} expert. Execute tasks efficiently and provide clear responses."
            ),
            HumanMessage(content=prompt),
        ]

        # Regular text response for task execution
        response = self.llm_call(messages)

        if hasattr(response, "content"):
            return response.content
        else:
            return str(response)

    def __str__(self):
        return f"{self.agent_name} ({self.role})"
