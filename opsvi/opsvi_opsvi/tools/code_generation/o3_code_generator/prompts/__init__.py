"""
Prompts package for O3 Code Generator

This package contains the prompt definitions.
"""

from .idea_formation_prompts import (
    BRAINSTORMING_SYSTEM_PROMPT,
    FEASIBILITY_ASSESSMENT_SYSTEM_PROMPT,
    IDEA_FORMATION_SYSTEM_PROMPT,
    MARKET_RESEARCH_SYSTEM_PROMPT,
)
from .system_prompt import SYSTEM_PROMPT

__all__ = [
    "SYSTEM_PROMPT",
    "BRAINSTORMING_SYSTEM_PROMPT",
    "IDEA_FORMATION_SYSTEM_PROMPT",
    "MARKET_RESEARCH_SYSTEM_PROMPT",
    "FEASIBILITY_ASSESSMENT_SYSTEM_PROMPT",
]
