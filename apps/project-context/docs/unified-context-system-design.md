# Unified Context System - Design Document

## Executive Summary

The Unified Context System transforms disparate development data sources (chat logs, code intelligence, git history, errors, monitoring) into a single, queryable knowledge graph that provides temporal, causal, and semantic understanding of software projects.

### Vision
Create a **temporal knowledge graph** that answers not just "what is this code?" but "what has this code done?", "why does it exist?", "who understands it?", and "what depends on it?"

### Core Value Propositions
1. **Predictive Debugging**: Predict failures based on historical patterns
2. **Impact Analysis**: Understand change consequences before deployment
3. **Knowledge Velocity**: Identify and fill knowledge gaps automatically
4. **Context Transfer**: Preserve and transfer developer understanding
5. **Performance Forensics**: Instant root cause analysis with full context

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────┐
│            External Interfaces                   │
├──────────────┬────────────────┬─────────────────┤
│   MCP API    │   GraphQL API  │   WebSocket API │
│  (FastMCP)   │  (Coming Soon) │   (Real-time)   │
├──────────────┴────────────────┴─────────────────┤
│           Semantic Query Layer                   │
│   - Natural language to SQL/Graph queries        │
│   - Cross-source aggregation                     │
│   - Relevance ranking                            │
├──────────────────────────────────────────────────┤
│            Correlation Engine                    │
│   - Temporal correlation                         │
│   - Causal chain analysis                        │
│   - Pattern detection                            │
├──────────────────────────────────────────────────┤
│           Cache Layer (Multi-tier)               │
│   - Query result cache                           │
│   - Aggregation cache                            │
│   - Embedding cache                              │
├──────────────────────────────────────────────────┤
│         Unified Context Database                 │
│   - PostgreSQL with TimescaleDB                  │
│   - pgvector for embeddings                      │
│   - Full-text search indexes                     │
├──────────────────────────────────────────────────┤
│          Ingestion Pipeline Layer                │
├────┬────┬────┬────┬────┬────┬────┬──────────────┤
│Chat│Code│Git │Err │CI  │API │Mon │              │
│Logs│Intel│Hist│Logs│CD  │Logs│Metrics│          │
└────┴────┴────┴────┴────┴────┴────┴──────────────┘
     ↑    ↑    ↑    ↑    ↑    ↑    ↑
  Real- Batch  Hook Real-Hook Real-Streaming
  time         based time     time
```

### Component Descriptions

#### 1. **Ingestion Pipeline Layer**
- **Purpose**: Normalize and ingest data from various sources
- **Components**:
  - Source-specific adapters
  - Data validators
  - Deduplication logic
  - Embedding generation
- **Processing Modes**:
  - Real-time: Chat logs, errors, monitoring
  - Near real-time: Git hooks, CI/CD webhooks
  - Batch: Code analysis, historical data

#### 2. **Unified Context Database**
- **Technology**: PostgreSQL + TimescaleDB + pgvector
- **Purpose**: Store all context data in a unified schema
- **Features**:
  - Time-series optimization
  - Vector similarity search
  - Full-text search
  - Graph relationships

#### 3. **Correlation Engine**
- **Purpose**: Identify patterns and relationships across sources
- **Capabilities**:
  - Temporal correlation (before/after/during)
  - Causal chain construction
  - Anomaly detection
  - Pattern mining

#### 4. **Semantic Query Layer**
- **Purpose**: Translate natural language queries to database operations
- **Features**:
  - Query planning and optimization
  - Cross-source JOIN strategies
  - Result ranking and filtering
  - Aggregation and summarization

## Data Model

### Core Schema

```sql
-- Main context table (polymorphic design)
CREATE TABLE context_items (
    -- Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_type VARCHAR(50) NOT NULL, -- 'chat', 'code', 'git', 'error', 'ci', 'api', 'monitor'
    source_id VARCHAR(255) NOT NULL, -- Original ID in source system
    entity_type VARCHAR(100) NOT NULL, -- 'message', 'function', 'commit', 'error', etc.

    -- Temporal
    timestamp TIMESTAMPTZ NOT NULL,
    timestamp_end TIMESTAMPTZ, -- For time ranges
    ingested_at TIMESTAMPTZ DEFAULT NOW(),

    -- Content
    title TEXT, -- Quick identifier/summary
    content TEXT, -- Full searchable content
    content_hash VARCHAR(64), -- SHA256 for deduplication
    summary TEXT, -- AI-generated summary

    -- Location Context
    project_id VARCHAR(255),
    file_path TEXT,
    line_start INTEGER,
    line_end INTEGER,
    function_name VARCHAR(255),
    class_name VARCHAR(255),
    module_name VARCHAR(255),

    -- Actor Information
    actor_id VARCHAR(255),
    actor_type VARCHAR(50), -- 'human', 'system', 'ai', 'bot'
    actor_name TEXT,

    -- Classification
    severity VARCHAR(20), -- 'debug', 'info', 'warning', 'error', 'critical'
    category VARCHAR(100), -- Domain-specific categorization
    tags TEXT[], -- Array of tags for filtering

    -- Metrics (source-specific numeric data)
    metrics JSONB, -- {'complexity': 10, 'coverage': 85, 'duration': 1500}

    -- Search Optimization
    embedding vector(1536), -- For semantic search
    search_vector tsvector, -- For full-text search

    -- Source-Specific Data
    source_data JSONB, -- Original data preserved

    -- Indexes
    CONSTRAINT unique_source_id UNIQUE(source_type, source_id)
);

