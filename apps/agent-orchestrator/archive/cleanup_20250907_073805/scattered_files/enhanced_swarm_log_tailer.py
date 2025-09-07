#!/usr/bin/env python3
"""
Enhanced Multi-Agent Log Tailer with Swarm Detection
=====================================================

A comprehensive log monitoring system for Claude Code sessions with advanced
swarm detection, real-time visualization, and high-performance async processing.

Version: 2.0.0
Author: Multi-Agent Design Team
Date: 2025-09-07

Features:
- Real-time monitoring of multiple Claude Code session logs
- Advanced swarm detection using DBSCAN, temporal clustering, and behavioral analysis
- Dynamic color-coded agent visualization
- Async file monitoring with position tracking
- Priority-based message queueing
- Comprehensive CLI with configuration management
- Performance optimization and memory management

Usage:
    ./enhanced_swarm_log_tailer.py [OPTIONS]
    
    Basic monitoring:
        ./enhanced_swarm_log_tailer.py
    
    Monitor specific directory:
        ./enhanced_swarm_log_tailer.py --projects-dir /path/to/logs
    
    With swarm detection tuning:
        ./enhanced_swarm_log_tailer.py --swarm-time-window 600 --swarm-min-agents 5
    
    High-performance mode:
        ./enhanced_swarm_log_tailer.py --workers 100 --buffer-size 5000
    
    Export configuration:
        ./enhanced_swarm_log_tailer.py --export-config config.yaml

Requirements:
    - Python 3.8+
    - numpy
    - scipy
    - networkx
    - pyyaml
"""

import asyncio
import argparse
import json
import logging
import os
import signal
import sys
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import (
    Any, AsyncIterator, Callable, Dict, List, Optional, 
    Set, Tuple, Union
)
import hashlib
from concurrent.futures import ThreadPoolExecutor

# Try to import required scientific libraries
try:
    import numpy as np
    from scipy.spatial import KDTree
    import networkx as nx
    SCIENTIFIC_LIBS_AVAILABLE = True
except ImportError:
    SCIENTIFIC_LIBS_AVAILABLE = False
    print("Warning: Scientific libraries (numpy, scipy, networkx) not available.")
    print("Swarm detection will use simplified algorithms.")

# Try to import YAML support
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

# ============================================================================
# Configuration Classes
# ============================================================================

@dataclass
class SystemConfig:
    """System-wide configuration"""
    projects_dir: Path = field(default_factory=lambda: Path("~/.claude/projects").expanduser())
    pattern: str = "*.jsonl"
    max_files: int = 1000
    include_historical: bool = False
    poll_interval_ms: int = 100
    buffer_size: int = 1000
    worker_threads: int = 50
    max_memory_mb: int = 500

@dataclass
class SwarmConfig:
    """Swarm detection configuration"""
    enabled: bool = True
    time_window_seconds: int = 300
    min_agents: int = 3
    temporal_epsilon: float = 5.0
    burst_window: float = 1.0
    burst_threshold: int = 5
    max_time_spread: float = 30.0
    min_connectivity: float = 0.3
    validation_threshold: float = 0.6

@dataclass
class VisualConfig:
    """Visual display configuration"""
    use_color: bool = True
    use_emoji: bool = True
    ascii_only: bool = False
    color_scheme: str = "default"
    truncate_content: bool = True
    max_content_length: int = 200

@dataclass
class OutputConfig:
    """Output configuration"""
    format: str = "text"  # text, json, csv
    file: Optional[str] = None
    quiet: bool = False
    verbose: int = 0
    debug: bool = False

# ============================================================================
# Core Data Classes
# ============================================================================

@dataclass
class AgentInfo:
    """Information about a Claude Code agent"""
    agent_id: str
    session_id: str
    project_path: Path
    role: str = "unknown"
    color: str = ""
    icon: str = "●"

@dataclass
class LogEntry:
    """Parsed log entry from JSONL file"""
    type: str
    timestamp: datetime
    uuid: str
    session_id: str
    agent_id: str
    content: Optional[str] = None
    tool_use: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class LogEvent:
    """Processed log event with context"""
    entry: LogEntry
    agent_info: AgentInfo
    swarm_id: Optional[str] = None
    priority: int = 0
    formatted_content: str = ""
    
    def __lt__(self, other: 'LogEvent') -> bool:
        return self.entry.timestamp < other.entry.timestamp

