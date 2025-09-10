-- ============================================
-- MIGRATION 003: ADD MATERIALIZED VIEWS
-- Unified Context System Phase 1
-- Performance-optimized materialized views for analytics
-- ============================================

BEGIN;

-- Log this migration
INSERT INTO migration_log (migration_id, description, rollback_sql) VALUES (
    '003_add_materialized_views',
    'Add materialized views for relationship analytics and pattern effectiveness',
    $rollback$
        DROP MATERIALIZED VIEW IF EXISTS pattern_effectiveness CASCADE;
        DROP MATERIALIZED VIEW IF EXISTS relationship_analytics CASCADE;
        DROP MATERIALIZED VIEW IF EXISTS knowledge_gap_summary CASCADE;
        DROP MATERIALIZED VIEW IF EXISTS context_correlation_matrix CASCADE;
        DROP FUNCTION IF EXISTS refresh_analytics_views CASCADE;
        DROP FUNCTION IF EXISTS get_analytics_summary CASCADE;
    $rollback$
);

-- ============================================
-- RELATIONSHIP ANALYTICS VIEW
-- ============================================

-- Comprehensive analytics on relationship patterns and effectiveness
CREATE MATERIALIZED VIEW IF NOT EXISTS relationship_analytics AS
SELECT
    cr.relationship_type,
    COUNT(*) as total_relationships,
    AVG(cr.confidence) as avg_confidence,
    STDDEV(cr.confidence) as confidence_stddev,
    COUNT(*) FILTER (WHERE cr.confidence >= 0.8) as high_confidence_count,
    COUNT(*) FILTER (WHERE cr.confidence BETWEEN 0.5 AND 0.8) as medium_confidence_count,
    COUNT(*) FILTER (WHERE cr.confidence < 0.5) as low_confidence_count,
    COUNT(*) FILTER (WHERE cr.validation_status = 'validated') as validated_count,
    COUNT(*) FILTER (WHERE cr.validation_status = 'rejected') as rejected_count,
    COUNT(*) FILTER (WHERE cr.validation_status = 'pending') as pending_count,
    COUNT(*) FILTER (WHERE cr.created_by = 'auto_detection') as auto_detected_count,
    COUNT(*) FILTER (WHERE cr.created_by = 'human') as human_created_count,

    -- Temporal analysis
    AVG(cr.time_delta_seconds) FILTER (WHERE cr.time_delta_seconds IS NOT NULL) as avg_time_delta_seconds,
    STDDEV(cr.time_delta_seconds) FILTER (WHERE cr.time_delta_seconds IS NOT NULL) as time_delta_stddev,
    MIN(cr.time_delta_seconds) FILTER (WHERE cr.time_delta_seconds IS NOT NULL) as min_time_delta_seconds,
    MAX(cr.time_delta_seconds) FILTER (WHERE cr.time_delta_seconds IS NOT NULL) as max_time_delta_seconds,

    -- Activity metrics
    COUNT(DISTINCT DATE_TRUNC('day', cr.created_at)) as active_days,
    MIN(cr.created_at) as first_relationship,
    MAX(cr.created_at) as latest_relationship,

    -- Source/target analysis
    COUNT(DISTINCT ci_source.source_type) as distinct_source_types,
    COUNT(DISTINCT ci_target.source_type) as distinct_target_types,
    MODE() WITHIN GROUP (ORDER BY ci_source.source_type) as most_common_source_type,
    MODE() WITHIN GROUP (ORDER BY ci_target.source_type) as most_common_target_type,

    -- Quality metrics
    CASE
        WHEN COUNT(*) > 0 THEN
            COUNT(*) FILTER (WHERE cr.validation_status = 'validated')::FLOAT / COUNT(*)
        ELSE 0.0
    END as validation_rate,

    CASE
        WHEN COUNT(*) FILTER (WHERE cr.created_by = 'auto_detection') > 0 THEN
            COUNT(*) FILTER (WHERE cr.created_by = 'auto_detection' AND cr.validation_status = 'validated')::FLOAT /
            COUNT(*) FILTER (WHERE cr.created_by = 'auto_detection')
        ELSE NULL
    END as auto_detection_accuracy

FROM context_relationships cr
JOIN context_items ci_source ON cr.source_id = ci_source.id
JOIN context_items ci_target ON cr.target_id = ci_target.id
GROUP BY cr.relationship_type;

-- Create unique index for efficient refresh
CREATE UNIQUE INDEX IF NOT EXISTS idx_relationship_analytics_type
ON relationship_analytics(relationship_type);

-- ============================================
-- PATTERN EFFECTIVENESS VIEW
-- ============================================

