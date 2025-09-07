# Multi-Agent Log Tailer Architecture Design

## System Overview

The Multi-Agent Log Tailer is an asynchronous, event-driven system designed to monitor and analyze Claude Code session logs in real-time. It provides intelligent swarm detection, visual formatting, and performance-optimized processing for hundreds of concurrent log files.

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Log Tailer System                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐      │
│  │   CLI Layer  │────▶│  Controller  │────▶│   Display    │      │
│  │              │     │              │     │   Manager    │      │
│  └──────────────┘     └──────────────┘     └──────────────┘      │
│         │                    │                      │              │
│         ▼                    ▼                      ▼              │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐      │
│  │Configuration │     │ Orchestrator │     │   Terminal   │      │
│  │   Manager    │     │              │     │   Renderer   │      │
│  └──────────────┘     └──────────────┘     └──────────────┘      │
│                              │                                     │
│                              ▼                                     │
│  ┌───────────────────────────────────────────────────────┐       │
│  │                  Processing Pipeline                    │       │
│  ├─────────────────────────────────────────────────────────┤       │
│  │                                                         │       │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │       │
│  │  │File Monitor │──▶│Log Parser   │──▶│Event Queue  │   │       │
│  │  └─────────────┘  └─────────────┘  └─────────────┘   │       │
│  │         │                │                  │           │       │
│  │         ▼                ▼                  ▼           │       │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │       │
│  │  │  Position   │  │   Content   │  │   Message   │   │       │
│  │  │   Tracker   │  │  Extractor  │  │  Processor  │   │       │
│  │  └─────────────┘  └─────────────┘  └─────────────┘   │       │
│  │                                             │           │       │
│  └─────────────────────────────────────────────│───────────┘       │
│                                                ▼                   │
│  ┌───────────────────────────────────────────────────────┐       │
│  │                Intelligence Layer                       │       │
│  ├─────────────────────────────────────────────────────────┤       │
│  │                                                         │       │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │       │
│  │  │   Swarm     │  │  Pattern    │  │   Anomaly   │   │       │
│  │  │  Detector   │  │ Recognition │  │  Detection  │   │       │
│  │  └─────────────┘  └─────────────┘  └─────────────┘   │       │
│  │         │                │                  │           │       │
│  │         └────────────────┼──────────────────┘           │       │
│  │                          ▼                              │       │
│  │                 ┌─────────────────┐                    │       │
│  │                 │  Event Emitter  │                    │       │
│  │                 └─────────────────┘                    │       │
│  └───────────────────────────────────────────────────────┘       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Class Definitions and Interfaces

### Core Components

#### 1. LogTailerController
```python
class LogTailerController:
    """Main controller orchestrating the log tailing system"""
    
    def __init__(self, config: TailerConfig):
        self.config = config
        self.orchestrator = ProcessOrchestrator()
        self.display_manager = DisplayManager()
        self.running = False
        
    async def start(self) -> None:
        """Initialize and start the tailing system"""
        
    async def stop(self) -> None:
        """Gracefully shutdown the system"""
        
    async def handle_signals(self) -> None:
        """Handle system signals (SIGINT, SIGTERM)"""
```

#### 2. ProcessOrchestrator
```python
class ProcessOrchestrator:
    """Manages async processing pipeline and worker coordination"""
    
    def __init__(self):
        self.file_monitors: Dict[str, FileMonitor] = {}
        self.event_queue = asyncio.PriorityQueue()
        self.worker_pool: List[asyncio.Task] = []
        self.semaphore = asyncio.Semaphore(50)  # Limit concurrent operations
        
    async def discover_files(self, pattern: str) -> List[Path]:
        """Discover log files matching pattern"""
        
    async def add_monitor(self, file_path: Path) -> None:
        """Add new file to monitoring"""
        
    async def process_events(self) -> None:
        """Main event processing loop"""
```

#### 3. FileMonitor
```python
class FileMonitor:
    """Monitors individual log file for changes"""
    
    def __init__(self, file_path: Path, agent_id: str):
        self.file_path = file_path
        self.agent_id = agent_id
        self.position = 0
        self.last_activity = time.time()
        self.poll_interval = 0.1  # Adaptive polling
        
    async def tail(self) -> AsyncIterator[LogEntry]:
        """Yield new log entries as they appear"""
        
    async def check_rotation(self) -> bool:
        """Check if file has been rotated"""
        
    def update_position(self, new_position: int) -> None:
        """Update and persist file position"""
```

#### 4. LogParser
```python
class LogParser:
    """Parses JSONL format Claude Code logs"""
    
    @staticmethod
    def parse_line(line: str) -> Optional[LogEntry]:
        """Parse single JSONL line into LogEntry"""
        
    @staticmethod
    def validate_entry(entry: dict) -> bool:
        """Validate required fields exist"""
        
    @staticmethod
    def extract_metadata(entry: dict) -> EntryMetadata:
        """Extract metadata from log entry"""
```

