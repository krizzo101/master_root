#!/bin/bash
# Materialized Views Test Runner
# Tests the unified context system's PostgreSQL materialized views

set -e

DB_CONNECTION="postgresql://opsvi:opsvi_secure_password@localhost:5432/unified_context"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
REPORT_FILE="mv_test_report_${TIMESTAMP}.json"

echo "=========================================="
echo "MATERIALIZED VIEWS TEST SUITE"
echo "=========================================="
echo "Database: ${DB_CONNECTION}"
echo "Report file: ${REPORT_FILE}"
echo "Started at: $(date)"
echo ""

# Check if Python dependencies are available
echo "Checking dependencies..."
python3 -c "import psycopg2, pandas" 2>/dev/null || {
    echo "Installing required Python packages..."
    pip install psycopg2-binary pandas
}

# Check database connectivity
echo "Testing database connection..."
psql "${DB_CONNECTION}" -c "SELECT version();" > /dev/null || {
    echo "ERROR: Cannot connect to database"
    echo "Please ensure PostgreSQL is running and credentials are correct"
    exit 1
}

echo "✓ Database connection successful"

# Check if materialized views exist
echo ""
echo "Checking materialized view existence..."
psql "${DB_CONNECTION}" -t -c "
    SELECT 'Found MV: ' || matviewname
    FROM pg_matviews
    WHERE schemaname = 'public'
    ORDER BY matviewname;
" || {
    echo "ERROR: Could not query materialized views"
    exit 1
}

# Run the Python test suite
echo ""
echo "Running comprehensive Python test suite..."
python3 test_materialized_views.py

echo ""
echo "=========================================="
echo "MANUAL TESTS"
echo "=========================================="

# Manual test 1: Check view contents
echo "1. Checking materialized view contents:"
echo ""

echo "   hourly_token_usage rows:"
psql "${DB_CONNECTION}" -t -c "SELECT COUNT(*) FROM hourly_token_usage;"

echo "   daily_file_activity rows:"
psql "${DB_CONNECTION}" -t -c "SELECT COUNT(*) FROM daily_file_activity;"

# Manual test 2: Test refresh function
echo ""
echo "2. Testing refresh function execution:"
psql "${DB_CONNECTION}" -c "SELECT refresh_materialized_views();" && {
    echo "✓ Refresh function executed successfully"
} || {
    echo "✗ Refresh function failed"
}

# Manual test 3: Check index usage
echo ""
echo "3. Checking materialized view indexes:"
psql "${DB_CONNECTION}" -c "
    SELECT
        schemaname,
        matviewname,
        hasindexes,
        ispopulated
    FROM pg_matviews
    WHERE schemaname = 'public';
"

# Manual test 4: Sample performance test
echo ""
echo "4. Quick performance comparison:"

echo "   Base query timing (token aggregation):"
psql "${DB_CONNECTION}" -c "\timing on" -c "
    SELECT
        source_type,
        SUM((metrics->>'tokens_input')::int) as total_input,
        SUM((metrics->>'tokens_output')::int) as total_output,
        SUM((metrics->>'cost')::numeric) as total_cost
    FROM context_items
    WHERE source_type IN ('chat', 'agent')
      AND metrics ? 'tokens_input'
    GROUP BY source_type;
" -c "\timing off"

echo ""
echo "   Materialized view timing (token aggregation):"
psql "${DB_CONNECTION}" -c "\timing on" -c "
    SELECT
        source_type,
        SUM(total_input_tokens) as total_input,
        SUM(total_output_tokens) as total_output,
        SUM(total_cost) as total_cost
    FROM hourly_token_usage
    GROUP BY source_type;
" -c "\timing off"

# Check for unique indexes (required for CONCURRENTLY refresh)
echo ""
echo "5. Checking unique indexes for concurrent refresh:"
psql "${DB_CONNECTION}" -c "
    SELECT
        i.relname as index_name,
        t.relname as table_name,
        ix.indisunique as is_unique
    FROM pg_class i
    JOIN pg_index ix ON i.oid = ix.indexrelid
    JOIN pg_class t ON ix.indrelid = t.oid
    WHERE t.relname IN ('hourly_token_usage', 'daily_file_activity')
    ORDER BY t.relname, i.relname;
"

# Test concurrent refresh capability
echo ""
echo "6. Testing concurrent refresh (requires unique indexes):"

for view in "hourly_token_usage" "daily_file_activity"; do
    echo "   Testing ${view}..."
    psql "${DB_CONNECTION}" -c "REFRESH MATERIALIZED VIEW CONCURRENTLY ${view};" 2>&1 | {
        if grep -q "ERROR"; then
            echo "   ✗ Concurrent refresh not available for ${view} (no unique index)"
        else
            echo "   ✓ Concurrent refresh successful for ${view}"
        fi
    }
done

echo ""
echo "=========================================="
echo "VIEW MONITORING QUERIES"
echo "=========================================="

# Provide monitoring queries
echo "7. View staleness check:"
psql "${DB_CONNECTION}" -c "
    WITH latest_data AS (
        SELECT
            MAX(timestamp) as latest_context_timestamp,
            MAX(CASE WHEN source_type IN ('chat', 'agent') AND metrics ? 'tokens_input'
                     THEN timestamp END) as latest_token_timestamp,
            MAX(CASE WHEN file_path IS NOT NULL
                     THEN timestamp END) as latest_file_timestamp
        FROM context_items
    ),
    mv_data AS (
        SELECT
            (SELECT MAX(hour) FROM hourly_token_usage) as latest_token_mv,
            (SELECT MAX(day) FROM daily_file_activity) as latest_file_mv
    )
    SELECT
        'hourly_token_usage' as view_name,
        ld.latest_token_timestamp as source_latest,
        mv.latest_token_mv as mv_latest,
        CASE
            WHEN ld.latest_token_timestamp > mv.latest_token_mv
            THEN EXTRACT(EPOCH FROM (ld.latest_token_timestamp - mv.latest_token_mv)) / 3600
            ELSE 0
        END as staleness_hours
    FROM latest_data ld, mv_data mv

    UNION ALL

    SELECT
        'daily_file_activity' as view_name,
        ld.latest_file_timestamp as source_latest,
        mv.latest_file_mv as mv_latest,
        CASE
            WHEN ld.latest_file_timestamp > mv.latest_file_mv
            THEN EXTRACT(EPOCH FROM (ld.latest_file_timestamp - mv.latest_file_mv)) / 86400
            ELSE 0
        END as staleness_hours
    FROM latest_data ld, mv_data mv;
"

echo ""
echo "8. View sizes:"
psql "${DB_CONNECTION}" -c "
    SELECT
        schemaname,
        matviewname,
        pg_size_pretty(pg_total_relation_size(schemaname||'.'||matviewname)) as size
    FROM pg_matviews
    WHERE schemaname = 'public'
    ORDER BY pg_total_relation_size(schemaname||'.'||matviewname) DESC;
"

echo ""
echo "=========================================="
echo "TEST COMPLETED"
echo "=========================================="
echo "Finished at: $(date)"
echo ""
echo "Next steps:"
echo "1. Review the generated JSON report: materialized_views_test_report.json"
echo "2. Set up automated refresh schedule if needed"
echo "3. Monitor view staleness using the provided queries"
echo "4. Consider adding unique indexes if concurrent refresh is required"
echo ""

# Save this script's execution log
echo "Test execution completed successfully" > "mv_test_${TIMESTAMP}.log"