@dataclass
class SwarmGroup:
    """Detected swarm grouping of agents"""
    swarm_id: str
    agents: Set[str]
    start_time: datetime
    end_time: Optional[datetime] = None
    icon: str = "⚡"
    detection_method: str = "unknown"
    confidence: float = 0.0
    color: str = ""

# ============================================================================
# Color Management
# ============================================================================

class ColorManager:
    """Dynamic color assignment and management for terminal output"""
    
    PALETTES = {
        "default": [
            "\033[38;5;39m",   # Bright blue
            "\033[38;5;40m",   # Green
            "\033[38;5;172m",  # Orange
            "\033[38;5;141m",  # Purple
            "\033[38;5;220m",  # Yellow
            "\033[38;5;203m",  # Pink
            "\033[38;5;51m",   # Cyan
            "\033[38;5;118m",  # Light green
        ],
        "high_contrast": [
            "\033[38;5;15m",   # White
            "\033[38;5;226m",  # Yellow
            "\033[38;5;51m",   # Cyan
            "\033[38;5;201m",  # Magenta
            "\033[38;5;46m",   # Green
            "\033[38;5;196m",  # Red
            "\033[38;5;21m",   # Blue
            "\033[38;5;208m",  # Orange
        ],
        "colorblind": [
            "\033[38;5;33m",   # Blue
            "\033[38;5;208m",  # Orange
            "\033[38;5;142m",  # Gold
            "\033[38;5;55m",   # Purple
            "\033[38;5;244m",  # Gray
            "\033[38;5;125m",  # Pink
            "\033[38;5;37m",   # Teal
            "\033[38;5;94m",   # Brown
        ]
    }
    
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    
    def __init__(self, config: VisualConfig):
        self.config = config
        self.no_color = not config.use_color or not self._supports_color()
        self.palette = self.PALETTES.get(config.color_scheme, self.PALETTES["default"])
        self.agent_colors: Dict[str, str] = {}
        self.color_index = 0
        self._lock = asyncio.Lock()
    
    def _supports_color(self) -> bool:
        """Check if terminal supports color output"""
        if not hasattr(sys.stdout, 'isatty'):
            return False
        if not sys.stdout.isatty():
            return False
        if os.environ.get('NO_COLOR'):
            return False
        if os.environ.get('TERM') == 'dumb':
            return False
        return True
    
    async def assign_color(self, agent_id: str) -> str:
        """Assign a unique color to an agent"""
        if self.no_color:
            return ""
            
        async with self._lock:
            if agent_id not in self.agent_colors:
                color = self.palette[self.color_index % len(self.palette)]
                self.agent_colors[agent_id] = color
                self.color_index += 1
            return self.agent_colors[agent_id]
    
    def format_with_color(self, text: str, agent_id: str, bold: bool = False) -> str:
        """Format text with agent's assigned color"""
        if self.no_color:
            return text
            
        color = self.agent_colors.get(agent_id, "")
        if not color:
            return text
            
        prefix = f"{self.BOLD}{color}" if bold else color
        return f"{prefix}{text}{self.RESET}"

# ============================================================================
# Log Parsing
# ============================================================================

