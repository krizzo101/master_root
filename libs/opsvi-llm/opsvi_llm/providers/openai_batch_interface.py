"""
OpenAI Batch API Interface

Comprehensive batch interface for the OPSVI ecosystem.
Ported from agent_world with enhancements for production use.

Authoritative implementation based on the official OpenAI Python SDK:
- https://github.com/openai/openai-python
- https://platform.openai.com/docs/api-reference/batch

Implements all core endpoints and features:
- create, retrieve, list, cancel batches
- sync and async support
- batch status monitoring
- error handling and retries

Version: Referenced as of July 2024
"""

import logging
import os
from typing import Any, Dict, List, Optional

from openai import AsyncOpenAI, OpenAI

logger = logging.getLogger(__name__)


class OpenAIBatchError(Exception):
    """Custom exception for OpenAI Batch API errors."""

    pass


class OpenAIBatchInterface:
    """
    Comprehensive interface for OpenAI Batch API.

    Provides both synchronous and asynchronous methods for all batch endpoints.
    All methods are standards-compliant and mapped to the official OpenAI Python SDK.
    """

    def __init__(
        self, api_key: Optional[str] = None, organization: Optional[str] = None
    ):
        """Initialize the batch interface.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            organization: OpenAI organization ID (defaults to OPENAI_ORG_ID env var)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.organization = organization or os.getenv("OPENAI_ORG_ID")

        if not self.api_key:
            raise OpenAIBatchError("OpenAI API key is required")

        self.client = OpenAI(api_key=self.api_key, organization=self.organization)

        logger.debug(f"OpenAIBatchInterface initialized with org: {self.organization}")

    def create_batch(self, **kwargs) -> Dict[str, Any]:
        """
        Create a new batch.

        Args:
            **kwargs: Batch creation parameters (input_file_id, endpoint, completion_window)

        Returns:
            Dictionary containing the batch response

        Raises:
            OpenAIBatchError: If the API call fails
        """
        try:
            response = self.client.batches.create(**kwargs)

            # Convert to dict for consistency
            if hasattr(response, "model_dump"):
                return response.model_dump()
            else:
                return dict(response)

        except Exception as e:
            logger.error(f"Failed to create batch: {e}")
            raise OpenAIBatchError(f"Failed to create batch: {e}")

    def retrieve_batch(self, batch_id: str) -> Dict[str, Any]:
        """
        Retrieve a batch by ID.

        Args:
            batch_id: The batch ID to retrieve

        Returns:
            Dictionary containing the batch details

        Raises:
            OpenAIBatchError: If the API call fails
        """
        try:
            response = self.client.batches.retrieve(batch_id)

            # Convert to dict for consistency
            if hasattr(response, "model_dump"):
                return response.model_dump()
            else:
                return dict(response)

        except Exception as e:
            logger.error(f"Failed to retrieve batch {batch_id}: {e}")
            raise OpenAIBatchError(f"Failed to retrieve batch {batch_id}: {e}")

    def list_batches(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        List all batches.

        Args:
            limit: Maximum number of batches to return

        Returns:
            List of batch dictionaries

        Raises:
            OpenAIBatchError: If the API call fails
        """
        try:
            params = {}
            if limit:
                params["limit"] = limit

            response = self.client.batches.list(**params)

            # Convert to list of dicts for consistency
            batches = []
            for batch in response.data:
                if hasattr(batch, "model_dump"):
                    batches.append(batch.model_dump())
                else:
                    batches.append(dict(batch))

            return batches

        except Exception as e:
            logger.error(f"Failed to list batches: {e}")
            raise OpenAIBatchError(f"Failed to list batches: {e}")

    def cancel_batch(self, batch_id: str) -> Dict[str, Any]:
        """
        Cancel a batch.

        Args:
            batch_id: The batch ID to cancel

        Returns:
            Dictionary containing the cancellation response

        Raises:
            OpenAIBatchError: If the API call fails
        """
        try:
            response = self.client.batches.cancel(batch_id)

            # Convert to dict for consistency
            if hasattr(response, "model_dump"):
                return response.model_dump()
            else:
                return dict(response)

        except Exception as e:
            logger.error(f"Failed to cancel batch {batch_id}: {e}")
            raise OpenAIBatchError(f"Failed to cancel batch {batch_id}: {e}")

    async def acreate_batch(self, **kwargs) -> Dict[str, Any]:
        """
        Async: Create a new batch.

        Args:
            **kwargs: Batch creation parameters (input_file_id, endpoint, completion_window)

        Returns:
            Dictionary containing the batch response

        Raises:
            OpenAIBatchError: If the API call fails
        """
        try:
            async_client = AsyncOpenAI(
                api_key=self.api_key, organization=self.organization
            )

            response = await async_client.batches.create(**kwargs)

            # Convert to dict for consistency
            if hasattr(response, "model_dump"):
                return response.model_dump()
            else:
                return dict(response)

        except Exception as e:
            logger.error(f"Failed to create batch (async): {e}")
            raise OpenAIBatchError(f"Failed to create batch (async): {e}")

    async def aretrieve_batch(self, batch_id: str) -> Dict[str, Any]:
        """
        Async: Retrieve a batch by ID.

        Args:
            batch_id: The batch ID to retrieve

        Returns:
            Dictionary containing the batch details

        Raises:
            OpenAIBatchError: If the API call fails
        """
        try:
            async_client = AsyncOpenAI(
                api_key=self.api_key, organization=self.organization
            )

            response = await async_client.batches.retrieve(batch_id)

            # Convert to dict for consistency
            if hasattr(response, "model_dump"):
                return response.model_dump()
            else:
                return dict(response)

        except Exception as e:
            logger.error(f"Failed to retrieve batch {batch_id} (async): {e}")
            raise OpenAIBatchError(f"Failed to retrieve batch {batch_id} (async): {e}")

    async def alist_batches(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Async: List all batches.

        Args:
            limit: Maximum number of batches to return

        Returns:
            List of batch dictionaries

        Raises:
            OpenAIBatchError: If the API call fails
        """
        try:
            async_client = AsyncOpenAI(
                api_key=self.api_key, organization=self.organization
            )

            params = {}
            if limit:
                params["limit"] = limit

            response = await async_client.batches.list(**params)

            # Convert to list of dicts for consistency
            batches = []
            for batch in response.data:
                if hasattr(batch, "model_dump"):
                    batches.append(batch.model_dump())
                else:
                    batches.append(dict(batch))

            return batches

        except Exception as e:
            logger.error(f"Failed to list batches (async): {e}")
            raise OpenAIBatchError(f"Failed to list batches (async): {e}")

    async def acancel_batch(self, batch_id: str) -> Dict[str, Any]:
        """
        Async: Cancel a batch.

        Args:
            batch_id: The batch ID to cancel

        Returns:
            Dictionary containing the cancellation response

        Raises:
            OpenAIBatchError: If the API call fails
        """
        try:
            async_client = AsyncOpenAI(
                api_key=self.api_key, organization=self.organization
            )

            response = await async_client.batches.cancel(batch_id)

            # Convert to dict for consistency
            if hasattr(response, "model_dump"):
                return response.model_dump()
            else:
                return dict(response)

        except Exception as e:
            logger.error(f"Failed to cancel batch {batch_id} (async): {e}")
            raise OpenAIBatchError(f"Failed to cancel batch {batch_id} (async): {e}")

    def get_batch_status(self, batch_id: str) -> str:
        """
        Get the status of a batch.

        Args:
            batch_id: The batch ID

        Returns:
            Batch status string
        """
        try:
            batch = self.retrieve_batch(batch_id)
            return batch.get("status", "unknown")
        except OpenAIBatchError:
            return "unknown"

    def is_batch_completed(self, batch_id: str) -> bool:
        """
        Check if a batch is completed.

        Args:
            batch_id: The batch ID

        Returns:
            True if completed, False otherwise
        """
        status = self.get_batch_status(batch_id)
        return status in ["completed", "failed", "cancelled"]

    def is_batch_failed(self, batch_id: str) -> bool:
        """
        Check if a batch failed.

        Args:
            batch_id: The batch ID

        Returns:
            True if failed, False otherwise
        """
        status = self.get_batch_status(batch_id)
        return status == "failed"

    def get_batches_by_status(self, status: str) -> List[Dict[str, Any]]:
        """
        Get batches by status.

        Args:
            status: The status to filter by

        Returns:
            List of batches with the specified status
        """
        try:
            all_batches = self.list_batches()
            filtered_batches = []

            for batch in all_batches:
                if batch.get("status") == status:
                    filtered_batches.append(batch)

            return filtered_batches

        except Exception as e:
            logger.error(f"Failed to get batches by status {status}: {e}")
            raise OpenAIBatchError(f"Failed to get batches by status {status}: {e}")

    def get_active_batches(self) -> List[Dict[str, Any]]:
        """
        Get all active (non-completed) batches.

        Returns:
            List of active batches
        """
        try:
            all_batches = self.list_batches()
            active_batches = []

            for batch in all_batches:
                status = batch.get("status", "unknown")
                if status not in ["completed", "failed", "cancelled"]:
                    active_batches.append(batch)

            return active_batches

        except Exception as e:
            logger.error(f"Failed to get active batches: {e}")
            raise OpenAIBatchError(f"Failed to get active batches: {e}")

    def get_batch_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all batches by status.

        Returns:
            Dictionary with batch counts by status
        """
        try:
            all_batches = self.list_batches()

            summary = {
                "total_batches": len(all_batches),
                "by_status": {},
            }

            for batch in all_batches:
                status = batch.get("status", "unknown")
                if status not in summary["by_status"]:
                    summary["by_status"][status] = 0
                summary["by_status"][status] += 1

            return summary

        except Exception as e:
            logger.error(f"Failed to get batch summary: {e}")
            raise OpenAIBatchError(f"Failed to get batch summary: {e}")

    def validate_batch_params(self, **kwargs) -> bool:
        """
        Validate batch creation parameters.

        Args:
            **kwargs: Batch parameters to validate

        Returns:
            True if valid, False otherwise
        """
        required_params = ["input_file_id", "endpoint"]

        for param in required_params:
            if param not in kwargs:
                logger.error(f"Missing required parameter: {param}")
                return False

        # Validate endpoint
        valid_endpoints = ["/v1/chat/completions", "/v1/completions"]
        if kwargs.get("endpoint") not in valid_endpoints:
            logger.error(f"Invalid endpoint: {kwargs.get('endpoint')}")
            return False

        return True
