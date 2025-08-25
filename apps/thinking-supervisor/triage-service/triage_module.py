#!/usr/bin/env python3
"""
Lightweight triage module for direct integration with thinking tool.
Optimized for speed - makes only ONE nano API call.
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

# CRITICAL: Set environment variables from .mcp.json BEFORE any imports
# These are required for knowledge system to work when imported directly
os.environ.setdefault("NEO4J_URI", "bolt://localhost:7687")
os.environ.setdefault("NEO4J_USER", "neo4j")
os.environ.setdefault("NEO4J_PASSWORD", "password")
os.environ.setdefault("EMBEDDING_SERVICE_URL", "http://localhost:8000")

# Add libs to path
sys.path.insert(0, "/home/opsvi/master_root/libs")
sys.path.insert(0, "/home/opsvi/master_root/apps")

from opsvi_llm.providers.openai_provider import OpenAIConfig
from opsvi_llm.providers.openai_unified_interface import OpenAIUnifiedInterface
from pydantic import BaseModel, Field

# Import knowledge tools for direct access (fast path for internal agents)
try:
    from apps.knowledge_system.mcp_knowledge_tools import (
        get_enhanced_query,
        get_smart_executor,
    )

    KNOWLEDGE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Knowledge system not available: {e}", file=sys.stderr)
    KNOWLEDGE_AVAILABLE = False


class TriageAnalysisSchema(BaseModel):
    """Schema for triage analysis output"""

    model_config = {
        "extra": "forbid",
        "json_schema_extra": {
            "required": [
                "violations",
                "patterns",
                "coaching_questions",
                "needs_escalation",
                "escalation_reason",
                "reminders",
                "confidence",
                "analysis",
            ]
        },
    }

    violations: List[str] = Field(
        description="List of violations detected (reflexive agreement, overconfidence, etc.)"
    )
    patterns: List[str] = Field(
        description="Multi-thought patterns observed (repetition, frustration, etc.)"
    )
    coaching_questions: List[str] = Field(
        description="Helpful leading questions to unstick the assistant"
    )
    needs_escalation: bool = Field(
        description="Whether to escalate to consult suite for deeper analysis"
    )
    escalation_reason: Optional[str] = Field(
        description="Why escalation would help", default=None
    )
    reminders: List[str] = Field(
        description="Instructions/rules to remind the assistant about"
    )
    confidence: float = Field(
        description="Confidence in analysis (0.0 to 1.0)", ge=0.0, le=1.0
    )
    analysis: str = Field(description="Brief explanation of the analysis")


class TriageAnalyzer:
    """Fast triage analyzer - ONE nano call only"""

    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set")

        config = OpenAIConfig(
            api_key=api_key,
            provider_name="openai",
            default_model="gpt-5-nano",
            enable_audit_logging=False,  # Disable for speed
            enable_sanitization=False,  # Disable for speed
        )
        self.interface = OpenAIUnifiedInterface(config)

        # Initialize knowledge tools if available
        if KNOWLEDGE_AVAILABLE:
            self.query_tool = get_enhanced_query()
            self.smart_query = get_smart_executor()
        else:
            self.query_tool = None
            self.smart_query = None

    async def load_instructions_from_kb(self) -> str:
        """Load relevant instructions from KB"""
        if not self.query_tool:
            return "No instructions available (KB not connected)"

        instructions = []

        try:
            # Query for global operational instructions
            result = await self.query_tool.execute_query(
                query_type="search",
                search_text="GLOBAL OPERATIONAL INSTRUCTIONS",
                limit=3,
            )
            for item in result.get("results", []):
                instructions.append(item.get("content", ""))

            # Query for specific rules about common violations
            result = await self.query_tool.execute_query(
                query_type="search",
                search_text="NO FALLBACKS reflexive agreement",
                limit=2,
            )
            for item in result.get("results", []):
                instructions.append(item.get("content", ""))

        except Exception as e:
            print(f"Warning: KB query failed: {e}", file=sys.stderr)

        return (
            "\n\n".join(instructions)
            if instructions
            else "No specific instructions found"
        )

    async def analyze(
        self,
        thought: str,
        thought_number: int,
        session_id: str = "default",
        history: List[str] = None,
        context: Dict = None,
    ) -> Dict[str, Any]:
        """Analyze a thought for violations and patterns"""

        start_time = time.time()

        # Build prompt
        prompt = f"""Analyze this thought for operational violations and patterns.

CURRENT THOUGHT #{thought_number}:
{thought}

RECENT HISTORY:
{chr(10).join(history[-3:]) if history else "No history"}

CRITICAL VIOLATIONS TO CHECK:
1. REFLEXIVE AGREEMENT: Starting with "You're right", "absolutely", "totally" without evaluation
2. OVERCONFIDENCE: Using "obviously", "clearly", "definitely" without evidence
3. UNVERIFIED ASSUMPTIONS: Making claims without checking facts
4. DESTRUCTIVE INTENT: Planning harmful/risky actions without safeguards
5. IGNORING INSTRUCTIONS: Not following established protocols

PATTERNS TO DETECT:
- Repetitive thinking (trying same approach repeatedly)
- Frustration indicators ("stuck", "can't", "confused")
- Missing context (not checking instructions/knowledge)
- Premature action (acting before understanding)

Provide structured analysis with actionable coaching questions and reminders."""

        # System instructions
        instructions = """You are a metacognitive analyzer detecting thinking violations and patterns.
Be precise, actionable, and helpful. Focus on improving thinking quality."""

        try:
            # ONE nano call only
            response = await self.interface.responses_create_structured(
                input=prompt,
                response_model=TriageAnalysisSchema,
                model="gpt-5-nano",
                instructions=instructions,
                temperature=0.3,
            )

            result = response.model_dump()
            result["response_time_ms"] = int((time.time() - start_time) * 1000)
            return result

        except Exception as e:
            # Return error response (NO FALLBACKS)
            return {
                "error": str(e),
                "violations": [],
                "patterns": [],
                "coaching_questions": [],
                "needs_escalation": False,
                "escalation_reason": None,
                "reminders": [],
                "confidence": 0.0,
                "analysis": f"Analysis failed: {e}",
                "response_time_ms": int((time.time() - start_time) * 1000),
            }


async def main():
    """CLI interface for testing"""

    if len(sys.argv) < 2:
        # Read from stdin if no args
        stdin_input = sys.stdin.read()
        if not stdin_input.strip():
            print(json.dumps({"error": "No input provided"}))
            return
        data = json.loads(stdin_input)
    else:
        # Parse command line JSON
        data = json.loads(sys.argv[1])

    analyzer = TriageAnalyzer()
    result = await analyzer.analyze(
        thought=data.get("thought", ""),
        thought_number=data.get("thought_number", 1),
        session_id=data.get("session_id", "cli-test"),
        history=data.get("history", []),
        context=data.get("context", {}),
    )

    # Output JSON to stdout
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