class LogParser:
    """Parses JSONL format Claude Code logs"""
    
    @staticmethod
    def parse_line(line: str) -> Optional[LogEntry]:
        """Parse single JSONL line into LogEntry"""
        if not line or not line.strip():
            return None
        
        try:
            data = json.loads(line)
            
            # Parse timestamp
            timestamp_str = data.get('timestamp', '')
            timestamp = LogParser._parse_timestamp(timestamp_str)
            if not timestamp:
                timestamp = datetime.now()
            
            # Create LogEntry
            return LogEntry(
                type=data.get('type', 'unknown'),
                timestamp=timestamp,
                uuid=data.get('uuid', ''),
                session_id=data.get('session_id', ''),
                agent_id=data.get('agent_id', ''),
                content=data.get('content', data.get('message', '')),
                tool_use=data.get('tool_use'),
                metadata={k: v for k, v in data.items() 
                         if k not in ['type', 'timestamp', 'uuid', 'session_id', 
                                     'agent_id', 'content', 'tool_use']}
            )
            
        except json.JSONDecodeError:
            return None
        except Exception:
            return None
    
    @staticmethod
    def _parse_timestamp(timestamp_str: str) -> Optional[datetime]:
        """Parse timestamp string into datetime"""
        if not timestamp_str:
            return None
        
        formats = [
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S",
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(timestamp_str, fmt)
            except ValueError:
                continue
        
        try:
            timestamp_float = float(timestamp_str)
            return datetime.fromtimestamp(timestamp_float)
        except (ValueError, TypeError):
            pass
        
        return None

# ============================================================================
# Simplified Swarm Detection (when scientific libs not available)
# ============================================================================

class SimpleSwarmDetector:
    """Simplified swarm detection without scientific libraries"""
    
    def __init__(self, config: SwarmConfig):
        self.config = config
        self.active_swarms: Dict[str, SwarmGroup] = {}
        self._swarm_counter = 0
    
    async def detect_swarms(self, events: List[LogEvent]) -> Dict[str, SwarmGroup]:
        """Detect swarms using simple time-based clustering"""
        if not self.config.enabled or len(events) < self.config.min_agents:
            return {}
        
        # Group events by time windows
        time_windows = defaultdict(list)
        window_size = timedelta(seconds=30)
        
        for event in events:
            window_key = int(event.entry.timestamp.timestamp() / 30)
            time_windows[window_key].append(event)
        
        # Find dense windows
        new_swarms = []
        for window_key, window_events in time_windows.items():
            if len(window_events) >= self.config.min_agents:
                # Create swarm
                agent_ids = {e.agent_info.agent_id for e in window_events}
                swarm_id = f"swarm_{self._swarm_counter}"
                self._swarm_counter += 1
                
                swarm = SwarmGroup(
                    swarm_id=swarm_id,
                    agents=agent_ids,
                    start_time=min(e.entry.timestamp for e in window_events),
                    icon="⚡" if len(agent_ids) > 5 else "→",
                    detection_method="time_window",
                    confidence=0.7
                )
                new_swarms.append(swarm)
        
        # Update active swarms
        for swarm in new_swarms:
            self.active_swarms[swarm.swarm_id] = swarm
        
        return self.active_swarms

# ============================================================================
# Advanced Swarm Detection (when scientific libs available)
# ============================================================================

if SCIENTIFIC_LIBS_AVAILABLE:
    class AdvancedSwarmDetector:
        """Advanced swarm detection using DBSCAN and network analysis"""
        
        def __init__(self, config: SwarmConfig):
            self.config = config
            self.active_swarms: Dict[str, SwarmGroup] = {}
            self._swarm_counter = 0
            self.event_buffer = deque(maxlen=10000)
        
        async def detect_swarms(self, events: List[LogEvent]) -> Dict[str, SwarmGroup]:
            """Detect swarms using DBSCAN clustering"""
            if not self.config.enabled or len(events) < self.config.min_agents:
                return {}
            
            # Add events to buffer
            self.event_buffer.extend(events)
            
            # Filter events within time window
            cutoff_time = datetime.now() - timedelta(seconds=self.config.time_window_seconds)
            window_events = [
                e for e in self.event_buffer 
                if e.entry.timestamp > cutoff_time
            ]
            
            if len(window_events) < self.config.min_agents:
                return {}
            
            # Prepare data for clustering
            timestamps = np.array([
                [e.entry.timestamp.timestamp(), 0.5]  # Add dummy dimension
                for e in window_events
            ])
            
            # Normalize timestamps
            if len(timestamps) > 0:
                timestamps[:, 0] = (timestamps[:, 0] - timestamps[:, 0].min()) / (timestamps[:, 0].max() - timestamps[:, 0].min() + 1e-10)
            
            # Build KD-tree for efficient neighbor queries
            tree = KDTree(timestamps)
            
            # DBSCAN clustering
            eps = 0.1  # Epsilon for neighbor distance
            min_pts = self.config.min_agents
            
            clusters = []
            visited = np.zeros(len(window_events), dtype=bool)
            
            for i in range(len(window_events)):
                if visited[i]:
                    continue
                
                neighbors = tree.query_ball_point(timestamps[i], eps)
                
                if len(neighbors) < min_pts:
                    continue
                
                # Expand cluster
                cluster = self._expand_cluster(
                    i, neighbors, tree, timestamps, visited, eps, min_pts
                )
                
                if len(cluster) >= min_pts:
                    clusters.append(cluster)
            
            # Create SwarmGroup objects
            new_swarms = []
            for cluster_indices in clusters:
                cluster_events = [window_events[i] for i in cluster_indices]
                agent_ids = {e.agent_info.agent_id for e in cluster_events}
                
                swarm_id = f"swarm_{self._swarm_counter}"
                self._swarm_counter += 1
                
                swarm = SwarmGroup(
                    swarm_id=swarm_id,
                    agents=agent_ids,
                    start_time=min(e.entry.timestamp for e in cluster_events),
                    icon=self._get_swarm_icon(len(agent_ids)),
                    detection_method="dbscan",
                    confidence=0.8 + (0.2 * min(1.0, len(agent_ids) / 10))
                )
                new_swarms.append(swarm)
            
            # Update active swarms
            for swarm in new_swarms:
                self.active_swarms[swarm.swarm_id] = swarm
            
            return self.active_swarms
        
        def _expand_cluster(self, seed_idx: int, neighbors: List[int], tree: KDTree,
                           data: np.ndarray, visited: np.ndarray, eps: float,
                           min_pts: int) -> List[int]:
            """Expand cluster from seed point"""
            cluster = set([seed_idx])
            queue = list(neighbors)
            
            while queue:
                point_idx = queue.pop(0)
                
                if visited[point_idx]:
                    continue
                
                visited[point_idx] = True
                cluster.add(point_idx)
                
                point_neighbors = tree.query_ball_point(data[point_idx], eps)
                
                if len(point_neighbors) >= min_pts:
                    for neighbor in point_neighbors:
                        if not visited[neighbor]:
                            queue.append(neighbor)
            
            return list(cluster)
        
        def _get_swarm_icon(self, size: int) -> str:
            """Get icon based on swarm size"""
            if size <= 3:
                return "→"  # Pipeline
            elif size <= 5:
                return "⚡"  # Burst
            elif size <= 10:
                return "⫽"  # Parallel
            else:
                return "🔺"  # Hierarchical

# ============================================================================
# File Monitoring
# ============================================================================

class AsyncFileMonitor:
    """Async file monitoring with position tracking"""
    
    def __init__(self, config: SystemConfig):
        self.config = config
        self.file_positions: Dict[Path, int] = {}
        self.position_file = Path(".file_positions.json")
        self.executor = ThreadPoolExecutor(max_workers=config.worker_threads)
        self.semaphore = asyncio.Semaphore(100)
        self._load_positions()
    
    def _load_positions(self):
        """Load saved file positions"""
        if self.position_file.exists():
            try:
                with open(self.position_file, 'r') as f:
                    data = json.load(f)
                    for path_str, position in data.items():
                        self.file_positions[Path(path_str)] = position
            except Exception:
                pass
    
    def _save_positions(self):
        """Save current file positions"""
        try:
            data = {str(path): pos for path, pos in self.file_positions.items()}
            with open(self.position_file, 'w') as f:
                json.dump(data, f)
        except Exception:
            pass
    
    async def discover_files(self) -> List[Path]:
        """Discover log files matching pattern"""
        files = []
        try:
            for file_path in self.config.projects_dir.rglob(self.config.pattern):
                if file_path.is_file():
                    files.append(file_path)
                    if len(files) >= self.config.max_files:
                        break
        except Exception as e:
            logging.error(f"Error discovering files: {e}")
        
        return sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)[:self.config.max_files]
    
    async def tail_file(self, file_path: Path) -> AsyncIterator[str]:
        """Tail a single file"""
        position = self.file_positions.get(file_path, 0)
        
        async with self.semaphore:
            while True:
                try:
                    # Read in thread pool
                    lines = await asyncio.get_event_loop().run_in_executor(
                        self.executor,
                        self._read_lines,
                        file_path,
                        position
                    )
                    
                    if lines:
                        for line, new_position in lines:
                            position = new_position
                            self.file_positions[file_path] = position
                            yield line
                        
                        # Save positions periodically
                        if len(lines) > 10:
                            self._save_positions()
                    
                    await asyncio.sleep(self.config.poll_interval_ms / 1000)
                    
                except asyncio.CancelledError:
                    self._save_positions()
                    raise
                except Exception as e:
                    logging.error(f"Error tailing {file_path}: {e}")
                    await asyncio.sleep(1.0)
    
    def _read_lines(self, file_path: Path, position: int) -> List[Tuple[str, int]]:
        """Read new lines from file"""
        lines = []
        try:
            if not file_path.exists():
                return lines
            
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                # Check if file was truncated
                f.seek(0, 2)  # End of file
                file_size = f.tell()
                if file_size < position:
                    position = 0
                
                f.seek(position)
                while True:
                    line = f.readline()
                    if not line:
                        break
                    lines.append((line.rstrip('\n\r'), f.tell()))
                    if len(lines) >= 100:  # Batch size
                        break
        except Exception:
            pass
        
        return lines

