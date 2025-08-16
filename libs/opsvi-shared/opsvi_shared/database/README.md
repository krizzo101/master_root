# Cognitive Database Interface

## Problem Solved

**Core Issue**: Agents "just CANNOT seem to get the AQL queries right" - persistent AQL syntax errors, validation failures, and database operation complexity was a major operational liability.

**Solution**: Complete abstraction of AQL complexity through agent-friendly methods and validated query templates.

## Architecture

### Core Components

1. **`core/cognitive_database.py`** - Core abstraction layer

   - Agent-friendly methods like `find_memories_about()`, `get_foundational_memories()`
   - Validated AQL query templates
   - Error handling and meaningful error messages
   - Handles null fields and schema variations gracefully

2. **`.cursor/tools/cognitive_query.py`** - Agent CLI interface

   - Direct command-line access for agents
   - JSON output format
   - Comprehensive argument parsing

3. **`mcp_server.py`** - MCP server wrapper (future enhancement)
   - Async MCP protocol support
   - Multiple interface options

## Available Methods

### Memory Operations

- `find_memories_about(topic, importance_threshold=0.7, limit=10)`
- `get_foundational_memories(min_quality=0.8)`
- `get_memories_by_type(memory_type, limit=20)`
- `get_startup_context()` - Essential startup knowledge

### Concept Operations

- `get_concepts_by_domain(domain, min_quality=0.7)`

### System Operations

- `assess_system_health()` - Collection counts and health metrics

## Usage Examples

### Command Line Interface

```bash
# Find memories about database operations
timeout 10 python .cursor/tools/cognitive_query.py find_memories_about --topic "database" --limit 5

# Get foundational memories for startup
timeout 10 python .cursor/tools/cognitive_query.py get_foundational_memories --min-quality 0.9

# Check system health
timeout 10 python .cursor/tools/cognitive_query.py assess_system_health

# Get operational memories
timeout 10 python .cursor/tools/cognitive_query.py get_memories_by_type --memory-type "operational" --limit 10
```

### MCP Server Interface

```bash
# Using the MCP server wrapper
timeout 10 python development/cognitive_interface/mcp_server.py find_memories_about topic=database limit=2
timeout 10 python development/cognitive_interface/mcp_server.py assess_system_health
```

### Python API

```python
from cognitive_database import CognitiveDatabase

db = CognitiveDatabase()

# Find memories
memories = db.find_memories_about("database", limit=5)

# Get startup context
context = db.get_startup_context()

# Check system health
health = db.assess_system_health()
```

## Benefits

### For Agents

- **No AQL Syntax Required** - Simple method calls instead of complex query construction
- **Error Prevention** - Validated query templates eliminate syntax errors
- **Meaningful Errors** - Clear error messages instead of cryptic AQL failures
- **Timeout Protection** - Use `timeout` command to prevent hanging operations

### For System

- **Preserves Cognitive Architecture** - Full access to sophisticated ArangoDB setup
- **Query Optimization** - Pre-validated and optimized query templates
- **Schema Flexibility** - Handles null fields and schema variations
- **Performance** - Efficient queries with proper indexing considerations

## Database Connection

Uses existing project configuration:

- **Host**: `http://127.0.0.1:8550`
- **Database**: `_system`
- **Authentication**: `root` / `change_me`

## Integration Pattern

This solution follows the **abstraction over migration** approach:

- Keeps sophisticated ArangoDB cognitive architecture (10+ collections, 230+ memories)
- Eliminates AQL complexity for agents through high-level interface
- Provides multiple access patterns (CLI, MCP, Python API)
- Maintains full backward compatibility

## Error Handling

- Graceful handling of null importance_score fields
- Meaningful error messages for agents
- Query validation and timeout protection
- Fallback patterns for schema variations

## Future Enhancements

1. **Full MCP Integration** - Register as proper MCP tool in Cursor
2. **Query Caching** - Cache frequent queries for performance
3. **Advanced Search** - Semantic search and vector operations
4. **Batch Operations** - Multi-operation transactions
5. **Schema Evolution** - Automatic schema adaptation

## Success Metrics

- ✅ Eliminates AQL syntax errors for agents
- ✅ Preserves full cognitive architecture functionality
- ✅ Provides multiple interface options
- ✅ Handles existing data schema gracefully
- ✅ Offers timeout protection for reliability
- ✅ Meaningful error messages for debugging

## MCP Configuration

### Adding to Cursor IDE

The cognitive database interface is now available as a proper MCP server! Add this to your `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "cognitive_database": {
      "command": "/home/opsvi/miniconda/bin/python",
      "args": [
        "/home/opsvi/agent_world/development/cognitive_interface/mcp_server.py"
      ],
      "env": {
        "PYTHONPATH": "/home/opsvi/agent_world/development/cognitive_interface/core",
        "ARANGO_URL": "http://127.0.0.1:8550",
        "ARANGO_DB": "_system",
        "ARANGO_USERNAME": "root",
        "ARANGO_PASSWORD": "change_me"
      }
    }
  }
}
```

### Available MCP Tools

Once configured, these tools will be available in Cursor:

1. **`cognitive_find_memories_about`**

   - Find memories related to a specific topic
   - Parameters: `topic` (required), `importance_threshold` (default: 0.7), `limit` (default: 10)

2. **`cognitive_get_foundational_memories`**

   - Get foundational memories for agent startup
   - Parameters: `min_quality` (default: 0.8)

3. **`cognitive_get_concepts_by_domain`**

   - Get cognitive concepts by domain
   - Parameters: `domain` (required), `min_quality` (default: 0.7)

4. **`cognitive_get_startup_context`**

   - Get complete startup context for agents
   - Parameters: none

5. **`cognitive_assess_system_health`**

   - Assess cognitive database system health
   - Parameters: none

6. **`cognitive_get_memories_by_type`**
   - Get memories filtered by type
   - Parameters: `memory_type` (required), `limit` (default: 20)

### Using in Cursor

After restarting Cursor IDE, agents can use these tools like:

```
Use cognitive_find_memories_about to search for "database" related memories
Use cognitive_get_foundational_memories to get startup knowledge
Use cognitive_assess_system_health to check system status
```

The tools will return clean JSON responses with all the cognitive architecture data without any AQL complexity!
