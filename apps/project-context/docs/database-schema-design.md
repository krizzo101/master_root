# Unified Context Database Schema Design

## Executive Summary

This document details the comprehensive database schema design for the Unified Context System Phase 1, which implements a temporal knowledge graph that unifies chat logs, code intelligence, git history, and error data into a queryable PostgreSQL + Neo4j backend with semantic search capabilities.

## Architecture Overview

The database schema is designed around three core principles:

1. **Temporal Knowledge Graph**: All data is time-ordered and relationship-aware
2. **Polymorphic Flexibility**: Single tables handle multiple data types efficiently
3. **Performance at Scale**: Optimized for 100M+ context items with sub-second queries

### Technology Stack

- **PostgreSQL 15+**: Primary relational database
- **TimescaleDB**: Time-series optimization and partitioning
- **pgvector**: Semantic search with vector embeddings
- **Neo4j**: Graph relationships (bidirectional integration)
- **Redis**: Caching layer for Context Bridge integration

## Schema Components

### 1. Core Context Storage

#### `context_items` Table (Hypertable)

The primary table storing all context data in a polymorphic design:

```sql
CREATE TABLE context_items (
    -- Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_type VARCHAR(50) NOT NULL, -- 'chat', 'code', 'monitor', 'ide', 'git'
    source_id VARCHAR(255) NOT NULL,  -- Original ID from source system
    entity_type VARCHAR(100) NOT NULL, -- 'message', 'file', 'function', 'metric'

    -- Temporal (TimescaleDB partitioned by timestamp)
    timestamp TIMESTAMPTZ NOT NULL,
    timestamp_end TIMESTAMPTZ,  -- For duration events
    ingested_at TIMESTAMPTZ DEFAULT NOW(),

    -- Content (Full-text searchable)
    title TEXT,
    content TEXT,  -- Full searchable content
    content_hash VARCHAR(64),  -- SHA256 for deduplication
    summary TEXT,  -- AI-generated summary

    -- Location Context
    project_id VARCHAR(255),
    file_path TEXT,
    line_start INTEGER,
    line_end INTEGER,
    function_name VARCHAR(255),
    class_name VARCHAR(255),

    -- Actor Information
    actor_id VARCHAR(255),
    actor_type VARCHAR(50), -- 'human', 'ai', 'system'
    session_id VARCHAR(255),  -- Links to chat sessions

    -- Classification
    severity VARCHAR(20),
    tags TEXT[],

    -- Flexible Data Storage
    metrics JSONB,  -- Performance/quality metrics
    source_data JSONB,  -- Original data preserved

    -- Search Optimization
    embedding vector(1536),  -- Semantic search vectors
    search_vector tsvector,  -- Full-text search

    -- Neo4j Integration
    neo4j_node_id VARCHAR(255),  -- Bidirectional graph linking

    CONSTRAINT unique_source UNIQUE(source_type, source_id)
);
```

**Design Decisions:**

- **Polymorphic Design**: Single table handles all context types to enable cross-type queries and relationships
- **TimescaleDB Hypertable**: 1-day chunks for optimal time-series performance
- **JSONB Storage**: Flexible metrics and source_data columns for evolving data structures
- **Dual Search**: Both semantic (vector) and full-text (tsvector) search capabilities
- **Deduplication**: content_hash prevents duplicate ingestion
- **Neo4j Bridge**: neo4j_node_id enables hybrid queries across PostgreSQL and Neo4j

### 2. Graph Relationship Modeling

#### `context_relationships` Table

Advanced relationship modeling between context items:

```sql
CREATE TABLE context_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL REFERENCES context_items(id) ON DELETE CASCADE,
    target_id UUID NOT NULL REFERENCES context_items(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) NOT NULL, -- 'causes', 'references', 'contains', 'follows', 'resolves'
    confidence FLOAT DEFAULT 1.0 CHECK (confidence BETWEEN 0.0 AND 1.0),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by VARCHAR(50) DEFAULT 'system', -- 'system', 'ai', 'human'

    -- Temporal context for relationships
    temporal_context VARCHAR(50), -- 'before', 'during', 'after', 'concurrent'
    time_delta_seconds INTEGER, -- Time difference between related items

    -- Validation context
    validation_status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'validated', 'rejected'
    validation_score FLOAT, -- AI confidence in relationship accuracy

    -- Neo4j integration
    neo4j_relationship_id VARCHAR(255),

    CONSTRAINT unique_relationship UNIQUE(source_id, target_id, relationship_type),
    CONSTRAINT no_self_reference CHECK (source_id != target_id)
);
```

**Design Decisions:**

- **Confidence Scoring**: All relationships have confidence scores for ML-based validation
- **Temporal Context**: Captures timing relationships (before/after/during)
- **Validation Workflow**: Support for human validation of AI-detected relationships
- **Creator Tracking**: Distinguish between human-created and auto-detected relationships
- **Cascade Deletion**: Relationships are cleaned up when context items are deleted

### 3. Machine Learning Pattern Storage

#### `correlation_patterns` Table

Stores learned correlation patterns for predictive analysis:

