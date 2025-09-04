#!/usr/bin/env python3
"""
Real-time chat log file watcher service for Claude chat logs.
Monitors multiple source directories and triggers immediate ingestion.
"""

import asyncio
import hashlib
import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

from watchdog.events import FileCreatedEvent, FileModifiedEvent, FileSystemEventHandler
from watchdog.observers import Observer

logger = logging.getLogger(__name__)


class ChatLogFileHandler(FileSystemEventHandler):
    """Handles file system events for chat log files."""

    def __init__(self, ingestion_queue: asyncio.Queue, processed_files: Set[str]):
        self.ingestion_queue = ingestion_queue
        self.processed_files = processed_files
        self.file_hashes = {}  # Track file content hashes

    def on_created(self, event):
        """Handle new file creation."""
        if not event.is_directory and event.src_path.endswith(".jsonl"):
            logger.info(f"New chat log file detected: {event.src_path}")
            asyncio.run_coroutine_threadsafe(
                self._queue_file_for_processing(event.src_path, "created"),
                asyncio.get_event_loop(),
            )

    def on_modified(self, event):
        """Handle file modifications."""
        if not event.is_directory and event.src_path.endswith(".jsonl"):
            # Only process if content actually changed
            if self._has_content_changed(event.src_path):
                logger.info(f"Chat log file modified: {event.src_path}")
                asyncio.run_coroutine_threadsafe(
                    self._queue_file_for_processing(event.src_path, "modified"),
                    asyncio.get_event_loop(),
                )

    def _has_content_changed(self, file_path: str) -> bool:
        """Check if file content has actually changed using hash comparison."""
        try:
            with open(file_path, "rb") as f:
                content = f.read()
                current_hash = hashlib.md5(content).hexdigest()

            previous_hash = self.file_hashes.get(file_path)
            self.file_hashes[file_path] = current_hash

            return previous_hash != current_hash
        except (IOError, OSError) as e:
            logger.warning(f"Could not read file {file_path}: {e}")
            return False

    async def _queue_file_for_processing(self, file_path: str, event_type: str):
        """Queue file for processing."""
        file_info = {
            "path": file_path,
            "event_type": event_type,
            "timestamp": datetime.now().isoformat(),
            "size": os.path.getsize(file_path) if os.path.exists(file_path) else 0,
        }
        await self.ingestion_queue.put(file_info)


class ChatLogWatcher:
    """Main chat log watcher service."""

    def __init__(self, watch_directories: List[str], ingestion_queue: asyncio.Queue):
        self.watch_directories = watch_directories
        self.ingestion_queue = ingestion_queue
        self.processed_files = set()
        self.observers = []
        self.running = False

    def start(self):
        """Start watching directories."""
        logger.info(
            f"Starting chat log watcher for {len(self.watch_directories)} directories"
        )

        for watch_dir in self.watch_directories:
            if not os.path.exists(watch_dir):
                logger.warning(f"Watch directory does not exist: {watch_dir}")
                continue

            observer = Observer()
            event_handler = ChatLogFileHandler(
                self.ingestion_queue, self.processed_files
            )
            observer.schedule(event_handler, watch_dir, recursive=True)
            observer.start()
            self.observers.append(observer)
            logger.info(f"Started watching: {watch_dir}")

        self.running = True

        # Process existing files on startup
        asyncio.create_task(self._process_existing_files())

    def stop(self):
        """Stop watching directories."""
        logger.info("Stopping chat log watcher")
        self.running = False

        for observer in self.observers:
            observer.stop()
            observer.join()

        self.observers.clear()

    async def _process_existing_files(self):
        """Process existing JSONL files on startup."""
        logger.info("Processing existing chat log files")

        for watch_dir in self.watch_directories:
            if not os.path.exists(watch_dir):
                continue

            for jsonl_file in Path(watch_dir).rglob("*.jsonl"):
                if str(jsonl_file) not in self.processed_files:
                    file_info = {
                        "path": str(jsonl_file),
                        "event_type": "existing",
                        "timestamp": datetime.now().isoformat(),
                        "size": jsonl_file.stat().st_size,
                    }
                    await self.ingestion_queue.put(file_info)

        logger.info("Finished queuing existing files")


