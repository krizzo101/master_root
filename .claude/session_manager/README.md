# Claude Code Session Manager

A comprehensive session management system for Claude Code that tracks, analyzes, and leverages session data for improved context and intelligence.

## Installation

The session manager is already installed in `.claude/session_manager/`. To use it globally, add to your PATH:

```bash
export PATH="$HOME/.claude/session_manager:$PATH"
```

## Quick Start

```bash
# Check current session
claude-session current

# Get session summary
claude-session summary

# View recent context
claude-session recent 100

# Export full context
claude-session export my-session.json
```

## Features

### 1. Session Detection
Automatically detects the current Claude session using multiple methods:
- Hook input data
- Environment variables
- State files
- Recent file analysis
- Synthetic ID generation

### 2. Context Extraction
Extract valuable context from sessions:
- Recent conversations
- Tool usage patterns
- Code changes
- Error patterns
- Session summaries

### 3. CLI Interface
Simple command-line interface for all operations:
```bash
claude-session [command] [options]
```

## Commands

| Command | Description |
|---------|-------------|
| `current` | Show current session ID |
| `info [ID]` | Get detailed session information |
| `path [ID]` | Get path to session file |
| `recent [N]` | Show last N entries |
| `conversation [N]` | Show conversation pairs |
| `tools` | Show tool usage statistics |
| `changes` | Show recent code changes |
| `errors` | Show errors and resolutions |
| `summary` | Show session summary |
| `export [FILE]` | Export full context |

## Python API

```python
from session_detector import SessionDetector
from session_context import SessionContext

# Detect current session
detector = SessionDetector()
session_id, method, confidence = detector.get_current_session_id()

# Extract context
context = SessionContext(session_id)
recent = context.get_recent_context(200)
summary = context.get_summary_context()
```

## Hook Integration

Add to `.claude/settings.json` to track sessions:

```json
{
  "hooks": {
    "UserPromptSubmit": {
      "handler": {
        "type": "command",
        "command": "/home/opsvi/master_root/.claude/hooks/session_tracker.py"
      }
    }
  }
}
```

## Use Cases

### 1. Get Context for Prompt Optimization
```bash
# Get last 200 lines of context
claude-session recent 200 --json | \
  jq '.[] | select(.type == "user") | .content'
```

### 2. Analyze Tool Usage
```bash
# See which tools are used most
claude-session tools --json | jq 'keys'
```

### 3. Track Code Changes
```bash
# See recent file modifications
claude-session changes --json | \
  jq '.[] | .file' | sort -u
```

### 4. Debug Errors
```bash
# Find recent errors and resolutions
claude-session errors
```

### 5. Export for Analysis
```bash
# Export full session context
claude-session export session-$(date +%Y%m%d).json
```

## Environment Variables

- `CLAUDE_SESSION_UUID`: Override session detection
- `CLAUDE_PROJECT_ROOT`: Project root directory
- `DEBUG`: Enable debug logging

## Architecture

The session manager consists of:

1. **SessionDetector**: Finds and tracks current session
2. **SessionContext**: Extracts context from session logs
3. **CLI Interface**: User-friendly command-line tool
4. **Hook Integration**: Captures session info in real-time

## Limitations

- Session files are only available for active Claude Code sessions
- Synthetic IDs are generated when actual session can't be detected
- Large sessions may take time to process
- Session logs are project-specific

## Future Enhancements

- [ ] Cross-session intelligence
- [ ] AI-powered summarization
- [ ] Pattern recognition
- [ ] Collaborative features
- [ ] Real-time monitoring
- [ ] Session replay
- [ ] Knowledge extraction

## Troubleshooting

### No session detected
- Ensure you're running within Claude Code
- Check if session files exist in `~/.claude/projects/`
- Try setting `CLAUDE_SESSION_UUID` manually

### Empty context
- Session may be new with no entries
- Check if session file exists and is readable
- Verify project directory matches

### Performance issues
- Reduce number of lines processed with `--lines`
- Use filters to extract specific types
- Export and process offline for large sessions