#### 5. SwarmDetector
```python
class SwarmDetector:
    """Detects and groups agent swarms"""
    
    def __init__(self, config: SwarmConfig):
        self.time_window = config.time_window  # 5 minutes
        self.min_agents = config.min_agents    # 3 agents
        self.algorithms = self._init_algorithms()
        
    async def detect_swarms(self, events: List[LogEvent]) -> Dict[str, SwarmGroup]:
        """Detect swarms using multiple algorithms"""
        
    def _dbscan_clustering(self, events: List[LogEvent]) -> List[Cluster]:
        """DBSCAN clustering algorithm"""
        
    def _sliding_window(self, events: List[LogEvent]) -> List[Cluster]:
        """Sliding window detection"""
        
    def _directory_grouping(self, events: List[LogEvent]) -> List[Cluster]:
        """Group by project directory"""
```

#### 6. DisplayManager
```python
class DisplayManager:
    """Manages terminal output and formatting"""
    
    def __init__(self, renderer: TerminalRenderer):
        self.renderer = renderer
        self.buffer = []
        self.last_flush = time.time()
        self.debounce_ms = 50
        
    async def display_event(self, event: FormattedEvent) -> None:
        """Display formatted event to terminal"""
        
    async def flush_buffer(self) -> None:
        """Flush buffered output to terminal"""
        
    def format_event(self, event: LogEvent) -> FormattedEvent:
        """Format event with colors and icons"""
```

### Data Models

#### LogEntry
```python
@dataclass
class LogEntry:
    """Parsed log entry"""
    type: str  # user, assistant, system, summary
    timestamp: datetime
    uuid: str
    session_id: str
    agent_id: str
    content: Optional[str]
    tool_use: Optional[ToolUse]
    metadata: Dict[str, Any]
```

#### LogEvent
```python
@dataclass
class LogEvent:
    """Processed log event with context"""
    entry: LogEntry
    agent_info: AgentInfo
    swarm_id: Optional[str]
    priority: int
    formatted_content: str
    
    def __lt__(self, other):
        """For priority queue ordering"""
        return self.entry.timestamp < other.entry.timestamp
```

#### SwarmGroup
```python
@dataclass
class SwarmGroup:
    """Detected swarm grouping"""
    swarm_id: str
    agents: Set[str]
    start_time: datetime
    end_time: Optional[datetime]
    icon: str
    detection_method: str
```

#### TailerConfig
```python
@dataclass
class TailerConfig:
    """System configuration"""
    projects_dir: Path
    pattern: str
    include_historical: bool
    max_files: int = 1000
    poll_interval: float = 0.1
    buffer_size: int = 1000
    color_scheme: str = "default"
    no_color: bool = False
```

## Data Flow Documentation

### 1. Initialization Flow
```
START
  │
  ├─▶ Load Configuration
  │     └─▶ Parse CLI arguments
  │     └─▶ Load config file
  │     └─▶ Apply environment overrides
  │
  ├─▶ Initialize Components
  │     └─▶ Create ProcessOrchestrator
  │     └─▶ Create DisplayManager
  │     └─▶ Initialize SwarmDetector
  │
  ├─▶ Discover Files
  │     └─▶ Scan projects directory
  │     └─▶ Filter by pattern
  │     └─▶ Sort by modification time
  │
  └─▶ Start Monitoring
        └─▶ Create FileMonitors
        └─▶ Start worker tasks
        └─▶ Begin event loop
```

### 2. Event Processing Flow
```
File Change Detected
  │
  ├─▶ FileMonitor.tail()
  │     └─▶ Read new lines
  │     └─▶ Update position
  │
  ├─▶ LogParser.parse_line()
  │     └─▶ Parse JSONL
  │     └─▶ Validate schema
  │     └─▶ Extract metadata
  │
  ├─▶ Create LogEvent
  │     └─▶ Assign priority
  │     └─▶ Add agent context
  │
  ├─▶ Event Queue
  │     └─▶ Priority ordering
  │     └─▶ Chronological merge
  │
  ├─▶ Intelligence Layer
  │     ├─▶ SwarmDetector.detect()
  │     ├─▶ PatternRecognition.analyze()
  │     └─▶ AnomalyDetection.check()
  │
  ├─▶ Message Processing
  │     └─▶ Content extraction
  │     └─▶ Smart truncation
  │     └─▶ Format enhancement
  │
  └─▶ Display Output
        └─▶ Apply formatting
        └─▶ Buffer management
        └─▶ Terminal rendering
```

