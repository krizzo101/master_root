-- ============================================
-- ENHANCED ERROR LOG INGESTION SCHEMA
-- Migration: 005_enhanced_error_log_schema.sql
-- Dependencies: Unified Context Schema (001-004)
-- ============================================

-- Add enhanced metadata to context_items for error processing
ALTER TABLE context_items
    ADD COLUMN IF NOT EXISTS error_signature TEXT,
    ADD COLUMN IF NOT EXISTS cluster_id VARCHAR(255),
    ADD COLUMN IF NOT EXISTS pattern_signature TEXT,
    ADD COLUMN IF NOT EXISTS correlation_score FLOAT DEFAULT 0.0,
    ADD COLUMN IF NOT EXISTS is_duplicate BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS root_cause_analysis JSONB DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS stack_trace_hash VARCHAR(64);

-- Error clusters table for deduplication
CREATE TABLE IF NOT EXISTS error_clusters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cluster_id VARCHAR(255) UNIQUE NOT NULL,
    signature TEXT NOT NULL,
    error_count INTEGER DEFAULT 1,
    first_seen TIMESTAMPTZ DEFAULT NOW(),
    last_seen TIMESTAMPTZ DEFAULT NOW(),
    representative_error_id UUID REFERENCES context_items(id),
    severity_distribution JSONB DEFAULT '{}',
    file_paths TEXT[],
    categories TEXT[],
    trend_data JSONB DEFAULT '{}',

    -- Clustering metadata
    similarity_threshold FLOAT DEFAULT 0.8,
    classification_confidence FLOAT DEFAULT 0.7,

    -- Created and updated timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Error patterns table for trend analysis
CREATE TABLE IF NOT EXISTS error_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern_id VARCHAR(255) UNIQUE NOT NULL,
    pattern_signature TEXT NOT NULL,
    error_type VARCHAR(255),
    file_pattern TEXT,
    category VARCHAR(100),

    -- Frequency data
    frequency_count INTEGER DEFAULT 1,
    frequency_per_hour FLOAT DEFAULT 0.0,
    first_occurrence TIMESTAMPTZ DEFAULT NOW(),
    last_occurrence TIMESTAMPTZ DEFAULT NOW(),

    -- Trend analysis
    trend_slope FLOAT DEFAULT 0.0,
    trend_direction VARCHAR(20) DEFAULT 'stable', -- 'increasing', 'decreasing', 'stable'
    severity_score FLOAT DEFAULT 0.0,
    prediction_confidence FLOAT DEFAULT 0.0,

    -- Pattern effectiveness
    correlation_accuracy FLOAT DEFAULT 0.0,
    false_positive_rate FLOAT DEFAULT 0.0,

    -- Time series data (hourly buckets for last 30 days)
    hourly_counts JSONB DEFAULT '{}',

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Stack traces table for reusable analysis
CREATE TABLE IF NOT EXISTS stack_traces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stack_hash VARCHAR(64) UNIQUE NOT NULL,
    raw_stack_trace TEXT NOT NULL,

    -- Parsed elements
    language VARCHAR(50),
    stack_depth INTEGER,
    root_function VARCHAR(255),
    root_file_path TEXT,
    root_line_number INTEGER,

    -- Stack elements as structured data
    stack_elements JSONB DEFAULT '[]',

    -- Analysis results
    complexity_score FLOAT DEFAULT 0.0,
    error_prone_functions TEXT[],
    common_patterns TEXT[],

    -- Occurrence tracking
    occurrence_count INTEGER DEFAULT 1,
    first_seen TIMESTAMPTZ DEFAULT NOW(),
    last_seen TIMESTAMPTZ DEFAULT NOW(),

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Error correlations table for intelligent linking
CREATE TABLE IF NOT EXISTS error_correlations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_error_id UUID NOT NULL REFERENCES context_items(id) ON DELETE CASCADE,
    target_item_id UUID NOT NULL REFERENCES context_items(id) ON DELETE CASCADE,

    -- Correlation details
    correlation_type VARCHAR(50) NOT NULL, -- 'git_commit', 'chat_discussion', 'code_location', 'similar_error', 'causal'
    correlation_strength FLOAT NOT NULL CHECK (correlation_strength BETWEEN 0.0 AND 1.0),

    -- Temporal context
    time_delta_seconds INTEGER,
    temporal_relationship VARCHAR(20), -- 'before', 'after', 'during', 'concurrent'

    -- Detection metadata
    detection_method VARCHAR(50) NOT NULL, -- 'automatic', 'ml_model', 'pattern_based', 'manual'
    detection_confidence FLOAT DEFAULT 0.7,

    -- Validation
    validation_status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'validated', 'rejected', 'disputed'
    validated_by VARCHAR(100),
    validated_at TIMESTAMPTZ,

    -- Usage tracking
    correlation_used_count INTEGER DEFAULT 0,
    last_used TIMESTAMPTZ,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Performance monitoring table for error processing