-- Indexes for performance
CREATE INDEX idx_context_timestamp ON context_items(timestamp DESC);
CREATE INDEX idx_context_source ON context_items(source_type, entity_type);
CREATE INDEX idx_context_file ON context_items(file_path) WHERE file_path IS NOT NULL;
CREATE INDEX idx_context_actor ON context_items(actor_id) WHERE actor_id IS NOT NULL;
CREATE INDEX idx_context_search ON context_items USING GIN(search_vector);
CREATE INDEX idx_context_embedding ON context_items USING ivfflat(embedding vector_cosine_ops);
CREATE INDEX idx_context_tags ON context_items USING GIN(tags);
CREATE INDEX idx_context_metrics ON context_items USING GIN(metrics);

-- Relationships table
CREATE TABLE context_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID REFERENCES context_items(id) ON DELETE CASCADE,
    target_id UUID REFERENCES context_items(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) NOT NULL, -- 'causes', 'references', 'contains', 'follows'
    confidence FLOAT DEFAULT 1.0,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT unique_relationship UNIQUE(source_id, target_id, relationship_type)
);

CREATE INDEX idx_rel_source ON context_relationships(source_id);
CREATE INDEX idx_rel_target ON context_relationships(target_id);
CREATE INDEX idx_rel_type ON context_relationships(relationship_type);

-- Correlation patterns table (learned patterns)
CREATE TABLE correlation_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern_name VARCHAR(255) NOT NULL,
    pattern_type VARCHAR(50), -- 'temporal', 'causal', 'co-occurrence'
    source_criteria JSONB NOT NULL, -- Criteria for source events
    target_criteria JSONB NOT NULL, -- Criteria for target events
    confidence FLOAT,
    support_count INTEGER DEFAULT 0,
    avg_time_delta INTERVAL,
    metadata JSONB,
    discovered_at TIMESTAMPTZ DEFAULT NOW(),
    last_matched TIMESTAMPTZ
);

-- Aggregated metrics table (for performance)
CREATE TABLE context_metrics_hourly (
    time_bucket TIMESTAMPTZ NOT NULL,
    source_type VARCHAR(50) NOT NULL,
    entity_type VARCHAR(100),
    project_id VARCHAR(255),

    -- Counts
    item_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,

    -- Aggregated metrics
    avg_response_time FLOAT,
    p95_response_time FLOAT,
    total_duration FLOAT,

    -- Rates
    error_rate FLOAT,
    throughput FLOAT,

    PRIMARY KEY (time_bucket, source_type, entity_type, project_id)
);

-- Create hypertable for time-series optimization
SELECT create_hypertable('context_items', 'timestamp');
SELECT create_hypertable('context_metrics_hourly', 'time_bucket');
```

### Data Type Mappings

```yaml
# Source Type → Entity Types
chat:
  - message
  - tool_use
  - conversation
  - decision

code:
  - file
  - function
  - class
  - import
  - symbol

git:
  - commit
  - branch
  - tag
  - pr
  - review

error:
  - exception
  - warning
  - stack_trace
  - crash

ci:
  - build
  - test_run
  - deployment
  - artifact

