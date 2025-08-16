"""WebSocket router for real-time progress updates via Redis PubSub."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi_websocket_pubsub import PubSubEndpoint

from config import config

logger = logging.getLogger(__name__)

# Create WebSocket router
ws_router = APIRouter()

# Initialize PubSub endpoint with Redis backend
pubsub_endpoint = PubSubEndpoint(broadcaster=config.redis_url)


@ws_router.websocket("/ws/{job_id}")
async def websocket_progress(websocket: WebSocket, job_id: str) -> None:
    """WebSocket endpoint for real-time job progress updates."""
    await websocket.accept()
    logger.info("WebSocket connection established for job %s", job_id)

    try:
        import redis.asyncio as redis_async

        # Subscribe to job-specific progress topic using direct Redis
        progress_topic = f"job_progress_{job_id}"

        try:
            # Create Redis connection for pub/sub
            r = redis_async.from_url(config.redis_url)
            pubsub = r.pubsub()
            await pubsub.subscribe(progress_topic)

            logger.info(
                "Subscribed to Redis topic %s for job %s", progress_topic, job_id
            )

            # Keep connection alive and handle incoming messages
            last_activity = asyncio.get_event_loop().time()
            heartbeat_interval = 30  # Send heartbeat every 30 seconds

            while True:
                try:
                    # Check for Redis messages with shorter timeout for responsiveness
                    message = await pubsub.get_message(
                        timeout=0.5, ignore_subscribe_messages=True
                    )
                    if message and message["type"] == "message":
                        # Forward Redis message to WebSocket
                        data = message["data"].decode("utf-8")
                        await websocket.send_text(data)
                        logger.debug("Forwarded progress update to WebSocket: %s", data)
                        last_activity = asyncio.get_event_loop().time()

                    # Check for WebSocket messages (heartbeat)
                    try:
                        ws_message = await asyncio.wait_for(
                            websocket.receive_text(), timeout=0.1
                        )
                        if ws_message == "ping":
                            await websocket.send_text("pong")
                            last_activity = asyncio.get_event_loop().time()
                    except asyncio.TimeoutError:
                        pass  # No WebSocket message, continue

                    # Send periodic heartbeat to detect disconnections
                    current_time = asyncio.get_event_loop().time()
                    if current_time - last_activity > heartbeat_interval:
                        try:
                            await websocket.send_text(
                                json.dumps(
                                    {
                                        "type": "heartbeat",
                                        "timestamp": current_time,
                                        "job_id": job_id,
                                    }
                                )
                            )
                            last_activity = current_time
                        except Exception as e:
                            logger.warning("Failed to send heartbeat: %s", e)
                            break

                except asyncio.TimeoutError:
                    # No Redis message, continue listening
                    continue
                except WebSocketDisconnect:
                    logger.info("WebSocket disconnected for job %s", job_id)
                    break

        except redis_async.ConnectionError as e:
            logger.error("Redis connection failed for WebSocket: %s", e)
            await websocket.send_text(
                json.dumps(
                    {
                        "status": "error",
                        "message": "Real-time updates unavailable. Please refresh page for status.",
                    }
                )
            )

        except Exception as e:
            logger.error("Redis pub/sub error: %s", e)
            await websocket.send_text(
                json.dumps(
                    {
                        "status": "error",
                        "message": "Connection error. Please refresh page.",
                    }
                )
            )

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected for job %s", job_id)
    except Exception as e:
        logger.error("WebSocket error for job %s: %s", job_id, e)
    finally:
        # Cleanup Redis subscription
        try:
            await pubsub.unsubscribe(progress_topic)
            await r.close()
        except Exception as e:
            logger.error("Failed to cleanup Redis subscription: %s", e)


@ws_router.websocket("/pubsub")
async def websocket_pubsub_endpoint(websocket: WebSocket) -> None:
    """General PubSub WebSocket endpoint for the fastapi-websocket-pubsub library."""
    await pubsub_endpoint.main_loop(websocket)


def publish_progress_update(job_id: str, data: dict[str, Any]) -> None:
    """Publish a progress update for a specific job."""
    try:
        import json

        import redis

        # Direct Redis pub/sub for more reliable progress updates
        progress_topic = f"job_progress_{job_id}"

        # Parse Redis URL from config
        redis_url = config.redis_url
        try:
            r = redis.from_url(redis_url)
            # Publish directly to Redis
            message = json.dumps(data)
            r.publish(progress_topic, message)
            logger.debug("Published progress update for job %s: %s", job_id, data)
        except redis.ConnectionError as e:
            logger.warning("Redis not available for progress updates: %s", e)
            # Fall back to in-memory storage for UI polling
            _store_progress_fallback(job_id, data)
        except Exception as e:
            logger.error("Failed to publish to Redis: %s", e)
            _store_progress_fallback(job_id, data)

    except Exception as e:
        logger.error("Failed to publish progress update for job %s: %s", job_id, e)


# Fallback progress storage for when Redis is not available
_progress_cache = {}


def _store_progress_fallback(job_id: str, data: dict[str, Any]) -> None:
    """Store progress update in memory as fallback."""
    _progress_cache[job_id] = data
    logger.debug("Stored progress fallback for job %s: %s", job_id, data)


def get_progress_fallback(job_id: str) -> dict[str, Any] | None:
    """Get progress from fallback storage."""
    return _progress_cache.get(job_id)
