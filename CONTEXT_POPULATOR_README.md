# Context Items Populator

A comprehensive data ingestion system for the unified context system that populates the `context_items` table from all available data sources.

## Features

✅ **Multi-source ingestion**: .proj-intel data, chat logs, monitoring metrics, system events
✅ **Batch processing**: High-performance async batch insertions
✅ **Data validation**: Comprehensive validation and deduplication
✅ **Progress tracking**: Real-time progress updates and error handling
✅ **Resumable ingestion**: Checkpoint system for large datasets
✅ **Conflict handling**: ON CONFLICT handling for duplicate data
✅ **Flexible configuration**: Configurable data sources and processing parameters

## Quick Start

### Basic Usage
```bash
# Run full ingestion from all sources
python context_items_populator.py

# Run with custom batch size and workers
python context_items_populator.py --batch-size 500 --max-workers 10

# Clear existing data and start fresh
python context_items_populator.py --clear-data --no-resume

# Use custom PostgreSQL URL
python context_items_populator.py --postgres-url "postgresql://user:pass@host:port/db"
```

### Test Mode
```bash
# Run limited test ingestion
python test_context_populator.py
```

## Data Sources

### 1. .proj-intel Data (Code Intelligence)
- **Source**: Multiple `.proj-intel` directories
- **Content**: Functions, classes, imports, code structure
- **Entity types**: `function`, `class`, `import`, `file`
- **Metadata**: Complexity scores, dependencies, language info

### 2. Chat Logs
- **SQLite Database**: `/home/opsvi/master_root/chat_logs.db`
- **Text Files**: Various chat log files across the project
- **Content**: User interactions, AI responses, session data
- **Entity types**: `sessions`, `messages`, `text_log`

### 3. Monitoring Data
- **System Metrics**: CPU, memory, disk usage snapshots
- **Log Files**: Application and system monitoring logs
- **Content**: Performance metrics, errors, warnings
- **Entity types**: `metrics`, `log_entry`

## Database Schema Integration

The populator inserts into the `context_items` table with the following key fields:

```sql
CREATE TABLE context_items (
    source_type VARCHAR(50),      -- 'code', 'chat', 'monitor', 'system'
    source_id VARCHAR(255),       -- Unique ID from source system
    entity_type VARCHAR(100),     -- Specific entity type
    timestamp TIMESTAMPTZ,        -- Event timestamp
    content TEXT,                 -- Searchable content
    content_hash VARCHAR(64),     -- Deduplication hash
    file_path TEXT,              -- Associated file path
    session_id VARCHAR(255),      -- Link to chat sessions
    metrics JSONB,                -- Flexible metrics storage
    source_data JSONB,            -- Original data preserved
    tags TEXT[]                   -- Searchable tags
);
```

## Configuration

Edit the `data_sources` configuration in the populator:

```python
self.data_sources = {
    "proj_intel": {
        "paths": [
            "/home/opsvi/master_root/.proj-intel",
            "/home/opsvi/master_root/libs/.proj-intel",
            # Add more paths...
        ],
        "enabled": True,
        "priority": 1,
    },
    "chat_logs": {
        "sqlite_path": "/home/opsvi/master_root/chat_logs.db",
        "text_logs": [
            "/home/opsvi/master_root/chat_improvement_log.txt",
            # Add more log files...
        ],
        "enabled": True,
        "priority": 2,
    }
}
```

## Performance Characteristics

- **Batch Size**: Default 1000 items per batch
- **Concurrency**: Default 5 async workers
- **Deduplication**: Content-based hashing prevents duplicates
- **Conflict Resolution**: ON CONFLICT DO UPDATE for existing items
- **Checkpointing**: Progress saved to `/tmp/context_items_checkpoint.json`

## Output Statistics

The populator provides detailed statistics:
```
📊 Final statistics:
   Proj-intel items: 2,847
   Chat log items: 1,256
   System metric items: 48
   Total new items: 4,151
   Processing errors: 3
   Skipped duplicates: 127
```

## Query Examples

After ingestion, you can query the unified context:

```sql
-- Recent code changes
SELECT * FROM context_items
WHERE source_type = 'code'
  AND timestamp > NOW() - INTERVAL '1 day';

-- Chat conversations about specific files
SELECT * FROM context_items
WHERE source_type = 'chat'
  AND content ILIKE '%filename.py%';

-- System performance metrics
SELECT metrics->>'cpu_percent' as cpu_usage
FROM context_items
WHERE source_type = 'system'
  AND entity_type = 'metrics';

-- Cross-source correlations
SELECT ci.source_type, ci.entity_type, COUNT(*)
FROM context_items ci
WHERE ci.session_id IN (
    SELECT DISTINCT session_id
    FROM context_items
    WHERE file_path = '/path/to/file.py'
)
GROUP BY ci.source_type, ci.entity_type;
```

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   .proj-intel   │    │   Chat Logs      │    │   Monitoring    │
│   - Functions   │    │   - SQLite DB    │    │   - Log Files   │
│   - Classes     │    │   - Text Files   │    │   - Metrics     │
│   - Imports     │    │   - Sessions     │    │   - System Info │
└─────────┬───────┘    └─────────┬────────┘    └─────────┬───────┘
          │                      │                       │
          └──────────────────────┼───────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   Context Populator     │
                    │   - Validation          │
                    │   - Deduplication       │
                    │   - Batch Processing    │
                    │   - Error Handling      │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   PostgreSQL            │
                    │   context_items table   │
                    │   - Unified schema      │
                    │   - JSONB flexibility   │
                    │   - Time-series         │
                    │   - Full-text search    │
                    └─────────────────────────┘
```

## Error Handling

The populator includes comprehensive error handling:
- **Validation errors**: Invalid items are logged and skipped
- **Database errors**: Individual item failures don't stop batch processing
- **Network errors**: Automatic retry logic for transient failures
- **Schema mismatches**: Graceful handling of unexpected data formats

## Monitoring & Logging

- Progress updates every batch
- Error logging with details
- Performance metrics tracking
- Final ingestion report with statistics

## Next Steps

1. **Schedule Regular Ingestion**: Set up cron job for periodic updates
2. **Add More Sources**: Extend to include IDE snapshots, git history
3. **Optimize Queries**: Add specialized indexes for common query patterns
4. **Real-time Updates**: Consider streaming ingestion for live data

## Troubleshooting

**Database Connection Issues**:
- Check PostgreSQL is running
- Verify connection credentials
- Ensure database exists and schema is created

**Memory Issues**:
- Reduce batch size (`--batch-size 100`)
- Decrease max workers (`--max-workers 2`)
- Process sources individually

**Duplicate Key Errors**:
- The populator handles duplicates automatically via ON CONFLICT
- If persistent issues occur, clear data with `--clear-data`

---

For support or questions, check the implementation in `context_items_populator.py` or run the test suite with `test_context_populator.py`.