CREATE TABLE IF NOT EXISTS error_processing_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_timestamp TIMESTAMPTZ DEFAULT NOW(),

    -- Processing performance
    total_errors_processed INTEGER DEFAULT 0,
    average_processing_time_ms FLOAT DEFAULT 0.0,
    p95_processing_time_ms FLOAT DEFAULT 0.0,
    max_processing_time_ms FLOAT DEFAULT 0.0,

    -- Error rates and failures
    parsing_failure_count INTEGER DEFAULT 0,
    parsing_failure_rate FLOAT DEFAULT 0.0,
    correlation_failure_count INTEGER DEFAULT 0,
    correlation_failure_rate FLOAT DEFAULT 0.0,

    -- Memory and resource usage
    memory_usage_mb FLOAT DEFAULT 0.0,
    cpu_usage_percent FLOAT DEFAULT 0.0,

    -- Pattern detection stats
    new_patterns_detected INTEGER DEFAULT 0,
    trending_patterns_count INTEGER DEFAULT 0,
    cluster_count INTEGER DEFAULT 0,

    -- Alert counts
    alerts_raised INTEGER DEFAULT 0,
    alert_types JSONB DEFAULT '[]',

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Alert history table
CREATE TABLE IF NOT EXISTS error_processing_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_type VARCHAR(100) NOT NULL,
    alert_severity VARCHAR(20) DEFAULT 'info', -- 'info', 'warning', 'error', 'critical'
    alert_message TEXT NOT NULL,

    -- Alert context
    metric_values JSONB DEFAULT '{}',
    threshold_values JSONB DEFAULT '{}',
    related_pattern_ids TEXT[],
    related_cluster_ids TEXT[],

    -- Alert lifecycle
    alert_status VARCHAR(20) DEFAULT 'active', -- 'active', 'acknowledged', 'resolved', 'suppressed'
    acknowledged_by VARCHAR(100),
    acknowledged_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- INDEXES FOR ENHANCED ERROR PROCESSING
-- ============================================

-- Context items error-specific indexes
CREATE INDEX IF NOT EXISTS idx_context_items_error_signature
    ON context_items(error_signature) WHERE error_signature IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_context_items_cluster_id
    ON context_items(cluster_id) WHERE cluster_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_context_items_pattern_signature
    ON context_items(pattern_signature) WHERE pattern_signature IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_context_items_stack_trace_hash
    ON context_items(stack_trace_hash) WHERE stack_trace_hash IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_context_items_is_duplicate
    ON context_items(is_duplicate) WHERE is_duplicate = true;

-- Error clusters indexes
CREATE INDEX IF NOT EXISTS idx_error_clusters_signature ON error_clusters(signature);
CREATE INDEX IF NOT EXISTS idx_error_clusters_error_count ON error_clusters(error_count DESC);
CREATE INDEX IF NOT EXISTS idx_error_clusters_last_seen ON error_clusters(last_seen DESC);
CREATE INDEX IF NOT EXISTS idx_error_clusters_representative ON error_clusters(representative_error_id);

