import pytest
from backend.websocket_manager import WebSocketManager
from unittest.mock import MagicMock


def test_websocket_manager_initialization():
    manager = WebSocketManager()
    assert hasattr(manager, "active_connections")
    assert isinstance(manager.active_connections, set)
    assert len(manager.active_connections) == 0


def test_websocket_manager_disconnect_removes_websocket():
    manager = WebSocketManager()
    websocket = MagicMock()
    manager.active_connections.add(websocket)
    manager.disconnect(websocket)
    assert websocket not in manager.active_connections
