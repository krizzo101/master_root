-- ============================================
-- MIGRATION 001: ADD RELATIONSHIP TABLES
-- Unified Context System Phase 1
-- Safe migration script with rollback capability
-- ============================================

-- Transaction for safe migration
BEGIN;

-- ============================================
-- MIGRATION METADATA
-- ============================================
CREATE TABLE IF NOT EXISTS migration_log (
    migration_id VARCHAR(50) PRIMARY KEY,
    applied_at TIMESTAMPTZ DEFAULT NOW(),
    rollback_sql TEXT,
    description TEXT
);

-- Log this migration
INSERT INTO migration_log (migration_id, description, rollback_sql) VALUES (
    '001_add_relationship_tables',
    'Add context_relationships and correlation_patterns tables for graph modeling',
    $rollback$
        DROP TABLE IF EXISTS pattern_applications CASCADE;
        DROP TABLE IF EXISTS knowledge_gaps CASCADE;
        DROP TABLE IF EXISTS context_metrics_hourly CASCADE;
        DROP TABLE IF EXISTS correlation_patterns CASCADE;
        DROP TABLE IF EXISTS context_relationships CASCADE;
        DROP FUNCTION IF EXISTS find_relationship_patterns CASCADE;
        DROP FUNCTION IF EXISTS identify_potential_relationships CASCADE;
        DROP FUNCTION IF EXISTS calculate_knowledge_gaps CASCADE;
        DROP MATERIALIZED VIEW IF EXISTS relationship_analytics CASCADE;
        DROP MATERIALIZED VIEW IF EXISTS pattern_effectiveness CASCADE;
    $rollback$
);

-- ============================================
-- PRE-MIGRATION CHECKS
-- ============================================
DO $$
BEGIN
    -- Check if required extensions exist
    IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'timescaledb') THEN
        RAISE EXCEPTION 'TimescaleDB extension is required but not installed';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'uuid-ossp') THEN
        RAISE EXCEPTION 'uuid-ossp extension is required but not installed';
    END IF;

    -- Check if base table exists
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'context_items') THEN
        RAISE EXCEPTION 'Base table context_items does not exist. Run base schema first.';
    END IF;

    RAISE NOTICE 'Pre-migration checks passed';
END $$;

-- ============================================
-- MIGRATION STEP 1: RELATIONSHIP TABLES
-- ============================================

-- Context relationships table
CREATE TABLE IF NOT EXISTS context_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL,
    target_id UUID NOT NULL,
    relationship_type VARCHAR(50) NOT NULL,
    confidence FLOAT DEFAULT 1.0 CHECK (confidence BETWEEN 0.0 AND 1.0),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by VARCHAR(50) DEFAULT 'system',

    -- Temporal context
    temporal_context VARCHAR(50),
    time_delta_seconds INTEGER,

    -- Validation context
    validation_status VARCHAR(20) DEFAULT 'pending',
    validation_score FLOAT,

    -- Neo4j integration
    neo4j_relationship_id VARCHAR(255),

    CONSTRAINT unique_relationship UNIQUE(source_id, target_id, relationship_type),
    CONSTRAINT no_self_reference CHECK (source_id != target_id)
);

-- Add foreign key constraints with proper error handling
DO $$
BEGIN
    -- Add foreign key to source_id if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'context_relationships_source_id_fkey'
    ) THEN
        ALTER TABLE context_relationships
        ADD CONSTRAINT context_relationships_source_id_fkey
        FOREIGN KEY (source_id) REFERENCES context_items(id) ON DELETE CASCADE;
    END IF;

    -- Add foreign key to target_id if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'context_relationships_target_id_fkey'
    ) THEN
        ALTER TABLE context_relationships
        ADD CONSTRAINT context_relationships_target_id_fkey
        FOREIGN KEY (target_id) REFERENCES context_items(id) ON DELETE CASCADE;
    END IF;
END $$;

-- Correlation patterns table
CREATE TABLE IF NOT EXISTS correlation_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern_name VARCHAR(255) NOT NULL,
    pattern_type VARCHAR(50) NOT NULL,
    source_criteria JSONB NOT NULL,
    target_criteria JSONB NOT NULL,
    confidence FLOAT CHECK (confidence BETWEEN 0.0 AND 1.0),
    support_count INTEGER DEFAULT 0,
    avg_time_delta INTERVAL,
    min_time_delta INTERVAL,
    max_time_delta INTERVAL,

    -- Pattern effectiveness
    success_rate FLOAT,
    false_positive_rate FLOAT,

    -- Pattern metadata
    discovered_at TIMESTAMPTZ DEFAULT NOW(),
    last_matched TIMESTAMPTZ,
    last_validated TIMESTAMPTZ,
    discovery_method VARCHAR(100),

    -- Pattern lifecycle
    pattern_status VARCHAR(20) DEFAULT 'active',
    priority INTEGER DEFAULT 1,
    metadata JSONB DEFAULT '{}'
);

