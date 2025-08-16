import logging
from typing import Any, Dict, List, Optional

from src.shared.openai_interfaces.base import OpenAIBaseInterface

logger = logging.getLogger(__name__)


class OpenAIResponsesInterface(OpenAIBaseInterface):
    """
    Interface for OpenAI Responses API (Beta).
    Supports structured outputs, reasoning, and conversation state per latest OpenAI docs.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        import openai

        self.client = openai.OpenAI()

    def create_response(
        self,
        model,
        input,
        instructions=None,
        text_format=None,
        response_format=None,
        reasoning=None,
        previous_response_id=None,
        store=None,
        max_output_tokens=None,
        debug=False,
    ):
        """
        Create a response using the OpenAI Responses API.
        Supports structured outputs (JSON schema), reasoning, and conversation state.
        Args:
            model: Model name (e.g., 'gpt-4.1-mini', 'o3', etc.)
            input: List of dicts (role/content) or string
            instructions: Optional system instructions
            text_format: None, 'json_object', or dict for JSON schema (legacy, prefer response_format)
            response_format: dict, e.g. {"type": "json_object"} (preferred for structured output)
            reasoning: dict, e.g. {"effort": "medium", "summary": "auto"}
            previous_response_id: str, for conversation state
            store: bool, whether to store response
            max_output_tokens: int, output token limit
            debug: bool, enable debug logging
        Returns:
            dict: API response
        """
        params = {"model": model, "input": input}
        if instructions:
            params["instructions"] = instructions
        # Prefer response_format if provided, fallback to text_format for legacy
        if response_format:
            params["response_format"] = response_format
        elif text_format:
            if isinstance(text_format, str):
                params["response_format"] = {"type": text_format}
            elif isinstance(text_format, dict):
                params["response_format"] = text_format
        if reasoning:
            params["reasoning"] = reasoning
        if previous_response_id:
            params["previous_response_id"] = previous_response_id
        if store is not None:
            params["store"] = store
        if max_output_tokens:
            params["max_output_tokens"] = max_output_tokens
        if debug:
            print("[DEBUG] OpenAI Responses API request params:", params)
        try:
            response = self.client.responses.create(**params)
            if debug:
                print("[DEBUG] OpenAI Responses API raw response:", response)
            # Robust output extraction
            output_text = getattr(response, "output_text", None)
            if not output_text and hasattr(response, "output"):
                # Try to extract from output[0].content[0].text
                try:
                    output = response.output
                    if output and "content" in output[0] and output[0]["content"]:
                        content = output[0]["content"][0]
                        if content.get("type") == "output_text":
                            output_text = content.get("text")
                        elif content.get("type") == "refusal":
                            output_text = f"[REFUSAL] {content.get('refusal')}"
                except Exception as e:
                    if debug:
                        print("[DEBUG] Output extraction error:", e)
            return {"raw": response, "output_text": output_text}
        except Exception as e:
            if debug:
                print("[DEBUG] OpenAI Responses API error:", e)
            return {"error": str(e)}

    def create_response_stream(self, **kwargs):
        """
        Create a streaming response (POST /responses with stream=True)
        Yields events as they arrive.
        """
        try:
            logger.debug(
                f"[OpenAIResponsesInterface] Creating streaming response with params: {kwargs}"
            )
            stream = self.client.responses.create(stream=True, **kwargs)
            for event in stream:
                yield event
        except Exception as e:
            logger.exception(
                f"[OpenAIResponsesInterface] Error creating streaming response: {e}"
            )
            self._handle_error(e)

    @staticmethod
    def parse_json_output(output_text: str) -> Optional[Any]:
        """
        Try to parse output_text as JSON. Returns dict/list or None if parsing fails.
        """
        import json

        try:
            return json.loads(output_text)
        except Exception:
            return None

    def retrieve_response(self, response_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Retrieve a response by ID (GET /responses/{response_id})"""
        try:
            logger.debug(
                f"[OpenAIResponsesInterface] Retrieving response_id: {response_id}"
            )
            response = self.client.responses.retrieve(response_id, **kwargs)
            logger.debug(f"[OpenAIResponsesInterface] Response retrieved: {response}")
            return (
                response.model_dump()
                if hasattr(response, "model_dump")
                else dict(response)
            )
        except Exception as e:
            logger.exception(
                f"[OpenAIResponsesInterface] Error retrieving response: {e}"
            )
            self._handle_error(e)
            return None

    def list_input_items(
        self, response_id: str, **kwargs
    ) -> Optional[List[Dict[str, Any]]]:
        """List input items for a response (GET /responses/{response_id}/input_items)"""
        try:
            logger.debug(
                f"[OpenAIResponsesInterface] Listing input items for response_id: {response_id}"
            )
            page = self.client.responses.input_items.list(response_id, **kwargs)
            logger.debug(f"[OpenAIResponsesInterface] Input items: {page.data}")
            return [
                item.model_dump() if hasattr(item, "model_dump") else dict(item)
                for item in page.data
            ]
        except Exception as e:
            logger.exception(
                f"[OpenAIResponsesInterface] Error listing input items: {e}"
            )
            self._handle_error(e)
            return None

    def delete_response(self, response_id: str) -> Optional[Dict[str, Any]]:
        """Delete a response by ID (DELETE /responses/{response_id})"""
        try:
            logger.debug(
                f"[OpenAIResponsesInterface] Deleting response_id: {response_id}"
            )
            result = self.client.responses.delete(response_id)
            logger.debug(f"[OpenAIResponsesInterface] Response deleted: {result}")
            return (
                result.model_dump() if hasattr(result, "model_dump") else dict(result)
            )
        except Exception as e:
            logger.exception(f"[OpenAIResponsesInterface] Error deleting response: {e}")
            self._handle_error(e)
            return None

    def cancel_response(self, response_id: str) -> Optional[Dict[str, Any]]:
        """Cancel a response (POST /responses/{response_id}/cancel)"""
        try:
            logger.debug(
                f"[OpenAIResponsesInterface] Cancelling response_id: {response_id}"
            )
            result = self.client.responses.cancel(response_id)
            logger.debug(f"[OpenAIResponsesInterface] Response cancelled: {result}")
            return (
                result.model_dump() if hasattr(result, "model_dump") else dict(result)
            )
        except Exception as e:
            logger.exception(
                f"[OpenAIResponsesInterface] Error cancelling response: {e}"
            )
            self._handle_error(e)
            return None

    # Async methods (optional, for completeness)
    async def acreate_response(self, **kwargs) -> Optional[Dict[str, Any]]:
        try:
            logger.debug(
                f"[OpenAIResponsesInterface] [async] Creating response with params: {kwargs}"
            )
            response = await self.client.responses.create(**kwargs)
            logger.debug(
                f"[OpenAIResponsesInterface] [async] Response created: {response}"
            )
            return (
                response.model_dump()
                if hasattr(response, "model_dump")
                else dict(response)
            )
        except Exception as e:
            logger.exception(
                f"[OpenAIResponsesInterface] [async] Error creating response: {e}"
            )
            self._handle_error(e)
            return None

    async def aretrieve_response(
        self, response_id: str, **kwargs
    ) -> Optional[Dict[str, Any]]:
        try:
            logger.debug(
                f"[OpenAIResponsesInterface] [async] Retrieving response_id: {response_id}"
            )
            response = await self.client.responses.retrieve(response_id, **kwargs)
            logger.debug(
                f"[OpenAIResponsesInterface] [async] Response retrieved: {response}"
            )
            return (
                response.model_dump()
                if hasattr(response, "model_dump")
                else dict(response)
            )
        except Exception as e:
            logger.exception(
                f"[OpenAIResponsesInterface] [async] Error retrieving response: {e}"
            )
            self._handle_error(e)
            return None

    async def alist_input_items(
        self, response_id: str, **kwargs
    ) -> Optional[List[Dict[str, Any]]]:
        try:
            logger.debug(
                f"[OpenAIResponsesInterface] [async] Listing input items for response_id: {response_id}"
            )
            page = await self.client.responses.input_items.list(response_id, **kwargs)
            logger.debug(f"[OpenAIResponsesInterface] [async] Input items: {page.data}")
            return [
                item.model_dump() if hasattr(item, "model_dump") else dict(item)
                for item in page.data
            ]
        except Exception as e:
            logger.exception(
                f"[OpenAIResponsesInterface] [async] Error listing input items: {e}"
            )
            self._handle_error(e)
            return None

    async def adelete_response(self, response_id: str) -> Optional[Dict[str, Any]]:
        try:
            logger.debug(
                f"[OpenAIResponsesInterface] [async] Deleting response_id: {response_id}"
            )
            result = await self.client.responses.delete(response_id)
            logger.debug(
                f"[OpenAIResponsesInterface] [async] Response deleted: {result}"
            )
            return (
                result.model_dump() if hasattr(result, "model_dump") else dict(result)
            )
        except Exception as e:
            logger.exception(
                f"[OpenAIResponsesInterface] [async] Error deleting response: {e}"
            )
            self._handle_error(e)
            return None

    async def acancel_response(self, response_id: str) -> Optional[Dict[str, Any]]:
        try:
            logger.debug(
                f"[OpenAIResponsesInterface] [async] Cancelling response_id: {response_id}"
            )
            result = await self.client.responses.cancel(response_id)
            logger.debug(
                f"[OpenAIResponsesInterface] [async] Response cancelled: {result}"
            )
            return (
                result.model_dump() if hasattr(result, "model_dump") else dict(result)
            )
        except Exception as e:
            logger.exception(
                f"[OpenAIResponsesInterface] [async] Error cancelling response: {e}"
            )
            self._handle_error(e)
            return None
