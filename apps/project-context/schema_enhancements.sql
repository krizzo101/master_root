-- ============================================
-- UNIFIED CONTEXT SCHEMA ENHANCEMENTS
-- Database specialist agent schema design
-- Implements missing relationship patterns and advanced analytics
-- ============================================

-- Enable additional extensions for relationship modeling
CREATE EXTENSION IF NOT EXISTS btree_gin;
CREATE EXTENSION IF NOT EXISTS btree_gist;

-- ============================================
-- MISSING CORE TABLES FROM DESIGN DOCUMENT
-- ============================================

-- Context relationships table for graph modeling
CREATE TABLE IF NOT EXISTS context_relationships (
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

-- Correlation patterns table for learned intelligence
CREATE TABLE IF NOT EXISTS correlation_patterns (
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

-- Context metrics aggregation table for performance analytics
CREATE TABLE IF NOT EXISTS context_metrics_hourly (
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

-- Pattern application log for tracking correlation pattern usage
CREATE TABLE IF NOT EXISTS pattern_applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern_id UUID NOT NULL REFERENCES correlation_patterns(id) ON DELETE CASCADE,
    applied_at TIMESTAMPTZ DEFAULT NOW(),
    source_item_id UUID NOT NULL REFERENCES context_items(id),
    target_item_id UUID REFERENCES context_items(id),

    -- Application results
    application_result VARCHAR(20), -- 'success', 'failure', 'partial'
    confidence_score FLOAT,
    actual_time_delta INTERVAL,

    -- Validation
    human_validation BOOLEAN,
    validation_feedback TEXT,

    metadata JSONB DEFAULT '{}'
);

-- Knowledge gaps tracking table
CREATE TABLE IF NOT EXISTS knowledge_gaps (
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

-- ============================================
-- TIMESCALEDB HYPERTABLES FOR NEW TABLES
-- ============================================

-- Create hypertables for time-series optimization
SELECT create_hypertable('context_metrics_hourly', 'time_bucket',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE);

-- Note: pattern_applications could be hypertable but may not be needed for smaller volumes
-- SELECT create_hypertable('pattern_applications', 'applied_at',
--     chunk_time_interval => INTERVAL '7 days',
--     if_not_exists => TRUE);

-- ============================================
-- ADVANCED RELATIONSHIP INDEXES
-- ============================================

-- Core relationship indexes
CREATE INDEX IF NOT EXISTS idx_rel_source ON context_relationships(source_id);
CREATE INDEX IF NOT EXISTS idx_rel_target ON context_relationships(target_id);
CREATE INDEX IF NOT EXISTS idx_rel_type ON context_relationships(relationship_type);
CREATE INDEX IF NOT EXISTS idx_rel_confidence ON context_relationships(confidence DESC)
    WHERE confidence >= 0.7;

-- Temporal relationship indexes
CREATE INDEX IF NOT EXISTS idx_rel_temporal_context ON context_relationships(temporal_context)
    WHERE temporal_context IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_rel_time_delta ON context_relationships(time_delta_seconds)
    WHERE time_delta_seconds IS NOT NULL;

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_rel_source_type ON context_relationships(source_id, relationship_type);
CREATE INDEX IF NOT EXISTS idx_rel_type_confidence ON context_relationships(relationship_type, confidence DESC);
CREATE INDEX IF NOT EXISTS idx_rel_created_at ON context_relationships(created_at DESC);

-- Pattern-related indexes
CREATE INDEX IF NOT EXISTS idx_patterns_type ON correlation_patterns(pattern_type);
CREATE INDEX IF NOT EXISTS idx_patterns_status ON correlation_patterns(pattern_status);
CREATE INDEX IF NOT EXISTS idx_patterns_confidence ON correlation_patterns(confidence DESC)
    WHERE confidence >= 0.5;
CREATE INDEX IF NOT EXISTS idx_patterns_support ON correlation_patterns(support_count DESC);
CREATE INDEX IF NOT EXISTS idx_patterns_last_matched ON correlation_patterns(last_matched DESC)
    WHERE last_matched IS NOT NULL;

-- Advanced JSONB indexes for pattern criteria
CREATE INDEX IF NOT EXISTS idx_patterns_source_criteria ON correlation_patterns
    USING GIN(source_criteria);
CREATE INDEX IF NOT EXISTS idx_patterns_target_criteria ON correlation_patterns
    USING GIN(target_criteria);

-- Knowledge gaps indexes
CREATE INDEX IF NOT EXISTS idx_gaps_type ON knowledge_gaps(gap_type, severity);
CREATE INDEX IF NOT EXISTS idx_gaps_status ON knowledge_gaps(resolution_status);
CREATE INDEX IF NOT EXISTS idx_gaps_file ON knowledge_gaps(file_path)
    WHERE file_path IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_gaps_identified_at ON knowledge_gaps(identified_at DESC);

-- ============================================
-- ADVANCED ANALYTICS FUNCTIONS
-- ============================================

-- Function to find relationship patterns
CREATE OR REPLACE FUNCTION find_relationship_patterns(
    source_type_filter VARCHAR(50) DEFAULT NULL,
    min_confidence FLOAT DEFAULT 0.5,
    max_results INTEGER DEFAULT 50
)
RETURNS TABLE (
    relationship_type VARCHAR(50),
    relationship_count INTEGER,
    avg_confidence FLOAT,
    avg_time_delta_seconds INTEGER,
    most_common_source_type VARCHAR(50),
    most_common_target_type VARCHAR(50)
)
LANGUAGE SQL STABLE
AS $$
    SELECT
        cr.relationship_type,
        COUNT(*)::INTEGER as relationship_count,
        AVG(cr.confidence) as avg_confidence,
        AVG(cr.time_delta_seconds)::INTEGER as avg_time_delta_seconds,
        MODE() WITHIN GROUP (ORDER BY ci_source.source_type) as most_common_source_type,
        MODE() WITHIN GROUP (ORDER BY ci_target.source_type) as most_common_target_type
    FROM context_relationships cr
    JOIN context_items ci_source ON cr.source_id = ci_source.id
    JOIN context_items ci_target ON cr.target_id = ci_target.id
    WHERE (source_type_filter IS NULL OR ci_source.source_type = source_type_filter)
      AND cr.confidence >= min_confidence
    GROUP BY cr.relationship_type
    HAVING COUNT(*) >= 3
    ORDER BY relationship_count DESC, avg_confidence DESC
    LIMIT max_results;
$$;

-- Function to identify potential relationships
CREATE OR REPLACE FUNCTION identify_potential_relationships(
    context_item_id UUID,
    relationship_types VARCHAR(50)[] DEFAULT ARRAY['references', 'causes', 'follows'],
    time_window_hours INTEGER DEFAULT 24,
    max_suggestions INTEGER DEFAULT 10
)
RETURNS TABLE (
    suggested_target_id UUID,
    suggested_relationship_type VARCHAR(50),
    confidence_score FLOAT,
    reasoning TEXT
)
LANGUAGE SQL STABLE
AS $$
    WITH item_context AS (
        SELECT * FROM context_items WHERE id = context_item_id
    ),
    candidate_targets AS (
        SELECT
            ci.*,
            CASE
                -- File-based relationships
                WHEN ic.file_path IS NOT NULL AND ci.file_path = ic.file_path
                    THEN 0.8
                -- Function-based relationships
                WHEN ic.function_name IS NOT NULL AND ci.content ILIKE '%' || ic.function_name || '%'
                    THEN 0.7
                -- Content similarity (basic text matching)
                WHEN ci.content IS NOT NULL AND ic.content IS NOT NULL
                    AND similarity(ci.title, ic.title) > 0.3
                    THEN similarity(ci.title, ic.title)
                -- Temporal proximity
                WHEN ABS(EXTRACT(EPOCH FROM ci.timestamp - ic.timestamp)) <= time_window_hours * 3600
                    THEN 0.5
                ELSE 0.1
            END as base_confidence
        FROM context_items ci, item_context ic
        WHERE ci.id != context_item_id
          AND ci.timestamp BETWEEN
              (SELECT timestamp - INTERVAL '1 hour' * time_window_hours FROM item_context)
              AND
              (SELECT timestamp + INTERVAL '1 hour' * time_window_hours FROM item_context)
    )
    SELECT
        ct.id as suggested_target_id,
        CASE
            WHEN ct.source_type = 'error' AND (SELECT source_type FROM item_context) = 'git'
                THEN 'causes'
            WHEN ct.timestamp > (SELECT timestamp FROM item_context)
                THEN 'follows'
            ELSE 'references'
        END as suggested_relationship_type,
        ct.base_confidence as confidence_score,
        CASE
            WHEN ct.file_path = (SELECT file_path FROM item_context)
                THEN 'Same file context'
            WHEN ct.base_confidence > 0.7
                THEN 'Strong content similarity'
            ELSE 'Temporal proximity'
        END as reasoning
    FROM candidate_targets ct
    WHERE ct.base_confidence >= 0.3
    ORDER BY ct.base_confidence DESC
    LIMIT max_suggestions;
$$;

-- Function to calculate knowledge gap metrics
CREATE OR REPLACE FUNCTION calculate_knowledge_gaps(
    file_path_filter TEXT DEFAULT NULL,
    gap_threshold INTEGER DEFAULT 5
)
RETURNS TABLE (
    file_path TEXT,
    discussion_frequency INTEGER,
    avg_discussion_complexity FLOAT,
    documentation_coverage FLOAT,
    knowledge_gap_score FLOAT
)
LANGUAGE SQL STABLE
AS $$
    WITH file_discussions AS (
        SELECT
            ci.file_path,
            COUNT(*) as discussion_count,
            AVG(COALESCE((ci.metrics->>'tokens')::INTEGER, 100)) as avg_tokens,
            COUNT(DISTINCT ci.session_id) as unique_sessions
        FROM context_items ci
        WHERE ci.source_type = 'chat'
          AND ci.file_path IS NOT NULL
          AND (file_path_filter IS NULL OR ci.file_path ILIKE '%' || file_path_filter || '%')
        GROUP BY ci.file_path
    ),
    file_documentation AS (
        SELECT
            ce.file_path,
            COUNT(*) FILTER (WHERE ce.docstring IS NOT NULL AND length(ce.docstring) > 50) as documented_elements,
            COUNT(*) as total_elements,
            CASE
                WHEN COUNT(*) > 0
                    THEN COUNT(*) FILTER (WHERE ce.docstring IS NOT NULL AND length(ce.docstring) > 50)::FLOAT / COUNT(*)
                ELSE 0.0
            END as doc_coverage
        FROM code_elements ce
        WHERE (file_path_filter IS NULL OR ce.file_path ILIKE '%' || file_path_filter || '%')
        GROUP BY ce.file_path
    )
    SELECT
        COALESCE(fd.file_path, fdoc.file_path) as file_path,
        COALESCE(fd.discussion_count, 0)::INTEGER as discussion_frequency,
        COALESCE(fd.avg_tokens, 0) as avg_discussion_complexity,
        COALESCE(fdoc.doc_coverage, 0) as documentation_coverage,
        -- Knowledge gap score: high discussions + low documentation = high gap
        CASE
            WHEN COALESCE(fd.discussion_count, 0) >= gap_threshold
                AND COALESCE(fdoc.doc_coverage, 0) < 0.3
                THEN LEAST(COALESCE(fd.discussion_count, 0)::FLOAT / 10.0 * (1.0 - COALESCE(fdoc.doc_coverage, 0)), 1.0)
            ELSE 0.0
        END as knowledge_gap_score
    FROM file_discussions fd
    FULL OUTER JOIN file_documentation fdoc ON fd.file_path = fdoc.file_path
    WHERE COALESCE(fd.discussion_count, 0) >= gap_threshold
       OR COALESCE(fdoc.doc_coverage, 0) < 0.3
    ORDER BY knowledge_gap_score DESC, discussion_frequency DESC;
$$;

-- ============================================
-- MATERIALIZED VIEWS FOR ANALYTICS
-- ============================================

-- Relationship analytics view
CREATE MATERIALIZED VIEW IF NOT EXISTS relationship_analytics AS
SELECT
    cr.relationship_type,
    COUNT(*) as total_relationships,
    AVG(cr.confidence) as avg_confidence,
    COUNT(*) FILTER (WHERE cr.confidence >= 0.8) as high_confidence_count,
    COUNT(*) FILTER (WHERE cr.validation_status = 'validated') as validated_count,
    AVG(cr.time_delta_seconds) FILTER (WHERE cr.time_delta_seconds IS NOT NULL) as avg_time_delta_seconds,
    COUNT(DISTINCT DATE_TRUNC('day', cr.created_at)) as active_days,
    MAX(cr.created_at) as latest_relationship
FROM context_relationships cr
GROUP BY cr.relationship_type;

-- Create unique index for materialized view
CREATE UNIQUE INDEX IF NOT EXISTS idx_relationship_analytics_type
ON relationship_analytics(relationship_type);

-- Pattern effectiveness view
CREATE MATERIALIZED VIEW IF NOT EXISTS pattern_effectiveness AS
SELECT
    cp.pattern_type,
    cp.pattern_name,
    cp.confidence,
    cp.support_count,
    cp.success_rate,
    COUNT(pa.id) as application_count,
    COUNT(pa.id) FILTER (WHERE pa.application_result = 'success') as successful_applications,
    CASE
        WHEN COUNT(pa.id) > 0
            THEN COUNT(pa.id) FILTER (WHERE pa.application_result = 'success')::FLOAT / COUNT(pa.id)
        ELSE 0.0
    END as actual_success_rate
FROM correlation_patterns cp
LEFT JOIN pattern_applications pa ON cp.id = pa.pattern_id
GROUP BY cp.id, cp.pattern_type, cp.pattern_name, cp.confidence, cp.support_count, cp.success_rate;

-- ============================================
-- TRIGGER FUNCTIONS FOR AUTOMATED INSIGHTS
-- ============================================

-- Function to auto-detect relationships when context items are inserted
CREATE OR REPLACE FUNCTION auto_detect_relationships()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    -- Only process for certain source types to avoid performance issues
    IF NEW.source_type IN ('error', 'git', 'chat') THEN
        -- Insert a background job marker for async processing
        INSERT INTO context_items (
            source_type, entity_type, title, content,
            timestamp, ingested_at, metrics
        ) VALUES (
            'system', 'relationship_detection_job',
            'Auto-relationship detection needed',
            'Context item: ' || NEW.id::TEXT,
            NOW(), NOW(),
            jsonb_build_object('target_item_id', NEW.id)
        );
    END IF;

    RETURN NEW;
END;
$$;

-- Trigger for auto-relationship detection
DROP TRIGGER IF EXISTS trigger_auto_detect_relationships ON context_items;
CREATE TRIGGER trigger_auto_detect_relationships
    AFTER INSERT ON context_items
    FOR EACH ROW
    EXECUTE FUNCTION auto_detect_relationships();

-- ============================================
-- MAINTENANCE FUNCTIONS
-- ============================================

-- Function to refresh all materialized views
CREATE OR REPLACE FUNCTION refresh_analytics_views()
RETURNS void AS $$
BEGIN
    -- Refresh relationship analytics
    REFRESH MATERIALIZED VIEW CONCURRENTLY relationship_analytics;

    -- Refresh pattern effectiveness
    REFRESH MATERIALIZED VIEW CONCURRENTLY pattern_effectiveness;

    -- Refresh existing views
    PERFORM refresh_performance_views();

    RAISE NOTICE 'Analytics materialized views refreshed successfully';
END;
$$ LANGUAGE plpgsql;

-- Function to clean up old relationship detection jobs
CREATE OR REPLACE FUNCTION cleanup_system_jobs()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM context_items
    WHERE source_type = 'system'
      AND entity_type = 'relationship_detection_job'
      AND ingested_at < NOW() - INTERVAL '1 day';

    GET DIAGNOSTICS deleted_count = ROW_COUNT;

    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- GRANTS AND PERMISSIONS
-- ============================================

-- Grant permissions on new tables
GRANT ALL PRIVILEGES ON context_relationships TO opsvi;
GRANT ALL PRIVILEGES ON correlation_patterns TO opsvi;
GRANT ALL PRIVILEGES ON context_metrics_hourly TO opsvi;
GRANT ALL PRIVILEGES ON pattern_applications TO opsvi;
GRANT ALL PRIVILEGES ON knowledge_gaps TO opsvi;

-- Grant execute permissions on new functions
GRANT EXECUTE ON FUNCTION find_relationship_patterns TO opsvi;
GRANT EXECUTE ON FUNCTION identify_potential_relationships TO opsvi;
GRANT EXECUTE ON FUNCTION calculate_knowledge_gaps TO opsvi;
GRANT EXECUTE ON FUNCTION refresh_analytics_views TO opsvi;
GRANT EXECUTE ON FUNCTION cleanup_system_jobs TO opsvi;

-- Grant select on materialized views
GRANT SELECT ON relationship_analytics TO opsvi;
GRANT SELECT ON pattern_effectiveness TO opsvi;

-- ============================================
-- SUCCESS MESSAGE
-- ============================================
DO $$
BEGIN
    RAISE NOTICE '===========================================';
    RAISE NOTICE 'UNIFIED CONTEXT SCHEMA ENHANCEMENTS COMPLETE';
    RAISE NOTICE '===========================================';
    RAISE NOTICE 'Added Tables:';
    RAISE NOTICE '  ✓ context_relationships - Graph relationship modeling';
    RAISE NOTICE '  ✓ correlation_patterns - Machine learning patterns';
    RAISE NOTICE '  ✓ context_metrics_hourly - Performance analytics';
    RAISE NOTICE '  ✓ pattern_applications - Pattern usage tracking';
    RAISE NOTICE '  ✓ knowledge_gaps - Knowledge gap detection';
    RAISE NOTICE '';
    RAISE NOTICE 'Added Functions:';
    RAISE NOTICE '  ✓ find_relationship_patterns() - Pattern analysis';
    RAISE NOTICE '  ✓ identify_potential_relationships() - AI suggestions';
    RAISE NOTICE '  ✓ calculate_knowledge_gaps() - Gap analysis';
    RAISE NOTICE '  ✓ refresh_analytics_views() - Maintenance';
    RAISE NOTICE '';
    RAISE NOTICE 'Advanced Features:';
    RAISE NOTICE '  ✓ Auto-relationship detection triggers';
    RAISE NOTICE '  ✓ TimescaleDB hypertables for metrics';
    RAISE NOTICE '  ✓ Materialized views for analytics';
    RAISE NOTICE '  ✓ Advanced JSONB indexes for patterns';
    RAISE NOTICE '  ✓ Knowledge gap scoring algorithms';
    RAISE NOTICE '';
    RAISE NOTICE 'Ready for Phase 1 temporal knowledge graph implementation!';
END $$;
