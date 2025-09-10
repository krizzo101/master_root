-- ============================================
-- CI/CD SCHEMA EXTENSIONS
-- Unified Context System - CI/CD Pipeline Integration
-- ============================================

-- Add CI/CD specific columns to context_items
ALTER TABLE context_items ADD COLUMN IF NOT EXISTS
    pipeline_id VARCHAR(255),
    build_number INTEGER,
    job_name VARCHAR(255),
    workflow_name VARCHAR(255),
    environment_name VARCHAR(100),
    deployment_status VARCHAR(50),
    artifact_urls TEXT[],
    test_results JSONB,
    performance_metrics JSONB,
    platform_metadata JSONB DEFAULT '{}';

-- ============================================
-- CI/CD CORRELATION TABLES
-- ============================================

-- CI/CD build correlations
CREATE TABLE IF NOT EXISTS cicd_correlations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    build_context_id UUID NOT NULL REFERENCES context_items(id) ON DELETE CASCADE,

    -- Source code correlation
    commit_sha VARCHAR(64),
    branch_name VARCHAR(255),
    pull_request_id VARCHAR(50),
    tag_name VARCHAR(255),

    -- Deployment correlation
    deployment_id UUID,
    environment VARCHAR(100),
    release_version VARCHAR(100),

    -- Build/pipeline details
    pipeline_type VARCHAR(50), -- 'ci', 'cd', 'build', 'test', 'deploy'
    pipeline_stage VARCHAR(100),
    parent_pipeline_id VARCHAR(255), -- For multi-stage pipelines

    -- Correlation metadata
    correlation_confidence FLOAT DEFAULT 1.0 CHECK (correlation_confidence BETWEEN 0.0 AND 1.0),
    correlation_method VARCHAR(50), -- 'commit_sha', 'branch_name', 'tag', 'temporal', 'manual'
    correlation_context JSONB DEFAULT '{}',

    -- Performance tracking
    build_duration_ms INTEGER,
    queue_time_ms INTEGER,
    deployment_duration_ms INTEGER,
    total_duration_ms INTEGER,

    -- Quality metrics
    test_count INTEGER DEFAULT 0,
    test_passed INTEGER DEFAULT 0,
    test_failed INTEGER DEFAULT 0,
    test_skipped INTEGER DEFAULT 0,
    coverage_percentage FLOAT,

    -- Success tracking
    build_success BOOLEAN,
    deployment_success BOOLEAN,
    overall_success BOOLEAN,

    -- Failure analysis
    failure_reason TEXT,
    failure_stage VARCHAR(100),
    retry_count INTEGER DEFAULT 0,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Build artifact tracking
CREATE TABLE IF NOT EXISTS build_artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    build_correlation_id UUID NOT NULL REFERENCES cicd_correlations(id) ON DELETE CASCADE,

    -- Artifact details
    artifact_name VARCHAR(255) NOT NULL,
    artifact_type VARCHAR(50), -- 'binary', 'container', 'package', 'documentation'
    artifact_url TEXT,
    artifact_hash VARCHAR(128),
    artifact_size_bytes BIGINT,

    -- Storage details
    storage_provider VARCHAR(50), -- 'github_packages', 'docker_hub', 'artifactory', 's3'
    storage_path TEXT,
    storage_metadata JSONB DEFAULT '{}',

    -- Lifecycle
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,

    -- Usage tracking
    download_count INTEGER DEFAULT 0,
    last_downloaded TIMESTAMPTZ
);

-- Pipeline stage tracking
CREATE TABLE IF NOT EXISTS pipeline_stages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    build_correlation_id UUID NOT NULL REFERENCES cicd_correlations(id) ON DELETE CASCADE,

    -- Stage details
    stage_name VARCHAR(255) NOT NULL,
    stage_type VARCHAR(50), -- 'build', 'test', 'security_scan', 'deploy', 'approval'
    stage_order INTEGER,

    -- Execution details
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    duration_ms INTEGER,
    status VARCHAR(50), -- 'pending', 'running', 'success', 'failed', 'cancelled', 'skipped'
    exit_code INTEGER,

    -- Stage output
    stage_logs TEXT,
    stage_output JSONB DEFAULT '{}',
    error_message TEXT,

    -- Dependencies
    depends_on_stages UUID[],
    allows_failure BOOLEAN DEFAULT FALSE,

    -- Resource usage
    cpu_usage_percent FLOAT,
    memory_usage_mb INTEGER,
    disk_usage_mb INTEGER,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Environment deployment tracking
