"""
OpenAI API client implementation.

This module provides the OpenAI-specific implementation of the APIClient.
"""

import json
import re
import sys
import os
from openai import AsyncOpenAI
from openai import RateLimitError, APIError, APITimeoutError
from typing import Optional, Dict, Any

from genfilemap.api.base import APIClient
from genfilemap.config import load_config, get_config_value
from genfilemap.utils.file_utils import is_quiet_mode
from genfilemap.logging_utils import debug as log_debug


# Define the only approved model for OpenAI
# APPROVED_MODEL = "gpt-4o-mini"
# APPROVED_MODEL = "gpt-4.1-mini"
class OpenAIClient(APIClient):
    """OpenAI API client"""

    def __init__(self, api_key: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(api_key)
        self.client = AsyncOpenAI(api_key=api_key)
        # Use provided configuration or load default
        self.config = config if config is not None else load_config()

    def debug_print(self, msg: str) -> None:
        """
        Print debug message only if debug mode is enabled.

        Args:
            msg: The message to print
        """
        debug_enabled = get_config_value(self.config, "debug", False)
        if debug_enabled:
            # Use logging system so output gets captured by --log-file
            log_debug(msg)

    async def generate_completion(
        self, system_message: str, user_message: str, model: str, max_tokens: int = None
    ) -> str:
        """Generate a completion using OpenAI API"""
        # Enforce the approved model regardless of what's passed
        # if model != APPROVED_MODEL:
        #     self.debug_print(f"Warning: Model '{model}' is not approved. Using '{APPROVED_MODEL}' instead.")
        #     model = APPROVED_MODEL

        # Get max_tokens from config if not provided
        if max_tokens is None:
            max_tokens = get_config_value(self.config, "api.max_tokens", 1500)

        try:
            # Print debug information
            self.debug_print(
                f"DEBUG-API: Making API call to OpenAI with model: {model}"
            )
            self.debug_print(
                f"DEBUG-API: API key (first 4 chars): {self.api_key[:4]}***"
            )

            response = await self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message},
                ],
                max_tokens=max_tokens,
                n=1,
                temperature=0.2,
            )

            # Extract the content from the response
            content = response.choices[0].message.content.strip()

            # Update API call stats
            self.stats["api_calls"] += 1
            self.stats["tokens_used"] += response.usage.total_tokens

            # Print first few chars of content for debugging
            self.debug_print(
                f"DEBUG-API: Received response, first 50 chars: {content[:50]}..."
            )

            # Print the full response for debugging (this helps identify issues)
            self.debug_print("DEBUG-CODE-RAW-RESPONSE-START")
            self.debug_print(f"{content}")
            self.debug_print("DEBUG-CODE-RAW-RESPONSE-END")

            # If we expect JSON, try to extract it from markdown code blocks
            if "json" in system_message.lower() or "JSON" in system_message:
                # Try to extract JSON from markdown code blocks
                json_pattern = r"```(?:json)?\s*\n([\s\S]*?)\n```"
                json_matches = re.findall(json_pattern, content)

                if json_matches:
                    # Use the first JSON block found
                    json_content = json_matches[0].strip()
                    self.debug_print(
                        f"DEBUG-API: Extracted JSON from markdown code block, length: {len(json_content)}"
                    )

                    # Validate that it's proper JSON
                    try:
                        json.loads(json_content)
                        return json_content
                    except json.JSONDecodeError as e:
                        self.debug_print(
                            f"DEBUG-API: Extracted content is not valid JSON: {str(e)}"
                        )
                        pass  # Continue with returning the original content
                else:
                    self.debug_print("DEBUG-API: No JSON code blocks found in response")

                # If we couldn't extract from code blocks, look for JSON directly
                json_pattern = r"\{[\s\S]*\}"
                json_matches = re.search(json_pattern, content)
                if json_matches:
                    potential_json = json_matches.group(0)
                    self.debug_print(
                        f"DEBUG-API: Found potential JSON directly in content, length: {len(potential_json)}"
                    )
                    # Validate that it's proper JSON
                    try:
                        json.loads(potential_json)
                        self.debug_print(
                            "DEBUG-API: Successfully extracted valid JSON directly from content"
                        )
                        return potential_json
                    except json.JSONDecodeError as e:
                        self.debug_print(
                            f"DEBUG-API: Potential JSON is not valid: {str(e)}"
                        )
                        pass  # Continue with returning the original content

            return content

        except RateLimitError as e:
            self.debug_print(f"DEBUG-API: Rate limit exceeded: {str(e)}")
            return f"ERROR: OpenAI API rate limit exceeded: {str(e)}"
        except APIError as e:
            self.debug_print(f"DEBUG-API: API error: {str(e)}")
            return f"ERROR: OpenAI API error: {str(e)}"
        except APITimeoutError as e:
            self.debug_print(f"DEBUG-API: API timeout: {str(e)}")
            return f"ERROR: OpenAI API timeout: {str(e)}"
        except Exception as e:
            self.debug_print(f"DEBUG-API: Unexpected error: {str(e)}")
            return f"ERROR: Unexpected error during API call: {str(e)}"
