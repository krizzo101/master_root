import logging
import os
from typing import Any, Dict

from agent_base.agent_base import LLMBaseAgent


class CheckMeAgent(LLMBaseAgent):
    """
    ACCF CheckMe Agent (Assistants API)
    Purpose: Provides self-check/validation for a given prompt, code, or text using OpenAI Assistants API.
    Returns a structured summary and list of issues or suggestions.
    Now supports session management and assistant caching.
    """

    # In-memory session store: session_id -> {thread_id, last_active}
    session_store = {}
    SESSION_TIMEOUT = 60 * 60  # 1 hour inactivity timeout
    MODEL = "gpt-4.1-mini"  # Default model, can be changed via config
    ASSISTANT_NAME = "CheckMeAgent_gpt41mini"
    _assistant_id = None  # Class-level cache

    def __init__(self, api_key_env: str = "OPENAI_API_KEY", config: dict = None):
        super().__init__(name="CheckMeAgent", api_key_env=api_key_env, config=config)
        # Logging to file (keep file handler logic)
        log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, "checkmeagent.log")
        log_file_handler_exists = any(
            isinstance(h, logging.FileHandler)
            and getattr(h, "baseFilename", None)
            and h.baseFilename.endswith("checkmeagent.log")
            for h in self.logger.handlers
        )
        if not log_file_handler_exists:
            handler = logging.FileHandler(log_path)
            formatter = logging.Formatter(
                "%(asctime)s %(levelname)s %(name)s %(message)s"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        # Model selection
        if config and "model" in config:
            self.MODEL = config["model"]
        # Assistant caching
        if not CheckMeAgent._assistant_id:
            CheckMeAgent._assistant_id = self._get_or_create_assistant()

    def _get_or_create_assistant(self):
        # Use shared interface for OpenAI API access
        from shared.openai_interfaces.responses_interface import (
            OpenAIResponsesInterface,
        )

        OpenAIResponsesInterface(api_key=self.api_key)

        # For session management, we'll use a simple approach with the shared interface
        # The assistant creation is handled internally by the shared interface
        return "shared_interface_assistant"

    def _session_expired(self, session):
        import time

        return time.time() - session["last_active"] > self.SESSION_TIMEOUT

    def _get_or_create_session(self, session_id):
        import time

        session = self.session_store.get(session_id)
        if not session or self._session_expired(session):
            # Use simple session tracking for shared interface
            session = {"session_id": session_id, "last_active": time.time()}
            self.session_store[session_id] = session
            self.logger.info(f"Started new session: {session_id}")
        else:
            session["last_active"] = time.time()
        return session

    def reset_session(self, session_id):
        import time

        # Use simple session tracking for shared interface
        session = {"session_id": session_id, "last_active": time.time()}
        self.session_store[session_id] = session
        self.logger.info(f"Session reset: {session_id}")
        return session

    def answer(self, prompt: str, session_id: str = "default") -> Dict[str, Any]:
        """
        Review the input for errors, omissions, or improvements using the OpenAI Assistants API.
        Maintains session context per session_id.
        Returns a dict with 'result' (summary) and 'details' (list of issues/suggestions).
        """
        import json

        try:
            self._get_or_create_session(session_id)
            review_prompt = (
                "You are a senior reviewer. Review the following for errors, omissions, or improvements. "
                "If you find any issues, list them clearly. If the input is correct, respond with 'APPROVED'. "
                "Otherwise, respond with 'NOT APPROVED' and actionable suggestions. "
                "Be specific and concise.\n\nInput:\n"
                + prompt
                + '\n\nRespond ONLY with a valid JSON object: {"result": "APPROVED|NOT APPROVED", "details": [ ... ]}'
            )
            self.logger.debug(f"CheckMeAgent prompt: {review_prompt}")

            # Use shared interface for OpenAI API access
            from shared.openai_interfaces.responses_interface import (
                OpenAIResponsesInterface,
            )

            llm = OpenAIResponsesInterface(api_key=self.api_key)

            # Use approved model for agent execution
            response = llm.create_response(
                model="gpt-4.1-mini",
                input=review_prompt,
                text_format={"type": "json_object"},
            )

            # Extract response from shared interface
            output_text = response.get("output_text") or response.get("answer") or ""
            self.logger.debug(f"CheckMeAgent output_text: {output_text}")
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
                    self.logger.debug(f"CheckMeAgent parsed JSON: {parsed}")
                except Exception as e:
                    self.logger.warning(
                        f"CheckMeAgent: Could not parse LLM output as JSON. Raw output: {output_text}. Error: {e}"
                    )
                    parsed = {"result": "NOT APPROVED", "details": [output_text]}
            return parsed or {"result": "NOT APPROVED", "details": [output_text]}
        except Exception as e:
            self.logger.error(f"CheckMeAgent shared interface call failed: {e}")
            return {"result": f"[Error: {e}]", "details": [], "raw": ""}
