# UNIFIED CONTEXT SYSTEM - FINAL DESIGN & IMPLEMENTATION GUIDE

## Executive Summary

We are building a **Unified Context System** that combines all development intelligence into a single, queryable platform using **PostgreSQL (with TimescaleDB) as the primary data store** and **Neo4j for relationship intelligence**. All existing systems will integrate through standardized APIs.

## 1. INSTRUCTIONS FOR EACH TEAM

### For Chat/Intel Dashboard Team

**YOUR MISSION**: Migrate from SQLite to PostgreSQL and implement the correlation features you designed.

**IMMEDIATE ACTIONS**:
1. **Keep SQLite running** during migration (dual-write pattern)
2. **Implement PostgreSQL schema** below (Section 3)
3. **Add your correlation tables** that were never created due to SQL errors
4. **Build ingestion pipeline** from .proj-intel to PostgreSQL
5. **Connect to Neo4j** for relationship extraction

**KEY POINTS**:
- Your correlation design was excellent - now implement it in PostgreSQL
- Use JSONB for all the JSON fields you had as TEXT
- Add TimescaleDB for time-series optimization
- Your dashboard can keep using SQLite during transition

### For Claude Monitor Team

**YOUR MISSION**: Keep real-time monitoring but redirect data to PostgreSQL for persistence.

**IMMEDIATE ACTIONS**:
1. **Keep collectors as-is** - they work great
2. **Add PostgreSQL sink** alongside SQLite
3. **Stream metrics to TimescaleDB** tables
4. **Maintain WebSocket** for real-time UI
5. **Extract relationships** to Neo4j

**KEY POINTS**:
- Your real-time architecture is perfect - don't change it
- Just add PostgreSQL as a persistence layer
- Keep Redis for pub/sub
- Your terminal UI remains unchanged

### For Project-Context Team

**YOUR MISSION**: Become the semantic query layer over the unified database.

**IMMEDIATE ACTIONS**:
1. **Stop trying to read files directly**
2. **Query PostgreSQL** for all data
3. **Use Neo4j** for relationship traversal
4. **Implement the 21 MCP tools** as queries
5. **Add Context Bridge** integration

**KEY POINTS**:
- You're the query interface, not a data collector
- All data comes from the unified DB
- Focus on semantic tool implementation
- Cache aggressively for performance

## 2. SYSTEM ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACES                              │
├──────────────┬──────────────┬──────────────┬───────────────────────┤
│ Chat Dashboard│ Claude Monitor│ Project-Context│  Other MCP Tools   │
│   (Flask)    │  (Rich TUI)   │   (FastMCP)    │                     │
└──────────────┴──────────────┴──────────────┴───────────────────────┘
                                      │
                    ┌─────────────────┴─────────────────┐
                    │      UNIFIED QUERY LAYER          │
                    │   (GraphQL or REST API)           │
                    └─────────────────┬─────────────────┘
                                      │
        ┌─────────────────────────────┴─────────────────────────┐
        │                                                         │
┌───────▼────────┐                                    ┌──────────▼────────┐
│   PostgreSQL   │                                    │      Neo4j        │
│  (TimescaleDB) │◄───────────────────────────────────│  (Graph Store)    │
│                │                                    │                   │
│  Source of     │         Relationships              │  - Knowledge      │
│  Truth for:    │         Extracted To               │  - Correlations   │
│  - Chat logs   │──────────────────────────────────►│  - Dependencies   │
│  - Code intel  │                                    │  - Impact chains  │
│  - Monitoring  │                                    │                   │
│  - IDE context │                                    └───────────────────┘
└────────────────┘
        ▲
        │ Data Ingestion
┌───────┴────────┬──────────────┬──────────────┬────────────────┐
│ Chat Logs      │ .proj-intel  │ Claude Monitor│ Context Bridge │
│ (Real-time)    │ (Batch)      │ (Streaming)   │ (Real-time)    │
└────────────────┴──────────────┴──────────────┴────────────────┘
```

## 3. POSTGRESQL MASTER SCHEMA

```sql
-- Enable extensions
CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS pgvector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- For fuzzy text search

