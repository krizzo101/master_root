-- ============================================
-- DATABASE PERFORMANCE OPTIMIZATIONS
-- Based on Performance Analysis Results
-- ============================================

-- ============================================
-- 1. ADDITIONAL INDEXES FOR TOOL PERFORMANCE
-- ============================================

-- Optimize common search patterns for get_file_info tool
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_code_elements_file_path_optimized
ON code_elements (file_path, element_type, line_start)
WHERE element_type IN ('function', 'class', 'method');

-- Optimize search_code operations with compound index
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_code_elements_search_optimized
ON code_elements (element_name, element_type, last_modified DESC)
WHERE element_name IS NOT NULL;

-- Optimize dependency analysis queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_code_elements_dependencies_gin
ON code_elements USING GIN (dependencies)
WHERE dependencies IS NOT NULL;

-- Optimize recent changes queries with partial index
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_code_elements_recent_modified
ON code_elements (last_modified DESC)
WHERE last_modified >= NOW() - INTERVAL '7 days';

-- Optimize language-specific queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_code_elements_language_type
ON code_elements (language, element_type, complexity_score DESC)
WHERE language IS NOT NULL;

-- ============================================
-- 2. CONTEXT CORRELATION OPTIMIZATIONS
-- ============================================

-- Optimize session-based queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_context_items_session_time
ON context_items (session_id, timestamp DESC)
WHERE session_id IS NOT NULL;

-- Optimize file-based context correlation
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_context_items_file_source
ON context_items (file_path, source_type, timestamp DESC)
WHERE file_path IS NOT NULL;

-- Optimize code context joins
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_code_context_element_session
ON code_context (code_element_id, session_id, timestamp DESC);

-- Optimize symbol tracking
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_symbol_references_symbol_session
ON symbol_references (symbol_name, session_id, timestamp DESC);

-- ============================================
-- 3. TIME-SERIES OPTIMIZATIONS
-- ============================================

-- Optimize monitoring metrics queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_monitoring_metrics_source_time
ON monitoring_metrics (source, metric_name, time DESC);

-- Optimize IDE context snapshots
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ide_context_session_time
ON ide_context_snapshots (session_id, timestamp DESC)
WHERE session_id IS NOT NULL;

-- ============================================
-- 4. AGGREGATION OPTIMIZATIONS
-- ============================================

-- Create covering index for hourly stats
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_context_items_hourly_stats
ON context_items (source_type, timestamp, session_id)
INCLUDE (metrics);

-- Optimize daily file activity aggregations
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_file_activity_daily_stats
ON file_activity (file_path, timestamp, action)
INCLUDE (tool_used);

-- ============================================
-- 5. QUERY RESULT CACHING VIEWS
-- ============================================

-- Create materialized view for project complexity stats
CREATE MATERIALIZED VIEW IF NOT EXISTS project_complexity_stats AS
SELECT
    language,
    element_type,
    COUNT(*) as element_count,
    AVG(complexity_score) as avg_complexity,
    MAX(complexity_score) as max_complexity,
    STDDEV(complexity_score) as complexity_stddev,
    COUNT(*) FILTER (WHERE complexity_score > 15) as high_complexity_count
FROM code_elements
WHERE complexity_score IS NOT NULL
GROUP BY language, element_type;

-- Create unique index on materialized view
CREATE UNIQUE INDEX IF NOT EXISTS idx_project_complexity_stats_unique
ON project_complexity_stats (language, element_type);

-- Create materialized view for dependency analysis
CREATE MATERIALIZED VIEW IF NOT EXISTS dependency_analysis AS
SELECT
    jsonb_array_elements_text(dependencies) as dependency,
    COUNT(*) as usage_count,
    array_agg(DISTINCT file_path) as used_in_files,
    array_agg(DISTINCT language) as languages
FROM code_elements
WHERE dependencies IS NOT NULL AND jsonb_array_length(dependencies) > 0
GROUP BY jsonb_array_elements_text(dependencies);

-- Create index on dependency materialized view
CREATE INDEX IF NOT EXISTS idx_dependency_analysis_dependency
ON dependency_analysis (dependency);

-- ============================================
-- 6. PERFORMANCE MONITORING
-- ============================================

