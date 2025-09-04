"""Adapter implementations for different data sources."""

from .chat_adapter import ChatAdapter
from .code_adapter import CodeAdapter
from .error_adapter import ErrorAdapter
from .git_adapter import GitAdapter

__all__ = [
    "ChatAdapter",
    "CodeAdapter",
    "GitAdapter",
    "ErrorAdapter",
]
