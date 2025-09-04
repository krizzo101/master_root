# Git History Adapter Architecture

## Overview

This document outlines the comprehensive architecture for the Git History Adapter, designed to provide incremental processing of Git repositories with sophisticated commit analysis, branch/merge detection, and temporal correlation with chat logs and code intelligence.

## Architecture Objectives

### Performance Targets
- Handle repositories with 10K+ commits efficiently
- Incremental processing to avoid reprocessing existing data
- Sub-second query response times for temporal correlations
- Batch processing optimizations for initial repository ingestion

### Integration Requirements
- Seamless integration with Phase 1 adapters (chat, code, error)
- Temporal correlation engine for cross-domain insights
- Relationship modeling between commits, files, and conversations
- Real-time processing for new commits via webhook integration

## Core Components Architecture

### 1. Enhanced GitAdapter Class

```python
class EnhancedGitAdapter(BaseAdapter):
    """
    Enhanced Git adapter with incremental processing and comprehensive analysis.

    Features:
    - Incremental commit processing with checkpoint management
    - Advanced commit analysis and metadata extraction
    - Branch topology mapping and merge detection
    - Author relationship tracking and contribution analysis
    - File change correlation and impact analysis
    - Performance optimization through parallel processing
    """

    def __init__(self, config: AdapterConfig):
        super().__init__(config)

        # Processing state management
        self.checkpoint_manager = GitCheckpointManager(config)
        self.commit_analyzer = CommitAnalyzer(config)
        self.branch_detector = BranchMergeDetector(config)
        self.relationship_engine = GitRelationshipEngine(config)

        # Performance optimization
        self.parallel_processor = ParallelGitProcessor(config)
        self.cache_manager = GitCacheManager(config)

        # Integration components
        self.temporal_correlator = TemporalCorrelator(config)
        self.embedding_generator = GitEmbeddingGenerator(config)
```

### 2. Incremental Processing System

#### Checkpoint Management
```python
class GitCheckpointManager:
    """
    Manages processing checkpoints for incremental git history ingestion.

    Features:
    - Persistent checkpoint storage in database
    - Branch-specific processing state tracking
    - Error recovery and resumption capabilities
    - Progress monitoring and reporting
    """

    async def get_last_processed_commit(self, branch: str) -> Optional[str]:
        """Get the last processed commit hash for a branch."""

    async def save_checkpoint(self, branch: str, commit_hash: str, timestamp: datetime):
        """Save processing checkpoint for a branch."""

    async def get_unprocessed_commits(self, branch: str, limit: int = 1000) -> List[Dict]:
        """Get commits that haven't been processed yet."""

    async def recover_from_failure(self, branch: str) -> ProcessingState:
        """Recover processing state after failure."""
```

#### Processing State Schema Extension
```sql
-- Git processing checkpoints table
CREATE TABLE IF NOT EXISTS git_processing_checkpoints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_path TEXT NOT NULL,
    branch_name VARCHAR(255) NOT NULL,
    last_processed_commit VARCHAR(40) NOT NULL, -- SHA-1 hash
    last_processed_timestamp TIMESTAMPTZ NOT NULL,
    processing_status VARCHAR(20) DEFAULT 'active', -- 'active', 'paused', 'error'
    commit_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    last_error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(repository_path, branch_name)
);

-- Git commit relationships table (extends unified schema)
CREATE TABLE IF NOT EXISTS git_commit_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    commit_hash VARCHAR(40) NOT NULL,
    parent_hash VARCHAR(40) NOT NULL,
    relationship_type VARCHAR(20) NOT NULL, -- 'parent', 'merge_parent'
    branch_name VARCHAR(255),
    merge_commit BOOLEAN DEFAULT FALSE,
    distance_from_head INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(commit_hash, parent_hash, relationship_type)
);

-- Git file impact tracking
CREATE TABLE IF NOT EXISTS git_file_impacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    commit_hash VARCHAR(40) NOT NULL,
    file_path TEXT NOT NULL,
    change_type VARCHAR(10) NOT NULL, -- 'A', 'M', 'D', 'R', 'C'
    lines_added INTEGER DEFAULT 0,
    lines_removed INTEGER DEFAULT 0,
    complexity_delta FLOAT DEFAULT 0.0,
    impact_score FLOAT DEFAULT 0.0, -- Calculated impact on codebase
    related_context_items UUID[], -- Links to related chat/code context
    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(commit_hash, file_path)
);
```

