# PostgreSQL Setup Instructions for Chat/Intel Team

## Your Mission
Set up PostgreSQL with TimescaleDB as the foundation for the Unified Context System.

## Step 1: Start PostgreSQL with Docker

Use the docker-compose file already created:

```bash
cd /home/opsvi/master_root
docker-compose -f docker-compose.postgres.yml up -d
```

This gives you:
- PostgreSQL 15 with TimescaleDB on port 5432
- pgAdmin on port 5433 (http://localhost:5433)
- Database: `unified_context`
- User: `opsvi` / Password: `opsvi_secure_password`

## Step 2: Create Initial Schema

Create this file: `/home/opsvi/master_root/init-scripts/01-create-schema.sql`

```sql
-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
CREATE EXTENSION IF NOT EXISTS vector;  -- Note: May need pgvector Docker image
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create the schema from the master design
-- Copy the ENTIRE Section 3 from:
-- /home/opsvi/master_root/docs/UNIFIED_CONTEXT_SYSTEM_FINAL_DESIGN.md

-- Start with core tables:
-- 1. context_items (with hypertable)
-- 2. chat_sessions (your existing structure, enhanced)
-- 3. code_elements (for .proj-intel)
-- 4. monitoring_metrics (with hypertable)
-- 5. code_context (YOUR correlation table - finally!)
-- 6. agent_usage (YOUR other correlation table)
```

## Step 3: Run Schema Creation

```bash
# After PostgreSQL is running
docker exec -it unified_context_postgres psql -U opsvi -d unified_context -f /docker-entrypoint-initdb.d/01-create-schema.sql
```

Or use pgAdmin at http://localhost:5433

## Step 4: Implement Dual-Write Pattern

In your ingestion code, add PostgreSQL alongside SQLite:

```python
import asyncpg  # Better than psycopg2 for async
import sqlite3

class DualDatabaseIngester:
    def __init__(self):
        # Keep SQLite for now
        self.sqlite = sqlite3.connect('/home/opsvi/master_root/chat_logs.db')

        # Add PostgreSQL
        self.pg_pool = None

    async def connect_postgres(self):
        self.pg_pool = await asyncpg.create_pool(
            'postgresql://opsvi:opsvi_secure_password@localhost:5432/unified_context',
            min_size=10,
            max_size=20
        )

    async def ingest_message(self, message):
        # Write to SQLite (existing code)
        self.sqlite.execute("INSERT INTO messages...")

        # ALSO write to PostgreSQL
        async with self.pg_pool.acquire() as conn:
            # Insert into context_items
            await conn.execute("""
                INSERT INTO context_items (
                    source_type, entity_type, timestamp,
                    content, session_id, actor_type, metrics,
                    source_data
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """, 'chat', 'message', message.timestamp,
                message.content, message.session_id,
                message.actor_type, json.dumps(message.metrics),
                json.dumps(message.raw))

            # Insert into YOUR correlation tables!
            if message.references_code:
                await conn.execute("""
                    INSERT INTO code_context (
                        session_id, timestamp, file_path,
                        symbols, change_type
                    ) VALUES ($1, $2, $3, $4, $5)
                """, message.session_id, message.timestamp,
                     message.file_path, json.dumps(message.symbols),
                     message.change_type)
```

## Step 5: Test Your Correlation Queries

Finally, you can run the queries you designed:

```sql
-- Your original complex query now works!
SELECT
    cc.session_id,
    cc.file_path,
    COUNT(DISTINCT sr.symbol_name) as symbols_discussed,
    COUNT(DISTINCT fa.id) as changes_made
FROM code_context cc
LEFT JOIN symbol_references sr ON cc.session_id = sr.session_id
LEFT JOIN file_activity fa ON cc.session_id = fa.session_id
    AND cc.file_path = fa.file_path
GROUP BY cc.session_id, cc.file_path
ORDER BY symbols_discussed DESC;
```

## Step 6: Notify Other Teams

Once PostgreSQL is running, tell the other teams:

```bash
# Connection details for all teams:
POSTGRES_URL=postgresql://opsvi:opsvi_secure_password@localhost:5432/unified_context

# For TimescaleDB-specific features:
# - Use time_bucket() for time aggregations
# - Hypertables are already created for context_items and monitoring_metrics

# For JSONB queries:
# - Use ->> operator to extract JSON fields
# - Create GIN indexes on JSONB columns for performance
```

## Important Notes:

1. **Keep SQLite running** - Don't break existing dashboards
2. **Use JSONB** not TEXT for JSON data (PostgreSQL native support)
3. **Test dual-write** thoroughly before switching reads
4. **Your correlation tables** can finally be created properly!

## What You're Getting:

- ✅ All the SQL features you needed (foreign keys, cascades, proper JSON)
- ✅ TimescaleDB for time-series queries
- ✅ Your correlation design finally working
- ✅ Scalability for concurrent writes
- ✅ Foundation for the entire unified system

## Docker Alternative with pgvector:

If you need vector similarity search immediately:

```yaml
# Use pgvector-enabled image instead
services:
  postgres:
    image: ankane/pgvector:latest
    # ... rest of config same as above
```

---

**Go ahead and set this up! Once it's running, your correlation features that failed in SQLite will finally work!**
