# Ingestion Pipeline Architecture

## Overview

The Unified Context System ingestion pipeline provides a sophisticated, pluggable architecture for ingesting data from various sources (chat, code, git, errors) into the unified PostgreSQL + Neo4j backend. The system is designed for high-throughput, fault-tolerant data processing with comprehensive monitoring and relationship detection.

## Architecture Principles

### 1. Pluggable Adapter Design
- **Base Adapter Interface**: All adapters implement `BaseAdapter` abstract class
- **Standard Lifecycle**: Initialize → Fetch → Transform → Validate → Store
- **Configuration-Driven**: Each adapter configured via `AdapterConfig` dataclass
- **Hot-Swappable**: Adapters can be added/removed/updated at runtime

### 2. Temporal Knowledge Graph Integration
- **Automatic Relationship Detection**: Adapters detect relationships during ingestion
- **Temporal Correlation**: Time-based relationship analysis between items
- **Cross-Source Relationships**: Relationships detected across different data sources
- **Confidence Scoring**: All relationships include confidence scores for validation

### 3. Performance and Scalability
- **Async Processing**: Fully asynchronous pipeline using `asyncio`
- **Batch Processing**: Multiple batch modes (streaming, micro-batch, batch, bulk)
- **Concurrent Adapters**: Multiple adapters run simultaneously with rate limiting
- **Error Recovery**: Comprehensive error handling with automatic retry logic

## Core Components

### BaseAdapter Abstract Interface

```python
class BaseAdapter(ABC):
    """Abstract base class for all ingestion adapters."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize adapter resources."""

    @abstractmethod
    async def fetch_items(self, since, until, limit) -> AsyncIterator[Dict]:
        """Fetch raw items from data source."""

    @abstractmethod
    async def transform_item(self, raw_item: Dict) -> ContextItem:
        """Transform raw item into ContextItem."""

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up adapter resources."""
```

**Key Features:**
- **Health Monitoring**: Built-in health checks and metrics collection
- **Rate Limiting**: Configurable processing rates and concurrency limits
- **Retry Logic**: Exponential backoff retry for transient failures
- **Status Management**: State tracking (idle, running, paused, error, shutdown)

### IngestionPipeline Coordinator

The main pipeline coordinator manages multiple adapters and provides:

- **Adapter Lifecycle Management**: Start/stop/pause/resume operations
- **Batch Processing Coordination**: Manages batch sizes and commit strategies
- **Health Monitoring**: Continuous health checks with auto-restart capabilities
- **Metrics Collection**: Real-time performance and throughput metrics
- **Failure Recovery**: Automatic adapter restart with backoff periods

### AdapterRegistry Plugin System

```python
class AdapterRegistry:
    """Registry for managing ingestion adapters."""

    def register_adapter(self, adapter_id: str, adapter_class: Type[BaseAdapter],
                        config: AdapterConfig) -> None
    def get_adapter(self, adapter_id: str) -> Optional[BaseAdapter]
    def discover_adapters(self, package_name: str) -> int
```

**Features:**
- **Dynamic Registration**: Runtime adapter registration and discovery
- **Configuration Management**: Centralized adapter configuration
- **Validation**: Adapter validation before registration
- **Metadata Tracking**: Rich metadata about each registered adapter

### DataTransformer Utilities

Common transformation functions used across all adapters:

- **Content Sanitization**: Remove problematic characters and truncate
- **Hash Generation**: SHA-256 content hashing for deduplication
- **Tag Normalization**: Standardized tag format and deduplication
- **Metadata Extraction**: Common metadata field extraction
- **Entity Type Inference**: Smart entity type detection based on content

## Adapter Implementations

### 1. ChatAdapter

**Purpose**: Ingests conversation and chat data from various formats.

**Supported Sources:**
- JSONL conversation logs
- JSON conversation exports
- Real-time chat streams (WebSocket)
- Chat API integrations (Slack, Discord, Teams)

**Key Features:**
- **Conversation Context**: Maintains conversation threading and context
- **Actor Classification**: Distinguishes between human, AI, and system messages
- **Relationship Detection**: Reply chains, thread relationships, temporal proximity
- **Content Extraction**: Message content, metadata, attachments

**Configuration:**
```python
ChatAdapter.default_config():
    input_format: "jsonl"  # jsonl, json, api, stream
    file_patterns: ["*.jsonl", "*.json"]
    watch_directories: []
    include_system_messages: True
    conversation_timeout_minutes: 60
```

### 2. CodeAdapter

**Purpose**: Ingests source code files and IDE integration data.

**Supported Sources:**
- File system scanning with configurable patterns
- IDE change tracking and diagnostics
- Code analysis and metadata extraction
- Function/class/module parsing

**Key Features:**
- **Language Detection**: Automatic programming language identification
- **Code Parsing**: Extract functions, classes, imports, comments
- **Change Tracking**: File modification detection and checksumming
- **Relationship Detection**: Import relationships, directory structure, language grouping

