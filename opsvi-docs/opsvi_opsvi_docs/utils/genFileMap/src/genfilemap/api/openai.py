# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"OpenAI API Client Implementation","description":"This module provides the OpenAI-specific implementation of the APIClient, including methods for generating completions using the OpenAI API.","last_updated":"2025-03-12","type":"python"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Imports","description":"Imports necessary modules and classes for the OpenAI API client.","line_start":3,"line_end":12},{"name":"OpenAIClient Class","description":"Defines the OpenAIClient class that extends APIClient and implements methods for interacting with the OpenAI API.","line_start":13,"line_end":35}],"key_elements":[{"name":"OpenAIClient","description":"Class for the OpenAI API client that inherits from APIClient.","line":13},{"name":"__init__","description":"Constructor for initializing the OpenAIClient with an API key.","line":15},{"name":"generate_completion","description":"Asynchronous method to generate a completion using the OpenAI API.","line":20}]}
"""
# FILE_MAP_END

"""
OpenAI API client implementation.

This module provides the OpenAI-specific implementation of the APIClient.
"""

from openai import AsyncOpenAI
from openai import RateLimitError, APIError, APITimeoutError

from genfilemap.api.base import APIClient
from genfilemap.config import Config


class OpenAIClient(APIClient):
    """OpenAI API client"""

    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.client = AsyncOpenAI(api_key=api_key)
        self.config = Config()  # Initialize config for settings

    async def generate_completion(
        self, system_message: str, user_message: str, model: str, max_tokens: int = None
    ) -> str:
        """Generate a completion using OpenAI API"""
        # Get max_tokens from config if not provided
        if max_tokens is None:
            max_tokens = self.config.get("api.max_tokens", 1500)

        response = await self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content.strip()
