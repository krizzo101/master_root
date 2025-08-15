# Knowledge Learning System

A comprehensive knowledge learning system for autonomous AI agents using Neo4j as the primary knowledge store, combining vector embeddings with graph traversal for hybrid retrieval.

## Features

- **Hybrid Retrieval**: Combines vector similarity search with graph traversal
- **Self-Learning**: Automatically learns from agent interactions
- **Multi-Model Embeddings**: Supports OpenAI and local embedding models
- **Pattern Recognition**: Discovers workflows, error resolutions, and usage patterns
- **Context-Aware**: Adapts to user preferences and conversation context
- **Token Optimized**: Minimizes token usage during retrieval
- **Scalable**: Built on Neo4j for handling millions of knowledge nodes

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      AI Agent Conversation                        │
└────────────────────────┬───────────────────────────────────────┘
                         │
                    ┌────▼────┐
                    │ Context │
                    │ Manager │
                    └────┬────┘
                         │
          ┌──────────────┼──────────────┐
          │              │              │
     ┌────▼────┐   ┌────▼────┐   ┌────▼────┐
     │Knowledge│   │ Pattern │   │Learning │
     │Retrieval│   │ Matcher │   │  Loop   │
     └────┬────┘   └────┬────┘   └────┬────┘
          │              │              │
          └──────────────┼──────────────┘
                         │
                 ┌───────▼───────┐
                 │   Neo4j DB     │
                 │  (Knowledge    │
                 │   Graph)       │
                 └───────────────┘
```

## Components

### 1. **Embedding Service** (`src/embedding_service.py`)
- Generates vector embeddings for knowledge content
- Supports OpenAI API and local Sentence Transformers
- Implements caching and dimension reduction
- Handles batch processing for efficiency

### 2. **Neo4j Knowledge Store** (`src/neo4j_knowledge_store.py`)
- Manages knowledge persistence in Neo4j
- Implements specialized stores for different knowledge types
- Handles relationship management
- Provides metrics and statistics

### 3. **Hybrid Retrieval** (`src/hybrid_retrieval.py`)
- Combines vector similarity with graph traversal
- Context-aware ranking and filtering
- Adaptive learning from feedback
- Caching for performance

### 4. **Self-Learning Loop** (`src/self_learning_loop.py`)
- Captures events from agent interactions
- Discovers patterns in actions and outcomes
- Creates new knowledge automatically
- Identifies knowledge gaps

### 5. **Agent Integration** (`src/agent_integration.py`)
- Seamless integration with AI agents
- Session management
- Event tracking
- MCP tool compatibility

## Knowledge Types

### CodePattern
```python
{
    "type": "CodePattern",
    "language": "Python",
    "pattern_type": "singleton",
    "content": "...",
    "embedding": [...],
    "confidence_score": 0.9
}
```

### ErrorResolution
```python
{
    "type": "ErrorResolution",
    "error_type": "ImportError",
    "error_signature": "...",
    "resolution": "...",
    "success_rate": 0.85
}
```

### Workflow
```python
{
    "type": "Workflow",
    "workflow_name": "git_workflow",
    "steps": [...],
    "tools_used": ["git"],
    "complexity_score": 0.3
}
```

### UserPreference
```python
{
    "type": "UserPreference",
    "user_id": "user123",
    "preference_category": "coding_style",
    "preference_value": {...}
}
```

## Installation

### Prerequisites

1. **Neo4j Database** (running in Docker):
```bash
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  -e NEO4J_PLUGINS='["apoc"]' \
  neo4j:latest
```

2. **Python Dependencies**:
```bash
pip install openai sentence-transformers numpy
```

3. **Environment Variables**:
```bash
export OPENAI_API_KEY="your-api-key"  # Optional, for OpenAI embeddings
```

### Initialize Database

```bash
python init_neo4j.py
```

This will:
- Create all required indexes
- Set up constraints
- Load initial categories and technologies
- Create sample knowledge entries

## Usage

### As a Standalone System

```python
from knowledge_system import KnowledgeLearningSystem, KnowledgeSystemConfig

# Configure system
config = KnowledgeSystemConfig(
    neo4j_uri="bolt://localhost:7687",
    neo4j_user="neo4j",
    neo4j_password="password",
    openai_api_key="your-key",  # Optional
    embedding_model="text-embedding-3-small",
    min_confidence=0.7
)

# Initialize system
system = KnowledgeLearningSystem(config)
await system.initialize()

# Query knowledge
result = await system.query(
    query="How to fix ImportError in Python?",
    context={"language": "Python"},
    max_results=5
)

