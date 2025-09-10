# Enhanced Chat Adapter Documentation

## Overview

The Enhanced Chat Adapter is a sophisticated ingestion component designed to process JSONL chat logs and extract meaningful entities and relationships for the unified context system. It transforms raw chat messages into structured `ContextItem` objects with rich metadata, entity extraction, and relationship mapping.

## Key Features

### 🔍 **Advanced Entity Extraction**
- **URLs**: GitHub links, web URLs, documentation links
- **Code References**: Function calls, class names, method invocations
- **File Paths**: Unix/Windows paths, relative paths
- **User Mentions**: @username patterns
- **Issue References**: GitHub issues (#123), Jira tickets (PROJ-123)
- **Commands**: Shell commands, CLI invocations
- **Email Addresses**: Full email validation
- **Timestamps**: Multiple date/time formats
- **Technology Keywords**: Programming languages, frameworks, tools

### 🔗 **Intelligent Relationship Detection**
- **Entity-based Relationships**: Messages sharing URLs, files, issues
- **Content Similarity**: Jaccard similarity for related topics
- **Actor Interactions**: Same user patterns, mentions, replies
- **Temporal Proximity**: Time-based message clustering
- **Thread Relationships**: Parent-child message hierarchies
- **Conversation Context**: Session and conversation groupings

### ⚡ **Performance Optimizations**
- **Streaming Processing**: Real-time message ingestion
- **Configurable Batch Modes**: Streaming, micro-batch, batch, bulk
- **Rate Limiting**: Configurable throughput controls
- **Memory Management**: Built-in memory limits and monitoring
- **Error Recovery**: Retry logic with exponential backoff

## Configuration

### Default Configuration
```python
config = ChatAdapter.default_config()
config.source_config.update({
    "input_format": "jsonl",
    "watch_directories": ["./chat_logs"],
    "file_patterns": ["*.jsonl"],
    "extract_entities": True,
    "entity_extraction_config": {
        "enable_url_detection": True,
        "enable_code_detection": True,
        "enable_mention_detection": True,
        "enable_issue_detection": True,
        "enable_tech_keyword_detection": True,
        "max_entities_per_type": 50,
    },
    "relationship_detection_config": {
        "enable_entity_relationships": True,
        "enable_content_similarity": True,
        "enable_actor_relationships": True,
        "similarity_threshold": 0.2,
        "entity_overlap_threshold": 0.3,
    }
})
```

### Configuration Options

#### Source Configuration (`source_config`)
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `input_format` | str | "jsonl" | Input format: jsonl, json, api, stream |
| `watch_directories` | List[str] | [] | Directories to monitor for new files |
| `file_patterns` | List[str] | ["*.jsonl"] | File patterns to match |
| `extract_entities` | bool | True | Enable entity extraction |
| `include_system_messages` | bool | True | Include system-generated messages |
| `include_metadata` | bool | True | Include message metadata |
| `conversation_timeout_minutes` | int | 60 | Conversation session timeout |

#### Entity Extraction Configuration
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enable_url_detection` | bool | True | Extract URLs and links |
| `enable_code_detection` | bool | True | Extract code references |
| `enable_mention_detection` | bool | True | Extract @mentions |
| `enable_issue_detection` | bool | True | Extract issue references |
| `enable_tech_keyword_detection` | bool | True | Extract technology keywords |
| `max_entities_per_type` | int | 50 | Maximum entities per category |

#### Relationship Detection Configuration
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enable_entity_relationships` | bool | True | Detect shared entity relationships |
| `enable_content_similarity` | bool | True | Detect content similarity |
| `enable_actor_relationships` | bool | True | Detect user interaction patterns |
| `similarity_threshold` | float | 0.2 | Minimum similarity for relationships |
| `entity_overlap_threshold` | float | 0.3 | Minimum entity overlap for relationships |

## JSONL Message Format

### Required Fields
```json
{
  "id": "msg_12345",
  "timestamp": "2024-01-15T10:00:00Z",
  "user_id": "alice",
  "content": "Message content here"
}
```

### Extended Fields
```json
{
  "id": "msg_12345",
  "timestamp": "2024-01-15T10:00:00Z",
  "user_id": "alice",
  "content": "Check out the bug report at https://github.com/repo/issues/123",
  "type": "message",
  "conversation_id": "conv_auth_discussion",
  "thread_id": "thread_001",
  "parent_id": "msg_12340",
  "author": "Alice Smith",
  "is_bot": false,
  "is_system": false,
  "edited": false,
  "attachments": [],
  "reactions": 3,
  "metadata": {
    "platform": "slack",
    "channel": "#engineering"
  }
}
```

### Field Mappings
| JSONL Field | ContextItem Field | Notes |
|-------------|------------------|-------|
| `id` | `source_id` | Primary message identifier |
| `timestamp` | `timestamp` | ISO 8601 or Unix timestamp |
| `user_id`/`author` | `actor_id` | User identifier |
| `content`/`text` | `content` | Message content |
| `conversation_id` | `session_id` | Conversation grouping |
| `type` | `metrics.message_type` | Message type classification |
| `parent_id` | `metrics.parent_message_id` | Reply relationships |
| `thread_id` | `metrics.thread_id` | Thread grouping |

## Entity Extraction Details

### URL Detection
Extracts and categorizes web links:
```python
# Examples extracted:
urls = [
    "https://github.com/user/repo/issues/123",
    "https://docs.example.com/api",
    "www.stackoverflow.com/questions/12345"
]
```

### Code Reference Detection
Identifies programming constructs:
```python
# Examples extracted:
code_references = [
    "login()",           # Function calls
    "AuthService.validate()",  # Method calls
    "class UserManager",       # Class definitions
    "user.profile.update()"    # Chained methods
]
```

### File Path Detection
Recognizes file and directory paths:
```python
# Examples extracted:
file_paths = [
    "/src/auth/login.py",
    "C:\\Users\\Alice\\Documents\\report.pdf",
    "./config/settings.json",
    "../../tests/test_auth.py"
]
```

### Issue Reference Detection
Finds ticket and issue references:
```python
# Examples extracted:
issues = [
    "#123",           # GitHub issues
    "PROJ-456",       # Jira tickets
    "issue 789",      # Natural language
    "bug 101"         # Bug references
]
```

### Technology Keyword Detection
Identifies technical terminology:
```python
tech_keywords = [
    "python", "javascript", "docker", "kubernetes",
    "aws", "postgresql", "react", "django", "redis"
]
```

## Relationship Types

### Entity-based Relationships
Messages sharing common entities:
```python
("shares_entities", target_message_id, confidence)
# confidence: 0.3-0.95 based on entity overlap
```

### Content Similarity
Messages with similar textual content:
```python
("content_similarity", target_message_id, confidence)
# confidence: 0.4-0.8 based on Jaccard similarity
```

### Actor Relationships
User interaction patterns:
```python
("same_actor", target_message_id, confidence)      # Same user
("mentions_actor", target_message_id, 0.7)         # User mention
("mentioned_by_actor", target_message_id, 0.7)     # Mentioned by user
```

### Temporal Relationships
Time-based proximity:
```python
("temporal_proximity", target_message_id, confidence)
# confidence: 0.3-1.0 based on time difference (5 min window)
```

### Structural Relationships
Chat platform structures:
```python
("replies_to", parent_message_id, 1.0)             # Direct reply
("same_thread", thread_message_id, 0.8)            # Thread member
("same_conversation", conversation_message_id, 0.6) # Conversation member
```

## Usage Examples

### Basic Usage
```python
from project_context.ingestion.adapters.chat_adapter import ChatAdapter

# Initialize with default config
config = ChatAdapter.default_config()
config.source_config["watch_directories"] = ["./chat_logs"]

adapter = ChatAdapter(config)
await adapter.initialize()

# Process messages
async for raw_message in adapter.fetch_items():
    context_item = await adapter.transform_item(raw_message)
    print(f"Processed: {context_item.title}")
    print(f"Entities: {context_item.metrics.get('extracted_entities', {})}")

await adapter.cleanup()
```

### Custom Entity Extraction
```python
# Disable certain entity types
config.source_config["entity_extraction_config"].update({
    "enable_tech_keyword_detection": False,  # Skip tech keywords
    "max_entities_per_type": 25,             # Limit entity count
})

adapter = ChatAdapter(config)
```

### Relationship Detection Tuning
```python
# Adjust relationship sensitivity
config.source_config["relationship_detection_config"].update({
    "similarity_threshold": 0.15,        # More sensitive content similarity
    "entity_overlap_threshold": 0.25,    # More sensitive entity relationships
})
```

### Integration with Pipeline
```python
from project_context.ingestion import IngestionPipeline, AdapterRegistry

# Register adapter
registry = AdapterRegistry()
registry.register_adapter("chat", ChatAdapter, config)

# Start pipeline
pipeline = IngestionPipeline(registry)
await pipeline.start()
```

## Performance Characteristics

### Throughput
- **Streaming Mode**: 1,000-5,000 messages/second
- **Batch Mode**: 10,000-50,000 messages/second
- **Memory Usage**: ~10-50MB per adapter instance
- **Entity Extraction**: ~1ms per message (avg)
- **Relationship Detection**: ~5ms per message (avg)

### Scalability Factors
- **Message Length**: Longer messages = more processing time
- **Entity Density**: More entities = higher memory usage
- **Context Window**: Larger windows = more relationship checks
- **Batch Size**: Larger batches = better throughput, higher memory

### Optimization Tips
1. **Tune Batch Sizes**: Start with 100-500 messages per batch
2. **Limit Context Windows**: Use 10-50 recent messages for relationships
3. **Configure Entity Limits**: Set `max_entities_per_type` based on needs
4. **Enable Circuit Breakers**: Prevent cascade failures
5. **Monitor Memory**: Set appropriate `max_memory_mb` limits

## Monitoring and Metrics

### Built-in Metrics
- `messages_processed_total`: Total messages ingested
- `entities_extracted_total`: Total entities found
- `relationships_detected_total`: Total relationships created
- `processing_time_seconds`: Per-message processing time
- `batch_size_current`: Current batch processing size
- `memory_usage_mb`: Current memory consumption
- `error_count_total`: Total errors encountered

### Health Checks
- **Adapter Status**: idle, running, paused, error, shutdown
- **Resource Utilization**: CPU, memory, file handles
- **Error Rates**: Success rate, retry counts, failure types
- **Performance**: Throughput, latency, queue depths

## Error Handling

### Common Error Types
1. **JSON Parse Errors**: Malformed JSONL lines
2. **Missing Required Fields**: Messages without id/timestamp
3. **File Access Errors**: Permission or path issues
4. **Memory Limit Errors**: Entity extraction memory exceeded
5. **Rate Limit Errors**: Processing rate exceeded

### Recovery Strategies
- **Automatic Retry**: Exponential backoff for transient errors
- **Circuit Breaker**: Temporary adapter shutdown on repeated failures
- **Graceful Degradation**: Continue processing with limited functionality
- **Dead Letter Queue**: Store failed messages for manual review

## Testing

### Unit Tests
Run the comprehensive validation:
```bash
python validate_chat_adapter_integration.py
```

### Integration Tests
```bash
python test_chat_adapter.py
```

### Load Testing
```bash
# Generate test data
python generate_test_chat_data.py --messages 10000

# Run performance test
python benchmark_chat_adapter.py --file test_chat.jsonl
```

## Best Practices

### Data Preparation
1. **Consistent Timestamps**: Use ISO 8601 format
2. **Unique Message IDs**: Ensure globally unique identifiers
3. **Clean Content**: Remove control characters, normalize encoding
4. **Rich Metadata**: Include conversation context when available

### Configuration
1. **Start Conservative**: Begin with default settings
2. **Monitor Performance**: Watch CPU, memory, throughput metrics
3. **Tune Gradually**: Adjust one parameter at a time
4. **Test Changes**: Validate with representative data

### Production Deployment
1. **Health Monitoring**: Implement comprehensive monitoring
2. **Graceful Shutdown**: Handle SIGTERM for clean shutdowns
3. **Resource Limits**: Set appropriate memory/CPU constraints
4. **Backup Strategy**: Maintain processed message tracking

## Troubleshooting

### Common Issues

**High Memory Usage**
- Reduce `max_entities_per_type`
- Decrease batch sizes
- Enable memory monitoring

**Low Throughput**
- Increase batch sizes
- Disable unnecessary entity types
- Reduce relationship context window

**Missing Relationships**
- Lower similarity thresholds
- Increase context window size
- Enable additional relationship types

**Processing Errors**
- Check JSONL format validation
- Verify file permissions
- Review error logs for patterns

## Future Enhancements

### Planned Features
1. **Semantic Embeddings**: Vector-based similarity instead of keyword matching
2. **ML Entity Recognition**: NLP models for custom entity types
3. **Real-time Streaming**: WebSocket support for live chat ingestion
4. **Advanced Analytics**: Sentiment analysis, topic modeling
5. **Multi-language Support**: Non-English content processing

### API Extensions
1. **Custom Entity Extractors**: Plugin system for domain-specific entities
2. **Relationship Validators**: Human-in-the-loop relationship confirmation
3. **Export Capabilities**: Extract processed data in various formats
4. **Query Interface**: GraphQL API for relationship exploration

---

**Version**: 1.0.0
**Last Updated**: January 2025
**Compatibility**: Python 3.11+, PostgreSQL 14+, TimescaleDB 2.8+
