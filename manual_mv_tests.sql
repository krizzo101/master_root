-- ============================================
-- MANUAL MATERIALIZED VIEWS TESTING SCRIPT
-- Quick validation queries for unified context system
-- ============================================

\echo 'Starting materialized views manual testing...'
\echo ''

-- Check database connection and timing
\timing on
\echo 'Timing enabled for performance comparison'
\echo ''

-- ============================================
-- 1. VIEW EXISTENCE CHECK
-- ============================================
\echo '1. Checking materialized view existence:'
SELECT
    schemaname,
    matviewname,
    hasindexes,
    ispopulated,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||matviewname)) as size
FROM pg_matviews
WHERE schemaname = 'public'
ORDER BY matviewname;

\echo ''

-- ============================================
-- 2. DATA POPULATION CHECK
-- ============================================
\echo '2. Checking data population:'
\echo '   hourly_token_usage rows:'
SELECT COUNT(*) as row_count FROM hourly_token_usage;

\echo '   daily_file_activity rows:'
SELECT COUNT(*) as row_count FROM daily_file_activity;

\echo '   Sample hourly_token_usage data:'
SELECT
    hour,
    source_type,
    total_input_tokens,
    total_output_tokens,
    total_cost,
    unique_sessions
FROM hourly_token_usage
ORDER BY hour DESC
LIMIT 5;

\echo '   Sample daily_file_activity data:'
SELECT
    day,
    file_path,
    touch_count,
    session_count,
    activity_types
FROM daily_file_activity
ORDER BY day DESC, touch_count DESC
LIMIT 5;

\echo ''

-- ============================================
-- 3. REFRESH FUNCTION TEST
-- ============================================
\echo '3. Testing refresh function:'
SELECT refresh_materialized_views() as refresh_result;

\echo '   Testing individual view refresh:'
REFRESH MATERIALIZED VIEW hourly_token_usage;
\echo '   ✓ hourly_token_usage refreshed'

REFRESH MATERIALIZED VIEW daily_file_activity;
\echo '   ✓ daily_file_activity refreshed'

\echo ''

-- ============================================
-- 4. PERFORMANCE COMPARISON TESTS
-- ============================================
\echo '4. Performance comparison - Token Usage Aggregation:'
\echo ''
\echo '   A. Base table query (complex):'
SELECT
    source_type,
    SUM((metrics->>'tokens_input')::int) as total_input,
    SUM((metrics->>'tokens_output')::int) as total_output,
    SUM((metrics->>'cost')::numeric) as total_cost,
    COUNT(DISTINCT session_id) as unique_sessions
FROM context_items
WHERE source_type IN ('chat', 'agent')
  AND metrics ? 'tokens_input'
GROUP BY source_type
ORDER BY source_type;

\echo ''
\echo '   B. Materialized view query (optimized):'
SELECT
    source_type,
    SUM(total_input_tokens) as total_input,
    SUM(total_output_tokens) as total_output,
    SUM(total_cost) as total_cost,
    SUM(unique_sessions) as unique_sessions
FROM hourly_token_usage
GROUP BY source_type
ORDER BY source_type;

\echo ''

-- ============================================
-- 5. DATA CONSISTENCY VALIDATION
-- ============================================
\echo '5. Data consistency validation:'
\echo ''
\echo '   Comparing aggregated totals:'

WITH base_totals AS (
    SELECT
        SUM((metrics->>'tokens_input')::int) as base_input,
        SUM((metrics->>'tokens_output')::int) as base_output,
        SUM((metrics->>'cost')::numeric) as base_cost
    FROM context_items
    WHERE source_type IN ('chat', 'agent')
      AND metrics ? 'tokens_input'
),
mv_totals AS (
    SELECT
        SUM(total_input_tokens) as mv_input,
        SUM(total_output_tokens) as mv_output,
        SUM(total_cost) as mv_cost
    FROM hourly_token_usage
)
SELECT
    bt.base_input,
    mt.mv_input,
    (bt.base_input = mt.mv_input) as input_match,
    bt.base_output,
    mt.mv_output,
    (bt.base_output = mt.mv_output) as output_match,
    ROUND(bt.base_cost, 4) as base_cost,
    ROUND(mt.mv_cost, 4) as mv_cost,
    (ROUND(bt.base_cost, 4) = ROUND(mt.mv_cost, 4)) as cost_match
FROM base_totals bt, mv_totals mt;

\echo ''

-- ============================================
-- 6. STALENESS CHECK
-- ============================================
\echo '6. Staleness monitoring:'
WITH source_times AS (
    SELECT
        MAX(CASE WHEN source_type IN ('chat', 'agent') AND metrics ? 'tokens_input'
                 THEN timestamp END) as latest_token_data,
        MAX(CASE WHEN file_path IS NOT NULL
                 THEN timestamp END) as latest_file_data
    FROM context_items
),
mv_times AS (
    SELECT
        (SELECT MAX(hour) FROM hourly_token_usage) as latest_token_mv,
        (SELECT MAX(day) FROM daily_file_activity) as latest_file_mv
)
SELECT
    'hourly_token_usage' as view_name,
    st.latest_token_data as source_latest,
    mt.latest_token_mv as mv_latest,
    CASE
        WHEN st.latest_token_data IS NOT NULL AND mt.latest_token_mv IS NOT NULL
        THEN ROUND(EXTRACT(EPOCH FROM (st.latest_token_data - mt.latest_token_mv)) / 3600, 2)
        ELSE NULL
    END as staleness_hours