-- ============================================
-- CORE CONTEXT TABLE (All events/items)
-- ============================================
CREATE TABLE context_items (
    -- Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_type VARCHAR(50) NOT NULL, -- 'chat', 'code', 'monitor', 'ide', 'git'
    source_id VARCHAR(255) NOT NULL,  -- Original ID from source system
    entity_type VARCHAR(100) NOT NULL, -- 'message', 'file', 'function', 'metric'

    -- Temporal
    timestamp TIMESTAMPTZ NOT NULL,
    timestamp_end TIMESTAMPTZ,  -- For duration events
    ingested_at TIMESTAMPTZ DEFAULT NOW(),

    -- Content
    title TEXT,
    content TEXT,  -- Full searchable content
    content_hash VARCHAR(64),  -- For deduplication
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

    -- Metrics & Data
    metrics JSONB,  -- Flexible metrics storage
    source_data JSONB,  -- Original data preserved

    -- Search Optimization
    embedding vector(1536),  -- For semantic search
    search_vector tsvector,  -- For full-text search

    -- Neo4j Reference
    neo4j_node_id VARCHAR(255),  -- Link to Neo4j if relationship exists

    CONSTRAINT unique_source UNIQUE(source_type, source_id)
);

-- Create hypertable for time-series optimization
SELECT create_hypertable('context_items', 'timestamp',
    chunk_time_interval => INTERVAL '1 day');

-- ============================================
-- CHAT SESSIONS (Existing structure, enhanced)
-- ============================================
CREATE TABLE chat_sessions (
    id VARCHAR(255) PRIMARY KEY,
    started_at TIMESTAMPTZ NOT NULL,
    ended_at TIMESTAMPTZ,
    user_id VARCHAR(255),
    project_path TEXT,
    total_tokens INTEGER DEFAULT 0,
    total_cost NUMERIC(10,4) DEFAULT 0,
    model_used VARCHAR(100),
    session_metadata JSONB,

    -- New fields for correlation
    primary_files TEXT[],  -- Main files discussed
    error_count INTEGER DEFAULT 0,
    tool_use_count INTEGER DEFAULT 0,
    neo4j_node_id VARCHAR(255)
);

-- ============================================
-- CODE INTELLIGENCE (From .proj-intel)
-- ============================================
CREATE TABLE code_elements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_path TEXT NOT NULL,
    element_type VARCHAR(50), -- 'file', 'function', 'class', 'import'
    element_name VARCHAR(255),
    signature TEXT,
    docstring TEXT,
    line_start INTEGER,
    line_end INTEGER,

    -- Metrics
    complexity_score NUMERIC,
    test_coverage NUMERIC,
    dependencies JSONB,  -- List of dependencies

    -- Metadata
    language VARCHAR(50),
    last_modified TIMESTAMPTZ,
    content_hash VARCHAR(64),
    proj_intel_data JSONB,  -- Full .proj-intel data

    -- Search
    search_vector tsvector,
    embedding vector(1536),

    -- Neo4j
    neo4j_node_id VARCHAR(255),

    UNIQUE(file_path, element_type, element_name, line_start)
);

-- ============================================
-- MONITORING METRICS (From claude-monitor)
-- ============================================
CREATE TABLE monitoring_metrics (
    time TIMESTAMPTZ NOT NULL,
    source VARCHAR(50) NOT NULL, -- 'system', 'docker', 'agent'
    metric_name VARCHAR(100) NOT NULL,
    metric_value NUMERIC,

    -- Dimensions
    container_id VARCHAR(255),
    agent_token VARCHAR(50),
    process_id INTEGER,

    -- Additional data
    labels JSONB,
    metadata JSONB,

    PRIMARY KEY (time, source, metric_name,
                 COALESCE(container_id, ''),
                 COALESCE(agent_token, ''))
);

SELECT create_hypertable('monitoring_metrics', 'time',
    chunk_time_interval => INTERVAL '1 hour');

-- ============================================
-- IDE CONTEXT (From context-bridge)
-- ============================================
CREATE TABLE ide_context_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ NOT NULL,
    active_file TEXT,
    selected_text TEXT,
    cursor_position JSONB,

    -- Diagnostics
    error_count INTEGER DEFAULT 0,
    warning_count INTEGER DEFAULT 0,
    diagnostics JSONB,  -- Full diagnostic details

    -- Environment
    project_root TEXT,
    open_files TEXT[],
    recent_files TEXT[],

    -- Session link
    session_id VARCHAR(255),

    -- Search
    search_vector tsvector
);

SELECT create_hypertable('ide_context_snapshots', 'timestamp',
    chunk_time_interval => INTERVAL '1 hour');