### 3. Swarm Detection Flow
```
Events Stream
  │
  ├─▶ Time Window Buffer
  │     └─▶ Maintain 5-minute window
  │     └─▶ Remove expired events
  │
  ├─▶ Algorithm Pipeline
  │     ├─▶ DBSCAN Clustering
  │     │     └─▶ Temporal distance matrix
  │     │     └─▶ Density-based grouping
  │     │
  │     ├─▶ Sliding Window
  │     │     └─▶ 30-second windows
  │     │     └─▶ 50% overlap
  │     │
  │     └─▶ Directory Grouping
  │           └─▶ Pattern matching
  │           └─▶ Timestamp proximity
  │
  ├─▶ Consensus Building
  │     └─▶ Merge algorithm results
  │     └─▶ Resolve conflicts
  │
  └─▶ Swarm Assignment
        └─▶ Update agent mappings
        └─▶ Assign swarm icons
        └─▶ Emit swarm events
```

## Error Handling Strategy

### 1. File System Errors
```python
class FileSystemErrorHandler:
    """Handles file system related errors"""
    
    async def handle_permission_error(self, path: Path) -> None:
        """Handle permission denied errors"""
        # Log warning, skip file, continue monitoring others
        
    async def handle_file_rotation(self, monitor: FileMonitor) -> None:
        """Handle log file rotation"""
        # Reset position, reopen file, continue tailing
        
    async def handle_file_deletion(self, monitor: FileMonitor) -> None:
        """Handle file deletion"""
        # Remove monitor, clean up resources
        
    async def handle_network_timeout(self, path: Path) -> None:
        """Handle network filesystem timeouts"""
        # Exponential backoff, retry with limits
```

### 2. Parsing Errors
```python
class ParsingErrorHandler:
    """Handles JSON parsing errors"""
    
    def handle_malformed_json(self, line: str) -> Optional[LogEntry]:
        """Attempt recovery from malformed JSON"""
        # Try to extract partial data
        # Log error with context
        # Return None or partial entry
        
    def handle_missing_fields(self, entry: dict) -> Optional[LogEntry]:
        """Handle entries with missing required fields"""
        # Apply defaults where possible
        # Skip if critical fields missing
        
    def handle_encoding_error(self, data: bytes) -> str:
        """Handle character encoding issues"""
        # Try multiple encodings
        # Replace invalid characters
```

### 3. Performance Degradation
```python
class PerformanceManager:
    """Manages system performance and resource limits"""
    
    async def monitor_resources(self) -> None:
        """Monitor CPU and memory usage"""
        # Track resource metrics
        # Trigger throttling if needed
        
    async def adaptive_throttling(self) -> None:
        """Adjust processing based on load"""
        # Increase poll intervals
        # Reduce buffer sizes
        # Limit concurrent operations
        
    async def handle_queue_overflow(self) -> None:
        """Handle event queue overflow"""
        # Drop oldest events
        # Increase processing workers
        # Alert user to data loss
```

### 4. Recovery Strategies

#### Circuit Breaker Pattern
```python
class CircuitBreaker:
    """Prevents cascading failures"""
    
    def __init__(self, failure_threshold: int = 5, timeout: float = 60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.last_failure = None
        self.state = "closed"  # closed, open, half-open
        
    async def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        if self.state == "open":
            if self._should_attempt_reset():
                self.state = "half-open"
            else:
                raise CircuitOpenError()
                
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
```

#### Graceful Degradation
```python
class GracefulDegradation:
    """Provides fallback behaviors"""
    
    DEGRADATION_LEVELS = [
        "full",      # All features enabled
        "reduced",   # Disable advanced features
        "minimal",   # Core functionality only
        "emergency"  # Bare minimum operation
    ]
    
    async def adjust_features(self, level: str) -> None:
        """Adjust feature set based on degradation level"""
        if level == "reduced":
            # Disable swarm detection
            # Reduce formatting
        elif level == "minimal":
            # Disable colors
            # Simple text output only
        elif level == "emergency":
            # Single file mode
            # No buffering
```

## Async Processing Pipeline

### 1. Worker Pool Architecture
```python
class WorkerPool:
    """Manages async worker tasks"""
    
    def __init__(self, min_workers: int = 5, max_workers: int = 50):
        self.min_workers = min_workers
        self.max_workers = max_workers
        self.workers: List[asyncio.Task] = []
        self.load_balancer = LoadBalancer()
        
    async def scale_workers(self, queue_size: int) -> None:
        """Dynamic worker scaling based on load"""
        target_workers = min(
            max(self.min_workers, queue_size // 10),
            self.max_workers
        )
        await self._adjust_worker_count(target_workers)
        
    async def worker_task(self, worker_id: int) -> None:
        """Individual worker processing loop"""
        while self.running:
            try:
                event = await self.event_queue.get()
                await self.process_event(event)
            except Exception as e:
                await self.error_handler.handle(e)
```

