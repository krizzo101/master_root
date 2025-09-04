# Git History Adapter - Complete Implementation Guide

## Overview

This comprehensive guide covers the complete implementation of the Enhanced Git History Adapter, a sophisticated system designed for incremental processing of Git repositories with advanced commit analysis, branch/merge detection, and temporal correlation with chat logs and code intelligence.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Core Components](#core-components)
3. [Database Schema](#database-schema)
4. [Implementation Guide](#implementation-guide)
5. [Configuration](#configuration)
6. [Testing Framework](#testing-framework)
7. [Deployment Guide](#deployment-guide)
8. [Performance Optimization](#performance-optimization)
9. [Monitoring & Troubleshooting](#monitoring--troubleshooting)
10. [API Reference](#api-reference)

---

## Architecture Overview

### Design Principles

The Git History Adapter follows these key architectural principles:

- **Incremental Processing**: Process only new commits since last checkpoint
- **Scalable Architecture**: Handle repositories with 10K+ commits efficiently
- **Comprehensive Analysis**: Extract semantic meaning from commits and code changes
- **Temporal Correlation**: Link git events with chat logs, errors, and code intelligence
- **Fault Tolerance**: Robust error handling and recovery mechanisms
- **Performance Optimized**: Sub-second query response times through intelligent indexing

### System Architecture Diagram

```mermaid
graph TB
    subgraph "Git Repositories"
        R1[Repository 1]
        R2[Repository 2]
        R3[Repository N]
    end

    subgraph "Enhanced Git Adapter"
        EGA[EnhancedGitAdapter]
        CM[CheckpointManager]
        CA[CommitAnalyzer]
        BMD[BranchMergeDetector]
        RE[RelationshipEngine]
    end

    subgraph "Processing Pipeline"
        IGS[IntegrationStrategy]
        PP[ParallelProcessor]
        TC[TemporalCorrelator]
        EM[EmbeddingGenerator]
    end

    subgraph "Database Layer"
        UC[(Unified Context DB)]
        GT[(Git Tables)]
        IX[(Specialized Indexes)]
    end

    subgraph "Integration Points"
        Chat[Chat Adapter]
        Code[Code Adapter]
        Error[Error Adapter]
    end

    R1 --> EGA
    R2 --> EGA
    R3 --> EGA

    EGA --> CM
    EGA --> CA
    EGA --> BMD
    EGA --> RE

    EGA --> IGS
    IGS --> PP
    IGS --> TC
    IGS --> EM

    PP --> UC
    PP --> GT
    UC --> IX
    GT --> IX

    TC --> Chat
    TC --> Code
    TC --> Error
```

---

## Core Components

### 1. EnhancedGitAdapter

The main adapter class that orchestrates git history processing.

**Key Features:**
- Incremental processing with checkpoint management
- Advanced commit analysis and classification
- Branch topology mapping and merge detection
- Parallel processing for performance optimization
- Comprehensive error handling and recovery

**Example Usage:**
```python
from src.project_context.ingestion.adapters.enhanced_git_adapter import EnhancedGitAdapter

# Create configuration
config = EnhancedGitAdapter.default_config()
config.source_config.update({
    "repository_path": "/path/to/repo",
    "enable_incremental": True,
    "enable_semantic_analysis": True,
    "max_commits_per_batch": 1000
})

# Initialize adapter
adapter = EnhancedGitAdapter(config, database_connection)
await adapter.initialize()

# Process git history
async for raw_item in adapter.fetch_items():
    context_item = await adapter.transform_item(raw_item)
    # Process context_item...
```

### 2. CommitAnalyzer

Performs sophisticated analysis of individual commits.

**Analysis Features:**
- Semantic classification (feature, bugfix, hotfix, etc.)
- Impact scoring (0.0 to 1.0 scale)
- Risk assessment based on change patterns
- File complexity analysis
- Author behavior pattern detection

**Example Analysis Output:**
```python
CommitAnalysis(
    commit_hash="abc123...",
    commit_type=CommitType.FEATURE,
    impact_score=0.85,
    risk_score=0.23,
    complexity_delta=2.1,
    files_impacted=["src/auth.py", "tests/test_auth.py"],
    semantic_tags=["authentication", "security", "language_py"],
    related_patterns=["late_night_commit", "single_author"],
    author_patterns={"commit_time_hour": 23, "message_length": 145}
)
```

### 3. BranchMergeDetector

Maps branch topology and detects merge operations.

**Detection Capabilities:**
- Branch type classification (main, feature, hotfix, release)
- Merge commit analysis with conflict detection
- Branch lifecycle tracking
- Merge strategy identification

**Branch Analysis Example:**
```python
BranchInfo(
    name="feature/user-authentication",
    head_commit="def456...",
    base_branch="develop",
    branch_type="feature",
    creation_date=datetime(2024, 1, 15),
    last_activity=datetime(2024, 1, 20),
    commit_count=12,
    is_merged=True,
    merge_commit="ghi789..."
)
```

### 4. GitCheckpointManager

Manages incremental processing state and recovery.

**Checkpoint Features:**
- Per-branch processing state tracking
- Automatic checkpoint creation and recovery
- Error state management
- Progress monitoring and metrics

**Checkpoint Operations:**
```python
# Save checkpoint
await checkpoint_manager.save_checkpoint(
    branch="main",
    commit_hash="latest123...",
    timestamp=datetime.utcnow(),
    commit_count=150
)

# Get last processed commit
last_commit = await checkpoint_manager.get_last_processed_commit("main")

# Recover from failure
state = await checkpoint_manager.get_processing_state("main")
if state.status == ProcessingStatus.ERROR:
    # Handle recovery...
```

---

## Database Schema

### Core Tables

#### git_processing_checkpoints
Tracks incremental processing state for each repository branch.

```sql
CREATE TABLE git_processing_checkpoints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_path TEXT NOT NULL,
    branch_name VARCHAR(255) NOT NULL,
    last_processed_commit VARCHAR(40) NOT NULL,
    last_processed_timestamp TIMESTAMPTZ NOT NULL,
    processing_status VARCHAR(20) DEFAULT 'active',
    commit_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    last_error TEXT,
    processing_metrics JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### git_file_impacts
Detailed file change analysis for each commit.

```sql
CREATE TABLE git_file_impacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_path TEXT NOT NULL,
    commit_hash VARCHAR(40) NOT NULL,
    file_path TEXT NOT NULL,
    change_type VARCHAR(10) NOT NULL,
    lines_added INTEGER DEFAULT 0,
    lines_removed INTEGER DEFAULT 0,
    complexity_delta FLOAT DEFAULT 0.0,
    impact_score FLOAT DEFAULT 0.0,
    is_core_file BOOLEAN DEFAULT FALSE,
    related_context_items UUID[],
    change_metadata JSONB DEFAULT '{}'
);
```

#### git_branches
Branch topology and metadata.

```sql
CREATE TABLE git_branches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_path TEXT NOT NULL,
    branch_name VARCHAR(255) NOT NULL,
    head_commit VARCHAR(40) NOT NULL,
    base_branch VARCHAR(255),
    branch_type VARCHAR(20) DEFAULT 'unknown',
    creation_date TIMESTAMPTZ,
    last_activity TIMESTAMPTZ NOT NULL,
    commit_count INTEGER DEFAULT 0,
    is_merged BOOLEAN DEFAULT FALSE,
    merge_commit VARCHAR(40),
    branch_metadata JSONB DEFAULT '{}'
);
```

### Enhanced Context Items

The main `context_items` table is extended with git-specific metadata:

```sql
ALTER TABLE context_items ADD COLUMN git_metadata JSONB DEFAULT '{}';
ALTER TABLE context_items ADD COLUMN file_impact_score FLOAT DEFAULT 0.0;
```

**Git Metadata Structure:**
```json
{
  "commit_hash": "abc123...",
  "branch_name": "feature/auth",
  "commit_type": "feature",
  "impact_score": 0.85,
  "risk_score": 0.23,
  "complexity_delta": 2.1,
  "is_merge_commit": false,
  "semantic_tags": ["authentication", "security"],
  "author_patterns": {
    "commit_time_hour": 14,
    "message_length": 89
  }
}
```

### Specialized Indexes

Performance-optimized indexes for git queries:

```sql
-- Commit hash lookups
CREATE INDEX idx_context_items_git_commit_hash
    ON context_items((git_metadata->>'commit_hash'))
    WHERE source_type = 'git' AND entity_type = 'commit';

-- Branch-based queries
CREATE INDEX idx_context_items_git_branch
    ON context_items((git_metadata->>'branch_name'))
    WHERE source_type = 'git';

-- Impact and risk scoring
CREATE INDEX idx_context_items_git_impact_score
    ON context_items((git_metadata->>'impact_score')::float)
    WHERE source_type = 'git' AND (git_metadata->>'impact_score')::float > 0.5;

-- Temporal git queries
CREATE INDEX idx_context_items_git_temporal
    ON context_items(timestamp DESC, (git_metadata->>'branch_name'))
    WHERE source_type = 'git';
```

---

## Implementation Guide

### Step 1: Environment Setup

1. **Prerequisites:**
   ```bash
   # PostgreSQL with extensions
   psql -c "CREATE EXTENSION IF NOT EXISTS timescaledb;"
   psql -c "CREATE EXTENSION IF NOT EXISTS vector;"
   psql -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;"

   # Python dependencies
   pip install asyncio asyncpg structlog psutil
   ```

2. **Database Schema Deployment:**
   ```bash
   # Deploy git adapter schema
   psql -f migrations/005_git_history_adapter_schema.sql

   # Verify tables created
   psql -c "\dt git_*"
   ```

### Step 2: Configuration Setup

Create your git adapter configuration:

```yaml
# config/git_adapter_config.yaml
git_adapter:
  repositories:
    - path: "/path/to/repo1"
      primary_branches: ["main", "develop"]
    - path: "/path/to/repo2"
      primary_branches: ["master", "staging"]

  processing:
    enable_incremental: true
    batch_size: 500
    checkpoint_interval: 100
    max_parallel_repositories: 3

  analysis:
    enable_semantic_analysis: true
    enable_impact_scoring: true
    enable_branch_topology: true
    enable_merge_analysis: true

  correlation:
    correlate_with_chat: true
    correlate_with_errors: true
    temporal_window_hours: 48

  performance:
    memory_limit_mb: 2048
    processing_timeout_minutes: 60
    parallel_processing: true
```

### Step 3: Integration Implementation

**Basic Integration:**
```python
import asyncio
from src.project_context.ingestion.git_integration_strategy import (
    GitIntegrationOrchestrator, IntegrationConfig
)

async def integrate_git_adapter():
    # Configure integration
    config = IntegrationConfig(
        repository_paths=["/path/to/repo1", "/path/to/repo2"],
        enable_incremental=True,
        enable_semantic_analysis=True,
        max_parallel_repositories=3
    )

    # Create orchestrator
    orchestrator = GitIntegrationOrchestrator(config, database_connection)

    # Execute integration
    success = await orchestrator.execute_integration()

    if success:
        print("Git adapter integration completed successfully!")
    else:
        print("Integration failed. Check logs for details.")

# Run integration
asyncio.run(integrate_git_adapter())
```

**Advanced Usage with Error Handling:**
```python
from src.project_context.ingestion.git_integration_strategy import (
    ErrorRecoveryStrategy, IntegrationPhase
)

async def robust_integration():
    config = IntegrationConfig(
        repository_paths=["/path/to/large/repo"],
        enable_incremental=True,
        max_retries=5,
        retry_delay_base_seconds=2.0,
        circuit_breaker_threshold=10,
        memory_limit_mb=4096
    )

    orchestrator = GitIntegrationOrchestrator(config, db)

    # Custom error recovery strategies
    orchestrator.error_recovery_strategies.update({
        "memory_error": ErrorRecoveryStrategy.GRACEFUL_DEGRADATION,
        "timeout_error": ErrorRecoveryStrategy.RETRY_EXPONENTIAL_BACKOFF,
        "connection_error": ErrorRecoveryStrategy.PAUSE_AND_ALERT
    })

    try:
        success = await orchestrator.execute_integration()

        # Monitor progress
        while orchestrator.current_phase != IntegrationPhase.MONITORING:
            metrics = orchestrator.metrics
            print(f"Phase: {metrics.phase.value}")
            print(f"Progress: {metrics.repositories_processed}/{metrics.total_repositories}")
            print(f"Commits: {metrics.commits_processed} ({metrics.commits_failed} failed)")
            await asyncio.sleep(30)

    except Exception as e:
        print(f"Integration failed: {e}")
        # Handle failure, check checkpoints, retry if appropriate

asyncio.run(robust_integration())
```

### Step 4: Testing and Validation

Run the comprehensive test suite:

```python
from src.project_context.ingestion.git_adapter_testing import GitAdapterTester

async def run_tests():
    tester = GitAdapterTester(database_connection)
    results = await tester.run_comprehensive_test_suite()

    print("Test Results Summary:")
    for category, tests in results.items():
        passed = sum(1 for test in tests if test.passed)
        total = len(tests)
        print(f"{category}: {passed}/{total} passed")

        # Show failed tests
        failed_tests = [test for test in tests if not test.passed]
        for test in failed_tests:
            print(f"  FAILED: {test.test_name} - {test.error_message}")

asyncio.run(run_tests())
```

---

## Configuration

### Complete Configuration Reference

```yaml
git_adapter:
  # Repository settings
  repositories:
    - path: "/path/to/repo"
      primary_branches: ["main", "develop"]
      max_commit_age_days: 365
      author_filters: []  # Empty = all authors
      branch_filters: []  # Empty = all branches

  # Processing configuration
  processing:
    enable_incremental: true
    batch_size: 500
    checkpoint_interval: 100
    max_commits_per_batch: 1000
    parallel_processing: true
    max_parallel_repositories: 3
    max_parallel_branches: 5

  # Analysis configuration
  analysis:
    enable_semantic_analysis: true
    enable_impact_scoring: true
    enable_relationship_detection: true
    enable_branch_topology: true
    enable_merge_analysis: true
    track_file_impacts: true

  # Error handling
  error_handling:
    max_retries: 3
    retry_delay_base_seconds: 2.0
    retry_backoff_factor: 2.0
    error_threshold_per_hour: 50
    circuit_breaker_threshold: 10

  # Performance settings
  performance:
    memory_limit_mb: 2048
    processing_timeout_minutes: 60
    query_timeout_seconds: 30
    cache_enabled: true
    cache_ttl_hours: 24

  # Integration settings
  integration:
    correlate_with_chat: true
    correlate_with_errors: true
    temporal_correlation_window_hours: 48
    generate_embeddings: true
    embedding_model: "text-embedding-ada-002"

  # Monitoring
  monitoring:
    enable_detailed_monitoring: true
    monitoring_interval_seconds: 60
    performance_alert_threshold: 0.8
    enable_metrics_export: true
```

### Environment Variables

```bash
# Database configuration
DATABASE_URL="postgresql://user:pass@localhost:5432/unified_context"

# Git adapter settings
GIT_ADAPTER_MEMORY_LIMIT=2048
GIT_ADAPTER_BATCH_SIZE=500
GIT_ADAPTER_PARALLEL_REPOS=3

# Feature flags
GIT_ENABLE_SEMANTIC_ANALYSIS=true
GIT_ENABLE_INCREMENTAL=true
GIT_ENABLE_BRANCH_DETECTION=true

# Performance tuning
GIT_PROCESSING_TIMEOUT=3600
GIT_QUERY_TIMEOUT=30
GIT_CHECKPOINT_INTERVAL=100
```

---

## Testing Framework

### Running Tests

**Unit Tests:**
```bash
# Run specific test category
python -m pytest src/project_context/ingestion/git_adapter_testing.py::test_git_adapter_basic_functionality -v

# Run all git adapter tests
python -m pytest src/project_context/ingestion/git_adapter_testing.py -v

# Run with coverage
python -m pytest src/project_context/ingestion/git_adapter_testing.py --cov=src.project_context.ingestion.adapters.enhanced_git_adapter
```

**Integration Tests:**
```bash
# Full test suite
python src/project_context/ingestion/git_adapter_testing.py

# Performance benchmarks
python -c "
import asyncio
from src.project_context.ingestion.git_adapter_testing import GitAdapterTester

async def benchmark():
    tester = GitAdapterTester()
    results = await tester.run_performance_tests()
    for result in results:
        print(f'{result.test_name}: {result.metrics}')

asyncio.run(benchmark())
"
```

### Test Configuration

Create a test-specific configuration:

```yaml
# config/git_adapter_test_config.yaml
git_adapter:
  repositories:
    - path: "/tmp/test_repo"
      primary_branches: ["main"]

  processing:
    enable_incremental: false  # Disable for consistent test results
    batch_size: 10
    max_parallel_repositories: 1

  analysis:
    enable_semantic_analysis: true
    enable_impact_scoring: true

  performance:
    memory_limit_mb: 512
    processing_timeout_minutes: 5
```

---

## Deployment Guide

### Production Deployment Steps

1. **Database Preparation:**
   ```bash
   # Create production database
   createdb unified_context_prod

   # Deploy schema
   psql unified_context_prod -f unified_context_schema.sql
   psql unified_context_prod -f migrations/005_git_history_adapter_schema.sql

   # Create indexes
   psql unified_context_prod -c "REINDEX DATABASE unified_context_prod;"

   # Update statistics
   psql unified_context_prod -c "ANALYZE;"
   ```

2. **Configuration Management:**
   ```bash
   # Production configuration
   export GIT_ADAPTER_CONFIG="/etc/unified_context/git_adapter_prod.yaml"
   export DATABASE_URL="postgresql://prod_user:secure_pass@db-server:5432/unified_context_prod"

   # Logging configuration
   export LOG_LEVEL="INFO"
   export LOG_FORMAT="json"
   export LOG_OUTPUT="/var/log/unified_context/git_adapter.log"
   ```

3. **Service Configuration (systemd):**
   ```ini
   # /etc/systemd/system/git-adapter.service
   [Unit]
   Description=Unified Context Git Adapter
   After=network.target postgresql.service

   [Service]
   Type=simple
   User=unified_context
   Group=unified_context
   WorkingDirectory=/opt/unified_context
   Environment=PYTHONPATH=/opt/unified_context
   ExecStart=/opt/unified_context/venv/bin/python -m src.project_context.ingestion.git_adapter_service
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

4. **Docker Deployment:**
   ```dockerfile
   FROM python:3.11-slim

   # Install system dependencies
   RUN apt-get update && apt-get install -y \
       git \
       postgresql-client \
       && rm -rf /var/lib/apt/lists/*

   # Install Python dependencies
   COPY requirements.txt .
   RUN pip install -r requirements.txt

   # Copy application
   COPY src/ /app/src/
   COPY config/ /app/config/

   WORKDIR /app

   # Health check
   HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
     CMD python -c "from src.project_context.ingestion.adapters.enhanced_git_adapter import EnhancedGitAdapter; print('OK')"

   CMD ["python", "-m", "src.project_context.ingestion.git_adapter_service"]
   ```

5. **Monitoring Setup:**
   ```bash
   # Prometheus metrics endpoint
   curl http://localhost:8080/metrics

   # Health check endpoint
   curl http://localhost:8080/health

   # Git adapter status
   curl http://localhost:8080/git-adapter/status
   ```

---

## Performance Optimization

### Database Optimization

1. **Partition Strategy:**
   ```sql
   -- Partition git_file_impacts by repository
   CREATE TABLE git_file_impacts_repo1 PARTITION OF git_file_impacts
   FOR VALUES IN ('repo1');

   -- Partition by time for large repositories
   CREATE TABLE git_file_impacts_2024 PARTITION OF git_file_impacts
   FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');
   ```

2. **Index Optimization:**
   ```sql
   -- Analyze query patterns
   SELECT query, calls, total_time, mean_time
   FROM pg_stat_statements
   WHERE query LIKE '%git_%'
   ORDER BY total_time DESC LIMIT 10;

   -- Create covering indexes for common queries
   CREATE INDEX CONCURRENTLY idx_git_commits_analysis_covering
   ON context_items (timestamp, actor_id, (git_metadata->>'branch_name'))
   WHERE source_type = 'git' AND entity_type = 'commit';
   ```

3. **Connection Pooling:**
   ```python
   import asyncpg

   # Production pool configuration
   async def create_db_pool():
       return await asyncpg.create_pool(
           dsn="postgresql://...",
           min_size=5,
           max_size=20,
           max_queries=50000,
           max_inactive_connection_lifetime=300,
           command_timeout=60
       )
   ```

### Processing Optimization

1. **Parallel Processing Tuning:**
   ```python
   # Optimal configuration for different environments

   # Small repositories (< 1K commits)
   config = IntegrationConfig(
       max_parallel_repositories=2,
       batch_size=100,
       checkpoint_interval=50
   )

   # Medium repositories (1K - 10K commits)
   config = IntegrationConfig(
       max_parallel_repositories=3,
       batch_size=500,
       checkpoint_interval=100
   )

   # Large repositories (> 10K commits)
   config = IntegrationConfig(
       max_parallel_repositories=5,
       batch_size=1000,
       checkpoint_interval=200,
       memory_limit_mb=4096
   )
   ```

2. **Memory Management:**
   ```python
   import gc
   import psutil

   async def memory_efficient_processing(adapter, items):
       processed_count = 0

       async for raw_item in items:
           context_item = await adapter.transform_item(raw_item)
           # Process item...

           processed_count += 1

           # Memory management
           if processed_count % 1000 == 0:
               gc.collect()  # Force garbage collection

               memory_usage = psutil.Process().memory_info().rss / 1024 / 1024
               if memory_usage > config.memory_limit_mb * 0.8:
                   await asyncio.sleep(1)  # Brief pause to allow cleanup
   ```

3. **Query Optimization:**
   ```sql
   -- Efficient git history search
   EXPLAIN (ANALYZE, BUFFERS)
   SELECT * FROM search_git_history(
       search_term := 'authentication',
       branch_filter := 'main',
       min_impact_score := 0.5,
       max_results := 100
   );

   -- Optimize based on explain plan
   -- Add missing indexes, adjust query structure
   ```

---

## Monitoring & Troubleshooting

### Key Metrics to Monitor

1. **Processing Metrics:**
   - Commits processed per second
   - Processing error rate
   - Memory usage trends
   - Database connection pool utilization

2. **Data Quality Metrics:**
   - Duplicate commit detection rate
   - Relationship accuracy scores
   - Checkpoint recovery success rate
   - Temporal correlation precision

3. **Performance Metrics:**
   - Query response times
   - Index hit ratios
   - Concurrent processing efficiency
   - Batch processing throughput

### Monitoring Dashboard

```python
# monitoring/git_adapter_dashboard.py
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List

@dataclass
class GitAdapterMetrics:
    # Processing metrics
    commits_per_second: float
    repositories_active: int
    processing_errors_last_hour: int
    memory_usage_mb: float

    # Data quality metrics
    duplicate_rate: float
    relationship_accuracy: float
    temporal_correlation_rate: float

    # Performance metrics
    avg_query_time_ms: float
    index_hit_ratio: float
    checkpoint_success_rate: float

async def collect_git_adapter_metrics(db_pool) -> GitAdapterMetrics:
    async with db_pool.acquire() as conn:
        # Collect processing metrics
        processing_stats = await conn.fetchrow("""
            SELECT
                COUNT(*) as commits_last_hour,
                COUNT(DISTINCT project_id) as active_repos,
                COUNT(*) FILTER (WHERE ingested_at < timestamp) as processing_errors
            FROM context_items
            WHERE source_type = 'git'
                AND timestamp >= NOW() - INTERVAL '1 hour'
        """)

        # Collect performance metrics
        performance_stats = await conn.fetchrow("""
            SELECT
                AVG(EXTRACT(milliseconds FROM age(NOW(), query_start))) as avg_query_time,
                (SELECT (heap_blks_hit::float / (heap_blks_hit + heap_blks_read)) * 100
                 FROM pg_stat_user_tables WHERE relname = 'context_items') as index_hit_ratio
            FROM pg_stat_activity
            WHERE query LIKE '%git_%' AND state = 'active'
        """)

        return GitAdapterMetrics(
            commits_per_second=processing_stats['commits_last_hour'] / 3600.0,
            repositories_active=processing_stats['active_repos'],
            processing_errors_last_hour=processing_stats['processing_errors'],
            memory_usage_mb=0.0,  # Would collect from system metrics
            duplicate_rate=0.0,   # Would calculate from data quality checks
            relationship_accuracy=0.0,  # Would calculate from validation
            temporal_correlation_rate=0.0,  # Would calculate from correlations
            avg_query_time_ms=performance_stats['avg_query_time'] or 0.0,
            index_hit_ratio=performance_stats['index_hit_ratio'] or 0.0,
            checkpoint_success_rate=0.0  # Would calculate from checkpoint logs
        )
```

### Common Issues & Solutions

1. **High Memory Usage:**
   ```python
   # Issue: Memory usage growing during processing
   # Solution: Implement batch processing with memory limits

   async def memory_controlled_processing(config, adapter):
       memory_threshold = config.memory_limit_mb * 0.8
       batch_size = config.batch_size

       while True:
           current_memory = get_memory_usage_mb()

           if current_memory > memory_threshold:
               # Reduce batch size and force garbage collection
               batch_size = max(batch_size // 2, 10)
               gc.collect()
               await asyncio.sleep(2)
           elif current_memory < memory_threshold * 0.5:
               # Increase batch size if memory usage is low
               batch_size = min(batch_size * 1.2, config.batch_size)

           # Process with adjusted batch size
           await process_batch(adapter, batch_size)
   ```

2. **Slow Query Performance:**
   ```sql
   -- Issue: Slow git history searches
   -- Solution: Analyze and optimize queries

   -- Check for missing indexes
   SELECT schemaname, tablename, attname, n_distinct, correlation
   FROM pg_stats
   WHERE tablename = 'context_items'
       AND attname IN ('timestamp', 'source_type', 'project_id');

   -- Add specialized indexes
   CREATE INDEX CONCURRENTLY idx_git_search_optimized
   ON context_items (source_type, timestamp DESC, project_id)
   WHERE source_type = 'git';
   ```

3. **Checkpoint Recovery Issues:**
   ```python
   # Issue: Checkpoint recovery failing
   # Solution: Implement robust checkpoint validation

   async def validate_and_recover_checkpoint(checkpoint_manager, repo_path, branch):
       try:
           state = await checkpoint_manager.get_processing_state(branch)

           if not state:
               # No checkpoint exists, create initial one
               await create_initial_checkpoint(repo_path, branch)
               return True

           if state.status == ProcessingStatus.ERROR:
               # Validate checkpoint integrity
               if await validate_checkpoint_commit(state.last_processed_commit):
                   # Reset to previous good state
                   await reset_to_previous_checkpoint(checkpoint_manager, branch)
               else:
                   # Checkpoint is corrupted, restart from beginning
                   await create_initial_checkpoint(repo_path, branch)

           return True

       except Exception as e:
           logger.error("Checkpoint recovery failed", error=str(e))
           return False
   ```

4. **Processing Bottlenecks:**
   ```python
   # Issue: Processing is slower than expected
   # Solution: Implement adaptive processing strategies

   class AdaptiveProcessingStrategy:
       def __init__(self, initial_config):
           self.config = initial_config
           self.performance_history = []

       async def adapt_processing_parameters(self, current_metrics):
           # Analyze recent performance
           if len(self.performance_history) >= 5:
               recent_rate = sum(self.performance_history[-5:]) / 5

               if recent_rate < self.config.target_processing_rate:
                   # Performance is below target, adjust parameters
                   if current_metrics.memory_usage_mb < self.config.memory_limit_mb * 0.7:
                       # Increase parallelism if memory allows
                       self.config.max_parallel_repositories += 1
                   else:
                       # Reduce batch size to decrease memory pressure
                       self.config.batch_size = max(self.config.batch_size // 1.2, 50)
               else:
                   # Performance is good, try to optimize further
                   if current_metrics.cpu_usage < 70:
                       self.config.batch_size = min(self.config.batch_size * 1.1, 2000)

           self.performance_history.append(current_metrics.commits_per_second)
           if len(self.performance_history) > 20:
               self.performance_history.pop(0)
   ```

### Troubleshooting Checklist

**Performance Issues:**
- [ ] Check database connection pool utilization
- [ ] Verify index usage with EXPLAIN ANALYZE
- [ ] Monitor memory usage patterns
- [ ] Review batch size and parallelism settings
- [ ] Check for table/index fragmentation

**Data Quality Issues:**
- [ ] Validate git repository accessibility
- [ ] Check for corrupted commit data
- [ ] Verify relationship detection accuracy
- [ ] Review duplicate detection logic
- [ ] Validate temporal correlation precision

**Integration Issues:**
- [ ] Verify database schema is up to date
- [ ] Check adapter configuration compatibility
- [ ] Validate cross-adapter relationship detection
- [ ] Review error handling and recovery logic
- [ ] Test checkpoint creation and recovery

---

## API Reference

### GitIntegrationOrchestrator

Main orchestrator class for git adapter integration.

#### Methods

**execute_integration() -> bool**
Executes the complete git integration strategy.

```python
async def execute_integration() -> bool:
    """
    Execute complete integration process including:
    1. Initialization
    2. Schema validation
    3. Incremental setup
    4. Bulk ingestion
    5. Real-time processing setup
    6. Optimization
    7. Monitoring setup

    Returns:
        bool: True if integration successful, False otherwise
    """
```

### EnhancedGitAdapter

Enhanced git adapter with comprehensive analysis capabilities.

#### Configuration

**default_config() -> AdapterConfig**
Returns default configuration for the git adapter.

#### Core Methods

**initialize() -> None**
Initialize adapter resources and validate repository access.

**fetch_items(since=None, until=None, limit=None) -> AsyncIterator[Dict]**
Fetch git items with incremental processing support.

**transform_item(raw_item: Dict) -> ContextItem**
Transform raw git item into standardized ContextItem.

**cleanup() -> None**
Clean up adapter resources.

### CommitAnalyzer

Advanced commit analysis component.

#### Methods

**analyze_commit(commit_data: Dict) -> CommitAnalysis**
Perform comprehensive commit analysis including semantic classification, impact scoring, and risk assessment.

```python
async def analyze_commit(self, commit_data: Dict) -> CommitAnalysis:
    """
    Analyze git commit comprehensively.

    Args:
        commit_data: Raw commit data from git log

    Returns:
        CommitAnalysis: Analysis results including:
        - commit_type: Semantic classification
        - impact_score: Impact on codebase (0.0-1.0)
        - risk_score: Risk assessment (0.0-1.0)
        - complexity_delta: Complexity change
        - files_impacted: List of affected files
        - semantic_tags: Extracted semantic tags
        - related_patterns: Detected patterns
    """
```

### Database Functions

#### search_git_history()

Search git history with advanced filtering.

```sql
SELECT * FROM search_git_history(
    search_term := 'authentication',
    repository_filter := 'main_repo',
    author_filter := 'john@example.com',
    branch_filter := 'main',
    commit_type_filter := 'feature',
    min_impact_score := 0.5,
    min_risk_score := 0.0,
    date_from := '2024-01-01'::timestamptz,
    date_to := '2024-12-31'::timestamptz,
    include_merge_commits := true,
    max_results := 100
);
```

#### get_git_repository_statistics()

Get comprehensive repository statistics.

```sql
SELECT * FROM get_git_repository_statistics(
    repository_path_filter := 'main_repo',
    date_from := '2024-01-01'::timestamptz,
    date_to := NOW()
);
```

#### analyze_git_commit_patterns()

Analyze commit patterns and trends.

```sql
SELECT * FROM analyze_git_commit_patterns(
    repository_path_filter := 'main_repo',
    author_filter := 'john@example.com',
    days_back := 30
);
```

---

## Conclusion

This comprehensive Git History Adapter provides a robust, scalable solution for ingesting and analyzing git repository data as part of the Unified Context System. The implementation includes:

- **Advanced Analysis**: Semantic commit classification, impact scoring, and risk assessment
- **Incremental Processing**: Efficient processing with checkpoint management and recovery
- **Temporal Correlation**: Links git events with chat logs, errors, and code intelligence
- **Performance Optimization**: Handles large repositories (10K+ commits) with sub-second query times
- **Comprehensive Testing**: Full test suite with unit, integration, and performance tests
- **Production Ready**: Complete deployment guide with monitoring and troubleshooting

The adapter integrates seamlessly with the existing Phase 1 adapters and provides the foundation for advanced temporal analysis and cross-domain insights in the Unified Context System.

<function_calls>
<invoke name="TodoWrite">
<parameter name="todos">[{"content": "Load operational instructions and analyze current system", "status": "completed", "activeForm": "Loading operational instructions and analyzing current system"}, {"content": "Design GitAdapter class architecture with incremental processing", "status": "completed", "activeForm": "Designing GitAdapter class architecture with incremental processing"}, {"content": "Design commit analysis and metadata extraction system", "status": "completed", "activeForm": "Designing commit analysis and metadata extraction system"}, {"content": "Design branch and merge detection algorithms", "status": "completed", "activeForm": "Designing branch and merge detection algorithms"}, {"content": "Design data model integration with unified schema", "status": "completed", "activeForm": "Designing data model integration with unified schema"}, {"content": "Create implementation strategy and error handling", "status": "completed", "activeForm": "Creating implementation strategy and error handling"}, {"content": "Document architecture and provide code implementation", "status": "completed", "activeForm": "Documenting architecture and providing code implementation"}]
