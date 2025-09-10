# Materialized Views Testing Guide

## Overview

The unified context system uses PostgreSQL materialized views to optimize performance for commonly executed queries. This guide provides comprehensive testing procedures for validating these views.

## Materialized Views in the System

### 1. hourly_token_usage
**Purpose**: Aggregates token usage and costs by hour and source type
**Source Tables**: `context_items`
**Schema**: `init-scripts/01-create-schema.sql:299-310`

```sql
-- Aggregates token usage data from context_items
-- Groups by 1-hour time buckets and source_type
-- Includes: total_input_tokens, total_output_tokens, total_cost, unique_sessions
```

### 2. daily_file_activity
**Purpose**: Tracks file activity patterns by day
**Source Tables**: `context_items`
**Schema**: `init-scripts/01-create-schema.sql:312-321`

```sql
-- Aggregates file activity from context_items
-- Groups by 1-day time buckets and file_path
-- Includes: touch_count, session_count, activity_types
```

### 3. Refresh Function
**Function**: `refresh_materialized_views()`
**Schema**: `init-scripts/01-create-schema.sql:326-332`

```sql
-- Refreshes both materialized views concurrently
-- Provides atomic refresh operation for all views
```

## Testing Components

### 1. Automated Python Test Suite
**File**: `test_materialized_views.py`
**Features**:
- Data consistency validation
- Performance benchmarking (base queries vs materialized views)
- Refresh function testing
- Staleness monitoring
- Automatic test data generation

### 2. Shell Test Runner
**File**: `run_materialized_view_tests.sh`
**Features**:
- Database connectivity verification
- Manual test execution
- Performance comparisons
- Index validation
- Monitoring query examples

## Test Categories

### A. Existence Tests
```bash
# Check if materialized views exist
psql $DB_CONNECTION -c "SELECT matviewname FROM pg_matviews WHERE schemaname = 'public'"
```

### B. Data Consistency Tests
Validates that materialized view data matches base table queries:
- Row count comparison
- Aggregate value verification
- Data type consistency

### C. Performance Benchmarks
Compares execution times:
- Base table queries (complex aggregations)
- Materialized view queries (simple selects)
- Measures percentage improvement

### D. Refresh Function Tests
- `refresh_materialized_views()` execution
- Individual view refresh capability
- Concurrent refresh support (requires unique indexes)
- Refresh timing measurements

### E. Staleness Monitoring
- Compares latest data timestamps between source tables and views
- Calculates staleness in hours/days
- Identifies when refresh is needed

## Running the Tests

### Quick Test
```bash
./run_materialized_view_tests.sh
```

### Comprehensive Test (Python)
```bash
python3 test_materialized_views.py
```

### Manual Verification
```sql
-- Check view populations
SELECT COUNT(*) FROM hourly_token_usage;
SELECT COUNT(*) FROM daily_file_activity;

-- Test refresh function
SELECT refresh_materialized_views();

-- Check staleness
SELECT
    'hourly_token_usage' as view,
    MAX(timestamp) as latest_source,
    (SELECT MAX(hour) FROM hourly_token_usage) as latest_mv
FROM context_items
WHERE source_type IN ('chat', 'agent') AND metrics ? 'tokens_input';
```

## Expected Performance Improvements

### Token Usage Queries
- **Base Query**: Complex JSONB operations, aggregations across time buckets
- **Materialized View**: Simple SUM operations on pre-computed values
- **Expected Improvement**: 60-90% faster execution

### File Activity Queries
- **Base Query**: Multiple aggregations, array operations, DISTINCT counts
- **Materialized View**: Simple aggregations on pre-computed values
- **Expected Improvement**: 50-80% faster execution

## Monitoring and Maintenance

### Staleness Monitoring
```sql
-- Check how stale views are
WITH source_freshness AS (
    SELECT
        MAX(timestamp) as latest_tokens
    FROM context_items
    WHERE source_type IN ('chat', 'agent') AND metrics ? 'tokens_input'
),
mv_freshness AS (
    SELECT MAX(hour) as latest_hour FROM hourly_token_usage
)
SELECT
    EXTRACT(EPOCH FROM (sf.latest_tokens - mf.latest_hour)) / 3600 as staleness_hours
FROM source_freshness sf, mv_freshness mf;
```

### Automated Refresh Strategy
```sql
-- Create automated refresh based on staleness
CREATE OR REPLACE FUNCTION auto_refresh_if_stale(threshold_hours INTEGER DEFAULT 1)
RETURNS void AS $$
BEGIN
    -- Implementation in test_materialized_views.py
    -- Checks staleness and refreshes if needed
END;
$$ LANGUAGE plpgsql;
```

### Size Monitoring
```sql
-- Monitor view sizes
SELECT
    matviewname,
    pg_size_pretty(pg_total_relation_size(matviewname)) as size
FROM pg_matviews
WHERE schemaname = 'public';
```

## Troubleshooting

### Common Issues

1. **Concurrent Refresh Fails**
   - **Cause**: No unique index on materialized view
   - **Solution**: Create unique index or use non-concurrent refresh

2. **Poor Performance Improvement**
   - **Cause**: Views not properly indexed or source queries already optimized
   - **Solution**: Add appropriate indexes to materialized views

3. **Data Inconsistency**
   - **Cause**: Views not refreshed after source data changes
   - **Solution**: Implement refresh triggers or scheduled refresh

4. **High Staleness**
   - **Cause**: Infrequent refresh schedule
   - **Solution**: Increase refresh frequency or implement trigger-based refresh

### Diagnostic Queries

```sql
-- Check index usage on materialized views
SELECT
    schemaname, matviewname, hasindexes, ispopulated
FROM pg_matviews WHERE schemaname = 'public';

-- View definition inspection
SELECT definition FROM pg_matviews WHERE matviewname = 'hourly_token_usage';

-- Check view dependencies
SELECT DISTINCT
    refobjid::regclass AS referenced_table
FROM pg_depend d
JOIN pg_rewrite r ON r.oid = d.objid
JOIN pg_class c ON c.oid = r.ev_class
WHERE c.relname = 'hourly_token_usage';
```

## Integration with Production

### Recommended Refresh Schedule
- **hourly_token_usage**: Every 15-30 minutes
- **daily_file_activity**: Every 1-2 hours or daily at midnight

### Monitoring Alerts
- Staleness > 2 hours for hourly_token_usage
- Staleness > 6 hours for daily_file_activity
- Refresh failures
- Unusual refresh times (> 30 seconds)

### Performance Baselines
After running tests, establish baselines for:
- Normal refresh times
- Expected performance improvements
- Typical view sizes
- Normal staleness patterns

## Test Output Files

- `materialized_views_test_report.json`: Comprehensive test results
- `mv_test_YYYYMMDD_HHMMSS.log`: Test execution log
- Performance metrics and recommendations

## Future Enhancements

Consider adding:
1. Additional materialized views for other common query patterns
2. Automatic refresh triggers based on source table changes
3. Partitioned materialized views for very large datasets
4. Custom aggregation functions for domain-specific metrics