CREATE TABLE IF NOT EXISTS environment_deployments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    build_correlation_id UUID NOT NULL REFERENCES cicd_correlations(id) ON DELETE CASCADE,

    -- Environment details
    environment_name VARCHAR(100) NOT NULL,
    environment_type VARCHAR(50), -- 'development', 'staging', 'production', 'test'
    environment_url TEXT,

    -- Deployment details
    deployment_strategy VARCHAR(50), -- 'rolling', 'blue_green', 'canary', 'recreate'
    deployed_version VARCHAR(100),
    previous_version VARCHAR(100),

    -- Timing
    deployment_started_at TIMESTAMPTZ,
    deployment_completed_at TIMESTAMPTZ,
    deployment_duration_ms INTEGER,

    -- Status
    deployment_status VARCHAR(50), -- 'pending', 'in_progress', 'success', 'failed', 'rolled_back'
    health_check_status VARCHAR(50), -- 'pending', 'healthy', 'unhealthy', 'unknown'

    -- Deployment metadata
    deployer_id VARCHAR(255),
    deployment_notes TEXT,
    rollback_available BOOLEAN DEFAULT TRUE,

    -- Infrastructure details
    instance_count INTEGER,
    resource_requirements JSONB DEFAULT '{}',

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Performance benchmarks
CREATE TABLE IF NOT EXISTS performance_benchmarks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    build_correlation_id UUID NOT NULL REFERENCES cicd_correlations(id) ON DELETE CASCADE,

    -- Benchmark details
    benchmark_name VARCHAR(255) NOT NULL,
    benchmark_type VARCHAR(50), -- 'load_test', 'unit_test', 'integration_test', 'security_test'
    benchmark_suite VARCHAR(100),

    -- Results
    execution_time_ms INTEGER,
    memory_usage_mb INTEGER,
    cpu_usage_percent FLOAT,

    -- Performance metrics
    requests_per_second FLOAT,
    response_time_p95_ms FLOAT,
    response_time_p99_ms FLOAT,
    error_rate FLOAT,
    throughput_mbps FLOAT,

    -- Benchmark specific metrics
    custom_metrics JSONB DEFAULT '{}',

    -- Comparison with baseline
    baseline_comparison JSONB DEFAULT '{}',
    performance_regression BOOLEAN DEFAULT FALSE,
    regression_threshold_exceeded BOOLEAN DEFAULT FALSE,

    -- Execution context
    executed_at TIMESTAMPTZ DEFAULT NOW(),
    execution_environment VARCHAR(100),
    test_data_version VARCHAR(50)
);

-- ============================================
-- CI/CD ANALYTICS AND INSIGHTS
-- ============================================

-- Build success rate tracking (materialized view)
CREATE MATERIALIZED VIEW IF NOT EXISTS build_success_analytics AS
SELECT
    DATE_TRUNC('day', cc.created_at) as date,
    ci.project_id,
    ci.metrics->>'platform' as platform,
    cc.pipeline_type,
    cc.environment,

    -- Build metrics
    COUNT(*) as total_builds,
    COUNT(*) FILTER (WHERE cc.build_success = TRUE) as successful_builds,
    COUNT(*) FILTER (WHERE cc.build_success = FALSE) as failed_builds,
    ROUND(COUNT(*) FILTER (WHERE cc.build_success = TRUE)::NUMERIC / COUNT(*) * 100, 2) as success_rate,

    -- Performance metrics
    AVG(cc.build_duration_ms) as avg_build_duration_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY cc.build_duration_ms) as p95_build_duration_ms,
    AVG(cc.queue_time_ms) FILTER (WHERE cc.queue_time_ms IS NOT NULL) as avg_queue_time_ms,

    -- Deployment metrics
    COUNT(*) FILTER (WHERE cc.deployment_id IS NOT NULL) as deployment_count,
    COUNT(*) FILTER (WHERE cc.deployment_success = TRUE) as successful_deployments,
    AVG(cc.deployment_duration_ms) FILTER (WHERE cc.deployment_duration_ms IS NOT NULL) as avg_deployment_duration_ms,

    -- Quality metrics
    AVG(cc.test_passed) FILTER (WHERE cc.test_count > 0) as avg_tests_passed,
    AVG(cc.coverage_percentage) FILTER (WHERE cc.coverage_percentage IS NOT NULL) as avg_coverage_percentage

