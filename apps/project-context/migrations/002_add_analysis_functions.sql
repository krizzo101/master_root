-- ============================================
-- MIGRATION 002: ADD ANALYSIS FUNCTIONS
-- Unified Context System Phase 1
-- Advanced analytics and relationship detection functions
-- ============================================

BEGIN;

-- Log this migration
INSERT INTO migration_log (migration_id, description, rollback_sql) VALUES (
    '002_add_analysis_functions',
    'Add advanced analytics and relationship detection functions',
    $rollback$
        DROP FUNCTION IF EXISTS find_relationship_patterns CASCADE;
        DROP FUNCTION IF EXISTS identify_potential_relationships CASCADE;
        DROP FUNCTION IF EXISTS calculate_knowledge_gaps CASCADE;
        DROP FUNCTION IF EXISTS auto_detect_relationships CASCADE;
        DROP FUNCTION IF EXISTS refresh_analytics_views CASCADE;
        DROP FUNCTION IF EXISTS cleanup_system_jobs CASCADE;
        DROP TRIGGER IF EXISTS trigger_auto_detect_relationships ON context_items;
    $rollback$
);

-- ============================================
-- RELATIONSHIP ANALYSIS FUNCTIONS
-- ============================================

-- Function to analyze relationship patterns across the database
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

-- Function to suggest potential relationships for a given context item
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
                -- File-based relationships (high confidence)
                WHEN ic.file_path IS NOT NULL AND ci.file_path = ic.file_path
                    THEN 0.8
                -- Function-based relationships (medium-high confidence)
                WHEN ic.function_name IS NOT NULL AND ci.content ILIKE '%' || ic.function_name || '%'
                    THEN 0.7
                -- Session-based relationships (medium confidence)
                WHEN ic.session_id IS NOT NULL AND ci.session_id = ic.session_id
                    THEN 0.6
                -- Content similarity (variable confidence based on similarity)
                WHEN ci.content IS NOT NULL AND ic.content IS NOT NULL
                    AND similarity(COALESCE(ci.title, ''), COALESCE(ic.title, '')) > 0.3
                    THEN LEAST(similarity(COALESCE(ci.title, ''), COALESCE(ic.title, '')) * 0.8, 0.7)
                -- Temporal proximity (lower confidence)
                WHEN ABS(EXTRACT(EPOCH FROM ci.timestamp - ic.timestamp)) <= time_window_hours * 3600
                    THEN GREATEST(0.3 - (ABS(EXTRACT(EPOCH FROM ci.timestamp - ic.timestamp)) / (time_window_hours * 3600 * 2)), 0.1)
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
            WHEN ct.source_type = 'error' AND (SELECT source_type FROM item_context) IN ('git', 'ci')
                THEN 'causes'
            WHEN ct.source_type IN ('code', 'file') AND (SELECT source_type FROM item_context) = 'chat'
                THEN 'references'
            WHEN ct.timestamp > (SELECT timestamp FROM item_context)
                THEN 'follows'
            WHEN ct.timestamp < (SELECT timestamp FROM item_context)
                THEN 'precedes'
            ELSE 'references'
        END as suggested_relationship_type,
        ct.base_confidence as confidence_score,
        CASE
            WHEN ct.file_path = (SELECT file_path FROM item_context)
                THEN 'Same file context - strong indication of relationship'
            WHEN ct.session_id = (SELECT session_id FROM item_context)
                THEN 'Same session context - likely related discussion'
            WHEN ct.base_confidence > 0.7
                THEN 'Strong content similarity detected'
            WHEN ct.base_confidence > 0.5
                THEN 'Medium similarity - function/symbol references found'
            ELSE 'Temporal proximity - occurred in similar timeframe'
        END as reasoning
    FROM candidate_targets ct
    WHERE ct.base_confidence >= 0.2
      AND NOT EXISTS (
          -- Don't suggest relationships that already exist
          SELECT 1 FROM context_relationships cr
          WHERE cr.source_id = context_item_id AND cr.target_id = ct.id
      )
    ORDER BY ct.base_confidence DESC
    LIMIT max_suggestions;
$$;

-- ============================================
-- KNOWLEDGE GAP ANALYSIS FUNCTIONS
-- ============================================