api:
  - request
  - response
  - endpoint
  - rate_limit

monitor:
  - metric
  - alert
  - incident
  - health_check
```

## Ingestion Pipelines

### Pipeline Architecture

```python
# Base ingestion pipeline
class IngestionPipeline:
    async def ingest(self, raw_data: Dict) -> ContextItem:
        # 1. Validate
        validated = await self.validate(raw_data)

        # 2. Transform
        normalized = await self.normalize(validated)

        # 3. Deduplicate
        if await self.is_duplicate(normalized):
            return await self.handle_duplicate(normalized)

        # 4. Enrich
        enriched = await self.enrich(normalized)

        # 5. Generate embeddings
        enriched.embedding = await self.generate_embedding(enriched.content)

        # 6. Extract relationships
        relationships = await self.extract_relationships(enriched)

        # 7. Store
        item = await self.store(enriched)
        await self.store_relationships(item.id, relationships)

        # 8. Trigger correlations
        await self.trigger_correlation_analysis(item)

        return item
```

### Source-Specific Pipelines

#### Chat Log Pipeline
```python
class ChatLogPipeline(IngestionPipeline):
    def normalize(self, msg):
        return ContextItem(
            source_type='chat',
            entity_type='message',
            source_id=msg['message_id'],
            timestamp=msg['timestamp'],
            content=msg['content'],
            actor_id=msg['sender_id'],
            actor_type='human' if msg['is_human'] else 'ai',
            metrics={
                'tokens': msg['token_count'],
                'cost': msg['cost'],
                'response_time': msg['response_time_ms']
            },
            source_data=msg
        )

    def extract_relationships(self, item):
        # Extract mentioned files, functions, errors
        files = extract_file_references(item.content)
        functions = extract_function_references(item.content)
        errors = extract_error_references(item.content)

        return [
            Relationship(target_id=f, type='references')
            for f in files + functions + errors
        ]
```

#### Code Intelligence Pipeline
```python
class CodeIntelPipeline(IngestionPipeline):
    def normalize(self, code_data):
        items = []

        # File-level item
        file_item = ContextItem(
            source_type='code',
            entity_type='file',
            source_id=f"file:{code_data['path']}",
            file_path=code_data['path'],
            content=code_data['content'],
            metrics={
                'lines': code_data['metrics']['lines'],
                'complexity': code_data['metrics']['complexity'],
                'coverage': code_data['metrics'].get('coverage')
            }
        )
        items.append(file_item)

        # Function-level items
        for func in code_data['functions']:
            func_item = ContextItem(
                source_type='code',
                entity_type='function',
                source_id=f"func:{code_data['path']}:{func['name']}",
                file_path=code_data['path'],
                function_name=func['name'],
                line_start=func['line_start'],
                line_end=func['line_end'],
                content=func['signature'] + '\n' + func.get('docstring', ''),
                metrics={
                    'complexity': func['complexity'],
                    'parameters': len(func['parameters'])
                }
            )
            items.append(func_item)

        return items
```

#### Error Log Pipeline
```python
class ErrorLogPipeline(IngestionPipeline):
    def normalize(self, error):
        return ContextItem(
            source_type='error',
            entity_type='exception',
            source_id=error['error_id'],
            timestamp=error['timestamp'],
            title=f"{error['error_type']}: {error['message'][:100]}",
            content=error['stack_trace'],
            file_path=error.get('file'),
            line_start=error.get('line'),
            function_name=error.get('function'),
            severity=error['severity'],
            metrics={
                'occurrence_count': error.get('count', 1),
                'affected_users': error.get('user_count', 0)
            },
            source_data=error
        )

    async def trigger_correlation_analysis(self, item):
        # Look for recent code changes that might have caused this
        recent_commits = await find_recent_commits(
            file=item.file_path,
            before=item.timestamp,
            limit=10
        )

        for commit in recent_commits:
            await analyze_error_commit_correlation(item, commit)
```

## Query Patterns

### Semantic Query Examples

```python
# Natural language → SQL/Graph queries

"What errors occurred after the last deployment?"
→ SELECT * FROM context_items
  WHERE source_type = 'error'
  AND timestamp > (
    SELECT timestamp FROM context_items
    WHERE entity_type = 'deployment'
    ORDER BY timestamp DESC LIMIT 1
  )

