"""Persistence backends for opsvi-core.

Provides pluggable persistence backends for state management.
"""

from .base import PersistenceBackend, PersistenceError
from .json_backend import JSONBackend
from .memory_backend import MemoryBackend
from .redis_backend import RedisBackend

__all__ = [
    "PersistenceBackend",
    "PersistenceError",
    "JSONBackend",
    "MemoryBackend",
    "RedisBackend",
]
