#!/usr/bin/env python3
"""
Real-time chat log ingestion pipeline with buffering and batch processing.
Handles parsing, correlation, and database persistence.
"""

import asyncio
import json
import logging
import sys
import time
from collections import deque
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Deque, Dict, List, Optional

# Add project root to path for imports
sys.path.insert(0, "/home/opsvi/master_root")

from opsvi_monitoring.chat_analytics.intelligence.correlator import (
    ProjectIntelligenceCorrelator,
)
from opsvi_monitoring.chat_analytics.intelligence.dual_write_adapter import (
    DualWriteAdapter,
)

logger = logging.getLogger(__name__)


@dataclass
class ChatLogEntry:
    """Represents a parsed chat log entry."""

    session_id: str
    message_id: str
    timestamp: str
    node_type: str  # 'user' or 'assistant'
    content: str
    tool_calls: List[Dict] = None
    file_path: str = None  # Source file path

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class IngestionBatch:
    """Represents a batch of chat log entries for processing."""

    entries: List[ChatLogEntry]
    batch_id: str
    timestamp: str
    source_files: List[str]

    @property
    def size(self) -> int:
        return len(self.entries)


class ChatLogParser:
    """Parses JSONL chat log files into structured entries."""

    def __init__(self):
        self.processed_lines = {}  # Track processed lines per file

    def parse_jsonl_file(self, file_path: str) -> List[ChatLogEntry]:
        """Parse a JSONL file and return chat log entries."""
        entries = []
        file_key = str(file_path)
        last_processed_line = self.processed_lines.get(file_key, 0)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

                # Process only new lines
                new_lines = lines[last_processed_line:]

                for line_num, line in enumerate(
                    new_lines, start=last_processed_line + 1
                ):
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        data = json.loads(line)
                        entry = self._parse_entry(data, file_path)
                        if entry:
                            entries.append(entry)
                    except json.JSONDecodeError as e:
                        logger.warning(
                            f"Invalid JSON on line {line_num} in {file_path}: {e}"
                        )
                        continue

                # Update processed line count
                self.processed_lines[file_key] = len(lines)

        except (IOError, OSError) as e:
            logger.error(f"Could not read file {file_path}: {e}")

        return entries

    def _parse_entry(self, data: Dict, file_path: str) -> Optional[ChatLogEntry]:
        """Parse a single JSON entry into a ChatLogEntry."""
        try:
            # Handle different JSONL formats
            if "type" in data:
                # Summary entries don't contain chat messages
                if data["type"] == "summary":
                    return None

            # Look for message content in various formats
            content = ""
            node_type = "unknown"
            message_id = ""
            session_id = Path(file_path).stem  # Use filename as session ID
            timestamp = datetime.now().isoformat()
            tool_calls = []

            # Try to extract standard chat message fields
            if "content" in data:
                content = str(data["content"])
            elif "message" in data:
                content = str(data["message"])
            elif "text" in data:
                content = str(data["text"])

            # Extract node type
            if "role" in data:
                node_type = data["role"]
            elif "type" in data:
                node_type = data["type"]
            elif "sender" in data:
                node_type = data["sender"]

            # Extract IDs and timestamps
            if "id" in data:
                message_id = str(data["id"])
            elif "uuid" in data:
                message_id = str(data["uuid"])
            elif "leafUuid" in data:
                message_id = str(data["leafUuid"])

            if "timestamp" in data:
                timestamp = str(data["timestamp"])
            elif "created_at" in data:
                timestamp = str(data["created_at"])

            # Extract tool calls
            if "tool_calls" in data:
                tool_calls = data["tool_calls"]
            elif "tools_used" in data:
                tool_calls = data["tools_used"]

            # Only create entry if we have meaningful content
            if content.strip() or tool_calls:
                return ChatLogEntry(
                    session_id=session_id,
                    message_id=message_id or f"{session_id}_{int(time.time())}",
                    timestamp=timestamp,
                    node_type=node_type,
                    content=content,
                    tool_calls=tool_calls,
                    file_path=file_path,
                )

        except Exception as e:
            logger.warning(f"Could not parse entry from {file_path}: {e}")

        return None


