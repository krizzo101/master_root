-- Performance Optimization Indexes for Production Chat Import
-- Generated: 2025-09-04
-- Target: 10x throughput improvement for GB-scale chat data processing

BEGIN;

-- =====================================================
-- PRIMARY PERFORMANCE INDEXES
-- =====================================================

-- Timestamp-based queries (most common for chat data)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_context_items_timestamp_btree
    ON context_items USING btree (timestamp DESC);

-- Session-based chat queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_context_items_session_timestamp
    ON context_items USING btree (session_id, timestamp DESC);

-- Source type filtering (essential for multi-adapter performance)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_context_items_source_type_timestamp
    ON context_items USING btree (source_type, timestamp DESC);

-- Actor-based queries (user activity analysis)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_context_items_actor_timestamp
    ON context_items USING btree (actor_id, timestamp DESC);

-- Content hash for deduplication (performance critical)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_context_items_content_hash
    ON context_items USING btree (content_hash);

-- =====================================================
-- EMBEDDING AND VECTOR SEARCH OPTIMIZATION
-- =====================================================

-- Vector similarity search (requires pgvector extension)
-- Optimized for cosine similarity (most common for embeddings)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_context_items_embedding_cosine
    ON context_items USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 1000);  -- Adjust based on data size: sqrt(total_rows) * 4

-- Alternative: L2 distance for embedding search
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_context_items_embedding_l2
    ON context_items USING ivfflat (embedding vector_l2_ops)
    WITH (lists = 1000);

-- =====================================================
-- ENTITY AND RELATIONSHIP OPTIMIZATION
-- =====================================================

-- Entity extraction metadata (GIN index for JSON queries)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_context_items_entities_gin
    ON context_items USING gin ((metrics->'extracted_entities'));

-- General metrics JSON search
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_context_items_metrics_gin
    ON context_items USING gin (metrics);

-- Source data JSON search
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_context_items_source_data_gin
    ON context_items USING gin (source_data);

-- Tags array search (for categorical queries)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_context_items_tags_gin
    ON context_items USING gin (tags);

-- =====================================================
-- RELATIONSHIP TABLE OPTIMIZATION
-- =====================================================

-- Primary relationship lookups
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_context_relationships_source_target
    ON context_relationships USING btree (source_id, target_id);

-- Reverse relationship lookups
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_context_relationships_target_source
    ON context_relationships USING btree (target_id, source_id);

-- Relationship type filtering
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_context_relationships_type
    ON context_relationships USING btree (relationship_type);

-- Confidence-based filtering (for high-quality relationships)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_context_relationships_confidence
    ON context_relationships USING btree (confidence DESC);

-- Temporal relationship analysis
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_context_relationships_created
    ON context_relationships USING btree (created_at DESC);

-- =====================================================
-- COMPOSITE INDEXES FOR COMPLEX QUERIES
-- =====================================================

-- Chat session analysis (source_type + session + time)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_context_items_chat_session_analysis
    ON context_items USING btree (source_type, session_id, timestamp DESC)
    WHERE source_type = 'chat';

-- Entity type + timestamp for content analysis
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_context_items_entity_timestamp
    ON context_items USING btree (entity_type, timestamp DESC);

-- Project-specific queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_context_items_project_timestamp
    ON context_items USING btree (project_id, timestamp DESC)
    WHERE project_id IS NOT NULL;

-- File path analysis (for code context)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_context_items_file_path
    ON context_items USING btree (file_path, line_start)
    WHERE file_path IS NOT NULL;

-- =====================================================
-- PARTIAL INDEXES FOR SPECIFIC USE CASES
-- =====================================================

-- Only chat messages with content (skip empty/system messages)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_context_items_chat_content
    ON context_items USING btree (timestamp DESC)
    WHERE source_type = 'chat' AND content IS NOT NULL AND length(content) > 0;

-- Only items with embeddings (for vector searches)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_context_items_with_embeddings
    ON context_items USING btree (timestamp DESC)
    WHERE embedding IS NOT NULL;

-- High-confidence relationships only
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_context_relationships_high_confidence
    ON context_relationships USING btree (source_id, target_id, relationship_type)
    WHERE confidence > 0.7;

-- Recent items (last 30 days) - frequently accessed
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_context_items_recent
    ON context_items USING btree (timestamp DESC, source_type)
    WHERE timestamp > (CURRENT_TIMESTAMP - INTERVAL '30 days');

-- =====================================================
-- SPECIALIZED CHAT IMPORT INDEXES
-- =====================================================

-- Message threading (parent-child relationships in chat)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_context_items_thread_analysis
    ON context_items USING btree ((metrics->>'thread_id'), timestamp)
    WHERE metrics ? 'thread_id';

-- User interaction patterns
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_context_items_actor_type_timestamp
    ON context_items USING btree (actor_type, actor_id, timestamp DESC)
    WHERE source_type = 'chat';

-- Command and code reference extraction
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_context_items_command_extraction
    ON context_items USING gin ((metrics->'extracted_entities'->'commands'))
    WHERE metrics ? 'extracted_entities' AND metrics->'extracted_entities' ? 'commands';