```sql
CREATE TABLE correlation_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern_name VARCHAR(255) NOT NULL,
    pattern_type VARCHAR(50) NOT NULL, -- 'temporal', 'causal', 'co-occurrence', 'sequence'
    source_criteria JSONB NOT NULL, -- Query criteria for source events
    target_criteria JSONB NOT NULL, -- Query criteria for target events
    confidence FLOAT CHECK (confidence BETWEEN 0.0 AND 1.0),
    support_count INTEGER DEFAULT 0, -- Number of times pattern was observed
    avg_time_delta INTERVAL, -- Average time between source and target
    min_time_delta INTERVAL,
    max_time_delta INTERVAL,

    -- Pattern effectiveness
    success_rate FLOAT, -- How often this pattern predicts correctly
    false_positive_rate FLOAT,

    -- Pattern metadata
    discovered_at TIMESTAMPTZ DEFAULT NOW(),
    last_matched TIMESTAMPTZ,
    last_validated TIMESTAMPTZ,
    discovery_method VARCHAR(100), -- 'ml', 'rule_based', 'manual'

    -- Pattern lifecycle
    pattern_status VARCHAR(20) DEFAULT 'active', -- 'active', 'deprecated', 'testing'
    priority INTEGER DEFAULT 1,
    metadata JSONB DEFAULT '{}'
);
```

**Design Decisions:**

- **JSONB Criteria**: Flexible query criteria allow complex pattern matching
- **Effectiveness Tracking**: success_rate and false_positive_rate for pattern quality
- **Lifecycle Management**: Patterns can be active, deprecated, or in testing
- **Discovery Attribution**: Track how patterns were discovered (ML, rules, manual)
- **Temporal Statistics**: Track time deltas for pattern timing predictions

### 4. Performance Analytics

#### `context_metrics_hourly` Table (Hypertable)

Time-series metrics for performance monitoring and trend analysis:

```sql
CREATE TABLE context_metrics_hourly (
    time_bucket TIMESTAMPTZ NOT NULL,
    source_type VARCHAR(50) NOT NULL,
    entity_type VARCHAR(100),
    project_id VARCHAR(255),

    -- Basic counts
    item_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    warning_count INTEGER DEFAULT 0,

    -- Performance metrics
    avg_response_time FLOAT,
    p95_response_time FLOAT,
    p99_response_time FLOAT,
    total_duration FLOAT,

    -- Quality metrics
    error_rate FLOAT,
    throughput FLOAT,
    success_rate FLOAT,

    -- Resource metrics
    total_tokens INTEGER DEFAULT 0,
    total_cost NUMERIC(12,4) DEFAULT 0,
    avg_complexity FLOAT,

    -- Relationship metrics
    relationship_count INTEGER DEFAULT 0,
    avg_relationships_per_item FLOAT,

    PRIMARY KEY (time_bucket, source_type, COALESCE(entity_type, ''), COALESCE(project_id, ''))
);
```

**Design Decisions:**

- **Hourly Aggregation**: Balances detail with storage efficiency
- **Multi-dimensional**: Aggregates by source_type, entity_type, and project_id
- **Comprehensive Metrics**: Covers performance, quality, resources, and relationships
- **TimescaleDB Optimization**: 1-day chunks for efficient time-series queries

### 5. Knowledge Gap Detection

#### `knowledge_gaps` Table

Tracks identified knowledge gaps for documentation and training:

```sql
CREATE TABLE knowledge_gaps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gap_type VARCHAR(50) NOT NULL, -- 'documentation', 'understanding', 'context'
    severity VARCHAR(20), -- 'low', 'medium', 'high', 'critical'

    -- Gap identification
    identified_at TIMESTAMPTZ DEFAULT NOW(),
    identified_by VARCHAR(50), -- 'system', 'human', 'pattern_analysis'

    -- Gap context
    file_path TEXT,
    function_name VARCHAR(255),
    related_context_items UUID[],

    -- Gap metrics
    discussion_count INTEGER DEFAULT 0, -- How many times discussed
    avg_discussion_length FLOAT, -- Average tokens in discussions
    resolution_attempts INTEGER DEFAULT 0,

    -- Gap resolution
    resolution_status VARCHAR(20) DEFAULT 'open', -- 'open', 'in_progress', 'resolved'
    resolved_at TIMESTAMPTZ,
    resolution_method TEXT,
    resolution_confidence FLOAT,

    metadata JSONB DEFAULT '{}'
);
```

**Design Decisions:**

- **Gap Classification**: Multiple gap types and severity levels
- **Resolution Tracking**: Full lifecycle from identification to resolution
- **Context Linking**: Array of related context items for comprehensive analysis
- **Metrics-Driven**: Uses discussion frequency and complexity for gap scoring

## Advanced Features

### 1. Semantic Search with pgvector

**Vector Embeddings**: 1536-dimensional vectors from OpenAI text-embedding-ada-002
**HNSW Indexing**: High-performance approximate nearest neighbor search
**Hybrid Search**: Combines semantic and full-text search with weighted scoring