FROM source_times st, mv_times mt

UNION ALL

SELECT
    'daily_file_activity' as view_name,
    st.latest_file_data as source_latest,
    mt.latest_file_mv as mv_latest,
    CASE
        WHEN st.latest_file_data IS NOT NULL AND mt.latest_file_mv IS NOT NULL
        THEN ROUND(EXTRACT(EPOCH FROM (st.latest_file_data - mt.latest_file_mv)) / 86400, 2)
        ELSE NULL
    END as staleness_days
FROM source_times st, mv_times mt;

\echo ''

-- ============================================
-- 7. INDEX AND CONCURRENT REFRESH TEST
-- ============================================
\echo '7. Testing concurrent refresh capability:'
\echo ''

\echo '   Checking for unique indexes:'
SELECT
    t.relname as table_name,
    i.relname as index_name,
    ix.indisunique as is_unique,
    array_agg(a.attname ORDER BY a.attnum) as indexed_columns
FROM pg_class t
JOIN pg_index ix ON t.oid = ix.indrelid
JOIN pg_class i ON i.oid = ix.indexrelid
JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey)
WHERE t.relname IN ('hourly_token_usage', 'daily_file_activity')
  AND ix.indisunique = true
GROUP BY t.relname, i.relname, ix.indisunique
ORDER BY t.relname, i.relname;

\echo '   Testing concurrent refresh (may fail without unique indexes):'

DO $$
BEGIN
    BEGIN
        REFRESH MATERIALIZED VIEW CONCURRENTLY hourly_token_usage;
        RAISE NOTICE '✓ hourly_token_usage: Concurrent refresh successful';
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE '✗ hourly_token_usage: Concurrent refresh failed (%) - use regular refresh', SQLERRM;
    END;

    BEGIN
        REFRESH MATERIALIZED VIEW CONCURRENTLY daily_file_activity;
        RAISE NOTICE '✓ daily_file_activity: Concurrent refresh successful';
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE '✗ daily_file_activity: Concurrent refresh failed (%) - use regular refresh', SQLERRM;
    END;
END $$;

\echo ''

-- ============================================
-- 8. PERFORMANCE METRICS
-- ============================================
\echo '8. Performance and usage metrics:'
SELECT
    schemaname,
    matviewname,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||matviewname)) as total_size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||matviewname)) as table_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||matviewname) -
                   pg_relation_size(schemaname||'.'||matviewname)) as index_size
FROM pg_matviews
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||matviewname) DESC;

\echo ''

-- ============================================
-- 9. RECOMMENDATIONS
-- ============================================
\echo '9. Performance recommendations:'

DO $$
DECLARE
    token_staleness NUMERIC;
    file_staleness NUMERIC;
    token_rows INTEGER;
    file_rows INTEGER;
BEGIN
    -- Check staleness
    SELECT
        COALESCE(EXTRACT(EPOCH FROM (MAX(ci.timestamp) - MAX(htu.hour))) / 3600, 0)
    INTO token_staleness
    FROM context_items ci
    CROSS JOIN (SELECT MAX(hour) as hour FROM hourly_token_usage LIMIT 1) htu
    WHERE ci.source_type IN ('chat', 'agent') AND ci.metrics ? 'tokens_input';

    SELECT COUNT(*) INTO token_rows FROM hourly_token_usage;
    SELECT COUNT(*) INTO file_rows FROM daily_file_activity;

    RAISE NOTICE 'RECOMMENDATIONS:';
    RAISE NOTICE '================';

    IF token_staleness > 2 THEN
        RAISE NOTICE '• hourly_token_usage is %.1f hours stale - consider more frequent refresh', token_staleness;
    ELSE
        RAISE NOTICE '• hourly_token_usage staleness (%.1f hours) is acceptable', token_staleness;
    END IF;

    IF token_rows = 0 THEN
        RAISE NOTICE '• hourly_token_usage is empty - populate with initial data';
    ELSIF token_rows < 24 THEN
        RAISE NOTICE '• hourly_token_usage has % rows - consider generating more test data', token_rows;
    ELSE
        RAISE NOTICE '• hourly_token_usage has % rows - good population', token_rows;
    END IF;

    IF file_rows = 0 THEN
        RAISE NOTICE '• daily_file_activity is empty - populate with initial data';
    ELSE
        RAISE NOTICE '• daily_file_activity has % rows - adequate for testing', file_rows;
    END IF;

    RAISE NOTICE '• Set up automated refresh every 15-30 minutes for optimal performance';
    RAISE NOTICE '• Monitor staleness with provided queries';
    RAISE NOTICE '• Consider adding unique indexes for concurrent refresh capability';
END $$;

\echo ''
\echo 'Manual testing completed!'
\echo 'For comprehensive testing, run: python3 test_materialized_views.py'
\echo 'For automated testing, run: ./run_materialized_view_tests.sh'

\timing off