-- ============================================
-- MIGRATION STEP 2: METRICS TABLES
-- ============================================

-- Context metrics hourly table
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

-- Pattern applications table
CREATE TABLE IF NOT EXISTS pattern_applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern_id UUID NOT NULL,
    applied_at TIMESTAMPTZ DEFAULT NOW(),
    source_item_id UUID NOT NULL,
    target_item_id UUID,

    -- Application results
    application_result VARCHAR(20),
    confidence_score FLOAT,
    actual_time_delta INTERVAL,

    -- Validation
    human_validation BOOLEAN,
    validation_feedback TEXT,

    metadata JSONB DEFAULT '{}'
);

-- Knowledge gaps table
CREATE TABLE IF NOT EXISTS knowledge_gaps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gap_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20),

    -- Gap identification
    identified_at TIMESTAMPTZ DEFAULT NOW(),
    identified_by VARCHAR(50),

    -- Gap context
    file_path TEXT,
    function_name VARCHAR(255),
    related_context_items UUID[],

    -- Gap metrics
    discussion_count INTEGER DEFAULT 0,
    avg_discussion_length FLOAT,
    resolution_attempts INTEGER DEFAULT 0,

    -- Gap resolution
    resolution_status VARCHAR(20) DEFAULT 'open',
    resolved_at TIMESTAMPTZ,
    resolution_method TEXT,
    resolution_confidence FLOAT,

    metadata JSONB DEFAULT '{}'
);

-- Add foreign key constraints for pattern_applications
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'pattern_applications_pattern_id_fkey'
    ) THEN
        ALTER TABLE pattern_applications
        ADD CONSTRAINT pattern_applications_pattern_id_fkey
        FOREIGN KEY (pattern_id) REFERENCES correlation_patterns(id) ON DELETE CASCADE;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'pattern_applications_source_item_id_fkey'
    ) THEN
        ALTER TABLE pattern_applications
        ADD CONSTRAINT pattern_applications_source_item_id_fkey
        FOREIGN KEY (source_item_id) REFERENCES context_items(id);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'pattern_applications_target_item_id_fkey'
    ) THEN
        ALTER TABLE pattern_applications
        ADD CONSTRAINT pattern_applications_target_item_id_fkey
        FOREIGN KEY (target_item_id) REFERENCES context_items(id);
    END IF;
END $$;

-- ============================================
-- MIGRATION STEP 3: TIMESCALEDB HYPERTABLES
-- ============================================

-- Create hypertable for context_metrics_hourly
SELECT create_hypertable('context_metrics_hourly', 'time_bucket',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE);

-- ============================================
-- MIGRATION STEP 4: INDEXES
-- ============================================

-- Relationship indexes
CREATE INDEX IF NOT EXISTS idx_rel_source ON context_relationships(source_id);
CREATE INDEX IF NOT EXISTS idx_rel_target ON context_relationships(target_id);
CREATE INDEX IF NOT EXISTS idx_rel_type ON context_relationships(relationship_type);
CREATE INDEX IF NOT EXISTS idx_rel_confidence ON context_relationships(confidence DESC)
    WHERE confidence >= 0.7;
CREATE INDEX IF NOT EXISTS idx_rel_created_at ON context_relationships(created_at DESC);

-- Pattern indexes
CREATE INDEX IF NOT EXISTS idx_patterns_type ON correlation_patterns(pattern_type);
CREATE INDEX IF NOT EXISTS idx_patterns_status ON correlation_patterns(pattern_status);
CREATE INDEX IF NOT EXISTS idx_patterns_confidence ON correlation_patterns(confidence DESC);
CREATE INDEX IF NOT EXISTS idx_patterns_support ON correlation_patterns(support_count DESC);

-- JSONB indexes for pattern criteria
CREATE INDEX IF NOT EXISTS idx_patterns_source_criteria ON correlation_patterns
    USING GIN(source_criteria);
CREATE INDEX IF NOT EXISTS idx_patterns_target_criteria ON correlation_patterns
    USING GIN(target_criteria);

