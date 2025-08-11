from typing import Any, Dict, List

from shared.openai_interfaces.base import OpenAIBaseInterface


class OpenAIFineTuningInterface(OpenAIBaseInterface):
    """
    Interface for OpenAI Fine-tuning API.
    Reference: https://platform.openai.com/docs/api-reference/fine-tuning

    This interface provides both synchronous and asynchronous methods for all fine-tuning endpoints.
    All methods are standards-compliant and mapped to the official OpenAI Python SDK.
    """

    def create_job(self, training_file: str, **kwargs) -> Dict[str, Any]:
        """
        Create a fine-tuning job.
        POST /v1/fine_tuning/jobs
        """
        try:
            response = self.client.fine_tuning.jobs.create(
                training_file=training_file, **kwargs
            )
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    def list_jobs(self) -> List[Dict[str, Any]]:
        """
        List all fine-tuning jobs.
        GET /v1/fine_tuning/jobs
        """
        try:
            response = self.client.fine_tuning.jobs.list()
            return response["data"]
        except Exception as e:
            self._handle_error(e)

    def retrieve_job(self, job_id: str) -> Dict[str, Any]:
        """
        Retrieve a fine-tuning job by ID.
        GET /v1/fine_tuning/jobs/{fine_tuning_job_id}
        """
        try:
            response = self.client.fine_tuning.jobs.retrieve(job_id)
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    def list_events(self, job_id: str) -> List[Dict[str, Any]]:
        """
        List events for a fine-tuning job.
        GET /v1/fine_tuning/jobs/{fine_tuning_job_id}/events
        """
        try:
            response = self.client.fine_tuning.jobs.list_events(job_id)
            return response["data"]
        except Exception as e:
            self._handle_error(e)

    def cancel_job(self, job_id: str) -> Dict[str, Any]:
        """
        Cancel a fine-tuning job.
        POST /v1/fine_tuning/jobs/{fine_tuning_job_id}/cancel
        """
        try:
            response = self.client.fine_tuning.jobs.cancel(job_id)
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    def list_fine_tuned_models(self) -> List[Dict[str, Any]]:
        """
        List all fine-tuned models.
        GET /v1/models (filtered for fine-tuned models)
        """
        try:
            models = self.client.models.list()
            return [m for m in models["data"] if m.get("fine_tuned")]
        except Exception as e:
            self._handle_error(e)

    async def acreate_job(self, training_file: str, **kwargs) -> Dict[str, Any]:
        """
        Async: Create a fine-tuning job.
        POST /v1/fine_tuning/jobs
        """
        try:
            response = await self.client.fine_tuning.jobs.create(
                training_file=training_file, **kwargs
            )
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    async def alist_jobs(self) -> List[Dict[str, Any]]:
        """
        Async: List all fine-tuning jobs.
        GET /v1/fine_tuning/jobs
        """
        try:
            response = await self.client.fine_tuning.jobs.list()
            return response["data"]
        except Exception as e:
            self._handle_error(e)

    async def aretrieve_job(self, job_id: str) -> Dict[str, Any]:
        """
        Async: Retrieve a fine-tuning job by ID.
        GET /v1/fine_tuning/jobs/{fine_tuning_job_id}
        """
        try:
            response = await self.client.fine_tuning.jobs.retrieve(job_id)
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    async def alist_events(self, job_id: str) -> List[Dict[str, Any]]:
        """
        Async: List events for a fine-tuning job.
        GET /v1/fine_tuning/jobs/{fine_tuning_job_id}/events
        """
        try:
            response = await self.client.fine_tuning.jobs.list_events(job_id)
            return response["data"]
        except Exception as e:
            self._handle_error(e)

    async def acancel_job(self, job_id: str) -> Dict[str, Any]:
        """
        Async: Cancel a fine-tuning job.
        POST /v1/fine_tuning/jobs/{fine_tuning_job_id}/cancel
        """
        try:
            response = await self.client.fine_tuning.jobs.cancel(job_id)
            return dict(response)
        except Exception as e:
            self._handle_error(e)

    async def alist_fine_tuned_models(self) -> List[Dict[str, Any]]:
        """
        Async: List all fine-tuned models.
        GET /v1/models (filtered for fine-tuned models)
        """
        try:
            models = await self.client.models.alist()
            return [m for m in models["data"] if m.get("fine_tuned")]
        except Exception as e:
            self._handle_error(e)
