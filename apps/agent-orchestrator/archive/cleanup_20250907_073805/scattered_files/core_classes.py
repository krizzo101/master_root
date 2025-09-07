#!/usr/bin/env python3
"""
Multi-Agent Log Tailer - Core Classes
======================================

This module contains the core classes for the Multi-Agent Log Tailer system,
a high-performance, asynchronous system designed to monitor and analyze 
Claude Code session logs in real-time.

Key Components:
- AgentLogTailer: Main controller orchestrating the log tailing system
- ProcessOrchestrator: Manages async processing pipeline and worker coordination
- FileMonitor: Monitors individual log files for changes
- LogParser: Parses JSONL format Claude Code logs
- SwarmDetector: Detects and groups agent swarms
- DisplayManager: Manages terminal output and formatting
- ColorManager: Dynamic color assignment and management

Author: Multi-Agent Design Team
Version: 1.0.0
Date: 2025-09-07
"""

import asyncio
import json
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
import os
import sys
import signal
from abc import ABC, abstractmethod


# ============================================================================
# Configuration and Data Models
# ============================================================================

@dataclass
class TailerConfig:
    """System configuration for the log tailer.
    
    Attributes:
        projects_dir: Root directory containing Claude Code projects
        pattern: Glob pattern for log file discovery (default: "*.jsonl")
        include_historical: Whether to include historical log entries
        max_files: Maximum number of files to monitor concurrently
        poll_interval: File polling interval in seconds
        buffer_size: Output buffer size for event batching
        color_scheme: Terminal color scheme selection
        no_color: Disable all color output
        use_emoji: Enable emoji indicators for swarms
        workers: Number of worker tasks for processing
    """
    projects_dir: Path
    pattern: str = "*.jsonl"
    include_historical: bool = False
    max_files: int = 1000
    poll_interval: float = 0.1
    buffer_size: int = 1000
    color_scheme: str = "default"
    no_color: bool = False
    use_emoji: bool = True
    workers: int = 10


@dataclass
class SwarmConfig:
    """Configuration for swarm detection algorithms.
    
    Attributes:
        enabled: Enable swarm detection
        time_window: Time window for swarm grouping (seconds)
        min_agents: Minimum agents required for swarm
        algorithms: List of detection algorithms to use
    """
    enabled: bool = True
    time_window: float = 300.0  # 5 minutes
    min_agents: int = 3
    algorithms: List[str] = field(default_factory=lambda: [
        "dbscan", "sliding_window", "directory_grouping"
    ])


@dataclass
class AgentInfo:
    """Information about a Claude Code agent.
    
    Attributes:
        agent_id: Unique agent identifier
        session_id: Session identifier
        project_path: Path to project directory
        role: Agent role (user/assistant/system)
        color: Assigned terminal color
        icon: Display icon for agent
    """
    agent_id: str
    session_id: str
    project_path: Path
    role: str = "unknown"
    color: str = ""
    icon: str = "●"


@dataclass
class LogEntry:
    """Parsed log entry from JSONL file.
    
    Attributes:
        type: Entry type (user/assistant/system/summary)
        timestamp: Entry timestamp
        uuid: Unique entry identifier
        session_id: Session identifier
        agent_id: Agent identifier
        content: Message content
        tool_use: Tool usage information
        metadata: Additional metadata
    """
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
    """Processed log event with context.
    
    Attributes:
        entry: Parsed log entry
        agent_info: Agent context information
        swarm_id: Assigned swarm identifier
        priority: Processing priority
        formatted_content: Pre-formatted display content
    """
    entry: LogEntry
    agent_info: AgentInfo
    swarm_id: Optional[str] = None
    priority: int = 0
    formatted_content: str = ""
    
    def __lt__(self, other: 'LogEvent') -> bool:
        """Compare events for priority queue ordering."""
        return self.entry.timestamp < other.entry.timestamp


@dataclass
class SwarmGroup:
    """Detected swarm grouping of agents.
    
    Attributes:
        swarm_id: Unique swarm identifier
        agents: Set of agent IDs in swarm
        start_time: Swarm start timestamp
        end_time: Swarm end timestamp (None if active)
        icon: Visual indicator for swarm type
        detection_method: Algorithm used for detection
        confidence: Detection confidence score (0-1)
    """
    swarm_id: str
    agents: Set[str]
    start_time: datetime
    end_time: Optional[datetime] = None
    icon: str = "⚡"
    detection_method: str = "unknown"
    confidence: float = 0.0