-- Knowledge gaps indexes
CREATE INDEX IF NOT EXISTS idx_gaps_type ON knowledge_gaps(gap_type, severity);
CREATE INDEX IF NOT EXISTS idx_gaps_status ON knowledge_gaps(resolution_status);
CREATE INDEX IF NOT EXISTS idx_gaps_file ON knowledge_gaps(file_path)
    WHERE file_path IS NOT NULL;

-- Pattern applications indexes
CREATE INDEX IF NOT EXISTS idx_pattern_apps_pattern ON pattern_applications(pattern_id);
CREATE INDEX IF NOT EXISTS idx_pattern_apps_applied_at ON pattern_applications(applied_at DESC);
CREATE INDEX IF NOT EXISTS idx_pattern_apps_result ON pattern_applications(application_result);

-- ============================================
-- MIGRATION STEP 5: INITIAL DATA
-- ============================================

-- Insert some basic correlation patterns for common relationships
INSERT INTO correlation_patterns (
    pattern_name, pattern_type, source_criteria, target_criteria,
    confidence, discovery_method, metadata
) VALUES
(
    'Git Commit Causes Error',
    'causal',
    '{"source_type": "git", "entity_type": "commit"}',
    '{"source_type": "error", "time_window_minutes": 60}',
    0.8,
    'rule_based',
    '{"description": "Git commits often cause errors within 1 hour"}'
),
(
    'Chat Discussion References Code',
    'co-occurrence',
    '{"source_type": "chat", "has_file_path": true}',
    '{"source_type": "code", "same_file": true}',
    0.9,
    'rule_based',
    '{"description": "Chat messages mentioning files relate to code elements in those files"}'
),
(
    'Error Follows Deployment',
    'temporal',
    '{"source_type": "ci", "entity_type": "deployment"}',
    '{"source_type": "error", "time_window_minutes": 120}',
    0.7,
    'rule_based',
    '{"description": "Errors often follow deployments within 2 hours"}'
)
ON CONFLICT DO NOTHING;

-- ============================================
-- POST-MIGRATION VALIDATION
-- ============================================
DO $$
DECLARE
    table_count INTEGER;
    index_count INTEGER;
BEGIN
    -- Validate all tables were created
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables
    WHERE table_name IN (
        'context_relationships',
        'correlation_patterns',
        'context_metrics_hourly',
        'pattern_applications',
        'knowledge_gaps'
    );

    IF table_count < 5 THEN
        RAISE EXCEPTION 'Migration failed: Expected 5 tables, found %', table_count;
    END IF;

    -- Validate indexes were created
    SELECT COUNT(*) INTO index_count
    FROM pg_indexes
    WHERE indexname LIKE 'idx_rel_%' OR indexname LIKE 'idx_patterns_%' OR indexname LIKE 'idx_gaps_%';

    IF index_count < 10 THEN
        RAISE NOTICE 'Warning: Expected at least 10 indexes, found %', index_count;
    END IF;

    -- Validate hypertable was created
    IF NOT EXISTS (
        SELECT 1 FROM timescaledb_information.hypertables
        WHERE hypertable_name = 'context_metrics_hourly'
    ) THEN
        RAISE EXCEPTION 'Migration failed: context_metrics_hourly hypertable not created';
    END IF;

    RAISE NOTICE 'Migration validation passed: % tables, % indexes created', table_count, index_count;
END $$;

-- ============================================
-- COMMIT MIGRATION
-- ============================================

-- Update migration log with completion
UPDATE migration_log
SET applied_at = NOW()
WHERE migration_id = '001_add_relationship_tables';

COMMIT;

-- ============================================
-- SUCCESS MESSAGE
-- ============================================
DO $$
BEGIN
    RAISE NOTICE '===============================================';
    RAISE NOTICE 'MIGRATION 001 COMPLETED SUCCESSFULLY';
    RAISE NOTICE '===============================================';
    RAISE NOTICE 'Tables Added:';
    RAISE NOTICE '  ✓ context_relationships';
    RAISE NOTICE '  ✓ correlation_patterns';
    RAISE NOTICE '  ✓ context_metrics_hourly (hypertable)';
    RAISE NOTICE '  ✓ pattern_applications';
    RAISE NOTICE '  ✓ knowledge_gaps';
    RAISE NOTICE '';
    RAISE NOTICE 'Indexes Created: 15+ performance indexes';
    RAISE NOTICE 'Sample Data: 3 basic correlation patterns loaded';
    RAISE NOTICE '';
    RAISE NOTICE 'Next Steps:';
    RAISE NOTICE '  1. Run migration 002 for advanced functions';
    RAISE NOTICE '  2. Run migration 003 for materialized views';
    RAISE NOTICE '  3. Test relationship detection';
END $$;