-- ============================================
-- CORRELATION TABLES (From chat/intel team)
-- ============================================
CREATE TABLE code_context (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    file_path TEXT,
    symbols JSONB,  -- List of symbols discussed
    content_hash VARCHAR(64),
    change_type VARCHAR(50),

    -- Links
    chat_session_id VARCHAR(255) REFERENCES chat_sessions(id),
    code_element_id UUID REFERENCES code_elements(id),
    neo4j_node_id VARCHAR(255),

    -- Metrics
    relevance_score NUMERIC,
    discussion_depth INTEGER  -- How much was it discussed
);

CREATE TABLE agent_usage (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    agent_class VARCHAR(255),
    agent_token VARCHAR(50),
    task_description TEXT,

    -- Performance
    execution_time_ms INTEGER,
    tokens_used INTEGER,
    success BOOLEAN,

    -- Context
    file_paths TEXT[],
    methods_invoked JSONB,
    context_data JSONB,

    -- Links
    neo4j_node_id VARCHAR(255)
);

-- ============================================
-- INDEXES FOR PERFORMANCE
-- ============================================
-- Time-based queries
CREATE INDEX idx_context_timestamp ON context_items(timestamp DESC);
CREATE INDEX idx_sessions_time ON chat_sessions(started_at DESC);

-- Source-based queries
CREATE INDEX idx_context_source ON context_items(source_type, entity_type);
CREATE INDEX idx_context_session ON context_items(session_id);

-- File-based queries
CREATE INDEX idx_context_file ON context_items(file_path) WHERE file_path IS NOT NULL;
CREATE INDEX idx_code_file ON code_elements(file_path);

-- Full-text search
CREATE INDEX idx_context_search ON context_items USING GIN(search_vector);
CREATE INDEX idx_code_search ON code_elements USING GIN(search_vector);

-- JSONB queries
CREATE INDEX idx_context_metrics ON context_items USING GIN(metrics);
CREATE INDEX idx_context_tags ON context_items USING GIN(tags);

-- Vector similarity search
CREATE INDEX idx_context_embedding ON context_items
    USING ivfflat(embedding vector_cosine_ops)
    WITH (lists = 100);

-- ============================================
-- MATERIALIZED VIEWS FOR COMMON QUERIES
-- ============================================
CREATE MATERIALIZED VIEW hourly_token_usage AS
SELECT
    time_bucket('1 hour', timestamp) AS hour,
    source_type,
    SUM((metrics->>'tokens_input')::int) as total_input_tokens,
    SUM((metrics->>'tokens_output')::int) as total_output_tokens,
    SUM((metrics->>'cost')::numeric) as total_cost,
    COUNT(DISTINCT session_id) as unique_sessions
FROM context_items
WHERE source_type IN ('chat', 'agent')
GROUP BY hour, source_type;

CREATE MATERIALIZED VIEW daily_file_activity AS
SELECT
    time_bucket('1 day', timestamp) AS day,
    file_path,
    COUNT(*) as touch_count,
    COUNT(DISTINCT session_id) as session_count,
    array_agg(DISTINCT entity_type) as activity_types
FROM context_items
WHERE file_path IS NOT NULL
GROUP BY day, file_path;

-- Refresh views periodically
CREATE OR REPLACE FUNCTION refresh_materialized_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY hourly_token_usage;
    REFRESH MATERIALIZED VIEW CONCURRENTLY daily_file_activity;
END;
$$ LANGUAGE plpgsql;

-- Schedule refresh every hour
-- (Requires pg_cron extension or external scheduler)
```

## 4. NEO4J SCHEMA

```cypher
// ============================================
// NODE TYPES
// ============================================

// Knowledge nodes (existing)
(k:Knowledge {
    knowledge_id: "string",
    content: "string",
    embedding: [float],
    confidence: float,
    created_at: datetime
})

// Chat Session nodes
(s:Session {
    session_id: "string",
    started_at: datetime,
    user_id: "string",
    project: "string",
    postgres_id: "string"  // Link back to PostgreSQL
})

// Code Element nodes
(c:CodeElement {
    element_id: "string",
    file_path: "string",
    element_type: "string",
    name: "string",
    postgres_id: "string"
})

// File nodes
(f:File {
    path: "string",
    language: "string",
    last_modified: datetime
})

