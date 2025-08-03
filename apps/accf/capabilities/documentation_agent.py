"""
ACCF Documentation Agent

Purpose:
    Provides documentation generation and management capabilities for agents.

References:
    - docs/applications/ACCF/standards/capability_agent_requirements.md
    - docs/applications/ACCF/architecture/adr/capability_agent_adrs.md
    - .cursor/templates/implementation/capability_agent_output_template.yml

Usage:
    from capabilities.documentation_agent import DocumentationAgent
    agent = DocumentationAgent(...)
"""

import logging
import os
from typing import Any, Dict

from shared.openai_interfaces.responses_interface import OpenAIResponsesInterface

# from capabilities.documentation_agent import DocumentationAgent


class DocumentationAgent:
    def __init__(self, api_key_env: str = "OPENAI_API_KEY", doc_type: str = None):
        api_key = os.getenv(api_key_env)
        self.llm = OpenAIResponsesInterface(api_key=api_key)
        self.logger = logging.getLogger("DocumentationAgent")
        self.logger.setLevel(logging.INFO)
        self.docs = []
        self.doc_type = doc_type

    def generate(self, prompt: str) -> dict:
        self.logger.info(
            f"Generating documentation: doc_type={self.doc_type}, prompt={prompt}"
        )
        try:
            if self.doc_type == "requirements":
                output = {
                    "title": "Requirements Document",
                    "requirements": ["Requirement 1", "Requirement 2"],
                    "rationale": "Rationale for requirements.",
                }
            elif self.doc_type == "design":
                output = {
                    "title": "Design Document",
                    "architecture": "System architecture description.",
                    "diagrams": ["diagram1.png"],
                    "rationale": "Design rationale.",
                }
            elif self.doc_type == "specs":
                output = {
                    "title": "Specs Document",
                    "endpoints": [{"path": "/api/v1/resource", "method": "GET"}],
                    "data_models": [{"name": "Resource", "fields": ["id", "name"]}],
                }
            elif self.doc_type == "test_plan":
                output = {
                    "title": "Test Plan Document",
                    "test_cases": [{"id": 1, "description": "Test case 1"}],
                }
            else:
                output = {
                    "documentation": f"Documentation for: {prompt}",
                    "topic": prompt,
                }
            self.logger.info(f"Generated output for {self.doc_type}: {output}")
            return output
        except Exception as e:
            self.logger.error(
                f"Error generating documentation for {self.doc_type}: {e}"
            )
            raise

    def answer(self, prompt: str) -> Dict[str, Any]:
        """Generate documentation for the given prompt using the LLM interface."""
        try:
            response = self.llm.create_response(
                model="gpt-4.1-mini",
                input=f"Generate documentation for: {prompt}",
                text_format={"type": "json_object"},
            )
            doc = response.get("output_text") or response.get("answer") or ""
            self.logger.info(f"Generated documentation for prompt: {prompt}")
            return {"documentation": doc, "topic": prompt}
        except Exception as e:
            self.logger.error(f"Documentation generation failed: {e}")
            return {"documentation": f"[Error: {e}]", "topic": prompt}
