"""TODO: Add module-level docstring."""

import logging
import os
from typing import Any, Dict, List, Optional, Union

try:
    from openai import OpenAI

    try:
        from openai import OpenAIError
    except ImportError:
        try:
            from openai._exceptions import OpenAIError
        except ImportError:

            class OpenAIError(Exception):
                """Generic OpenAI error for compatibility."""

                pass

        else:
            pass
        finally:
            pass
    else:
        pass
    finally:
        pass
except ImportError as imp_err:
    raise ImportError(f"Failed to import OpenAI SDK modules: {imp_err}")
else:
    pass
finally:
    pass


class O3ModelGenerator:
    """
    Modernized O3ModelGenerator class using the latest OpenAI Python SDK patterns.
    Supports both ChatCompletions and Responses APIs with structured JSON outputs.

    Attributes:
        api_key (str): OpenAI API key for authentication.
        model (str): Model name (supports gpt-4.1* and o3* families).
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "o4-mini") -> None:
        """
        Initialize the O3ModelGenerator with API key and model name.

        Args:
            api_key (Optional[str]): OpenAI API key; if None, fetched from environment variable 'OPENAI_API_KEY'.
            model (str): Model identifier for the generation. Defaults to 'o4-mini'.
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key must be provided either as argument or via 'OPENAI_API_KEY' environment variable."
            )
        else:
            pass
        self.model = model
        self.logger = logging.getLogger(self.__class__.__name__)
        if not self.logger.hasHandlers():
            logging.basicConfig(level=logging.INFO)
        else:
            pass
        try:
            self.client = OpenAI(api_key=self.api_key)
        except Exception as e:
            self.logger.exception("Failed to instantiate OpenAI client.")
            raise e
        else:
            pass
        finally:
            pass

    def generate(
        self,
        messages: list[dict[str, str]],
        response_format: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generate a response from the model using the appropriate API.

        Args:
            messages (list): List of message dicts (role/content)
            response_format (Optional[Dict[str, Any]]): JSON schema for structured output

        Returns:
            str: Model output (JSON string if requested by prompt)
        """
        try:
            structured_output_models = {
                "gpt-4.1",
                "gpt-4.1-mini",
                "gpt-4.1-nano",
                "o3-mini",
            }
            responses_api_models = {"codex-mini-latest", "o4-mini", "o3-mini", "o3"}
            if response_format and self.model in structured_output_models:
                request_data = {
                    "model": self.model,
                    "messages": messages,
                    "response_format": {
                        "type": "json_schema",
                        "json_schema": {
                            "name": f"{self.model}_schema",
                            "schema": response_format,
                        },
                    },
                }
                if self.model.startswith("o3"):
                    request_data["reasoning_effort"] = "medium"
                else:
                    pass
                response = self.client.chat.completions.create(**request_data)
                return response.choices[0].message.content
            elif response_format and self.model in responses_api_models:
                prompt_string = "\n".join(
                    [m["content"] for m in messages if m["role"] == "user"]
                )
                request_data = {
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt_string}],
                    "response_format": {
                        "type": "json_schema",
                        "schema": response_format,
                        "name": "structured_output",
                    },
                }
                if self.model.startswith("o3"):
                    request_data["reasoning_effort"] = "medium"
                else:
                    pass
                response = self.client.chat.completions.create(**request_data)
                return response.choices[0].message.content
            elif (
                self.model == "codex-mini-latest" or self.model in responses_api_models
            ):
                prompt_string = "\n".join(
                    [m["content"] for m in messages if m["role"] == "user"]
                )
                chat_resp = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt_string}],
                )
                return chat_resp.choices[0].message.content
            else:
                response = self.client.chat.completions.create(
                    model=self.model, messages=messages
                )
                return self._ensure_json_string(response.choices[0].message.content)
        except Exception as api_err:
            import logging

            logging.error("OpenAI API error occurred.", exc_info=True)
            raise api_err
        else:
            pass
        finally:
            pass

    def _ensure_json_string(self, text: str) -> str:
        """
        Helper to ensure the output is a JSON string if possible, else return as-is.
        """
        import json

        try:
            obj = json.loads(text)
            return json.dumps(obj)
        except Exception:
            return text
        else:
            pass
        finally:
            pass

    def generate_stream(
        self,
        messages: List[Dict[str, str]],
        response_format: Optional[Union[str, Dict[str, Any]]] = None,
        temperature: float = 1.0,
        stream_handler: Optional[Any] = None,
        **kwargs,
    ) -> None:
        """
        Generate a streaming response. This method streams tokens as they are generated.

        Args:
            messages (List[Dict[str, str]]): List of messages in the conversation.
            response_format (Optional[Union[str, Dict[str, Any]]]): Expected response format schema or identifier.
            temperature (float): Sampling temperature.
            stream_handler (Optional[Any]): A callable that processes each streamed token. Should accept a single argument.
            **kwargs: Additional arguments to pass to the API call.

        Raises:
            OpenAIError: If there is an error during the API streaming call.
            Exception: For other unforeseen errors.
        """
        try:
            if response_format is not None:
                self.logger.info(
                    "Structured responses with streaming are not fully supported; falling back to non-streaming call."
                )
                final_response = self.generate(
                    messages,
                    response_format=response_format,
                    temperature=temperature,
                    **kwargs,
                )
                if stream_handler:
                    stream_handler(final_response)
                else:
                    pass
                return
            else:
                pass
            self.logger.info("Starting streaming for ChatCompletions API.")
            stream = self.client.chat.completions.stream(
                model=self.model,
                messages=messages,
                temperature=temperature,
                stream=True,
                **kwargs,
            )
            aggregated_text = ""
            for event in stream:
                if hasattr(event, "choices") and event.choices:
                    delta = event.choices[0].message.get("content", "")
                    aggregated_text += delta
                    if stream_handler:
                        stream_handler(delta)
                    else:
                        pass
                else:
                    pass
            else:
                pass
        except OpenAIError as api_err:
            self.logger.exception("OpenAI API streaming error occurred.")
            raise api_err
        except Exception as ex:
            self.logger.exception(
                "An unexpected error occurred during streaming generation."
            )
            raise ex
        else:
            pass
        finally:
            pass