-- URL and link analysis
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_context_items_url_extraction
    ON context_items USING gin ((metrics->'extracted_entities'->'urls'))
    WHERE metrics ? 'extracted_entities' AND metrics->'extracted_entities' ? 'urls';

-- =====================================================
-- MAINTENANCE AND MONITORING INDEXES
-- =====================================================

-- Ingestion monitoring (track import progress)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_context_items_ingested_at
    ON context_items USING btree (ingested_at DESC);

-- Error tracking and quality assurance
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_context_items_quality_metrics
    ON context_items USING btree (ingested_at)
    WHERE metrics ? 'entity_extraction_error' OR metrics ? 'embedding_error';

-- Neo4j integration tracking
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_context_items_neo4j_sync
    ON context_items USING btree (neo4j_node_id)
    WHERE neo4j_node_id IS NOT NULL;

-- =====================================================
-- PERFORMANCE TUNING SETTINGS
-- =====================================================

-- Optimize autovacuum for high-throughput ingestion
ALTER TABLE context_items SET (
    autovacuum_vacuum_scale_factor = 0.02,      -- More frequent vacuuming
    autovacuum_analyze_scale_factor = 0.01,     -- More frequent analyze
    autovacuum_vacuum_cost_limit = 2000,        -- Higher cost limit
    autovacuum_vacuum_cost_delay = 10           -- Lower delay
);

ALTER TABLE context_relationships SET (
    autovacuum_vacuum_scale_factor = 0.02,
    autovacuum_analyze_scale_factor = 0.01,
    autovacuum_vacuum_cost_limit = 2000,
    autovacuum_vacuum_cost_delay = 10
);

-- =====================================================
-- STATISTICS UPDATES FOR QUERY PLANNER
-- =====================================================

-- Update table statistics for optimal query planning
ANALYZE context_items;
ANALYZE context_relationships;

-- Set statistics targets for key columns
ALTER TABLE context_items ALTER COLUMN source_type SET STATISTICS 1000;
ALTER TABLE context_items ALTER COLUMN timestamp SET STATISTICS 1000;
ALTER TABLE context_items ALTER COLUMN session_id SET STATISTICS 1000;
ALTER TABLE context_items ALTER COLUMN actor_id SET STATISTICS 1000;

ALTER TABLE context_relationships ALTER COLUMN relationship_type SET STATISTICS 1000;
ALTER TABLE context_relationships ALTER COLUMN confidence SET STATISTICS 1000;

COMMIT;

-- =====================================================
-- INDEX USAGE MONITORING QUERIES
-- =====================================================

/*
-- Monitor index usage after deployment:

-- Check index usage statistics
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
  AND tablename IN ('context_items', 'context_relationships')
ORDER BY idx_scan DESC;

-- Check for unused indexes (run after some production usage)
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
  AND tablename IN ('context_items', 'context_relationships')
  AND idx_scan < 10  -- Adjust threshold as needed
ORDER BY idx_scan;

-- Monitor query performance
SELECT
    query,
    calls,
    total_time,
    mean_time,
    min_time,
    max_time,
    stddev_time
FROM pg_stat_statements
WHERE query LIKE '%context_items%'
   OR query LIKE '%context_relationships%'
ORDER BY total_time DESC
LIMIT 20;

-- Check index sizes
SELECT
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
  AND tablename IN ('context_items', 'context_relationships')
ORDER BY pg_relation_size(indexrelid) DESC;
*/

-- =====================================================
-- PERFORMANCE VALIDATION QUERIES
-- =====================================================

/*
-- Test query performance after index creation:

-- 1. Session-based chat retrieval (should use idx_context_items_session_timestamp)
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, timestamp, content, actor_id
FROM context_items
WHERE session_id = 'test_session_id'
  AND timestamp > CURRENT_TIMESTAMP - INTERVAL '1 day'
ORDER BY timestamp DESC
LIMIT 100;

-- 2. Entity extraction queries (should use idx_context_items_entities_gin)
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, timestamp, content
FROM context_items
WHERE metrics->'extracted_entities' ? 'urls'
  AND jsonb_array_length(metrics->'extracted_entities'->'urls') > 0;

-- 3. Vector similarity search (should use idx_context_items_embedding_cosine)
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, content, embedding <-> '[0.1,0.2,0.3]'::vector as distance
FROM context_items
WHERE embedding IS NOT NULL
ORDER BY embedding <-> '[0.1,0.2,0.3]'::vector
LIMIT 10;

-- 4. Relationship traversal (should use composite relationship indexes)
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    ci1.content as source_content,
    cr.relationship_type,
    cr.confidence,
    ci2.content as target_content
FROM context_items ci1
JOIN context_relationships cr ON ci1.id = cr.source_id
JOIN context_items ci2 ON cr.target_id = ci2.id
WHERE ci1.session_id = 'test_session_id'
  AND cr.confidence > 0.5
ORDER BY cr.confidence DESC;
*/
