"""Prompt Gateway for intercepting and enhancing OpenAI Responses API calls."""

import json
import logging
import time
from typing import Any, Dict, List, Optional, Union, Generator, Type
from datetime import datetime

from openai.types.responses import Response, ResponseStreamEvent

from opsvi_pipeline.infrastructure.llm.openai_client import OpenAIResponsesClient
from opsvi_pipeline.core.prompting.models import PromptPack
from opsvi_pipeline.core.prompting.pga import PromptGenerationAgent
from opsvi_pipeline.core.decision_kernel.interfaces import IPromptGateway

logger = logging.getLogger(__name__)


class PromptGateway(IPromptGateway):
    """Gateway that intercepts OpenAI calls and applies DPG."""

    def __init__(
        self,
        openai_client: OpenAIResponsesClient,
        pga: PromptGenerationAgent,
    ):
        """Initialize the Prompt Gateway.

        Args:
            openai_client: OpenAI client instance
            pga: Prompt Generation Agent
        """
        self.openai_client = openai_client
        self.pga = pga
        self.cache: Dict[str, PromptPack] = {}

        logger.info("Initialized Prompt Gateway")

    def create_response(
        self,
        run_id: str,
        role: str,
        task_type: str,
        user_goal: str,
        constraints: Optional[Dict[str, Any]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        response_schema: Optional[Dict[str, Any]] = None,
        stream: bool = False,
        **kwargs,
    ) -> Union[Response, Generator[ResponseStreamEvent, None, None]]:
        """Create a response using DPG-enhanced prompt.

        Args:
            run_id: Run identifier
            role: Agent role
            task_type: Task type
            user_goal: User's goal/request
            constraints: Additional constraints
            tools: Available tools
            response_schema: Expected response schema
            stream: Whether to enable streaming
            **kwargs: Additional parameters

        Returns:
            OpenAI response or stream
        """
        start_time = time.time()

        try:
            # Step 1: Generate PromptPack
            prompt_pack = self.pga.build_prompt_pack(
                run_id=run_id,
                role=role,
                task_type=task_type,
                user_goal=user_goal,
                constraints=constraints,
                tools=tools,
                response_schema=response_schema,
                stream=stream,
            )

            # Step 2: Check cache for similar prompts
            cache_key = self._compute_cache_key(prompt_pack)
            if cache_key in self.cache:
                logger.info(f"Cache hit for prompt pack {prompt_pack.id}")
                # Use cached version but update metadata
                cached_pack = self.cache[cache_key]
                prompt_pack.id = cached_pack.id
                prompt_pack.created_at = cached_pack.created_at

            # Step 3: Convert to OpenAI parameters
            openai_params = prompt_pack.to_openai_params()

            # Step 4: Apply DPG-specific configurations
            self._apply_dpg_configurations(openai_params, prompt_pack)

            # Step 5: Make OpenAI call
            if stream:
                response = self.openai_client.client.responses.create(
                    stream=True, **openai_params
                )
            else:
                response = self.openai_client.client.responses.create(**openai_params)

            # Step 6: Process response
            latency = time.time() - start_time
            self._process_response(response, prompt_pack, latency)

            # Step 7: Cache the prompt pack
            self.cache[cache_key] = prompt_pack

            logger.info(f"Completed DPG-enhanced response in {latency:.2f}s")
            return response

        except Exception as e:
            logger.error(f"Error in PromptGateway: {e}")
            raise

    async def create_structured_response(
        self,
        run_id: str,
        role: str,
        task_type: str,
        user_goal: str,
        schema: Union[Dict[str, Any], type],
        constraints: Optional[Dict[str, Any]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        verifier_model: str = "gpt-4o-mini",
        max_repair_attempts: int = 1,
        **kwargs,
    ) -> Any:
        """Create a structured response using DPG with verification and auto-repair.

        Args:
            run_id: Run identifier
            role: Agent role
            task_type: Task type
            user_goal: User's goal/request
            schema: Response schema
            constraints: Additional constraints
            tools: Available tools
            verifier_model: Model to use for verification
            max_repair_attempts: Maximum repair attempts before hard fail
            **kwargs: Additional parameters

        Returns:
            Structured response
        """
        start_time = time.time()

        try:
            # Generate PromptPack with structured output
            prompt_pack = self.pga.build_prompt_pack(
                run_id=run_id,
                role=role,
                task_type=task_type,
                user_goal=user_goal,
                constraints=constraints,
                tools=tools,
                response_schema=schema,
                stream=False,  # Structured outputs can't be streamed
            )

            # Convert to OpenAI parameters
            openai_params = prompt_pack.to_openai_params()

            # Disable parallel tool calls for structured outputs
            if "parallel_tool_calls" in openai_params:
                openai_params["parallel_tool_calls"] = False

            # Make OpenAI call using the structured method
            if isinstance(schema, type):
                # Schema is a Pydantic class
                response = self.openai_client.create_structured(
                    model=openai_params["model"],
                    schema=schema,
                    input_text=openai_params["input"],
                    instructions=openai_params.get("instructions"),
                    temperature=openai_params.get("temperature", 0.1),
                )
                return response
            else:
                # Schema is a dict, use regular API call
                response = self.openai_client.client.responses.create(**openai_params)

            # Process response
            latency = time.time() - start_time
            self._process_response(response, prompt_pack, latency)

            # Parse structured response
            if hasattr(response, "output_text"):
                try:
                    import json

                    parsed_response = json.loads(response.output_text)

                    # Verify the response
                    from opsvi_pipeline.core.decision_kernel.verification import (
                        verify_output,
                    )

                    passed, score, rationale, agreement_rate = await verify_output(
                        parsed_response, schema, verifier_model
                    )

                    if not passed:
                        # Try auto-repair up to max_repair_attempts
                        logger.warning(
                            f"Schema validation failed, attempting auto-repair: {rationale}"
                        )

                        for attempt in range(max_repair_attempts):
                            repaired_response = await self._attempt_auto_repair(
                                parsed_response, schema, user_goal, openai_params
                            )

                            if repaired_response:
                                # Verify the repaired response
                                (
                                    passed,
                                    score,
                                    rationale,
                                    agreement_rate,
                                ) = await verify_output(
                                    repaired_response, schema, verifier_model
                                )

                                if passed:
                                    logger.info(
                                        f"Auto-repair successful on attempt {attempt + 1}"
                                    )
                                    return repaired_response
                                else:
                                    logger.warning(
                                        f"Auto-repair attempt {attempt + 1} failed: {rationale}"
                                    )
                                    parsed_response = repaired_response  # Use repaired as base for next attempt
                            else:
                                logger.error(
                                    f"Auto-repair attempt {attempt + 1} failed"
                                )
                                break

                        # All repair attempts failed
                        logger.error(
                            f"All repair attempts failed. Final rationale: {rationale}"
                        )
                        raise ValueError(
                            f"Schema validation failed after {max_repair_attempts} repair attempts: {rationale}"
                        )

                    return parsed_response

                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse structured response: {e}")
                    raise
            else:
                logger.error("Response does not have output_text attribute")
                raise ValueError("Invalid response format")

        except Exception as e:
            logger.error(f"Error in structured response: {e}")
            raise

    async def _attempt_auto_repair(
        self,
        failed_response: Any,
        schema: Union[Dict[str, Any], type],
        user_goal: str,
        openai_params: Dict[str, Any],
    ) -> Optional[Any]:
        """Attempt to auto-repair a failed structured response."""
        try:
            # Create repair prompt
            repair_prompt = self._create_repair_prompt(
                failed_response, schema, user_goal
            )

            # Make repair call with different model if available
            repair_params = openai_params.copy()
            repair_params["input"] = repair_prompt
            repair_params["temperature"] = 0.1  # Lower temperature for repair

            # Use a more capable model for repair if available
            if "model" in repair_params and repair_params["model"] == "o4-mini":
                repair_params["model"] = "gpt-4o-mini"

            response = self.openai_client.client.responses.create(**repair_params)

            if hasattr(response, "output_text"):
                import json

                try:
                    return json.loads(response.output_text)
                except json.JSONDecodeError:
                    logger.error("Repair response is not valid JSON")
                    return None
            else:
                logger.error("Repair response does not have output_text")
                return None

        except Exception as e:
            logger.error(f"Auto-repair failed: {e}")
            return None

    def _create_repair_prompt(
        self, failed_response: Any, schema: Union[Dict[str, Any], type], user_goal: str
    ) -> str:
        """Create a prompt for auto-repair."""
        schema_str = str(schema)
        failed_str = (
            json.dumps(failed_response, indent=2)
            if isinstance(failed_response, (dict, list))
            else str(failed_response)
        )

        return f"""
        The previous response failed schema validation. Please fix the response to match the schema exactly.

        Original goal: {user_goal}
        Schema: {schema_str}
        Failed response: {failed_str}

        Common issues to fix:
        1. Missing required fields
        2. Wrong data types (string vs number vs boolean)
        3. Invalid enum values
        4. Nested object structure mismatches
        5. Array item validation failures

        Please provide a corrected response that matches the schema exactly. Return only valid JSON.
        """

    def create_with_reasoning(
        self,
        run_id: str,
        role: str,
        task_type: str,
        user_goal: str,
        effort: str = "medium",
        include_encrypted: bool = False,
        constraints: Optional[Dict[str, Any]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> Response:
        """Create a response with reasoning using DPG.

        Args:
            run_id: Run identifier
            role: Agent role
            task_type: Task type
            user_goal: User's goal/request
            effort: Reasoning effort level
            include_encrypted: Whether to include encrypted reasoning
            constraints: Additional constraints
            tools: Available tools
            **kwargs: Additional parameters

        Returns:
            Response with reasoning
        """
        start_time = time.time()

        try:
            # Generate PromptPack with reasoning
            prompt_pack = self.pga.build_prompt_pack(
                run_id=run_id,
                role=role,
                task_type=task_type,
                user_goal=user_goal,
                constraints=constraints,
                tools=tools,
                stream=False,
            )

            # Configure reasoning
            prompt_pack.controls.reasoning = {"effort": effort, "summary": "auto"}

            if include_encrypted:
                prompt_pack.controls.include = ["reasoning.encrypted_content"]

            # Convert to OpenAI parameters
            openai_params = prompt_pack.to_openai_params()

            # Make OpenAI call
            response = self.openai_client.client.responses.create(**openai_params)

            # Process response
            latency = time.time() - start_time
            self._process_response(response, prompt_pack, latency)

            return response

        except Exception as e:
            logger.error(f"Error in reasoning response: {e}")
            raise

    def create_background_task(
        self,
        run_id: str,
        role: str,
        task_type: str,
        user_goal: str,
        constraints: Optional[Dict[str, Any]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> Response:
        """Create a background task using DPG.

        Args:
            run_id: Run identifier
            role: Agent role
            task_type: Task type
            user_goal: User's goal/request
            constraints: Additional constraints
            tools: Available tools
            **kwargs: Additional parameters

        Returns:
            Background task response
        """
        start_time = time.time()

        try:
            # Generate PromptPack for background task
            prompt_pack = self.pga.build_prompt_pack(
                run_id=run_id,
                role=role,
                task_type=task_type,
                user_goal=user_goal,
                constraints=constraints,
                tools=tools,
                stream=False,
            )

            # Configure for background execution
            prompt_pack.controls.background = True
            prompt_pack.controls.include = ["reasoning.encrypted_content"]

            # Convert to OpenAI parameters
            openai_params = prompt_pack.to_openai_params()

            # Make OpenAI call
            response = self.openai_client.client.responses.create(**openai_params)

            # Process response
            latency = time.time() - start_time
            self._process_response(response, prompt_pack, latency)

            return response

        except Exception as e:
            logger.error(f"Error in background task: {e}")
            raise

    def _compute_cache_key(self, prompt_pack: PromptPack) -> str:
        """Compute cache key for prompt pack.

        Args:
            prompt_pack: The prompt pack

        Returns:
            Cache key
        """
        # Use the cache keys from the prompt pack
        cache_keys = prompt_pack.controls.cache_keys
        key_parts = [
            cache_keys.get("system_hash", ""),
            cache_keys.get("tools_hash", ""),
            cache_keys.get("context_hash", ""),
            prompt_pack.model,
            str(prompt_pack.controls.stream),
        ]

        return "|".join(key_parts)

    def _apply_dpg_configurations(
        self, openai_params: Dict[str, Any], prompt_pack: PromptPack
    ):
        """Apply DPG-specific configurations to OpenAI parameters.

        Args:
            openai_params: OpenAI parameters to modify
            prompt_pack: The prompt pack
        """
        # Ensure strict function validation
        if "tools" in openai_params:
            for tool in openai_params["tools"]:
                if tool.get("type") == "function" and "function" in tool:
                    tool["function"]["strict"] = True

        # Configure response format for structured outputs
        if prompt_pack.response_format.get("type") == "json_schema":
            openai_params["response_format"] = prompt_pack.response_format
            # Disable parallel tool calls for structured outputs
            openai_params["parallel_tool_calls"] = False

        # Configure reasoning for o-series models
        if prompt_pack.model.startswith("o") and prompt_pack.controls.reasoning:
            openai_params["reasoning"] = prompt_pack.controls.reasoning

        # Configure background mode
        if prompt_pack.controls.background:
            openai_params["background"] = True

        # Configure include items
        if prompt_pack.controls.include:
            openai_params["include"] = prompt_pack.controls.include

    def _process_response(
        self, response: Response, prompt_pack: PromptPack, latency: float
    ):
        """Process the response and update metrics.

        Args:
            response: OpenAI response
            prompt_pack: The prompt pack used
            latency: Response latency
        """
        try:
            # Extract metrics from response
            usage = getattr(response, "usage", None)
            tokens_used = usage.total_tokens if usage else 0

            # Update prompt profile
            profile = self.pga.get_prompt_profile(
                prompt_pack.routing.role, prompt_pack.routing.task_type
            )

            if profile is None:
                profile = PromptProfile(
                    role=prompt_pack.routing.role,
                    task_type=prompt_pack.routing.task_type,
                )

            # Determine success based on response status
            success = hasattr(response, "status") and response.status == "completed"

            # Update profile
            profile.update_from_result(
                success=success,
                tokens=tokens_used,
                latency=latency,
                model=prompt_pack.model,
            )

            # Persist updated profile
            self.pga.update_prompt_profile(profile)

            logger.info(
                f"Updated profile for {profile.role}/{profile.task_type}: "
                f"success_rate={profile.success_rate:.2f}, "
                f"avg_tokens={profile.avg_tokens:.0f}, "
                f"avg_latency={profile.avg_latency:.2f}s"
            )

        except Exception as e:
            logger.error(f"Failed to process response: {e}")

    def get_prompt_pack(self, pack_id: str) -> Optional[PromptPack]:
        """Get a prompt pack by ID.

        Args:
            pack_id: Prompt pack ID

        Returns:
            Prompt pack if found
        """
        # Check cache first
        for pack in self.cache.values():
            if pack.id == pack_id:
                return pack

        # Query from Neo4j (simplified - in real implementation you'd query the graph)
        logger.warning(f"Prompt pack {pack_id} not found in cache")
        return None

    def list_recent_prompt_packs(self, limit: int = 10) -> List[PromptPack]:
        """List recent prompt packs.

        Args:
            limit: Maximum number of packs to return

        Returns:
            List of recent prompt packs
        """
        # Return cached packs sorted by creation time
        sorted_packs = sorted(
            self.cache.values(), key=lambda p: p.created_at, reverse=True
        )

        return sorted_packs[:limit]

    def clear_cache(self):
        """Clear the prompt pack cache."""
        self.cache.clear()
        logger.info("Cleared prompt pack cache")

    def get_stats(self) -> Dict[str, Any]:
        """Get gateway statistics.

        Returns:
            Dictionary with statistics
        """
        return {
            "cached_packs": len(self.cache),
            "cache_keys": list(self.cache.keys())[:5],  # First 5 keys
        }
