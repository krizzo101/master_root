# Claude Code Session Management Architecture

## Overview
A unified system for tracking, analyzing, and leveraging Claude Code sessions to provide context-aware assistance and cross-session intelligence.

## Core Components

### 1. Session Detection & Tracking
**Purpose**: Identify and track the current active session UUID at runtime

**Methods**:
- **Hook-based detection**: Capture session_id from hook inputs
- **Process inspection**: Check parent Claude process for session info
- **File monitoring**: Watch for recently modified .jsonl files
- **Environment injection**: Request Claude to set CLAUDE_SESSION_UUID env var

**Implementation**:
```python
class SessionDetector:
    def get_current_session_id():
        # 1. Check if passed via hook input
        # 2. Check environment variable
        # 3. Find most recently modified .jsonl in project dir
        # 4. Fallback: generate temporary session ID
```

### 2. Session Context Extraction
**Purpose**: Extract relevant context from current and past sessions

**Features**:
- Last N messages from current session
- Tool usage patterns
- Error patterns and resolutions
- Code changes and refactoring history
- User preferences and patterns

**Implementation**:
```python
class SessionContext:
    def get_recent_context(session_id, num_lines=200):
        # Extract and parse recent session lines
        # Filter by relevance (user prompts, assistant responses, errors)
        # Return structured context

    def get_code_changes(session_id):
        # Extract all Edit/Write tool uses
        # Build change history

    def get_error_patterns(session_id):
        # Extract error messages and resolutions
        # Identify recurring issues
```

### 3. Session Summarization
**Purpose**: Create concise, searchable summaries of sessions

**Features**:
- Auto-generate session titles based on main task
- Track key accomplishments
- Note unresolved issues
- Tag with technologies used
- Create dependency graph between sessions

**Storage Format**:
```json
{
  "session_id": "uuid",
  "project": "/home/opsvi/master_root",
  "title": "Implement prompt optimizer with bypass mechanism",
  "summary": "Added configurable modes to prompt optimizer...",
  "start_time": "2025-08-31T08:00:00Z",
  "end_time": "2025-08-31T10:30:00Z",
  "technologies": ["python", "bash", "hooks", "openai"],
  "files_modified": ["prompt_opt.py", "settings.json"],
  "key_accomplishments": [
    "Added bypass mechanism with !raw prefix",
    "Implemented configurable modes (opt-in, opt-out, always, disabled)"
  ],
  "unresolved": ["Consider ambiguity detection integration"],
  "related_sessions": ["previous-uuid"],
  "tags": ["optimization", "hooks", "configuration"]
}
```

### 4. Cross-Session Intelligence
**Purpose**: Learn from past sessions to improve future assistance

**Features**:
- Pattern recognition across sessions
- Common error database with solutions
- User preference learning
- Code style analysis
- Frequently used commands/patterns

**Implementation**:
```python
class CrossSessionIntelligence:
    def find_similar_sessions(current_context):
        # Search past sessions for similar tasks
        # Return relevant solutions and approaches

    def get_user_preferences():
        # Analyze patterns across sessions
        # Return coding style, tool preferences, etc.

    def suggest_from_history(current_task):
        # Find similar past tasks
        # Suggest approaches that worked
```

### 5. Session State Management
**Purpose**: Maintain persistent state across Claude restarts

**Features**:
- Save/restore working context
- Track long-running tasks
- Maintain todo lists across sessions
- Remember user preferences

**Storage**:
```
~/.claude/session_manager/
├── active_session.json     # Current session info
├── sessions/               # Session summaries
│   └── {uuid}.json
├── state/                  # Persistent state
│   ├── todos.json
│   ├── preferences.json
│   └── patterns.json
└── knowledge/              # Extracted knowledge
    ├── errors.json
    ├── solutions.json
    └── commands.json
```

### 6. Hook Integration
**Purpose**: Seamlessly integrate with Claude Code hooks

**Integration Points**:
- **UserPromptSubmit**: Capture session start, update context
- **Stop**: Generate session summary, save state
- **PreToolUse**: Track tool usage patterns
- **PostToolUse**: Capture results and errors
- **PreCompact**: Export session before compaction

### 7. API & CLI Interface
**Purpose**: Provide easy access to session information

**Commands**:
```bash
# CLI Commands
claude-session current      # Show current session ID and info
claude-session summary      # Generate summary of current session
claude-session list         # List recent sessions
claude-session search TERM  # Search across sessions
claude-session context      # Get context from current session
claude-session export       # Export session for sharing

# Python API
from claude_session import SessionManager

sm = SessionManager()
session_id = sm.get_current_session_id()
context = sm.get_recent_context(200)
similar = sm.find_similar_sessions("implement OAuth")
```

## Implementation Phases

### Phase 1: Basic Detection & Context (Immediate)
- Detect current session ID
- Extract last N lines from session
- Create simple context retrieval tool

### Phase 2: Summarization & Storage (Short-term)
- Auto-generate session summaries
- Store in structured format
- Add search capability

### Phase 3: Cross-Session Intelligence (Medium-term)
- Pattern recognition
- Error/solution database
- Preference learning

### Phase 4: Advanced Features (Long-term)
- AI-powered insights
- Predictive assistance
- Multi-user collaboration support

## Security Considerations
- Never expose sensitive data in summaries
- Sanitize API keys and tokens
- Respect user privacy
- Allow opt-out of tracking

## Performance Considerations
- Use incremental parsing for large sessions
- Cache frequently accessed data
- Background processing for summaries
- Efficient indexing for search

## Integration with Existing Tools
- Knowledge base (mcp__knowledge__)
- Thinking tools (mcp__thinking__)
- Task management (TodoWrite)
- Git history
- MCP servers

## Benefits
1. **Context Preservation**: Never lose important context
2. **Learning**: System improves over time
3. **Efficiency**: Reuse solutions from past sessions
4. **Debugging**: Track down when/how issues occurred
5. **Collaboration**: Share session summaries with team
6. **Documentation**: Auto-generate project history