class SwarmType(Enum):
    """Types of agent swarms detected."""
    BURST = "burst"        # Rapid sequential activity
    PIPELINE = "pipeline"  # Ordered processing chain
    PARALLEL = "parallel"  # Concurrent operations
    HIERARCHICAL = "hierarchical"  # Parent-child relationships


# ============================================================================
# Color Management
# ============================================================================

class ColorManager:
    """Dynamic color assignment and management for terminal output.
    
    This class manages color allocation for agents and swarms, supporting
    256-color terminals with colorblind-safe schemes and automatic
    contrast optimization.
    """
    
    # Color palettes for different schemes
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
    
    def __init__(self, scheme: str = "default", no_color: bool = False):
        """Initialize color manager.
        
        Args:
            scheme: Color scheme name
            no_color: Disable all colors
        """
        self.scheme = scheme
        self.no_color = no_color or not self._supports_color()
        self.palette = self.PALETTES.get(scheme, self.PALETTES["default"])
        self.agent_colors: Dict[str, str] = {}
        self.color_index = 0
        self._lock = asyncio.Lock()
    
    def _supports_color(self) -> bool:
        """Check if terminal supports color output."""
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
        """Assign a unique color to an agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            ANSI color code for the agent
        """
        if self.no_color:
            return ""
            
        async with self._lock:
            if agent_id not in self.agent_colors:
                color = self.palette[self.color_index % len(self.palette)]
                self.agent_colors[agent_id] = color
                self.color_index += 1
            return self.agent_colors[agent_id]
    
    def get_color(self, agent_id: str) -> str:
        """Get assigned color for an agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            ANSI color code or empty string if not assigned
        """
        if self.no_color:
            return ""
        return self.agent_colors.get(agent_id, "")
    
    def format_with_color(self, text: str, agent_id: str, bold: bool = False) -> str:
        """Format text with agent's assigned color.
        
        Args:
            text: Text to format
            agent_id: Agent identifier for color lookup
            bold: Apply bold formatting
            
        Returns:
            Formatted text with ANSI codes
        """
        if self.no_color:
            return text
            
        color = self.get_color(agent_id)
        if not color:
            return text
            
        prefix = f"{self.BOLD}{color}" if bold else color
        return f"{prefix}{text}{self.RESET}"
    
    def reset(self) -> None:
        """Reset all color assignments."""
        self.agent_colors.clear()
        self.color_index = 0


# ============================================================================
# File Discovery and Monitoring
# ============================================================================

