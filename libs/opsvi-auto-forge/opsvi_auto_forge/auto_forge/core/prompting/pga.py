"""Prompt Generation Agent (PGA) for Dynamic Prompt Generation."""

import logging
from typing import Any, Dict, List, Optional, Tuple

from opsvi_auto_forge.infrastructure.memory.graph.client import Neo4jClient
from opsvi_auto_forge.infrastructure.memory.vector.context_store import ContextStore
from opsvi_auto_forge.core.prompting.models import (
    PromptPack,
    ContextBundle,
    PromptProfile,
    RoutingConfig,
    Controls,
    SafetyConfig,
)

logger = logging.getLogger(__name__)


class PromptGenerationAgent:
    """Agent responsible for generating context-aware PromptPacks."""

    def __init__(
        self,
        neo4j_client: Neo4jClient,
        context_store: ContextStore,
        default_models: Optional[Dict[str, str]] = None,
    ):
        """Initialize the Prompt Generation Agent.

        Args:
            neo4j_client: Neo4j client for graph queries
            context_store: Context store for bundles
            default_models: Default model mapping for roles/tasks
        """
        self.neo4j_client = neo4j_client
        self.context_store = context_store

        # Default model routing
        self.default_models = default_models or {
            "conversation": "gpt-4.1-mini",
            "coding": "gpt-4.1-mini",
            "planning": "o4-mini",
            "reasoning": "o4-mini",
            "testing": "gpt-4.1-mini",
            "validation": "gpt-4.1-mini",
        }

        # Model complexity thresholds
        self.complexity_thresholds = {
            "low": 1000,  # < 1k tokens
            "medium": 10000,  # 1k-10k tokens
            "high": 100000,  # 10k-100k tokens
        }

        logger.info("Initialized Prompt Generation Agent")

    async def build_prompt_pack(
        self,
        run_id: str,
        role: str,
        task_type: str,
        user_goal: str,
        constraints: Optional[Dict[str, Any]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        response_schema: Optional[Dict[str, Any]] = None,
        stream: bool = False,
    ) -> PromptPack:
        """Build a complete PromptPack for a task.

        Args:
            run_id: Run identifier
            role: Agent role
            task_type: Type of task
            user_goal: User's goal/request
            constraints: Additional constraints
            tools: Available tools
            response_schema: Expected response schema
            stream: Whether to enable streaming

        Returns:
            Complete PromptPack
        """
        logger.info(f"Building PromptPack for {role}/{task_type}: {user_goal[:100]}...")

        # Step 1: Gather context
        context_bundles = await self._gather_context(role, task_type, user_goal)

        # Step 2: Determine model and routing
        model, complexity = self._select_model_and_complexity(
            role, task_type, context_bundles
        )

        # Step 3: Compress context
        compressed_bundles = self._compress_context(context_bundles, complexity)

        # Step 4: Build messages
        messages = self._build_messages(
            role, task_type, user_goal, compressed_bundles, constraints
        )

        # Step 5: Configure tools
        final_tools = self._configure_tools(tools or [])

        # Step 6: Configure response format
        response_format = self._configure_response_format(
            response_schema, role, task_type
        )

        # Step 7: Configure controls
        controls = self._configure_controls(
            stream, model, response_format, role, task_type
        )

        # Step 8: Configure routing
        routing = self._configure_routing(role, task_type, complexity, model)

        # Step 9: Configure safety
        safety = self._configure_safety(role, task_type, constraints)

        # Step 10: Create PromptPack
        prompt_pack = PromptPack(
            model=model,
            messages=messages,
            tools=final_tools,
            response_format=response_format,
            routing=routing,
            controls=controls,
            context_bundles=compressed_bundles,
            safety=safety,
        )

        # Step 11: Compute cache keys
        prompt_pack.controls.cache_keys = prompt_pack.compute_cache_keys()

        # Step 12: Estimate tokens
        prompt_pack.estimated_tokens = self._estimate_tokens(prompt_pack)

        # Step 13: Persist to Neo4j
        await self._persist_prompt_pack(prompt_pack, run_id)

        logger.info(
            f"Built PromptPack {prompt_pack.id} with {prompt_pack.estimated_tokens} tokens"
        )
        return prompt_pack

    async def _gather_context(
        self, role: str, task_type: str, goal: str
    ) -> List[ContextBundle]:
        """Gather relevant context from memory.

        Args:
            role: Agent role
            task_type: Task type
            goal: User goal

        Returns:
            List of relevant context bundles
        """
        bundles = []

        # Get context bundles from vector store if available
        if self.context_store is not None:
            try:
                bundles = self.context_store.get_bundles_for_task(
                    task_type=task_type,
                    role=role,
                    goal=goal,
                    max_tokens=10000,  # Conservative limit
                )
            except Exception as e:
                logger.warning(f"Failed to get context bundles from vector store: {e}")
                bundles = []

        # Get recent critiques and outcomes from Neo4j
        recent_context = await self._get_recent_context(role, task_type)
        if recent_context:
            bundles.extend(recent_context)

        logger.info(f"Gathered {len(bundles)} context bundles")
        return bundles

    async def _get_recent_context(
        self, role: str, task_type: str
    ) -> List[ContextBundle]:
        """Get recent context from Neo4j graph.

        Args:
            role: Agent role
            task_type: Task type

        Returns:
            List of context bundles from recent runs
        """
        if self.neo4j_client is None:
            logger.debug("Neo4j client not available, skipping recent context")
            return []

        try:
            # Query recent critiques and outcomes
            query = """
            MATCH (c:Critique)-[:FOR_TASK]->(t:Task)
            WHERE t.agent_role = $role AND t.task_type = $task_type
            RETURN c.score, c.reasons, c.patch_plan
            ORDER BY c.created_at DESC
            LIMIT 5
            """

            results = await self.neo4j_client.execute_query(
                query, {"role": role, "task_type": task_type}
            )

            bundles = []
            for result in results:
                if result.get("c.score"):
                    bundle = ContextBundle(
                        purpose="recent_critique",
                        tokens=200,  # Estimate
                        summary=f"Recent critique score: {result['c.score']}. Reasons: {', '.join(result.get('c.reasons', []))}",
                        sources=[f"critique_{result.get('id', 'unknown')}"],
                    )
                    bundles.append(bundle)

            return bundles

        except Exception as e:
            logger.warning(f"Failed to get recent context from Neo4j: {e}")
            return []

    def _select_model_and_complexity(
        self, role: str, task_type: str, context_bundles: List[ContextBundle]
    ) -> Tuple[str, str]:
        """Select appropriate model and complexity level.

        Args:
            role: Agent role
            task_type: Task type
            context_bundles: Context bundles

        Returns:
            Tuple of (model, complexity)
        """
        # Calculate total context tokens
        total_tokens = sum(bundle.tokens for bundle in context_bundles)

        # Determine complexity
        if total_tokens < self.complexity_thresholds["low"]:
            complexity = "low"
        elif total_tokens < self.complexity_thresholds["medium"]:
            complexity = "medium"
        else:
            complexity = "high"

        # Select model based on role, task, and complexity
        if role == "planner" or task_type in ["planning", "reasoning"]:
            if complexity == "high":
                model = "o3"
            else:
                model = "o4-mini"
        elif complexity == "high" and total_tokens > 150000:
            model = "gpt-4.1"  # Use full context for very large inputs
        else:
            model = self.default_models.get(task_type, "gpt-4.1-mini")

        logger.info(
            f"Selected model {model} for complexity {complexity} ({total_tokens} tokens)"
        )
        return model, complexity

    def _compress_context(
        self, bundles: List[ContextBundle], complexity: str
    ) -> List[ContextBundle]:
        """Compress context bundles to fit within limits.

        Args:
            bundles: Original context bundles
            complexity: Task complexity

        Returns:
            Compressed context bundles
        """
        # Get token budget based on complexity
        budget = self.complexity_thresholds.get(complexity, 10000)

        # Sort by relevance (assuming bundles are already sorted by relevance)
        compressed = []
        total_tokens = 0

        for bundle in bundles:
            if total_tokens + bundle.tokens <= budget:
                compressed.append(bundle)
                total_tokens += bundle.tokens
            else:
                # Try to compress this bundle
                compressed_bundle = self._compress_single_bundle(
                    bundle, budget - total_tokens
                )
                if compressed_bundle:
                    compressed.append(compressed_bundle)
                    total_tokens += compressed_bundle.tokens
                break

        logger.info(
            f"Compressed {len(bundles)} bundles to {len(compressed)} ({total_tokens} tokens)"
        )
        return compressed

    def _compress_single_bundle(
        self, bundle: ContextBundle, available_tokens: int
    ) -> Optional[ContextBundle]:
        """Compress a single context bundle.

        Args:
            bundle: Original bundle
            available_tokens: Available token budget

        Returns:
            Compressed bundle or None if too large
        """
        if bundle.tokens <= available_tokens:
            return bundle

        # Simple compression: truncate summary
        # In a real implementation, you'd use a more sophisticated compression
        max_chars = available_tokens * 4  # Rough estimate: 4 chars per token
        compressed_summary = (
            bundle.summary[:max_chars] + "..."
            if len(bundle.summary) > max_chars
            else bundle.summary
        )

        return ContextBundle(
            purpose=bundle.purpose + "_compressed",
            tokens=len(compressed_summary) // 4,  # Rough estimate
            summary=compressed_summary,
            sources=bundle.sources,
        )

    def _build_messages(
        self,
        role: str,
        task_type: str,
        goal: str,
        bundles: List[ContextBundle],
        constraints: Optional[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Build message history for the prompt.

        Args:
            role: Agent role
            task_type: Task type
            goal: User goal
            bundles: Context bundles
            constraints: Additional constraints

        Returns:
            List of messages
        """
        messages = []

        # System message
        system_content = self._build_system_message(role, task_type, constraints)
        messages.append({"role": "system", "content": system_content})

        # Context summary (if bundles exist)
        if bundles:
            context_summary = self._build_context_summary(bundles)
            messages.append(
                {"role": "assistant", "content": f"Context summary: {context_summary}"}
            )

        # User message
        messages.append({"role": "user", "content": goal})

        return messages

    def _build_system_message(
        self, role: str, task_type: str, constraints: Optional[Dict[str, Any]]
    ) -> str:
        """Build system message for the agent.

        Args:
            role: Agent role
            task_type: Task type
            constraints: Additional constraints

        Returns:
            System message content
        """
        base_messages = {
            "planner": "You are a planning agent responsible for breaking down complex tasks into actionable steps.",
            "coder": "You are a coding agent responsible for implementing software solutions with high quality and best practices.",
            "tester": "You are a testing agent responsible for creating comprehensive test suites and validating functionality.",
            "critic": "You are a critic agent responsible for evaluating work quality and providing constructive feedback.",
            "architect": "You are an architect agent responsible for designing system architecture and technical specifications.",
        }

        system_content = base_messages.get(
            role, f"You are a {role} agent responsible for {task_type} tasks."
        )

        # Add task-specific instructions
        if task_type == "planning":
            system_content += " Focus on creating clear, actionable plans with dependencies and timelines."
        elif task_type == "coding":
            system_content += " Write clean, maintainable code with proper error handling and documentation."
        elif task_type == "testing":
            system_content += (
                " Create comprehensive tests covering edge cases and error conditions."
            )

        # Add constraints
        if constraints:
            constraint_text = " ".join([f"{k}: {v}" for k, v in constraints.items()])
            system_content += f" Constraints: {constraint_text}"

        return system_content

    def _build_context_summary(self, bundles: List[ContextBundle]) -> str:
        """Build a summary of context bundles.

        Args:
            bundles: Context bundles

        Returns:
            Context summary
        """
        if not bundles:
            return "No relevant context available."

        summaries = []
        for bundle in bundles:
            summaries.append(f"{bundle.purpose}: {bundle.summary}")

        return " | ".join(summaries)

    def _configure_tools(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Configure tools for the prompt.

        Args:
            tools: Available tools

        Returns:
            Configured tools with strict validation
        """
        configured_tools = []

        for tool in tools:
            if tool.get("type") == "function":
                # Ensure strict validation
                if "function" in tool:
                    tool["function"]["strict"] = True
            configured_tools.append(tool)

        return configured_tools

    def _configure_response_format(
        self, schema: Optional[Dict[str, Any]], role: str, task_type: str
    ) -> Dict[str, Any]:
        """Configure response format.

        Args:
            schema: Expected response schema
            role: Agent role
            task_type: Task type

        Returns:
            Response format configuration
        """
        if schema:
            return {
                "type": "json_schema",
                "json_schema": {
                    "name": f"{role}_{task_type}_response",
                    "strict": True,
                    "schema": schema,
                },
            }

        # Default to text format
        return {"type": "text"}

    def _configure_controls(
        self,
        stream: bool,
        model: str,
        response_format: Dict[str, Any],
        role: str,
        task_type: str,
    ) -> Controls:
        """Configure control parameters.

        Args:
            stream: Whether to enable streaming
            model: Selected model
            response_format: Response format
            role: Agent role
            task_type: Task type

        Returns:
            Controls configuration
        """
        controls = Controls(
            stream=stream,
            parallel_tool_calls=False,  # Disable for structured outputs
            background=False,
            include=[],
            reasoning={},
        )

        # Configure for o-series models
        if model.startswith("o"):
            controls.reasoning = {
                "effort": (
                    "high" if task_type in ["planning", "reasoning"] else "medium"
                ),
                "summary": "auto",
            }

            # Enable background for long tasks
            if task_type in ["planning", "reasoning"]:
                controls.background = True
                controls.include = ["reasoning.encrypted_content"]

        # Disable parallel tool calls for structured outputs
        if response_format.get("type") == "json_schema":
            controls.parallel_tool_calls = False

        return controls

    def _configure_routing(
        self, role: str, task_type: str, complexity: str, model: str
    ) -> RoutingConfig:
        """Configure routing parameters.

        Args:
            role: Agent role
            task_type: Task type
            complexity: Task complexity
            model: Selected model

        Returns:
            Routing configuration
        """
        # Determine confidence threshold based on complexity
        confidence_threshold = {"low": 0.8, "medium": 0.85, "high": 0.9}.get(
            complexity, 0.85
        )

        # Determine escalation models
        escalation = []
        if model == "o4-mini" and complexity == "high":
            escalation = ["o3"]
        elif model == "gpt-4.1-mini" and complexity == "high":
            escalation = ["gpt-4.1"]

        return RoutingConfig(
            role=role,
            task_type=task_type,
            complexity=complexity,
            confidence_threshold=confidence_threshold,
            escalation=escalation,
        )

    def _configure_safety(
        self, role: str, task_type: str, constraints: Optional[Dict[str, Any]]
    ) -> SafetyConfig:
        """Configure safety parameters.

        Args:
            role: Agent role
            task_type: Task type
            constraints: Additional constraints

        Returns:
            Safety configuration
        """
        guardrails = ["no_harmful_content", "no_personal_data"]

        # Add role-specific guardrails
        if role == "coder":
            guardrails.extend(["secure_coding", "no_secrets_in_code"])
        elif role == "critic":
            guardrails.extend(["constructive_feedback", "no_personal_attacks"])

        red_flags = []
        if constraints:
            if constraints.get("security_critical"):
                red_flags.append("security_vulnerabilities")
            if constraints.get("production_deployment"):
                red_flags.append("breaking_changes")

        return SafetyConfig(guardrails=guardrails, red_flags=red_flags)

    def _estimate_tokens(self, prompt_pack: PromptPack) -> int:
        """Estimate total token count for the prompt pack.

        Args:
            prompt_pack: The prompt pack

        Returns:
            Estimated token count
        """
        # Simple token estimation: ~4 characters per token
        total_chars = 0

        # Count message content
        for message in prompt_pack.messages:
            total_chars += len(message.get("content", ""))

        # Count context bundles
        for bundle in prompt_pack.context_bundles:
            total_chars += len(bundle.summary)

        # Add overhead for tools and metadata
        total_chars += 1000  # Rough overhead estimate

        return total_chars // 4

    async def _persist_prompt_pack(self, prompt_pack: PromptPack, run_id: str):
        """Persist PromptPack to Neo4j.

        Args:
            prompt_pack: The prompt pack to persist
            run_id: Run identifier
        """
        try:
            # Create PromptPack node
            query = """
            CREATE (p:PromptPack {
                id: $id,
                role: $role,
                task_type: $task_type,
                model: $model,
                tokens: $tokens,
                system_hash: $system_hash,
                tools_hash: $tools_hash,
                context_hash: $context_hash,
                created_at: datetime()
            })
            """

            cache_keys = prompt_pack.controls.cache_keys
            params = {
                "id": prompt_pack.id,
                "role": prompt_pack.routing.role,
                "task_type": prompt_pack.routing.task_type,
                "model": prompt_pack.model,
                "tokens": prompt_pack.estimated_tokens,
                "system_hash": cache_keys.get("system_hash", ""),
                "tools_hash": cache_keys.get("tools_hash", ""),
                "context_hash": cache_keys.get("context_hash", ""),
            }

            await self.neo4j_client.execute_query(query, params)

            # Link to run
            link_query = """
            MATCH (p:PromptPack {id: $pack_id})
            MATCH (r:Run {id: $run_id})
            CREATE (p)-[:USED_IN]->(r)
            """

            await self.neo4j_client.execute_query(
                link_query, {"pack_id": prompt_pack.id, "run_id": run_id}
            )

            logger.info(f"Persisted PromptPack {prompt_pack.id} to Neo4j")

        except Exception as e:
            logger.error(f"Failed to persist PromptPack to Neo4j: {e}")

    async def get_prompt_profile(
        self, role: str, task_type: str
    ) -> Optional[PromptProfile]:
        """Get prompt profile for optimization.

        Args:
            role: Agent role
            task_type: Task type

        Returns:
            Prompt profile if exists
        """
        try:
            query = """
            MATCH (p:PromptProfile {role: $role, task_type: $task_type})
            RETURN p
            """

            results = await self.neo4j_client.execute_query(
                query, {"role": role, "task_type": task_type}
            )

            if results:
                data = results[0]["p"]
                return PromptProfile(**data)

            return None

        except Exception as e:
            logger.error(f"Failed to get prompt profile: {e}")
            return None

    async def update_prompt_profile(self, profile: PromptProfile):
        """Update prompt profile with new results.

        Args:
            profile: Updated profile
        """
        try:
            query = """
            MERGE (p:PromptProfile {role: $role, task_type: $task_type})
            SET p.wins = $wins,
                p.fails = $fails,
                p.avg_tokens = $avg_tokens,
                p.avg_latency = $avg_latency,
                p.last_success_model = $last_success_model,
                p.confidence_threshold = $confidence_threshold,
                p.updated_at = datetime()
            """

            params = {
                "role": profile.role,
                "task_type": profile.task_type,
                "wins": profile.wins,
                "fails": profile.fails,
                "avg_tokens": profile.avg_tokens,
                "avg_latency": profile.avg_latency,
                "last_success_model": profile.last_success_model,
                "confidence_threshold": profile.confidence_threshold,
            }

            await self.neo4j_client.execute_query(query, params)
            logger.info(
                f"Updated prompt profile for {profile.role}/{profile.task_type}"
            )

        except Exception as e:
            logger.error(f"Failed to update prompt profile: {e}")
