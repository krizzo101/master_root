"""Claude Code Clone - Multi-Provider AI Coding Assistant.

A powerful AI coding assistant that supports multiple LLM providers
and provides Claude Code-like functionality with headless execution.
"""

__version__ = "0.1.0"
__author__ = "OPSVI Team"
__email__ = "team@opsvi.com"

# Core exports
from .core.executor import ClaudeCodeExecutor
from .core.analyzer import CodeAnalyzer
from .core.streaming import StreamingHandler
from .providers.llm_adapter import LLMAdapter
from .config import ClaudeCodeConfig

__all__ = [
    "ClaudeCodeExecutor",
    "CodeAnalyzer",
    "StreamingHandler",
    "LLMAdapter",
    "ClaudeCodeConfig",
]