### 3. Advanced Commit Analysis Engine

```python
class CommitAnalyzer:
    """
    Advanced commit analysis with semantic understanding and impact assessment.

    Features:
    - Commit message semantic analysis
    - Code change impact assessment
    - Author contribution pattern analysis
    - Commit classification (feature, bugfix, refactor, etc.)
    - Risk assessment for changes
    """

    async def analyze_commit(self, commit_data: Dict) -> CommitAnalysis:
        """
        Perform comprehensive commit analysis.

        Returns:
            CommitAnalysis containing:
            - Semantic classification
            - Impact metrics
            - Risk assessment
            - Related context suggestions
        """

    async def extract_commit_metadata(self, commit_hash: str) -> Dict:
        """Extract comprehensive metadata from commit."""

    async def calculate_impact_score(self, commit_data: Dict) -> float:
        """Calculate the impact score of a commit on the codebase."""

    async def detect_commit_patterns(self, commit_data: Dict) -> List[str]:
        """Detect patterns in commit (hotfix, feature, merge, etc.)."""
```

### 4. Branch and Merge Detection System

```python
class BranchMergeDetector:
    """
    Sophisticated branch topology analysis and merge detection.

    Features:
    - Branch relationship mapping
    - Merge commit detection and analysis
    - Feature branch lifecycle tracking
    - Release branch identification
    - Hotfix branch detection
    """

    async def map_branch_topology(self, repository_path: str) -> BranchTopology:
        """Create comprehensive branch topology map."""

    async def detect_merge_commits(self, commit_data: Dict) -> MergeInfo:
        """Detect and analyze merge commits."""

    async def track_branch_lifecycle(self, branch_name: str) -> BranchLifecycle:
        """Track the complete lifecycle of a feature branch."""

    async def identify_release_branches(self) -> List[ReleaseBranch]:
        """Identify release and hotfix branches."""
```

### 5. Temporal Correlation Engine

```python
class TemporalCorrelator:
    """
    Correlates git events with chat logs, errors, and code intelligence.

    Features:
    - Time-based event correlation
    - Causality detection between commits and errors
    - Developer conversation correlation with commits
    - Build/deployment correlation with commits
    """

    async def correlate_commits_with_chat(self, commit_hash: str, time_window: timedelta) -> List[ChatCorrelation]:
        """Find chat messages temporally related to commits."""

    async def correlate_commits_with_errors(self, commit_hash: str) -> List[ErrorCorrelation]:
        """Find errors that occurred after specific commits."""

    async def detect_development_patterns(self, developer_id: str) -> DeveloperPatterns:
        """Detect patterns in developer behavior across commit/chat data."""
```

## Data Model Integration

### Extended Unified Schema

```sql
-- Enhanced context_items extensions for git data
ALTER TABLE context_items ADD COLUMN IF NOT EXISTS git_metadata JSONB DEFAULT '{}';

-- Create specialized indexes for git data
CREATE INDEX IF NOT EXISTS idx_context_items_git_commit_hash
    ON context_items((git_metadata->>'commit_hash'))
    WHERE source_type = 'git' AND entity_type = 'commit';

CREATE INDEX IF NOT EXISTS idx_context_items_git_author
    ON context_items(actor_id)
    WHERE source_type = 'git';

CREATE INDEX IF NOT EXISTS idx_context_items_git_branch
    ON context_items((git_metadata->>'branch_name'))
    WHERE source_type = 'git';

-- Git-specific relationship types
INSERT INTO correlation_patterns (
    pattern_name, pattern_type, source_criteria, target_criteria,
    confidence, avg_time_delta, discovery_method
) VALUES
(
    'Commit-Error Causation',
    'temporal',
    '{"source_type": "git", "entity_type": "commit"}'::jsonb,
    '{"source_type": "error", "severity": ["high", "critical"]}'::jsonb,
    0.75,
    INTERVAL '2 hours',
    'ml'
),
(
    'Developer Discussion-Commit Correlation',
    'temporal',
    '{"source_type": "chat", "actor_type": "human"}'::jsonb,
    '{"source_type": "git", "entity_type": "commit"}'::jsonb,
    0.65,
    INTERVAL '30 minutes',
    'pattern_analysis'
);
```