class FileDiscovery:
    """Utilities for discovering and filtering log files.
    
    This class handles the discovery of Claude Code session log files
    within the projects directory structure.
    """
    
    @staticmethod
    async def discover_files(
        base_dir: Path, 
        pattern: str = "*.jsonl",
        max_files: int = 1000
    ) -> List[Path]:
        """Discover log files matching the specified pattern.
        
        Args:
            base_dir: Base directory to search
            pattern: Glob pattern for file matching
            max_files: Maximum number of files to return
            
        Returns:
            List of discovered file paths, sorted by modification time
        """
        discovered_files = []
        
        try:
            # Use rglob for recursive pattern matching
            for file_path in base_dir.rglob(pattern):
                if file_path.is_file():
                    discovered_files.append(file_path)
                    
                    # Early exit if we've found enough files
                    if len(discovered_files) >= max_files:
                        break
            
            # Sort by modification time (newest first)
            discovered_files.sort(
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
            
            # Limit to max_files
            return discovered_files[:max_files]
            
        except Exception as e:
            print(f"Error discovering files: {e}", file=sys.stderr)
            return []
    
    @staticmethod
    def extract_agent_id(file_path: Path) -> str:
        """Extract agent ID from file path.
        
        Args:
            file_path: Path to log file
            
        Returns:
            Extracted agent ID or generated hash
        """
        # Try to extract from filename pattern
        # Expected format: session_YYYYMMDD_HHMMSS_UUID.jsonl
        filename = file_path.stem
        parts = filename.split('_')
        
        if len(parts) >= 4:
            # Use the UUID part as agent ID
            return parts[-1]
        
        # Fallback: generate ID from path hash
        path_hash = hashlib.md5(str(file_path).encode()).hexdigest()
        return f"agent_{path_hash[:8]}"
    
    @staticmethod
    def extract_project_path(file_path: Path) -> Path:
        """Extract project directory from file path.
        
        Args:
            file_path: Path to log file
            
        Returns:
            Project directory path
        """
        # Navigate up to find project root
        # Typically: projects/project_name/logs/session.jsonl
        for parent in file_path.parents:
            if parent.name == "projects" or parent.name == ".claude":
                return parent.parent
        
        # Fallback to parent directory
        return file_path.parent


class FileMonitor:
    """Monitors individual log file for changes.
    
    This class handles the monitoring of a single log file,
    tracking position, detecting changes, and yielding new entries.
    """
    
    def __init__(self, file_path: Path, agent_id: str):
        """Initialize file monitor.
        
        Args:
            file_path: Path to log file
            agent_id: Associated agent identifier
        """
        self.file_path = file_path
        self.agent_id = agent_id
        self.position = 0
        self.last_activity = time.time()
        self.poll_interval = 0.1  # Start with default
        self.is_paused = False
        self._file_handle = None
        self._last_inode = None
    
    async def tail(self) -> AsyncIterator[str]:
        """Yield new log lines as they appear.
        
        Yields:
            New lines from the log file
        """
        while not self.is_paused:
            try:
                # Check for file rotation
                if await self.check_rotation():
                    self.position = 0
                
                # Open file if needed
                if not self._file_handle:
                    self._file_handle = open(self.file_path, 'r')
                    self._file_handle.seek(self.position)
                
                # Read new lines
                lines = self._file_handle.readlines()
                if lines:
                    for line in lines:
                        yield line.strip()
                    
                    # Update position
                    self.position = self._file_handle.tell()
                    self.last_activity = time.time()
                    
                    # Adaptive polling: speed up when active
                    self.poll_interval = max(0.01, self.poll_interval * 0.9)
                else:
                    # No new data: slow down polling
                    self.poll_interval = min(1.0, self.poll_interval * 1.1)
                    await asyncio.sleep(self.poll_interval)
                    
            except FileNotFoundError:
                # File deleted or moved
                if self._file_handle:
                    self._file_handle.close()
                    self._file_handle = None
                await asyncio.sleep(1.0)
                
            except Exception as e:
                print(f"Error tailing {self.file_path}: {e}", file=sys.stderr)
                await asyncio.sleep(1.0)
    
    async def check_rotation(self) -> bool:
        """Check if file has been rotated.
        
        Returns:
            True if file was rotated, False otherwise
        """
        try:
            current_stat = self.file_path.stat()
            current_inode = current_stat.st_ino
            
            if self._last_inode is None:
                self._last_inode = current_inode
                return False
            
            if current_inode != self._last_inode:
                # File has been rotated
                self._last_inode = current_inode
                if self._file_handle:
                    self._file_handle.close()
                    self._file_handle = None
                return True
                
            # Check if file truncated
            if current_stat.st_size < self.position:
                if self._file_handle:
                    self._file_handle.close()
                    self._file_handle = None
                return True
                
        except FileNotFoundError:
            return False
        except Exception:
            return False
        
        return False
    
    def update_position(self, new_position: int) -> None:
        """Update and persist file position.
        
        Args:
            new_position: New file position
        """
        self.position = new_position
    
    def pause(self) -> None:
        """Pause file monitoring."""
        self.is_paused = True
    
    def resume(self) -> None:
        """Resume file monitoring."""
        self.is_paused = False
    
    def close(self) -> None:
        """Close file handle and cleanup."""
        if self._file_handle:
            self._file_handle.close()
            self._file_handle = None


# ============================================================================
# Log Parsing
# ============================================================================

class LogParser:
    """Parses JSONL format Claude Code logs.
    
    This class handles the parsing of JSON Lines log entries,
    extracting relevant information and handling malformed data.
    """
    
    @staticmethod
    def parse_line(line: str) -> Optional[LogEntry]:
        """Parse single JSONL line into LogEntry.
        
        Args:
            line: Raw JSON line from log file
            
        Returns:
            Parsed LogEntry or None if parsing fails
        """
        if not line or not line.strip():
            return None
        
        try:
            data = json.loads(line)
            
            # Validate required fields
            if not LogParser.validate_entry(data):
                return None
            
            # Parse timestamp
            timestamp = LogParser._parse_timestamp(data.get('timestamp', ''))
            if not timestamp:
                return None
            
            # Extract metadata
            metadata = LogParser.extract_metadata(data)
            
            # Create LogEntry
            return LogEntry(
                type=data.get('type', 'unknown'),
                timestamp=timestamp,
                uuid=data.get('uuid', ''),
                session_id=data.get('session_id', ''),
                agent_id=data.get('agent_id', ''),
                content=data.get('content'),
                tool_use=data.get('tool_use'),
                metadata=metadata
            )
            
        except json.JSONDecodeError as e:
            # Attempt to recover partial data
            return LogParser._recover_partial_entry(line)
        except Exception:
            return None
    
    @staticmethod
    def validate_entry(entry: dict) -> bool:
        """Validate required fields exist.
        
        Args:
            entry: Parsed JSON dictionary
            
        Returns:
            True if entry has required fields
        """
        required_fields = ['type', 'timestamp']
        return all(field in entry for field in required_fields)
    
    @staticmethod
    def extract_metadata(entry: dict) -> Dict[str, Any]:
        """Extract metadata from log entry.
        
        Args:
            entry: Parsed JSON dictionary
            
        Returns:
            Extracted metadata dictionary
        """
        # Known fields to exclude from metadata
        known_fields = {
            'type', 'timestamp', 'uuid', 'session_id',
            'agent_id', 'content', 'tool_use'
        }
        
        metadata = {}
        for key, value in entry.items():
            if key not in known_fields:
                metadata[key] = value
        
        return metadata
    
    @staticmethod
    def _parse_timestamp(timestamp_str: str) -> Optional[datetime]:
        """Parse timestamp string into datetime.
        
        Args:
            timestamp_str: Timestamp string
            
        Returns:
            Parsed datetime or None
        """
        if not timestamp_str:
            return None
        
        # Try common timestamp formats
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
        
        # Try Unix timestamp
        try:
            timestamp_float = float(timestamp_str)
            return datetime.fromtimestamp(timestamp_float)
        except (ValueError, TypeError):
            pass
        
        return None
    
    @staticmethod
    def _recover_partial_entry(line: str) -> Optional[LogEntry]:
        """Attempt to recover partial data from malformed JSON.
        
        Args:
            line: Malformed JSON line
            
        Returns:
            Partial LogEntry or None
        """
        # Try to extract basic fields using regex
        import re
        
        type_match = re.search(r'"type"\s*:\s*"([^"]+)"', line)
        timestamp_match = re.search(r'"timestamp"\s*:\s*"([^"]+)"', line)
        
        if type_match and timestamp_match:
            timestamp = LogParser._parse_timestamp(timestamp_match.group(1))
            if timestamp:
                return LogEntry(
                    type=type_match.group(1),
                    timestamp=timestamp,
                    uuid="recovered",
                    session_id="unknown",
                    agent_id="unknown",
                    metadata={"recovered": True, "raw": line[:100]}
                )
        
        return None


# ============================================================================
# Swarm Detection
# ============================================================================

class SwarmDetector:
    """Detects and groups agent swarms using multiple algorithms.
    
    This class implements core swarm detection logic using DBSCAN clustering,
    sliding window analysis, and behavioral pattern recognition.
    """
    
    def __init__(self, config: SwarmConfig):
        """Initialize swarm detector.
        
        Args:
            config: Swarm detection configuration
        """
        self.config = config
        self.time_window = timedelta(seconds=config.time_window)
        self.min_agents = config.min_agents
        self.active_swarms: Dict[str, SwarmGroup] = {}
        self.event_buffer: deque = deque(maxlen=10000)
        self._swarm_counter = 0
    
    async def detect_swarms(self, events: List[LogEvent]) -> Dict[str, SwarmGroup]:
        """Detect swarms using configured algorithms.
        
        Args:
            events: List of log events to analyze
            
        Returns:
            Dictionary of detected swarm groups
        """
        if not self.config.enabled or len(events) < self.min_agents:
            return {}
        
        # Add events to buffer
        self.event_buffer.extend(events)
        
        # Filter events within time window
        cutoff_time = datetime.now() - self.time_window
        window_events = [
            e for e in self.event_buffer 
            if e.entry.timestamp > cutoff_time
        ]
        
        # Run detection algorithms
        clusters = []
        
        if "dbscan" in self.config.algorithms:
            clusters.extend(self._dbscan_clustering(window_events))
        
        if "sliding_window" in self.config.algorithms:
            clusters.extend(self._sliding_window(window_events))
        
        if "directory_grouping" in self.config.algorithms:
            clusters.extend(self._directory_grouping(window_events))
        
        # Build consensus and merge results
        swarms = self._build_consensus(clusters)
        
        # Update active swarms
        self._update_active_swarms(swarms)
        
        return self.active_swarms
    
    def _dbscan_clustering(self, events: List[LogEvent]) -> List[Set[str]]:
        """DBSCAN clustering algorithm for temporal grouping.
        
        Args:
            events: Events to cluster
            
        Returns:
            List of agent ID clusters
        """
        if len(events) < self.min_agents:
            return []
        
        # Build temporal distance matrix
        clusters = []
        processed = set()
        
        for i, event in enumerate(events):
            if event.agent_info.agent_id in processed:
                continue
            
            # Find neighbors within time threshold (5 seconds)
            neighbors = []
            for j, other in enumerate(events):
                if i != j:
                    time_diff = abs(
                        (event.entry.timestamp - other.entry.timestamp).total_seconds()
                    )
                    if time_diff <= 5.0:  # eps parameter
                        neighbors.append(other.agent_info.agent_id)
            
            # Form cluster if enough neighbors
            if len(neighbors) >= self.min_agents - 1:
                cluster = {event.agent_info.agent_id}
                cluster.update(neighbors)
                clusters.append(cluster)
                processed.update(cluster)
        
        return clusters
    
    def _sliding_window(self, events: List[LogEvent]) -> List[Set[str]]:
        """Sliding window detection for streaming analysis.
        
        Args:
            events: Events to analyze
            
        Returns:
            List of agent ID clusters
        """
        if len(events) < self.min_agents:
            return []
        
        clusters = []
        window_size = timedelta(seconds=30)
        step_size = timedelta(seconds=15)  # 50% overlap
        
        # Sort events by timestamp
        sorted_events = sorted(events, key=lambda e: e.entry.timestamp)
        
        if not sorted_events:
            return []
        
        start_time = sorted_events[0].entry.timestamp
        end_time = sorted_events[-1].entry.timestamp
        
        current_start = start_time
        while current_start < end_time:
            current_end = current_start + window_size
            
            # Get events in window
            window_events = [
                e for e in sorted_events
                if current_start <= e.entry.timestamp < current_end
            ]
            
            # Count agents in window
            agent_counts = defaultdict(int)
            for event in window_events:
                agent_counts[event.agent_info.agent_id] += 1
            
            # Check density threshold
            if len(agent_counts) >= self.min_agents:
                # Calculate activity density
                total_events = sum(agent_counts.values())
                density = total_events / (len(agent_counts) * 30.0)  # events per agent per second
                
                if density > 0.3:  # Activity threshold
                    clusters.append(set(agent_counts.keys()))
            
            current_start += step_size
        
        return clusters
    
    def _directory_grouping(self, events: List[LogEvent]) -> List[Set[str]]:
        """Group agents by project directory.
        
        Args:
            events: Events to group
            
        Returns:
            List of agent ID clusters
        """
        if len(events) < self.min_agents:
            return []
        
        # Group by project path
        project_groups = defaultdict(set)
        for event in events:
            project_path = event.agent_info.project_path
            project_groups[project_path].add(event.agent_info.agent_id)
        
        # Filter groups meeting minimum size
        clusters = [
            agents for agents in project_groups.values()
            if len(agents) >= self.min_agents
        ]
        
        return clusters
    
    def _build_consensus(self, clusters: List[Set[str]]) -> List[SwarmGroup]:
        """Build consensus from multiple detection algorithms.
        
        Args:
            clusters: List of detected clusters
            
        Returns:
            Consolidated swarm groups
        """
        if not clusters:
            return []
        
        # Merge overlapping clusters
        merged = []
        for cluster in clusters:
            merged_with_existing = False
            
            for existing in merged:
                # Check overlap threshold (50%)
                overlap = len(cluster & existing) / min(len(cluster), len(existing))
                if overlap > 0.5:
                    existing.update(cluster)
                    merged_with_existing = True
                    break
            
            if not merged_with_existing:
                merged.append(cluster)
        
        # Create SwarmGroup objects
        swarms = []
        for agent_set in merged:
            if len(agent_set) >= self.min_agents:
                swarm = SwarmGroup(
                    swarm_id=self._generate_swarm_id(),
                    agents=agent_set,
                    start_time=datetime.now(),
                    icon=self._determine_swarm_icon(agent_set),
                    detection_method="consensus",
                    confidence=self._calculate_confidence(agent_set, clusters)
                )
                swarms.append(swarm)
        
        return swarms
    
    def _update_active_swarms(self, new_swarms: List[SwarmGroup]) -> None:
        """Update active swarms with new detections.
        
        Args:
            new_swarms: Newly detected swarms
        """
        # Mark dissolved swarms
        current_time = datetime.now()
        for swarm_id, swarm in list(self.active_swarms.items()):
            still_active = False
            for new_swarm in new_swarms:
                if swarm.agents & new_swarm.agents:
                    still_active = True
                    break
            
            if not still_active and swarm.end_time is None:
                swarm.end_time = current_time
        
        # Add or update swarms
        for new_swarm in new_swarms:
            # Check if extends existing swarm
            extended = False
            for swarm_id, existing in self.active_swarms.items():
                overlap = len(new_swarm.agents & existing.agents) / len(new_swarm.agents)
                if overlap > 0.7:  # 70% overlap threshold
                    existing.agents.update(new_swarm.agents)
                    existing.end_time = None  # Still active
                    extended = True
                    break
            
            if not extended:
                self.active_swarms[new_swarm.swarm_id] = new_swarm
    
    def _generate_swarm_id(self) -> str:
        """Generate unique swarm identifier."""
        self._swarm_counter += 1
        return f"swarm_{self._swarm_counter:04d}"
    
    def _determine_swarm_icon(self, agents: Set[str]) -> str:
        """Determine appropriate icon for swarm type."""
        # Simple heuristic based on agent count and pattern
        if len(agents) <= 3:
            return "→"  # Pipeline
        elif len(agents) <= 5:
            return "⚡"  # Burst
        elif len(agents) <= 10:
            return "⫽"  # Parallel
        else:
            return "🔺"  # Hierarchical
    
    def _calculate_confidence(self, agents: Set[str], clusters: List[Set[str]]) -> float:
        """Calculate detection confidence score.
        
        Args:
            agents: Agent set in swarm
            clusters: All detected clusters
            
        Returns:
            Confidence score between 0 and 1
        """
        if not clusters:
            return 0.0
        
        # Count how many algorithms detected this group
        detection_count = 0
        for cluster in clusters:
            overlap = len(agents & cluster) / len(agents)
            if overlap > 0.7:
                detection_count += 1
        
        # Normalize by number of algorithms
        max_detections = len(self.config.algorithms)
        confidence = min(1.0, detection_count / max_detections)
        
        return confidence


# ============================================================================
# Display Management
# ============================================================================

class DisplayManager:
    """Manages terminal output and formatting.
    
    This class handles the formatting and display of log events,
    including buffering, debouncing, and terminal rendering.
    """
    
    def __init__(self, color_manager: ColorManager, config: TailerConfig):
        """Initialize display manager.
        
        Args:
            color_manager: Color management instance
            config: System configuration
        """
        self.color_manager = color_manager
        self.config = config
        self.buffer: List[str] = []
        self.last_flush = time.time()
        self.debounce_ms = 50
        self._lock = asyncio.Lock()
    
    async def display_event(self, event: LogEvent) -> None:
        """Display formatted event to terminal.
        
        Args:
            event: Log event to display
        """
        formatted = await self.format_event(event)
        
        async with self._lock:
            self.buffer.append(formatted)
            
            # Check if should flush
            current_time = time.time()
            if (current_time - self.last_flush) * 1000 >= self.debounce_ms:
                await self.flush_buffer()
    
    async def flush_buffer(self) -> None:
        """Flush buffered output to terminal."""
        if not self.buffer:
            return
        
        # Join all buffered lines
        output = '\n'.join(self.buffer)
        print(output)
        
        # Clear buffer
        self.buffer.clear()
        self.last_flush = time.time()
    
    async def format_event(self, event: LogEvent) -> str:
        """Format event with colors and icons.
        
        Args:
            event: Event to format
            
        Returns:
            Formatted string for display
        """
        # Get agent color
        color = await self.color_manager.assign_color(event.agent_info.agent_id)
        
        # Format timestamp
        timestamp_str = event.entry.timestamp.strftime("%H:%M:%S.%f")[:-3]
        
        # Format agent identifier
        agent_str = f"[{event.agent_info.agent_id[:8]}]"
        if event.swarm_id:
            swarm = self._get_swarm_icon(event.swarm_id)
            agent_str = f"{swarm} {agent_str}"
        
        # Format content
        content = event.entry.content or ""
        if len(content) > 200:
            content = content[:197] + "..."
        
        # Apply formatting
        if self.config.no_color:
            return f"{timestamp_str} {agent_str} {event.entry.type}: {content}"
        else:
            agent_colored = self.color_manager.format_with_color(
                agent_str, 
                event.agent_info.agent_id,
                bold=True
            )
            return f"{timestamp_str} {agent_colored} {event.entry.type}: {content}"
    
    def _get_swarm_icon(self, swarm_id: str) -> str:
        """Get icon for swarm ID."""
        if not self.config.use_emoji:
            return "*"
        
        # Rotate through available icons based on swarm ID
        icons = ["⚡", "→", "⫽", "🔺"]
        try:
            index = int(swarm_id.split('_')[-1]) % len(icons)
            return icons[index]
        except (ValueError, IndexError):
            return "●"


# ============================================================================
# Process Orchestration
# ============================================================================

class ProcessOrchestrator:
    """Manages async processing pipeline and worker coordination.
    
    This class orchestrates the entire processing pipeline,
    managing file monitors, event queues, and worker tasks.
    """
    
    def __init__(self, config: TailerConfig):
        """Initialize process orchestrator.
        
        Args:
            config: System configuration
        """
        self.config = config
        self.file_monitors: Dict[str, FileMonitor] = {}
        self.event_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self.worker_tasks: List[asyncio.Task] = []
        self.semaphore = asyncio.Semaphore(50)  # Limit concurrent operations
        self.swarm_detector = SwarmDetector(SwarmConfig())
        self.parser = LogParser()
        self.running = False
    
    async def discover_files(self, pattern: str) -> List[Path]:
        """Discover log files matching pattern.
        
        Args:
            pattern: Glob pattern for file discovery
            
        Returns:
            List of discovered file paths
        """
        return await FileDiscovery.discover_files(
            self.config.projects_dir,
            pattern,
            self.config.max_files
        )
    
    async def add_monitor(self, file_path: Path) -> None:
        """Add new file to monitoring.
        
        Args:
            file_path: Path to file to monitor
        """
        if str(file_path) in self.file_monitors:
            return
        
        agent_id = FileDiscovery.extract_agent_id(file_path)
        project_path = FileDiscovery.extract_project_path(file_path)
        
        # Create agent info
        agent_info = AgentInfo(
            agent_id=agent_id,
            session_id=f"session_{agent_id}",
            project_path=project_path
        )
        
        # Create and store monitor
        monitor = FileMonitor(file_path, agent_id)
        self.file_monitors[str(file_path)] = monitor
        
        # Start monitoring task
        task = asyncio.create_task(
            self._monitor_file(monitor, agent_info)
        )
        self.worker_tasks.append(task)
    
    async def _monitor_file(self, monitor: FileMonitor, agent_info: AgentInfo) -> None:
        """Monitor single file for changes.
        
        Args:
            monitor: File monitor instance
            agent_info: Associated agent information
        """
        async for line in monitor.tail():
            if not self.running:
                break
            
            # Parse log entry
            entry = self.parser.parse_line(line)
            if entry:
                # Create event
                event = LogEvent(
                    entry=entry,
                    agent_info=agent_info,
                    priority=int(entry.timestamp.timestamp() * 1000)
                )
                
                # Add to queue
                await self.event_queue.put((event.priority, event))
    
    async def process_events(self) -> None:
        """Main event processing loop."""
        batch = []
        batch_timeout = 0.1
        last_batch_time = time.time()
        
        while self.running:
            try:
                # Try to get event with timeout
                priority, event = await asyncio.wait_for(
                    self.event_queue.get(),
                    timeout=batch_timeout
                )
                batch.append(event)
                
                # Check if should process batch
                current_time = time.time()
                if (current_time - last_batch_time >= batch_timeout or 
                    len(batch) >= 10):
                    
                    # Detect swarms in batch
                    swarms = await self.swarm_detector.detect_swarms(batch)
                    
                    # Assign swarm IDs to events
                    for event in batch:
                        for swarm_id, swarm in swarms.items():
                            if event.agent_info.agent_id in swarm.agents:
                                event.swarm_id = swarm_id
                                break
                    
                    # Process batch
                    for event in batch:
                        yield event
                    
                    batch.clear()
                    last_batch_time = current_time
                    
            except asyncio.TimeoutError:
                # Process any pending batch
                if batch:
                    for event in batch:
                        yield event
                    batch.clear()
                    last_batch_time = time.time()
            except Exception as e:
                print(f"Error processing events: {e}", file=sys.stderr)
    
    async def start(self) -> None:
        """Start the orchestrator."""
        self.running = True
        
        # Discover and add monitors
        files = await self.discover_files(self.config.pattern)
        for file_path in files:
            await self.add_monitor(file_path)
    
    async def stop(self) -> None:
        """Stop the orchestrator."""
        self.running = False
        
        # Close all monitors
        for monitor in self.file_monitors.values():
            monitor.close()
        
        # Cancel worker tasks
        for task in self.worker_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self.worker_tasks, return_exceptions=True)