"Show me all context about the auth system"
→ SELECT * FROM context_items
  WHERE search_vector @@ plainto_tsquery('auth authentication login')
  OR file_path LIKE '%auth%'
  OR function_name LIKE '%auth%'
  ORDER BY ts_rank(search_vector, plainto_tsquery('auth')) DESC

"What did developers struggle with in this module?"
→ WITH module_files AS (
    SELECT DISTINCT file_path FROM context_items
    WHERE file_path LIKE '%/module_name/%'
  ),
  related_chats AS (
    SELECT c.*, r.target_id
    FROM context_items c
    JOIN context_relationships r ON c.id = r.source_id
    WHERE c.source_type = 'chat'
    AND r.target_id IN (SELECT id FROM context_items WHERE file_path IN (SELECT * FROM module_files))
  )
  SELECT
    COUNT(*) as discussion_count,
    AVG(metrics->>'tokens') as avg_discussion_length,
    array_agg(DISTINCT title) as topics
  FROM related_chats
  GROUP BY date_trunc('week', timestamp)
```

### Correlation Queries

```python
class CorrelationQueries:
    @staticmethod
    async def find_error_causes(error_id: str):
        """Find potential causes of an error"""
        query = """
        WITH error_time AS (
            SELECT timestamp, file_path, function_name
            FROM context_items
            WHERE id = $1
        )
        SELECT
            ci.*,
            EXTRACT(EPOCH FROM (et.timestamp - ci.timestamp)) as seconds_before_error
        FROM context_items ci, error_time et
        WHERE ci.timestamp BETWEEN et.timestamp - INTERVAL '1 hour' AND et.timestamp
        AND (
            (ci.source_type = 'git' AND ci.entity_type = 'commit')
            OR (ci.source_type = 'ci' AND ci.entity_type = 'deployment')
            OR (ci.source_type = 'code' AND ci.file_path = et.file_path)
        )
        ORDER BY ci.timestamp DESC
        """
        return await db.fetch(query, error_id)

    @staticmethod
    async def find_impact_radius(file_path: str):
        """Find everything affected by a file"""
        query = """
        WITH RECURSIVE impact AS (
            -- Start with the file
            SELECT id, file_path, 0 as depth
            FROM context_items
            WHERE file_path = $1

            UNION

            -- Find everything that references it
            SELECT ci.id, ci.file_path, impact.depth + 1
            FROM context_items ci
            JOIN context_relationships r ON ci.id = r.source_id
            JOIN impact ON r.target_id = impact.id
            WHERE impact.depth < 3
        )
        SELECT DISTINCT
            source_type,
            entity_type,
            COUNT(*) as impact_count
        FROM context_items
        WHERE id IN (SELECT id FROM impact)
        GROUP BY source_type, entity_type
        """
        return await db.fetch(query, file_path)
```

## Use Cases

### 1. Predictive Debugging
```python
async def predict_failure_risk(change: CodeChange) -> RiskAssessment:
    # Find historical patterns
    similar_changes = await find_similar_changes(change)

    # Calculate failure rate
    failure_rate = await calculate_historical_failure_rate(similar_changes)

    # Identify common failure modes
    common_errors = await find_common_errors_after_changes(similar_changes)

    return RiskAssessment(
        risk_score=failure_rate,
        likely_errors=common_errors,
        mitigation_suggestions=await generate_mitigations(common_errors)
    )
```

### 2. Knowledge Gap Detection
```python
async def find_knowledge_gaps(project_id: str) -> List[KnowledgeGap]:
    # Find frequently discussed but undocumented code
    query = """
    WITH chat_refs AS (
        SELECT
            file_path,
            COUNT(*) as discussion_count,
            AVG(metrics->>'tokens') as avg_length
        FROM context_items
        WHERE source_type = 'chat'
        AND file_path IS NOT NULL
        GROUP BY file_path
    ),
    doc_coverage AS (
        SELECT
            file_path,
            metrics->>'doc_coverage' as coverage
        FROM context_items
        WHERE source_type = 'code'
        AND entity_type = 'file'
    )
    SELECT
        cr.file_path,
        cr.discussion_count,
        cr.avg_length,
        COALESCE(dc.coverage::float, 0) as doc_coverage
    FROM chat_refs cr
    LEFT JOIN doc_coverage dc ON cr.file_path = dc.file_path
    WHERE cr.discussion_count > 5
    AND COALESCE(dc.coverage::float, 0) < 30
    ORDER BY cr.discussion_count DESC
    """

    return await identify_gaps(query)
