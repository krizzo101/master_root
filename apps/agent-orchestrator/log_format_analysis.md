# Claude Code Session Log Format Analysis

## Overview
Claude Code stores session logs as JSONL (JSON Lines) files in the `~/.claude/projects/` directory. Each project directory contains multiple session log files with UUID-based filenames.

## File Structure

### Location Pattern
```
~/.claude/projects/{sanitized-project-path}/{session-uuid}.jsonl
```

**Example Paths:**
- `~/.claude/projects/-home-opsvi/b9d42065-ce57-427b-ba55-5811767f0bcf.jsonl`
- `~/.claude/projects/-tmp-test-analyze-job-52175846/cde4869a-37e8-4018-b73a-2cfdbe5244cb.jsonl`

### File Naming Convention
- Project directories: Sanitized paths with hyphens replacing slashes
- Log files: UUID v4 format with `.jsonl` extension

## Log Entry Types

### 1. Summary Entry
```json
{
  "type": "summary",
  "summary": "Brief description of conversation topic",
  "leafUuid": "uuid-for-this-summary"
}
```

### 2. User Message Entry
```json
{
  "parentUuid": "parent-message-uuid-or-null",
  "isSidechain": false,
  "userType": "external",
  "cwd": "/working/directory/path",
  "sessionId": "session-uuid",
  "version": "1.0.100",
  "gitBranch": "",
  "type": "user",
  "message": {
    "role": "user",
    "content": "User's message text or array of content blocks"
  },
  "uuid": "unique-message-uuid",
  "timestamp": "2025-09-02T02:12:03.935Z"
}
```

### 3. Assistant Message Entry
```json
{
  "parentUuid": "parent-message-uuid",
  "isSidechain": false,
  "userType": "external",
  "cwd": "/working/directory/path",
  "sessionId": "session-uuid",
  "version": "1.0.100",
  "gitBranch": "",
  "message": {
    "id": "msg_01VRJAXBPKZdzPTAbMk8QFJb",
    "type": "message",
    "role": "assistant",
    "model": "claude-opus-4-1-20250805",
    "content": [
      {
        "type": "text",
        "text": "Assistant's response text"
      }
    ],
    "stop_reason": null,
    "stop_sequence": null,
    "usage": {
      "input_tokens": 3,
      "cache_creation_input_tokens": 16146,
      "cache_read_input_tokens": 0,
      "cache_creation": {
        "ephemeral_5m_input_tokens": 16146,
        "ephemeral_1h_input_tokens": 0
      },
      "output_tokens": 3,
      "service_tier": "standard"
    }
  },
  "requestId": "req_011CSimFVQUVuTJjoWpLaFTf",
  "type": "assistant",
  "uuid": "unique-message-uuid",
  "timestamp": "2025-09-02T02:12:07.796Z"
}
```

### 4. Tool Use Entry
```json
{
  "parentUuid": "parent-message-uuid",
  "isSidechain": false,
  "userType": "external",
  "cwd": "/working/directory/path",
  "sessionId": "session-uuid",
  "version": "1.0.100",
  "gitBranch": "",
  "message": {
    "id": "msg_id",
    "type": "message",
    "role": "assistant",
    "model": "claude-model-version",
    "content": [
      {
        "type": "tool_use",
        "id": "toolu_unique_id",
        "name": "ToolName",
        "input": {
          "parameter1": "value1",
          "parameter2": "value2"
        }
      }
    ],
    "stop_reason": null,
    "stop_sequence": null,
    "usage": {
      // token usage details
    }
  },
  "requestId": "req_id",
  "type": "assistant",
  "uuid": "unique-message-uuid",
  "timestamp": "ISO-8601-timestamp"
}
```

### 5. Tool Result Entry
```json
{
  "parentUuid": "parent-message-uuid",
  "isSidechain": false,
  "userType": "external",
  "cwd": "/working/directory/path",
  "sessionId": "session-uuid",
  "version": "1.0.100",
  "gitBranch": "",
  "type": "user",
  "message": {
    "role": "user",
    "content": [
      {
        "type": "tool_result",
        "content": "Tool execution result or error message",
        "is_error": false,
        "tool_use_id": "toolu_unique_id"
      }
    ]
  },
  "uuid": "unique-message-uuid",
  "timestamp": "ISO-8601-timestamp",
  "toolUseResult": "Optional additional result data"
}
```

## Key Fields Explained

### Common Fields
- **uuid**: Unique identifier for each log entry
- **parentUuid**: Links entries in conversation chain
- **sessionId**: Groups all entries in a single session
- **timestamp**: ISO 8601 formatted timestamp
- **cwd**: Current working directory at time of entry
- **version**: Claude Code version
- **type**: Entry type (user, assistant, summary)

### Message-Specific Fields
- **role**: "user" or "assistant"
- **content**: Message content (text, tool_use, tool_result)
- **model**: Claude model version for assistant messages
- **usage**: Token usage statistics for assistant messages