-- Function to identify and score knowledge gaps in the codebase
CREATE OR REPLACE FUNCTION calculate_knowledge_gaps(
    file_path_filter TEXT DEFAULT NULL,
    gap_threshold INTEGER DEFAULT 5,
    time_window_days INTEGER DEFAULT 30
)
RETURNS TABLE (
    file_path TEXT,
    discussion_frequency INTEGER,
    avg_discussion_complexity FLOAT,
    documentation_coverage FLOAT,
    knowledge_gap_score FLOAT,
    gap_severity VARCHAR(20)
)
LANGUAGE SQL STABLE
AS $$
    WITH file_discussions AS (
        SELECT
            ci.file_path,
            COUNT(*) as discussion_count,
            AVG(COALESCE((ci.metrics->>'tokens')::INTEGER, 100)) as avg_tokens,
            COUNT(DISTINCT ci.session_id) as unique_sessions,
            MAX(ci.timestamp) as latest_discussion
        FROM context_items ci
        WHERE ci.source_type = 'chat'
          AND ci.file_path IS NOT NULL
          AND ci.timestamp >= NOW() - INTERVAL '1 day' * time_window_days
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
            END as doc_coverage,
            AVG(COALESCE(ce.complexity_score, 5)) as avg_complexity
        FROM code_elements ce
        WHERE (file_path_filter IS NULL OR ce.file_path ILIKE '%' || file_path_filter || '%')
        GROUP BY ce.file_path
    ),
    error_frequency AS (
        SELECT
            ci.file_path,
            COUNT(*) as error_count,
            MAX(ci.timestamp) as latest_error
        FROM context_items ci
        WHERE ci.source_type = 'error'
          AND ci.file_path IS NOT NULL
          AND ci.timestamp >= NOW() - INTERVAL '1 day' * time_window_days
        GROUP BY ci.file_path
    )
    SELECT
        COALESCE(fd.file_path, fdoc.file_path, ef.file_path) as file_path,
        COALESCE(fd.discussion_count, 0)::INTEGER as discussion_frequency,
        COALESCE(fd.avg_tokens, 0) as avg_discussion_complexity,
        COALESCE(fdoc.doc_coverage, 0) as documentation_coverage,
        -- Knowledge gap score calculation
        CASE
            WHEN COALESCE(fd.discussion_count, 0) >= gap_threshold
                AND COALESCE(fdoc.doc_coverage, 0) < 0.3
                THEN LEAST(
                    (COALESCE(fd.discussion_count, 0)::FLOAT / 20.0) * -- Discussion frequency weight
                    (1.0 - COALESCE(fdoc.doc_coverage, 0)) * -- Documentation gap weight
                    (1.0 + COALESCE(ef.error_count, 0)::FLOAT / 10.0) * -- Error frequency multiplier
                    (COALESCE(fdoc.avg_complexity, 5) / 10.0), -- Complexity multiplier
                    1.0
                )
            WHEN COALESCE(fd.discussion_count, 0) >= gap_threshold * 2
                THEN 0.3 -- High discussion even with good docs indicates some gap
            WHEN COALESCE(fdoc.doc_coverage, 0) < 0.1 AND COALESCE(fdoc.total_elements, 0) > 5
                THEN 0.4 -- Poor documentation on complex files
            ELSE 0.0
        END as knowledge_gap_score,
        -- Gap severity classification
        CASE
            WHEN COALESCE(fd.discussion_count, 0) >= gap_threshold
                AND COALESCE(fdoc.doc_coverage, 0) < 0.3
                AND COALESCE(ef.error_count, 0) > 2
                THEN 'critical'
            WHEN COALESCE(fd.discussion_count, 0) >= gap_threshold
                AND COALESCE(fdoc.doc_coverage, 0) < 0.5
                THEN 'high'
            WHEN COALESCE(fd.discussion_count, 0) >= gap_threshold / 2
                OR COALESCE(fdoc.doc_coverage, 0) < 0.2
                THEN 'medium'
            ELSE 'low'
        END as gap_severity
    FROM file_discussions fd
    FULL OUTER JOIN file_documentation fdoc ON fd.file_path = fdoc.file_path
    FULL OUTER JOIN error_frequency ef ON COALESCE(fd.file_path, fdoc.file_path) = ef.file_path
    WHERE (
        COALESCE(fd.discussion_count, 0) >= gap_threshold / 2
        OR COALESCE(fdoc.doc_coverage, 0) < 0.3
        OR COALESCE(ef.error_count, 0) > 0
    )
    AND COALESCE(fd.file_path, fdoc.file_path, ef.file_path) IS NOT NULL
    ORDER BY knowledge_gap_score DESC, discussion_frequency DESC;
$$;

-- ============================================
-- AUTOMATED RELATIONSHIP DETECTION
-- ============================================

-- Function to automatically detect relationships when new items are added
CREATE OR REPLACE FUNCTION auto_detect_relationships()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    relationship_suggestions RECORD;
    inserted_count INTEGER := 0;