FROM cicd_correlations cc
JOIN context_items ci ON cc.build_context_id = ci.id
WHERE cc.created_at >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY
    DATE_TRUNC('day', cc.created_at),
    ci.project_id,
    ci.metrics->>'platform',
    cc.pipeline_type,
    cc.environment;

-- Create unique index for materialized view
CREATE UNIQUE INDEX IF NOT EXISTS idx_build_success_analytics_unique
ON build_success_analytics(date, COALESCE(project_id, ''), COALESCE(platform, ''),
                           COALESCE(pipeline_type, ''), COALESCE(environment, ''));

-- Deployment frequency analytics
CREATE MATERIALIZED VIEW IF NOT EXISTS deployment_frequency_analytics AS
SELECT
    DATE_TRUNC('week', ed.deployment_started_at) as week,
    ed.environment_name,
    ed.environment_type,
    ci.project_id,

    -- Deployment frequency
    COUNT(*) as deployment_count,
    COUNT(*) FILTER (WHERE ed.deployment_status = 'success') as successful_deployments,
    COUNT(*) FILTER (WHERE ed.deployment_status = 'failed') as failed_deployments,

    -- Lead time (time from commit to deployment)
    AVG(EXTRACT(EPOCH FROM (ed.deployment_started_at - ci.timestamp)) / 3600) as avg_lead_time_hours,

    -- Deployment performance
    AVG(ed.deployment_duration_ms) as avg_deployment_duration_ms,
    COUNT(DISTINCT DATE_TRUNC('day', ed.deployment_started_at)) as deployment_days,

    -- Rollback tracking
    COUNT(*) FILTER (WHERE ed.deployment_status = 'rolled_back') as rollback_count,

    MAX(ed.deployment_started_at) as latest_deployment

FROM environment_deployments ed
JOIN cicd_correlations cc ON ed.build_correlation_id = cc.id
JOIN context_items ci ON cc.build_context_id = ci.id
WHERE ed.deployment_started_at >= CURRENT_DATE - INTERVAL '180 days'
GROUP BY
    DATE_TRUNC('week', ed.deployment_started_at),
    ed.environment_name,
    ed.environment_type,
    ci.project_id;

-- Create unique index for deployment frequency view
CREATE UNIQUE INDEX IF NOT EXISTS idx_deployment_frequency_analytics_unique
ON deployment_frequency_analytics(week, environment_name, COALESCE(project_id, ''));

-- ============================================
-- INDEXES FOR PERFORMANCE
-- ============================================

-- CI/CD specific indexes on context_items
CREATE INDEX IF NOT EXISTS idx_context_items_cicd_platform
ON context_items(source_type, (source_data->>'platform'))
WHERE source_type = 'cicd';

CREATE INDEX IF NOT EXISTS idx_context_items_cicd_status
ON context_items((metrics->>'status'), timestamp)
WHERE source_type = 'cicd';

CREATE INDEX IF NOT EXISTS idx_context_items_pipeline_id
ON context_items(pipeline_id)
WHERE pipeline_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_context_items_build_number
ON context_items(project_id, build_number)
WHERE build_number IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_context_items_environment
ON context_items(environment_name, deployment_status)
WHERE environment_name IS NOT NULL;

-- CI/CD correlation indexes
CREATE INDEX IF NOT EXISTS idx_cicd_correlations_build_context
ON cicd_correlations(build_context_id);

CREATE INDEX IF NOT EXISTS idx_cicd_correlations_commit_sha
ON cicd_correlations(commit_sha)
WHERE commit_sha IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_cicd_correlations_branch
ON cicd_correlations(branch_name)
WHERE branch_name IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_cicd_correlations_environment
ON cicd_correlations(environment, deployment_status)
WHERE environment IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_cicd_correlations_success
ON cicd_correlations(overall_success, created_at);

CREATE INDEX IF NOT EXISTS idx_cicd_correlations_duration
ON cicd_correlations(total_duration_ms)
WHERE total_duration_ms IS NOT NULL;

-- Pipeline stage indexes
CREATE INDEX IF NOT EXISTS idx_pipeline_stages_correlation
ON pipeline_stages(build_correlation_id);

