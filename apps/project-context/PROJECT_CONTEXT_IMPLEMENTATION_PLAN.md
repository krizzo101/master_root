# Project-Context Implementation Plan

## My Role
I am the **semantic query layer** that provides 21 MCP tools for accessing unified context data.

## Current Status
- [x] Basic FastMCP server structure
- [ ] PostgreSQL connection
- [ ] Neo4j connection
- [ ] Context Bridge integration
- [ ] Tool implementations (0/21 complete)

## Dependencies
**WAITING FOR**: Chat/intel team to set up PostgreSQL

## Implementation Phases

### Phase 1: Database Connections (After PostgreSQL is ready)
```python
# src/project_context/db/connections.py
import asyncpg
from neo4j import AsyncGraphDatabase
import redis.asyncio as redis

class DatabaseConnections:
    def __init__(self):
        self.pg_pool = None
        self.neo4j_driver = None
        self.redis_client = None

    async def connect_all(self):
        # PostgreSQL
        self.pg_pool = await asyncpg.create_pool(
            'postgresql://opsvi:opsvi_secure_password@localhost:5432/unified_context'
        )

        # Neo4j
        self.neo4j_driver = AsyncGraphDatabase.driver(
            "bolt://localhost:7687",
            auth=("neo4j", "password")
        )

        # Redis (for Context Bridge)
        self.redis_client = redis.Redis(
            host='localhost', port=6379, decode_responses=True
        )
```

### Phase 2: Core Query Builder
```python
# src/project_context/queries/builder.py
class UnifiedQueryBuilder:
    """Builds queries across PostgreSQL and Neo4j"""

    async def get_file_context(self, file_path: str):
        # Query PostgreSQL for code elements
        code_elements = await self.pg.fetch("""
            SELECT * FROM code_elements
            WHERE file_path = $1
        """, file_path)

        # Query Neo4j for relationships
        relationships = await self.neo4j.run("""
            MATCH (f:File {path: $path})-[r]-(n)
            RETURN type(r) as rel_type, labels(n) as node_type, n
        """, path=file_path)

        # Get current IDE context from Redis
        current_context = await self.redis.get(f'context:file:{file_path}')

        return self.merge_contexts(code_elements, relationships, current_context)
```

### Phase 3: Implement 21 Tools

#### Discovery Tools (4)
```python
@mcp.tool()
async def get_project_summary() -> dict:
    """Get overall project statistics and summary"""
    async with db.pg_pool.acquire() as conn:
        stats = await conn.fetchrow("""
            SELECT
                COUNT(DISTINCT file_path) as file_count,
                COUNT(DISTINCT session_id) as session_count,
                SUM((metrics->>'tokens')::int) as total_tokens,
                COUNT(DISTINCT actor_id) as developer_count
            FROM context_items
            WHERE timestamp > NOW() - INTERVAL '30 days'
        """)

        # Get language distribution
        languages = await conn.fetch("""
            SELECT
                language,
                COUNT(*) as file_count
            FROM code_elements
            GROUP BY language
        """)

        return {
            "files": stats['file_count'],
            "sessions": stats['session_count'],
            "tokens_used": stats['total_tokens'],
            "developers": stats['developer_count'],
            "languages": {l['language']: l['file_count'] for l in languages}
        }

@mcp.tool()
async def find_files(pattern: str, file_type: Optional[str] = None) -> list:
    """Search for files by pattern or criteria"""
    # Implementation...

@mcp.tool()
async def get_file_info(path: str) -> dict:
    """Detailed information about specific files"""
    # Implementation...

@mcp.tool()
async def find_symbols(
    name: str,
    symbol_type: Optional[str] = None
) -> list:
    """Search for functions, classes, variables"""
    # Implementation...
```

#### Architecture Tools (5)
```python
@mcp.tool()
async def get_dependencies() -> dict:
    """Project dependency graph"""
    # Query Neo4j for dependency relationships

@mcp.tool()
async def find_agents() -> list:
    """Discover agent architectures"""
    # Query agent_usage table

@mcp.tool()
async def get_entry_points() -> list:
    """Find CLI and main entries"""
    # Query for main functions, CLI commands

@mcp.tool()
async def get_api_endpoints() -> list:
    """List API routes"""
    # Query for FastAPI, Flask routes

@mcp.tool()
async def get_data_models() -> list:
    """Find data structures"""
    # Query for Pydantic, SQLAlchemy models
```

#### Quality Tools (3)
```python
@mcp.tool()
async def get_tests() -> dict:
    """Test file mapping"""

@mcp.tool()
async def get_config() -> dict:
    """Configuration overview"""

@mcp.tool()
async def get_quality_metrics() -> dict:
    """Code quality statistics"""
```

#### Change Tools (2)
```python
@mcp.tool()
async def get_recent_changes() -> list:
    """Recent modifications"""

@mcp.tool()
async def search_code(query: str) -> list:
    """Full-text code search"""
```

#### Analysis Tools (4)
```python
@mcp.tool()
async def get_call_graph() -> dict:
    """Function call relationships"""

@mcp.tool()
async def get_imports() -> dict:
    """Import analysis"""

@mcp.tool()
async def get_complexity() -> dict:
    """Complexity metrics"""

@mcp.tool()
async def get_documentation() -> dict:
    """Documentation coverage"""
```

#### Maintenance Tools (3)
```python
@mcp.tool()
async def get_todos() -> list:
    """TODO/FIXME items"""

@mcp.tool()
async def get_security_issues() -> list:
    """Security concerns"""

@mcp.tool()
async def validate_intelligence() -> dict:
    """Data integrity check"""
```

### Phase 4: Context Bridge Integration
```python
# Subscribe to IDE context changes
async def connect_context_bridge():
    # Subscribe to context updates
    await mcp.call_tool(
        "mcp__context_bridge__subscribe_to_context",
        {
            "subscription_data": {
                "subscriber_id": "project_context",
                "event_types": ["FILE_CHANGED", "DIAGNOSTICS_UPDATED"]
            }
        }
    )
```

### Phase 5: Caching Layer
```python
from functools import lru_cache
from aiocache import cached

class SmartCache:
    @cached(ttl=60)
    async def get_file_summary(self, file_path: str):
        # Cache file summaries for 60 seconds

    @cached(ttl=300)
    async def get_project_stats(self):
        # Cache project stats for 5 minutes
```

## Testing Plan
1. Unit tests for each tool
2. Integration tests with real PostgreSQL/Neo4j
3. Performance benchmarks (target: <100ms per query)
4. Load testing with concurrent requests

## Success Criteria
- [ ] All 21 tools implemented
- [ ] Query response < 100ms average
- [ ] Context Bridge integration working
- [ ] 90%+ test coverage
- [ ] Documentation complete

## Next Steps
1. **WAIT** for chat/intel team to confirm PostgreSQL is running
2. **TEST** connection to PostgreSQL
3. **START** implementing tools one by one
4. **INTEGRATE** with Context Bridge
5. **OPTIMIZE** with caching

---

**I am ready to implement as soon as PostgreSQL is available!**
