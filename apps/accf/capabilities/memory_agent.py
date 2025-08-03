"""
ACCF Memory Agent

Purpose:
    Provides memory management and retrieval capabilities for agents, including persistent storage and LLM-backed Q&A.

References:
    - docs/applications/ACCF/standards/capability_agent_requirements.md
    - docs/applications/ACCF/architecture/adr/capability_agent_adrs.md
    - .cursor/templates/implementation/capability_agent_output_template.yml

Usage:
    from capabilities.memory_agent import MemoryAgent
    agent = MemoryAgent(...)
"""

from agent_base.agent_base import LLMBaseAgent


class MemoryAgent(LLMBaseAgent):
    def __init__(self, api_key_env: str = "OPENAI_API_KEY", config: dict = None):
        super().__init__(name="MemoryAgent", api_key_env=api_key_env, config=config)
        self.memory = {}

    def store(self, key: str, value):
        """Store a value in persistent memory."""
        self.memory[key] = value
        self.logger.info(f"Stored key={key}")

    def retrieve(self, key: str):
        """Retrieve a value from persistent memory."""
        value = self.memory.get(key)
        self.logger.info(f"Retrieved key={key} value={value}")
        return value

    def answer(self, prompt: str) -> dict:
        """Answer a memory-related question using LLM and stored memory."""
        import json

        try:
            context = "\n".join(f"{k}: {v}" for k, v in self.memory.items())
            full_prompt = f"Memory Context:\n{context}\n\nQuestion: {prompt}"
            self.logger.debug(f"MemoryAgent prompt: {full_prompt}")
            # Use shared interface for OpenAI API access
            from shared.openai_interfaces.responses_interface import (
                OpenAIResponsesInterface,
            )

            llm = OpenAIResponsesInterface(api_key=self.api_key)

            # Use approved model for agent execution
            response = llm.create_response(
                model="gpt-4.1-mini",
                input=full_prompt,
                text_format={"type": "json_object"},
            )

            # Extract response from shared interface
            output_text = response.get("output_text") or response.get("answer") or ""
            # Response already extracted from shared interface above
            self.logger.debug(f"MemoryAgent output_text: {output_text}")
            parsed = None
            if output_text:
                try:
                    import re

                    code_fence_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
                    match = re.search(
                        code_fence_pattern,
                        output_text.strip(),
                        re.IGNORECASE | re.DOTALL,
                    )
                    if match:
                        json_str = match.group(1).strip()
                        self.logger.debug(f"Extracted JSON from code fence: {json_str}")
                    else:
                        json_str = output_text.strip()
                        self.logger.debug(
                            f"No code fence found, using raw output: {json_str}"
                        )
                    parsed = json.loads(json_str)
                    self.logger.debug(f"MemoryAgent parsed JSON: {parsed}")
                except Exception as e:
                    self.logger.warning(
                        f"MemoryAgent: Could not parse LLM output as JSON. Raw output: {output_text}. Error: {e}"
                    )
                    parsed = {"answer": output_text, "context": context}
            else:
                parsed = {"answer": "", "context": context}
            return parsed
        except Exception as e:
            self.logger.error(f"LLM call failed: {e}")
            return {"answer": f"[Error: {e}]", "context": ""}
