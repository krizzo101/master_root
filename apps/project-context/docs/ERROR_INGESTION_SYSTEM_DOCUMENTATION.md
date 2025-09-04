# Enhanced Error Log Ingestion System

## Complete Implementation Guide and Documentation

### Table of Contents

1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Components](#components)
4. [Configuration](#configuration)
5. [Usage Examples](#usage-examples)
6. [Database Schema](#database-schema)
7. [Performance Tuning](#performance-tuning)
8. [Monitoring & Alerts](#monitoring--alerts)
9. [Troubleshooting](#troubleshooting)
10. [API Reference](#api-reference)
11. [Production Deployment](#production-deployment)

---

## System Overview

The Enhanced Error Log Ingestion System is a comprehensive, intelligent error processing pipeline designed for the Unified Context System. It provides automated error log ingestion, intelligent parsing, classification, correlation detection, and trend analysis.

### Key Features

- **Multi-Format Parsing**: Supports JSON, structured text, and plain text log formats
- **Intelligent Classification**: Automatic error categorization with confidence scoring
- **Stack Trace Analysis**: Multi-language stack trace parsing and analysis
- **Error Deduplication**: Automatic clustering of similar errors
- **Trend Analysis**: Real-time pattern detection and predictive analytics
- **Correlation Detection**: Intelligent linking with Git commits, chat conversations, and code changes
- **Performance Monitoring**: Built-in performance tracking and alerting
- **Real-time Processing**: Streaming ingestion with configurable batching

### Benefits

- **Reduced MTTR**: Faster error resolution through intelligent correlation
- **Proactive Monitoring**: Trend analysis enables early problem detection
- **Cost Optimization**: Error deduplication reduces storage and processing overhead
- **Enhanced Visibility**: Comprehensive error analytics and reporting
- **Developer Productivity**: Automated root cause analysis suggestions

---

## Architecture

### High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Log Sources   │────│  Error Adapter  │────│   Database      │
│                 │    │                 │    │                 │
│ • JSON Logs     │    │ • Multi-format  │    │ • Context Items │
│ • Text Logs     │    │   Parsing       │    │ • Error Clusters│
│ • API Streams   │    │ • Classification│    │ • Patterns      │
│ • Monitoring    │    │ • Correlation   │    │ • Correlations  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │  Intelligence   │
                       │                 │
                       │ • Trend Analysis│
                       │ • Deduplication │
                       │ • Performance   │
                       │   Monitoring    │
                       └─────────────────┘
```

### Component Architecture

```
EnhancedErrorAdapter
├── LogFormatDetector
├── StackTraceParser
├── ErrorClassifier
├── TrendAnalyzer
├── ErrorDeduplicator
├── PerformanceMonitor
├── CorrelationEngine
└── DataTransformer
```

---

## Components

### 1. EnhancedErrorAdapter

**Primary Component**: The main orchestrator that coordinates all error processing activities.

```python
from src.project_context.ingestion.adapters.enhanced_error_adapter import EnhancedErrorAdapter
from src.project_context.ingestion.base_adapter import AdapterConfig, BatchMode

config = AdapterConfig(
    adapter_id="production_error_adapter",
    source_type="error",
    batch_mode=BatchMode.STREAMING,
    batch_size=50,
    source_config={
        "input_sources": ["logs", "realtime", "monitoring"],
        "log_directories": ["./logs", "/var/log/app"],
        "log_file_patterns": ["*.log", "*.err", "error*.log"],
        "enable_error_classification": True,
        "enable_pattern_detection": True,
        "enable_correlation_detection": True,
    }
)

adapter = EnhancedErrorAdapter(config)
```

### 2. LogFormatDetector

**Purpose**: Automatically detects log format types for appropriate parsing.

**Supported Formats**:
- **JSON**: Structured JSON log entries
- **Structured**: Traditional syslog-style entries
- **Plain**: Unstructured text logs

**Example Usage**:
```python
detector = LogFormatDetector()
format_type = detector.detect_format('{"timestamp": "2024-01-01", "level": "ERROR"}')
# Returns: "json"
```

### 3. StackTraceParser

**Purpose**: Parses stack traces from multiple programming languages.

**Supported Languages**:
- Python
- Java
- JavaScript/TypeScript
- C#
- Ruby
- Go

**Example Usage**:
```python
parser = StackTraceParser()
stack_trace = '''
Traceback (most recent call last):
  File "/app/main.py", line 25, in process_data
    result = calculate_value(data)
ZeroDivisionError: division by zero
'''
elements = parser.parse_stack_trace(stack_trace)
# Returns: List[StackTraceElement]
```

### 4. ErrorClassifier

**Purpose**: Automatically categorizes errors based on content and patterns.

**Categories**:
- **Network**: Connection, timeout, DNS issues
- **Database**: SQL errors, connection pool, deadlocks
- **Memory**: Out of memory, heap errors, GC pressure
- **Security**: Authentication, authorization, access violations
- **Performance**: Timeouts, rate limits, slow queries
- **Filesystem**: File not found, permission errors
- **Syntax**: Parse errors, invalid syntax
- **Runtime**: Null pointer, array bounds, division by zero

### 5. TrendAnalyzer

**Purpose**: Analyzes error patterns over time for trend detection and prediction.

**Features**:
- Linear regression-based trend calculation
- Configurable time windows
- Severity scoring
- Future volume prediction

**API**:
```python
analyzer = TrendAnalyzer(time_window_hours=24)
analyzer.update_pattern_frequency("pattern_001", datetime.now(), 3)
trending = analyzer.get_trending_patterns(min_frequency=5, limit=10)
prediction = analyzer.predict_future_occurrences("pattern_001", hours_ahead=2)
```

### 6. ErrorDeduplicator

**Purpose**: Clusters similar errors to reduce noise and storage overhead.

**Algorithm**: Content-based similarity matching with configurable thresholds.

**Features**:
- Error signature generation
- Similarity calculation
- Automatic cluster management
- Representative error selection

### 7. PerformanceMonitor

**Purpose**: Monitors adapter performance and generates alerts.

**Metrics Tracked**:
- Processing time per error
- Error processing rate
- Memory usage
- Parsing failure rate
- Correlation failure rate

**Alert Types**:
- High processing time
- High error rate
- Memory usage warnings
- Failure rate thresholds

### 8. CorrelationEngine

**Purpose**: Detects relationships between errors and other context items.

**Correlation Types**:
- **Git Commits**: Links errors to recent code changes
- **Chat Discussions**: Connects errors to developer conversations
- **Code Locations**: Associates errors with specific code sections
- **Similar Errors**: Groups related error instances

---

## Configuration

### Basic Configuration

```python
config = AdapterConfig(
    adapter_id="error_adapter",
    source_type="error",
    batch_mode=BatchMode.STREAMING,  # or BATCH, MICRO_BATCH
    batch_size=100,
    source_config={
        # Input Sources
        "input_sources": ["logs", "realtime", "api", "monitoring"],
        "log_directories": ["./logs", "./log", "/var/log"],
        "log_file_patterns": ["*.log", "*.err", "error*.log"],
        "watch_directories": True,
        "realtime_processing": True,

        # Parsing Configuration
        "supported_formats": ["json", "structured", "plain"],
        "auto_detect_format": True,
        "extract_stack_traces": True,
        "parse_multiline_errors": True,
        "multiline_timeout_seconds": 5,

        # Classification
        "enable_error_classification": True,
        "enable_severity_scoring": True,
        "severity_keywords": {
            "critical": ["fatal", "critical", "crash", "panic"],
            "high": ["error", "err", "exception", "fail"],
            "medium": ["warn", "warning", "caution"],
            "low": ["info", "debug", "trace"]
        },

        # Pattern Detection
        "enable_pattern_detection": True,
        "pattern_similarity_threshold": 0.8,
        "pattern_frequency_threshold": 3,
        "pattern_time_window_hours": 24,

        # Correlation
        "enable_correlation_detection": True,
        "correlation_window_hours": 2,
        "git_correlation_enabled": True,
        "chat_correlation_enabled": True,
        "code_correlation_enabled": True,

        # Performance
        "max_file_size_mb": 100,
        "max_stack_trace_length": 10000,
        "max_error_age_days": 30,
        "batch_processing_timeout": 60,

        # Filtering
        "exclude_patterns": [
            r".*DEBUG.*",
            r".*health.*check.*",
            r".*heartbeat.*"
        ],
        "severity_filters": ["error", "warning"],
        "min_message_length": 10,
        "max_message_length": 10000,
    }
)
```

### Environment-Specific Configurations

#### Development Environment
```python
dev_config = {
    "log_directories": ["./dev-logs"],
    "realtime_processing": False,
    "enable_correlation_detection": False,
    "batch_size": 20,
}
```

#### Production Environment
```python
prod_config = {
    "log_directories": ["/var/log/app", "/opt/app/logs"],
    "realtime_processing": True,
    "enable_correlation_detection": True,
    "batch_size": 100,
    "max_file_size_mb": 500,
}
```

---

## Usage Examples

### 1. Basic Error Processing

```python
import asyncio
from datetime import datetime, timedelta

async def basic_error_processing():
    # Initialize adapter
    adapter = EnhancedErrorAdapter(config)
    await adapter.initialize()

    try:
        # Process recent errors
        since = datetime.now() - timedelta(hours=1)
        async for raw_error in adapter.fetch_items(since=since, limit=100):
            # Transform to context item
            context_item = await adapter.transform_item(raw_error)

            # Process the context item
            print(f"Processed error: {context_item.title}")
            print(f"  Severity: {context_item.severity}")
            print(f"  File: {context_item.file_path}")
            print(f"  Cluster: {context_item.metrics.get('cluster_id')}")

    finally:
        await adapter.cleanup()

asyncio.run(basic_error_processing())
```

### 2. Real-time Error Monitoring

```python
async def realtime_monitoring():
    adapter = EnhancedErrorAdapter(config)
    await adapter.initialize()

    try:
        while True:
            # Process new errors
            async for raw_error in adapter.fetch_items(limit=10):
                context_item = await adapter.transform_item(raw_error)

                # Check for high-severity errors
                if context_item.severity == "critical":
                    await send_alert(context_item)

                # Check for trending patterns
                trending = await adapter.get_trending_errors(limit=5)
                if trending:
                    await analyze_trends(trending)

            # Wait before next check
            await asyncio.sleep(60)

    finally:
        await adapter.cleanup()
```

### 3. Error Analysis and Reporting

```python
async def generate_error_report():
    adapter = EnhancedErrorAdapter(config)
    await adapter.initialize()

    try:
        # Get comprehensive statistics
        stats = await adapter.get_adapter_statistics()

        # Get error clusters
        clusters = await adapter.get_error_clusters(limit=20)

        # Get trending patterns
        trending = await adapter.get_trending_errors(limit=10)

        # Get performance alerts
        alerts = await adapter.get_performance_alerts(minutes=60)

        # Generate report
        report = {
            "timestamp": datetime.now(),
            "total_errors": stats["total_errors_processed"],
            "performance": stats["performance_stats"],
            "clusters": len(clusters),
            "trending_patterns": len(trending),
            "active_alerts": len(alerts),
            "top_clusters": clusters[:5],
            "trending_errors": trending,
            "recent_alerts": alerts
        }

        return report

    finally:
        await adapter.cleanup()
```

### 4. Custom Error Processing Pipeline

```python
class CustomErrorProcessor:
    def __init__(self):
        self.adapter = EnhancedErrorAdapter(config)
        self.notification_service = NotificationService()
        self.metrics_collector = MetricsCollector()

    async def process_error_batch(self, batch_size: int = 50):
        await self.adapter.initialize()

        try:
            batch = []
            async for raw_error in self.adapter.fetch_items(limit=batch_size):
                context_item = await self.adapter.transform_item(raw_error)
                batch.append(context_item)

            # Process batch
            await self._analyze_batch(batch)
            await self._update_metrics(batch)
            await self._check_alerts(batch)

        finally:
            await self.adapter.cleanup()

    async def _analyze_batch(self, batch):
        # Custom analysis logic
        for item in batch:
            if self._is_critical_error(item):
                await self.notification_service.send_alert(item)

    async def _update_metrics(self, batch):
        # Update custom metrics
        self.metrics_collector.record_batch_processed(len(batch))

    async def _check_alerts(self, batch):
        # Check for performance alerts
        alerts = await self.adapter.get_performance_alerts()
        for alert in alerts:
            await self.notification_service.send_performance_alert(alert)
```

---

## Database Schema

### Core Tables

#### context_items (Enhanced)
```sql
-- Additional columns for error processing
ALTER TABLE context_items ADD COLUMN IF NOT EXISTS error_signature TEXT;
ALTER TABLE context_items ADD COLUMN IF NOT EXISTS cluster_id VARCHAR(255);
ALTER TABLE context_items ADD COLUMN IF NOT EXISTS pattern_signature TEXT;
ALTER TABLE context_items ADD COLUMN IF NOT EXISTS correlation_score FLOAT DEFAULT 0.0;
ALTER TABLE context_items ADD COLUMN IF NOT EXISTS is_duplicate BOOLEAN DEFAULT FALSE;
```

#### error_clusters
```sql
CREATE TABLE error_clusters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cluster_id VARCHAR(255) UNIQUE NOT NULL,
    signature TEXT NOT NULL,
    error_count INTEGER DEFAULT 1,
    first_seen TIMESTAMPTZ DEFAULT NOW(),
    last_seen TIMESTAMPTZ DEFAULT NOW(),
    representative_error_id UUID REFERENCES context_items(id),
    severity_distribution JSONB DEFAULT '{}',
    trend_data JSONB DEFAULT '{}'
);
```

#### error_patterns
```sql
CREATE TABLE error_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern_id VARCHAR(255) UNIQUE NOT NULL,
    pattern_signature TEXT NOT NULL,
    frequency_count INTEGER DEFAULT 1,
    trend_slope FLOAT DEFAULT 0.0,
    trend_direction VARCHAR(20) DEFAULT 'stable',
    severity_score FLOAT DEFAULT 0.0,
    hourly_counts JSONB DEFAULT '{}'
);
```

#### error_correlations
```sql
CREATE TABLE error_correlations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_error_id UUID NOT NULL REFERENCES context_items(id),
    target_item_id UUID NOT NULL REFERENCES context_items(id),
    correlation_type VARCHAR(50) NOT NULL,
    correlation_strength FLOAT NOT NULL,
    detection_method VARCHAR(50) NOT NULL,
    validation_status VARCHAR(20) DEFAULT 'pending'
);
```

### Indexes for Performance

```sql
-- Error-specific indexes
CREATE INDEX idx_context_items_error_signature ON context_items(error_signature);
CREATE INDEX idx_context_items_cluster_id ON context_items(cluster_id);
CREATE INDEX idx_error_clusters_signature ON error_clusters(signature);
CREATE INDEX idx_error_patterns_frequency ON error_patterns(frequency_count DESC);
CREATE INDEX idx_error_correlations_strength ON error_correlations(correlation_strength DESC);
```

### Analytics Functions

#### Error Trend Analysis
```sql
CREATE OR REPLACE FUNCTION analyze_error_trends(
    time_window_hours INTEGER DEFAULT 24,
    min_frequency INTEGER DEFAULT 3
)
RETURNS TABLE (
    pattern_id VARCHAR(255),
    frequency_count INTEGER,
    trend_slope FLOAT,
    prediction_next_hour FLOAT
) AS $$
    SELECT
        pattern_id,
        frequency_count,
        trend_slope,
        GREATEST(0, frequency_per_hour + trend_slope) as prediction_next_hour
    FROM error_patterns
    WHERE frequency_count >= min_frequency
      AND last_occurrence > NOW() - INTERVAL '1 hour' * time_window_hours
    ORDER BY severity_score DESC;
$$;
```

#### Cluster Analysis
```sql
CREATE OR REPLACE FUNCTION get_error_cluster_analysis()
RETURNS TABLE (
    cluster_id VARCHAR(255),
    error_count INTEGER,
    avg_severity FLOAT,
    trend_direction VARCHAR(20)
) AS $$
    SELECT
        cluster_id,
        error_count,
        (trend_data->>'avg_severity')::FLOAT as avg_severity,
        (trend_data->>'trend_direction')::VARCHAR(20) as trend_direction
    FROM error_clusters
    WHERE error_count >= 2
    ORDER BY error_count DESC;
$$;
```

---

## Performance Tuning

### Configuration Optimization

#### High-Volume Environments
```python
high_volume_config = {
    "batch_mode": BatchMode.BATCH,
    "batch_size": 500,
    "batch_processing_timeout": 120,
    "max_concurrent_batches": 10,
    "pattern_similarity_threshold": 0.9,  # Higher for faster processing
    "enable_correlation_detection": False,  # Disable for performance
}
```

#### Memory-Constrained Environments
```python
memory_optimized_config = {
    "batch_size": 20,
    "max_file_size_mb": 50,
    "pattern_time_window_hours": 12,
    "max_error_age_days": 7,
    "exclude_patterns": [r".*DEBUG.*", r".*TRACE.*"],  # Filter more aggressively
}
```

### Database Optimization

#### Index Optimization
```sql
-- Composite indexes for common queries
CREATE INDEX idx_context_items_error_composite
    ON context_items(source_type, severity, timestamp DESC)
    WHERE source_type = 'error';

CREATE INDEX idx_error_patterns_trending
    ON error_patterns(trend_direction, severity_score DESC)
    WHERE trend_direction = 'increasing';
```

#### Partitioning Strategy
```sql
-- Partition error_patterns by time
CREATE TABLE error_patterns_y2024m01 PARTITION OF error_patterns
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

### Processing Optimization

#### Async Processing
```python
async def optimized_processing():
    semaphore = asyncio.Semaphore(10)  # Limit concurrent processing

    async def process_item(raw_error):
        async with semaphore:
            return await adapter.transform_item(raw_error)

    # Process in parallel
    tasks = []
    async for raw_error in adapter.fetch_items(limit=100):
        task = asyncio.create_task(process_item(raw_error))
        tasks.append(task)

    results = await asyncio.gather(*tasks)
    return results
```

#### Memory Management
```python
# Enable memory monitoring
config.source_config.update({
    "max_memory_mb": 1024,
    "memory_check_interval_seconds": 30,
    "auto_cleanup_on_memory_pressure": True
})
```

---

## Monitoring & Alerts

### Built-in Performance Monitoring

The adapter includes comprehensive performance monitoring:

```python
# Get current performance stats
stats = await adapter.get_adapter_statistics()
print(f"Processing rate: {stats['performance_stats']['current_processing_rate']} errors/sec")
print(f"Average time: {stats['performance_stats']['avg_processing_time_ms']}ms")
print(f"Memory usage: {stats['performance_stats']['current_memory_mb']}MB")
```

### Alert Configuration

```python
# Configure custom alert thresholds
adapter.performance_monitor.alert_thresholds.update({
    'max_processing_time_ms': 3000,
    'max_errors_per_minute': 200,
    'max_memory_usage_mb': 1024,
    'max_parsing_failure_rate': 0.05,
})
```

### Integration with External Monitoring

#### Prometheus Integration
```python
from prometheus_client import Counter, Histogram, Gauge

errors_processed = Counter('error_adapter_processed_total', 'Total errors processed')
processing_time = Histogram('error_adapter_processing_seconds', 'Processing time')
memory_usage = Gauge('error_adapter_memory_bytes', 'Memory usage')

class PrometheusMonitoringAdapter(EnhancedErrorAdapter):
    async def transform_item(self, raw_item):
        start_time = time.time()
        result = await super().transform_item(raw_item)

        # Record metrics
        errors_processed.inc()
        processing_time.observe(time.time() - start_time)
        memory_usage.set(self.performance_monitor.get_performance_stats().get('current_memory_mb', 0) * 1024 * 1024)

        return result
```

#### Grafana Dashboard Queries
```promql
# Error processing rate
rate(error_adapter_processed_total[5m])

# Average processing time
rate(error_adapter_processing_seconds_sum[5m]) / rate(error_adapter_processing_seconds_count[5m])

# Memory usage trend
error_adapter_memory_bytes
```

### Health Checks

```python
async def health_check():
    try:
        # Check adapter health
        health = await adapter.health_check()

        # Check recent alerts
        alerts = await adapter.get_performance_alerts(minutes=5)
        critical_alerts = [a for a in alerts if a['severity'] == 'critical']

        return {
            "status": "healthy" if health["is_healthy"] and not critical_alerts else "unhealthy",
            "adapter_status": health["status"],
            "error_count": health["error_count"],
            "processing_rate": health["metrics"]["current_processing_rate"],
            "critical_alerts": len(critical_alerts)
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

---

## Troubleshooting

### Common Issues

#### 1. High Memory Usage

**Symptoms**: Memory usage alerts, slow processing
**Causes**: Large log files, inefficient parsing, memory leaks
**Solutions**:
```python
# Reduce batch size
config.batch_size = 20

# Limit file size
config.source_config["max_file_size_mb"] = 50

# Enable aggressive cleanup
config.source_config["auto_cleanup_on_memory_pressure"] = True
```

#### 2. Slow Processing

**Symptoms**: High processing times, backlog buildup
**Causes**: Complex correlations, large stack traces, database bottlenecks
**Solutions**:
```python
# Disable expensive features
config.source_config["enable_correlation_detection"] = False

# Increase parallelism
config.max_concurrent_batches = 5

# Optimize parsing
config.source_config["max_stack_trace_length"] = 5000
```

#### 3. Parsing Failures

**Symptoms**: High parsing failure rate alerts
**Causes**: Unsupported log formats, encoding issues, malformed logs
**Solutions**:
```python
# Add custom patterns
config.source_config["custom_log_patterns"] = [
    r"(?P<timestamp>\\d{4}-\\d{2}-\\d{2}).*(?P<level>ERROR|WARN).*(?P<message>.*)"
]

# Handle encoding issues
config.source_config["encoding"] = "utf-8"
config.source_config["encoding_errors"] = "ignore"
```

#### 4. Correlation Issues

**Symptoms**: Low correlation detection, correlation failures
**Causes**: Database connectivity, timeout issues, data inconsistency
**Solutions**:
```python
# Increase timeouts
config.source_config["correlation_timeout_seconds"] = 30

# Reduce correlation window
config.source_config["correlation_window_hours"] = 1

# Add retry logic
config.max_retries = 3
config.retry_delay_seconds = 2.0
```

### Debug Logging

Enable detailed logging for troubleshooting:

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('enhanced_error_adapter')
logger.setLevel(logging.DEBUG)

# Enable adapter-specific debug options
config.source_config.update({
    "debug_parsing": True,
    "debug_correlation": True,
    "debug_performance": True,
    "log_raw_errors": True
})
```

### Performance Diagnostics

```python
async def diagnose_performance():
    adapter = EnhancedErrorAdapter(config)
    await adapter.initialize()

    # Run diagnostic processing
    start_time = time.time()
    error_count = 0

    async for raw_error in adapter.fetch_items(limit=100):
        item_start = time.time()
        context_item = await adapter.transform_item(raw_error)
        item_time = time.time() - item_start

        error_count += 1

        if item_time > 1.0:  # Log slow items
            logger.warning(f"Slow processing: {item_time:.2f}s for {context_item.title}")

    total_time = time.time() - start_time
    avg_time = total_time / error_count if error_count > 0 else 0

    print(f"Processed {error_count} errors in {total_time:.2f}s")
    print(f"Average time per error: {avg_time:.3f}s")

    # Get detailed stats
    stats = await adapter.get_adapter_statistics()
    print(f"Performance stats: {stats['performance_stats']}")

    await adapter.cleanup()
```

---

## API Reference

### EnhancedErrorAdapter

#### Core Methods

```python
class EnhancedErrorAdapter(BaseAdapter):
    async def initialize() -> None
    async def fetch_items(since=None, until=None, limit=None) -> AsyncIterator[Dict]
    async def transform_item(raw_item: Dict) -> ContextItem
    async def detect_relationships(item: ContextItem, context_window: List[ContextItem]) -> List[tuple]
    async def cleanup() -> None
```

#### Intelligence API

```python
# Trend Analysis
async def get_trending_errors(limit: int = 20) -> List[Dict[str, Any]]
async def predict_error_volume(pattern_id: str, hours_ahead: int = 1) -> float

# Clustering
async def get_error_clusters(limit: int = 50) -> List[Dict[str, Any]]

# Performance
async def get_adapter_statistics() -> Dict[str, Any]
async def get_performance_alerts(minutes: int = 15) -> List[Dict[str, Any]]

# Patterns
async def get_error_patterns() -> List[Dict[str, Any]]
```

### TrendAnalyzer

```python
class TrendAnalyzer:
    def __init__(time_window_hours: int = 24)
    def update_pattern_frequency(pattern_id: str, timestamp: datetime, count: int = 1) -> None
    def get_trending_patterns(min_frequency: int = 3, limit: int = 20) -> List[Dict[str, Any]]
    def predict_future_occurrences(pattern_id: str, hours_ahead: int = 1) -> float
```

### ErrorDeduplicator

```python
class ErrorDeduplicator:
    def __init__(similarity_threshold: float = 0.8)
    def find_or_create_cluster(parsed_error: ParsedError) -> str
    def get_cluster_info(cluster_id: str) -> Optional[Dict[str, Any]]
    def get_all_clusters() -> List[Dict[str, Any]]
```

### PerformanceMonitor

```python
class PerformanceMonitor:
    def record_processing_time(processing_time_ms: float) -> None
    def record_error_count(timestamp: datetime, count: int = 1) -> None
    def record_memory_usage(memory_mb: float) -> None
    def get_performance_stats() -> Dict[str, Any]
    def get_recent_alerts(minutes: int = 15) -> List[Dict[str, Any]]
```

---

## Production Deployment

### Prerequisites

1. **Python 3.9+** with required dependencies
2. **PostgreSQL 13+** with TimescaleDB and pgvector extensions
3. **Redis** (optional, for caching)
4. **Monitoring system** (Prometheus/Grafana recommended)

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run database migrations
psql -d your_database -f migrations/005_enhanced_error_log_schema.sql

# Verify installation
python validate_enhanced_error_adapter.py --verbose
```

### Configuration Management

#### Environment Variables
```bash
export ERROR_ADAPTER_CONFIG_PATH="/etc/error-adapter/config.yaml"
export ERROR_ADAPTER_LOG_LEVEL="INFO"
export ERROR_ADAPTER_DB_URL="postgresql://user:pass@localhost/db"
export ERROR_ADAPTER_REDIS_URL="redis://localhost:6379"
```

#### Configuration File (`config.yaml`)
```yaml
adapter:
  id: "production_error_adapter"
  source_type: "error"
  batch_mode: "streaming"
  batch_size: 100

sources:
  log_directories:
    - "/var/log/app"
    - "/opt/application/logs"
  log_file_patterns:
    - "*.log"
    - "*.err"
    - "error*.log"
  realtime_processing: true

intelligence:
  enable_error_classification: true
  enable_pattern_detection: true
  enable_correlation_detection: true
  pattern_similarity_threshold: 0.8
  pattern_time_window_hours: 24

performance:
  max_file_size_mb: 100
  max_concurrent_batches: 5
  batch_processing_timeout: 60
  memory_check_interval_seconds: 30

monitoring:
  prometheus_enabled: true
  metrics_port: 9090
  health_check_port: 8080
```

### Deployment Strategies

#### 1. Standalone Deployment

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ ./src/
COPY config/ ./config/

CMD ["python", "-m", "src.project_context.ingestion.adapters.enhanced_error_adapter"]
```

#### 2. Kubernetes Deployment

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: error-adapter
spec:
  replicas: 3
  selector:
    matchLabels:
      app: error-adapter
  template:
    metadata:
      labels:
        app: error-adapter
    spec:
      containers:
      - name: error-adapter
        image: error-adapter:latest
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        env:
        - name: DB_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
        volumeMounts:
        - name: log-volume
          mountPath: /var/log/app
        - name: config-volume
          mountPath: /etc/error-adapter
      volumes:
      - name: log-volume
        hostPath:
          path: /var/log/app
      - name: config-volume
        configMap:
          name: error-adapter-config
```

#### 3. Service Configuration

```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: error-adapter-service
spec:
  selector:
    app: error-adapter
  ports:
  - name: metrics
    port: 9090
    targetPort: 9090
  - name: health
    port: 8080
    targetPort: 8080
```

### Monitoring Setup

#### Prometheus Configuration
```yaml
# prometheus.yml
scrape_configs:
- job_name: 'error-adapter'
  static_configs:
  - targets: ['error-adapter-service:9090']
  metrics_path: /metrics
  scrape_interval: 30s
```

#### Grafana Dashboard
```json
{
  "dashboard": {
    "title": "Error Adapter Dashboard",
    "panels": [
      {
        "title": "Error Processing Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(error_adapter_processed_total[5m])",
            "legendFormat": "Errors/sec"
          }
        ]
      },
      {
        "title": "Processing Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, error_adapter_processing_seconds_bucket)",
            "legendFormat": "95th percentile"
          }
        ]
      }
    ]
  }
}
```

### Scaling Considerations

#### Horizontal Scaling
- Deploy multiple adapter instances
- Use message queue for load distribution
- Implement leader election for coordination

#### Vertical Scaling
- Increase memory limits for large log files
- Scale CPU for complex correlation processing
- Optimize database connection pooling

### Maintenance

#### Regular Tasks
```bash
# Daily cleanup
python -c "
import asyncio
from your_adapter import cleanup_old_patterns
asyncio.run(cleanup_old_patterns(days=30))
"

# Weekly performance analysis
python -c "
import asyncio
from your_adapter import generate_performance_report
asyncio.run(generate_performance_report())
"

# Monthly correlation validation
python -c "
import asyncio
from your_adapter import validate_correlations
asyncio.run(validate_correlations())
"
```

#### Backup Procedures
```sql
-- Backup error patterns
COPY error_patterns TO '/backup/error_patterns.csv' CSV HEADER;

-- Backup clusters
COPY error_clusters TO '/backup/error_clusters.csv' CSV HEADER;

-- Backup correlations
COPY error_correlations TO '/backup/error_correlations.csv' CSV HEADER;
```

---

## Conclusion

The Enhanced Error Log Ingestion System provides a comprehensive, production-ready solution for intelligent error processing and analysis. With its advanced features like trend analysis, automatic correlation detection, and performance monitoring, it significantly improves error resolution times and system reliability.

For additional support or questions, please refer to the troubleshooting section or contact the development team.

---

**Last Updated**: January 2024
**Version**: 1.0.0
**Authors**: Unified Context System Development Team