// Error nodes
(e:Error {
    error_id: "string",
    type: "string",
    message: "string",
    first_seen: datetime
})

// Container nodes
(cont:Container {
    container_id: "string",
    name: "string",
    image: "string"
})

// Agent nodes
(a:Agent {
    agent_token: "string",
    agent_type: "string"
})

// ============================================
// RELATIONSHIP TYPES
// ============================================

// Knowledge relationships
(k1:Knowledge)-[:RELATED_TO {strength: float}]->(k2:Knowledge)
(k:Knowledge)-[:DERIVED_FROM]->(s:Session)

// Session relationships
(s:Session)-[:DISCUSSED]->(f:File)
(s:Session)-[:REFERENCED]->(c:CodeElement)
(s:Session)-[:ENCOUNTERED]->(e:Error)
(s:Session)-[:USED_AGENT]->(a:Agent)

// Code relationships
(c1:CodeElement)-[:CALLS]->(c2:CodeElement)
(c:CodeElement)-[:BELONGS_TO]->(f:File)
(c1:CodeElement)-[:DEPENDS_ON]->(c2:CodeElement)
(f1:File)-[:IMPORTS]->(f2:File)

// Error relationships
(e:Error)-[:OCCURRED_IN]->(f:File)
(e:Error)-[:CAUSED_BY]->(c:CodeElement)
(e:Error)-[:FIXED_IN]->(s:Session)

// Container relationships
(cont:Container)-[:RUNS]->(s:Session)
(cont:Container)-[:USES_AGENT]->(a:Agent)

// Agent relationships
(a:Agent)-[:EXECUTED_TASK {
    timestamp: datetime,
    duration_ms: int,
    success: boolean
}]->(task:Task)

// ============================================
// INDEXES FOR PERFORMANCE
// ============================================
CREATE INDEX ON :Knowledge(knowledge_id);
CREATE INDEX ON :Session(session_id);
CREATE INDEX ON :CodeElement(element_id);
CREATE INDEX ON :File(path);
CREATE INDEX ON :Error(type);
CREATE INDEX ON :Container(container_id);
CREATE INDEX ON :Agent(agent_token);

// Full-text indexes
CALL db.index.fulltext.createNodeIndex(
    "knowledge_search",
    ["Knowledge"],
    ["content", "summary"]
);

CALL db.index.fulltext.createNodeIndex(
    "code_search",
    ["CodeElement"],
    ["name", "docstring"]
);
```

## 5. DATA FLOW & INTEGRATION

### A. Ingestion Pipelines

```python
# 1. CHAT LOGS PIPELINE
async def ingest_chat_message(message):
    # Store in PostgreSQL
    pg_id = await postgres.insert("""
        INSERT INTO context_items (
            source_type, entity_type, timestamp,
            content, session_id, actor_type, metrics
        ) VALUES ('chat', 'message', %s, %s, %s, %s, %s)
        RETURNING id
    """, ...)

    # Extract entities for Neo4j
    files = extract_file_references(message.content)
    for file in files:
        await neo4j.run("""
            MATCH (s:Session {session_id: $sid})
            MERGE (f:File {path: $path})
            CREATE (s)-[:DISCUSSED {timestamp: $ts}]->(f)
        """, sid=session_id, path=file, ts=timestamp)

    # Publish to Context Bridge
    await redis.publish('context:update', {
        'type': 'chat_message',
        'session_id': session_id,
        'files': files
    })

# 2. CODE INTELLIGENCE PIPELINE
async def ingest_proj_intel(jsonl_path):
    # Parse .proj-intel file
    for line in read_jsonl(jsonl_path):
        # Store in PostgreSQL
        await postgres.insert("""
            INSERT INTO code_elements (
                file_path, element_type, element_name,
                line_start, complexity_score, proj_intel_data
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """, ...)

        # Create Neo4j nodes
        await neo4j.run("""
            MERGE (f:File {path: $path})
            MERGE (c:CodeElement {
                element_id: $id,
                type: $type,
                name: $name
            })
            CREATE (c)-[:BELONGS_TO]->(f)
        """, ...)