# ============================================================================
# Display Manager
# ============================================================================

class DisplayManager:
    """Manages terminal output and formatting"""
    
    def __init__(self, color_manager: ColorManager, config: VisualConfig):
        self.color_manager = color_manager
        self.config = config
        self.buffer: List[str] = []
        self.last_flush = time.time()
        self.debounce_ms = 50
        self._lock = asyncio.Lock()
    
    async def display_event(self, event: LogEvent) -> None:
        """Display formatted event to terminal"""
        formatted = await self.format_event(event)
        
        async with self._lock:
            self.buffer.append(formatted)
            
            # Check if should flush
            current_time = time.time()
            if (current_time - self.last_flush) * 1000 >= self.debounce_ms or len(self.buffer) > 10:
                await self.flush_buffer()
    
    async def flush_buffer(self) -> None:
        """Flush buffered output to terminal"""
        if not self.buffer:
            return
        
        output = '\n'.join(self.buffer)
        print(output)
        
        self.buffer.clear()
        self.last_flush = time.time()
    
    async def format_event(self, event: LogEvent) -> str:
        """Format event with colors and icons"""
        # Get agent color
        color = await self.color_manager.assign_color(event.agent_info.agent_id)
        
        # Format timestamp
        timestamp_str = event.entry.timestamp.strftime("%H:%M:%S.%f")[:-3]
        
        # Format agent identifier
        agent_str = f"[{event.agent_info.agent_id[:8]}]"
        if event.swarm_id:
            swarm_icon = self._get_swarm_icon(event.swarm_id)
            agent_str = f"{swarm_icon} {agent_str}"
        
        # Format content
        content = event.entry.content or ""
        if self.config.truncate_content and len(content) > self.config.max_content_length:
            content = content[:self.config.max_content_length-3] + "..."
        
        # Apply formatting
        if not self.config.use_color:
            return f"{timestamp_str} {agent_str} {event.entry.type}: {content}"
        else:
            agent_colored = self.color_manager.format_with_color(
                agent_str, 
                event.agent_info.agent_id,
                bold=True
            )
            return f"{timestamp_str} {agent_colored} {event.entry.type}: {content}"
    
    def _get_swarm_icon(self, swarm_id: str) -> str:
        """Get icon for swarm ID"""
        if not self.config.use_emoji:
            return "*"
        
        icons = ["⚡", "→", "⫽", "🔺"]
        try:
            index = int(swarm_id.split('_')[-1]) % len(icons)
            return icons[index]
        except (ValueError, IndexError):
            return "●"

