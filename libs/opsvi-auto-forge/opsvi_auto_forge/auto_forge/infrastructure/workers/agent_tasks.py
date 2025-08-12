"""Agent task execution for autonomous software factory."""

import asyncio
import logging
import time
import uuid
from typing import Any, Dict, Optional

from opsvi_auto_forge.infrastructure.workers.celery_app import app

logger = logging.getLogger(__name__)

# ============================================================================
# AGENT EXECUTION TASKS
# ============================================================================

# Agent queue mapping based on complexity
AGENT_QUEUE_MAPPING = {
    "planner": "default",  # Standard planning tasks
    "specifier": "default",  # Standard specification tasks
    "architect": "heavy",  # Complex architecture tasks
    "coder": "heavy",  # Code generation tasks
    "tester": "test",  # Testing tasks
    "critic": "default",  # Review tasks
    "perf_smoke": "test",  # Performance testing
    "perf_opt": "heavy",  # Performance optimization
    "security_validator": "test",  # Security validation
    "syntax_fixer": "default",  # Syntax fixing
    "assurance_orchestrator": "heavy",  # Assurance orchestration
    "base_repair": "default",  # Basic repair tasks
}


def get_agent_class(agent_type: str):
    """Get the agent class for the given agent type."""
    # Import agent classes
    from opsvi_auto_forge.agents.planner_agent import PlannerAgent
    from opsvi_auto_forge.agents.specifier_agent import SpecifierAgent
    from opsvi_auto_forge.agents.architect_agent import ArchitectAgent
    from opsvi_auto_forge.agents.coder_agent import CoderAgent
    from opsvi_auto_forge.agents.tester_agent import TesterAgent
    from opsvi_auto_forge.agents.critic_agent import CriticAgent
    from opsvi_auto_forge.agents.perf_smoke_agent import PerfSmokeAgent
    from opsvi_auto_forge.agents.perf_opt_agent import PerfOptAgent
    from opsvi_auto_forge.agents.security_validator import SecurityValidator
    from opsvi_auto_forge.agents.syntax_fixer import SyntaxFixer
    from opsvi_auto_forge.agents.assurance_orchestrator import AssuranceOrchestrator
    from opsvi_auto_forge.agents.base_repair_agent import BaseRepairAgent

    # Agent class mapping
    agent_classes = {
        "planner": PlannerAgent,
        "specifier": SpecifierAgent,
        "architect": ArchitectAgent,
        "coder": CoderAgent,
        "tester": TesterAgent,
        "critic": CriticAgent,
        "perf_smoke": PerfSmokeAgent,
        "perf_opt": PerfOptAgent,
        "security_validator": SecurityValidator,
        "syntax_fixer": SyntaxFixer,
        "assurance_orchestrator": AssuranceOrchestrator,
        "base_repair": BaseRepairAgent,
    }

    return agent_classes.get(agent_type)


def get_agent_queue(agent_type: str) -> str:
    """Get the appropriate queue for an agent type."""
    return AGENT_QUEUE_MAPPING.get(agent_type, "default")


def get_dependencies():
    """Get shared dependencies for agent tasks."""
    from opsvi_auto_forge.infrastructure.memory.graph.client import Neo4jClient
    from opsvi_auto_forge.infrastructure.memory.vector.context_store import ContextStore
    from opsvi_auto_forge.infrastructure.memory.vector.chroma_client import ChromaClient
    from opsvi_auto_forge.core.prompting.gateway import PromptGateway
    from opsvi_auto_forge.core.prompting.pga import PromptGenerationAgent
    from opsvi_auto_forge.infrastructure.llm.openai_client import OpenAIResponsesClient
    from opsvi_auto_forge.config.settings import Settings

    settings = Settings()

    # Initialize dependencies
    neo4j_client = Neo4jClient(
        uri=settings.neo4j_url,
        user=settings.neo4j_user,
        password=settings.neo4j_password,
    )

    # Create ChromaClient first with a unique collection name to avoid conflicts
    collection_name = f"{settings.vector_store_collection}_{int(time.time())}"
    chroma_client = ChromaClient(
        host="localhost",  # Default to localhost for now
        port=8001,  # ChromaDB port from docker-compose
        collection_name=collection_name,
        api_key=settings.openai_api_key,
    )

    context_store = ContextStore(chroma_client=chroma_client)

    # Create OpenAI client - handle missing API key gracefully
    try:
        openai_client = OpenAIResponsesClient(
            api_key=settings.openai_api_key,
        )
    except Exception as e:
        logger.warning(f"Failed to create OpenAI client: {e}")
        # Create a mock client or use a fallback
        openai_client = None

    # Create Prompt Generation Agent
    pga = PromptGenerationAgent(
        neo4j_client=neo4j_client,
        context_store=context_store,
    )

    # Only create PromptGateway if we have a valid OpenAI client
    if openai_client:
        prompt_gateway = PromptGateway(
            openai_client=openai_client,
            pga=pga,
        )
    else:
        prompt_gateway = None

    return neo4j_client, context_store, prompt_gateway


