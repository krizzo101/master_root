#!/usr/bin/env python3
"""
Knowledge Nano Agent - Middleware for transforming raw knowledge into structured format

This agent sits between the MCP tool and the storage layer, transforming
raw agent input into properly structured knowledge entries.
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from opsvi_llm.providers.openai_provider import OpenAIConfig

# Import OpenAI unified interface for structured outputs
from opsvi_llm.providers.openai_unified_interface import OpenAIUnifiedInterface
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class KnowledgeSchema(BaseModel):
    """Structured output schema for knowledge entries"""

    model_config = {"extra": "forbid"}  # This ensures additionalProperties: false

    knowledge_type: str = Field(
        description="Type: ERROR_SOLUTION, CODE_PATTERN, WORKFLOW, USER_PREFERENCE, CONTEXT_PATTERN, TOOL_USAGE"
    )
    content: str = Field(description="The main knowledge content, clear and actionable")
    summary: str = Field(description="Brief one-line summary of the knowledge")
    tags: List[str] = Field(description="Relevant tags for categorization and search")
    context: str = Field(description="Contextual information as a JSON string")
    confidence_score: float = Field(
        description="Initial confidence score (0.0 to 1.0)", ge=0.0, le=1.0
    )
    supersedes: List[str] = Field(
        description="List of knowledge IDs this entry supersedes"
    )
    related_to: List[str] = Field(description="List of related knowledge IDs")


class KnowledgeNanoAgent:
    """
    Nano agent that transforms raw knowledge input into structured format
    using gpt-5-nano with structured outputs.
    """

    SYSTEM_PROMPT = """## ROLE
You are the KB Storage Nano Agent that structures knowledge for optimal retrieval.

## KNOWLEDGE TYPES (Use Consistently)
- ERROR_SOLUTION: Bugs, errors, exceptions with their fixes
- CODE_PATTERN: Functions, classes, code structures, implementations
- WORKFLOW: Multi-step processes, procedures, migrations
- USER_PREFERENCE: Settings, configurations, user choices
- CONTEXT_PATTERN: Session contexts, insights, decisions, observations
- TOOL_USAGE: Commands, tool instructions, how-to guides

## MANDATORY CONTENT PREFIXES
ALWAYS add these prefixes to content field when applicable:
- "MEMENTO NOTE:" - Personal reminders, important notes
- "SYSTEM TRUTH:" - Verified facts about the system
- "BUG DISCOVERED:" - When documenting a problem/bug
- "FIX APPLIED:" - When documenting a solution/fix
- "SESSION CONTEXT:" - Session-specific information
- "GLOBAL OPERATIONAL INSTRUCTIONS" - System-wide rules
- "OPTIMIZATION OPPORTUNITY:" - Potential improvements
- "PATTERN OBSERVED:" - Recurring patterns noticed
- "PROJECT INTELLIGENCE:" - Project structure/analysis info

## TAGGING RULES (For Searchability)
Always include relevant tags from these categories:
1. **Project tags**: accf, knowledge-system, project-intelligence, master-root
2. **Tech tags**: python, typescript, neo4j, mcp, fastmcp, openai, claude
3. **Type tags**: bug, fix, architecture, critical, session, workflow
4. **Source tags**: source-code, documentation, analysis, user-input
5. **Specific tags**: Related to the actual content

## CONTENT STRUCTURING
1. Start with appropriate prefix (see above)
2. Follow with clear, actionable content
3. Include file paths when relevant (use file_path field)
4. Reference related knowledge IDs in related_to field
5. Mark deprecated knowledge in supersedes field

## PROJECT-INTELLIGENCE INTEGRATION
When storing project-related knowledge:
- Tag with project name (e.g., "project-intelligence")
- Include file paths in file_path field
- Reference .consult/ directories if relevant
- Note workspace-relative vs absolute paths
- Tag with "project-map" if about structure