# Learn from interaction
await system.learn_from_interaction(
    interaction_type="tool_usage",
    data={
        "tool": "pytest",
        "parameters": {"file": "test.py"},
        "result": "All tests passed",
        "success": True
    }
)

# Get statistics
stats = await system.get_statistics()
```

### Integration with AI Agents

```python
from src.agent_integration import KnowledgeIntegration

# Initialize integration
integration = KnowledgeIntegration(
    knowledge_store=store,
    retriever=retriever,
    learner=learner,
    embedding_service=embedder
)

# Start session
context = await integration.initialize_session(
    session_id="session123",
    user_id="user456"
)

# Query during conversation
results = await integration.query_knowledge(
    session_id="session123",
    query="How to implement singleton pattern?",
    max_results=3
)

# Report tool usage
await integration.report_tool_usage(
    session_id="session123",
    tool_name="git",
    parameters={"command": "commit"},
    result="Success",
    success=True
)

# Report and resolve errors
resolution = await integration.report_error(
    session_id="session123",
    error_type="ImportError",
    error_message="No module named 'numpy'"
)

# End session and trigger learning
analysis = await integration.end_session("session123")
```

### Using MCP Tools

The system integrates with MCP tools for Neo4j access:

```python
# Query knowledge via MCP
results = await mcp_tool.query(
    query="Python async patterns",
    max_results=5,
    knowledge_type="CodePattern"
)

# Apply knowledge
content = await mcp_tool.apply(knowledge_id="abc123")

# Report error for resolution
resolution = await mcp_tool.report_error(
    error_type="SyntaxError",
    error_message="unexpected EOF while parsing"
)
```

## CLI Interface

```bash
# Initialize the system
python knowledge_system.py init

# Query knowledge
python knowledge_system.py query --query "How to use Docker?" --max-results 5

# Get system statistics
python knowledge_system.py stats

# Run optimization
python knowledge_system.py optimize
```

## Performance Optimization

### Caching
- Embedding cache reduces API calls
- Retrieval cache speeds up repeated queries
- Configurable TTL for cache entries

### Batch Processing
- Batch embedding generation
- Batch Neo4j operations
- Parallel search strategies

### Token Optimization
- Returns summaries instead of full content
- Progressive context loading
- Smart truncation strategies

## Monitoring

### Metrics Available
- Total knowledge entries
- Average confidence scores
- Success rates by type
- Query performance
- Learning patterns discovered
- Session analytics

### Knowledge Gaps Detection
- Unresolved errors
- Low success rate tools
- Empty context patterns
- Missing knowledge areas

## Best Practices

1. **Regular Optimization**: Run `optimize()` periodically to merge duplicates and deprecate old knowledge
2. **Session Management**: Always use sessions for better context tracking
3. **Feedback Loop**: Report outcomes (success/failure) for continuous learning
4. **Context Provision**: Provide rich context for better retrieval
5. **Batch Operations**: Use batch methods for multiple operations

## Advanced Features

### Adaptive Retrieval
The system learns from feedback to adjust retrieval weights:
```python
results, feedback_id = await retriever.retrieve_with_feedback(query, context)
# After user interaction
retriever.record_feedback(
    feedback_id,
    useful_results=["id1", "id2"],
    not_useful_results=["id3"]
)
```

### Pattern Discovery
Automatically discovers patterns from repeated actions:
- Workflow sequences
- Error resolution patterns
- Tool usage combinations
- Context triggers

### Knowledge Evolution
- Automatic confidence adjustment based on usage
- Relationship strength updates
- Duplicate merging
- Deprecation of outdated knowledge

## Troubleshooting

### Common Issues

1. **Neo4j Connection Failed**
   - Ensure Neo4j is running: `docker ps`
   - Check credentials in config
   - Verify ports 7474 and 7687 are accessible

2. **Embedding Generation Slow**
   - Use local model for faster embeddings
   - Enable caching
   - Reduce embedding dimension

3. **High Token Usage**
   - Adjust `max_results` parameter
   - Use summaries instead of full content
   - Enable token optimization

## Future Enhancements

- [ ] Graph neural networks for improved retrieval
- [ ] Multi-language support
- [ ] Distributed knowledge federation
- [ ] Real-time knowledge streaming
- [ ] Advanced visualization dashboard
- [ ] Knowledge versioning and rollback
- [ ] Automated knowledge validation
- [ ] Cross-session learning patterns

## License

This project is part of the master_root AI agent system.

## Support

For issues and questions, please refer to the main project documentation or create an issue in the repository.