-- JSONB indexes for cluster metadata
CREATE INDEX IF NOT EXISTS idx_error_clusters_severity_dist
    ON error_clusters USING GIN(severity_distribution);
CREATE INDEX IF NOT EXISTS idx_error_clusters_trend_data
    ON error_clusters USING GIN(trend_data);

-- Error patterns indexes
CREATE INDEX IF NOT EXISTS idx_error_patterns_signature ON error_patterns(pattern_signature);
CREATE INDEX IF NOT EXISTS idx_error_patterns_frequency ON error_patterns(frequency_count DESC);
CREATE INDEX IF NOT EXISTS idx_error_patterns_trend_slope ON error_patterns(trend_slope DESC);
CREATE INDEX IF NOT EXISTS idx_error_patterns_severity_score ON error_patterns(severity_score DESC);
CREATE INDEX IF NOT EXISTS idx_error_patterns_last_occurrence ON error_patterns(last_occurrence DESC);
CREATE INDEX IF NOT EXISTS idx_error_patterns_trend_direction ON error_patterns(trend_direction);

-- Composite indexes for pattern analysis
CREATE INDEX IF NOT EXISTS idx_error_patterns_type_category
    ON error_patterns(error_type, category);
CREATE INDEX IF NOT EXISTS idx_error_patterns_trending
    ON error_patterns(trend_direction, severity_score DESC)
    WHERE trend_direction = 'increasing';

-- Stack traces indexes
CREATE INDEX IF NOT EXISTS idx_stack_traces_hash ON stack_traces(stack_hash);
CREATE INDEX IF NOT EXISTS idx_stack_traces_language ON stack_traces(language);
CREATE INDEX IF NOT EXISTS idx_stack_traces_root_function ON stack_traces(root_function);
CREATE INDEX IF NOT EXISTS idx_stack_traces_root_file ON stack_traces(root_file_path);
CREATE INDEX IF NOT EXISTS idx_stack_traces_occurrence_count ON stack_traces(occurrence_count DESC);
CREATE INDEX IF NOT EXISTS idx_stack_traces_complexity ON stack_traces(complexity_score DESC);

-- Error correlations indexes
CREATE INDEX IF NOT EXISTS idx_error_correlations_source ON error_correlations(source_error_id);
CREATE INDEX IF NOT EXISTS idx_error_correlations_target ON error_correlations(target_item_id);
CREATE INDEX IF NOT EXISTS idx_error_correlations_type ON error_correlations(correlation_type);
CREATE INDEX IF NOT EXISTS idx_error_correlations_strength ON error_correlations(correlation_strength DESC);
CREATE INDEX IF NOT EXISTS idx_error_correlations_method ON error_correlations(detection_method);
CREATE INDEX IF NOT EXISTS idx_error_correlations_validation_status ON error_correlations(validation_status);

-- Composite indexes for correlation queries
CREATE INDEX IF NOT EXISTS idx_error_correlations_type_strength
    ON error_correlations(correlation_type, correlation_strength DESC);
CREATE INDEX IF NOT EXISTS idx_error_correlations_temporal
    ON error_correlations(temporal_relationship, time_delta_seconds);

