"""
OpenAI adapter with STRICT 2025 model compliance.
NO FORBIDDEN MODELS. NO EXCEPTIONS. NO FALLBACKS.
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add libs to path for shared interfaces
sys.path.insert(0, str(Path(__file__).parents[5] / "libs"))

try:
    from opsvi_llm.interfaces.openai_interface import OpenAIUnifiedInterface
    from opsvi_llm.validators.openai_validator import OpenAIModelValidator
except ImportError:
    # Fallback to direct OpenAI SDK with STRICT validation
    import openai

    OpenAIUnifiedInterface = None
    OpenAIModelValidator = None

from .model_config import ModelConfig

logger = logging.getLogger(__name__)


class OpenAIAdapter:
    """OpenAI adapter with STRICT 2025 model compliance."""

    def __init__(self, model_config: Optional[ModelConfig] = None):
        """Initialize with STRICT model validation."""
        self.model_config = model_config or ModelConfig()
        self.api_key = os.environ.get("OPENAI_API_KEY")

        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        # Use shared interface if available
        if OpenAIUnifiedInterface:
            self.client = OpenAIUnifiedInterface(api_key=self.api_key)
            self.validator = OpenAIModelValidator() if OpenAIModelValidator else None
        else:
            # Direct OpenAI SDK with STRICT validation
            openai.api_key = self.api_key
            self.client = openai
            self.validator = None

    async def analyze_task(
        self, task: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze task to determine type and requirements.
        Uses ONLY approved 2025 models.
        """
        # Get approved model for execution
        model = self.model_config.get_model_for_task("execution")

        # STRICT validation before any API call
        self._validate_model_strict(model)

        prompt = f"""Analyze this task and determine its type and requirements.

Task: {task}

Context: {json.dumps(context) if context else "None"}

Respond with a JSON object containing:
- task_type: One of "code_generation", "reasoning", "planning", "analysis", "general"
- complexity: One of "simple", "moderate", "complex"
- requirements: List of requirements
- suggested_approach: Brief description
"""

        try:
            if self.client and hasattr(self.client, "create_completion"):
                # Use shared interface
                response = await self.client.create_completion(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"},
                )
                result = response.choices[0].message.content
            else:
                # Direct OpenAI SDK
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: openai.ChatCompletion.create(
                        model=model,
                        messages=[{"role": "user", "content": prompt}],
                        response_format={"type": "json_object"},
                    ),
                )
                result = response.choices[0].message.content

            # Parse JSON response with flexible handling
            return self._parse_json_response(result)

        except Exception as e:
            logger.error(f"Task analysis failed with {model}: {e}")
            # Return default analysis, no fallback to forbidden models
            return {
                "task_type": "general",
                "complexity": "moderate",
                "requirements": ["analysis failed"],
                "suggested_approach": "Manual review required",
            }

    async def execute_reasoning(
        self, task: str, context: Optional[Dict[str, Any]] = None, model: Optional[str] = None
    ) -> str:
        """
        Execute reasoning task with STRICT model compliance.
        ONLY uses approved reasoning models (o3, o4-mini).
        """
        if not model:
            model = self.model_config.get_model_for_task("reasoning")

        # STRICT validation
        self._validate_model_strict(model)

        prompt = f"""Perform deep reasoning on this task:

Task: {task}

Context: {json.dumps(context) if context else "None"}

Provide step-by-step reasoning and a clear conclusion."""

        try:
            if self.client and hasattr(self.client, "create_completion"):
                response = await self.client.create_completion(
                    model=model, messages=[{"role": "user", "content": prompt}]
                )
                return response.choices[0].message.content
            else:
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: openai.ChatCompletion.create(
                        model=model, messages=[{"role": "user", "content": prompt}]
                    ),
                )
                return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Reasoning failed with {model}: {e}")
            raise ValueError(f"Reasoning failed. No forbidden models will be used. Error: {e}")

    async def execute_task(
        self, task: str, context: Optional[Dict[str, Any]] = None, model: Optional[str] = None
    ) -> str:
        """
        Execute general task with STRICT model compliance.
        ONLY uses approved execution models (gpt-5 series).
        """
        if not model:
            model = self.model_config.get_model_for_task("execution")

        # STRICT validation
        self._validate_model_strict(model)

        prompt = f"""Execute this task:

Task: {task}

Context: {json.dumps(context) if context else "None"}

Provide a complete and actionable response."""

        try:
            if self.client and hasattr(self.client, "create_completion"):
                response = await self.client.create_completion(
                    model=model, messages=[{"role": "user", "content": prompt}]
                )
                return response.choices[0].message.content
            else:
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: openai.ChatCompletion.create(
                        model=model, messages=[{"role": "user", "content": prompt}]
                    ),
                )
                return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Task execution failed with {model}: {e}")
            raise ValueError(f"Task execution failed. No forbidden models will be used. Error: {e}")

    def _validate_model_strict(self, model: str) -> None:
        """
        STRICT model validation. NO EXCEPTIONS.
        Validates against forbidden patterns and approved lists.
        """
        # Check forbidden patterns
        forbidden_patterns = [
            "gpt-4o",
            "gpt-3.5",
            "gpt-4-turbo",
            "claude",
            "gemini",
            "llama",
            "mistral",
        ]
        model_lower = model.lower()

        for pattern in forbidden_patterns:
            if pattern in model_lower:
                raise ValueError(
                    f"❌ FORBIDDEN MODEL DETECTED: {model}. This model is explicitly banned by 2025 standards."
                )

        # Ensure model is in approved list
        approved_models = ["o3", "o4-mini", "gpt-5", "gpt-5-mini", "gpt-5-nano"]
        if not any(approved in model for approved in approved_models):
            raise ValueError(f"❌ Model {model} is not in the approved 2025 list: {approved_models}")

        logger.info(f"✅ Model {model} passed STRICT validation")

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """
        Parse JSON response with flexible handling for different model formats.
        """
        try:
            # Try direct parsing
            return json.loads(response)
        except json.JSONDecodeError:
            # Try extracting JSON from markdown
            import re

            json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))

            # Try parsing nested structures
            try:
                # Some models return {"properties": {...}} or {"value": {...}}
                temp = json.loads(response)
                if "properties" in temp:
                    return temp["properties"]
                elif "value" in temp:
                    return temp["value"]
                return temp
            except:
                pass

            # Last resort: return structured default
            logger.warning(f"Could not parse JSON response: {response[:200]}...")
            return {
                "task_type": "general",
                "complexity": "moderate",
                "requirements": ["json_parse_failed"],
                "suggested_approach": "Manual review of response",
            }
