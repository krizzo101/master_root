"""
Gemini Agent MCP Server

Provides integration with Google's Gemini CLI for AI-powered coding assistance.
"""

from .server import GeminiAgentServer
from .config import GeminiConfig
from .models import GeminiRequest, GeminiResponse, GeminiMode, GeminiCapabilities

__all__ = [
    "GeminiAgentServer",
    "GeminiConfig",
    "GeminiRequest",
    "GeminiResponse",
    "GeminiMode",
    "GeminiCapabilities",
]

__version__ = "1.0.0"