### Tool-Related Fields
- **tool_use_id**: Unique identifier linking tool calls to results
- **name**: Tool name (Bash, Read, Write, etc.)
- **input**: Tool parameters
- **is_error**: Boolean indicating tool execution failure

## Timestamp Formats
All timestamps use ISO 8601 format with millisecond precision:
```
2025-09-02T02:12:03.935Z
```

## Session ID Patterns
Session IDs are UUID v4 format, consistent throughout a conversation:
```
cde4869a-37e8-4018-b73a-2cfdbe5244cb
```

## Sample Log Entries

### Complete User-Assistant Exchange with Tool Use
```json
// User message
{
  "parentUuid": null,
  "type": "user",
  "message": {
    "role": "user",
    "content": "List files in current directory"
  },
  "uuid": "msg-uuid-1",
  "timestamp": "2025-09-07T10:00:00.000Z"
}

// Assistant message with tool use
{
  "parentUuid": "msg-uuid-1",
  "type": "assistant",
  "message": {
    "role": "assistant",
    "content": [{
      "type": "tool_use",
      "id": "tool-id-1",
      "name": "Bash",
      "input": {"command": "ls -la"}
    }]
  },
  "uuid": "msg-uuid-2",
  "timestamp": "2025-09-07T10:00:01.000Z"
}

// Tool result
{
  "parentUuid": "msg-uuid-2",
  "type": "user",
  "message": {
    "role": "user",
    "content": [{
      "type": "tool_result",
      "tool_use_id": "tool-id-1",
      "content": "file1.txt\nfile2.md\ndir1/"
    }]
  },
  "uuid": "msg-uuid-3",
  "timestamp": "2025-09-07T10:00:02.000Z"
}
```

## Parsing Strategies

### 1. Stream Processing (Recommended for Large Files)
```python
import json

def parse_claude_log(filepath):
    with open(filepath, 'r') as f:
        for line in f:
            entry = json.loads(line)
            yield entry
```

### 2. Filter by Entry Type
```python
def get_user_messages(filepath):
    for entry in parse_claude_log(filepath):
        if entry.get('type') == 'user' and 'message' in entry:
            role = entry['message'].get('role')
            if role == 'user':
                yield entry
```

### 3. Reconstruct Conversation Thread
```python
def build_conversation_tree(entries):
    tree = {}
    for entry in entries:
        uuid = entry.get('uuid')
        parent = entry.get('parentUuid')
        
        if uuid:
            tree[uuid] = {
                'entry': entry,
                'children': []
            }
            
        if parent and parent in tree:
            tree[parent]['children'].append(uuid)
    
    return tree
```

### 4. Extract Tool Usage
```python
def extract_tool_usage(entries):
    tools = []
    for entry in entries:
        if entry.get('type') == 'assistant':
            content = entry.get('message', {}).get('content', [])
            for item in content:
                if item.get('type') == 'tool_use':
                    tools.append({
                        'tool': item.get('name'),
                        'input': item.get('input'),
                        'timestamp': entry.get('timestamp')
                    })
    return tools
```

## Edge Cases and Error Handling

### 1. Interrupted Tool Executions
```json
{
  "type": "tool_result",
  "content": "[Request interrupted by user for tool use]\nCommand aborted before execution",
  "is_error": true
}
```

### 2. Empty or Null Fields
- `gitBranch` often empty string
- `parentUuid` null for first message
- `stop_reason` and `stop_sequence` often null

### 3. Large Content Fields
- File contents in Read tool results can be very large
- May include system reminders and warnings
- Content may be truncated with ellipsis notation

### 4. Multi-part Messages
Assistant messages may contain multiple content blocks:
```json
"content": [
  {"type": "text", "text": "Let me check that..."},
  {"type": "tool_use", "name": "Read", "input": {...}},
  {"type": "text", "text": "Based on the file..."}
]
```

## Performance Considerations

1. **File Sizes**: Log files can grow very large (>1MB)
2. **Memory Usage**: Avoid loading entire files into memory
3. **Parsing Speed**: Use streaming JSON parsing for large files
4. **Index Building**: Consider building indices for frequently accessed data

## Security Notes

- Logs may contain sensitive file paths and content
- Tool inputs/outputs may include credentials or API keys
- Consider sanitizing logs before sharing or archiving
- File paths in project directories are already sanitized

## Version Compatibility

Current version observed: `1.0.100`
- Version field appears consistent across entries
- Future versions may introduce schema changes
- Consider version checking when parsing logs

## Best Practices

1. **Always use streaming parsing** for production code
2. **Handle malformed JSON lines** gracefully
3. **Validate UUID formats** when building relationships
4. **Cache parsed data** for repeated analysis
5. **Implement retry logic** for incomplete logs
6. **Use timestamp indices** for time-based queries
7. **Sanitize sensitive data** before external storage