-- Analytics on correlation pattern performance and application success
CREATE MATERIALIZED VIEW IF NOT EXISTS pattern_effectiveness AS
SELECT
    cp.id as pattern_id,
    cp.pattern_name,
    cp.pattern_type,
    cp.confidence as declared_confidence,
    cp.support_count,
    cp.success_rate as declared_success_rate,
    cp.pattern_status,
    cp.priority,
    cp.discovered_at,
    cp.last_matched,

    -- Application statistics
    COUNT(pa.id) as total_applications,
    COUNT(pa.id) FILTER (WHERE pa.application_result = 'success') as successful_applications,
    COUNT(pa.id) FILTER (WHERE pa.application_result = 'failure') as failed_applications,
    COUNT(pa.id) FILTER (WHERE pa.application_result = 'partial') as partial_applications,

    -- Actual performance metrics
    CASE
        WHEN COUNT(pa.id) > 0
            THEN COUNT(pa.id) FILTER (WHERE pa.application_result = 'success')::FLOAT / COUNT(pa.id)
        ELSE 0.0
    END as actual_success_rate,

    AVG(pa.confidence_score) as avg_application_confidence,
    STDDEV(pa.confidence_score) as confidence_score_stddev,

    -- Temporal analysis of applications
    AVG(EXTRACT(EPOCH FROM pa.actual_time_delta)) FILTER (WHERE pa.actual_time_delta IS NOT NULL) as avg_actual_time_delta_seconds,
    STDDEV(EXTRACT(EPOCH FROM pa.actual_time_delta)) FILTER (WHERE pa.actual_time_delta IS NOT NULL) as time_delta_variation,

    -- Pattern health metrics
    CASE
        WHEN cp.last_matched IS NOT NULL
            THEN EXTRACT(DAYS FROM NOW() - cp.last_matched)
        ELSE NULL
    END as days_since_last_match,

    -- Human validation statistics
    COUNT(pa.id) FILTER (WHERE pa.human_validation IS TRUE) as human_validated_count,
    COUNT(pa.id) FILTER (WHERE pa.human_validation IS TRUE AND pa.application_result = 'success') as human_confirmed_successes,

    -- Pattern accuracy score (combines multiple factors)
    CASE
        WHEN COUNT(pa.id) >= 5 THEN -- Only calculate for patterns with sufficient data
            LEAST(
                -- Base success rate
                (COUNT(pa.id) FILTER (WHERE pa.application_result = 'success')::FLOAT / COUNT(pa.id)) * 0.5 +
                -- Confidence alignment
                (1.0 - ABS(cp.confidence - AVG(pa.confidence_score))) * 0.3 +
                -- Recency bonus
                CASE
                    WHEN cp.last_matched > NOW() - INTERVAL '7 days' THEN 0.2
                    WHEN cp.last_matched > NOW() - INTERVAL '30 days' THEN 0.1
                    ELSE 0.0
                END,
                1.0
            )
        ELSE NULL
    END as pattern_accuracy_score

FROM correlation_patterns cp
LEFT JOIN pattern_applications pa ON cp.id = pa.pattern_id
GROUP BY cp.id, cp.pattern_name, cp.pattern_type, cp.confidence, cp.support_count,
         cp.success_rate, cp.pattern_status, cp.priority, cp.discovered_at, cp.last_matched;

-- Create unique index for efficient refresh
CREATE UNIQUE INDEX IF NOT EXISTS idx_pattern_effectiveness_id
ON pattern_effectiveness(pattern_id);

-- ============================================
-- KNOWLEDGE GAP SUMMARY VIEW
-- ============================================

-- Aggregated view of knowledge gaps across the codebase
CREATE MATERIALIZED VIEW IF NOT EXISTS knowledge_gap_summary AS
WITH gap_calculations AS (
    SELECT * FROM calculate_knowledge_gaps(NULL, 3, 30)
),
gap_aggregations AS (
    SELECT
        gap_severity,
        COUNT(*) as file_count,
        AVG(knowledge_gap_score) as avg_gap_score,
        SUM(discussion_frequency) as total_discussions,
        AVG(documentation_coverage) as avg_doc_coverage,
        array_agg(file_path ORDER BY knowledge_gap_score DESC) as affected_files
    FROM gap_calculations
    WHERE knowledge_gap_score > 0
    GROUP BY gap_severity
)
SELECT
    gap_severity,
    file_count,
    avg_gap_score,
    total_discussions,
    avg_doc_coverage,
    affected_files[1:5] as top_affected_files, -- Top 5 files per severity
    CASE
        WHEN gap_severity = 'critical' THEN file_count * 10
        WHEN gap_severity = 'high' THEN file_count * 5
        WHEN gap_severity = 'medium' THEN file_count * 2
        ELSE file_count
    END as priority_score
