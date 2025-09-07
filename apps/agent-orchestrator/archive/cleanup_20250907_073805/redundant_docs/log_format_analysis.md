# Claude Code Log Format Analysis

## Overview
Claude Code session logs are stored as JSONL (JSON Lines) files in `~/.claude/projects/` with project-specific subdirectories. Each line represents a single log entry in JSON format.

## Directory Structure
```
~/.claude/projects/
├── -home-opsvi-master-root/           # Main project directory
│   ├── *.jsonl                         # Session log files (UUID-named)
├── -home-opsvi-master-root-apps-agent-orchestrator/
├── -home-opsvi-master-root-libs-opsvi-mcp/
└── ... (other project directories)
```

### File Naming Convention
- Format: `{session-uuid}.jsonl`
- Example: `3cf2e5de-b4a8-4ded-a0f2-8466bea1548f.jsonl`

## Log Entry Types

### Distribution (from 155,096 analyzed entries)
- **assistant**: 83,306 entries (53.7%) - Claude's responses
- **user**: 62,391 entries (40.2%) - User messages and tool results
- **system**: 8,287 entries (5.3%) - System events and metadata
- **summary**: 1,112 entries (0.7%) - Session summaries

## JSON Structure

### Common Fields (All Entry Types)
```json
{
  "type": "user|assistant|system|summary",
  "sessionId": "UUID string",
  "timestamp": "ISO 8601 format",
  "uuid": "Unique entry UUID",
  "parentUuid": "Parent entry UUID or null",
  "isSidechain": boolean,
  "userType": "external",
  "cwd": "Current working directory path",
  "version": "Claude Code version (e.g., 1.0.108)",
  "gitBranch": "Current git branch name"
}
```

### Entry Type Specifics

#### 1. User Entry
```json
{
  "type": "user",
  "message": {
    "role": "user",
    "content": "User's message or <session-start-hook>..."
  },
  "toolUseResult": [  // Optional: Present when responding to tool use
    {
      "type": "text",
      "text": "Tool execution result"
    }
  ]
}
```

#### 2. Assistant Entry
```json
{
  "type": "assistant",
  "message": {
    "id": "msg_...",
    "type": "message",
    "role": "assistant",
    "model": "claude-sonnet-4-20250514",
    "content": [
      {
        "type": "text",
        "text": "Assistant's response"
      },
      // OR
      {
        "type": "tool_use",
        "id": "toolu_...",
        "name": "tool_name",
        "input": { /* tool parameters */ }
      }
    ],
    "stop_reason": null,
    "stop_sequence": null,
    "usage": {
      "input_tokens": number,
      "output_tokens": number,
      "cache_creation_input_tokens": number,
      "cache_read_input_tokens": number,
      "cache_creation": {
        "ephemeral_5m_input_tokens": number,
        "ephemeral_1h_input_tokens": number
      },
      "service_tier": "standard"
    }
  },
  "requestId": "req_..."
}
```

#### 3. System Entry
```json
{
  "type": "system",
  "content": "System message with ANSI escape codes",
  "isMeta": false,
  "level": "info|warning|error",
  "toolUseID": "Tool use identifier"
}
```

#### 4. Summary Entry
```json
{
  "type": "summary",
  "summary": "Brief description of conversation topic",
  "leafUuid": "Reference UUID"
}
```

## Timestamp Formats
- **Format**: ISO 8601 with milliseconds
- **Example**: `"2025-09-07T08:28:02.124Z"`
- **Timezone**: Always UTC (Z suffix)
- **Precision**: Millisecond accuracy

## Session ID Patterns
- **Format**: Standard UUID v4
- **Example**: `3cf2e5de-b4a8-4ded-a0f2-8466bea1548f`
- **Consistency**: Same sessionId throughout a conversation
- **File Naming**: Session ID is used as the filename

## Tool Use Patterns