-- Performance metrics indexes
CREATE INDEX IF NOT EXISTS idx_error_processing_metrics_timestamp
    ON error_processing_metrics(metric_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_error_processing_metrics_processing_time
    ON error_processing_metrics(average_processing_time_ms DESC);
CREATE INDEX IF NOT EXISTS idx_error_processing_metrics_failure_rate
    ON error_processing_metrics(parsing_failure_rate DESC);

-- Alert history indexes
CREATE INDEX IF NOT EXISTS idx_error_alerts_type ON error_processing_alerts(alert_type);
CREATE INDEX IF NOT EXISTS idx_error_alerts_severity ON error_processing_alerts(alert_severity);
CREATE INDEX IF NOT EXISTS idx_error_alerts_status ON error_processing_alerts(alert_status);
CREATE INDEX IF NOT EXISTS idx_error_alerts_created_at ON error_processing_alerts(created_at DESC);

-- ============================================
-- ADVANCED ANALYTICS FUNCTIONS
-- ============================================

-- Function to calculate error trend analysis
CREATE OR REPLACE FUNCTION analyze_error_trends(
    time_window_hours INTEGER DEFAULT 24,
    min_frequency INTEGER DEFAULT 3,
    trend_threshold FLOAT DEFAULT 0.1
)
RETURNS TABLE (
    pattern_id VARCHAR(255),
    pattern_signature TEXT,
    frequency_count INTEGER,
    trend_slope FLOAT,
    trend_direction VARCHAR(20),
    severity_score FLOAT,
    prediction_next_hour FLOAT
)
LANGUAGE SQL STABLE
AS $$
    SELECT
        ep.pattern_id,
        ep.pattern_signature,
        ep.frequency_count,
        ep.trend_slope,
        ep.trend_direction,
        ep.severity_score,
        GREATEST(0, ep.frequency_per_hour + ep.trend_slope) as prediction_next_hour
    FROM error_patterns ep
    WHERE ep.frequency_count >= min_frequency
      AND ep.last_occurrence > NOW() - INTERVAL '1 hour' * time_window_hours
      AND ABS(ep.trend_slope) > trend_threshold
    ORDER BY ep.severity_score DESC, ep.frequency_count DESC
    LIMIT 50;
$$;

-- Function to get error cluster analysis
CREATE OR REPLACE FUNCTION get_error_cluster_analysis(
    min_error_count INTEGER DEFAULT 2,
    time_window_hours INTEGER DEFAULT 168  -- 1 week
)
RETURNS TABLE (
    cluster_id VARCHAR(255),
    signature TEXT,
    error_count INTEGER,
    unique_files INTEGER,
    avg_severity FLOAT,
    trend_direction VARCHAR(20),
    first_seen TIMESTAMPTZ,
    last_seen TIMESTAMPTZ
)
LANGUAGE SQL STABLE
AS $$
    WITH cluster_stats AS (
        SELECT
            ec.cluster_id,
            ec.signature,
            ec.error_count,
            array_length(ec.file_paths, 1) as unique_files,
            ec.first_seen,
            ec.last_seen,
            -- Calculate average severity from distribution
            (
                COALESCE((ec.severity_distribution->>'critical')::INTEGER, 0) * 4 +
                COALESCE((ec.severity_distribution->>'high')::INTEGER, 0) * 3 +
                COALESCE((ec.severity_distribution->>'medium')::INTEGER, 0) * 2 +
                COALESCE((ec.severity_distribution->>'low')::INTEGER, 0) * 1
            )::FLOAT / GREATEST(ec.error_count, 1) as avg_severity,
            -- Extract trend direction from trend_data
            COALESCE(ec.trend_data->>'trend_direction', 'stable')::VARCHAR(20) as trend_direction
        FROM error_clusters ec
        WHERE ec.error_count >= min_error_count
          AND ec.last_seen > NOW() - INTERVAL '1 hour' * time_window_hours
    )
    SELECT
        cs.cluster_id,
        cs.signature,
        cs.error_count,
        cs.unique_files,
        cs.avg_severity,
        cs.trend_direction,
        cs.first_seen,
        cs.last_seen
    FROM cluster_stats cs
    ORDER BY cs.error_count DESC, cs.avg_severity DESC, cs.last_seen DESC;
$$;

-- Function to find correlated errors for root cause analysis
CREATE OR REPLACE FUNCTION find_correlated_errors(
    error_id UUID,
    correlation_threshold FLOAT DEFAULT 0.5,
    max_results INTEGER DEFAULT 20
)
RETURNS TABLE (
    target_error_id UUID,
    target_title TEXT,
    target_file_path TEXT,
    correlation_type VARCHAR(50),
    correlation_strength FLOAT,
    time_delta_seconds INTEGER,
    detection_confidence FLOAT
)
LANGUAGE SQL STABLE
AS $$
    SELECT
        ci.id as target_error_id,
        ci.title as target_title,
        ci.file_path as target_file_path,
        ec.correlation_type,
        ec.correlation_strength,
        ec.time_delta_seconds,
        ec.detection_confidence
    FROM error_correlations ec
    JOIN context_items ci ON ec.target_item_id = ci.id
    WHERE ec.source_error_id = error_id
      AND ec.correlation_strength >= correlation_threshold
      AND ec.validation_status != 'rejected'
    ORDER BY ec.correlation_strength DESC, ec.detection_confidence DESC
    LIMIT max_results;
$$;

-- Function to calculate stack trace complexity scores
CREATE OR REPLACE FUNCTION calculate_stack_complexity()
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    updated_count INTEGER := 0;
BEGIN
    UPDATE stack_traces SET
        complexity_score = (
            -- Base complexity from stack depth
            LEAST(stack_depth / 10.0, 1.0) * 0.3 +
            -- Complexity from number of different files
            LEAST(
                (SELECT COUNT(DISTINCT elem->>'file_path')
                 FROM jsonb_array_elements(stack_elements) elem
                 WHERE elem->>'file_path' IS NOT NULL) / 5.0,
                1.0
            ) * 0.3 +
            -- Complexity from occurrence frequency (more frequent = less complex to fix)
            (1.0 - LEAST(occurrence_count / 100.0, 1.0)) * 0.2 +
            -- Complexity from pattern diversity
            LEAST(array_length(common_patterns, 1) / 3.0, 1.0) * 0.2
        )
    WHERE complexity_score = 0.0 OR complexity_score IS NULL;

    GET DIAGNOSTICS updated_count = ROW_COUNT;
    RETURN updated_count;
END;
$$;

-- ============================================
-- TRIGGERS FOR AUTOMATIC MAINTENANCE
-- ============================================

-- Trigger function to update error cluster statistics
CREATE OR REPLACE FUNCTION update_error_cluster_stats()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    -- Update cluster when new error is added
    IF TG_OP = 'INSERT' AND NEW.cluster_id IS NOT NULL THEN
        INSERT INTO error_clusters (cluster_id, signature, representative_error_id)
        VALUES (NEW.cluster_id, COALESCE(NEW.error_signature, 'unknown'), NEW.id)
        ON CONFLICT (cluster_id) DO UPDATE SET
            error_count = error_clusters.error_count + 1,
            last_seen = NOW(),
            file_paths = array_append(
                COALESCE(error_clusters.file_paths, '{}'),
                NEW.file_path
            ),
            updated_at = NOW();
    END IF;

    RETURN COALESCE(NEW, OLD);
END;
$$;

-- Trigger for updating cluster stats
DROP TRIGGER IF EXISTS trigger_update_cluster_stats ON context_items;
CREATE TRIGGER trigger_update_cluster_stats
    AFTER INSERT OR UPDATE OF cluster_id ON context_items
    FOR EACH ROW
    WHEN (NEW.source_type = 'error')
    EXECUTE FUNCTION update_error_cluster_stats();

-- Trigger function to create stack trace hash
CREATE OR REPLACE FUNCTION generate_stack_trace_hash()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.source_type = 'error' AND NEW.metrics ? 'stack_trace' THEN
        NEW.stack_trace_hash = encode(
            digest(NEW.metrics->>'stack_trace', 'sha256'),
            'hex'
        );

        -- Insert or update stack traces table
        INSERT INTO stack_traces (stack_hash, raw_stack_trace, occurrence_count)
        VALUES (NEW.stack_trace_hash, NEW.metrics->>'stack_trace', 1)
        ON CONFLICT (stack_hash) DO UPDATE SET
            occurrence_count = stack_traces.occurrence_count + 1,
            last_seen = NOW();
    END IF;

    RETURN NEW;
END;
$$;

-- Trigger for stack trace processing
DROP TRIGGER IF EXISTS trigger_process_stack_traces ON context_items;
CREATE TRIGGER trigger_process_stack_traces
    BEFORE INSERT OR UPDATE ON context_items
    FOR EACH ROW
    EXECUTE FUNCTION generate_stack_trace_hash();

-- ============================================
-- MAINTENANCE AND CLEANUP PROCEDURES
-- ============================================

-- Function to clean up old performance metrics
CREATE OR REPLACE FUNCTION cleanup_old_metrics(retention_days INTEGER DEFAULT 30)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM error_processing_metrics
    WHERE created_at < NOW() - INTERVAL '1 day' * retention_days;

    GET DIAGNOSTICS deleted_count = ROW_COUNT;

    DELETE FROM error_processing_alerts
    WHERE created_at < NOW() - INTERVAL '1 day' * retention_days
      AND alert_status IN ('resolved', 'suppressed');

    RETURN deleted_count;
END;
$$;

-- Function to archive old error patterns
CREATE OR REPLACE FUNCTION archive_inactive_patterns(inactive_days INTEGER DEFAULT 7)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    archived_count INTEGER;
BEGIN
    UPDATE error_patterns
    SET trend_direction = 'archived'
    WHERE last_occurrence < NOW() - INTERVAL '1 day' * inactive_days
      AND trend_direction != 'archived'
      AND frequency_count < 5;

    GET DIAGNOSTICS archived_count = ROW_COUNT;
    RETURN archived_count;
END;
$$;

-- ============================================
-- INITIAL DATA AND CONFIGURATION
-- ============================================

-- Insert default performance thresholds
INSERT INTO system_config (key, value, description) VALUES
('error_processing_max_time_ms', '5000', 'Maximum processing time per error in milliseconds'),
('error_processing_max_rate_per_min', '100', 'Maximum error processing rate per minute'),
('error_trend_analysis_window_hours', '24', 'Time window for trend analysis in hours'),
('error_correlation_threshold', '0.5', 'Minimum correlation strength for error linking'),
('error_deduplication_threshold', '0.8', 'Similarity threshold for error deduplication'),
('error_pattern_min_frequency', '3', 'Minimum frequency to consider error pattern significant')
ON CONFLICT (key) DO NOTHING;

-- ============================================
-- COMPLETION CONFIRMATION
-- ============================================

DO $$
BEGIN
    RAISE NOTICE '===========================================';
    RAISE NOTICE 'ENHANCED ERROR LOG SCHEMA MIGRATION COMPLETE';
    RAISE NOTICE '===========================================';
    RAISE NOTICE 'New Tables Created:';
    RAISE NOTICE '  ✓ error_clusters - Error deduplication and clustering';
    RAISE NOTICE '  ✓ error_patterns - Trend analysis and pattern detection';
    RAISE NOTICE '  ✓ stack_traces - Reusable stack trace analysis';
    RAISE NOTICE '  ✓ error_correlations - Intelligent error correlation';
    RAISE NOTICE '  ✓ error_processing_metrics - Performance monitoring';
    RAISE NOTICE '  ✓ error_processing_alerts - Alert management';
    RAISE NOTICE '';
    RAISE NOTICE 'Enhanced Features:';
    RAISE NOTICE '  ✓ Automatic error clustering and deduplication';
    RAISE NOTICE '  ✓ Real-time trend analysis and prediction';
    RAISE NOTICE '  ✓ Stack trace complexity scoring';
    RAISE NOTICE '  ✓ Intelligent error correlation detection';
    RAISE NOTICE '  ✓ Performance monitoring and alerting';
    RAISE NOTICE '  ✓ Automated maintenance and cleanup procedures';
    RAISE NOTICE '';
    RAISE NOTICE 'Analytics Functions Added:';
    RAISE NOTICE '  ✓ analyze_error_trends() - Trend analysis';
    RAISE NOTICE '  ✓ get_error_cluster_analysis() - Cluster insights';
    RAISE NOTICE '  ✓ find_correlated_errors() - Root cause analysis';
    RAISE NOTICE '  ✓ calculate_stack_complexity() - Complexity scoring';
    RAISE NOTICE '';
    RAISE NOTICE 'Ready for enhanced error log ingestion and analysis!';
END $$;