# ============================================================================
# Main Controller
# ============================================================================

class AgentLogTailer:
    """Main controller orchestrating the log tailing system.
    
    This is the primary entry point for the Multi-Agent Log Tailer,
    coordinating all components and managing the system lifecycle.
    """
    
    def __init__(self, config: TailerConfig):
        """Initialize the log tailer.
        
        Args:
            config: System configuration
        """
        self.config = config
        self.orchestrator = ProcessOrchestrator(config)
        self.color_manager = ColorManager(
            scheme=config.color_scheme,
            no_color=config.no_color
        )
        self.display_manager = DisplayManager(self.color_manager, config)
        self.running = False
        self._signal_handlers = []
    
    async def start(self) -> None:
        """Initialize and start the tailing system."""
        print(f"Starting Multi-Agent Log Tailer...")
        print(f"Monitoring: {self.config.projects_dir}")
        print(f"Pattern: {self.config.pattern}")
        print("-" * 60)
        
        self.running = True
        
        # Setup signal handlers
        self._setup_signal_handlers()
        
        # Start orchestrator
        await self.orchestrator.start()
        
        # Main processing loop
        try:
            async for event in self.orchestrator.process_events():
                if not self.running:
                    break
                
                await self.display_manager.display_event(event)
                
        except KeyboardInterrupt:
            print("\nReceived interrupt signal...")
        finally:
            await self.stop()
    
    async def stop(self) -> None:
        """Gracefully shutdown the system."""
        if not self.running:
            return
        
        print("\nShutting down...")
        self.running = False
        
        # Flush any pending output
        await self.display_manager.flush_buffer()
        
        # Stop orchestrator
        await self.orchestrator.stop()
        
        # Cleanup signal handlers
        self._cleanup_signal_handlers()
        
        print("Shutdown complete.")
    
    def _setup_signal_handlers(self) -> None:
        """Setup system signal handlers."""
        def signal_handler(signum, frame):
            self.running = False
        
        for sig in [signal.SIGINT, signal.SIGTERM]:
            old_handler = signal.signal(sig, signal_handler)
            self._signal_handlers.append((sig, old_handler))
    
    def _cleanup_signal_handlers(self) -> None:
        """Restore original signal handlers."""
        for sig, handler in self._signal_handlers:
            signal.signal(sig, handler)
        self._signal_handlers.clear()
    
    async def handle_signals(self) -> None:
        """Handle system signals (async version)."""
        # This method can be used with asyncio signal handling
        # if preferred over traditional signal module
        pass
    
    @classmethod
    def from_args(cls, args: dict) -> 'AgentLogTailer':
        """Create instance from command-line arguments.
        
        Args:
            args: Parsed command-line arguments
            
        Returns:
            Configured AgentLogTailer instance
        """
        config = TailerConfig(
            projects_dir=Path(args.get('projects_dir', '~/.claude/projects')).expanduser(),
            pattern=args.get('pattern', '*.jsonl'),
            include_historical=args.get('include_historical', False),
            max_files=args.get('max_files', 1000),
            poll_interval=args.get('poll_interval', 0.1),
            buffer_size=args.get('buffer_size', 1000),
            color_scheme=args.get('color_scheme', 'default'),
            no_color=args.get('no_color', False),
            use_emoji=args.get('use_emoji', True),
            workers=args.get('workers', 10)
        )
        return cls(config)


# ============================================================================
# Entry Point
# ============================================================================

async def main():
    """Main entry point for the application."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Multi-Agent Log Tailer - Real-time monitoring for Claude Code sessions"
    )
    
    parser.add_argument(
        '--projects-dir',
        type=str,
        default='~/.claude/projects',
        help='Projects directory to monitor'
    )
    
    parser.add_argument(
        '--pattern',
        type=str,
        default='*.jsonl',
        help='File pattern to match'
    )
    
    parser.add_argument(
        '--include-historical',
        action='store_true',
        help='Include historical log entries'
    )
    
    parser.add_argument(
        '--no-color',
        action='store_true',
        help='Disable color output'
    )
    
    parser.add_argument(
        '--color-scheme',
        choices=['default', 'high_contrast', 'colorblind'],
        default='default',
        help='Color scheme to use'
    )
    
    parser.add_argument(
        '--workers',
        type=int,
        default=10,
        help='Number of worker tasks'
    )
    
    args = parser.parse_args()
    
    # Create and start tailer
    tailer = AgentLogTailer.from_args(vars(args))
    await tailer.start()


if __name__ == "__main__":
    asyncio.run(main())