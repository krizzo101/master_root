"""
ACCF Critique Agent

Purpose:
    Provides critique and review capabilities for agents.

References:
    - docs/applications/ACCF/standards/capability_agent_requirements.md
    - docs/applications/ACCF/architecture/adr/capability_agent_adrs.md
    - .cursor/templates/implementation/capability_agent_output_template.yml

Usage:
    from capabilities.critique_agent import CritiqueAgent
    agent = CritiqueAgent(...)
"""

import logging
import os
from typing import Any, Dict

from shared.openai_interfaces.responses_interface import OpenAIResponsesInterface

# from capabilities.critique_agent import CritiqueAgent


class CritiqueAgent:
    def __init__(self, api_key_env: str = "OPENAI_API_KEY"):
        api_key = os.getenv(api_key_env)
        self.llm = OpenAIResponsesInterface(api_key=api_key)
        self.logger = logging.getLogger("CritiqueAgent")
        self.criteria = []
        self.critiques = []

    def critique(self, content: str) -> Dict[str, Any]:
        """Critique content using LLM (simulated)."""
        try:
            prompt = f"Critique the following content: {content}"
            response = self.llm.create_response(
                model="gpt-4.1-mini",
                input=prompt,
                text_format={"type": "json_object"},
            )
            critique = response.get("output_text") or response.get("answer") or ""
            self.logger.info("Critiqued content")
            return {"critique": critique, "content": content}
        except Exception as e:
            self.logger.error(f"Critique failed: {e}")
            return {"critique": f"[Error: {e}]", "content": content}

    def answer(self, prompt: str) -> dict:
        """Critique the given prompt using the LLM-backed critique method."""
        return self.critique(prompt)
