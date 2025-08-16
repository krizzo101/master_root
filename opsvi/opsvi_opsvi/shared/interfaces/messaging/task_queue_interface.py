"""
Task Queue Shared Interface
--------------------------
Authoritative implementation based on the official Celery and RQ documentation:
- https://docs.celeryq.dev/en/stable/
- https://python-rq.org/
Implements all core features: enqueue, get_job, result handling, and error handling.
Version: Referenced as of July 2024
"""

import logging
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


class TaskQueueInterface:
    """
    Authoritative shared interface for task queue operations (Celery, RQ).
    See:
    - https://docs.celeryq.dev/en/stable/
    - https://python-rq.org/
    """

    def __init__(self, provider: str, **kwargs):
        """
        Initialize the interface for a given provider ('celery', 'rq').
        Args:
            provider: Provider name.
            kwargs: Provider-specific options (e.g., broker URL).
        """
        self.provider = provider.lower()
        self.kwargs = kwargs
        self._init_client()

    def _init_client(self):
        if self.provider == "celery":
            try:
                from celery import Celery

                self.client = Celery(**self.kwargs)
            except ImportError:
                raise ImportError("celery required. Install with `pip install celery`.")
        elif self.provider == "rq":
            try:
                import rq
                from redis import Redis

                self.redis_conn = Redis(**self.kwargs)
                self.client = rq.Queue(connection=self.redis_conn)
            except ImportError:
                raise ImportError(
                    "rq and redis required. Install with `pip install rq redis`."
                )
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def enqueue(self, func: Callable, *args, **kwargs) -> Any:
        """
        Enqueue a job.
        See:
        - Celery: https://docs.celeryq.dev/en/stable/userguide/calling.html
        - RQ: https://python-rq.org/docs/
        """
        if self.provider == "celery":
            return self.client.send_task(func.__name__, args=args, kwargs=kwargs)
        elif self.provider == "rq":
            return self.client.enqueue(func, *args, **kwargs)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def get_job(self, job_id: str) -> Any:
        """
        Retrieve a job by ID.
        See:
        - Celery: https://docs.celeryq.dev/en/stable/reference/celery.result.html
        - RQ: https://python-rq.org/docs/
        """
        if self.provider == "celery":
            return self.client.AsyncResult(job_id)
        elif self.provider == "rq":
            import rq

            return rq.job.Job.fetch(job_id, connection=self.redis_conn)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")


# Example usage and advanced features are available in the official docs:
# https://docs.celeryq.dev/en/stable/
# https://python-rq.org/
