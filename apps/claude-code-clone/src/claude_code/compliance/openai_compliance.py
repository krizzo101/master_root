"""OpenAI API Standards 2025 Compliance Layer.

This module enforces strict compliance with OpenAI API Standards 2025,
providing deterministic model routing, schema enforcement, and proper
parameter handling for the Responses API.
"""

import logging
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ReasoningEffort(str, Enum):
    """Allowed reasoning effort levels for o4-mini."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ModelFamily(str, Enum):
    """Model families with different capabilities."""
    GENERAL = "general"
    REASONING = "o-series"


@dataclass
class ComplianceRequest:
    """Structured request for OpenAI API compliance."""
    prompt: str
    max_tokens: int
    schema: Optional[Dict[str, Any]] = None
    reasoning: Optional[ReasoningEffort] = None
    reuse_reasoning_from: Optional[str] = None
    unstructured_justification: Optional[str] = None
    tools: Optional[List[Dict[str, Any]]] = None
    extras: Optional[Dict[str, Any]] = None
    model_override: Optional[str] = None


@dataclass
class ComplianceResponse:
    """Response from the compliance layer."""
    endpoint: str
    request: Dict[str, Any]
    model: str
    family: ModelFamily
    proof_blob: Dict[str, Any]


class OpenAIComplianceError(Exception):
    """Error in OpenAI compliance validation."""
    pass


class OpenAIComplianceLayer:
    """Enforces OpenAI API Standards 2025 compliance."""
    
    # MANDATORY: Approved models only - NO EXCEPTIONS
    ALLOWED_GENERAL = ["gpt-5-nano", "gpt-5-mini", "gpt-5"]
    REASONING_MODEL = "o4-mini"
    
    # 🔐 CRITICAL: These are the ONLY approved models
    ALL_APPROVED_MODELS = ALLOWED_GENERAL + [REASONING_MODEL]
    
    def __init__(self):
        """Initialize compliance layer."""
        logger.info("🔐 OpenAI API Standards 2025 Compliance Layer initialized")
        self._validate_initialization()
    
    def _validate_initialization(self) -> None:
        """Validate compliance layer initialization."""
        # Ensure we have the mandatory approved models
        if not self.ALLOWED_GENERAL or not self.REASONING_MODEL:
            raise OpenAIComplianceError(
                "CRITICAL: Approved models not properly configured"
            )
        
        logger.info(f"✅ Approved general models: {self.ALLOWED_GENERAL}")
        logger.info(f"✅ Reasoning model: {self.REASONING_MODEL}")
    
    def _default_schema(self) -> Dict[str, Any]:
        """Default JSON schema for structured outputs."""
        return {
            "name": "text_payload",
            "strict": True,
            "schema": {
                "type": "object",
                "additionalProperties": False,
                "properties": {"text": {"type": "string"}},
                "required": ["text"]
            }
        }
    
    def _validate_model(self, model: str) -> None:
        """Validate that model is approved."""
        if model not in self.ALL_APPROVED_MODELS:
            raise OpenAIComplianceError(
                f"UNAUTHORIZED MODEL: {model}\n"
                f"APPROVED MODELS ONLY: {', '.join(self.ALL_APPROVED_MODELS)}\n"
                "🔐 NO OVERRIDES - NO EXCEPTIONS - NO COMPATIBILITY EXCUSES"
            )
    
    def _validate_reasoning_params(self, request: ComplianceRequest) -> None:
        """Validate reasoning parameters."""
        if request.reasoning and request.model_override:
            if request.model_override != self.REASONING_MODEL:
                raise OpenAIComplianceError(
                    f"Reasoning effort can only be used with {self.REASONING_MODEL}, "
                    f"got {request.model_override}"
                )
        
        if request.reuse_reasoning_from and not request.reasoning:
            raise OpenAIComplianceError(
                "reuse_reasoning_from can only be used with reasoning parameter"
            )
    
    def _validate_schema_bypass(self, request: ComplianceRequest) -> None:
        """Validate unstructured output bypass."""
        if not request.schema and not request.unstructured_justification:
            logger.info("No schema provided, using default structured output")
    
    def _determine_model_and_family(self, request: ComplianceRequest) -> tuple[str, ModelFamily]:
        """Determine model and family based on request."""
        if request.reasoning in {ReasoningEffort.LOW, ReasoningEffort.MEDIUM, ReasoningEffort.HIGH}:
            model = request.model_override or self.REASONING_MODEL
            family = ModelFamily.REASONING
        else:
            model = request.model_override or self.ALLOWED_GENERAL[0]  # Start with nano
            family = ModelFamily.GENERAL
        
        self._validate_model(model)
        return model, family
    
    def _build_request_payload(
        self, 
        request: ComplianceRequest, 
        model: str, 
        family: ModelFamily
    ) -> Dict[str, Any]:
        """Build the request payload for Responses API."""
        # Base payload - ALWAYS use Responses API
        payload = {
            "model": model,
            "input": request.prompt,
            "max_output_tokens": request.max_tokens  # CRITICAL: Responses API uses this
        }
        
        # Structured output (default ON unless justified bypass)
        if request.unstructured_justification:
            logger.warning(f"Bypassing structured output: {request.unstructured_justification}")
        else:
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": request.schema or self._default_schema()
            }
        
        # Reasoning options (only for o-series)
        if family == ModelFamily.REASONING:
            effort_map = {
                ReasoningEffort.LOW: "low",
                ReasoningEffort.MEDIUM: "medium", 
                ReasoningEffort.HIGH: "high"
            }
            payload["reasoning"] = {"effort": effort_map[request.reasoning]}
            
            if request.reuse_reasoning_from:
                payload["previous_response_id"] = request.reuse_reasoning_from
        
        # Tools (optional, Responses API supports it)
        if request.tools:
            payload["tools"] = [{"type": "function", "function": tool} for tool in request.tools]
            payload["tool_choice"] = "auto"
        
        # Extras passthrough (safe parameters only)
        if request.extras:
            safe_extras = {
                "temperature", "top_p", "stream", "user", "metadata"
            }
            filtered_extras = {
                k: v for k, v in request.extras.items() 
                if k in safe_extras
            }
            payload.update(filtered_extras)
        
        return payload
    
    def _generate_proof_blob(
        self, 
        request: ComplianceRequest, 
        model: str, 
        family: ModelFamily,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate compliance proof blob for audit trail."""
        schema_hash = None
        if "response_format" in payload:
            schema_str = str(payload["response_format"])
            schema_hash = hash(schema_str) % 1000000  # Simple hash for tracking
        
        return {
            "api": "responses",
            "model": model,
            "family": family.value,
            "structured": "response_format" in payload,
            "schema_hash": schema_hash,
            "reasoning_effort": request.reasoning.value if request.reasoning else None,
            "previous_response_id": request.reuse_reasoning_from,
            "compliance_version": "2025-09-07",
            "enforcement": "strict"
        }
    
    def build_compliant_request(self, request: ComplianceRequest) -> ComplianceResponse:
        """Build a compliant OpenAI API request."""
        logger.info(f"🔐 Processing compliance request for: {request.prompt[:50]}...")
        
        # Validate all parameters
        self._validate_reasoning_params(request)
        self._validate_schema_bypass(request)
        
        # Determine model and family
        model, family = self._determine_model_and_family(request)
        
        # Build request payload
        payload = self._build_request_payload(request, model, family)
        
        # Generate proof blob
        proof_blob = self._generate_proof_blob(request, model, family, payload)
        
        logger.info(f"✅ Compliance validated: {model} ({family.value})")
        logger.debug(f"Proof blob: {proof_blob}")
        
        return ComplianceResponse(
            endpoint="/v1/responses",
            request=payload,
            model=model,
            family=family,
            proof_blob=proof_blob
        )
    
    def validate_response(self, response: Any) -> Dict[str, Any]:
        """Validate response format and extract content."""
        if hasattr(response, 'output_text'):
            # New Responses API format
            return {
                "content": response.output_text,
                "format": "responses_api",
                "compliant": True
            }
        elif hasattr(response, 'choices') and response.choices:
            # Legacy format (should not happen with Responses API)
            logger.warning("Received legacy response format - ensure using Responses API")
            return {
                "content": response.choices[0].message.content,
                "format": "legacy",
                "compliant": False
            }
        else:
            raise OpenAIComplianceError(f"Unexpected response format: {type(response)}")


# Convenience functions for common patterns
def create_simple_request(
    prompt: str, 
    max_tokens: int = 1000,
    model: str = "gpt-5-nano"
) -> ComplianceRequest:
    """Create a simple compliant request."""
    return ComplianceRequest(
        prompt=prompt,
        max_tokens=max_tokens,
        model_override=model
    )


def create_reasoning_request(
    prompt: str,
    effort: ReasoningEffort = ReasoningEffort.MEDIUM,
    max_tokens: int = 2000,
    reuse_from: Optional[str] = None
) -> ComplianceRequest:
    """Create a reasoning request for o4-mini."""
    return ComplianceRequest(
        prompt=prompt,
        max_tokens=max_tokens,
        reasoning=effort,
        reuse_reasoning_from=reuse_from
    )


def create_structured_request(
    prompt: str,
    schema: Dict[str, Any],
    max_tokens: int = 1000,
    model: str = "gpt-5-mini"
) -> ComplianceRequest:
    """Create a structured output request."""
    return ComplianceRequest(
        prompt=prompt,
        max_tokens=max_tokens,
        schema=schema,
        model_override=model
    )