# 3. MONITORING PIPELINE
async def ingest_monitoring_metric(metric):
    # Store time-series in PostgreSQL
    await postgres.insert("""
        INSERT INTO monitoring_metrics (
            time, source, metric_name, metric_value,
            container_id, metadata
        ) VALUES (%s, %s, %s, %s, %s, %s)
    """, ...)

    # Update Neo4j if threshold exceeded
    if metric.value > threshold:
        await neo4j.run("""
            MERGE (c:Container {container_id: $cid})
            SET c.high_resource_usage = true,
                c.last_alert = datetime()
        """, cid=metric.container_id)

# 4. IDE CONTEXT PIPELINE
async def ingest_ide_context(context):
    # Snapshot to PostgreSQL
    await postgres.insert("""
        INSERT INTO ide_context_snapshots (
            timestamp, active_file, error_count,
            diagnostics, session_id
        ) VALUES (%s, %s, %s, %s, %s)
    """, ...)

    # Update current context in Redis
    await redis.set('context:current', context.json())

    # Publish change event
    await redis.publish('context:events', {
        'type': 'FILE_CHANGED',
        'file': context.active_file
    })
```

### B. Query Patterns

```python
# UNIFIED QUERY API
class UnifiedContextAPI:

    async def get_file_context(self, file_path: str):
        """Get all context for a file across all sources"""

        # 1. Get code intelligence from PostgreSQL
        code_data = await postgres.fetch("""
            SELECT * FROM code_elements
            WHERE file_path = %s
        """, file_path)

        # 2. Get chat discussions from PostgreSQL
        discussions = await postgres.fetch("""
            SELECT * FROM context_items
            WHERE file_path = %s
            AND source_type = 'chat'
            ORDER BY timestamp DESC
        """, file_path)

        # 3. Get relationships from Neo4j
        relationships = await neo4j.run("""
            MATCH (f:File {path: $path})
            OPTIONAL MATCH (f)<-[:BELONGS_TO]-(c:CodeElement)
            OPTIONAL MATCH (f)<-[:DISCUSSED]-(s:Session)
            OPTIONAL MATCH (f)<-[:OCCURRED_IN]-(e:Error)
            RETURN f, collect(c) as elements,
                   collect(s) as sessions,
                   collect(e) as errors
        """, path=file_path)

        # 4. Get current IDE context from Redis
        current_context = await redis.get('context:current')

        # 5. Combine and return
        return {
            'code': code_data,
            'discussions': discussions,
            'relationships': relationships,
            'current_ide_state': current_context,
            'metrics': await self.get_file_metrics(file_path)
        }

    async def find_similar_errors(self, error_message: str):
        """Find similar errors using embeddings"""

        # Generate embedding
        embedding = await generate_embedding(error_message)

        # Query PostgreSQL with pgvector
        similar = await postgres.fetch("""
            SELECT *,
                   1 - (embedding <=> %s) as similarity
            FROM context_items
            WHERE entity_type = 'error'
            ORDER BY embedding <=> %s
            LIMIT 10
        """, embedding, embedding)

        # Get solutions from Neo4j
        for error in similar:
            solutions = await neo4j.run("""
                MATCH (e:Error {error_id: $id})
                OPTIONAL MATCH (e)-[:FIXED_IN]->(s:Session)
                RETURN s.session_id, s.summary
            """, id=error['id'])
            error['solutions'] = solutions

        return similar
```

### C. Real-time Subscriptions

```python
# WEBSOCKET API FOR REAL-TIME UPDATES
class RealtimeContextStream:

    async def subscribe_to_file(self, file_path: str, websocket):
        """Subscribe to all updates for a file"""

        # Subscribe to Redis channels
        pubsub = redis.pubsub()
        await pubsub.subscribe(
            f'file:{file_path}:*',
            'context:events'
        )

        # Stream updates to client
        async for message in pubsub.listen():
            if affects_file(message, file_path):
                await websocket.send_json({
                    'type': message['channel'],
                    'data': message['data'],
                    'timestamp': datetime.utcnow()
                })
```

## 6. MIGRATION PLAN

### Phase 1: Dual-Write (Week 1)
- Set up PostgreSQL with schema
- Implement dual-write to SQLite + PostgreSQL
- No breaking changes to existing systems

### Phase 2: Read Migration (Week 2)
- Update dashboards to read from PostgreSQL
- Keep SQLite as fallback
- Implement query layer

### Phase 3: Neo4j Integration (Week 3)
- Start extracting relationships
- Build knowledge graph
- Connect Context Bridge

### Phase 4: Deprecate SQLite (Week 4)
- Switch fully to PostgreSQL
- Archive SQLite databases
- Performance optimization

## 7. API CONTRACTS

### REST API Endpoints

```yaml
# Core Context API
GET /api/context/items
  params:
    - source_type: string
    - entity_type: string
    - session_id: string
    - file_path: string
    - time_range: string
    - limit: int

