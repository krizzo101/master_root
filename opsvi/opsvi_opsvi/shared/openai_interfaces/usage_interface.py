from typing import Any, Dict

from shared.openai_interfaces.base import OpenAIBaseInterface


class OpenAIUsageInterface(OpenAIBaseInterface):
    """
    Interface for OpenAI Usage API.
    Reference: https://platform.openai.com/docs/api-reference/usage
    """

    def retrieve_usage(self, **kwargs) -> Dict[str, Any]:
        """
        Retrieve usage statistics.
        GET /v1/dashboard/billing/usage
        """
        try:
            response = self.client.usage.retrieve(**kwargs)
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    def retrieve_subscription(self, **kwargs) -> Dict[str, Any]:
        """
        Retrieve subscription information.
        GET /v1/dashboard/billing/subscription
        """
        try:
            response = self.client.usage.retrieve_subscription(**kwargs)
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    async def aretrieve_usage(self, **kwargs) -> Dict[str, Any]:
        """
        Async: Retrieve usage statistics.
        GET /v1/dashboard/billing/usage
        """
        try:
            response = await self.client.usage.retrieve(**kwargs)
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    async def aretrieve_subscription(self, **kwargs) -> Dict[str, Any]:
        """
        Async: Retrieve subscription information.
        GET /v1/dashboard/billing/subscription
        """
        try:
            response = await self.client.usage.retrieve_subscription(**kwargs)
            return dict(response)
        except Exception as e:
            self._handle_error(e)