class IngestionBuffer:
    """Buffers chat log entries for batch processing."""

    def __init__(self, max_size: int = 100, max_age_seconds: int = 30):
        self.max_size = max_size
        self.max_age_seconds = max_age_seconds
        self.buffer: Deque[ChatLogEntry] = deque()
        self.source_files: set = set()
        self.buffer_created_at = time.time()

    def add_entries(self, entries: List[ChatLogEntry], source_file: str):
        """Add entries to the buffer."""
        self.buffer.extend(entries)
        self.source_files.add(source_file)

        # Reset buffer age if this is the first entry
        if len(self.buffer) == len(entries):
            self.buffer_created_at = time.time()

    def should_flush(self) -> bool:
        """Check if buffer should be flushed."""
        if not self.buffer:
            return False

        # Flush if buffer is full
        if len(self.buffer) >= self.max_size:
            return True

        # Flush if buffer is old
        age = time.time() - self.buffer_created_at
        if age >= self.max_age_seconds:
            return True

        return False

    def flush(self) -> Optional[IngestionBatch]:
        """Flush buffer and return batch."""
        if not self.buffer:
            return None

        batch = IngestionBatch(
            entries=list(self.buffer),
            batch_id=f"batch_{int(time.time())}_{len(self.buffer)}",
            timestamp=datetime.now().isoformat(),
            source_files=list(self.source_files),
        )

        # Clear buffer
        self.buffer.clear()
        self.source_files.clear()
        self.buffer_created_at = time.time()

        return batch

    @property
    def size(self) -> int:
        return len(self.buffer)

    @property
    def age_seconds(self) -> float:
        return time.time() - self.buffer_created_at


