# Git History Integration Guide
## Unified Context System - Phase 2 Implementation

### Overview

This guide provides comprehensive instructions for integrating Git history analysis into the Unified Context System, enabling temporal correlation between code changes, conversations, and errors.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Configuration](#configuration)
3. [Advanced Usage](#advanced-usage)
4. [Performance Tuning](#performance-tuning)
5. [Troubleshooting](#troubleshooting)
6. [API Reference](#api-reference)

## Quick Start

### 1. Basic Setup

```python
from project_context.ingestion.adapters.git_adapter import GitAdapter
from project_context.ingestion.base_adapter import AdapterConfig, BatchMode

# Basic configuration
config = AdapterConfig(
    adapter_id="my_git",
    source_type="git",
    batch_mode=BatchMode.BATCH,
    batch_size=200,
    source_config={
        "repository_path": "/path/to/your/repo",
        "enable_semantic_analysis": True,
        "max_commit_age_days": 90,
    }
)

# Initialize adapter
git_adapter = GitAdapter(config)
await git_adapter.initialize()

# Fetch and process commits
async for raw_commit in git_adapter.fetch_items(limit=100):
    context_item = await git_adapter.transform_item(raw_commit)
    # Process context_item...
```

### 2. Database Integration

```python
from project_context.ingestion.database import DatabaseConnectionPool, IngestionDatabase

# Setup database connection
db_pool = DatabaseConnectionPool(
    "postgresql://user:pass@localhost:5432/unified_context"
)
await db_pool.initialize()

db = IngestionDatabase(db_pool)

# Store Git context items
commits = []
async for raw_commit in git_adapter.fetch_items():
    context_item = await git_adapter.transform_item(raw_commit)
    commits.append(context_item)

result = await db.store_context_items(commits)
print(f"Stored {result.processed_items} commits")
```

### 3. Relationship Detection

```python
# Process commits and detect relationships
all_commits = []
async for raw_commit in git_adapter.fetch_items():
    context_item = await git_adapter.transform_item(raw_commit)

    # Detect relationships with existing commits
    relationships = await git_adapter.detect_relationships(
        context_item, all_commits[-50:]  # Use sliding window
    )

    all_commits.append(context_item)

    # Store relationships
    if relationships:
        rel_objects = [
            ContextRelationship(
                source_id=context_item.id,
                target_id=target_id,
                relationship_type=rel_type,
                confidence=confidence
            )
            for rel_type, target_id, confidence in relationships
        ]
        await db.store_relationships(rel_objects)
```

## Configuration

### Core Configuration Options

```yaml
# git_adapter_config.yaml
git_adapters:
  - adapter_id: "primary_git"
    source_type: "git"
    batch_mode: "batch"
    batch_size: 200

    source_config:
      # Repository settings
      repository_path: "/path/to/repo"
      max_commit_age_days: 365

      # Processing options
      enable_incremental: true
      checkpoint_interval: 100
      max_commits_per_batch: 1000

      # Analysis features
      enable_semantic_analysis: true
      enable_impact_scoring: true
      enable_relationship_detection: true
      enable_branch_detection: true

      # Correlation settings
      correlate_with_chat: true
      correlate_with_errors: true
      temporal_window_hours: 48

      # Performance settings
      parallel_processing: true
      max_parallel_workers: 4

      # Content settings
      include_commits: true
      include_branches: true
      include_tags: true
      include_file_changes: true
      include_diff_content: true
      max_diff_size_kb: 100

      # Filtering
      branch_filters: ["main", "develop", "feature/*"]
      author_filters: []
      exclude_merge_commits: false
```

### Configuration Reference

#### Repository Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `repository_path` | str | "." | Path to Git repository |
| `max_commit_age_days` | int | None | Only process commits newer than N days |
| `branch_filters` | List[str] | [] | List of branches to process (supports wildcards) |
| `author_filters` | List[str] | [] | Only process commits by these authors |
| `exclude_merge_commits` | bool | false | Skip merge commits |

#### Processing Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `enable_incremental` | bool | true | Enable incremental processing |
| `checkpoint_interval` | int | 100 | Save checkpoint every N commits |
| `max_commits_per_batch` | int | 1000 | Maximum commits per processing batch |
| `parallel_processing` | bool | false | Enable parallel processing |
| `max_parallel_workers` | int | 4 | Number of parallel workers |

#### Analysis Features

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `enable_semantic_analysis` | bool | true | Analyze commit messages and types |
| `enable_impact_scoring` | bool | true | Calculate commit impact scores |
| `enable_relationship_detection` | bool | true | Detect commit relationships |
| `enable_branch_detection` | bool | true | Analyze branch patterns |

#### Correlation Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `correlate_with_chat` | bool | true | Find correlations with chat data |
| `correlate_with_errors` | bool | true | Find correlations with error data |
| `temporal_window_hours` | int | 48 | Time window for correlations |

#### Content Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `include_commits` | bool | true | Process commit objects |
| `include_branches` | bool | true | Process branch objects |
| `include_tags` | bool | true | Process tag objects |
| `include_file_changes` | bool | true | Include file change details |
| `include_diff_content` | bool | true | Include diff content |
| `max_diff_size_kb` | int | 100 | Maximum diff size to include |

## Advanced Usage

### 1. Custom Commit Analysis

```python
from project_context.ingestion.adapters.git_adapter import CommitProcessor

class CustomCommitProcessor(CommitProcessor):
    """Custom commit processor with domain-specific analysis."""

    def _classify_commit_type(self, message: str, changed_files: List[Dict]) -> CommitType:
        """Custom commit classification logic."""
        # Add your domain-specific patterns
        if "deployment" in message.lower():
            return CommitType.DEPLOYMENT
        elif any("config" in f["file"] for f in changed_files):
            return CommitType.CONFIGURATION

        return super()._classify_commit_type(message, changed_files)

    async def _calculate_impact_score(self, commit_data: Dict) -> float:
        """Custom impact scoring."""
        base_score = await super()._calculate_impact_score(commit_data)

        # Boost score for critical files
        critical_files = ["main.py", "app.py", "server.py"]
        changed_files = [f["file"] for f in commit_data.get("changed_files", [])]

        if any(cf in file for cf in critical_files for file in changed_files):
            base_score += 0.3

        return min(base_score, 1.0)

# Use custom processor
config.source_config["processor_class"] = CustomCommitProcessor
```

### 2. Advanced Relationship Detection

```python
async def detect_custom_relationships(
    item: ContextItem,
    context_window: List[ContextItem]
) -> List[tuple]:
    """Custom relationship detection logic."""
    relationships = []

    # Detect code review relationships
    if item.source_type == "git" and "review" in item.title.lower():
        for context_item in context_window:
            if (context_item.source_type == "chat" and
                "review" in context_item.content.lower()):
                relationships.append(("code_review_discussion", str(context_item.id), 0.8))

    # Detect deployment relationships
    if item.metrics and item.metrics.get("commit_type") == "deployment":
        for context_item in context_window:
            if context_item.source_type == "error":
                time_diff = abs((item.timestamp - context_item.timestamp).total_seconds())
                if time_diff < 7200:  # Within 2 hours
                    confidence = max(0.4, 1.0 - (time_diff / 7200))
                    relationships.append(("deployment_error", str(context_item.id), confidence))

    return relationships

# Override relationship detection
original_detect = git_adapter.detect_relationships
git_adapter.detect_relationships = detect_custom_relationships
```

### 3. Performance Optimization

```python
# Configure for large repositories
large_repo_config = AdapterConfig(
    adapter_id="large_git",
    source_type="git",
    batch_mode=BatchMode.BULK,
    batch_size=1000,
    source_config={
        "repository_path": "/path/to/large/repo",
        "parallel_processing": True,
        "max_parallel_workers": 8,
        "max_commit_age_days": 180,  # Limit scope
        "include_diff_content": False,  # Skip diffs for speed
        "enable_semantic_analysis": False,  # Skip analysis for speed
        "checkpoint_interval": 50,
        "branch_filters": ["main", "develop"],  # Limit branches
    }
)

# Use caching for repeated analysis
from diskcache import Cache
cache = Cache("/tmp/git_analysis_cache")

async def cached_analysis(commit_sha: str):
    if commit_sha in cache:
        return cache[commit_sha]

    # Perform analysis...
    result = await analyze_commit(commit_sha)
    cache[commit_sha] = result
    return result
```

### 4. Incremental Processing

```python
async def incremental_git_processing():
    """Example of incremental Git processing."""

    # Get last processed commit
    checkpoint_manager = GitCheckpointManager(config, db_pool)
    last_commit = await checkpoint_manager.get_last_processed_commit("main")

    if last_commit:
        print(f"Resuming from commit: {last_commit[:8]}")

    # Process only new commits
    since = None
    if last_commit:
        # Find timestamp of last processed commit
        since = await get_commit_timestamp(last_commit)

    processed_count = 0
    async for raw_commit in git_adapter.fetch_items(since=since):
        context_item = await git_adapter.transform_item(raw_commit)
        await db.store_context_items([context_item])

        processed_count += 1

        # Save checkpoint every 100 commits
        if processed_count % 100 == 0:
            await checkpoint_manager.save_checkpoint(
                "main",
                raw_commit["hash"],
                context_item.timestamp,
                processed_count
            )
            print(f"Checkpoint saved at commit {processed_count}")

    print(f"Processed {processed_count} new commits")
```

## Performance Tuning

### Repository Size Guidelines

| Repository Size | Recommended Settings |
|-----------------|---------------------|
| Small (<1K commits) | Default settings, enable all analysis |
| Medium (1K-10K commits) | `batch_size=500`, `parallel_processing=true` |
| Large (10K-50K commits) | `batch_size=1000`, `max_parallel_workers=8`, limit branches |
| Very Large (>50K commits) | Consider pygit2 migration, disable diff content |

### Performance Configuration Examples

#### Speed Optimized (Fast ingestion)

```yaml
source_config:
  batch_size: 1000
  parallel_processing: true
  max_parallel_workers: 8
  enable_semantic_analysis: false
  include_diff_content: false
  max_commit_age_days: 90
  branch_filters: ["main"]
```

#### Analysis Optimized (Rich data)

```yaml
source_config:
  batch_size: 100
  parallel_processing: false
  enable_semantic_analysis: true
  enable_impact_scoring: true
  include_diff_content: true
  max_diff_size_kb: 500
  correlate_with_chat: true
  correlate_with_errors: true
```

#### Balanced (Production)

```yaml
source_config:
  batch_size: 200
  parallel_processing: true
  max_parallel_workers: 4
  enable_semantic_analysis: true
  include_diff_content: true
  max_diff_size_kb: 100
  max_commit_age_days: 365
```

### Memory Management

```python
# Monitor memory usage
import psutil

async def process_with_memory_monitoring():
    process = psutil.Process()

    batch_count = 0
    async for raw_commit in git_adapter.fetch_items():
        context_item = await git_adapter.transform_item(raw_commit)
        # Process item...

        batch_count += 1

        # Check memory every 100 items
        if batch_count % 100 == 0:
            memory_mb = process.memory_info().rss / (1024 * 1024)
            print(f"Memory usage: {memory_mb:.1f} MB")

            if memory_mb > 1000:  # 1GB limit
                print("Memory usage high, forcing garbage collection")
                import gc
                gc.collect()
```

## Troubleshooting

### Common Issues

#### 1. Repository Access Issues

```python
# Check if repository is accessible
import os
from git import Repo

try:
    repo = Repo("/path/to/repo")
    print(f"Repository valid: {repo.git_dir}")
    print(f"Current branch: {repo.active_branch.name}")
except Exception as e:
    print(f"Repository error: {e}")
    # Check permissions, path, etc.
```

#### 2. Performance Issues

```python
# Profile Git operations
import cProfile
import pstats

def profile_git_processing():
    profiler = cProfile.Profile()
    profiler.enable()

    # Run your Git processing
    asyncio.run(process_git_history())

    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(20)  # Top 20 functions
```

#### 3. Database Connection Issues

```python
# Test database connectivity
async def test_database():
    try:
        db_pool = DatabaseConnectionPool(database_url)
        await db_pool.initialize()

        # Test query
        result = await db_pool.execute_query("SELECT 1", fetch="val")
        print(f"Database test result: {result}")

        await db_pool.close()
        print("Database connection successful")
    except Exception as e:
        print(f"Database connection failed: {e}")
```

#### 4. Memory Leaks

```python
# Debug memory usage
import tracemalloc
import asyncio

async def debug_memory():
    tracemalloc.start()

    # Take snapshot before processing
    snapshot1 = tracemalloc.take_snapshot()

    # Process commits
    async for commit in git_adapter.fetch_items(limit=1000):
        await git_adapter.transform_item(commit)

    # Take snapshot after processing
    snapshot2 = tracemalloc.take_snapshot()

    # Compare snapshots
    top_stats = snapshot2.compare_to(snapshot1, 'lineno')

    print("Top 10 memory allocations:")
    for stat in top_stats[:10]:
        print(stat)
```

### Performance Monitoring

```python
class GitProcessingMonitor:
    """Monitor Git processing performance."""

    def __init__(self):
        self.start_time = None
        self.commits_processed = 0
        self.errors = 0
        self.memory_samples = []

    async def monitor_processing(self, git_adapter):
        """Monitor the processing pipeline."""
        self.start_time = asyncio.get_event_loop().time()
        process = psutil.Process()

        async for raw_commit in git_adapter.fetch_items():
            try:
                context_item = await git_adapter.transform_item(raw_commit)
                self.commits_processed += 1

                # Sample memory every 50 commits
                if self.commits_processed % 50 == 0:
                    memory_mb = process.memory_info().rss / (1024 * 1024)
                    self.memory_samples.append(memory_mb)

                    rate = self.commits_processed / (asyncio.get_event_loop().time() - self.start_time)
                    print(f"Processed: {self.commits_processed}, Rate: {rate:.1f}/s, Memory: {memory_mb:.1f}MB")

            except Exception as e:
                self.errors += 1
                print(f"Error processing commit: {e}")

    def get_report(self):
        """Generate performance report."""
        duration = asyncio.get_event_loop().time() - self.start_time if self.start_time else 0
        rate = self.commits_processed / duration if duration > 0 else 0

        return {
            'duration_seconds': duration,
            'commits_processed': self.commits_processed,
            'processing_rate': rate,
            'error_count': self.errors,
            'error_rate': self.errors / max(self.commits_processed, 1),
            'peak_memory_mb': max(self.memory_samples) if self.memory_samples else 0,
            'average_memory_mb': sum(self.memory_samples) / len(self.memory_samples) if self.memory_samples else 0
        }
```

## API Reference

### GitAdapter

Main adapter class for Git history processing.

```python
class GitAdapter(BaseAdapter):
    def __init__(self, config: AdapterConfig, database_connection=None)

    async def initialize(self) -> None
    async def fetch_items(self, since=None, until=None, limit=None) -> AsyncIterator[Dict]
    async def transform_item(self, raw_item: Dict) -> ContextItem
    async def detect_relationships(self, item: ContextItem, context_window: List[ContextItem]) -> List[tuple]
    async def cleanup(self) -> None
```

### CommitProcessor

Advanced commit analysis and semantic understanding.

```python
class CommitProcessor:
    def __init__(self, config: AdapterConfig)

    async def analyze_commit(self, commit_data: Dict) -> CommitAnalysis
    def _classify_commit_type(self, message: str, changed_files: List[Dict]) -> CommitType
    async def _calculate_impact_score(self, commit_data: Dict) -> float
    def _calculate_risk_score(self, commit_data: Dict, impact_score: float) -> float
```

### GitCheckpointManager

Manages incremental processing checkpoints.

```python
class GitCheckpointManager:
    def __init__(self, config: AdapterConfig, database_connection=None)

    async def get_last_processed_commit(self, branch: str) -> Optional[str]
    async def save_checkpoint(self, branch: str, commit_hash: str, timestamp: datetime, commit_count: int = 0)
```

### Data Models

Key data structures for Git processing.

```python
@dataclass
class CommitAnalysis:
    commit_hash: str
    commit_type: CommitType
    impact_score: float
    risk_score: float
    complexity_delta: float
    files_impacted: List[str]
    semantic_tags: List[str]
    related_patterns: List[str]
    author_patterns: Dict[str, Any]

@dataclass
class BranchInfo:
    name: str
    head_commit: str
    base_branch: Optional[str]
    branch_type: str
    creation_date: datetime
    last_activity: datetime
    commit_count: int
    is_merged: bool
    merge_commit: Optional[str]
```

## Integration Examples

### With Chat Context

```python
async def correlate_git_with_chat():
    """Correlate Git commits with chat conversations."""

    # Get recent commits
    commits = []
    async for raw_commit in git_adapter.fetch_items(limit=100):
        context_item = await git_adapter.transform_item(raw_commit)
        commits.append(context_item)

    # Get recent chat messages
    chat_messages = await get_recent_chat_messages()

    # Find correlations
    correlations = []
    for commit in commits:
        for chat_msg in chat_messages:
            # Time-based correlation
            time_diff = abs((commit.timestamp - chat_msg.timestamp).total_seconds())
            if time_diff < 3600:  # Within 1 hour

                # Content-based correlation
                commit_files = commit.metrics.get('changed_files', [])
                if any(file_path in chat_msg.content for file_path in commit_files):
                    correlation = ContextRelationship(
                        source_id=commit.id,
                        target_id=chat_msg.id,
                        relationship_type="git_chat_correlation",
                        confidence=0.8,
                        temporal_context="concurrent",
                        time_delta_seconds=int(time_diff)
                    )
                    correlations.append(correlation)

    await db.store_relationships(correlations)
    print(f"Found {len(correlations)} Git-Chat correlations")
```

### With Error Context

```python
async def correlate_git_with_errors():
    """Correlate Git commits with error occurrences."""

    # Get high-risk commits
    high_risk_commits = []
    async for raw_commit in git_adapter.fetch_items(limit=200):
        context_item = await git_adapter.transform_item(raw_commit)

        if context_item.metrics.get('risk_score', 0) > 0.6:
            high_risk_commits.append(context_item)

    # Get recent errors
    recent_errors = await get_recent_errors(hours=48)

    # Find potential causation relationships
    causation_relationships = []
    for commit in high_risk_commits:
        for error in recent_errors:
            # Errors occurring after high-risk commits
            if error.timestamp > commit.timestamp:
                time_diff = (error.timestamp - commit.timestamp).total_seconds()

                if time_diff < 7200:  # Within 2 hours
                    # Check if error involves files changed in commit
                    changed_files = set(commit.metrics.get('changed_files', []))

                    if any(file_path in error.content for file_path in changed_files):
                        confidence = 0.8
                    else:
                        confidence = 0.3 + (commit.metrics.get('risk_score', 0) * 0.4)

                    relationship = ContextRelationship(
                        source_id=commit.id,
                        target_id=error.id,
                        relationship_type="potential_error_causation",
                        confidence=confidence,
                        temporal_context="before",
                        time_delta_seconds=int(time_diff)
                    )
                    causation_relationships.append(relationship)

    await db.store_relationships(causation_relationships)
    print(f"Found {len(causation_relationships)} potential Git-Error causation relationships")
```

This comprehensive guide provides everything needed to successfully integrate Git history analysis into the Unified Context System, enabling rich temporal correlations and insights into code evolution patterns.