GET /api/context/items/{id}

POST /api/context/search
  body:
    query: string
    filters: object
    include_embeddings: boolean

# Session API
GET /api/sessions
GET /api/sessions/{id}
GET /api/sessions/{id}/context

# Code Intelligence API
GET /api/code/files
GET /api/code/files/{path}
GET /api/code/elements
GET /api/code/dependencies

# Monitoring API
GET /api/metrics
  params:
    - source: string
    - metric_name: string
    - time_range: string
    - aggregation: string

# Real-time WebSocket
WS /ws/subscribe
  messages:
    - subscribe: {channels: [string]}
    - unsubscribe: {channels: [string]}
```

### GraphQL Schema (Alternative)

```graphql
type Query {
  contextItems(
    sourceType: String
    entityType: String
    timeRange: TimeRange
    first: Int
  ): ContextItemConnection!

  session(id: ID!): Session

  file(path: String!): FileContext

  search(
    query: String!
    filters: SearchFilters
  ): SearchResults!
}

type Subscription {
  contextUpdates(
    channels: [String!]!
  ): ContextEvent!
}

type ContextItem {
  id: ID!
  sourceType: String!
  entityType: String!
  timestamp: DateTime!
  content: String
  metrics: JSON
  relationships: [Relationship!]!
}

type FileContext {
  path: String!
  codeElements: [CodeElement!]!
  discussions: [ContextItem!]!
  errors: [Error!]!
  currentIDEState: IDEContext
}
```

## 8. KEY DECISIONS & RATIONALE

### Why PostgreSQL + Neo4j (Not Everything in Neo4j)?
- **PostgreSQL**: Optimized for time-series, aggregations, full-text search
- **Neo4j**: Optimized for relationships, graph traversal, impact analysis
- **Best tool for each job** rather than forcing everything into one

### Why Keep Redis?
- **Real-time pub/sub** that's proven to work
- **Current IDE state** caching
- **Lightweight** for transient data

### Why Dual-Write During Migration?
- **Zero downtime** migration
- **Rollback capability** if issues arise
- **Gradual validation** of new system

## 9. SUCCESS METRICS

- Query performance: < 100ms for common queries
- Ingestion rate: > 10,000 events/second
- Storage efficiency: 50% reduction vs current
- Correlation accuracy: > 90% relevant results
- System availability: 99.9% uptime

## 10. COMMUNICATION TEMPLATE

### Message to Chat/Intel Dashboard Team:

"Implement the PostgreSQL schema in Section 3. Your correlation tables are now part of the master schema. Use JSONB for all JSON fields. Add TimescaleDB for time-series. Keep SQLite running during migration with dual-write pattern."

### Message to Claude Monitor Team:

"Keep your collectors unchanged. Add PostgreSQL sink using the monitoring_metrics table in Section 3. Stream to TimescaleDB for persistence while maintaining WebSocket for real-time. Extract container/agent relationships to Neo4j when thresholds exceeded."

### Message to Project-Context Team:

"Stop reading files directly. Implement the 21 MCP tools as queries against PostgreSQL + Neo4j using the patterns in Section 5B. Subscribe to Context Bridge for current IDE state. You're the semantic layer, not a collector."

## APPENDIX: Quick Reference

### Connection Strings
```bash
# PostgreSQL
postgresql://user:pass@localhost:5432/unified_context

# Neo4j
bolt://localhost:7687

# Redis
redis://localhost:6379

# Context Bridge MCP
ws://localhost:8001/context
```

### Required Extensions
```sql
CREATE EXTENSION timescaledb;
CREATE EXTENSION pgvector;
CREATE EXTENSION pg_trgm;
CREATE EXTENSION pg_cron;  -- For scheduled refreshes
```

### Environment Variables
```bash
POSTGRES_URL=postgresql://localhost:5432/unified_context
NEO4J_URL=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
REDIS_URL=redis://localhost:6379
CONTEXT_BRIDGE_URL=ws://localhost:8001
```

---

**This is the final, authoritative design. All teams should align with this architecture.**