class RealTimeIngestionPipeline:
    """Main real-time ingestion pipeline."""

    def __init__(
        self,
        correlator: Optional[ProjectIntelligenceCorrelator] = None,
        db_adapter: Optional[DualWriteAdapter] = None,
    ):
        self.parser = ChatLogParser()
        self.buffer = IngestionBuffer()

        # Initialize correlator and database adapter
        self.correlator = correlator or ProjectIntelligenceCorrelator()
        self.db_adapter = db_adapter or DualWriteAdapter()

        # Processing statistics
        self.stats = {
            "files_processed": 0,
            "entries_processed": 0,
            "batches_processed": 0,
            "correlation_time_ms": 0,
            "db_write_time_ms": 0,
            "start_time": time.time(),
        }

        # Processing queue
        self.processing_queue = asyncio.Queue(maxsize=1000)
        self.running = False

    async def start(self):
        """Start the ingestion pipeline."""
        logger.info("Starting real-time ingestion pipeline")
        self.running = True

        # Start background tasks
        await asyncio.gather(self._process_files(), self._flush_buffer_periodically())

    async def stop(self):
        """Stop the ingestion pipeline."""
        logger.info("Stopping real-time ingestion pipeline")
        self.running = False

        # Flush any remaining entries
        await self._flush_buffer()

        # Close connections
        if self.correlator:
            self.correlator.close()
        if self.db_adapter:
            self.db_adapter.close()

    async def process_file(self, file_info: Dict):
        """Process a single file for ingestion."""
        file_path = file_info["path"]

        try:
            start_time = time.time()

            # Parse the file
            entries = self.parser.parse_jsonl_file(file_path)

            if not entries:
                logger.debug(f"No new entries found in {file_path}")
                return

            logger.info(f"Parsed {len(entries)} entries from {file_path}")

            # Add to buffer
            self.buffer.add_entries(entries, file_path)

            # Flush if needed
            if self.buffer.should_flush():
                await self._flush_buffer()

            # Update statistics
            self.stats["files_processed"] += 1
            self.stats["entries_processed"] += len(entries)

            processing_time = (time.time() - start_time) * 1000
            logger.debug(f"Processed file {file_path} in {processing_time:.2f}ms")

        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")

    async def _process_files(self):
        """Background task to process files from the queue."""
        while self.running:
            try:
                # Wait for file with timeout
                file_info = await asyncio.wait_for(
                    self.processing_queue.get(), timeout=1.0
                )

                await self.process_file(file_info)
                self.processing_queue.task_done()

            except asyncio.TimeoutError:
                # Check if buffer should be flushed during idle time
                if self.buffer.should_flush():
                    await self._flush_buffer()
                continue
            except Exception as e:
                logger.error(f"Error in file processing loop: {e}")
                await asyncio.sleep(1)

    async def _flush_buffer_periodically(self):
        """Background task to flush buffer periodically."""
        while self.running:
            await asyncio.sleep(10)  # Check every 10 seconds

            if self.buffer.should_flush():
                await self._flush_buffer()

    async def _flush_buffer(self):
        """Flush the current buffer."""
        batch = self.buffer.flush()
        if not batch:
            return

        logger.info(f"Processing batch {batch.batch_id} with {batch.size} entries")

        try:
            await self._process_batch(batch)
            self.stats["batches_processed"] += 1

        except Exception as e:
            logger.error(f"Error processing batch {batch.batch_id}: {e}")

    async def _process_batch(self, batch: IngestionBatch):
        """Process a batch of entries."""
        correlation_start = time.time()

        # Process each entry through correlator
        for entry in batch.entries:
            try:
                # Convert to message format expected by correlator
                message = {
                    "id": entry.message_id,
                    "content": entry.content,
                    "timestamp": entry.timestamp,
                    "tool_calls": entry.tool_calls or [],
                }

                # Run correlation
                context = self.correlator.process_message(message, entry.session_id)

                # Store additional context
                await self._store_context(entry, context)

            except Exception as e:
                logger.error(f"Error correlating entry {entry.message_id}: {e}")

        correlation_time = (time.time() - correlation_start) * 1000
        self.stats["correlation_time_ms"] += correlation_time

        logger.debug(f"Batch {batch.batch_id} processed in {correlation_time:.2f}ms")

    async def _store_context(self, entry: ChatLogEntry, context: Dict):
        """Store additional context for an entry."""
        try:
            # Store entry metadata
            await self._store_entry_metadata(entry)

            # Context is already stored by correlator, but we could add additional
            # real-time specific metadata here

        except Exception as e:
            logger.error(f"Error storing context for entry {entry.message_id}: {e}")

    async def _store_entry_metadata(self, entry: ChatLogEntry):
        """Store entry metadata for real-time tracking."""
        try:
            # Use dual-write adapter to store entry metadata
            # This could include real-time processing timestamps, source file info, etc.
            pass
        except Exception as e:
            logger.error(f"Error storing entry metadata: {e}")

    def get_stats(self) -> Dict:
        """Get processing statistics."""
        uptime = time.time() - self.stats["start_time"]

        return {
            **self.stats,
            "uptime_seconds": uptime,
            "files_per_minute": (self.stats["files_processed"] / uptime) * 60
            if uptime > 0
            else 0,
            "entries_per_minute": (self.stats["entries_processed"] / uptime) * 60
            if uptime > 0
            else 0,
            "buffer_size": self.buffer.size,
            "buffer_age_seconds": self.buffer.age_seconds,
            "queue_size": self.processing_queue.qsize(),
        }


class IngestionCoordinator:
    """Coordinates the entire real-time ingestion system."""

    def __init__(self):
        self.pipeline = RealTimeIngestionPipeline()
        self.file_queue = asyncio.Queue(maxsize=1000)
        self.running = False

    async def start(self):
        """Start the ingestion coordinator."""
        logger.info("Starting ingestion coordinator")
        self.running = True

        # Start pipeline
        pipeline_task = asyncio.create_task(self.pipeline.start())

        # Start file queue processor
        queue_task = asyncio.create_task(self._process_file_queue())

        await asyncio.gather(pipeline_task, queue_task)

    async def stop(self):
        """Stop the ingestion coordinator."""
        logger.info("Stopping ingestion coordinator")
        self.running = False
        await self.pipeline.stop()

    async def queue_file(self, file_info: Dict):
        """Queue a file for processing."""
        await self.file_queue.put(file_info)

    async def _process_file_queue(self):
        """Process files from the queue."""
        while self.running:
            try:
                file_info = await asyncio.wait_for(self.file_queue.get(), timeout=1.0)

                await self.pipeline.process_file(file_info)
                self.file_queue.task_done()

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in file queue processing: {e}")
                await asyncio.sleep(1)

    def get_status(self) -> Dict:
        """Get coordinator status."""
        return {
            "running": self.running,
            "pipeline_stats": self.pipeline.get_stats(),
            "file_queue_size": self.file_queue.qsize(),
        }
