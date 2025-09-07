#!/usr/bin/env python3
"""
Async File Monitoring System

High-performance async file tailing with position tracking,
message queuing, and error recovery.
"""

import asyncio
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import AsyncIterator, Dict, List, Optional, Set, Any, Callable
from collections import deque
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Priority(Enum):
    """Message priority levels"""
    HIGH = 1
    MEDIUM = 2
    LOW = 3


class ActivityLevel(Enum):
    """File activity levels for adaptive monitoring"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    IDLE = "idle"


@dataclass
class FilePosition:
    """Track file reading position"""
    path: Path
    position: int = 0
    inode: Optional[int] = None
    last_read: float = field(default_factory=time.time)
    
    def update(self, new_position: int):
        """Update position and timestamp"""
        self.position = new_position
        self.last_read = time.time()


@dataclass
class LogMessage:
    """Enhanced log message structure"""
    timestamp: datetime
    file_path: Path
    line_number: int
    content: str
    priority: Priority = Priority.MEDIUM
    metadata: Dict[str, Any] = field(default_factory=dict)
    agent_id: Optional[str] = None
    session_id: Optional[str] = None
    swarm_id: Optional[str] = None
    correlation_id: Optional[str] = None


class AsyncFileMonitor:
    """
    Async file monitoring with adaptive strategies and position tracking
    """
    
    def __init__(self, max_concurrent: int = 100, max_workers: int = 50):
        self.max_concurrent = max_concurrent
        self.file_semaphore = asyncio.Semaphore(max_concurrent)
        
        # Thread pool for blocking I/O
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # Position tracking
        self.file_positions: Dict[Path, FilePosition] = {}
        self.position_file = Path(".file_positions.json")
        
        # Activity tracking
        self.activity_tracker: Dict[Path, deque] = {}
        self.activity_window = 60  # seconds
        
        # Active monitoring tasks
        self.active_monitors: Dict[Path, asyncio.Task] = {}
        
        # Load saved positions
        self._load_positions()
    
    def _load_positions(self):
        """Load saved file positions from disk"""
        if self.position_file.exists():
            try:
                with open(self.position_file, 'r') as f:
                    data = json.load(f)
                    for path_str, pos_data in data.items():
                        path = Path(path_str)
                        self.file_positions[path] = FilePosition(
                            path=path,
                            position=pos_data.get('position', 0),
                            inode=pos_data.get('inode'),
                            last_read=pos_data.get('last_read', time.time())
                        )
            except Exception as e:
                logger.warning(f"Failed to load positions: {e}")
    
    def _save_positions(self):
        """Save current file positions to disk"""
        try:
            data = {}
            for path, pos in self.file_positions.items():
                data[str(path)] = {
                    'position': pos.position,
                    'inode': pos.inode,
                    'last_read': pos.last_read
                }
            with open(self.position_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save positions: {e}")
    
    def _get_file_position(self, file_path: Path) -> FilePosition:
        """Get or create file position tracker"""
        if file_path not in self.file_positions:
            self.file_positions[file_path] = FilePosition(path=file_path)
        return self.file_positions[file_path]
    
    def _assess_activity_level(self, file_path: Path) -> ActivityLevel:
        """Assess file activity level based on recent read patterns"""
        if file_path not in self.activity_tracker:
            return ActivityLevel.MEDIUM
        
        activity = self.activity_tracker[file_path]
        now = time.time()
        
        # Clean old entries
        while activity and (now - activity[0]) > self.activity_window:
            activity.popleft()
        
        if not activity:
            return ActivityLevel.IDLE
        
        rate = len(activity) / self.activity_window
        
        if rate > 10:  # More than 10 events per minute
            return ActivityLevel.HIGH
        elif rate > 1:  # 1-10 events per minute
            return ActivityLevel.MEDIUM
        elif rate > 0.1:  # Less than 1 event per minute
            return ActivityLevel.LOW
        else:
            return ActivityLevel.IDLE
    
    def _track_activity(self, file_path: Path):
        """Track file activity for adaptive monitoring"""
        if file_path not in self.activity_tracker:
            self.activity_tracker[file_path] = deque(maxlen=1000)
        self.activity_tracker[file_path].append(time.time())
    
    def _blocking_read_chunk(self, file_path: Path, position: int, chunk_size: int = 8192) -> tuple[List[str], int]:
        """Synchronous file reading in thread pool"""
        lines = []
        new_position = position
        
        try:
            # Check if file exists and get stats
            if not file_path.exists():
                return lines, position
            
            stat = file_path.stat()
            
            # Check if file was truncated
            if stat.st_size < position:
                logger.info(f"File {file_path} was truncated, resetting position")
                position = 0
            
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                f.seek(position)
                
                while True:
                    line = f.readline()
                    if not line:
                        break
                    
                    lines.append(line.rstrip('\n\r'))
                    
                    # Limit batch size
                    if len(lines) >= 1000:
                        break
                
                new_position = f.tell()
                
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
        
        return lines, new_position
    
    async def tail_file(self, file_path: Path) -> AsyncIterator[LogMessage]:
        """
        Asynchronously tail a file with position tracking
        
        Yields LogMessage objects as new lines are added to the file
        """
        file_path = Path(file_path).resolve()
        position_tracker = self._get_file_position(file_path)
        line_number = 0
        
        # Determine initial polling interval based on activity
        activity_level = self._assess_activity_level(file_path)
        
        if activity_level == ActivityLevel.HIGH:
            poll_interval = 0.05  # 50ms for active files
        elif activity_level == ActivityLevel.MEDIUM:
            poll_interval = 0.1   # 100ms for medium activity
        elif activity_level == ActivityLevel.LOW:
            poll_interval = 0.5   # 500ms for low activity
        else:
            poll_interval = 1.0   # 1s for idle files
        
        consecutive_empty_reads = 0
        max_empty_reads = 10
        
        async with self.file_semaphore:
            while True:
                try:
                    # Read chunk in thread pool
                    lines, new_position = await asyncio.get_event_loop().run_in_executor(
                        self.executor,
                        self._blocking_read_chunk,
                        file_path,
                        position_tracker.position
                    )
                    
                    if lines:
                        # Reset empty read counter
                        consecutive_empty_reads = 0
                        
                        # Track activity
                        self._track_activity(file_path)
                        
                        # Update position
                        position_tracker.update(new_position)
                        
                        # Yield messages
                        for line in lines:
                            line_number += 1
                            
                            # Parse line and create message
                            message = self._parse_line(line, file_path, line_number)
                            yield message
                        
                        # Save positions periodically
                        if line_number % 100 == 0:
                            self._save_positions()
                        
                        # Adapt polling interval based on activity
                        if len(lines) > 100:
                            poll_interval = max(0.01, poll_interval * 0.8)  # Speed up
                        elif len(lines) > 10:
                            poll_interval = max(0.05, poll_interval * 0.9)
                    else:
                        # No new data
                        consecutive_empty_reads += 1
                        
                        # Adaptive backoff
                        if consecutive_empty_reads > max_empty_reads:
                            poll_interval = min(5.0, poll_interval * 1.5)  # Slow down
                    
                    # Wait before next read
                    await asyncio.sleep(poll_interval)
                    
                except asyncio.CancelledError:
                    # Clean shutdown
                    self._save_positions()
                    raise
                except Exception as e:
                    logger.error(f"Error tailing {file_path}: {e}")
                    await asyncio.sleep(1.0)  # Error backoff
    
    def _parse_line(self, line: str, file_path: Path, line_number: int) -> LogMessage:
        """Parse log line into LogMessage"""
        # Try to parse as JSON
        content = line
        metadata = {}
        agent_id = None
        session_id = None
        priority = Priority.MEDIUM
        
        try:
            data = json.loads(line)
            if isinstance(data, dict):
                # Extract common fields
                agent_id = data.get('agent_id')
                session_id = data.get('session_id')
                
                # Determine priority
                if 'error' in data or 'ERROR' in str(data).upper():
                    priority = Priority.HIGH
                elif 'warning' in data or 'WARN' in str(data).upper():
                    priority = Priority.MEDIUM
                
                metadata = data
                content = data.get('message', line)
        except json.JSONDecodeError:
            # Not JSON, use raw line
            if 'ERROR' in line.upper():
                priority = Priority.HIGH
            elif 'WARN' in line.upper():
                priority = Priority.MEDIUM
        
        return LogMessage(
            timestamp=datetime.now(),
            file_path=file_path,
            line_number=line_number,
            content=content,
            priority=priority,
            metadata=metadata,
            agent_id=agent_id,
            session_id=session_id
        )
    
    async def monitor_files(self, file_paths: List[Path]) -> AsyncIterator[LogMessage]:
        """
        Monitor multiple files concurrently
        
        Yields messages from all files as they arrive
        """
        tasks = []
        queues = []
        
        for file_path in file_paths:
            queue = asyncio.Queue(maxsize=1000)
            queues.append(queue)
            
            # Create monitoring task
            task = asyncio.create_task(
                self._monitor_file_to_queue(file_path, queue)
            )
            tasks.append(task)
            self.active_monitors[file_path] = task
        
        try:
            # Merge messages from all queues
            async for message in self._merge_queues(queues):
                yield message
        finally:
            # Cancel all monitoring tasks
            for task in tasks:
                task.cancel()
            
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _monitor_file_to_queue(self, file_path: Path, queue: asyncio.Queue):
        """Monitor a file and put messages into queue"""
        try:
            async for message in self.tail_file(file_path):
                await queue.put(message)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"Error monitoring {file_path}: {e}")
    
    async def _merge_queues(self, queues: List[asyncio.Queue]) -> AsyncIterator[LogMessage]:
        """Merge messages from multiple queues"""
        # Map tasks to their queue index
        task_to_queue = {}
        pending = set()
        
        # Start with getting from all queues
        for i, queue in enumerate(queues):
            task = asyncio.create_task(queue.get())
            task_to_queue[task] = i
            pending.add(task)
        
        try:
            while pending:
                done, pending = await asyncio.wait(
                    pending,
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                for task in done:
                    try:
                        message = task.result()
                        yield message
                        
                        # Get next message from same queue
                        queue_idx = task_to_queue.pop(task)
                        new_task = asyncio.create_task(queues[queue_idx].get())
                        task_to_queue[new_task] = queue_idx
                        pending.add(new_task)
                        
                    except asyncio.CancelledError:
                        raise
                    except Exception as e:
                        logger.error(f"Error getting from queue: {e}")
        finally:
            # Cancel any pending tasks
            for task in pending:
                task.cancel()
            if pending:
                await asyncio.gather(*pending, return_exceptions=True)
    
    async def stop(self):
        """Stop all monitoring tasks and save state"""
        for task in self.active_monitors.values():
            task.cancel()
        
        await asyncio.gather(*self.active_monitors.values(), return_exceptions=True)
        
        self._save_positions()
        self.executor.shutdown(wait=False)


class MessageQueue:
    """
    Priority-based message queue with back-pressure management
    """
    
    def __init__(self, high_size: int = 1000, medium_size: int = 5000, low_size: int = 10000):
        self.queues = {
            Priority.HIGH: asyncio.Queue(maxsize=high_size),
            Priority.MEDIUM: asyncio.Queue(maxsize=medium_size),
            Priority.LOW: asyncio.Queue(maxsize=low_size)
        }
        
        self.backpressure_threshold = 0.8
        self.stats = {
            'messages_queued': 0,
            'messages_dropped': 0,
            'messages_processed': 0
        }
    
    async def put(self, message: LogMessage) -> bool:
        """
        Put message in appropriate queue
        
        Returns True if queued, False if dropped
        """
        queue = self.queues[message.priority]
        
        # Check back-pressure
        utilization = queue.qsize() / queue.maxsize if queue.maxsize > 0 else 0
        
        if utilization >= 1.0:
            # Queue full
            if message.priority == Priority.LOW:
                # Drop low priority messages when full
                self.stats['messages_dropped'] += 1
                return False
            else:
                # Wait for high priority messages
                await queue.put(message)
        elif utilization > self.backpressure_threshold:
            # Apply back-pressure strategy
            if message.priority == Priority.LOW and utilization > 0.9:
                # Drop low priority when near capacity
                self.stats['messages_dropped'] += 1
                return False
            else:
                await queue.put(message)
        else:
            # Normal operation
            await queue.put(message)
        
        self.stats['messages_queued'] += 1
        return True
    
    async def get(self) -> LogMessage:
        """
        Get next message with priority ordering
        
        Checks high priority first, then medium, then low
        """
        # Try high priority first
        for priority in [Priority.HIGH, Priority.MEDIUM, Priority.LOW]:
            queue = self.queues[priority]
            if not queue.empty():
                message = await queue.get()
                self.stats['messages_processed'] += 1
                return message
        
        # All queues empty, wait on any
        tasks = [
            asyncio.create_task(queue.get())
            for queue in self.queues.values()
        ]
        
        done, pending = await asyncio.wait(
            tasks,
            return_when=asyncio.FIRST_COMPLETED
        )
        
        # Cancel pending tasks
        for task in pending:
            task.cancel()
        
        # Return first completed
        for task in done:
            message = task.result()
            self.stats['messages_processed'] += 1
            return message
    
    def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        stats = self.stats.copy()
        stats['queue_sizes'] = {
            priority.name: queue.qsize()
            for priority, queue in self.queues.items()
        }
        return stats


class OutputProcessor:
    """
    Process and format output messages
    """
    
    def __init__(self, format_func: Optional[Callable] = None):
        self.format_func = format_func or self._default_format
        self.buffer = []
        self.buffer_size = 100
        self.flush_interval = 0.1
        self.last_flush = time.time()
    
    def _default_format(self, message: LogMessage) -> str:
        """Default message formatting"""
        timestamp = message.timestamp.strftime('%H:%M:%S.%f')[:-3]
        
        # Color codes for terminal
        colors = {
            Priority.HIGH: '\033[91m',    # Red
            Priority.MEDIUM: '\033[93m',  # Yellow
            Priority.LOW: '\033[0m'        # Default
        }
        
        color = colors.get(message.priority, '\033[0m')
        reset = '\033[0m'
        
        # Format with metadata
        parts = [f"{color}[{timestamp}]"]
        
        if message.agent_id:
            parts.append(f"[{message.agent_id}]")
        
        parts.append(f"{message.file_path.name}:{message.line_number}")
        parts.append(message.content)
        
        return ' '.join(parts) + reset
    
    async def process(self, message: LogMessage):
        """Process a single message"""
        formatted = self.format_func(message)
        self.buffer.append(formatted)
        
        # Check if should flush
        if len(self.buffer) >= self.buffer_size or \
           (time.time() - self.last_flush) > self.flush_interval:
            await self.flush()
    
    async def flush(self):
        """Flush buffered output"""
        if not self.buffer:
            return
        
        # Print all buffered messages
        for line in self.buffer:
            print(line)
        
        self.buffer.clear()
        self.last_flush = time.time()


class AsyncMonitoringPipeline:
    """
    Complete async monitoring pipeline with all components
    """
    
    def __init__(self, max_concurrent: int = 100):
        self.monitor = AsyncFileMonitor(max_concurrent=max_concurrent)
        self.queue = MessageQueue()
        self.processor = OutputProcessor()
        self.running = False
        self.tasks = []
    
    async def start(self, file_paths: List[Path]):
        """Start the monitoring pipeline"""
        self.running = True
        
        # Start file monitoring task
        monitor_task = asyncio.create_task(
            self._run_monitor(file_paths)
        )
        self.tasks.append(monitor_task)
        
        # Start message processing task
        process_task = asyncio.create_task(
            self._run_processor()
        )
        self.tasks.append(process_task)
        
        # Start stats reporting task
        stats_task = asyncio.create_task(
            self._run_stats()
        )
        self.tasks.append(stats_task)
        
        logger.info(f"Started monitoring {len(file_paths)} files")
    
    async def _run_monitor(self, file_paths: List[Path]):
        """Run file monitoring and queue messages"""
        try:
            async for message in self.monitor.monitor_files(file_paths):
                if not self.running:
                    break
                
                # Queue message
                queued = await self.queue.put(message)
                if not queued:
                    logger.debug(f"Dropped message from {message.file_path}")
                    
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"Monitor error: {e}")
    
    async def _run_processor(self):
        """Process messages from queue"""
        try:
            while self.running:
                try:
                    # Get message with timeout
                    message = await asyncio.wait_for(
                        self.queue.get(),
                        timeout=1.0
                    )
                    
                    # Process and output
                    await self.processor.process(message)
                    
                except asyncio.TimeoutError:
                    # Flush any pending output
                    await self.processor.flush()
                    
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"Processor error: {e}")
    
    async def _run_stats(self):
        """Periodically report statistics"""
        try:
            while self.running:
                await asyncio.sleep(10)  # Report every 10 seconds
                
                stats = self.queue.get_stats()
                logger.info(f"Queue stats: {stats}")
                
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"Stats error: {e}")
    
    async def stop(self):
        """Stop the monitoring pipeline"""
        self.running = False
        
        # Cancel all tasks
        for task in self.tasks:
            task.cancel()
        
        await asyncio.gather(*self.tasks, return_exceptions=True)
        
        # Stop monitor
        await self.monitor.stop()
        
        # Final flush
        await self.processor.flush()
        
        # Final stats
        stats = self.queue.get_stats()
        logger.info(f"Final stats: {stats}")


async def main():
    """Example usage"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python async_monitoring.py <file1> [file2] ...")
        sys.exit(1)
    
    # Get file paths from arguments
    file_paths = [Path(arg) for arg in sys.argv[1:]]
    
    # Create and start pipeline
    pipeline = AsyncMonitoringPipeline()
    
    try:
        await pipeline.start(file_paths)
        
        # Run until interrupted
        await asyncio.Event().wait()
        
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        await pipeline.stop()


if __name__ == "__main__":
    asyncio.run(main())