class ChatLogDiscovery:
    """Discovers and manages chat log source directories."""

    def __init__(self):
        self.claude_projects_dir = Path.home() / ".claude" / "projects"
        self.additional_sources = [
            "/home/opsvi/master_root",  # Direct project files
            "/home/opsvi/master_root/apps",
            "/home/opsvi/master_root/workspace",
            "/home/opsvi/master_root/razer_workspace",
        ]

    def discover_watch_directories(self) -> List[str]:
        """Discover all directories that should be watched for chat logs."""
        watch_dirs = []

        # Add Claude project directories
        if self.claude_projects_dir.exists():
            for project_dir in self.claude_projects_dir.iterdir():
                if project_dir.is_dir():
                    watch_dirs.append(str(project_dir))

        # Add additional source directories
        for source_dir in self.additional_sources:
            if os.path.exists(source_dir):
                watch_dirs.append(source_dir)

        # Filter out non-existent directories and duplicates
        valid_dirs = []
        for watch_dir in watch_dirs:
            if os.path.exists(watch_dir) and watch_dir not in valid_dirs:
                valid_dirs.append(watch_dir)

        logger.info(f"Discovered {len(valid_dirs)} watch directories")
        return valid_dirs

    def get_project_metadata(self, project_path: str) -> Dict:
        """Extract metadata about a project directory."""
        path = Path(project_path)
        return {
            "name": path.name,
            "path": str(path),
            "exists": path.exists(),
            "is_claude_project": ".claude" in str(path),
            "jsonl_count": len(list(path.rglob("*.jsonl"))) if path.exists() else 0,
            "last_modified": path.stat().st_mtime if path.exists() else None,
        }


# Health check and monitoring utilities
class WatcherHealthCheck:
    """Health monitoring for the watcher service."""

    def __init__(self):
        self.start_time = time.time()
        self.files_processed = 0
        self.last_activity = time.time()
        self.errors = []

    def record_activity(self):
        """Record activity timestamp."""
        self.last_activity = time.time()

    def record_file_processed(self):
        """Record successful file processing."""
        self.files_processed += 1
        self.record_activity()

    def record_error(self, error: str):
        """Record an error."""
        self.errors.append({"timestamp": datetime.now().isoformat(), "error": error})
        # Keep only last 100 errors
        if len(self.errors) > 100:
            self.errors = self.errors[-100:]

    def get_status(self) -> Dict:
        """Get current health status."""
        uptime = time.time() - self.start_time
        idle_time = time.time() - self.last_activity

        return {
            "uptime_seconds": uptime,
            "idle_seconds": idle_time,
            "files_processed": self.files_processed,
            "recent_errors": len(self.errors),
            "is_healthy": idle_time < 3600
            or self.files_processed
            > 0,  # Healthy if active in last hour or processed files
            "last_activity": datetime.fromtimestamp(self.last_activity).isoformat(),
        }


# Configuration management
class WatcherConfig:
    """Configuration for the chat log watcher."""

    def __init__(self):
        self.watch_enabled = os.getenv("CHAT_WATCHER_ENABLED", "true").lower() == "true"
        self.watch_interval = int(os.getenv("CHAT_WATCHER_INTERVAL", "1"))  # seconds
        self.batch_size = int(os.getenv("CHAT_WATCHER_BATCH_SIZE", "10"))
        self.queue_size = int(os.getenv("CHAT_WATCHER_QUEUE_SIZE", "1000"))
        self.health_check_interval = int(
            os.getenv("CHAT_WATCHER_HEALTH_INTERVAL", "60")
        )

        # File filtering
        self.file_extensions = os.getenv("CHAT_WATCHER_EXTENSIONS", ".jsonl").split(",")
        self.ignore_patterns = os.getenv("CHAT_WATCHER_IGNORE", ".tmp,.backup").split(
            ","
        )

        # Rate limiting
        self.max_files_per_minute = int(
            os.getenv("CHAT_WATCHER_MAX_FILES_PER_MIN", "100")
        )

    def is_file_allowed(self, file_path: str) -> bool:
        """Check if file should be processed based on configuration."""
        path = Path(file_path)

        # Check extension
        if not any(path.suffix == ext for ext in self.file_extensions):
            return False

        # Check ignore patterns
        for pattern in self.ignore_patterns:
            if pattern in str(path):
                return False

        return True


if __name__ == "__main__":
    # Basic test of the watcher
    logging.basicConfig(level=logging.INFO)

    discovery = ChatLogDiscovery()
    watch_dirs = discovery.discover_watch_directories()

    print(f"Would watch {len(watch_dirs)} directories:")
    for directory in watch_dirs:
        metadata = discovery.get_project_metadata(directory)
        print(f"  {directory} ({metadata['jsonl_count']} JSONL files)")
