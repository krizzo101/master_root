"""Streaming handler for Claude Code Clone."""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, AsyncGenerator, Union
from pathlib import Path

from opsvi_foundation import BaseComponent, ComponentError
from ..config import ClaudeCodeConfig

logger = logging.getLogger(__name__)


class StreamingHandlerError(ComponentError):
    """Error in streaming handler operations."""

    pass


class StreamingHandler(BaseComponent):
    """Handler for streaming responses and real-time updates."""

    def __init__(self, config: ClaudeCodeConfig):
        """Initialize the streaming handler."""
        super().__init__(name="StreamingHandler")
        self.config = config
        self.active_streams: Dict[str, asyncio.Task] = {}

        logger.info("Initialized streaming handler")

    async def _initialize_impl(self) -> None:
        """Initialize the streaming handler."""
        logger.info("Streaming handler initialized")

    async def _shutdown_impl(self) -> None:
        """Shutdown the streaming handler."""
        await self.close()
        logger.info("Streaming handler shutdown")

    async def _health_check_impl(self) -> bool:
        """Check if the streaming handler is healthy."""
        try:
            return True  # Streaming handler is always healthy
        except Exception as e:
            logger.error(f"Streaming handler health check failed: {e}")
            return False

    async def stream_response(
        self,
        stream_id: str,
        response_generator: AsyncGenerator[str, None],
        output_format: str = "text",
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream a response with metadata."""
        try:
            self.active_streams[stream_id] = asyncio.current_task()

            async for chunk in response_generator:
                if output_format == "json":
                    yield {
                        "stream_id": stream_id,
                        "type": "chunk",
                        "data": chunk,
                        "timestamp": asyncio.get_event_loop().time(),
                    }
                else:
                    yield {"stream_id": stream_id, "type": "chunk", "data": chunk}

            # Send completion signal
            yield {"stream_id": stream_id, "type": "complete", "data": None}

        except Exception as e:
            logger.error(f"Streaming error for {stream_id}: {e}")
            yield {"stream_id": stream_id, "type": "error", "data": str(e)}
        finally:
            self.active_streams.pop(stream_id, None)

    async def stream_file_analysis(
        self,
        file_path: str,
        analysis_type: str = "general",
        context: Optional[str] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream file analysis results."""
        stream_id = f"analysis_{Path(file_path).name}_{asyncio.get_event_loop().time()}"

        try:
            # Send start signal
            yield {
                "stream_id": stream_id,
                "type": "start",
                "data": f"Starting analysis of {file_path}",
            }

            # Simulate analysis progress (in real implementation, this would be actual analysis)
            analysis_steps = [
                "Reading file...",
                "Parsing syntax...",
                "Analyzing structure...",
                "Checking for issues...",
                "Generating report...",
            ]

            for step in analysis_steps:
                yield {"stream_id": stream_id, "type": "progress", "data": step}
                await asyncio.sleep(0.1)  # Simulate processing time

            # Send completion
            yield {
                "stream_id": stream_id,
                "type": "complete",
                "data": f"Analysis of {file_path} completed",
            }

        except Exception as e:
            logger.error(f"File analysis streaming error: {e}")
            yield {"stream_id": stream_id, "type": "error", "data": str(e)}

    async def stream_code_generation(
        self, prompt: str, language: str = "python", context: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream code generation process."""
        stream_id = f"generation_{language}_{asyncio.get_event_loop().time()}"

        try:
            # Send start signal
            yield {
                "stream_id": stream_id,
                "type": "start",
                "data": f"Starting {language} code generation",
            }

            # Simulate generation steps
            generation_steps = [
                "Analyzing requirements...",
                "Planning code structure...",
                "Generating code...",
                "Validating syntax...",
                "Optimizing code...",
            ]

            for step in generation_steps:
                yield {"stream_id": stream_id, "type": "progress", "data": step}
                await asyncio.sleep(0.2)  # Simulate processing time

            # Send completion
            yield {
                "stream_id": stream_id,
                "type": "complete",
                "data": f"{language} code generation completed",
            }

        except Exception as e:
            logger.error(f"Code generation streaming error: {e}")
            yield {"stream_id": stream_id, "type": "error", "data": str(e)}

    async def stream_project_analysis(
        self, project_path: str, analysis_types: List[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream project analysis results."""
        if analysis_types is None:
            analysis_types = ["structure", "complexity", "duplicates", "issues"]

        stream_id = f"project_analysis_{asyncio.get_event_loop().time()}"

        try:
            # Send start signal
            yield {
                "stream_id": stream_id,
                "type": "start",
                "data": f"Starting project analysis of {project_path}",
            }

            # Stream each analysis type
            for analysis_type in analysis_types:
                yield {
                    "stream_id": stream_id,
                    "type": "progress",
                    "data": f"Running {analysis_type} analysis...",
                }

                # Simulate analysis time
                await asyncio.sleep(0.5)

                yield {
                    "stream_id": stream_id,
                    "type": "result",
                    "data": {
                        "analysis_type": analysis_type,
                        "status": "completed",
                        "summary": f"{analysis_type} analysis completed",
                    },
                }

            # Send completion
            yield {
                "stream_id": stream_id,
                "type": "complete",
                "data": "Project analysis completed",
            }

        except Exception as e:
            logger.error(f"Project analysis streaming error: {e}")
            yield {"stream_id": stream_id, "type": "error", "data": str(e)}

    def get_active_streams(self) -> List[str]:
        """Get list of active stream IDs."""
        return list(self.active_streams.keys())

    async def cancel_stream(self, stream_id: str) -> bool:
        """Cancel an active stream."""
        if stream_id in self.active_streams:
            task = self.active_streams[stream_id]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            self.active_streams.pop(stream_id, None)
            logger.info(f"Cancelled stream {stream_id}")
            return True
        return False

    async def cancel_all_streams(self) -> int:
        """Cancel all active streams."""
        cancelled_count = 0
        for stream_id in list(self.active_streams.keys()):
            if await self.cancel_stream(stream_id):
                cancelled_count += 1
        logger.info(f"Cancelled {cancelled_count} streams")
        return cancelled_count

    async def close(self) -> None:
        """Close the streaming handler and cleanup resources."""
        await self.cancel_all_streams()
        logger.info("Streaming handler closed")
