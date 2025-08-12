"""
OpenAI Reasoning Interface: Handles communication with OpenAI models, retries, structured outputs.
"""
import json
from typing import Any

import openai
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from multiagent_cli.config import AppConfig


class OpenAIReasoningInterface:
    """
    Abstraction for OpenAI model calls with robust error handling & JSON structure enforcement.
    """

    def __init__(self, config: AppConfig, logger_inst):
        self.config = config
        self.logger = logger_inst
        openai.api_key = config.OPENAI_API_KEY
        self.model = config.OPENAI_API_MODEL

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(2),
        retry=retry_if_exception_type((openai.error.OpenAIError, RuntimeError)),
        reraise=True,
    )
    async def reason(self, prompt: str, input_data: dict) -> dict:
        """
        Calls OpenAI model, expects a single structured JSON response.
        """
        self.logger.debug(f"Calling OpenAI: model={self.model}, prompt={prompt}")
        try:
            from openai import AsyncOpenAI

            openai_async = AsyncOpenAI(api_key=self.config.OPENAI_API_KEY)
            user_message = f"Task input: {json.dumps(input_data, ensure_ascii=False)}. Remember: reply ONLY with a JSON object, do NOT include extra text."
            response = await openai_async.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.2,
                max_tokens=512,
            )
            reply = response.choices[0].message.content.strip()
            # Find first {...} block for JSON
            json_start = reply.find("{")
            json_end = reply.rfind("}")
            if json_start == -1 or json_end == -1:
                raise RuntimeError(f"No JSON response detected in reply: {reply!r}")
            json_str = reply[json_start : json_end + 1]
            result = json.loads(json_str)
            self._validate_structured_response(result)
            self.logger.success("OpenAI returned valid JSON for task.")
            return result
        except Exception as exc:
            self.logger.opt(exception=exc).error(f"OpenAI call failed: {exc}")
            raise

    def _validate_structured_response(self, result: Any):
        if not isinstance(result, dict):
            raise RuntimeError(f"OpenAI response is not a JSON object: {result!r}")
        # Optional further schema validation
        return True
