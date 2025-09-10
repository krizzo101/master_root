"""Universal OpenAI API Standards 2025 Compliance for All Project Components.

This module enforces OpenAI API Standards 2025 compliance universally across:
- All agents and tools
- All MCP servers
- All direct OpenAI integrations
- All user interactions (including Claude)

CRITICAL: This compliance layer is MANDATORY for ALL OpenAI interactions.
"""

import logging
import os
import json
from typing import Dict, Any, Optional, List, Union, Callable
from functools import wraps
from dataclasses import dataclass, asdict
from enum import Enum
import threading

logger = logging.getLogger(__name__)


class ComplianceViolation(Exception):
    """Critical compliance violation that cannot be ignored."""

    pass


class UniversalOpenAICompliance:
    """Universal OpenAI API Standards 2025 enforcement system."""

    # 🔐 CRITICAL: These are the ONLY approved models - NO EXCEPTIONS
    APPROVED_MODELS = {
        "general": ["gpt-5-nano", "gpt-5-mini", "gpt-5"],
        "reasoning": ["o4-mini"],
        "legacy_blocked": ["gpt-4", "gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"],
    }

    # Global singleton instance
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Ensure singleton pattern for universal enforcement."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize universal compliance system."""
        if hasattr(self, "_initialized"):
            return

        self._initialized = True
        self._compliance_log = []
        self._violation_count = 0
        self._enforcement_active = True

        # Log initialization
        logger.critical("🔐 UNIVERSAL OpenAI API Standards 2025 Compliance ACTIVE")
        logger.critical(
            f"✅ Approved general models: {self.APPROVED_MODELS['general']}"
        )
        logger.critical(
            f"✅ Approved reasoning models: {self.APPROVED_MODELS['reasoning']}"
        )
        logger.critical(
            f"❌ BLOCKED legacy models: {self.APPROVED_MODELS['legacy_blocked']}"
        )

        # Set environment enforcement
        self._enforce_environment_compliance()

    def _enforce_environment_compliance(self):
        """Enforce compliance in environment variables."""
        # Check if legacy model is set in environment
        openai_model = os.getenv("OPENAI_MODEL", "")
        if openai_model in self.APPROVED_MODELS["legacy_blocked"]:
            logger.error(
                f"🚨 COMPLIANCE VIOLATION: Environment variable OPENAI_MODEL={openai_model}"
            )
            logger.error("🔐 CORRECTING: Setting OPENAI_MODEL to gpt-5-mini")
            os.environ["OPENAI_MODEL"] = "gpt-5-mini"

    def validate_model(self, model: str, context: str = "unknown") -> str:
        """Validate model against approved list.

        Args:
            model: Model to validate
            context: Context for logging (e.g., "thinking-tool", "agent-X")

        Returns:
            Validated model name

        Raises:
            ComplianceViolation: If model is not approved
        """
        all_approved = (
            self.APPROVED_MODELS["general"] + self.APPROVED_MODELS["reasoning"]
        )

        if model not in all_approved:
            violation_msg = (
                f"🚨 UNIVERSAL COMPLIANCE VIOLATION in {context}\n"
                f"❌ UNAUTHORIZED MODEL: {model}\n"
                f"✅ APPROVED MODELS: {', '.join(all_approved)}\n"
                f"🔐 NO OVERRIDES - NO EXCEPTIONS - NO COMPATIBILITY EXCUSES"
            )

            self._violation_count += 1
            logger.critical(violation_msg)

            # Log to compliance audit trail
            violation_record = {
                "timestamp": str(pd.Timestamp.now()),
                "context": context,
                "violation_type": "unauthorized_model",
                "attempted_model": model,
                "violation_count": self._violation_count,
            }
            self._compliance_log.append(violation_record)

            if self._enforcement_active:
                raise ComplianceViolation(violation_msg)

        # Log successful validation
        logger.info(f"✅ Model validation passed: {model} in {context}")
        return model

    def get_compliance_approved_model(
        self,
        requested_model: Optional[str] = None,
        use_reasoning: bool = False,
        context: str = "unknown",
    ) -> str:
        """Get a compliance-approved model with automatic fallback.

        Args:
            requested_model: The requested model (will be validated)
            use_reasoning: Whether reasoning is needed (routes to o4-mini)
            context: Context for logging

        Returns:
            Approved model name
        """
        if use_reasoning:
            approved_model = self.APPROVED_MODELS["reasoning"][0]  # o4-mini
            logger.info(f"🧠 Reasoning requested in {context}: using {approved_model}")
            return approved_model

        if requested_model:
            # Validate the requested model
            return self.validate_model(requested_model, context)

        # Default to nano for efficiency
        default_model = self.APPROVED_MODELS["general"][0]  # gpt-5-nano
        logger.info(f"🔧 Default model selection in {context}: {default_model}")
        return default_model

    def enforce_responses_api(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enforce Responses API usage instead of Chat Completions.

        Args:
            request_data: Original request data

        Returns:
            Corrected request data for Responses API
        """
        corrected = request_data.copy()

        # Convert max_tokens to max_output_tokens for Responses API
        if "max_tokens" in corrected:
            corrected["max_output_tokens"] = corrected.pop("max_tokens")
            logger.info("🔄 Converted max_tokens → max_output_tokens for Responses API")

        # Convert messages to input for Responses API
        if "messages" in corrected:
            # Simple conversion: join messages into input
            messages = corrected.pop("messages")
            if isinstance(messages, list) and messages:
                input_text = "\n".join(
                    [
                        f"{msg.get('role', 'user')}: {msg.get('content', '')}"
                        for msg in messages
                    ]
                )
                corrected["input"] = input_text
                logger.info("🔄 Converted messages → input for Responses API")

        # Ensure structured output by default
        if "response_format" not in corrected:
            corrected["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "default_response",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {"text": {"type": "string"}},
                        "required": ["text"],
                    },
                },
            }
            logger.info("🔧 Added default structured output for Responses API")

        return corrected

    def log_compliance_event(
        self, event_type: str, context: str, details: Dict[str, Any]
    ):
        """Log compliance event for audit trail."""
        event = {
            "timestamp": str(pd.Timestamp.now()),
            "event_type": event_type,
            "context": context,
            "details": details,
        }
        self._compliance_log.append(event)
        logger.debug(f"📝 Compliance event logged: {event_type} in {context}")

    def get_compliance_report(self) -> Dict[str, Any]:
        """Get compliance audit report."""
        return {
            "enforcement_active": self._enforcement_active,
            "violation_count": self._violation_count,
            "approved_models": self.APPROVED_MODELS,
            "events": self._compliance_log[-50:],  # Last 50 events
            "environment_check": {
                "OPENAI_MODEL": os.getenv("OPENAI_MODEL"),
                "OPENAI_API_KEY_SET": bool(os.getenv("OPENAI_API_KEY")),
            },
        }


# Global singleton instance
UNIVERSAL_COMPLIANCE = UniversalOpenAICompliance()


def openai_compliance_required(context: str = None):
    """Decorator to enforce OpenAI compliance on functions/methods.

    Args:
        context: Context description for compliance logging
    """

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract model from kwargs if present
            model = kwargs.get("model")
            if model:
                validated_model = UNIVERSAL_COMPLIANCE.validate_model(
                    model, context or func.__name__
                )
                kwargs["model"] = validated_model

            # Log compliance check
            UNIVERSAL_COMPLIANCE.log_compliance_event(
                "function_call",
                context or func.__name__,
                {"args_count": len(args), "kwargs_keys": list(kwargs.keys())},
            )

            return func(*args, **kwargs)

        return wrapper

    return decorator


def ensure_openai_compliance(
    model: Optional[str] = None, context: str = "unknown", use_reasoning: bool = False
) -> str:
    """Convenience function to ensure OpenAI compliance.

    Args:
        model: Requested model
        context: Context for logging
        use_reasoning: Whether reasoning is needed

    Returns:
        Compliance-approved model
    """
    return UNIVERSAL_COMPLIANCE.get_compliance_approved_model(
        requested_model=model, use_reasoning=use_reasoning, context=context
    )


def patch_openai_environment():
    """Patch environment variables for compliance."""
    UNIVERSAL_COMPLIANCE._enforce_environment_compliance()


def get_universal_compliance_status() -> Dict[str, Any]:
    """Get current universal compliance status."""
    return UNIVERSAL_COMPLIANCE.get_compliance_report()


# Auto-patch environment on import
try:
    import pandas as pd
except ImportError:
    # Fallback for timestamp if pandas not available
    from datetime import datetime

    class pd:
        @staticmethod
        def Timestamp():
            class TS:
                @staticmethod
                def now():
                    return datetime.now().isoformat()

            return TS()


# Apply environment patches immediately
patch_openai_environment()

logger.info("🔐 Universal OpenAI API Standards 2025 Compliance System Loaded")
