"""
WebSocket real-time collaboration handler based on Y.js/CRDT simulation (mock for demo).
Implements: doc state broadcast, user presence, basic sync.
"""
import logging
from typing import Any

from fastapi import WebSocket

from .models import User

# Simple in-memory room and state:
_DOC_ROOMS: dict[str, set[WebSocket]] = {}
_DOC_STATE: dict[str, str] = {}  # doc_id -> text


async def join_collab_room(doc_id: str, socket: WebSocket, user: User) -> None:
    await socket.accept()
    _DOC_ROOMS.setdefault(doc_id, set()).add(socket)
    if doc_id not in _DOC_STATE:
        _DOC_STATE[doc_id] = ""  # Initial blank
    # Send current state
    await socket.send_json({"type": "init", "body": _DOC_STATE[doc_id]})
    try:
        while True:
            data = await socket.receive_json()
            # Simulate OT/CRDT by taking overwrite as final (for demo only)
            msg_type = data.get("type")
            if msg_type == "edit":
                new_body = data.get("body", "")
                _DOC_STATE[doc_id] = new_body
                # Broadcast to all except sender
                await _broadcast(
                    doc_id, {"type": "update", "body": new_body}, exclude=socket
                )
            elif msg_type == "ping":
                await socket.send_json({"type": "pong"})
    except Exception as e:
        # Disconnection or handler error
        logging.info(f"WebSocket disconnect from doc {doc_id}: {repr(e)}")
    finally:
        _DOC_ROOMS[doc_id].discard(socket)
        await _broadcast(doc_id, {"type": "user_leave", "user": user.username})
        await socket.close()


def get_active_users(doc_id: str) -> int:
    return len(_DOC_ROOMS.get(doc_id, []))


async def _broadcast(doc_id: str, msg: Any, exclude: WebSocket = None):
    to_send = [s for s in _DOC_ROOMS.get(doc_id, set()) if s != exclude]
    for ws in to_send:
        try:
            await ws.send_json(msg)
        except Exception:
            pass  # Socket likely closed