# ============================================================================
# Main Controller
# ============================================================================

class EnhancedSwarmLogTailer:
    """Main controller orchestrating the enhanced log tailing system"""
    
    def __init__(self, system_config: SystemConfig, swarm_config: SwarmConfig, 
                 visual_config: VisualConfig, output_config: OutputConfig):
        self.system_config = system_config
        self.swarm_config = swarm_config
        self.visual_config = visual_config
        self.output_config = output_config
        
        # Initialize components
        self.file_monitor = AsyncFileMonitor(system_config)
        self.color_manager = ColorManager(visual_config)
        self.display_manager = DisplayManager(self.color_manager, visual_config)
        self.parser = LogParser()
        
        # Initialize swarm detector based on available libraries
        if SCIENTIFIC_LIBS_AVAILABLE:
            self.swarm_detector = AdvancedSwarmDetector(swarm_config)
        else:
            self.swarm_detector = SimpleSwarmDetector(swarm_config)
        
        # State management
        self.running = False
        self.active_monitors: Dict[Path, asyncio.Task] = {}
        self.event_queue: asyncio.Queue = asyncio.Queue(maxsize=10000)
        self.statistics = {
            'files_monitored': 0,
            'events_processed': 0,
            'swarms_detected': 0,
            'start_time': None
        }
    
    async def start(self) -> None:
        """Start the enhanced log tailing system"""
        self.running = True
        self.statistics['start_time'] = datetime.now()
        
        # Print startup banner
        self._print_startup_banner()
        
        # Discover files
        files = await self.file_monitor.discover_files()
        if not files:
            print("No log files found to monitor!")
            return
        
        print(f"Monitoring {len(files)} log file(s)...")
        self.statistics['files_monitored'] = len(files)
        
        # Start file monitoring tasks
        for file_path in files:
            task = asyncio.create_task(self._monitor_file(file_path))
            self.active_monitors[file_path] = task
        
        # Start event processing
        processor_task = asyncio.create_task(self._process_events())
        
        # Start swarm detection
        swarm_task = asyncio.create_task(self._detect_swarms())
        
        try:
            # Run until stopped
            await asyncio.gather(processor_task, swarm_task)
        except asyncio.CancelledError:
            pass
        finally:
            await self.stop()
    
    async def _monitor_file(self, file_path: Path) -> None:
        """Monitor a single file and queue events"""
        agent_id = self._extract_agent_id(file_path)
        project_path = self._extract_project_path(file_path)
        
        agent_info = AgentInfo(
            agent_id=agent_id,
            session_id=f"session_{agent_id}",
            project_path=project_path
        )
        
        try:
            async for line in self.file_monitor.tail_file(file_path):
                if not self.running:
                    break
                
                entry = self.parser.parse_line(line)
                if entry:
                    event = LogEvent(
                        entry=entry,
                        agent_info=agent_info
                    )
                    await self.event_queue.put(event)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logging.error(f"Error monitoring {file_path}: {e}")
    
    async def _process_events(self) -> None:
        """Process events from queue and display"""
        batch = []
        batch_timeout = 0.1
        last_batch_time = time.time()
        
        while self.running:
            try:
                # Get event with timeout
                event = await asyncio.wait_for(
                    self.event_queue.get(),
                    timeout=batch_timeout
                )
                batch.append(event)
                
                # Check if should process batch
                current_time = time.time()
                if current_time - last_batch_time >= batch_timeout or len(batch) >= 10:
                    # Display events
                    for event in batch:
                        await self.display_manager.display_event(event)
                        self.statistics['events_processed'] += 1
                    
                    batch.clear()
                    last_batch_time = current_time
                    
            except asyncio.TimeoutError:
                # Process any pending batch
                if batch:
                    for event in batch:
                        await self.display_manager.display_event(event)
                        self.statistics['events_processed'] += 1
                    batch.clear()
                    last_batch_time = time.time()
                
                # Flush display buffer
                await self.display_manager.flush_buffer()
            except Exception as e:
                logging.error(f"Error processing events: {e}")
    
    async def _detect_swarms(self) -> None:
        """Periodically detect swarms from recent events"""
        recent_events = deque(maxlen=1000)
        
        while self.running:
            try:
                # Collect recent events
                try:
                    while not self.event_queue.empty():
                        event = self.event_queue.get_nowait()
                        recent_events.append(event)
                        # Put back in queue for processing
                        await self.event_queue.put(event)
                except asyncio.QueueEmpty:
                    pass
                
                # Detect swarms
                if len(recent_events) >= self.swarm_config.min_agents:
                    swarms = await self.swarm_detector.detect_swarms(list(recent_events))
                    
                    # Assign swarm IDs to events
                    for event in recent_events:
                        for swarm_id, swarm in swarms.items():
                            if event.agent_info.agent_id in swarm.agents:
                                event.swarm_id = swarm_id
                                break
                    
                    # Update statistics
                    self.statistics['swarms_detected'] = len(swarms)
                
                await asyncio.sleep(5.0)  # Check every 5 seconds
                
            except Exception as e:
                logging.error(f"Error detecting swarms: {e}")
                await asyncio.sleep(5.0)
    
    async def stop(self) -> None:
        """Stop the enhanced log tailing system"""
        self.running = False
        
        # Cancel all monitoring tasks
        for task in self.active_monitors.values():
            task.cancel()
        
        if self.active_monitors:
            await asyncio.gather(*self.active_monitors.values(), return_exceptions=True)
        
        # Final flush
        await self.display_manager.flush_buffer()
        
        # Print statistics
        self._print_statistics()
    
    def _extract_agent_id(self, file_path: Path) -> str:
        """Extract agent ID from file path"""
        filename = file_path.stem
        parts = filename.split('_')
        
        if len(parts) >= 4:
            return parts[-1]
        
        path_hash = hashlib.md5(str(file_path).encode()).hexdigest()
        return f"agent_{path_hash[:8]}"
    
    def _extract_project_path(self, file_path: Path) -> Path:
        """Extract project directory from file path"""
        for parent in file_path.parents:
            if parent.name in ["projects", ".claude"]:
                return parent.parent
        return file_path.parent
    
    def _print_startup_banner(self) -> None:
        """Print startup banner"""
        banner = """
╔═══════════════════════════════════════════════════════════════════════╗
║          Enhanced Multi-Agent Log Tailer with Swarm Detection        ║
║                           Version 2.0.0                              ║
╚═══════════════════════════════════════════════════════════════════════╝
        """
        print(banner)
        print(f"Projects Directory: {self.system_config.projects_dir}")
        print(f"File Pattern: {self.system_config.pattern}")
        print(f"Swarm Detection: {'Enabled' if self.swarm_config.enabled else 'Disabled'}")
        if self.swarm_config.enabled:
            print(f"  - Time Window: {self.swarm_config.time_window_seconds}s")
            print(f"  - Min Agents: {self.swarm_config.min_agents}")
        print(f"Visual Mode: {self.visual_config.color_scheme}")
        print("-" * 75)
    
    def _print_statistics(self) -> None:
        """Print final statistics"""
        if self.statistics['start_time']:
            runtime = datetime.now() - self.statistics['start_time']
            print("\n" + "=" * 75)
            print("Session Statistics:")
            print(f"  Runtime: {runtime}")
            print(f"  Files Monitored: {self.statistics['files_monitored']}")
            print(f"  Events Processed: {self.statistics['events_processed']}")
            print(f"  Swarms Detected: {self.statistics['swarms_detected']}")
            if runtime.total_seconds() > 0:
                rate = self.statistics['events_processed'] / runtime.total_seconds()
                print(f"  Processing Rate: {rate:.1f} events/sec")