### 2. Event Coalescing
```python
class EventCoalescer:
    """Coalesces rapid events to reduce processing overhead"""
    
    def __init__(self, window_ms: int = 50):
        self.window_ms = window_ms
        self.buffers: Dict[str, List[LogEvent]] = defaultdict(list)
        self.timers: Dict[str, asyncio.Task] = {}
        
    async def add_event(self, event: LogEvent) -> None:
        """Add event to coalescing buffer"""
        key = f"{event.agent_id}:{event.entry.type}"
        self.buffers[key].append(event)
        
        if key not in self.timers:
            self.timers[key] = asyncio.create_task(
                self._flush_after_delay(key)
            )
```

### 3. Backpressure Management
```python
class BackpressureManager:
    """Manages system backpressure"""
    
    def __init__(self):
        self.high_water_mark = 1000
        self.low_water_mark = 500
        self.paused_monitors: Set[FileMonitor] = set()
        
    async def check_pressure(self, queue_size: int) -> None:
        """Check and manage backpressure"""
        if queue_size > self.high_water_mark:
            await self._pause_monitors()
        elif queue_size < self.low_water_mark:
            await self._resume_monitors()
            
    async def _pause_monitors(self) -> None:
        """Pause file monitoring when overwhelmed"""
        for monitor in self.active_monitors:
            if monitor not in self.paused_monitors:
                monitor.pause()
                self.paused_monitors.add(monitor)
```

## Performance Optimizations

### 1. Memory Management
- Stream processing with generators
- Bounded queues and buffers
- Automatic garbage collection triggers
- Memory-mapped file reading for large logs

### 2. CPU Optimization
- Compiled regex patterns
- Lazy evaluation where possible
- Batch processing for similar operations
- Profile-guided optimization points

### 3. I/O Optimization
- Asynchronous file operations
- Buffered reading with optimal chunk sizes
- Event-based monitoring (inotify/kqueue)
- Connection pooling for network filesystems

### 4. Concurrency Optimization
- Semaphore-limited operations
- Lock-free data structures where possible
- Read-write locks for shared state
- Coroutine pooling and reuse

## Testing Strategy

### Unit Test Coverage
```python
# test_file_monitor.py
class TestFileMonitor:
    async def test_tail_new_lines()
    async def test_position_tracking()
    async def test_file_rotation_handling()
    async def test_adaptive_polling()
    
# test_log_parser.py
class TestLogParser:
    def test_parse_valid_json()
    def test_handle_malformed_json()
    def test_extract_tool_use()
    def test_unicode_handling()
    
# test_swarm_detector.py
class TestSwarmDetector:
    async def test_dbscan_clustering()
    async def test_sliding_window()
    async def test_directory_grouping()
    async def test_consensus_building()
```

### Integration Tests
```python
# test_integration.py
class TestIntegration:
    async def test_multi_file_synchronization()
    async def test_event_ordering()
    async def test_swarm_detection_accuracy()
    async def test_graceful_shutdown()
```

### Performance Benchmarks
```python
# benchmark_performance.py
class PerformanceBenchmark:
    async def benchmark_100_files()
    async def benchmark_1000_events_per_second()
    async def benchmark_memory_usage()
    async def benchmark_startup_time()
```

## Deployment Considerations

### 1. Configuration Management
- YAML/JSON configuration files
- Environment variable overrides
- Command-line argument precedence
- Runtime configuration reload

### 2. Monitoring and Metrics
- Prometheus metrics export
- Health check endpoints
- Performance dashboards
- Alert thresholds

### 3. Logging and Debugging
- Structured logging (JSON)
- Log levels per component
- Debug mode with verbose output
- Performance profiling hooks

### 4. Platform Support
- Linux: Full feature set with inotify
- macOS: FSEvents for file monitoring
- Windows: Win32 API for file watching
- WSL: Fallback to polling mode

## Future Enhancements

### Phase 1: Core Improvements
- [ ] Implement inotify/FSEvents support
- [ ] Add plugin architecture
- [ ] Enhance swarm detection algorithms
- [ ] Create web dashboard interface

### Phase 2: Advanced Features
- [ ] Machine learning anomaly detection
- [ ] Distributed monitoring capability
- [ ] Real-time collaboration features
- [ ] Advanced pattern recognition

### Phase 3: Integration
- [ ] Orchestrator system integration
- [ ] Export to monitoring platforms
- [ ] REST API for remote access
- [ ] Kubernetes operator support

## Conclusion

This architecture provides a robust, scalable foundation for the Multi-Agent Log Tailer system. The modular design allows for easy extension and maintenance, while the async processing pipeline ensures high performance even with hundreds of concurrent log files. The error handling and recovery strategies ensure system resilience, and the intelligence layer provides valuable insights through swarm detection and pattern recognition.

The implementation follows best practices for Python async programming and provides clear interfaces for testing and future enhancements. The system is designed to gracefully handle edge cases and degrade functionality when under stress rather than failing completely.