-- Create function to refresh materialized views efficiently
CREATE OR REPLACE FUNCTION refresh_performance_views()
RETURNS void AS $$
BEGIN
    -- Refresh with CONCURRENTLY to avoid locking
    REFRESH MATERIALIZED VIEW CONCURRENTLY project_complexity_stats;
    REFRESH MATERIALIZED VIEW CONCURRENTLY dependency_analysis;

    -- Also refresh existing views
    REFRESH MATERIALIZED VIEW CONCURRENTLY hourly_token_usage;
    REFRESH MATERIALIZED VIEW CONCURRENTLY daily_file_activity;

    RAISE NOTICE 'Performance materialized views refreshed successfully';
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 7. TABLE MAINTENANCE OPTIMIZATIONS
-- ============================================

-- Set appropriate autovacuum settings for large tables
ALTER TABLE code_elements SET (
    autovacuum_vacuum_scale_factor = 0.1,
    autovacuum_analyze_scale_factor = 0.05
);

ALTER TABLE context_items SET (
    autovacuum_vacuum_scale_factor = 0.2,
    autovacuum_analyze_scale_factor = 0.1
);

-- ============================================
-- 8. CONNECTION POOL OPTIMIZATIONS
-- ============================================

-- Adjust connection settings for better performance
-- Note: These would typically be set in postgresql.conf or via connection string
-- Documenting recommended settings:

-- shared_buffers = 256MB (25% of RAM for dedicated DB server)
-- effective_cache_size = 1GB (75% of available RAM)
-- work_mem = 4MB (for sorting/hashing operations)
-- maintenance_work_mem = 64MB (for maintenance operations)
-- max_connections = 100 (adjust based on application needs)
-- log_min_duration_statement = 1000 (log slow queries > 1s)

-- ============================================
-- 9. STATISTICS AND MONITORING
-- ============================================

-- Create view for monitoring query performance
CREATE OR REPLACE VIEW query_performance_stats AS
SELECT
    query,
    calls,
    total_time,
    mean_time,
    min_time,
    max_time,
    stddev_time,
    rows
FROM pg_stat_statements
WHERE query NOT LIKE '%pg_stat%'
ORDER BY mean_time DESC;

-- Create view for index usage monitoring
CREATE OR REPLACE VIEW index_usage_stats AS
SELECT
    schemaname,
    tablename,
    indexname,
    idx_tup_read,
    idx_tup_fetch,
    pg_size_pretty(pg_relation_size((schemaname||'.'||indexname)::regclass)) as index_size,
    CASE
        WHEN idx_tup_read = 0 THEN 'UNUSED'
        WHEN idx_tup_read < 1000 THEN 'LOW_USAGE'
        WHEN idx_tup_read < 10000 THEN 'MODERATE_USAGE'
        ELSE 'HIGH_USAGE'
    END as usage_category
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_tup_read DESC;

-- ============================================
-- 10. BACKUP AND MAINTENANCE SCHEDULE
-- ============================================

-- Create function for automated maintenance
CREATE OR REPLACE FUNCTION automated_maintenance()
RETURNS void AS $$
BEGIN
    -- Analyze tables for updated statistics
    ANALYZE code_elements;
    ANALYZE context_items;
    ANALYZE code_context;

    -- Refresh materialized views
    PERFORM refresh_performance_views();

    -- Log maintenance completion
    INSERT INTO context_items (
        source_type, entity_type, title, content,
        timestamp, ingested_at
    ) VALUES (
        'system', 'maintenance', 'Automated Maintenance Complete',
        'Database maintenance tasks completed successfully',
        NOW(), NOW()
    );

    RAISE NOTICE 'Automated maintenance completed successfully';
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- SUCCESS MESSAGE
-- ============================================
DO $$
BEGIN
    RAISE NOTICE 'Database performance optimizations applied successfully!';
    RAISE NOTICE 'New indexes created for improved query performance';
    RAISE NOTICE 'Materialized views created for complex aggregations';
    RAISE NOTICE 'Monitoring views available for performance tracking';
    RAISE NOTICE 'Run refresh_performance_views() to populate materialized views';
END $$;