# ============================================================================
# CLI Interface
# ============================================================================

def create_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser"""
    parser = argparse.ArgumentParser(
        prog='enhanced_swarm_log_tailer',
        description='Enhanced Multi-Agent Log Tailer with Swarm Detection',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Core arguments
    parser.add_argument(
        '--projects-dir',
        type=str,
        default='~/.claude/projects',
        help='Projects directory to monitor (default: ~/.claude/projects)'
    )
    
    parser.add_argument(
        '--pattern',
        type=str,
        default='*.jsonl',
        help='File pattern to match (default: *.jsonl)'
    )
    
    parser.add_argument(
        '--include-historical',
        action='store_true',
        help='Include historical log entries'
    )
    
    # Swarm detection
    parser.add_argument(
        '--no-swarm-detection',
        action='store_true',
        help='Disable swarm detection'
    )
    
    parser.add_argument(
        '--swarm-time-window',
        type=int,
        default=300,
        help='Time window for swarm detection in seconds (default: 300)'
    )
    
    parser.add_argument(
        '--swarm-min-agents',
        type=int,
        default=3,
        help='Minimum agents for swarm detection (default: 3)'
    )
    
    # Visual options
    parser.add_argument(
        '--color-scheme',
        choices=['default', 'high_contrast', 'colorblind'],
        default='default',
        help='Color scheme (default: default)'
    )
    
    parser.add_argument(
        '--no-color',
        action='store_true',
        help='Disable color output'
    )
    
    parser.add_argument(
        '--no-emoji',
        action='store_true',
        help='Disable emoji in output'
    )
    
    parser.add_argument(
        '--ascii-only',
        action='store_true',
        help='Use ASCII characters only'
    )
    
    # Performance
    parser.add_argument(
        '--workers',
        type=int,
        default=50,
        help='Number of worker threads (default: 50)'
    )
    
    parser.add_argument(
        '--buffer-size',
        type=int,
        default=1000,
        help='Output buffer size (default: 1000)'
    )
    
    parser.add_argument(
        '--max-files',
        type=int,
        default=1000,
        help='Maximum files to monitor (default: 1000)'
    )
    
    # Output
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress non-essential output'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='count',
        default=0,
        help='Verbose output'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode'
    )
    
    # Special commands
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 2.0.0'
    )
    
    parser.add_argument(
        '--export-config',
        type=str,
        metavar='FILE',
        help='Export configuration to file'
    )
    
    parser.add_argument(
        '--help-examples',
        action='store_true',
        help='Show usage examples'
    )
    
    return parser

def print_examples():
    """Print usage examples"""
    examples = """