```

### 3. Context Transfer
```python
async def get_developer_context(file_path: str, developer_id: str) -> DeveloperContext:
    # Get all context from previous developers
    query = """
    SELECT
        ci.*,
        'Previously encountered' as context_type
    FROM context_items ci
    WHERE ci.file_path = $1
    AND ci.actor_id != $2
    AND ci.source_type IN ('chat', 'error', 'git')
    ORDER BY ci.timestamp DESC
    LIMIT 50
    """

    previous_context = await db.fetch(query, file_path, developer_id)

    return DeveloperContext(
        previous_discussions=filter_chats(previous_context),
        previous_errors=filter_errors(previous_context),
        previous_changes=filter_commits(previous_context),
        suggestions=await generate_suggestions(previous_context)
    )
```

## Implementation Roadmap

### Phase 1: Foundation (Week 1-2)
- [ ] Set up PostgreSQL with TimescaleDB and pgvector
- [ ] Implement core schema
- [ ] Create base ingestion pipeline
- [ ] Build chat log adapter
- [ ] Build code intelligence adapter
- [ ] Basic query interface

### Phase 2: Core Ingestion (Week 3-4)
- [ ] Git history adapter
- [ ] Error log adapter
- [ ] CI/CD adapter
- [ ] Deduplication system
- [ ] Embedding generation
- [ ] Relationship extraction

### Phase 3: Correlation Engine (Week 5-6)
- [ ] Temporal correlation
- [ ] Causal chain analysis
- [ ] Pattern detection
- [ ] Anomaly detection
- [ ] Correlation storage

### Phase 4: Query Layer (Week 7-8)
- [ ] Natural language parser
- [ ] Query planner
- [ ] Cross-source aggregation
- [ ] Result ranking
- [ ] Caching layer

### Phase 5: MCP Integration (Week 9-10)
- [ ] Update MCP tool definitions
- [ ] Implement 21 semantic tools
- [ ] Real-time subscriptions
- [ ] WebSocket support
- [ ] Performance optimization

### Phase 6: Advanced Features (Week 11-12)
- [ ] Machine learning patterns
- [ ] Auto-summarization
- [ ] Predictive analytics
- [ ] Knowledge gap automation
- [ ] Impact analysis

## Performance Considerations

### Optimization Strategies
1. **Partitioning**: Partition by timestamp (monthly)
2. **Compression**: Enable TimescaleDB compression for old data
3. **Materialized Views**: For common aggregations
4. **Connection Pooling**: PgBouncer for connection management
5. **Caching**: Redis for query results
6. **Async Processing**: Background jobs for heavy computation

### Scalability Targets
- 100M+ context items
- 1M+ items ingested daily
- Sub-second query response
- 100+ concurrent users
- Real-time updates < 100ms latency

## Security & Privacy

### Data Protection
- Encryption at rest (PostgreSQL TDE)
- Encryption in transit (TLS)
- Row-level security for multi-tenant
- Audit logging for all access
- PII detection and masking

### Access Control
- Role-based access (RBAC)
- Project-level isolation
- API key authentication
- Rate limiting
- Query complexity limits

## Monitoring & Observability

### Key Metrics
- Ingestion rate by source
- Query response times
- Cache hit rates
- Correlation accuracy
- Storage growth rate
- Error rates by pipeline

### Dashboards
- System health overview
- Ingestion pipeline status
- Query performance
- Correlation patterns
- Knowledge gap trends
- User activity

## Conclusion

The Unified Context System represents a paradigm shift in how we understand and interact with software development data. By unifying disparate sources into a temporal knowledge graph, we enable:

1. **Predictive Intelligence**: Anticipate problems before they occur
2. **Contextual Understanding**: See the full story behind code
3. **Knowledge Preservation**: Capture and transfer understanding
4. **Impact Visibility**: Understand consequences across the system
5. **Developer Acceleration**: Reduce time to understanding

This system transforms reactive debugging into proactive prevention, isolated changes into understood impacts, and fragmented knowledge into unified intelligence.

---

*Document Version: 1.0*
*Last Updated: 2024*
*Status: Design Phase*
