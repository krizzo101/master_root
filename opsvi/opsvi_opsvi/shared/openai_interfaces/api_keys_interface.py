from typing import Any

from shared.openai_interfaces.base import OpenAIBaseInterface


class OpenAIAPIKeysInterface(OpenAIBaseInterface):
    """
    Interface for OpenAI API Keys API.
    Reference: https://platform.openai.com/docs/api-reference/api-keys
    """

    def create_api_key(self, **kwargs) -> dict[str, Any]:
        """
        Create an API key.
        POST /v1/api_keys
        """
        try:
            response = self.client.api_keys.create(**kwargs)
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    def list_api_keys(self) -> list[dict[str, Any]]:
        """
        List all API keys.
        GET /v1/api_keys
        """
        try:
            response = self.client.api_keys.list()
            return response["data"]
        except Exception as e:
            self._handle_error(e)

    def retrieve_api_key(self, api_key_id: str) -> dict[str, Any]:
        """
        Retrieve an API key by ID.
        GET /v1/api_keys/{api_key_id}
        """
        try:
            response = self.client.api_keys.retrieve(api_key_id)
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    def delete_api_key(self, api_key_id: str) -> dict[str, Any]:
        """
        Delete an API key by ID.
        DELETE /v1/api_keys/{api_key_id}
        """
        try:
            response = self.client.api_keys.delete(api_key_id)
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    async def acreate_api_key(self, **kwargs) -> dict[str, Any]:
        """
        Async: Create an API key.
        POST /v1/api_keys
        """
        try:
            response = await self.client.api_keys.create(**kwargs)
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    async def alist_api_keys(self) -> list[dict[str, Any]]:
        """
        Async: List all API keys.
        GET /v1/api_keys
        """
        try:
            response = await self.client.api_keys.list()
            return response["data"]
        except Exception as e:
            self._handle_error(e)

    async def aretrieve_api_key(self, api_key_id: str) -> dict[str, Any]:
        """
        Async: Retrieve an API key by ID.
        GET /v1/api_keys/{api_key_id}
        """
        try:
            response = await self.client.api_keys.retrieve(api_key_id)
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    async def adelete_api_key(self, api_key_id: str) -> dict[str, Any]:
        """
        Async: Delete an API key by ID.
        DELETE /v1/api_keys/{api_key_id}
        """
        try:
            response = await self.client.api_keys.delete(api_key_id)
            return dict(response)
        except Exception as e:
            self._handle_error(e)