async def execute_agent_task(
    agent_type: str,
    task_execution_data: Dict[str, Any],
    project_id: Optional[str] = None,
    run_id: Optional[str] = None,
    node_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Execute an agent task with the given parameters."""
    import time
    from uuid import uuid4
    from opsvi_auto_forge.application.orchestrator.task_models import (
        TaskExecution,
        TaskDefinition,
        TaskType,
        TaskPriority,
    )
    from opsvi_auto_forge.config.models import TaskStatus
    from opsvi_auto_forge.config.settings import settings

    # Get agent class
    agent_class = get_agent_class(agent_type)
    if agent_class is None:
        raise ValueError(f"Unknown agent type: {agent_type}")

    # Get dependencies
    neo4j_client, context_store, prompt_gateway = get_dependencies()

    # Handle missing required fields in task_execution_data
    try:
        task_execution = TaskExecution(**task_execution_data)
    except Exception as e:
        logger.warning(f"Failed to create TaskExecution from data: {e}")
        logger.warning(f"task_execution_data keys: {list(task_execution_data.keys())}")

        # Create a minimal TaskExecution with default values
        task_id = task_execution_data.get("id") or uuid4()
        project_uuid = task_execution_data.get("project_id") or project_id or uuid4()
        run_uuid = task_execution_data.get("run_id") or run_id or uuid4()

        # Create a minimal TaskDefinition
        definition = TaskDefinition(
            name=task_execution_data.get("name", f"{agent_type}_task"),
            type=TaskType.PLANNING,  # Default type
            agent_type=agent_type,
            description=task_execution_data.get(
                "description", f"Task for {agent_type} agent"
            ),
            inputs=task_execution_data.get("inputs", {}),
            outputs=task_execution_data.get("outputs", {}),
            dependencies=task_execution_data.get("dependencies", []),
            timeout_seconds=task_execution_data.get("timeout_seconds", 300),
            retry_attempts=task_execution_data.get("retry_attempts", 3),
            priority=TaskPriority.NORMAL,
            queue=task_execution_data.get("queue", "default"),
        )

        task_execution = TaskExecution(
            id=task_id,
            definition=definition,
            project_id=project_uuid,
            run_id=run_uuid,
            status=TaskStatus.PENDING,
            inputs=task_execution_data.get("inputs", {}),
            outputs=task_execution_data.get("outputs", {}),
        )

    # Initialize agent with appropriate parameters based on agent type
    if agent_type == "critic":
        agent = agent_class(
            neo4j_client=neo4j_client,
        )
    else:
        agent = agent_class(
            neo4j_client=neo4j_client,
            prompt_gateway=prompt_gateway,
            context_store=context_store,
        )

    # Decision Kernel and Retrieval Orchestrator Integration
    context_pack = None
    schema = None

    if settings.knowledge_enable:
        try:
            # Build context pack using retrieval orchestrator
            context_pack = await build_context_pack(
                task_type=agent_type,
                task_id=str(task_execution.id),
                query=task_execution_data.get("inputs", {}).get("query", ""),
                max_snippets=10,
            )
        except Exception as e:
            logger.warning(f"Retrieval orchestrator failed: {e}")

    if settings.reasoning_enable:
        try:
            # Get schema for structured output validation
            schema = get_schema(f"{agent_type}_output")
        except Exception as e:
            logger.warning(f"Schema registry failed: {e}")

    # Execute agent
    start_time = time.time()
    try:
        result = await agent.run(task_execution, task_execution_data.get("inputs", {}))
        execution_time = time.time() - start_time

        # Convert result to dict
        result_dict = result.model_dump()
        result_dict["execution_time_seconds"] = execution_time
        result_dict["agent_type"] = agent_type

        # Structured Output Validation and Verification
        if settings.reasoning_enable and schema:
            try:
                # Validate output against schema
                validation_result = verify_output(result_dict, schema)
                if not validation_result.passed:
                    logger.warning(
                        f"Output validation failed: {validation_result.details}"
                    )
                    # Implement repair mechanism for validation failures
                    repaired_result = await _process_validation_failure(
                        result_dict=result_dict,
                        validation_result=validation_result,
                        agent_type=agent_type,
                        task_execution=task_execution,
                        project_id=project_id,
                        run_id=run_id,
                        node_id=node_id,
                    )
                    if repaired_result:
                        result_dict = repaired_result
                        logger.info(f"Validation repair successful for {agent_type}")

                # Calibrate confidence
                confidence = calibrate_confidence(
                    base_confidence=0.8,
                    critic_score=validation_result.score,
                    agreement_rate=0.7,
                )

                # Update result with confidence
                result_dict["confidence"] = confidence
                result_dict["validation_passed"] = validation_result.passed

            except Exception as e:
                logger.warning(f"Verification failed: {e}")

        # Add integration metadata
        result_dict["context_pack_used"] = context_pack is not None
        result_dict["schema_validation"] = schema is not None

        return result_dict

    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(
            f"Agent execution failed: {agent_type}",
            extra={
                "agent_type": agent_type,
                "task_id": str(task_execution.id),
                "project_id": project_id,
                "run_id": run_id,
                "node_id": node_id,
                "error": str(e),
                "execution_time_seconds": execution_time,
            },
            exc_info=True,
        )
        raise


# ============================================================================
# HELPER FUNCTIONS (Core Business Logic)
# ============================================================================


async def _execute_planner_agent_impl(
    task_execution_data: Dict[str, Any],
    project_id: Optional[str] = None,
    run_id: Optional[str] = None,
    node_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Core implementation for planner agent execution."""
    from opsvi_auto_forge.infrastructure.workers.agent_tasks import logger

    task_id = f"planner_{project_id}_{run_id}_{node_id}_{uuid.uuid4().hex[:8]}"
    logger.info(
        f"Executing planner agent - Task ID: {task_id}",
        extra={
            "task_id": task_id,
            "queue": "default",
            "project_id": project_id,
            "run_id": run_id,
            "node_id": node_id,
        },
    )
    try:
        result = await execute_agent_task(
            "planner",
            task_execution_data,
            project_id,
            run_id,
            node_id,
        )
        logger.info(
            f"Planner agent completed - Task ID: {task_id}",
            extra={
                "task_id": task_id,
                "status": "completed",
                "project_id": project_id,
                "run_id": run_id,
                "node_id": node_id,
            },
        )
        return result
    except Exception as e:
        logger.error(
            f"Planner agent failed - Task ID: {task_id}",
            extra={
                "task_id": task_id,
                "error": str(e),
                "project_id": project_id,
                "run_id": run_id,
                "node_id": node_id,
            },
            exc_info=True,
        )
        raise


async def _execute_specifier_agent_impl(
    task_execution_data: Dict[str, Any],
    project_id: Optional[str] = None,
    run_id: Optional[str] = None,
    node_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Core implementation for specifier agent execution."""
    from opsvi_auto_forge.infrastructure.workers.agent_tasks import logger

    task_id = f"specifier_{project_id}_{run_id}_{node_id}_{uuid.uuid4().hex[:8]}"
    logger.info(
        f"Executing specifier agent - Task ID: {task_id}",
        extra={
            "task_id": task_id,
            "queue": "default",
            "project_id": project_id,
            "run_id": run_id,
            "node_id": node_id,
        },
    )
    try:
        result = await execute_agent_task(
            "specifier",
            task_execution_data,
            project_id,
            run_id,
            node_id,
        )
        logger.info(
            f"Specifier agent completed - Task ID: {task_id}",
            extra={
                "task_id": task_id,
                "status": "completed",
                "project_id": project_id,
                "run_id": run_id,
                "node_id": node_id,
            },
        )
        return result
    except Exception as e:
        logger.error(
            f"Specifier agent failed - Task ID: {task_id}",
            extra={
                "task_id": task_id,
                "error": str(e),
                "project_id": project_id,
                "run_id": run_id,
                "node_id": node_id,
            },
            exc_info=True,
        )
        raise


async def _execute_architect_agent_impl(
    task_execution_data: Dict[str, Any],
    project_id: Optional[str] = None,
    run_id: Optional[str] = None,
    node_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Core implementation for architect agent execution."""
    from opsvi_auto_forge.infrastructure.workers.agent_tasks import logger

    task_id = f"architect_{project_id}_{run_id}_{node_id}_{uuid.uuid4().hex[:8]}"
    logger.info(
        f"Executing architect agent - Task ID: {task_id}",
        extra={
            "task_id": task_id,
            "queue": "heavy",
            "project_id": project_id,
            "run_id": run_id,
            "node_id": node_id,
        },
    )
    try:
        result = await execute_agent_task(
            "architect",
            task_execution_data,
            project_id,
            run_id,
            node_id,
        )
        logger.info(
            f"Architect agent completed - Task ID: {task_id}",
            extra={
                "task_id": task_id,
                "status": "completed",
                "project_id": project_id,
                "run_id": run_id,
                "node_id": node_id,
            },
        )
        return result
    except Exception as e:
        logger.error(
            f"Architect agent failed - Task ID: {task_id}",
            extra={
                "task_id": task_id,
                "error": str(e),
                "project_id": project_id,
                "run_id": run_id,
                "node_id": node_id,
            },
            exc_info=True,
        )
        raise


# ============================================================================
# CELERY TASKS (Wrappers)
# ============================================================================


@app.task(
    bind=True,
    name="workers.agent_tasks.execute_planner_agent",
    queue="default",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
    default_retry_delay=5,
)
def execute_planner_agent(
    self,
    task_execution_data: Dict[str, Any],
    project_id: Optional[str] = None,
    run_id: Optional[str] = None,
    node_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Celery task wrapper for planner agent execution."""
    try:
        return asyncio.run(
            _execute_planner_agent_impl(
                task_execution_data,
                project_id,
                run_id,
                node_id,
            )
        )
    except Exception as e:
        self.retry(countdown=60, max_retries=3, exc=e)


# ============================================================================
# SPECIFIER AGENT TASK
# ============================================================================


@app.task(
    bind=True,
    name="workers.agent_tasks.execute_specifier_agent",
    queue="default",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
    default_retry_delay=5,
)
def execute_specifier_agent(
    self,
    task_execution_data: Dict[str, Any],
    project_id: Optional[str] = None,
    run_id: Optional[str] = None,
    node_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Celery task wrapper for specifier agent execution."""
    try:
        return asyncio.run(
            _execute_specifier_agent_impl(
                task_execution_data,
                project_id,
                run_id,
                node_id,
            )
        )
    except Exception as e:
        self.retry(countdown=60, max_retries=3, exc=e)


# ============================================================================
# ARCHITECT AGENT TASK
# ============================================================================


@app.task(
    bind=True,
    name="workers.agent_tasks.execute_architect_agent",
    queue="heavy",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=2,
    default_retry_delay=10,
)
def execute_architect_agent(
    self,
    task_execution_data: Dict[str, Any],
    project_id: Optional[str] = None,
    run_id: Optional[str] = None,
    node_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Celery task wrapper for architect agent execution."""
    try:
        return asyncio.run(
            _execute_architect_agent_impl(
                task_execution_data,
                project_id,
                run_id,
                node_id,
            )
        )
    except Exception as e:
        self.retry(countdown=60, max_retries=2, exc=e)


# ============================================================================
# CODER AGENT TASK
# ============================================================================


async def _execute_coder_agent_impl(
    task_execution_data: Dict[str, Any],
    project_id: Optional[str] = None,
    run_id: Optional[str] = None,
    node_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Core implementation for coder agent execution."""
    from opsvi_auto_forge.infrastructure.workers.agent_tasks import logger

    task_id = f"coder_{project_id}_{run_id}_{node_id}_{uuid.uuid4().hex[:8]}"
    logger.info(
        f"Executing coder agent - Task ID: {task_id}",
        extra={
            "task_id": task_id,
            "queue": "heavy",
            "project_id": project_id,
            "run_id": run_id,
            "node_id": node_id,
        },
    )
    try:
        result = await execute_agent_task(
            "coder",
            task_execution_data,
            project_id,
            run_id,
            node_id,
        )
        logger.info(
            f"Coder agent completed - Task ID: {task_id}",
            extra={
                "task_id": task_id,
                "status": "completed",
                "project_id": project_id,
                "run_id": run_id,
                "node_id": node_id,
            },
        )
        return result
    except Exception as e:
        logger.error(
            f"Coder agent failed - Task ID: {task_id}",
            extra={
                "task_id": task_id,
                "error": str(e),
                "project_id": project_id,
                "run_id": run_id,
                "node_id": node_id,
            },
            exc_info=True,
        )
        raise


@app.task(
    bind=True,
    name="workers.agent_tasks.execute_coder_agent",
    queue="heavy",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=2,
    default_retry_delay=10,
)
def execute_coder_agent(
    self,
    task_execution_data: Dict[str, Any],
    project_id: Optional[str] = None,
    run_id: Optional[str] = None,
    node_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Celery task wrapper for coder agent execution."""
    try:
        return asyncio.run(
            _execute_coder_agent_impl(
                task_execution_data,
                project_id,
                run_id,
                node_id,
            )
        )
    except Exception as e:
        self.retry(countdown=60, max_retries=2, exc=e)


# ============================================================================
# TESTER AGENT TASK
# ============================================================================


async def _execute_tester_agent_impl(
    task_execution_data: Dict[str, Any],
    project_id: Optional[str] = None,
    run_id: Optional[str] = None,
    node_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Core implementation for tester agent execution."""
    from opsvi_auto_forge.infrastructure.workers.agent_tasks import logger

    task_id = f"tester_{project_id}_{run_id}_{node_id}_{uuid.uuid4().hex[:8]}"
    logger.info(
        f"Executing tester agent - Task ID: {task_id}",
        extra={
            "task_id": task_id,
            "queue": "test",
            "project_id": project_id,
            "run_id": run_id,
            "node_id": node_id,
        },
    )
    try:
        result = await execute_agent_task(
            "tester",
            task_execution_data,
            project_id,
            run_id,
            node_id,
        )
        logger.info(
            f"Tester agent completed - Task ID: {task_id}",
            extra={
                "task_id": task_id,
                "status": "completed",
                "project_id": project_id,
                "run_id": run_id,
                "node_id": node_id,
            },
        )
        return result
    except Exception as e:
        logger.error(
            f"Tester agent failed - Task ID: {task_id}",
            extra={
                "task_id": task_id,
                "error": str(e),
                "project_id": project_id,
                "run_id": run_id,
                "node_id": node_id,
            },
            exc_info=True,
        )
        raise


@app.task(
    bind=True,
    name="workers.agent_tasks.execute_tester_agent",
    queue="test",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
    default_retry_delay=5,
)
def execute_tester_agent(
    self,
    task_execution_data: Dict[str, Any],
    project_id: Optional[str] = None,
    run_id: Optional[str] = None,
    node_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Celery task wrapper for tester agent execution."""
    try:
        return asyncio.run(
            _execute_tester_agent_impl(
                task_execution_data,
                project_id,
                run_id,
                node_id,
            )
        )
    except Exception as e:
        self.retry(countdown=60, max_retries=3, exc=e)


# ============================================================================
# CRITIC AGENT TASK
# ============================================================================


async def _execute_critic_agent_impl(
    task_execution_data: Dict[str, Any],
    project_id: Optional[str] = None,
    run_id: Optional[str] = None,
    node_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Core implementation for critic agent execution."""
    from opsvi_auto_forge.infrastructure.workers.agent_tasks import logger

    task_id = f"critic_{project_id}_{run_id}_{node_id}_{uuid.uuid4().hex[:8]}"
    logger.info(
        f"Executing critic agent - Task ID: {task_id}",
        extra={
            "task_id": task_id,
            "queue": "default",
            "project_id": project_id,
            "run_id": run_id,
            "node_id": node_id,
        },
    )
    try:
        result = await execute_agent_task(
            "critic",
            task_execution_data,
            project_id,
            run_id,
            node_id,
        )
        logger.info(
            f"Critic agent completed - Task ID: {task_id}",
            extra={
                "task_id": task_id,
                "status": "completed",
                "project_id": project_id,
                "run_id": run_id,
                "node_id": node_id,
            },
        )
        return result
    except Exception as e:
        logger.error(
            f"Critic agent failed - Task ID: {task_id}",
            extra={
                "task_id": task_id,
                "error": str(e),
                "project_id": project_id,
                "run_id": run_id,
                "node_id": node_id,
            },
            exc_info=True,
        )
        raise


@app.task(
    bind=True,
    name="workers.agent_tasks.execute_critic_agent",
    queue="default",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
    default_retry_delay=5,
)
def execute_critic_agent(
    self,
    task_execution_data: Dict[str, Any],
    project_id: Optional[str] = None,
    run_id: Optional[str] = None,
    node_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Celery task wrapper for critic agent execution."""
    try:
        return asyncio.run(
            _execute_critic_agent_impl(
                task_execution_data,
                project_id,
                run_id,
                node_id,
            )
        )
    except Exception as e:
        self.retry(countdown=60, max_retries=3, exc=e)


# ============================================================================
# GENERIC AGENT TASK (for other agent types)
# ============================================================================


async def _execute_agent_impl(
    agent_type: str,
    task_execution_data: Dict[str, Any],
    project_id: Optional[str] = None,
    run_id: Optional[str] = None,
    node_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Core implementation for generic agent execution."""
    from opsvi_auto_forge.infrastructure.workers.agent_tasks import logger

    task_id = f"{agent_type}_{project_id}_{run_id}_{node_id}_{uuid.uuid4().hex[:8]}"
    logger.info(
        f"Executing {agent_type} agent - Task ID: {task_id}",
        extra={
            "task_id": task_id,
            "agent_type": agent_type,
            "queue": get_agent_queue(agent_type),
            "project_id": project_id,
            "run_id": run_id,
            "node_id": node_id,
        },
    )
    try:
        result = await execute_agent_task(
            agent_type,
            task_execution_data,
            project_id,
            run_id,
            node_id,
        )
        logger.info(
            f"{agent_type} agent completed - Task ID: {task_id}",
            extra={
                "task_id": task_id,
                "status": "completed",
                "agent_type": agent_type,
                "project_id": project_id,
                "run_id": run_id,
                "node_id": node_id,
            },
        )
        return result
    except Exception as e:
        logger.error(
            f"{agent_type} agent failed - Task ID: {task_id}",
            extra={
                "task_id": task_id,
                "error": str(e),
                "agent_type": agent_type,
                "project_id": project_id,
                "run_id": run_id,
                "node_id": node_id,
            },
            exc_info=True,
        )
        raise


@app.task(
    bind=True,
    name="workers.agent_tasks.execute_agent",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
    default_retry_delay=5,
)
def execute_agent(
    self,
    agent_type: str,
    task_execution_data: Dict[str, Any],
    project_id: Optional[str] = None,
    run_id: Optional[str] = None,
    node_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Celery task wrapper for generic agent execution."""
    try:
        return asyncio.run(
            _execute_agent_impl(
                agent_type,
                task_execution_data,
                project_id,
                run_id,
                node_id,
            )
        )
    except Exception as e:
        self.retry(countdown=60, max_retries=3, exc=e)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


def get_agent_task_name(agent_type: str) -> str:
    """Get the Celery task name for an agent type."""
    task_mapping = {
        "planner": "workers.agent_tasks.execute_planner_agent",
        "specifier": "workers.agent_tasks.execute_specifier_agent",
        "architect": "workers.agent_tasks.execute_architect_agent",
        "coder": "workers.agent_tasks.execute_coder_agent",
        "tester": "workers.agent_tasks.execute_tester_agent",
        "critic": "workers.agent_tasks.execute_critic_agent",
    }

    return task_mapping.get(agent_type, "workers.agent_tasks.execute_agent")


def submit_agent_task(
    agent_type: str,
    task_execution_data: Dict[str, Any],
    project_id: Optional[str] = None,
    run_id: Optional[str] = None,
    node_id: Optional[str] = None,
    **kwargs,
):
    """Submit an agent task to Celery."""

    task_name = get_agent_task_name(agent_type)

    if task_name == "workers.agent_tasks.execute_agent":
        # Use generic task for unknown agent types
        return execute_agent.apply_async(
            kwargs={
                "agent_type": agent_type,
                "task_execution_data": task_execution_data,
                "project_id": project_id,
                "run_id": run_id,
                "node_id": node_id,
            },
            queue=get_agent_queue(agent_type),
            **kwargs,
        )
    else:
        # Use specific task for known agent types
        task_func = app.tasks[task_name]
        return task_func.apply_async(
            kwargs={
                "task_execution_data": task_execution_data,
                "project_id": project_id,
                "run_id": run_id,
                "node_id": node_id,
            },
            queue=get_agent_queue(agent_type),
            **kwargs,
        )


# ============================================================================
# HEALTH CHECK TASK
# ============================================================================


@app.task(bind=True, name="workers.agent_tasks.health_check")
def agent_health_check(self):
    """Health check task for agent tasks."""
    import time

    logger.info(f"Agent health check task {self.request.id} executed")
    return {
        "status": "healthy",
        "task_id": self.request.id,
        "timestamp": time.time(),
        "available_agents": list(AGENT_QUEUE_MAPPING.keys()),
    }


@app.task(
    bind=True,
    name="workers.agent_tasks.run_agent",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
    default_retry_delay=5,
)
def run_agent(
    self,
    task_spec_json: str,
    project_id: Optional[str] = None,
    run_id: Optional[str] = None,
    node_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Generic agent execution task."""
    import json
    import asyncio

    # Deserialize TaskSpec
    task_spec = json.loads(task_spec_json)
    agent_type = task_spec["agent"]

    logger.info(
        f"Executing agent {agent_type} - Task ID: {node_id}",
        extra={
            "task_id": node_id,
            "agent_type": agent_type,
            "project_id": project_id,
            "run_id": run_id,
        },
    )

    # Execute the agent directly
    try:
        # Get task execution data from task_spec
        task_execution_data = task_spec.get("inputs_json", {})
        if isinstance(task_execution_data, str):
            task_execution_data = json.loads(task_execution_data)

        # Execute the agent synchronously
        result = asyncio.run(
            execute_agent_task(
                agent_type=agent_type,
                task_execution_data=task_execution_data,
                project_id=project_id,
                run_id=run_id,
                node_id=node_id,
            )
        )

        return {
            "task_id": node_id,
            "agent_type": agent_type,
            "status": "completed",
            "result": result,
        }
    except Exception as e:
        logger.error(f"Agent execution failed: {e}")
        return {
            "task_id": node_id,
            "agent_type": agent_type,
            "status": "failed",
            "error": str(e),
        }


# ============================================================================
# PIPELINE EXECUTION TASK
# ============================================================================


@app.task(name="workers.agent_tasks.test_task")
def test_task():
    """Simple test task to verify task registration."""
    return {"status": "success", "message": "Test task executed"}


@app.task(name="workers.agent_tasks.execute_pipeline")
def execute_pipeline(
    run_id: str, project_id: str, pipeline_name: str = "software_factory_v1"
):
    """Execute a pipeline using the MetaOrchestrator."""
    import asyncio
    import logging

    logger = logging.getLogger(__name__)
    logger.info(f"🚀 CELERY PIPELINE TASK STARTED for run: {run_id}")

    try:
        # Import MetaOrchestrator
        from opsvi_auto_forge.application.orchestrator.meta_orchestrator import (
            MetaOrchestrator,
        )
        from opsvi_auto_forge.infrastructure.memory.graph.client import Neo4jClient

        logger.info(f"🚀 Step 1: Initializing Neo4j client for run {run_id}")
        # Initialize Neo4j client
        neo4j_client = Neo4jClient()

        logger.info(f"🚀 Step 2: Initializing orchestrator for run {run_id}")
        # Initialize orchestrator
        orchestrator = MetaOrchestrator(neo4j_client)

        logger.info(
            f"🚀 Step 3: Starting pipeline for run {run_id}, project {project_id}"
        )
        # Start pipeline using MetaOrchestrator
        context = asyncio.run(
            orchestrator.start_pipeline(
                project_id=project_id,
                run_id=run_id,
                pipeline_name=pipeline_name,
            )
        )

        logger.info(
            f"🚀 Step 4: Pipeline started successfully for run {run_id}, DAG ID: {context.dag_id}"
        )

        logger.info(f"🚀 Step 5: Executing pipeline for run {run_id}")
        # Execute pipeline
        result = asyncio.run(orchestrator.execute_pipeline(context))

        logger.info(
            f"🚀 Step 6: Pipeline execution completed for run {run_id}, result: {result}"
        )

        if result.get("success", False):
            logger.info(f"🟢 Pipeline execution SUCCESS for run {run_id}")
            return {
                "status": "success",
                "run_id": run_id,
                "result": result,
            }
        else:
            logger.error(f"🔴 Pipeline execution FAILED for run {run_id}")
            return {
                "status": "failed",
                "run_id": run_id,
                "error": "Pipeline execution failed",
                "result": result,
            }

    except Exception as e:
        logger.error(f"🔴 CELERY PIPELINE TASK FAILED for run {run_id}: {str(e)}")
        import traceback

        logger.error(f"🔴 Traceback: {traceback.format_exc()}")

        return {
            "status": "failed",
            "run_id": run_id,
            "error": str(e),
        }


async def _process_validation_failure(
    result_dict: Dict[str, Any],
    validation_result: Any,
    agent_type: str,
    task_execution: Any,
    project_id: Optional[str] = None,
    run_id: Optional[str] = None,
    node_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Process validation failure by attempting repair with retry logic."""
    from tenacity import retry, stop_after_attempt, wait_exponential
    from opsvi_auto_forge.agents.concrete_repair_agent import ConcreteRepairAgent
    from opsvi_auto_forge.agents.base_repair_agent import RepairRequest, Artifact
    from opsvi_auto_forge.infrastructure.memory.graph.client import Neo4jClient
    from opsvi_auto_forge.config.settings import settings

    max_retries = getattr(settings, "repair_max_retries", 3)

    @retry(
        stop=stop_after_attempt(max_retries),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True,
    )
    async def attempt_repair(attempt: int) -> Optional[Dict[str, Any]]:
        """Attempt repair with exponential backoff."""
        logger.info(f"Repair attempt {attempt + 1}/{max_retries} for {agent_type}")

        try:
            # Create Neo4j client for lineage tracking
            neo4j_client = Neo4jClient(
                uri=settings.neo4j_uri,
                username=settings.neo4j_username,
                password=settings.neo4j_password,
            )

            # Create repair agent
            repair_agent = ConcreteRepairAgent(
                name=f"RepairAgent_{agent_type}",
                description=f"Repair agent for {agent_type} validation failures",
                neo4j_client=neo4j_client,
            )

            # Determine issue type from validation result
            issue_type = _determine_issue_type(validation_result)

            # Create artifact from failed result
            artifact = Artifact(
                id=str(task_execution.id),
                type="agent_output",
                metadata={
                    "content": str(result_dict),
                    "agent_type": agent_type,
                    "validation_errors": validation_result.details,
                    "project_id": project_id,
                    "run_id": run_id,
                    "node_id": node_id,
                },
            )

            # Create repair request
            repair_request = RepairRequest(
                artifact=artifact,
                issue_type=issue_type,
                issue_description=f"Validation failed: {validation_result.details}",
                context={
                    "agent_type": agent_type,
                    "project_id": project_id,
                    "run_id": run_id,
                    "node_id": node_id,
                    "attempt": attempt + 1,
                },
            )

            # Attempt repair
            repair_result = await repair_agent.repair_artifact(repair_request)

            if repair_result.success and repair_result.fixed_artifact:
                logger.info(
                    f"Repair successful for {agent_type}, attempt {attempt + 1}"
                )

                # Extract repaired content
                repaired_content = repair_result.fixed_artifact.metadata.get(
                    "content", ""
                )

                # Try to parse the repaired content back to dict
                try:
                    import ast

                    if isinstance(repaired_content, str):
                        # Try to evaluate as Python literal
                        repaired_dict = ast.literal_eval(repaired_content)
                    else:
                        repaired_dict = repaired_content

                    # Re-validate the repaired result
                    if hasattr(validation_result, "validator"):
                        new_validation = validation_result.validator(repaired_dict)
                        if new_validation.passed:
                            logger.info(
                                f"Repaired result passes validation for {agent_type}"
                            )
                            return repaired_dict
                        else:
                            logger.warning(
                                f"Repaired result still fails validation: {new_validation.details}"
                            )
                            raise ValueError("Repaired result still invalid")
                    else:
                        # If no validator, assume success
                        return repaired_dict

                except (ValueError, SyntaxError) as e:
                    logger.warning(f"Failed to parse repaired content: {e}")
                    raise ValueError(f"Repair parsing failed: {e}")
            else:
                logger.warning(
                    f"Repair failed for {agent_type}: {repair_result.error_message}"
                )
                raise ValueError(f"Repair failed: {repair_result.error_message}")

        except Exception as e:
            logger.error(f"Repair attempt {attempt + 1} failed for {agent_type}: {e}")
            if attempt + 1 >= max_retries:
                logger.error(f"All repair attempts failed for {agent_type}")
                return None
            raise  # Retry

    try:
        return await attempt_repair(0)
    except Exception as e:
        logger.error(f"All repair attempts exhausted for {agent_type}: {e}")
        return None


def _determine_issue_type(validation_result: Any) -> str:
    """Determine the issue type from validation result details."""
    details = str(validation_result.details).lower()

    if any(keyword in details for keyword in ["syntax", "indentation", "parse"]):
        return "syntax_error"
    elif any(
        keyword in details for keyword in ["security", "vulnerability", "injection"]
    ):
        return "security_vulnerability"
    elif any(keyword in details for keyword in ["performance", "slow", "efficiency"]):
        return "performance_issue"
    elif any(keyword in details for keyword in ["style", "format", "pep8"]):
        return "code_style"
    elif any(keyword in details for keyword in ["import", "module", "package"]):
        return "missing_import"
    elif any(keyword in details for keyword in ["type", "attribute", "method"]):
        return "type_error"
    else:
        return "validation_error"