FROM gap_aggregations
UNION ALL
-- Add overall summary row
SELECT
    'overall' as gap_severity,
    SUM(file_count)::INTEGER as file_count,
    AVG(avg_gap_score) as avg_gap_score,
    SUM(total_discussions)::INTEGER as total_discussions,
    AVG(avg_doc_coverage) as avg_doc_coverage,
    ARRAY[]::TEXT[] as top_affected_files,
    SUM(CASE
        WHEN gap_severity = 'critical' THEN file_count * 10
        WHEN gap_severity = 'high' THEN file_count * 5
        WHEN gap_severity = 'medium' THEN file_count * 2
        ELSE file_count
    END)::INTEGER as priority_score
FROM gap_aggregations;

-- Create unique index for efficient refresh
CREATE UNIQUE INDEX IF NOT EXISTS idx_knowledge_gap_summary_severity
ON knowledge_gap_summary(gap_severity);

-- ============================================
-- CONTEXT CORRELATION MATRIX VIEW
-- ============================================

-- Matrix showing correlation strengths between different source types
CREATE MATERIALIZED VIEW IF NOT EXISTS context_correlation_matrix AS
SELECT
    ci_source.source_type as source_type,
    ci_target.source_type as target_type,
    COUNT(*) as relationship_count,
    AVG(cr.confidence) as avg_confidence,
    COUNT(*) FILTER (WHERE cr.confidence >= 0.8) as strong_relationships,
    COUNT(*) FILTER (WHERE cr.validation_status = 'validated') as validated_relationships,

    -- Relationship type distribution
    COUNT(*) FILTER (WHERE cr.relationship_type = 'causes') as causes_count,
    COUNT(*) FILTER (WHERE cr.relationship_type = 'references') as references_count,
    COUNT(*) FILTER (WHERE cr.relationship_type = 'follows') as follows_count,
    COUNT(*) FILTER (WHERE cr.relationship_type = 'contains') as contains_count,

    -- Temporal characteristics
    AVG(cr.time_delta_seconds) FILTER (WHERE cr.time_delta_seconds IS NOT NULL) as avg_time_delta_seconds,

    -- Correlation strength score
    CASE
        WHEN COUNT(*) > 0 THEN
            LEAST(
                -- Relationship density
                COUNT(*)::FLOAT / 100.0 * 0.4 +
                -- Average confidence
                AVG(cr.confidence) * 0.4 +
                -- Validation rate
                (COUNT(*) FILTER (WHERE cr.validation_status = 'validated')::FLOAT / COUNT(*)) * 0.2,
                1.0
            )
        ELSE 0.0
    END as correlation_strength

FROM context_relationships cr
JOIN context_items ci_source ON cr.source_id = ci_source.id
JOIN context_items ci_target ON cr.target_id = ci_target.id
GROUP BY ci_source.source_type, ci_target.source_type
HAVING COUNT(*) >= 3 -- Only include correlations with at least 3 relationships
ORDER BY correlation_strength DESC;

-- Create unique index for efficient refresh
CREATE UNIQUE INDEX IF NOT EXISTS idx_context_correlation_matrix_types
ON context_correlation_matrix(source_type, target_type);

-- ============================================
-- VIEW REFRESH FUNCTIONS
-- ============================================

-- Enhanced function to refresh all analytics materialized views
CREATE OR REPLACE FUNCTION refresh_analytics_views()
RETURNS TABLE (
    view_name TEXT,
    refresh_duration INTERVAL,
    row_count INTEGER,
    last_refreshed TIMESTAMPTZ
)
LANGUAGE plpgsql
AS $$
DECLARE
    start_time TIMESTAMPTZ;
    end_time TIMESTAMPTZ;
    view_record RECORD;
    refresh_error TEXT;
