# 🧠 AUTONOMOUS KNOWLEDGE SYSTEM

## CRITICAL: THIS IS MANDATORY FOR ALL AGENTS

This document describes the knowledge learning system that ALL agents MUST use.
The system is stored in Neo4j and enables persistent learning across sessions.

## 🚨 MANDATORY STARTUP PROTOCOL

**EVERY agent/session MUST execute these steps IMMEDIATELY after time check:**

```python
# 1. Check knowledge system availability
from apps.knowledge_system.claude_knowledge_retrieval import ClaudeKnowledgeRetrieval

# 2. Query for relevant context knowledge
context_knowledge = mcp__db__read_neo4j_cypher(
    query="MATCH (k:Knowledge) WHERE k.confidence_score > 0.8 RETURN k LIMIT 10",
    params={}
)

# 3. Load high-confidence patterns into working memory
# This gives you immediate access to proven solutions
```

## 📋 WHEN TO RETRIEVE KNOWLEDGE (MANDATORY)

### ALWAYS query knowledge BEFORE:
- **Solving any error** → Check ERROR_SOLUTION type
- **Writing new code** → Check CODE_PATTERN type  
- **Starting a workflow** → Check WORKFLOW type
- **Using a tool** → Check TOOL_USAGE type
- **Making architecture decisions** → Check CONTEXT_PATTERN type

### Query Example:
```python
# Before fixing an ImportError
from apps.knowledge_system.claude_knowledge_retrieval import ClaudeKnowledgeRetrieval

query_info = ClaudeKnowledgeRetrieval.get_error_solution("ImportError: No module named X")
result = mcp__db__read_neo4j_cypher(query=query_info['query'], params=query_info['params'])

if result and result[0]['confidence'] > 0.7:
    # Apply the known solution
    apply_solution(result[0]['solution'])
else:
    # Solve from scratch and store new knowledge
    solution = solve_problem()
    store_new_knowledge(solution)
```

## 📝 WHEN TO STORE KNOWLEDGE (MANDATORY)

### ALWAYS store knowledge AFTER:

1. **Successfully solving an error** (ERROR_SOLUTION)
   ```python
   store_query = ClaudeKnowledgeRetrieval.store_new_learning(
       knowledge_type='ERROR_SOLUTION',
       content=f'Fixed {error_type} by {solution_description}',
       context={'error_type': error_type, 'solution': solution},
       tags=['error', language, tool]
   )
   mcp__db__write_neo4j_cypher(query=store_query['query'], params=store_query['params'])
   ```

2. **Creating reusable code** (CODE_PATTERN)
   - Any function/class used 3+ times
   - Any pattern that solves a common problem
   - Any optimization that improves performance

3. **Completing a multi-step task** (WORKFLOW)
   - Any sequence of 3+ steps that achieved a goal
   - Any process that will likely be repeated

4. **Discovering tool usage patterns** (TOOL_USAGE)
   - Successful tool combinations
   - Optimal parameters for tools
   - Tool sequences that work well

5. **Learning user preferences** (USER_PREFERENCE)
   - Coding style preferences
   - Workflow preferences
   - Communication preferences

6. **Finding context-specific approaches** (CONTEXT_PATTERN)
   - What works in production vs development
   - Language-specific best practices
   - Project-specific conventions

## 🔄 KNOWLEDGE LIFECYCLE

### Pattern Recognition Triggers:
- **Repetition**: Same action performed 3+ times → Create pattern
- **Success**: Solution works with >80% success rate → Increase confidence
- **Failure**: Solution fails 3+ times → Decrease confidence or deprecate
- **Evolution**: Better solution found → Create relationship, update confidence

### Automatic Learning Events:
```python
# After EVERY successful action
if action_succeeded:
    # Check if this is a new pattern
    if is_new_pattern(action):
        store_as_knowledge(action)
    # Or update existing knowledge
    elif existing_knowledge := find_similar_knowledge(action):
        update_knowledge_success(existing_knowledge.id)

# After EVERY failure
if action_failed:
    if existing_knowledge := find_related_knowledge(action):
        update_knowledge_failure(existing_knowledge.id, failure_reason)
```