**Configuration:**
```python
CodeAdapter.default_config():
    scan_directories: ["."]
    include_patterns: ["*.py", "*.js", "*.ts", ...]
    exclude_patterns: ["node_modules/**", ".git/**", ...]
    max_file_size_mb: 10
    extract_functions: True
    extract_classes: True
    track_changes: True
```

### 3. GitAdapter

**Purpose**: Ingests version control history and metadata.

**Supported Sources:**
- Git commit history with full metadata
- Branch and tag information
- File change tracking per commit
- Author and committer data

**Key Features:**
- **Commit Analysis**: Full commit message, diff, and metadata parsing
- **Relationship Detection**: Parent-child commit chains, branch relationships, author correlation
- **Change Tracking**: Files modified per commit with change types
- **Diff Integration**: Optional diff content inclusion with size limits

**Configuration:**
```python
GitAdapter.default_config():
    repository_path: "."
    include_commits: True
    include_branches: True
    include_tags: True
    max_commit_age_days: None  # All history
    include_diff_content: True
    max_diff_size_kb: 100
```

### 4. ErrorAdapter

**Purpose**: Ingests error logs, diagnostics, and failure data.

**Supported Sources:**
- Application error logs (various formats)
- IDE diagnostics and warnings
- Test failure reports
- Monitoring alerts and performance issues

**Key Features:**
- **Error Parsing**: Multi-format log parsing with smart extraction
- **Stack Trace Analysis**: Parse and extract location information
- **Error Grouping**: Similar error detection and grouping
- **Relationship Detection**: Error chains, file location relationships, temporal correlation

**Configuration:**
```python
ErrorAdapter.default_config():
    input_sources: ["logs", "ide", "test", "monitor"]
    log_file_patterns: ["*.log", "error*.log", "*.err"]
    severity_filters: ["error", "warning"]
    stack_trace_parsing: True
    group_similar_errors: True
    similarity_threshold: 0.8
```

## Data Flow Architecture

### 1. Ingestion Flow

```
Data Source → Adapter.fetch_items() → Raw Items
    ↓
Raw Items → Adapter.transform_item() → ContextItems
    ↓
ContextItems → DataTransformer.transform_item() → Normalized Items
    ↓
Normalized Items → Validation → Valid Items
    ↓
Valid Items → Relationship Detection → Items + Relationships
    ↓
Items + Relationships → Database Storage → PostgreSQL + Neo4j
```

### 2. Pipeline Coordination

```
IngestionPipeline
├── AdapterRegistry (plugin management)
├── Multiple BaseAdapter instances
│   ├── Async processing loops
│   ├── Health monitoring
│   └── Metrics collection
├── DataTransformer (common utilities)
├── Background tasks
│   ├── Health check loop
│   └── Metrics collection loop
└── Database integration
```

### 3. Error Handling and Recovery

- **Adapter-Level Errors**: Recorded in metrics, trigger health checks
- **Item-Level Failures**: Logged but don't stop batch processing
- **Configuration Errors**: Prevent adapter startup, logged clearly
- **Resource Failures**: Automatic cleanup and restart attempts
- **Pipeline Failures**: Graceful shutdown with resource cleanup

## Configuration System

### AdapterConfig Dataclass

```python
@dataclass
class AdapterConfig:
    # Identification
    adapter_id: str
    source_type: str
    version: str = "1.0"

    # Processing
    batch_mode: BatchMode = BatchMode.STREAMING
    batch_size: int = 100
    max_items_per_second: int = 1000

    # Retry logic
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    retry_backoff_factor: float = 2.0

    # Data processing
    generate_embeddings: bool = True
    generate_summaries: bool = False
    extract_relationships: bool = True

    # Source-specific configuration
    source_config: Dict[str, Any] = field(default_factory=dict)
```

### Pipeline Configuration

```python
class PipelineConfig:
    max_concurrent_adapters: int = 10
    batch_commit_size: int = 1000
    health_check_interval: int = 60
    auto_restart_failed_adapters: bool = True
    pipeline_shutdown_timeout_seconds: int = 60
```

## Monitoring and Metrics

### Adapter Metrics

```python
@dataclass
class AdapterMetrics:
    # Counters
    total_items_processed: int = 0
    total_items_failed: int = 0
    total_errors: int = 0

    # Rates (items/second)
    current_processing_rate: float = 0.0
    average_processing_rate: float = 0.0
    peak_processing_rate: float = 0.0

    # Quality metrics
    duplicate_rate: float = 0.0
    validation_failure_rate: float = 0.0

    # Resource usage
    current_memory_mb: float = 0.0
    current_cpu_percent: float = 0.0
```

### Pipeline Metrics

- **Throughput Tracking**: Items processed per second across all adapters
- **Error Rates**: Failed items and adapter failure counts
- **Health Status**: Real-time adapter health and status
- **Resource Usage**: Memory and CPU consumption monitoring
- **Relationship Quality**: Relationship detection success rates