CREATE INDEX IF NOT EXISTS idx_pipeline_stages_status
ON pipeline_stages(status, stage_type);

CREATE INDEX IF NOT EXISTS idx_pipeline_stages_duration
ON pipeline_stages(duration_ms DESC)
WHERE duration_ms IS NOT NULL;

-- Environment deployment indexes
CREATE INDEX IF NOT EXISTS idx_environment_deployments_correlation
ON environment_deployments(build_correlation_id);

CREATE INDEX IF NOT EXISTS idx_environment_deployments_env_status
ON environment_deployments(environment_name, deployment_status);

CREATE INDEX IF NOT EXISTS idx_environment_deployments_time
ON environment_deployments(deployment_started_at DESC);

-- Performance benchmark indexes
CREATE INDEX IF NOT EXISTS idx_performance_benchmarks_correlation
ON performance_benchmarks(build_correlation_id);

CREATE INDEX IF NOT EXISTS idx_performance_benchmarks_regression
ON performance_benchmarks(performance_regression)
WHERE performance_regression = TRUE;

-- ============================================
-- TRIGGERS AND FUNCTIONS
-- ============================================

-- Function to update correlation updated_at timestamp
CREATE OR REPLACE FUNCTION update_correlation_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for correlation updates
DROP TRIGGER IF EXISTS trigger_update_correlation_timestamp ON cicd_correlations;
CREATE TRIGGER trigger_update_correlation_timestamp
    BEFORE UPDATE ON cicd_correlations
    FOR EACH ROW
    EXECUTE FUNCTION update_correlation_timestamp();

-- Function to calculate build success rate
CREATE OR REPLACE FUNCTION calculate_build_success_rate(
    project_filter VARCHAR DEFAULT NULL,
    platform_filter VARCHAR DEFAULT NULL,
    days_back INTEGER DEFAULT 30
)
RETURNS TABLE (
    project_id VARCHAR,
    platform VARCHAR,
    total_builds INTEGER,
    successful_builds INTEGER,
    success_rate NUMERIC
)
LANGUAGE SQL STABLE
AS $$
    SELECT
        ci.project_id,
        ci.metrics->>'platform' as platform,
        COUNT(*)::INTEGER as total_builds,
        COUNT(*) FILTER (WHERE cc.build_success = TRUE)::INTEGER as successful_builds,
        ROUND(COUNT(*) FILTER (WHERE cc.build_success = TRUE)::NUMERIC / COUNT(*) * 100, 2) as success_rate
    FROM cicd_correlations cc
    JOIN context_items ci ON cc.build_context_id = ci.id
    WHERE cc.created_at >= CURRENT_DATE - INTERVAL '1 day' * days_back
      AND (project_filter IS NULL OR ci.project_id = project_filter)
      AND (platform_filter IS NULL OR ci.metrics->>'platform' = platform_filter)
    GROUP BY ci.project_id, ci.metrics->>'platform'
    ORDER BY success_rate DESC;
$$;

-- Function to find correlated failures
CREATE OR REPLACE FUNCTION find_correlated_failures(
    failure_window_hours INTEGER DEFAULT 2,
    min_correlation_count INTEGER DEFAULT 3
)
RETURNS TABLE (
    correlation_type VARCHAR,
    correlation_value VARCHAR,
    failure_count INTEGER,
    total_builds INTEGER,
    failure_rate NUMERIC,
    first_failure TIMESTAMPTZ,
    latest_failure TIMESTAMPTZ
)
LANGUAGE SQL STABLE
AS $$
    WITH failure_patterns AS (
        SELECT
            cc.commit_sha,
            cc.branch_name,
            cc.pipeline_stage,
            cc.failure_reason,
            COUNT(*) as failure_count,
            COUNT(*) FILTER (WHERE cc.build_success = FALSE) as failed_builds,
            MIN(cc.created_at) as first_failure,
            MAX(cc.created_at) as latest_failure
        FROM cicd_correlations cc
        WHERE cc.build_success = FALSE
          AND cc.created_at >= NOW() - INTERVAL '1 hour' * failure_window_hours
        GROUP BY cc.commit_sha, cc.branch_name, cc.pipeline_stage, cc.failure_reason
        HAVING COUNT(*) >= min_correlation_count
    )
    SELECT
        CASE
            WHEN commit_sha IS NOT NULL THEN 'commit_sha'
            WHEN branch_name IS NOT NULL THEN 'branch_name'
            WHEN pipeline_stage IS NOT NULL THEN 'pipeline_stage'
            WHEN failure_reason IS NOT NULL THEN 'failure_reason'
            ELSE 'unknown'
        END as correlation_type,
        COALESCE(commit_sha, branch_name, pipeline_stage, failure_reason, 'unknown') as correlation_value,
        failure_count::INTEGER,
        failed_builds::INTEGER as total_builds,
        ROUND(failed_builds::NUMERIC / failure_count * 100, 2) as failure_rate,
        first_failure,
        latest_failure
    FROM failure_patterns
    ORDER BY failure_count DESC, latest_failure DESC;