### Performance Optimization Schema

```sql
-- Materialized view for git statistics
CREATE MATERIALIZED VIEW IF NOT EXISTS git_statistics AS
SELECT
    DATE_TRUNC('day', timestamp) as day,
    actor_id as author,
    COUNT(*) as commit_count,
    COUNT(DISTINCT (git_metadata->>'branch_name')) as branches_touched,
    SUM((git_metadata->>'files_changed')::integer) as total_files_changed,
    AVG((git_metadata->>'impact_score')::float) as avg_impact_score,
    STRING_AGG(DISTINCT git_metadata->>'commit_type', ', ') as commit_types
FROM context_items
WHERE source_type = 'git' AND entity_type = 'commit'
GROUP BY DATE_TRUNC('day', timestamp), actor_id;

CREATE UNIQUE INDEX idx_git_statistics_day_author ON git_statistics(day, author);

-- Function for hybrid git search
CREATE OR REPLACE FUNCTION search_git_history(
    search_term TEXT,
    author_filter TEXT DEFAULT NULL,
    branch_filter TEXT DEFAULT NULL,
    date_from TIMESTAMPTZ DEFAULT NULL,
    date_to TIMESTAMPTZ DEFAULT NULL,
    include_diffs BOOLEAN DEFAULT FALSE
) RETURNS TABLE (
    commit_hash VARCHAR(40),
    title TEXT,
    author VARCHAR(255),
    commit_date TIMESTAMPTZ,
    branch_name VARCHAR(255),
    files_changed TEXT[],
    impact_score FLOAT,
    relevance_score FLOAT
) LANGUAGE SQL STABLE AS $$
    SELECT
        ci.git_metadata->>'commit_hash' as commit_hash,
        ci.title,
        ci.actor_id as author,
        ci.timestamp as commit_date,
        ci.git_metadata->>'branch_name' as branch_name,
        ARRAY(SELECT jsonb_array_elements_text(ci.git_metadata->'changed_files')) as files_changed,
        (ci.git_metadata->>'impact_score')::float as impact_score,
        ts_rank_cd(ci.search_vector, plainto_tsquery(search_term)) as relevance_score
    FROM context_items ci
    WHERE ci.source_type = 'git'
        AND ci.entity_type = 'commit'
        AND (author_filter IS NULL OR ci.actor_id = author_filter)
        AND (branch_filter IS NULL OR ci.git_metadata->>'branch_name' = branch_filter)
        AND (date_from IS NULL OR ci.timestamp >= date_from)
        AND (date_to IS NULL OR ci.timestamp <= date_to)
        AND (search_term IS NULL OR ci.search_vector @@ plainto_tsquery(search_term))
    ORDER BY relevance_score DESC, ci.timestamp DESC;
$$;
```

## Implementation Strategy

### Phase 1: Core Infrastructure (Week 1-2)
1. **Enhanced GitAdapter Implementation**
   - Extend existing GitAdapter with checkpoint management
   - Implement parallel processing capabilities
   - Add comprehensive error handling and recovery

2. **Database Schema Extensions**
   - Deploy git-specific tables and indexes
   - Create materialized views for analytics
   - Implement specialized stored procedures

3. **Incremental Processing Engine**
   - Implement GitCheckpointManager
   - Add processing state persistence
   - Create recovery mechanisms