```sql
-- Example hybrid search function
CREATE OR REPLACE FUNCTION hybrid_context_search(
    query_text TEXT,
    query_embedding vector(1536),
    text_weight FLOAT DEFAULT 0.3,
    vector_weight FLOAT DEFAULT 0.7,
    similarity_threshold FLOAT DEFAULT 0.5,
    max_results INTEGER DEFAULT 10
)
```

### 2. Automated Relationship Detection

**Trigger-Based**: Auto-detects relationships on context item insertion
**Confidence Scoring**: Only suggests high-confidence relationships (>0.5)
**Async Processing**: Background job approach prevents ingestion slowdowns

### 3. Performance Optimizations

**21+ Specialized Indexes**: Covering all major query patterns
**Materialized Views**: Pre-computed analytics for dashboard performance
**Partitioning**: TimescaleDB automatic partitioning by timestamp
**Concurrent Refresh**: Non-blocking materialized view updates

## Integration Architecture

### PostgreSQL ↔ Neo4j Bridge

**Bidirectional Linking**:
- PostgreSQL tables have `neo4j_node_id` fields
- Neo4j nodes reference PostgreSQL IDs
- Enables complex graph queries with ACID compliance

**Use Cases**:
- Knowledge graph traversal
- Multi-hop relationship discovery
- Complex pattern matching across relationship types

### Context Bridge Integration

**Real-time Flow**:
```
IDE → Context Bridge → Redis → Project Context MCP → PostgreSQL
```

**Data Types**:
- Active file changes and cursor positions
- Diagnostic information (errors, warnings)
- Project context snapshots
- Real-time activity tracking

## Performance Characteristics

### Scalability Targets

- **Storage**: 100M+ context items (estimated 50-500GB)
- **Ingestion**: 1,000+ items/second sustained
- **Query Performance**: <100ms for most queries
- **Concurrent Users**: 20+ simultaneous connections
- **Real-time Updates**: <100ms latency for Context Bridge

### Query Optimization Strategies

1. **Index Strategy**: 21 specialized indexes covering all query patterns
2. **Partitioning**: TimescaleDB 1-day chunks for time-series data
3. **Materialized Views**: Pre-computed aggregations for dashboard queries
4. **Connection Pooling**: PgBouncer for connection management
5. **Query Planning**: Custom functions optimized for specific use cases

## Security and Privacy

### Access Control

- **Role-Based Security**: PostgreSQL roles for different access levels
- **Row-Level Security**: Project-level isolation support
- **API Authentication**: Integration with MCP server authentication
- **Audit Logging**: All access logged in context_items

### Data Protection

- **Encryption at Rest**: PostgreSQL TDE support
- **Encryption in Transit**: TLS for all connections
- **PII Detection**: Content scanning for sensitive information
- **Data Retention**: Configurable retention policies via TimescaleDB

## Migration Strategy

### Three-Phase Migration Approach

**Migration 001**: Core relationship tables and indexes
**Migration 002**: Advanced analytics functions
**Migration 003**: Materialized views and performance optimization

Each migration includes:
- Pre-migration validation
- Rollback procedures
- Post-migration verification
- Performance impact assessment

### Backward Compatibility

- **Existing Schema**: Builds on existing context_items foundation
- **Gradual Migration**: New features can be enabled incrementally
- **Fallback Support**: System continues functioning if enhancements fail

## Monitoring and Maintenance

### Health Metrics

- **Ingestion Rate**: Items per second by source type
- **Query Performance**: Response time percentiles
- **Relationship Quality**: Validation rates and confidence scores
- **Knowledge Gap Trends**: Gap identification and resolution rates
- **Storage Growth**: Space utilization and projection

### Automated Maintenance

```sql
-- Automated maintenance function
SELECT refresh_analytics_views();  -- Refresh materialized views
SELECT cleanup_system_jobs(24);    -- Clean old background jobs
SELECT validate_relationships(100, 0.5);  -- Validate relationship confidence
```

## Future Enhancements

### Phase 2 Considerations

1. **Machine Learning Integration**: Automated pattern discovery
2. **Real-time Streaming**: Apache Kafka integration for high-volume ingestion
3. **Multi-tenant Support**: Enhanced row-level security
4. **Advanced Analytics**: Time-series forecasting and anomaly detection
5. **Graph Algorithms**: PageRank, community detection, centrality metrics

### Scalability Improvements

1. **Sharding Strategy**: Horizontal partitioning for massive scale
2. **Read Replicas**: Query performance optimization
3. **Caching Layer**: Redis integration for frequently accessed data
4. **Compression**: TimescaleDB compression for historical data

## Conclusion

This database schema provides a robust, scalable foundation for the Unified Context System that can handle the complexity of temporal knowledge graphs while maintaining excellent query performance. The design balances flexibility with performance, enabling sophisticated analysis while supporting rapid ingestion and real-time queries.

The combination of PostgreSQL's reliability, TimescaleDB's time-series optimization, pgvector's semantic search capabilities, and careful relationship modeling creates a system capable of transforming fragmented development data into actionable insights.

---

**Document Version**: 1.0
**Last Updated**: 2025-01-17
**Schema Version**: Phase 1 Complete
**Status**: Production Ready
