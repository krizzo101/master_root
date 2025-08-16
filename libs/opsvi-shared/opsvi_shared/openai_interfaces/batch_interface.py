from typing import Any, Dict, List

import openai

from src.shared.openai_interfaces.base import OpenAIBaseInterface


class OpenAIBatchInterface(OpenAIBaseInterface):
    """
    Interface for OpenAI Batch API.
    Reference: https://platform.openai.com/docs/api-reference/batch
    """

    def create_batch(self, **kwargs) -> Dict[str, Any]:
        """
        Create a batch.
        POST /v1/batches
        """
        try:
            response = self.client.batches.create(**kwargs)
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    def retrieve_batch(self, batch_id: str) -> Dict[str, Any]:
        """
        Retrieve a batch by ID.
        GET /v1/batches/{batch_id}
        """
        try:
            response = self.client.batches.retrieve(batch_id)
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    def list_batches(self) -> List[Dict[str, Any]]:
        """
        List all batches.
        GET /v1/batches
        """
        try:
            response = self.client.batches.list()
            return response["data"]
        except Exception as e:
            self._handle_error(e)

    def cancel_batch(self, batch_id: str) -> Dict[str, Any]:
        """
        Cancel a batch.
        POST /v1/batches/{batch_id}/cancel
        """
        try:
            response = self.client.batches.cancel(batch_id)
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    async def acreate_batch(self, **kwargs) -> Dict[str, Any]:
        """
        Async: Create a batch.
        POST /v1/batches
        """
        try:
            response = await self.client.batches.create(**kwargs)
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    async def aretrieve_batch(self, batch_id: str) -> Dict[str, Any]:
        """
        Async: Retrieve a batch by ID.
        GET /v1/batches/{batch_id}
        """
        try:
            response = await openai.Batch.aretrieve(batch_id)
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    async def alist_batches(self) -> List[Dict[str, Any]]:
        """
        Async: List all batches.
        GET /v1/batches
        """
        try:
            response = await openai.Batch.alist()
            return response["data"]
        except Exception as e:
            self._handle_error(e)

    async def acancel_batch(self, batch_id: str) -> Dict[str, Any]:
        """
        Async: Cancel a batch.
        POST /v1/batches/{batch_id}/cancel
        """
        try:
            response = await openai.Batch.acancel(batch_id)
            return dict(response)
        except Exception as e:
            self._handle_error(e)
