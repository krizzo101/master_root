"""Celery application configuration for the software factory."""

import logging
import os
from typing import Any

from celery import Celery
from celery.schedules import crontab

logger = logging.getLogger(__name__)

# Celery configuration
CELERY_CONFIG = {
    "broker_url": os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    "result_backend": os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    "task_serializer": "json",
    "accept_content": ["json"],
    "result_serializer": "json",
    "timezone": "UTC",
    "enable_utc": True,
    "task_track_started": True,
    "task_time_limit": 3600,  # 1 hour
    "task_soft_time_limit": 3300,  # 55 minutes
    "worker_prefetch_multiplier": 1,
    "worker_max_tasks_per_child": 1000,
    "worker_disable_rate_limits": False,
    "task_acks_late": True,
    "worker_send_task_events": True,
    "task_send_sent_event": True,
    "result_expires": 86400,  # 24 hours
    "broker_connection_retry_on_startup": True,
}

# Create Celery app
celery_app = Celery("software_factory")

# Configure Celery
celery_app.conf.update(CELERY_CONFIG)

# Define task routes for different queues
celery_app.conf.task_routes = {
    "src.workers.tasks.execute_plan_task": {"queue": "default"},
    "src.workers.tasks.execute_spec_task": {"queue": "default"},
    "src.workers.tasks.execute_research_task": {"queue": "io"},
    "src.workers.tasks.execute_code_task": {"queue": "heavy"},
    "src.workers.tasks.execute_test_task": {"queue": "test"},
    "src.workers.tasks.execute_validate_task": {"queue": "test"},
    "src.workers.tasks.execute_document_task": {"queue": "io"},
    "src.workers.tasks.execute_critic_task": {"queue": "test"},
}

# Configure queues
celery_app.conf.task_default_queue = "default"
celery_app.conf.task_default_exchange = "software_factory"
celery_app.conf.task_default_routing_key = "default"

celery_app.conf.task_queues = {
    "default": {
        "exchange": "software_factory",
        "routing_key": "default",
    },
    "io": {
        "exchange": "software_factory",
        "routing_key": "io",
        "queue_arguments": {"x-max-priority": 10},
    },
    "heavy": {
        "exchange": "software_factory",
        "routing_key": "heavy",
        "queue_arguments": {"x-max-priority": 10},
    },
    "test": {
        "exchange": "software_factory",
        "routing_key": "test",
        "queue_arguments": {"x-max-priority": 10},
    },
}

# Configure task execution
celery_app.conf.task_annotations = {
    "*": {
        "rate_limit": "10/m",  # 10 tasks per minute
    },
    "src.workers.tasks.execute_research_task": {
        "rate_limit": "5/m",  # 5 research tasks per minute
    },
    "src.workers.tasks.execute_code_task": {
        "rate_limit": "3/m",  # 3 code generation tasks per minute
    },
    "src.workers.tasks.execute_critic_task": {
        "rate_limit": "20/m",  # 20 critic tasks per minute
    },
}

# Configure retry policies
celery_app.conf.task_annotations.update(
    {
        "src.workers.tasks.execute_plan_task": {
            "autoretry_for": (Exception,),
            "retry_kwargs": {"max_retries": 3},
            "retry_backoff": True,
            "retry_backoff_max": 600,  # 10 minutes
        },
        "src.workers.tasks.execute_spec_task": {
            "autoretry_for": (Exception,),
            "retry_kwargs": {"max_retries": 3},
            "retry_backoff": True,
            "retry_backoff_max": 600,
        },
        "src.workers.tasks.execute_code_task": {
            "autoretry_for": (Exception,),
            "retry_kwargs": {"max_retries": 2},
            "retry_backoff": True,
            "retry_backoff_max": 1200,  # 20 minutes
        },
        "src.workers.tasks.execute_test_task": {
            "autoretry_for": (Exception,),
            "retry_kwargs": {"max_retries": 2},
            "retry_backoff": True,
            "retry_backoff_max": 300,  # 5 minutes
        },
    }
)

# Configure periodic tasks (if needed)
celery_app.conf.beat_schedule = {
    "cleanup-old-results": {
        "task": "src.workers.tasks.cleanup_old_results",
        "schedule": crontab(hour=2, minute=0),  # Daily at 2 AM
    },
    "health-check": {
        "task": "src.workers.tasks.health_check",
        "schedule": 300.0,  # Every 5 minutes
    },
}

# Import tasks to register them
celery_app.autodiscover_tasks(["src.workers"])


@celery_app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery setup."""
    logger.info(f"Request: {self.request!r}")
    return "Debug task completed"


@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Setup periodic tasks after Celery configuration."""
    logger.info("Celery periodic tasks configured")


@celery_app.on_after_finalize.connect
def setup_worker_events(sender, **kwargs):
    """Setup worker events after Celery finalization."""
    logger.info("Celery worker events configured")


def get_celery_app() -> Celery:
    """Get the configured Celery application."""
    return celery_app


def get_queue_stats() -> dict[str, Any]:
    """Get queue statistics."""
    try:
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        active_tasks = inspect.active()
        reserved_tasks = inspect.reserved()

        return {
            "stats": stats,
            "active_tasks": active_tasks,
            "reserved_tasks": reserved_tasks,
        }
    except Exception as e:
        logger.error(f"Failed to get queue stats: {e}")
        return {}


def purge_queue(queue_name: str) -> bool:
    """Purge a specific queue."""
    try:
        celery_app.control.purge()
        logger.info(f"Purged queue: {queue_name}")
        return True
    except Exception as e:
        logger.error(f"Failed to purge queue {queue_name}: {e}")
        return False


def get_worker_status() -> dict[str, Any]:
    """Get worker status information."""
    try:
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        active = inspect.active()
        registered = inspect.registered()

        return {
            "workers": list(stats.keys()) if stats else [],
            "active_tasks": active,
            "registered_tasks": registered,
        }
    except Exception as e:
        logger.error(f"Failed to get worker status: {e}")
        return {"workers": [], "active_tasks": {}, "registered_tasks": {}}
