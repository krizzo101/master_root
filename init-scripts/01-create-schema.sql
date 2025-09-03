-- ============================================
-- UNIFIED CONTEXT SYSTEM - POSTGRESQL SCHEMA
-- Chat/Intel Team Correlation Tables Included
-- ============================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;
-- Note: pgvector may need special Docker image
-- CREATE EXTENSION IF NOT EXISTS vector;

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
    -- embedding vector(1536),  -- Uncomment when pgvector available
    search_vector tsvector,  -- For full-text search

    -- Neo4j Reference
    neo4j_node_id VARCHAR(255),  -- Link to Neo4j if relationship exists

    CONSTRAINT unique_source UNIQUE(source_type, source_id)
);

-- Create hypertable for time-series optimization
SELECT create_hypertable('context_items', 'timestamp',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE);

-- ============================================
-- CHAT SESSIONS (Existing structure, enhanced)
-- ============================================
CREATE TABLE IF NOT EXISTS chat_sessions (
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
CREATE TABLE IF NOT EXISTS code_elements (
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
    -- embedding vector(1536),  -- Uncomment when pgvector available

    -- Neo4j
    neo4j_node_id VARCHAR(255),

    UNIQUE(file_path, element_type, element_name, line_start)
);

-- ============================================
-- MONITORING METRICS (From claude-monitor)
-- ============================================
CREATE TABLE IF NOT EXISTS monitoring_metrics (
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
    chunk_time_interval => INTERVAL '1 hour',
    if_not_exists => TRUE);

-- ============================================
-- IDE CONTEXT (From context-bridge)
-- ============================================
CREATE TABLE IF NOT EXISTS ide_context_snapshots (
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
    chunk_time_interval => INTERVAL '1 hour',
    if_not_exists => TRUE);

-- ============================================
-- CORRELATION TABLES (From chat/intel team)
-- FINALLY WORKING IN POSTGRESQL!
-- ============================================
CREATE TABLE IF NOT EXISTS code_context (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    file_path TEXT,
    symbols JSONB,  -- List of symbols discussed (JSONB not TEXT!)
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

CREATE TABLE IF NOT EXISTS agent_usage (
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
    methods_invoked JSONB,  -- JSONB for flexible method data
    context_data JSONB,  -- JSONB for arbitrary context

    -- Links
    neo4j_node_id VARCHAR(255)
);

-- ============================================
-- Additional correlation tables we designed
-- ============================================
CREATE TABLE IF NOT EXISTS symbol_references (
    id SERIAL PRIMARY KEY,
    message_id VARCHAR(255),
    session_id VARCHAR(255) NOT NULL,
    symbol_name VARCHAR(255) NOT NULL,
    symbol_type VARCHAR(50),
    file_path TEXT,
    line_number INTEGER,
    reference_type VARCHAR(50),  -- 'mentioned', 'modified', 'created', 'deleted'
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS file_activity (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    file_path TEXT NOT NULL,
    action VARCHAR(50),  -- 'create', 'modify', 'delete', 'read'
    tool_used VARCHAR(100),
    functions_affected JSONB,
    classes_affected JSONB,
    before_hash VARCHAR(64),
    after_hash VARCHAR(64)
);

-- ============================================
-- INDEXES FOR PERFORMANCE
-- ============================================
-- Time-based queries
CREATE INDEX idx_context_timestamp ON context_items(timestamp DESC);
CREATE INDEX idx_sessions_time ON chat_sessions(started_at DESC);
CREATE INDEX idx_code_context_time ON code_context(timestamp DESC);
CREATE INDEX idx_agent_usage_time ON agent_usage(timestamp DESC);

-- Source-based queries
CREATE INDEX idx_context_source ON context_items(source_type, entity_type);
CREATE INDEX idx_context_session ON context_items(session_id);
CREATE INDEX idx_code_context_session ON code_context(session_id);
CREATE INDEX idx_agent_usage_session ON agent_usage(session_id);

-- File-based queries
CREATE INDEX idx_context_file ON context_items(file_path) WHERE file_path IS NOT NULL;
CREATE INDEX idx_code_file ON code_elements(file_path);
CREATE INDEX idx_code_context_file ON code_context(file_path);
CREATE INDEX idx_file_activity_file ON file_activity(file_path);

-- Symbol queries
CREATE INDEX idx_symbol_refs_name ON symbol_references(symbol_name);
CREATE INDEX idx_symbol_refs_session ON symbol_references(session_id);

-- Full-text search
CREATE INDEX idx_context_search ON context_items USING GIN(search_vector);
CREATE INDEX idx_code_search ON code_elements USING GIN(search_vector);

-- JSONB queries
CREATE INDEX idx_context_metrics ON context_items USING GIN(metrics);
CREATE INDEX idx_context_tags ON context_items USING GIN(tags);
CREATE INDEX idx_code_context_symbols ON code_context USING GIN(symbols);
CREATE INDEX idx_agent_methods ON agent_usage USING GIN(methods_invoked);

-- Vector similarity search (uncomment when pgvector available)
-- CREATE INDEX idx_context_embedding ON context_items
--     USING ivfflat(embedding vector_cosine_ops)
--     WITH (lists = 100);

-- ============================================
-- MATERIALIZED VIEWS FOR COMMON QUERIES
-- ============================================
CREATE MATERIALIZED VIEW IF NOT EXISTS hourly_token_usage AS
SELECT
    time_bucket('1 hour', timestamp) AS hour,
    source_type,
    SUM((metrics->>'tokens_input')::int) as total_input_tokens,
    SUM((metrics->>'tokens_output')::int) as total_output_tokens,
    SUM((metrics->>'cost')::numeric) as total_cost,
    COUNT(DISTINCT session_id) as unique_sessions
FROM context_items
WHERE source_type IN ('chat', 'agent')
  AND metrics ? 'tokens_input'
GROUP BY hour, source_type;

CREATE MATERIALIZED VIEW IF NOT EXISTS daily_file_activity AS
SELECT
    time_bucket('1 day', timestamp) AS day,
    file_path,
    COUNT(*) as touch_count,
    COUNT(DISTINCT session_id) as session_count,
    array_agg(DISTINCT entity_type) as activity_types
FROM context_items
WHERE file_path IS NOT NULL
GROUP BY day, file_path;

-- ============================================
-- HELPER FUNCTIONS
-- ============================================
CREATE OR REPLACE FUNCTION refresh_materialized_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY hourly_token_usage;
    REFRESH MATERIALIZED VIEW CONCURRENTLY daily_file_activity;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- Grant permissions
-- ============================================
-- Grant usage on schema
GRANT USAGE ON SCHEMA public TO opsvi;

-- Grant all privileges on all tables
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO opsvi;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO opsvi;

-- Grant execute on functions
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO opsvi;

-- Ensure future objects also get permissions
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT ALL ON TABLES TO opsvi;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT ALL ON SEQUENCES TO opsvi;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT EXECUTE ON FUNCTIONS TO opsvi;

-- ============================================
-- Success message
-- ============================================
DO $$
BEGIN
    RAISE NOTICE 'Schema created successfully!';
    RAISE NOTICE 'Chat/Intel correlation tables are ready:';
    RAISE NOTICE '  - code_context (with JSONB symbols)';
    RAISE NOTICE '  - agent_usage (with JSONB methods)';
    RAISE NOTICE '  - symbol_references';
    RAISE NOTICE '  - file_activity';
    RAISE NOTICE 'TimescaleDB hypertables created for time-series data';
END $$;
