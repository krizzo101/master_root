"""OpenAI provider for opsvi-memory using Responses API (GPT-5 family).

Functional minimal implementation with retries and timeouts. Reads API key
and configuration from environment variables:
- OPENAI_API_KEY (required)
- OPENAI_BASE_URL (optional)
- OPENAI_MODEL (optional; default gpt-5-mini)
"""

from typing import Any, Optional
import os
import logging
import json
import time

from opsvi_memory.providers.base import OpsviMemoryProvider
from opsvi_memory.config.settings import OpsviMemoryConfig
from opsvi_memory.exceptions.base import OpsviMemoryError

logger = logging.getLogger(__name__)

DEFAULT_MODEL = os.environ.get("OPENAI_MODEL", "gpt-5-mini")

class OpenAIProvider(OpsviMemoryProvider):
    """OpenAI API provider using Responses API."""

    def __init__(self, config: OpsviMemoryConfig):
        super().__init__(config=config)
        self._client = None

    async def connect(self) -> bool:
        """Initialize OpenAI client if API key is present."""
        try:
            if "OPENAI_API_KEY" not in os.environ:
                logger.error("OPENAI_API_KEY is not set in environment")
                return False
            base_url = os.environ.get("OPENAI_BASE_URL")
            timeout = int(os.environ.get("OPENAI_TIMEOUT", "90"))
            from openai import OpenAI  # type: ignore
            client_kwargs = {"timeout": timeout}
            if base_url:
                client_kwargs["base_url"] = base_url
            self._client = OpenAI(**client_kwargs)
            return True
        except Exception as e:  # noqa: BLE001
            logger.exception("Failed to initialize OpenAI client: %s", e)
            return False

    async def disconnect(self) -> None:
        self._client = None

    async def health_check(self) -> bool:
        return bool(self._client or os.environ.get("OPENAI_API_KEY"))

    async def generate_text(self, prompt: str, *, max_output_tokens: int = 800,
                             model: Optional[str] = None) -> str:
        """Generate text using OpenAI Responses API; returns raw text.

        Falls back to parsing output_text when structured outputs are unsupported.
        """
        if self._client is None:
            ok = await self.connect()
            if not ok:
                raise OpsviMemoryError("OpenAI client not initialized; set OPENAI_API_KEY")
        assert self._client is not None

        model_name = model or os.environ.get("OPENAI_MODEL", DEFAULT_MODEL)
        schema = {
            "name": "text_response",
            "schema": {
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
                "additionalProperties": False,
            },
        }

        base_kwargs = {
            "model": model_name,
            "input": prompt,
            "max_output_tokens": max_output_tokens,
        }
        with_schema = {
            **base_kwargs,
            "response_format": {"type": "json_schema", "json_schema": schema},
        }

        last_err: Optional[Exception] = None
        for attempt in range(1, 4):
            for use_schema in (True, False):
                kwargs = with_schema if use_schema else base_kwargs
                try:
                    resp = self._client.responses.create(**kwargs)
                    parsed = getattr(resp, "output_parsed", None)
                    if isinstance(parsed, dict) and parsed.get("text"):
                        return parsed["text"]
                    text = getattr(resp, "output_text", "") or ""
                    if isinstance(text, str) and text.strip():
                        try:
                            obj = json.loads(text)
                            if isinstance(obj, dict) and obj.get("text"):
                                return str(obj["text"])  # parsed JSON
                        except Exception:
                            pass
                        return text
                    # deep fallback
                    try:
                        data = resp.model_dump()
                    except Exception:
                        data = {}
                    outputs = (data.get("output") or data.get("outputs") or [])
                    for item in outputs:
                        if item.get("type") == "message":
                            for c in item.get("content") or []:
                                if c.get("type") in ("output_text", "text", "input_text"):
                                    val = c.get("text")
                                    if isinstance(val, dict):
                                        val = val.get("value") or val.get("text")
                                    if isinstance(val, str) and val.strip():
                                        return val
                    last_err = RuntimeError("Empty response content")
                except TypeError as e:
                    last_err = e
                    if use_schema:
                        # retry without schema
                        continue
                    raise
                except Exception as e:  # noqa: BLE001
                    last_err = e
            if attempt < 3:
                time.sleep(1.0 * attempt)
        raise OpsviMemoryError(f"OpenAI generation failed: {last_err}")