USAGE EXAMPLES:

Basic monitoring:
    ./enhanced_swarm_log_tailer.py

Monitor specific directory:
    ./enhanced_swarm_log_tailer.py --projects-dir /path/to/logs

With swarm detection tuning:
    ./enhanced_swarm_log_tailer.py --swarm-time-window 600 --swarm-min-agents 5

High-performance mode:
    ./enhanced_swarm_log_tailer.py --workers 100 --buffer-size 5000

Visual customization:
    ./enhanced_swarm_log_tailer.py --color-scheme colorblind --no-emoji

Disable swarm detection:
    ./enhanced_swarm_log_tailer.py --no-swarm-detection

Debug mode:
    ./enhanced_swarm_log_tailer.py --debug --verbose

Export configuration:
    ./enhanced_swarm_log_tailer.py --export-config my_config.json
    """
    print(examples)

async def main():
    """Main entry point"""
    # Parse arguments
    parser = create_parser()
    args = parser.parse_args()
    
    # Handle special commands
    if args.help_examples:
        print_examples()
        return 0
    
    # Configure logging
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    elif args.verbose > 0:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.WARNING)
    
    # Build configuration
    system_config = SystemConfig(
        projects_dir=Path(args.projects_dir).expanduser(),
        pattern=args.pattern,
        max_files=args.max_files,
        include_historical=args.include_historical,
        buffer_size=args.buffer_size,
        worker_threads=args.workers
    )
    
    swarm_config = SwarmConfig(
        enabled=not args.no_swarm_detection,
        time_window_seconds=args.swarm_time_window,
        min_agents=args.swarm_min_agents
    )
    
    visual_config = VisualConfig(
        use_color=not args.no_color,
        use_emoji=not args.no_emoji and not args.ascii_only,
        ascii_only=args.ascii_only,
        color_scheme=args.color_scheme
    )
    
    output_config = OutputConfig(
        quiet=args.quiet,
        verbose=args.verbose,
        debug=args.debug
    )
    
    # Export config if requested
    if args.export_config:
        config_data = {
            'system': system_config.__dict__,
            'swarm': swarm_config.__dict__,
            'visual': visual_config.__dict__,
            'output': output_config.__dict__
        }
        # Convert Path objects to strings
        config_data['system']['projects_dir'] = str(config_data['system']['projects_dir'])
        
        with open(args.export_config, 'w') as f:
            json.dump(config_data, f, indent=2, default=str)
        print(f"Configuration exported to: {args.export_config}")
        return 0
    
    # Create and run tailer
    tailer = EnhancedSwarmLogTailer(
        system_config=system_config,
        swarm_config=swarm_config,
        visual_config=visual_config,
        output_config=output_config
    )
    
    # Setup signal handlers
    def signal_handler(sig, frame):
        print("\nShutdown signal received...")
        asyncio.create_task(tailer.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await tailer.start()
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        logging.error(f"Fatal error: {e}", exc_info=True)
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)