## 🗂️ KNOWLEDGE TYPES REFERENCE

| Type | Description | When to Store | When to Query |
|------|-------------|---------------|---------------|
| ERROR_SOLUTION | Fixes for specific errors | After fixing any error | Before attempting error fix |
| CODE_PATTERN | Reusable code solutions | After creating useful pattern | Before writing similar code |
| WORKFLOW | Multi-step processes | After completing complex task | Before starting similar task |
| USER_PREFERENCE | How user likes things | After user feedback/correction | Before making style decisions |
| CONTEXT_PATTERN | Situational approaches | After finding what works where | When entering similar context |
| TOOL_USAGE | Effective tool use | After successful tool usage | Before using tools |

## 🔍 KNOWLEDGE DISCOVERY QUERIES

### Find all available knowledge types:
```cypher
MATCH (k:Knowledge)
RETURN DISTINCT k.knowledge_type, count(*) as count
ORDER BY count DESC
```

### Get high-confidence knowledge:
```cypher
MATCH (k:Knowledge)
WHERE k.confidence_score > 0.8
RETURN k
ORDER BY k.confidence_score DESC, k.usage_count DESC
```

### Find related knowledge:
```cypher
MATCH (k1:Knowledge {knowledge_id: $current_id})-[r:RELATED_TO|SIMILAR_TO|DERIVED_FROM]-(k2:Knowledge)
RETURN k2
```

## 📊 SUCCESS METRICS

Track these to ensure the system is working:
- **Query Rate**: Should query knowledge 5+ times per session
- **Store Rate**: Should store 1+ new knowledge per session
- **Hit Rate**: Should find relevant knowledge >60% of queries
- **Success Rate**: Applied knowledge should succeed >70%

## 🚀 IMPLEMENTATION CHECKLIST

For every agent/session:
- [ ] Import knowledge retrieval module at start
- [ ] Query for context knowledge on startup
- [ ] Check knowledge before solving problems
- [ ] Store knowledge after successes
- [ ] Update confidence after applications
- [ ] Create relationships between related knowledge
- [ ] Review knowledge metrics at session end

## 🔗 INTEGRATION POINTS

### With CLAUDE.md:
- Knowledge system is MANDATORY (same level as git commits)
- Runs AFTER time check, BEFORE main work
- Automatic storage triggers on success patterns

### With Error Patterns:
- `.proj-intel/error_patterns.json` feeds into ERROR_SOLUTION knowledge
- Bidirectional sync between systems

### With Project Intelligence:
- Use project analysis to identify CODE_PATTERNS
- Extract workflows from agent activities

### With MCP Tools:
- `mcp__db__read_neo4j_cypher` for retrieval
- `mcp__db__write_neo4j_cypher` for storage
- `mcp__db__get_neo4j_schema` for discovery

## 📚 KNOWLEDGE SYSTEM FILES

- `/apps/knowledge_system/knowledge_learning_neo4j.py` - Core implementation
- `/apps/knowledge_system/claude_knowledge_retrieval.py` - Query interface
- `/.proj-intel/autonomous_learning_system.py` - Extended learning system
- `/.proj-intel/KNOWLEDGE_SYSTEM.md` - This file (discovery point)

## ⚠️ CRITICAL REMINDERS

1. **NEVER skip knowledge queries** - Even if you think you know the answer
2. **ALWAYS store successful patterns** - Others need to learn from them
3. **UPDATE confidence after use** - This improves the system
4. **CREATE relationships** - Connect related knowledge
5. **SHARE across agents** - Knowledge is universal, not agent-specific

## 🔄 VERSIONING

**Current Version**: 1.0.0
**Schema Version**: 1.0.0
**Compatibility**: All agents using Neo4j MCP tools

Future versions MUST maintain backward compatibility with this schema.

---

**Remember**: The knowledge system is not optional. It's how we learn and improve.
Every interaction should contribute to or benefit from collective knowledge.