### Health Checks

- **Adapter Health**: Status, error counts, processing rates
- **Resource Health**: Memory usage, file handles, connections
- **Data Quality**: Validation failure rates, duplicate detection
- **Performance Health**: Processing rate trends, latency metrics

## Usage Examples

### Basic Pipeline Usage

```python
# Initialize components
registry = AdapterRegistry()
transformer = DataTransformer()
pipeline = IngestionPipeline(registry, transformer)

# Register adapters
chat_adapter = ChatAdapter(ChatAdapter.default_config())
code_adapter = CodeAdapter(CodeAdapter.default_config())

registry.register_adapter("chat", ChatAdapter, chat_adapter.config)
registry.register_adapter("code", CodeAdapter, code_adapter.config)

# Start pipeline
async with pipeline.managed_pipeline(["chat", "code"]):
    # Pipeline runs automatically
    await asyncio.sleep(3600)  # Run for 1 hour
# Pipeline stops automatically
```

### Custom Adapter Development

```python
class CustomAdapter(BaseAdapter):
    async def initialize(self):
        # Set up connections, validate config
        pass

    async def fetch_items(self, since=None, until=None, limit=None):
        # Fetch from your data source
        for item in data_source:
            yield item

    async def transform_item(self, raw_item):
        # Transform to ContextItem
        item = self.transformer.create_base_context_item(
            source_type="custom",
            source_id=raw_item["id"],
            raw_data=raw_item
        )
        # Add custom fields...
        return item

    async def cleanup(self):
        # Clean up resources
        pass

# Register and use
config = AdapterConfig(adapter_id="custom", source_type="custom")
registry.register_adapter("custom", CustomAdapter, config)
```

### Runtime Management

```python
# Get pipeline status
status = await pipeline.get_status()
print(f"Pipeline running: {status['pipeline']['running']}")
print(f"Items ingested: {status['pipeline']['total_items_ingested']}")

# Pause/resume specific adapter
await pipeline.pause_adapter("chat")
await pipeline.resume_adapter("chat")

# Monitor health
for adapter_id, adapter_status in status['adapters'].items():
    if not adapter_status['is_healthy']:
        print(f"Unhealthy adapter: {adapter_id}")
```

## Integration Points

### Database Layer

- **Context Items**: Stored in `context_items` table (PostgreSQL)
- **Relationships**: Stored in `context_relationships` table
- **Neo4j Nodes**: Bidirectional linking via `neo4j_node_id`
- **Vector Embeddings**: Generated during transformation, stored in `embedding` column

### MCP Server Integration

- **Real-time Ingestion**: Pipeline integrates with MCP server for real-time data
- **Status Reporting**: Pipeline status exposed via MCP tools
- **Configuration Management**: Adapter configs managed via MCP interface

### Context Bridge Integration

- **IDE Data**: Real-time IDE data flows through Context Bridge to pipeline
- **Change Notifications**: File changes trigger adapter processing
- **Project Context**: IDE project context integrated into code adapter

## Performance Characteristics

### Throughput Targets

- **Chat Adapter**: 100-500 messages/second
- **Code Adapter**: 50-200 files/second
- **Git Adapter**: 200-1000 commits/second
- **Error Adapter**: 500-2000 log entries/second

### Scalability Features

- **Concurrent Processing**: Multiple adapters run simultaneously
- **Batch Optimization**: Configurable batch sizes for optimal throughput
- **Memory Management**: Streaming processing to minimize memory usage
- **Connection Pooling**: Efficient database connection management

### Resource Requirements

- **Memory**: 512MB-2GB depending on batch sizes and concurrent adapters
- **CPU**: 2-4 cores for optimal performance with multiple adapters
- **Network**: Minimal network usage except for API-based adapters
- **Storage**: Efficient storage with deduplication and compression

## Future Enhancements

### Phase 2 Roadmap

1. **Advanced Adapters**:
   - Slack/Discord/Teams API integrations
   - Jira/GitHub Issues adapter
   - Database query log adapter
   - Application performance monitoring adapter

2. **AI-Powered Features**:
   - Automatic relationship detection using ML models
   - Content summarization and key phrase extraction
   - Anomaly detection in error patterns
   - Intelligent data classification

3. **Scalability Improvements**:
   - Horizontal scaling with multiple pipeline instances
   - Message queue integration (Apache Kafka/RabbitMQ)
   - Distributed processing with worker pools
   - Cloud-native deployment options

4. **Advanced Monitoring**:
   - Grafana/Prometheus integration
   - Custom alerting rules
   - Performance optimization recommendations
   - Data quality scoring and reporting

---

This ingestion pipeline architecture provides a robust, scalable foundation for the Unified Context System, enabling high-quality data ingestion from diverse sources while maintaining excellent performance and reliability characteristics.