### Tool Call (in Assistant Entry)
```json
"content": [{
  "type": "tool_use",
  "id": "toolu_01PAtsqqD8WgbVaKWhwbSQBE",
  "name": "mcp__time__current_time",
  "input": {
    "format": "YYYY-MM-DD HH:mm:ss"
  }
}]
```

### Tool Result (in User Entry)
```json
"toolUseResult": [{
  "type": "text",
  "text": "Current UTC time is 2025-09-07 08:28:25..."
}]
```

## UUID Relationships
- **parentUuid**: Links entries in conversation threads
- **uuid**: Unique identifier for each entry
- **leafUuid**: Used in summary entries for reference
- **Hierarchy**: Forms a tree structure of conversation flow

## Edge Cases and Special Patterns

### 1. Session Start Hook
```json
"content": "<session-start-hook>Session started: 2025-09-07 04:28:02</session-start-hook>"
```

### 2. ANSI Escape Codes in System Messages
- System content may include formatting: `\\u001b[1m...\\u001b[22m`
- Used for bold, colors, and other terminal formatting

### 3. Multi-line User Input
- Long user messages are preserved with newlines
- Content field can be very large (thousands of characters)

### 4. Tool Chaining
- Multiple tool uses in single assistant message
- Tool results referenced by tool_use_id

## Parsing Strategies

### 1. Streaming Parse
```python
import json
from pathlib import Path

def parse_jsonl(file_path):
    with open(file_path, 'r') as f:
        for line in f:
            if line.strip():
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    # Skip malformed lines
                    continue
```

### 2. Entry Type Filtering
```python
def filter_by_type(entries, entry_type):
    return [e for e in entries if e.get('type') == entry_type]
```

### 3. Chronological Sorting
```python
from datetime import datetime

def sort_by_timestamp(entries):
    return sorted(entries,
                  key=lambda x: datetime.fromisoformat(
                      x['timestamp'].replace('Z', '+00:00')))
```

### 4. Session Reconstruction
```python
def build_conversation_tree(entries):
    tree = {}
    for entry in entries:
        parent = entry.get('parentUuid')
        uuid = entry.get('uuid')
        if parent:
            tree.setdefault(parent, []).append(entry)
    return tree
```

## Error Handling Recommendations

### 1. Malformed JSON
- Use try/except around json.loads()
- Log or skip bad lines rather than crashing
- Consider partial line buffering for incomplete writes

### 2. Missing Fields
- Use .get() method with defaults
- Validate required fields before processing
- Handle null/None values gracefully

### 3. Large Files
- Use streaming/iterative parsing
- Implement file position tracking for resume capability
- Consider memory limits with large sessions

### 4. Concurrent Access
- Handle file locks appropriately
- Implement retry logic for temporary access issues
- Use file modification time to detect changes

## Performance Considerations

### 1. File Discovery
- Cache directory listings
- Use file modification times to skip unchanged files
- Implement efficient glob patterns

### 2. Real-time Monitoring
- Use inotify/kqueue for file change detection
- Implement tail-like behavior with seek()
- Buffer reads for efficiency

### 3. Memory Management
- Process entries in streams, not bulk loads
- Implement sliding window for recent entries
- Clear processed data regularly

## Sample Log Entries

### Typical Conversation Flow
```jsonl
{"type":"system","content":"SessionStart...","timestamp":"2025-09-07T08:28:02.124Z",...}
{"type":"user","message":{"content":"<session-start-hook>..."},...}
{"type":"user","message":{"content":"Create a Python script"},...}
{"type":"assistant","message":{"content":[{"type":"text","text":"I'll help you..."}]},...}
{"type":"assistant","message":{"content":[{"type":"tool_use","name":"Write",...}]},...}
{"type":"user","toolUseResult":[{"type":"text","text":"File created"}],...}
```

## Implementation Notes

1. **File Rotation**: New session = new file
2. **Active Detection**: Check file modification time < 2 minutes
3. **Swarm Identification**: Multiple files in same directory modified simultaneously
4. **Color Coding**: Use last 8 chars of UUID for agent identification
5. **Truncation**: Consider message length limits for display