BEGIN
    -- Refresh relationship_analytics
    start_time := clock_timestamp();
    BEGIN
        REFRESH MATERIALIZED VIEW CONCURRENTLY relationship_analytics;
        end_time := clock_timestamp();
        SELECT COUNT(*) INTO view_record FROM relationship_analytics;
        RETURN QUERY SELECT 'relationship_analytics'::TEXT, end_time - start_time, view_record, end_time;
    EXCEPTION WHEN OTHERS THEN
        refresh_error := SQLERRM;
        RAISE NOTICE 'Error refreshing relationship_analytics: %', refresh_error;
    END;

    -- Refresh pattern_effectiveness
    start_time := clock_timestamp();
    BEGIN
        REFRESH MATERIALIZED VIEW CONCURRENTLY pattern_effectiveness;
        end_time := clock_timestamp();
        SELECT COUNT(*) INTO view_record FROM pattern_effectiveness;
        RETURN QUERY SELECT 'pattern_effectiveness'::TEXT, end_time - start_time, view_record, end_time;
    EXCEPTION WHEN OTHERS THEN
        refresh_error := SQLERRM;
        RAISE NOTICE 'Error refreshing pattern_effectiveness: %', refresh_error;
    END;

    -- Refresh knowledge_gap_summary
    start_time := clock_timestamp();
    BEGIN
        REFRESH MATERIALIZED VIEW CONCURRENTLY knowledge_gap_summary;
        end_time := clock_timestamp();
        SELECT COUNT(*) INTO view_record FROM knowledge_gap_summary;
        RETURN QUERY SELECT 'knowledge_gap_summary'::TEXT, end_time - start_time, view_record, end_time;
    EXCEPTION WHEN OTHERS THEN
        refresh_error := SQLERRM;
        RAISE NOTICE 'Error refreshing knowledge_gap_summary: %', refresh_error;
    END;

    -- Refresh context_correlation_matrix
    start_time := clock_timestamp();
    BEGIN
        REFRESH MATERIALIZED VIEW CONCURRENTLY context_correlation_matrix;
        end_time := clock_timestamp();
        SELECT COUNT(*) INTO view_record FROM context_correlation_matrix;
        RETURN QUERY SELECT 'context_correlation_matrix'::TEXT, end_time - start_time, view_record, end_time;
    EXCEPTION WHEN OTHERS THEN
        refresh_error := SQLERRM;
        RAISE NOTICE 'Error refreshing context_correlation_matrix: %', refresh_error;
    END;

    -- Also refresh the existing views
    start_time := clock_timestamp();
    BEGIN
        PERFORM refresh_performance_views();
        end_time := clock_timestamp();
        RETURN QUERY SELECT 'legacy_performance_views'::TEXT, end_time - start_time, 0, end_time;
    EXCEPTION WHEN OTHERS THEN
        refresh_error := SQLERRM;
        RAISE NOTICE 'Error refreshing performance views: %', refresh_error;
    END;
END;
$$;

-- Function to get a comprehensive analytics summary
CREATE OR REPLACE FUNCTION get_analytics_summary()
RETURNS TABLE (
    metric_category TEXT,
    metric_name TEXT,
    metric_value TEXT,
    last_updated TIMESTAMPTZ
)
LANGUAGE SQL STABLE
AS $$
    -- Relationship metrics
    SELECT
        'relationships' as metric_category,
        'total_relationships' as metric_name,
        SUM(total_relationships)::TEXT as metric_value,
        MAX(latest_relationship) as last_updated
    FROM relationship_analytics

    UNION ALL

    SELECT
        'relationships' as metric_category,
        'avg_confidence' as metric_name,
        ROUND(AVG(avg_confidence), 3)::TEXT as metric_value,
        MAX(latest_relationship) as last_updated
    FROM relationship_analytics

    UNION ALL

    SELECT
        'relationships' as metric_category,
        'validation_rate' as metric_name,
        ROUND(AVG(validation_rate), 3)::TEXT as metric_value,
        MAX(latest_relationship) as last_updated
    FROM relationship_analytics

    UNION ALL

    -- Pattern metrics
    SELECT
        'patterns' as metric_category,
        'active_patterns' as metric_name,
        COUNT(*)::TEXT as metric_value,
        MAX(last_matched) as last_updated
    FROM pattern_effectiveness
    WHERE pattern_status = 'active'

    UNION ALL

    SELECT
        'patterns' as metric_category,
        'avg_pattern_accuracy' as metric_name,
        ROUND(AVG(pattern_accuracy_score), 3)::TEXT as metric_value,
        MAX(last_matched) as last_updated
    FROM pattern_effectiveness
    WHERE pattern_accuracy_score IS NOT NULL

    UNION ALL

    -- Knowledge gap metrics
    SELECT
        'knowledge_gaps' as metric_category,
        'critical_gaps' as metric_name,
        COALESCE(file_count, 0)::TEXT as metric_value,
        NOW() as last_updated
    FROM knowledge_gap_summary
    WHERE gap_severity = 'critical'

    UNION ALL

    SELECT
        'knowledge_gaps' as metric_category,
        'total_gap_files' as metric_name,
        COALESCE(file_count, 0)::TEXT as metric_value,
        NOW() as last_updated
    FROM knowledge_gap_summary
    WHERE gap_severity = 'overall'

    UNION ALL

    -- System health metrics
    SELECT
        'system' as metric_category,
        'strongest_correlation' as metric_name,
        source_type || ' -> ' || target_type || ' (' || ROUND(correlation_strength, 3)::TEXT || ')' as metric_value,
        NOW() as last_updated
    FROM context_correlation_matrix
    ORDER BY correlation_strength DESC
    LIMIT 1;