BEGIN
    -- Only process certain source types to avoid performance issues
    IF NEW.source_type IN ('error', 'git', 'chat', 'ci') AND NEW.content IS NOT NULL THEN

        -- Get potential relationships for this new item
        FOR relationship_suggestions IN
            SELECT * FROM identify_potential_relationships(
                NEW.id,
                ARRAY['references', 'causes', 'follows', 'precedes'],
                24, -- 24 hour window
                5   -- Max 5 suggestions to avoid spam
            )
            WHERE confidence_score >= 0.5 -- Only high confidence suggestions
        LOOP
            -- Insert the suggested relationship
            INSERT INTO context_relationships (
                source_id,
                target_id,
                relationship_type,
                confidence,
                created_by,
                validation_status,
                metadata
            ) VALUES (
                NEW.id,
                relationship_suggestions.suggested_target_id,
                relationship_suggestions.suggested_relationship_type,
                relationship_suggestions.confidence_score,
                'auto_detection',
                'pending',
                jsonb_build_object(
                    'reasoning', relationship_suggestions.reasoning,
                    'auto_detected_at', NOW(),
                    'detection_version', '1.0'
                )
            )
            ON CONFLICT (source_id, target_id, relationship_type) DO NOTHING;

            inserted_count := inserted_count + 1;
        END LOOP;

        -- Log the auto-detection activity if relationships were found
        IF inserted_count > 0 THEN
            UPDATE context_items
            SET metrics = COALESCE(metrics, '{}'::jsonb) || jsonb_build_object(
                'auto_relationships_detected', inserted_count,
                'last_relationship_detection', NOW()
            )
            WHERE id = NEW.id;
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

-- Create trigger for auto-relationship detection (but make it optional)
CREATE OR REPLACE FUNCTION enable_auto_relationship_detection()
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
    -- Drop existing trigger if it exists
    DROP TRIGGER IF EXISTS trigger_auto_detect_relationships ON context_items;

    -- Create new trigger
    CREATE TRIGGER trigger_auto_detect_relationships
        AFTER INSERT ON context_items
        FOR EACH ROW
        EXECUTE FUNCTION auto_detect_relationships();

    RAISE NOTICE 'Auto-relationship detection enabled';
END;
$$;

CREATE OR REPLACE FUNCTION disable_auto_relationship_detection()
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
    DROP TRIGGER IF EXISTS trigger_auto_detect_relationships ON context_items;
    RAISE NOTICE 'Auto-relationship detection disabled';
END;
$$;

-- ============================================
-- MAINTENANCE AND UTILITY FUNCTIONS
-- ============================================

-- Function to clean up system-generated items and old data
CREATE OR REPLACE FUNCTION cleanup_system_jobs(
    older_than_hours INTEGER DEFAULT 24
)
RETURNS RECORD
LANGUAGE plpgsql
AS $$
DECLARE
    cleanup_stats RECORD;
    deleted_items INTEGER;
    deleted_relationships INTEGER;
    deleted_applications INTEGER;
BEGIN
    -- Clean up old relationship detection job markers
    DELETE FROM context_items
    WHERE source_type = 'system'
      AND entity_type LIKE '%_job'
      AND ingested_at < NOW() - INTERVAL '1 hour' * older_than_hours;

    GET DIAGNOSTICS deleted_items = ROW_COUNT;

    -- Clean up low-confidence relationships that haven't been validated
    DELETE FROM context_relationships
    WHERE confidence < 0.3
      AND validation_status = 'pending'
      AND created_at < NOW() - INTERVAL '1 hour' * older_than_hours;

    GET DIAGNOSTICS deleted_relationships = ROW_COUNT;

    -- Clean up old pattern applications
    DELETE FROM pattern_applications
    WHERE applied_at < NOW() - INTERVAL '1 day' * 7 -- Keep 1 week
      AND application_result = 'failure';

    GET DIAGNOSTICS deleted_applications = ROW_COUNT;

    -- Return cleanup statistics
    SELECT deleted_items, deleted_relationships, deleted_applications
    INTO cleanup_stats;

    RETURN cleanup_stats;
END;
$$;

-- Function to validate and score existing relationships
CREATE OR REPLACE FUNCTION validate_relationships(
    batch_size INTEGER DEFAULT 100,
    confidence_threshold FLOAT DEFAULT 0.5
)
RETURNS TABLE (
    relationship_id UUID,
    old_confidence FLOAT,
    new_confidence FLOAT,
    validation_result VARCHAR(20)
)
LANGUAGE plpgsql
AS $$
DECLARE
    rel_record RECORD;
    new_conf FLOAT;
    validation VARCHAR(20);