$$;

-- ============================================
-- MAINTENANCE FUNCTIONS
-- ============================================

-- Function to refresh CI/CD analytics views
CREATE OR REPLACE FUNCTION refresh_cicd_analytics_views()
RETURNS void AS $$
BEGIN
    -- Refresh build success analytics
    REFRESH MATERIALIZED VIEW CONCURRENTLY build_success_analytics;

    -- Refresh deployment frequency analytics
    REFRESH MATERIALIZED VIEW CONCURRENTLY deployment_frequency_analytics;

    RAISE NOTICE 'CI/CD analytics materialized views refreshed successfully';
END;
$$ LANGUAGE plpgsql;

-- Function to cleanup old CI/CD data
CREATE OR REPLACE FUNCTION cleanup_old_cicd_data(retention_days INTEGER DEFAULT 365)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    -- Delete old correlations (cascades to related tables)
    DELETE FROM cicd_correlations
    WHERE created_at < NOW() - INTERVAL '1 day' * retention_days;

    GET DIAGNOSTICS deleted_count = ROW_COUNT;

    -- Delete old CI/CD context items
    DELETE FROM context_items
    WHERE source_type = 'cicd'
      AND timestamp < NOW() - INTERVAL '1 day' * retention_days;

    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- INITIAL CONFIGURATION
-- ============================================

-- Insert CI/CD specific system configuration
INSERT INTO system_config (key, value, description) VALUES
('cicd_retention_days', '365', 'Number of days to retain CI/CD data'),
('cicd_analytics_refresh_interval', '3600', 'Seconds between analytics view refreshes'),
('cicd_correlation_confidence_threshold', '0.7', 'Minimum confidence for auto-detected correlations'),
('cicd_failure_alert_threshold', '0.2', 'Failure rate threshold for alerts')
ON CONFLICT (key) DO NOTHING;

-- Grant permissions on new tables
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO opsvi;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO opsvi;

-- ============================================
-- SUCCESS CONFIRMATION
-- ============================================

DO $$
BEGIN
    RAISE NOTICE '===========================================';
    RAISE NOTICE 'CI/CD SCHEMA EXTENSIONS IMPLEMENTATION COMPLETE';
    RAISE NOTICE '===========================================';
    RAISE NOTICE 'New Tables Created:';
    RAISE NOTICE '  ✓ cicd_correlations - Build and deployment correlations';
    RAISE NOTICE '  ✓ build_artifacts - Build artifact tracking';
    RAISE NOTICE '  ✓ pipeline_stages - Pipeline stage execution details';
    RAISE NOTICE '  ✓ environment_deployments - Environment deployment tracking';
    RAISE NOTICE '  ✓ performance_benchmarks - Performance test results';
    RAISE NOTICE '';
    RAISE NOTICE 'Materialized Views Created:';
    RAISE NOTICE '  ✓ build_success_analytics - Build success rate analytics';
    RAISE NOTICE '  ✓ deployment_frequency_analytics - Deployment frequency tracking';
    RAISE NOTICE '';
    RAISE NOTICE 'Functions Added:';
    RAISE NOTICE '  ✓ calculate_build_success_rate() - Success rate calculations';
    RAISE NOTICE '  ✓ find_correlated_failures() - Failure pattern detection';
    RAISE NOTICE '  ✓ refresh_cicd_analytics_views() - Analytics refresh';
    RAISE NOTICE '  ✓ cleanup_old_cicd_data() - Data retention management';
    RAISE NOTICE '';
    RAISE NOTICE 'Indexes Created: 15+ specialized indexes for query optimization';
    RAISE NOTICE 'Ready for CI/CD pipeline integration and analytics!';
END $$;