## CONFIDENCE SCORING
- 0.9-1.0: Tested, verified, production-ready
- 0.7-0.8: Good solution, minor refinements possible
- 0.5-0.6: General pattern, needs validation
- 0.3-0.4: Uncertain, requires testing
- 0.1-0.2: Experimental, speculative

## SUMMARY GENERATION
Create concise one-line summaries that:
- Start with the main action/finding
- Include the key context
- Are searchable and descriptive

## CONTEXT FIELD
Store as JSON string with relevant metadata:
- Session ID if available
- File paths involved
- Related commands or operations
- Timestamps of events
Use "{}" only if truly no context exists.

## CRITICAL RULES
1. ALWAYS use prefixes - they enable effective search
2. ALWAYS include multiple relevant tags
3. ALWAYS assess confidence honestly
4. ALWAYS provide actionable content
5. NEVER leave summary empty - it aids discovery

## OUTPUT
Return structured JSON with ALL fields populated correctly."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the nano agent with OpenAI configuration"""
        config = OpenAIConfig(
            provider_name="openai",  # Required field
            api_key=api_key or os.getenv("OPENAI_API_KEY"),
            default_model="gpt-5-nano",  # Use nano for efficiency
            temperature=0.3,  # Low temperature for consistency
            max_tokens=1000,
            enable_audit_logging=True,
        )
        self.interface = OpenAIUnifiedInterface(config)
        logger.info("Knowledge Nano Agent initialized with gpt-5-nano")

    async def transform_knowledge(
        self,
        raw_input: str,
        hint_type: Optional[str] = None,
        hint_tags: Optional[List[str]] = None,
        hint_supersedes: Optional[List[str]] = None,
    ) -> KnowledgeSchema:
        """
        Transform raw knowledge input into structured format.

        Args:
            raw_input: Raw knowledge text from agent
            hint_type: Optional hint about knowledge type
            hint_tags: Optional suggested tags
            hint_supersedes: Optional IDs this supersedes

        Returns:
            Structured knowledge entry
        """
        # Build the user prompt
        user_prompt = f"Transform this knowledge into structured format:\n\n{raw_input}"

        if hint_type:
            user_prompt += f"\n\nHint: This is likely a {hint_type}"
        if hint_tags:
            user_prompt += f"\nSuggested tags: {', '.join(hint_tags)}"
        if hint_supersedes:
            user_prompt += f"\nThis supersedes: {', '.join(hint_supersedes)}"

        try:
            # Use Responses API with structured output (2025 STANDARD)
            response = await self.interface.responses_create_structured(
                instructions=self.SYSTEM_PROMPT,
                input=user_prompt,
                response_model=KnowledgeSchema,  # Fixed parameter name
                model="gpt-5-nano",
                temperature=0.3,
            )

            # Add hints if not already included
            if hint_supersedes and not response.supersedes:
                response.supersedes = hint_supersedes

            logger.info(
                f"Transformed knowledge: type={response.knowledge_type}, tags={response.tags}"
            )
            return response

        except Exception as e:
            error_msg = f"Failed to transform knowledge: {e}"
            logger.error(error_msg)
            logger.error(f"Failed content: {raw_input[:200]}...")
            # No fallback - raise the error
            raise RuntimeError(error_msg) from e

    def transform_knowledge_sync(
        self,
        raw_input: str,
        hint_type: Optional[str] = None,
        hint_tags: Optional[List[str]] = None,
        hint_supersedes: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Synchronous wrapper for transform_knowledge.
        Returns dict instead of Pydantic model for compatibility.
        """
        import asyncio

        # Get or create event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Run the async function
        result = loop.run_until_complete(
            self.transform_knowledge(raw_input, hint_type, hint_tags, hint_supersedes)
        )

        # Convert to dict
        return result.model_dump()


# Singleton instance for reuse
_nano_agent = None


def get_nano_agent() -> KnowledgeNanoAgent:
    """Get or create the singleton nano agent instance"""
    global _nano_agent
    if _nano_agent is None:
        _nano_agent = KnowledgeNanoAgent()
    return _nano_agent
