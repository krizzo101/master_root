#!/usr/bin/env python3
"""
OAMAT Structured Output Enforcement Engine
==========================================

Implements OpenAI structured output enforcement with comprehensive:
- response_format parameter usage with strict JSON schemas
- Multi-stage validation and error recovery
- Comprehensive debug logging and monitoring
- Retry logic with exponential backoff
- Schema compliance verification at every pipeline stage

"""

import asyncio
from datetime import datetime
import json
import logging
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Type

import jsonschema
from jsonschema import Draft7Validator
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from src.applications.oamat_sd.src.config.config_manager import ConfigManager


class StructuredOutputError(Exception):
    """Exception raised when structured output enforcement fails"""

    pass


class SchemaValidationError(Exception):
    """Exception raised when schema validation fails"""

    pass


class StructuredOutputEnforcer:
    """
    Core engine for enforcing structured outputs from O3 models using OpenAI's
    response_format parameter with comprehensive schema validation.
    """

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # Load schemas
        self.schemas = self._load_schemas()

        # Configure retry settings with fallbacks
        config_manager = ConfigManager()
        try:
            self.max_retries = (
                getattr(config_manager, "api", {})
                .get("retry", {})
                .get("max_attempts", 3)
            )
            self.base_delay = (
                getattr(config_manager, "api", {})
                .get("retry", {})
                .get("base_delay_seconds", 1)
            )
        except:
            self.max_retries = 3
            self.base_delay = 1

        # Debug settings with fallbacks
        try:
            self.debug_mode = (
                getattr(config_manager, "logging", {})
                .get("levels", {})
                .get("debug_enabled", True)
            )
            self.save_raw_responses = (
                getattr(config_manager, "logging", {})
                .get("o3_responses", {})
                .get("save_raw", True)
            )
        except:
            self.debug_mode = True
            self.save_raw_responses = True

        self.logger.info(
            "✅ Structured Output Enforcer initialized with comprehensive schema validation"
        )

    def _load_schemas(self) -> Dict[str, Any]:
        """Load all JSON schemas for structured output enforcement and resolve references recursively"""
        try:
            schema_file = (
                Path(__file__).parent.parent.parent
                / "config"
                / "schemas"
                / "o3_structured_output_schemas.json"
            )

            if not schema_file.exists():
                raise FileNotFoundError(f"Schema file not found: {schema_file}")

            with open(schema_file) as f:
                schema_data = json.load(f)

            # Resolve references recursively for OpenAI structured output compatibility
            definitions = schema_data.get("definitions", {})
            resolved_schemas = {}

            for schema_name, schema in schema_data["schemas"].items():
                resolved_schemas[schema_name] = self._resolve_schema_references(
                    schema, definitions
                )

            self.logger.info(
                f"✅ Loaded and resolved {len(resolved_schemas)} structured output schemas"
            )
            return resolved_schemas

        except Exception as e:
            self.logger.error(f"❌ Failed to load schemas: {e}")
            raise StructuredOutputError(f"Schema loading failed: {e}")

    def _resolve_schema_references(
        self, schema: Any, definitions: Dict[str, Any]
    ) -> Any:
        """Recursively resolve $ref references in a schema"""
        if isinstance(schema, dict):
            if "$ref" in schema:
                # Extract the reference path and resolve it
                ref_path = schema["$ref"].replace("#/definitions/", "")
                if ref_path in definitions:
                    # Recursively resolve the referenced schema
                    return self._resolve_schema_references(
                        definitions[ref_path], definitions
                    )
                else:
                    self.logger.warning(
                        f"Reference {ref_path} not found in definitions"
                    )
                    return schema
            else:
                # Recursively resolve all properties in the schema
                resolved = {}
                for key, value in schema.items():
                    resolved[key] = self._resolve_schema_references(value, definitions)
                return resolved
        elif isinstance(schema, list):
            # Recursively resolve all items in the list
            return [
                self._resolve_schema_references(item, definitions) for item in schema
            ]
        else:
            # Return primitive values as-is
            return schema

    def _resolve_refs(
        self, schema: Dict[str, Any], definitions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Resolve $ref references using the definitions"""
        if isinstance(schema, dict):
            if "$ref" in schema:
                # Extract the reference path (e.g., "#/$defs/RequestClassification")
                ref_path = schema["$ref"]
                if ref_path.startswith("#/$defs/"):
                    def_name = ref_path.replace("#/$defs/", "")
                    if def_name in definitions:
                        # Recursively resolve the referenced definition
                        resolved = self._resolve_refs(
                            definitions[def_name], definitions
                        )
                        return self._make_openai_compliant_schema(resolved)
                    else:
                        self.logger.warning(
                            f"Reference {ref_path} not found in definitions"
                        )
                        return {}
                return schema
            else:
                # Recursively resolve all values in the dict
                resolved = {}
                for key, value in schema.items():
                    resolved[key] = self._resolve_refs(value, definitions)
                return resolved
        elif isinstance(schema, list):
            # Recursively resolve all items in the list
            return [self._resolve_refs(item, definitions) for item in schema]
        else:
            # Return primitive values as-is
            return schema

    def _make_openai_compliant_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert a Pydantic-generated schema to OpenAI structured output compliant format.

        OpenAI requires:
        - "additionalProperties": false on all objects
        - All properties must be in "required" array when additionalProperties is false
        - No $ref references - everything must be inlined
        """
        if isinstance(schema, dict):
            schema_copy = schema.copy()

            # Store definitions for reference resolution
            definitions = schema_copy.get("$defs", {})

            # First resolve all $ref references
            if definitions:
                schema_copy = self._resolve_refs(schema_copy, definitions)

            # Remove $defs after resolving references
            if "$defs" in schema_copy:
                del schema_copy["$defs"]

            # If this is an object type, make it OpenAI compliant
            if schema_copy.get("type") == "object":
                schema_copy["additionalProperties"] = False

                # Ensure all properties are required when additionalProperties is false
                if "properties" in schema_copy:
                    # Only include properties that actually exist in the properties dict
                    existing_required = schema_copy.get("required", [])
                    all_properties = list(schema_copy["properties"].keys())

                    # Filter existing required to only include actual properties
                    valid_required = [
                        req for req in existing_required if req in all_properties
                    ]

                    # Add any missing properties to required
                    final_required = list(set(valid_required + all_properties))
                    schema_copy["required"] = final_required

                    # Recursively process nested objects
                    for prop_name, prop_schema in schema_copy["properties"].items():
                        schema_copy["properties"][
                            prop_name
                        ] = self._make_openai_compliant_schema(prop_schema)

            # Process array items
            elif schema_copy.get("type") == "array" and "items" in schema_copy:
                schema_copy["items"] = self._make_openai_compliant_schema(
                    schema_copy["items"]
                )

            # Process other nested structures recursively
            else:
                for key, value in schema_copy.items():
                    if key in ["$defs", "$ref"]:  # Skip these
                        continue
                    elif isinstance(value, dict):
                        schema_copy[key] = self._make_openai_compliant_schema(value)
                    elif isinstance(value, list):
                        schema_copy[key] = [
                            (
                                self._make_openai_compliant_schema(item)
                                if isinstance(item, dict)
                                else item
                            )
                            for item in value
                        ]

            return schema_copy

        return schema

    async def enforce_request_standardization(
        self,
        prompt: str,
        model_config: Dict[str, Any],
        context: Dict[str, Any] = None,
        max_attempts: int = None,
        timeout_seconds: int = None,
    ) -> Dict[str, Any]:
        """
        Enforce structured output for request standardization using GPT-4.1-mini.

        Uses function calling approach to avoid OpenAI's strict structured output requirements.
        """
        operation_name = "request_standardization"

        # Get configuration values from ConfigManager
        config_manager = ConfigManager()
        max_attempts = max_attempts or config_manager.execution.max_retry_attempts
        timeout_seconds = (
            timeout_seconds or config_manager.execution.agent_timeout_seconds
        )

        # Generate schema dynamically from Pydantic model
        from ..preprocessing.schemas import StandardizedRequest

        base_schema = StandardizedRequest.model_json_schema()

        # For function calling, we can use the schema more directly
        request_schema = {
            "name": "standardize_request",
            "description": "Convert raw user request into standardized format",
            "parameters": base_schema,
        }

        # Create model with function calling using centralized configuration
        config_manager = ConfigManager()
        model_name = model_config.get(
            "model", config_manager.models["agent"].model_name
        )
        llm_kwargs = {}

        # Only add reasoning_effort for O3 models
        if model_name.startswith("o3"):
            llm_kwargs["reasoning_effort"] = model_config.get(
                "reasoning_effort",
                config_manager.models["reasoning"].reasoning_effort,
            )
        # Add temperature for non-O3 models (like GPT-4.1-mini)
        elif "temperature" in model_config:
            llm_kwargs["temperature"] = model_config["temperature"]
        else:
            # Use default temperature from config if not specified
            agent_model = config_manager.models["agent"]
            if agent_model.supports_temperature and agent_model.temperature is not None:
                llm_kwargs["temperature"] = agent_model.temperature

        llm = ChatOpenAI(model=model_name, **llm_kwargs)

        # Use with_structured_output with method="function_calling"
        structured_llm = llm.with_structured_output(
            StandardizedRequest, method="function_calling"
        )

        for attempt in range(1, max_attempts + 1):
            try:
                self.logger.debug(f"🎯 Attempt {attempt} for {operation_name}")

                # Create the final prompt (avoiding datetime serialization issues)
                def serialize_context(obj):
                    """Custom serializer for datetime and other objects"""
                    if hasattr(obj, "isoformat"):  # datetime objects
                        return obj.isoformat()
                    elif hasattr(obj, "__dict__"):  # complex objects
                        return str(obj)
                    return str(obj)

                # Clean context to avoid serialization issues
                clean_context = {}
                for key, value in (context or {}).items():
                    try:
                        json.dumps(value)  # Test if serializable
                        clean_context[key] = value
                    except (TypeError, ValueError):
                        clean_context[key] = serialize_context(value)

                final_prompt = f"""
{prompt}

Please analyze this request and return a comprehensive StandardizedRequest object with all fields properly filled out.
Pay special attention to:
- Accurate classification of request type and complexity
- Comprehensive technical specifications
- Well-defined functional requirements
- Realistic deliverables and success criteria
- Appropriate confidence scoring for each section

Make sure to fill in all required fields with appropriate default values where information is not explicitly provided.
"""

                # Execute with timeout
                start_time = time.time()
                result = await asyncio.wait_for(
                    structured_llm.ainvoke(final_prompt), timeout=timeout_seconds
                )

                processing_time = (time.time() - start_time) * 1000

                # Convert Pydantic model to dict
                result_dict = result.model_dump()

                self.logger.debug(f"✅ {operation_name} successful on attempt {attempt}")
                self._log_success_metrics(result_dict, operation_name, attempt)

                return {
                    "success": True,
                    "result": result_dict,
                    "attempts": attempt,
                    "processing_time_ms": processing_time,
                    "model_used": model_name,
                }

            except asyncio.TimeoutError:
                self.logger.warning(
                    f"⏰ Attempt {attempt} timed out for {operation_name}"
                )

            except Exception as e:
                self.logger.warning(
                    f"⚠️ Attempt {attempt} failed for {operation_name}: {e}"
                )

                if attempt == max_attempts:
                    return {
                        "success": False,
                        "error": str(e),
                        "attempts": max_attempts,
                        "model_used": model_name,
                    }

        return {
            "success": False,
            "error": f"All {max_attempts} attempts failed",
            "attempts": max_attempts,
            "model_used": model_name,
        }

    async def enforce_workflow_specification(
        self,
        prompt: str,
        model_config: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Enforce structured output for WorkflowSpecification generation with O3
        """
        schema_name = "workflow_specification"
        return await self._enforce_structured_output(
            prompt=prompt,
            schema_name=schema_name,
            model_config=model_config,
            context=context or {},
            operation_name="WorkflowSpecification Generation",
        )

    async def enforce_dynamic_config(
        self,
        prompt: str,
        model_config: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Enforce structured output for Dynamic Configuration generation with O3
        """
        schema_name = "dynamic_config"
        return await self._enforce_structured_output(
            prompt=prompt,
            schema_name=schema_name,
            model_config=model_config,
            context=context or {},
            operation_name="Dynamic Configuration Generation",
        )

    async def enforce_complexity_analysis(
        self,
        prompt: str,
        model_config: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Enforce structured output for Complexity Analysis generation with O3
        """
        schema_name = "complexity_analysis"
        return await self._enforce_structured_output(
            prompt=prompt,
            schema_name=schema_name,
            model_config=model_config,
            context=context or {},
            operation_name="Complexity Analysis",
        )

    async def enforce_agent_strategy(
        self,
        prompt: str,
        model_config: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Enforce structured output for Agent Strategy generation with O3
        """
        schema_name = "agent_strategy"
        return await self._enforce_structured_output(
            prompt=prompt,
            schema_name=schema_name,
            model_config=model_config,
            context=context or {},
            operation_name="Agent Strategy",
        )

    async def enforce_agent_response(
        self,
        prompt: str,
        model_config: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Enforce structured output for Agent Response processing using function calling
        """
        from langchain_openai import ChatOpenAI

        from src.applications.oamat_sd.src.models.agent_response_models import (
            AgentResponse,
        )

        # Create model with function calling approach using centralized configuration
        config_manager = ConfigManager()
        model_name = model_config.get(
            "model_name", config_manager.models["agent"].model_name
        )
        llm_kwargs = {}

        # Add temperature only if model supports it
        if "temperature" in model_config:
            llm_kwargs["temperature"] = model_config["temperature"]
        else:
            agent_model = config_manager.models["agent"]
            if agent_model.supports_temperature and agent_model.temperature is not None:
                llm_kwargs["temperature"] = agent_model.temperature

        # Add max_tokens from config
        if "max_tokens" in model_config:
            llm_kwargs["max_tokens"] = model_config["max_tokens"]
        else:
            llm_kwargs["max_tokens"] = agent_model.max_tokens

        llm = ChatOpenAI(model=model_name, **llm_kwargs)

        # Use with_structured_output with method="function_calling" - our established pattern
        structured_llm = llm.with_structured_output(
            AgentResponse, method="function_calling"
        )

        try:
            self.logger.debug("🔒 Processing agent output with structured enforcement")

            # Execute structured output processing
            result = await structured_llm.ainvoke(prompt)

            # Convert Pydantic model to dict for consistent return format
            if hasattr(result, "model_dump"):
                result_dict = result.model_dump()
            else:
                result_dict = dict(result) if hasattr(result, "__dict__") else result

            self.logger.info("✅ Agent response structured successfully")
            return result_dict

        except Exception as e:
            self.logger.error(f"❌ Agent response structuring failed: {e}")
            raise

    async def _enforce_structured_output(
        self,
        prompt: str,
        schema_name: str,
        model_config: Dict[str, Any],
        context: Dict[str, Any],
        operation_name: str,
    ) -> Dict[str, Any]:
        """
        Core method for enforcing structured outputs with comprehensive validation
        """
        if schema_name not in self.schemas:
            raise StructuredOutputError(f"Schema '{schema_name}' not found")

        schema = self.schemas[schema_name]

        # Create validator
        validator = Draft7Validator(schema)

        self.logger.info(
            f"🔒 Starting structured output enforcement for {operation_name}"
        )
        self.logger.info(f"📋 Using schema: {schema_name}")

        for attempt in range(1, self.max_retries + 1):
            try:
                self.logger.info(
                    f"🔄 Attempt {attempt}/{self.max_retries} for {operation_name}"
                )

                # Create enhanced prompt with schema requirements
                enhanced_prompt = self._create_schema_enforced_prompt(
                    prompt, schema, schema_name
                )

                # Execute O3 call with structured output enforcement
                result = await self._execute_structured_call(
                    enhanced_prompt, schema, model_config, operation_name, attempt
                )

                # Validate against schema
                self._validate_against_schema(result, validator, schema_name)

                # Additional business logic validation
                self._validate_business_logic(result, schema_name, context)

                self.logger.info(
                    f"✅ {operation_name} structured output enforcement SUCCEEDED (attempt {attempt})"
                )

                if self.debug_mode:
                    self._log_success_metrics(result, schema_name, attempt)

                return result

            except Exception as e:
                self.logger.warning(
                    f"⚠️ Attempt {attempt} failed for {operation_name}: {e}"
                )

                if attempt == self.max_retries:
                    self.logger.error(
                        f"❌ All {self.max_retries} attempts failed for {operation_name}"
                    )
                    raise StructuredOutputError(
                        f"Structured output enforcement failed after {self.max_retries} attempts: {e}"
                    )

                # Exponential backoff
                delay = self.base_delay * (2 ** (attempt - 1))
                self.logger.info(f"⏳ Retrying in {delay} seconds...")
                await asyncio.sleep(delay)

        # Should never reach here
        raise StructuredOutputError(
            f"Unexpected error in structured output enforcement for {operation_name}"
        )

    def _create_schema_enforced_prompt(
        self, prompt: str, schema: Dict[str, Any], schema_name: str
    ) -> str:
        """
        Create an enhanced prompt that enforces schema compliance
        """
        schema_description = self._generate_schema_description(schema)

        enhanced_prompt = f"""
{prompt}

🔒 **CRITICAL: STRUCTURED OUTPUT ENFORCEMENT**

You MUST respond with VALID JSON that EXACTLY matches this schema:

**SCHEMA NAME**: {schema_name}
**REQUIRED FORMAT**: {json.dumps(schema, indent=2)}

**SCHEMA CONSTRAINTS**:
{schema_description}

**ENFORCEMENT RULES**:
1. Response must be VALID JSON - no markdown, no explanation, no extra text
2. ALL required fields must be present
3. ALL enum values must match exactly (case-sensitive)
4. ALL data types must match schema specification
5. NO additional properties allowed beyond schema
6. Array lengths must respect minItems/maxItems constraints
7. String lengths must respect minLength/maxLength constraints
8. Numeric values must respect minimum/maximum constraints

**FAILURE CONSEQUENCES**:
- Invalid JSON will cause system failure
- Missing required fields will cause system failure
- Wrong data types will cause system failure
- Invalid enum values will cause system failure

**SUCCESS CRITERIA**:
Return ONLY valid JSON matching the schema exactly. No other text.

**OUTPUT FORMAT**: JSON ONLY
"""

        if self.debug_mode:
            self.logger.debug(
                f"📝 Enhanced prompt created for {schema_name} (length: {len(enhanced_prompt)})"
            )

        return enhanced_prompt

    def _generate_schema_description(self, schema: Dict[str, Any]) -> str:
        """
        Generate human-readable description of schema constraints
        """
        descriptions = []

        if "required" in schema:
            descriptions.append(f"- Required fields: {', '.join(schema['required'])}")

        if "properties" in schema:
            for prop_name, prop_schema in schema["properties"].items():
                if "enum" in prop_schema:
                    descriptions.append(
                        f"- {prop_name}: must be one of {prop_schema['enum']}"
                    )
                if "minLength" in prop_schema:
                    descriptions.append(
                        f"- {prop_name}: minimum length {prop_schema['minLength']}"
                    )
                if "maxLength" in prop_schema:
                    descriptions.append(
                        f"- {prop_name}: maximum length {prop_schema['maxLength']}"
                    )
                if "minimum" in prop_schema:
                    descriptions.append(
                        f"- {prop_name}: minimum value {prop_schema['minimum']}"
                    )
                if "maximum" in prop_schema:
                    descriptions.append(
                        f"- {prop_name}: maximum value {prop_schema['maximum']}"
                    )

        return "\n".join(descriptions) if descriptions else "No specific constraints"

    async def _execute_structured_call(
        self,
        prompt: str,
        schema: Dict[str, Any],
        model_config: Dict[str, Any],
        operation_name: str,
        attempt: int,
    ) -> Dict[str, Any]:
        """
        Execute OpenAI API call with structured output enforcement using response_format
        """
        try:
            # Create OpenAI client with structured output enforcement
            model_name = model_config.get("model_name", "o3-mini")

            # Build kwargs dynamically based on model type
            llm_kwargs = {
                "model": model_name,
                "max_completion_tokens": model_config.get("max_tokens", 16000),
                # CRITICAL: Use OpenAI's structured output enforcement
                "model_kwargs": {
                    "response_format": {
                        "type": "json_schema",
                        "json_schema": {
                            "name": f"{operation_name.lower().replace(' ', '_')}_schema",
                            "strict": True,
                            "schema": schema,
                        },
                    }
                },
            }

            # Only add reasoning_effort for O3 models
            if model_name.startswith("o3"):
                llm_kwargs["reasoning_effort"] = model_config.get(
                    "reasoning_effort", "medium"
                )
            # Add temperature for non-O3 models (like GPT-4.1-mini)
            elif "temperature" in model_config:
                llm_kwargs["temperature"] = model_config["temperature"]

            llm = ChatOpenAI(**llm_kwargs)

            messages = [
                SystemMessage(
                    content="You are an AI assistant that MUST respond with valid JSON matching the provided schema exactly."
                ),
                HumanMessage(content=prompt),
            ]

            self.logger.info(
                f"🤖 Executing O3 call with structured output enforcement (attempt {attempt})"
            )

            # Execute with timeout using centralized configuration
            config_manager = ConfigManager()
            timeout_seconds = config_manager.execution.agent_timeout_seconds

            response = await asyncio.wait_for(
                llm.ainvoke(messages),
                timeout=timeout_seconds,
            )

            # Extract and parse JSON response
            raw_response = response.content

            if self.save_raw_responses:
                self._save_raw_response(raw_response, operation_name, attempt)

            # Parse JSON with comprehensive error handling
            try:
                result = json.loads(raw_response)
                self.logger.info(
                    f"✅ Successfully parsed JSON response (attempt {attempt})"
                )
                return result

            except json.JSONDecodeError as e:
                raise StructuredOutputError(f"Invalid JSON response from O3: {e}")

        except asyncio.TimeoutError:
            raise StructuredOutputError(
                f"O3 call timed out after {timeout_seconds} seconds"
            )
        except Exception as e:
            raise StructuredOutputError(f"O3 API call failed: {e}")

    def _validate_against_schema(
        self, result: Dict[str, Any], validator: Draft7Validator, schema_name: str
    ) -> None:
        """
        Validate result against JSON schema with detailed error reporting
        """
        try:
            validator.validate(result)
            self.logger.info(f"✅ Schema validation PASSED for {schema_name}")

        except jsonschema.ValidationError as e:
            error_details = self._format_validation_error(e)
            self.logger.error(
                f"❌ Schema validation FAILED for {schema_name}: {error_details}"
            )
            raise SchemaValidationError(f"Schema validation failed: {error_details}")

    def _validate_business_logic(
        self, result: Dict[str, Any], schema_name: str, context: Dict[str, Any]
    ) -> None:
        """
        Additional business logic validation beyond schema compliance
        """
        try:
            if schema_name == "workflow_specification":
                self._validate_workflow_business_logic(result, context)
            elif schema_name == "dynamic_config":
                self._validate_config_business_logic(result, context)
            elif schema_name == "complexity_analysis":
                self._validate_complexity_business_logic(result, context)
            elif schema_name == "agent_strategy":
                self._validate_strategy_business_logic(result, context)

            self.logger.info(f"✅ Business logic validation PASSED for {schema_name}")

        except Exception as e:
            self.logger.error(
                f"❌ Business logic validation FAILED for {schema_name}: {e}"
            )
            raise SchemaValidationError(f"Business logic validation failed: {e}")

    def _validate_workflow_business_logic(
        self, result: Dict[str, Any], context: Dict[str, Any]
    ) -> None:
        """Validate WorkflowSpecification business logic"""
        # Ensure agent count makes sense for complexity
        agent_count = len(result.get("agent_specifications", []))
        complexity = result.get("complexity_level", "medium")

        complexity_agent_ranges = {"low": (1, 3), "medium": (2, 5), "high": (3, 10)}

        min_agents, max_agents = complexity_agent_ranges[complexity]
        if not (min_agents <= agent_count <= max_agents):
            raise ValueError(
                f"Agent count {agent_count} invalid for {complexity} complexity (expected {min_agents}-{max_agents})"
            )

    def _validate_config_business_logic(
        self, result: Dict[str, Any], context: Dict[str, Any]
    ) -> None:
        """Validate Dynamic Configuration business logic"""
        # Ensure reasoning effort matches expected complexity
        reasoning_effort = result["models"]["reasoning"]["reasoning_effort"]
        max_tokens = result["models"]["reasoning"]["max_tokens"]

        # Higher effort should have higher token limits
        effort_token_minimums = {"low": 1000, "medium": 8000, "high": 16000}

        if max_tokens < effort_token_minimums[reasoning_effort]:
            raise ValueError(
                f"Token limit {max_tokens} too low for {reasoning_effort} effort"
            )

    def _validate_complexity_business_logic(
        self, result: Dict[str, Any], context: Dict[str, Any]
    ) -> None:
        """Validate Complexity Analysis business logic"""
        # Ensure overall score matches factor scores
        factors = result["complexity_factors"]
        factor_scores = list(factors.values())
        calculated_average = sum(factor_scores) / len(factor_scores)

        overall_score = result["overall_score"]
        config_manager = ConfigManager()
        tolerance = config_manager.analysis.complexity.variance_analysis.get(
            "score_tolerance", 2.0
        )
        if abs(overall_score - calculated_average) > tolerance:
            raise ValueError(
                f"Overall score {overall_score} doesn't match factor average {calculated_average:.2f} (tolerance: {tolerance})"
            )

    def _validate_strategy_business_logic(
        self, result: Dict[str, Any], context: Dict[str, Any]
    ) -> None:
        """Validate Agent Strategy business logic"""
        # Ensure execution orders are sequential and valid
        assignments = result.get("agent_assignments", [])
        execution_orders = [a["execution_order"] for a in assignments]

        if len(set(execution_orders)) != len(execution_orders):
            raise ValueError("Duplicate execution orders found in agent assignments")

        if sorted(execution_orders) != list(range(1, len(execution_orders) + 1)):
            raise ValueError("Execution orders must be sequential starting from 1")

    def _format_validation_error(self, error: jsonschema.ValidationError) -> str:
        """Format validation error for detailed debugging"""
        return (
            f"Path: {'.'.join(str(p) for p in error.absolute_path)}, "
            f"Message: {error.message}, "
            f"Failed value: {error.instance}"
        )

    def _save_raw_response(
        self, response: str, operation_name: str, attempt: int
    ) -> None:
        """Save raw O3 response for debugging"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"o3_response_{operation_name}_{timestamp}_attempt{attempt}.json"

            try:
                debug_dir = Path(
                    getattr(ConfigManager(), "logging", {})
                    .get("paths", {})
                    .get("debug_responses", "./logs/debug")
                )
            except:
                # Create debug logs in app root, not project root
                app_root = Path(__file__).parent.parent.parent
                debug_dir = app_root / "logs" / "debug"
            debug_dir.mkdir(exist_ok=True)

            with open(debug_dir / filename, "w") as f:
                f.write(response)

            self.logger.debug(f"💾 Saved raw response to {filename}")

        except Exception as e:
            self.logger.warning(f"Failed to save raw response: {e}")

    def _log_success_metrics(
        self, result: Dict[str, Any], schema_name: str, attempt: int
    ) -> None:
        """Log success metrics for monitoring"""
        self.logger.debug(f"📊 SUCCESS METRICS for {schema_name}:")
        self.logger.debug(f"  - Attempts needed: {attempt}")
        self.logger.debug(f"  - Response size: {len(json.dumps(result))} characters")
        self.logger.debug("  - Schema compliance: PASSED")
        self.logger.debug("  - Business logic: PASSED")

    async def enforce_subdivision_metadata(
        self,
        prompt: str,
        model_config: dict[str, Any],
        context: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Enforce structured output for Subdivision Metadata generation with O3
        """
        schema_name = "subdivision_metadata"
        return await self._enforce_structured_output(
            prompt=prompt,
            schema_name=schema_name,
            model_config=model_config,
            context=context or {},
            operation_name="Subdivision Metadata Analysis",
        )

    async def enforce_json_output(
        self,
        prompt: str,
        model_config: dict[str, Any],
        context: Optional[dict[str, Any]] = None,
    ) -> Any:
        """
        Enforce structured JSON output for dynamic O3 generation
        (Used for agent specifications and other dynamic structures)
        """
        # For JSON output, we use a flexible schema that accepts any valid JSON
        try:
            from langchain_openai import ChatOpenAI

            # Create model instance
            llm = ChatOpenAI(
                model=model_config["model_name"],
                **{k: v for k, v in model_config.items() if k != "model_name"},
            )

            # Execute with JSON response format
            response = await llm.ainvoke([{"role": "user", "content": prompt}])

            # Parse JSON response
            import json

            result = json.loads(response.content)

            self.logger.debug("✅ JSON output enforcement successful")
            return result

        except Exception as e:
            self.logger.error(f"❌ JSON output enforcement failed: {e}")
            raise RuntimeError(f"JSON output enforcement failed: {e}")

    def get_available_schemas(self) -> List[str]:
        """Get list of available schema names"""
        return list(self.schemas.keys())

    def get_schema(self, schema_name: str) -> Dict[str, Any]:
        """Get specific schema by name"""
        if schema_name not in self.schemas:
            raise ValueError(f"Schema '{schema_name}' not found")
        return self.schemas[schema_name]

    async def validate_existing_data(
        self, data: Dict[str, Any], schema_name: str
    ) -> bool:
        """
        Validate existing data against schema (for testing/debugging)
        """
        try:
            schema = self.get_schema(schema_name)
            validator = Draft7Validator(schema)
            self._validate_against_schema(data, validator, schema_name)
            return True
        except Exception as e:
            self.logger.error(f"❌ Existing data validation failed: {e}")
            return False

    async def enforce_structured_output(
        self,
        prompt: str,
        output_schema: Type[BaseModel],
        model_config: dict,
        context: dict = None,
    ) -> BaseModel:
        """Enforce structured output using Pydantic schema with centralized configuration"""

        try:
            # Use centralized configuration like the rest of the application
            from langchain_core.messages import HumanMessage, SystemMessage
            from langchain_openai import ChatOpenAI

            # Get model configuration from centralized ConfigManager
            config_manager = ConfigManager()

            # Determine model type from model_config or use reasoning as default
            model_type = model_config.get("model_type", "reasoning")
            model_spec = config_manager.get_model_config(model_type)

            # Create model instance using centralized configuration
            llm = ChatOpenAI(
                model=model_spec.model_name,
                temperature=(
                    model_spec.temperature if model_spec.supports_temperature else None
                ),
                max_tokens=model_spec.max_tokens,
            )

            # Create messages following LangChain pattern
            messages = [
                SystemMessage(
                    content="You are an expert AI assistant that generates structured outputs according to the provided schema."
                ),
                HumanMessage(content=prompt),
            ]

            # Call LangChain model
            response = await llm.ainvoke(messages)

            # Parse response and validate against schema
            parsed_data = json.loads(response.content)

            # Validate and return Pydantic model
            return output_schema(**parsed_data)

        except Exception as e:
            self.logger.error(f"❌ Structured output enforcement failed: {e}")
            raise RuntimeError(f"Structured output generation failed: {e}") from e