### Phase 2: Analysis and Correlation (Week 3-4)
1. **Advanced Commit Analysis**
   - Implement CommitAnalyzer with semantic analysis
   - Add impact scoring algorithms
   - Create commit classification system

2. **Temporal Correlation**
   - Build TemporalCorrelator for cross-domain insights
   - Implement causality detection algorithms
   - Add pattern recognition for developer behavior

3. **Branch and Merge Detection**
   - Implement BranchMergeDetector
   - Add branch topology mapping
   - Create merge analysis capabilities

### Phase 3: Integration and Optimization (Week 5-6)
1. **Performance Optimization**
   - Implement parallel processing for large repositories
   - Add intelligent caching mechanisms
   - Optimize database queries and indexes

2. **Real-time Processing**
   - Add webhook support for real-time commit processing
   - Implement event-driven architecture
   - Add monitoring and alerting

3. **Testing and Validation**
   - Comprehensive testing on large repositories
   - Performance benchmarking
   - Integration testing with existing adapters

## Configuration Management

### GitAdapter Configuration
```yaml
git_adapter:
  # Repository settings
  repository_path: "/path/to/repo"
  max_commit_age_days: null  # Process all history

  # Incremental processing
  enable_incremental: true
  checkpoint_interval: 100  # commits
  max_commits_per_batch: 1000

  # Analysis settings
  enable_semantic_analysis: true
  enable_impact_scoring: true
  enable_relationship_detection: true

  # Performance settings
  parallel_processing: true
  max_parallel_workers: 4
  cache_enabled: true
  cache_ttl_hours: 24

  # Integration settings
  correlate_with_chat: true
  correlate_with_errors: true
  temporal_window_hours: 48

  # Advanced features
  enable_branch_detection: true
  enable_merge_analysis: true
  track_file_impacts: true
  generate_embeddings: true
```

## Monitoring and Observability

### Key Metrics
- **Processing Performance**: Commits per second, batch processing time
- **Data Quality**: Duplicate detection rate, relationship accuracy
- **System Health**: Memory usage, error rates, checkpoint success rate
- **Correlation Quality**: Cross-domain relationship accuracy, temporal correlation precision

### Monitoring Dashboard Components
```python
class GitAdapterMonitoring:
    """Monitoring and observability for Git adapter."""

    async def get_processing_metrics(self) -> Dict:
        """Get current processing performance metrics."""

    async def get_data_quality_metrics(self) -> Dict:
        """Get data quality and accuracy metrics."""

    async def get_correlation_metrics(self) -> Dict:
        """Get cross-domain correlation effectiveness metrics."""

    async def health_check(self) -> HealthStatus:
        """Comprehensive health check for git adapter."""
```

## Error Handling and Recovery

### Resilience Patterns
1. **Graceful Degradation**: Continue processing even if some features fail
2. **Circuit Breaker**: Stop processing if error rate exceeds threshold
3. **Retry Logic**: Exponential backoff for transient failures
4. **Checkpoint Recovery**: Resume from last successful checkpoint
5. **Partial Success Handling**: Process what's possible, log failures

### Error Scenarios
- **Repository Access Failures**: Network issues, permission problems
- **Git Command Failures**: Corrupt repository, missing commits
- **Database Connection Issues**: Connection pooling, transaction failures
- **Memory Pressure**: Large repository handling, batch size optimization
- **Correlation Failures**: External service dependencies

## Testing Strategy

### Unit Testing
- Individual component testing (CommitAnalyzer, BranchDetector, etc.)
- Mock git repository scenarios
- Database interaction testing

### Integration Testing
- End-to-end pipeline testing
- Multi-adapter integration scenarios
- Real repository processing validation

### Performance Testing
- Large repository processing (10K+ commits)
- Concurrent processing load testing
- Memory usage profiling
- Query performance validation

### Validation Testing
- Data accuracy verification
- Relationship detection accuracy
- Temporal correlation validation
- Cross-domain integration verification

This architecture provides a robust, scalable, and comprehensive solution for Git history ingestion that integrates seamlessly with the existing Unified Context System while providing advanced analytics and correlation capabilities.