BEGIN
    -- Process a batch of unvalidated relationships
    FOR rel_record IN
        SELECT cr.id, cr.source_id, cr.target_id, cr.relationship_type, cr.confidence
        FROM context_relationships cr
        WHERE cr.validation_status = 'pending'
          AND cr.confidence >= confidence_threshold
        ORDER BY cr.created_at DESC
        LIMIT batch_size
    LOOP
        -- Re-evaluate confidence based on current data
        -- This is a simplified validation - in practice would use more sophisticated ML
        SELECT COALESCE(
            CASE
                WHEN ci_source.file_path IS NOT NULL AND ci_target.file_path = ci_source.file_path
                    THEN LEAST(rel_record.confidence * 1.2, 1.0)
                WHEN ci_source.session_id IS NOT NULL AND ci_target.session_id = ci_source.session_id
                    THEN LEAST(rel_record.confidence * 1.1, 1.0)
                WHEN ABS(EXTRACT(EPOCH FROM ci_target.timestamp - ci_source.timestamp)) > 86400 -- More than 1 day
                    THEN rel_record.confidence * 0.8
                ELSE rel_record.confidence
            END,
            rel_record.confidence
        ) INTO new_conf
        FROM context_items ci_source
        JOIN context_items ci_target ON ci_target.id = rel_record.target_id
        WHERE ci_source.id = rel_record.source_id;

        -- Determine validation result
        IF new_conf >= 0.8 THEN
            validation := 'validated';
        ELSIF new_conf >= 0.5 THEN
            validation := 'pending';
        ELSE
            validation := 'rejected';
        END IF;

        -- Update the relationship
        UPDATE context_relationships
        SET
            confidence = new_conf,
            validation_status = validation,
            validation_score = new_conf,
            last_validated = NOW()
        WHERE id = rel_record.id;

        -- Return the result
        RETURN QUERY SELECT rel_record.id, rel_record.confidence, new_conf, validation;
    END LOOP;
END;
$$;

-- ============================================
-- GRANTS AND PERMISSIONS
-- ============================================

-- Grant execute permissions on all new functions
GRANT EXECUTE ON FUNCTION find_relationship_patterns TO opsvi;
GRANT EXECUTE ON FUNCTION identify_potential_relationships TO opsvi;
GRANT EXECUTE ON FUNCTION calculate_knowledge_gaps TO opsvi;
GRANT EXECUTE ON FUNCTION enable_auto_relationship_detection TO opsvi;
GRANT EXECUTE ON FUNCTION disable_auto_relationship_detection TO opsvi;
GRANT EXECUTE ON FUNCTION cleanup_system_jobs TO opsvi;
GRANT EXECUTE ON FUNCTION validate_relationships TO opsvi;

-- Update migration log
UPDATE migration_log
SET applied_at = NOW()
WHERE migration_id = '002_add_analysis_functions';

COMMIT;

-- ============================================
-- SUCCESS MESSAGE
-- ============================================
DO $$
BEGIN
    RAISE NOTICE '===============================================';
    RAISE NOTICE 'MIGRATION 002 COMPLETED SUCCESSFULLY';
    RAISE NOTICE '===============================================';
    RAISE NOTICE 'Functions Added:';
    RAISE NOTICE '  ✓ find_relationship_patterns()';
    RAISE NOTICE '  ✓ identify_potential_relationships()';
    RAISE NOTICE '  ✓ calculate_knowledge_gaps()';
    RAISE NOTICE '  ✓ auto_detect_relationships() + trigger';
    RAISE NOTICE '  ✓ validate_relationships()';
    RAISE NOTICE '  ✓ cleanup_system_jobs()';
    RAISE NOTICE '  ✓ enable/disable_auto_relationship_detection()';
    RAISE NOTICE '';
    RAISE NOTICE 'Features Ready:';
    RAISE NOTICE '  • Intelligent relationship suggestion';
    RAISE NOTICE '  • Knowledge gap analysis and scoring';
    RAISE NOTICE '  • Automated relationship detection (disabled by default)';
    RAISE NOTICE '  • Relationship validation and scoring';
    RAISE NOTICE '  • System maintenance and cleanup';
    RAISE NOTICE '';
    RAISE NOTICE 'Next Steps:';
    RAISE NOTICE '  1. Run: SELECT enable_auto_relationship_detection();';
    RAISE NOTICE '  2. Test: SELECT * FROM calculate_knowledge_gaps();';
    RAISE NOTICE '  3. Run migration 003 for materialized views';
END $$;