$$;

-- ============================================
-- AUTOMATED REFRESH SCHEDULER FUNCTION
-- ============================================

-- Function to set up automated refresh schedule (would typically be called by cron/scheduler)
CREATE OR REPLACE FUNCTION schedule_view_refresh()
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
    -- In a production environment, this would integrate with pg_cron or external scheduler
    -- For now, it just logs the intent to refresh
    INSERT INTO context_items (
        source_type, entity_type, title, content,
        timestamp, ingested_at, metrics
    ) VALUES (
        'system', 'maintenance_job',
        'Analytics View Refresh Scheduled',
        'Automated refresh of materialized views requested',
        NOW(), NOW(),
        jsonb_build_object(
            'job_type', 'view_refresh',
            'scheduled_at', NOW(),
            'priority', 'medium'
        )
    );

    RAISE NOTICE 'Analytics view refresh scheduled. Call refresh_analytics_views() to execute.';
END;
$$;

-- ============================================
-- GRANTS AND PERMISSIONS
-- ============================================

-- Grant select permissions on materialized views
GRANT SELECT ON relationship_analytics TO opsvi;
GRANT SELECT ON pattern_effectiveness TO opsvi;
GRANT SELECT ON knowledge_gap_summary TO opsvi;
GRANT SELECT ON context_correlation_matrix TO opsvi;

-- Grant execute permissions on functions
GRANT EXECUTE ON FUNCTION refresh_analytics_views TO opsvi;
GRANT EXECUTE ON FUNCTION get_analytics_summary TO opsvi;
GRANT EXECUTE ON FUNCTION schedule_view_refresh TO opsvi;

-- Update migration log
UPDATE migration_log
SET applied_at = NOW()
WHERE migration_id = '003_add_materialized_views';

COMMIT;

-- ============================================
-- INITIAL VIEW POPULATION
-- ============================================

-- Populate the materialized views with initial data
DO $$
DECLARE
    refresh_results RECORD;
BEGIN
    RAISE NOTICE 'Populating materialized views with initial data...';

    -- Refresh all views
    FOR refresh_results IN SELECT * FROM refresh_analytics_views()
    LOOP
        RAISE NOTICE 'Refreshed %: % rows in %',
            refresh_results.view_name,
            refresh_results.row_count,
            refresh_results.refresh_duration;
    END LOOP;

    RAISE NOTICE 'Initial materialized view population completed';
END $$;

-- ============================================
-- SUCCESS MESSAGE
-- ============================================
DO $$
BEGIN
    RAISE NOTICE '===============================================';
    RAISE NOTICE 'MIGRATION 003 COMPLETED SUCCESSFULLY';
    RAISE NOTICE '===============================================';
    RAISE NOTICE 'Materialized Views Added:';
    RAISE NOTICE '  ✓ relationship_analytics - Relationship pattern analysis';
    RAISE NOTICE '  ✓ pattern_effectiveness - ML pattern performance tracking';
    RAISE NOTICE '  ✓ knowledge_gap_summary - Knowledge gap aggregation';
    RAISE NOTICE '  ✓ context_correlation_matrix - Source type correlations';
    RAISE NOTICE '';
    RAISE NOTICE 'Functions Added:';
    RAISE NOTICE '  ✓ refresh_analytics_views() - Refresh all views';
    RAISE NOTICE '  ✓ get_analytics_summary() - Quick metrics overview';
    RAISE NOTICE '  ✓ schedule_view_refresh() - Automated scheduling';
    RAISE NOTICE '';
    RAISE NOTICE 'Quick Start Commands:';
    RAISE NOTICE '  • SELECT * FROM get_analytics_summary();';
    RAISE NOTICE '  • SELECT * FROM relationship_analytics;';
    RAISE NOTICE '  • SELECT * FROM knowledge_gap_summary;';
    RAISE NOTICE '  • SELECT * FROM refresh_analytics_views();';
    RAISE NOTICE '';
    RAISE NOTICE 'Schema Enhancement Complete!';
    RAISE NOTICE 'Ready for Phase 1 implementation and testing.';
END $$;
