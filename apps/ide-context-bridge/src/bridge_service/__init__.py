"""
IDE Context Bridge Service

A service that bridges IDE context with the unified context system for intelligent code assistance.
"""

__version__ = "1.0.0"
__author__ = "OPSVI Team"

# Import modules individually to avoid dependency issues during testing
# from .server import BridgeServer
# from .context_manager import ContextManager
# from .suggestion_engine import SuggestionEngine
# from .websocket_handler import WebSocketHandler

__all__ = ["BridgeServer", "ContextManager", "SuggestionEngine", "WebSocketHandler"]
