# Session Handoff

**Quick session handoff for agents taking over from prior work**

## Usage
```bash
python .claude/commands/handoff.py <session-id-partial>
```

**This single command runs all required queries efficiently and provides structured output for handoff.**

## How It Works

The script analyzes the prior session across 5 key areas:
1. **Session Timeline** - Initial vs final user requests
2. **Work Progress** - What was completed, failed, or blocked
3. **Knowledge Context** - Documentation read, concepts learned
4. **Technical Dependencies** - Files modified, tools used
5. **Final State** - Where the previous agent left off

All analysis is done efficiently in a single command with structured output.

## Recommended Handoff Workflow

### Option 1: One-Command Handoff (Recommended)
```bash
# Get complete handoff summary in one command
python apps/chat-search/chat_search.py --handoff --file-filter session_id.jsonl
```

This single command provides:
- Session overview and purpose
- All user requests
- Agent accomplishments summary
- Files modified
- Tools used
- Completion status assessment

### Option 2: Detailed Analysis (When needed)
```bash
# Step 1: Quick session overview
python apps/chat-search/chat_search.py --conversation-flow --file-filter session_id.jsonl --stats-only
python apps/chat-search/chat_search.py --list-tools-used --file-filter session_id.jsonl

# Step 2: Understand context
python apps/chat-search/chat_search.py --conversation-flow --file-filter session_id.jsonl --response-chars 150

# Step 3: Search for specific issues or completions
python apps/chat-search/chat_search.py "error\|failed\|blocked" --file-filter session_id.jsonl
python apps/chat-search/chat_search.py "completed\|success\|done" --file-filter session_id.jsonl
```

### Option 3: File-Focused Analysis
```bash
# When you need detailed file information
python apps/chat-search/chat_search.py --list-files-used --file-filter session_id.jsonl --verbose
```

## After Review Protocol

1. **Summarize Understanding**:
   "Based on session [ID], I understand you want to [final objective] having already [completed work] using [learned technologies]"

2. **Identify Next Action**:
   "The previous agent was ready to: [specific next action]"

3. **Request Clarification**:
   "I need clarification on [specific gaps] before proceeding"

4. **Validate Context**:
   "Previous work was in [directory] on [branch] - is this still current?"

5. **WAIT FOR USER INSTRUCTIONS**:
   "I'm now up to speed on the prior session. Please let me know how you'd like me to proceed."

**IMPORTANT: Do NOT continue with the previous agent's planned work until the user explicitly confirms or provides new instructions.**

## Session Handoff Markers

**For Current Agent**: Use these standardized phrases so future agents can easily find key information:

### Progress Markers
- `HANDOFF_READY:` - Current task is ready for handoff
- `BLOCKED_ON:` - What is preventing progress
- `NEXT_AGENT_SHOULD:` - Explicit instructions for continuation
- `CONTEXT_SUMMARY:` - Key context for handoff

### Status Markers
- `COMPLETED_SUCCESSFULLY:` - Task finished
- `PARTIALLY_COMPLETE:` - Work in progress
- `REQUIRES_USER_INPUT:` - Waiting for user decision
- `TECHNICAL_BLOCKER:` - System/dependency issue

### Knowledge Markers
- `KEY_LEARNING:` - Important insight discovered
- `ARCHITECTURE_NOTE:` - System understanding
- `DEPENDENCY_IDENTIFIED:` - Technical requirement found
- `USER_PREFERENCE:` - User's stated preference

## Example Handoff Message
```
HANDOFF_READY: Parallel agent orchestrator test setup
CONTEXT_SUMMARY: User wants to test 2-3 parallel agents with real-time log monitoring using chat_search.py
COMPLETED_SUCCESSFULLY: Agent-orchestrator framework research, headless agent architecture understanding
NEXT_AGENT_SHOULD: Execute orchestrator test with unique session IDs, monitor log file creation
TECHNICAL_BLOCKER: None - all dependencies understood
```

## Token Efficiency Tips

- **Total queries: 5** (not more)
- **Max results: ~50** across all queries
- **Review time: <2 minutes**
- **Confirmation: 1 question to user**
- **Ready to proceed**

This protocol ensures **complete context transfer** with **minimal token usage** and **fast agent onboarding**.

## Chat Search Tool

**Location**: `/home/opsvi/master_root/apps/chat-search/chat_search.py`

**Purpose**: Search and monitor real-time `.jsonl` chat log archives in `chat_logs/` directory. These files contain live session data from active agents.

### Basic Search Usage
```bash
# Basic search
python apps/chat-search/chat_search.py "search term"

# List available log files with session counts
python apps/chat-search/chat_search.py --files

# Search specific content types
python apps/chat-search/chat_search.py "error" --type tools --limit 5
python apps/chat-search/chat_search.py "request" --type user

# Filter by date or files
python apps/chat-search/chat_search.py "parallel" --date-from 2025-01-01
python apps/chat-search/chat_search.py "orchestrator" --file-filter session_123
```

### Advanced Search with Regex Patterns

The chat_search tool supports **full regex patterns** for complex keyword searches. This is particularly useful for finding sessions with multiple related terms.

#### OR Logic (Any of the terms)
```bash
# Find sessions containing any of these terms
python apps/chat-search/chat_search.py "unified|context|project-context|orchestrator"

# With word boundaries for exact matches
python apps/chat-search/chat_search.py "\b(unified|context|project-context|orchestrator)\b"

# Combined with date filtering
python apps/chat-search/chat_search.py "unified|context|orchestrator" --date-from 2025-09-03 --date-to 2025-09-03
```

#### AND Logic (All terms must be present)
```bash
# Find sessions containing ALL terms (in same message)
python apps/chat-search/chat_search.py "(?=.*unified)(?=.*context)(?=.*orchestrator)"

# Complex AND/OR combinations
python apps/chat-search/chat_search.py "(?=.*unified)(?=.*(context|project-context))(?=.*orchestrator)"
```

#### Common Regex Patterns for Session Discovery
```bash
# Find sessions about specific topics
python apps/chat-search/chat_search.py "\b(agent|orchestrat|parallel|multi-agent)\b"

# Find sessions with specific tools or technologies
python apps/chat-search/chat_search.py "\b(docker|kubernetes|fastapi|websocket)\b"

# Find sessions with specific outcomes
python apps/chat-search/chat_search.py "\b(completed|success|failed|error|blocked)\b"

# Find sessions with specific file types or patterns
python apps/chat-search/chat_search.py "\b(\.py|\.json|\.yaml|\.md)\b"
```

#### When to Use Regex vs Simple Search

**Use Regex When:**
- **Multiple keywords**: Need to find sessions with any of several related terms
- **Complex patterns**: Looking for specific combinations of terms
- **Precise matching**: Need exact word boundaries or specific patterns
- **Session discovery**: Finding sessions by topic across multiple related terms

**Use Simple Search When:**
- **Single concept**: Looking for one specific term or phrase
- **Exact phrases**: Need to find specific quoted text
- **Quick lookup**: Simple, straightforward searches

#### Regex Search Best Practices

**1. Start Simple, Then Refine**
```bash
# Start with basic OR pattern
python apps/chat-search/chat_search.py "unified|context|orchestrator"

# Refine based on results
python apps/chat-search/chat_search.py "unified.*context|project-context.*orchestrator"
```

**2. Use Word Boundaries for Precision**
```bash
# Avoid partial matches
python apps/chat-search/chat_search.py "\bcontext\b"  # Matches "context" but not "contextual"
```

**3. Combine with Other Filters**
```bash
# Regex + date + content type
python apps/chat-search/chat_search.py "unified|context" --date-from 2025-09-01 --type user --limit 10
```

**4. Test Your Patterns**
```bash
# Test regex pattern with a small limit first
python apps/chat-search/chat_search.py "your_regex_pattern" --limit 3
```

### NEW: Session Analysis Features

#### 1. File Operations Extraction
**Purpose**: Get a complete list of all files the agent worked on during a session.

```bash
# Extract all file operations from a session
python apps/chat-search/chat_search.py --list-files-used --file-filter session_id.jsonl

# With verbose output (shows full tool input details)
python apps/chat-search/chat_search.py --list-files-used --file-filter session_id.jsonl --verbose
```

**Output**: Categorized file operations (READ, WRITE, EDIT, DELETE, LIST) with timestamps and file paths.

**When to Use**:
- **Session handoff**: Understand what files were modified
- **Impact analysis**: See scope of changes made
- **Dependency tracking**: Identify files that need attention
- **Code review**: Get complete file change history

#### 2. Conversation Flow Extraction
**Purpose**: Extract user prompts and agent response previews for quick session understanding.

```bash
# Extract conversation flow (default 200 chars per response)
python apps/chat-search/chat_search.py --conversation-flow --file-filter session_id.jsonl

# Custom response length
python apps/chat-search/chat_search.py --conversation-flow --file-filter session_id.jsonl --response-chars 300

# Statistics only (no conversation content)
python apps/chat-search/chat_search.py --conversation-flow --file-filter session_id.jsonl --stats-only
```

**Output**:
- User prompts (what was requested)
- Agent response previews (what was accomplished)
- Tool usage summaries (`[Used ToolName]`)
- Conversation statistics (turns, response lengths, etc.)

**When to Use**:
- **Session handoff**: Quick understanding of conversation flow
- **Progress review**: See what was requested vs accomplished
- **Context transfer**: Get essential conversation context without full file size
- **Token efficiency**: 97.76% size reduction on average

#### 3. Tool Usage Analysis
**Purpose**: Get a complete summary of all tools used during a session.

```bash
# Extract tool usage summary
python apps/chat-search/chat_search.py --list-tools-used --file-filter session_id.jsonl
```

**Output**:
- Tool names with usage counts
- First and last usage timestamps
- Total tool calls and unique tools used

**When to Use**:
- **Capability assessment**: Understanding what tools are available/needed
- **Approach analysis**: See what methods the previous agent used
- **Resource planning**: Identify tools that might be needed for continuation
- **Performance monitoring**: Track tool usage patterns

#### 4. Comprehensive Handoff Summary
**Purpose**: Get everything needed for a complete session handoff in one command.

```bash
# Generate complete handoff summary
python apps/chat-search/chat_search.py --handoff --file-filter session_id.jsonl

# Custom response length for accomplishments
python apps/chat-search/chat_search.py --handoff --file-filter session_id.jsonl --response-chars 200
```

**Output**:
- Session overview (turns, duration, purpose)
- User requests (what was asked for)
- Agent accomplishments (what was done)
- Files modified (scope of changes)
- Tools used (capabilities utilized)
- Session summary (totals and metrics)
- Next steps assessment (completion status)

**When to Use**:
- **Complete handoff**: Everything needed to take over a session
- **Quick assessment**: Full context in one command
- **Documentation**: Generate session summaries for records
- **Onboarding**: Perfect for new agents taking over work

### Performance Benefits

**File Operations Extraction**:
- **Instant overview** of all files touched during session
- **Categorized by operation type** (read/write/edit/delete)
- **Timestamped** for chronological understanding
- **Verbose mode** for detailed tool input analysis

**Conversation Flow Extraction**:
- **97.76% average size reduction** (10MB → 126KB typical)
- **52:1 compression ratio** on average
- **Token efficient**: Millions of tokens → tens of thousands
- **Handoff ready**: Perfect for session context transfer

**Why Use These Features**:
- **Session handoff**: Complete context in minutes, not hours
- **Impact analysis**: Understand scope of changes instantly
- **Progress tracking**: See what was requested vs accomplished
- **Token efficiency**: Analyze large sessions without token limits
- **Real-time monitoring**: Track agent activity across parallel sessions

**Note**: The chat_search tool has been updated with improved code formatting and enhanced error handling for better reliability and maintainability.

### When to Use Each Feature

#### Use `--list-files-used` When:
- **Taking over a session**: Need to understand what files were modified
- **Code review**: Want to see complete file change history
- **Impact assessment**: Understanding scope of changes before proceeding
- **Dependency analysis**: Identifying files that need attention
- **Debugging**: Finding which files were involved in a problem

#### Use `--conversation-flow` When:
- **Session handoff**: Need quick understanding of conversation context
- **Progress review**: See what was requested vs what was accomplished
- **Context transfer**: Get essential conversation without full file size
- **Token limits**: Need to analyze large sessions efficiently
- **Summary generation**: Creating session summaries for documentation

#### Use `--stats-only` When:
- **Quick assessment**: Just need conversation metrics
- **Session comparison**: Comparing activity levels across sessions
- **Resource planning**: Understanding session complexity before deep dive
- **Monitoring**: Tracking agent productivity and response patterns

#### Use `--list-tools-used` When:
- **Capability assessment**: Understanding what tools are available/needed
- **Approach analysis**: See what methods the previous agent used
- **Resource planning**: Identify tools that might be needed for continuation
- **Performance monitoring**: Track tool usage patterns

#### Use `--handoff` When:
- **Complete handoff**: Everything needed to take over a session
- **Quick assessment**: Full context in one command
- **Documentation**: Generate session summaries for records
- **Onboarding**: Perfect for new agents taking over work
- **First-time analysis**: When you need comprehensive understanding

### Integration with Existing Workflow

**Replace manual analysis** with these automated tools:
- **Before**: Read entire 10MB+ files manually
- **After**: Get 97.76% size reduction with essential context

**Enhance search-based analysis**:
- **Before**: Rely on search results alone
- **After**: Combine search with file operations and conversation flow

**Improve handoff efficiency**:
- **Before**: Hours of manual file review
- **After**: Minutes of automated analysis with complete context

## Using Chat Search Effectively

After getting up to speed, you'll likely need to search chat logs for ongoing work. Here's how to think strategically about search:

### Search Strategy Framework

**1. Define Your Intent**
- What specific information are you trying to find?
- Who would have said it? (user vs assistant)
- When in the workflow would it appear?

**2. Think Like the Speaker**
- **User requests**: How do users typically phrase requests? Consider variations in language
- **Assistant responses**: What words indicate completion, failure, or discovery?
- **Tool patterns**: What's the consistent structure in tool calls?

**3. Build Effective Queries**
- **Think conceptually first**: What would someone naturally say in this situation?
- **Consider variations**: People express the same idea in different ways
- **Start simple, then refine**: Begin with core concepts, add specificity as needed
- **Test and iterate**: Use results to guide your next search

### Core Search Dimensions

**By Message Type:**
- `--type user` - Instructions, feedback, new requests
- `--type assistant` - Work done, discoveries, plans
- `--type tools` - Tool results, errors, structured data

**By Information Type:**
- **Intentions**: What language indicates user goals?
- **Actions**: How are completed tasks typically described?
- **Problems**: What words signal issues or blockers?
- **Discoveries**: How is new understanding expressed?

**By Timing:**
- Use `--file-filter` for specific sessions
- Use `--date-from/--date-to` for time ranges
- Consider workflow sequence (early vs late session patterns)

### Query Construction Methodology

- **Define your search intent**: "I need to find..." - be specific about what you're looking for
- **Consider the speaker's mindset**: How would a user phrase a request vs how would an assistant describe completion?
- **Think about context clues**: What words or phrases would naturally appear near your target information?
- **Use progressive refinement**: Start with broad concepts, then add constraints based on what you find
- **Leverage message structure**: Users make requests, assistants report progress, tools return data - each has patterns

## ⚠️ CRITICAL: File Metadata Reliability

**IMPORTANT DISCOVERY**: Session file headers and summaries cannot be trusted and may contain completely inaccurate information.

### The Problem
- **File headers** may claim sessions are about one topic when they're actually about something completely different
- **Session summaries** in file metadata can be misleading or outdated
- **Search-based analysis** that relies on file metadata can lead to incorrect conclusions

### Real Example
- **File Header Claimed**: "Debugging Complex Web App Authentication and Performance Issues"
- **Actual Session Content**: Analysis of opsvi-llm library and OpenAI interface validation
- **Impact**: Complete mischaracterization of session purpose

### Best Practices for Reliable Analysis

**1. Always Verify File Metadata**
- Don't trust session summaries or headers
- Cross-check file metadata against actual content
- Use search tools to find the real user requests and session purpose

**2. Hybrid Analysis Approach**
- **Search tools**: Excellent for finding specific technical content quickly
- **Full file review**: Essential for understanding true context and purpose
- **Combined approach**: Most effective for comprehensive analysis

**3. Verification Protocol**
```bash
# Step 1: Check file header/summary
head -5 chat_logs/session_id.jsonl

# Step 2: Find actual user requests
python apps/chat-search/chat_search.py "user" --type user --file-filter session_id --limit 3

# Step 3: Verify session purpose matches header
python apps/chat-search/chat_search.py "analyze\|debug\|implement" --file-filter session_id --limit 5
```

**4. Red Flags to Watch For**
- Session summaries that seem generic or vague
- Headers that don't match the technical content found
- Discrepancies between file metadata and search results
- Multiple conflicting descriptions of the same session

### Impact on Handoff Process

**For Session Handoff**:
1. **Never rely solely on file headers** for understanding session purpose
2. **Always search for actual user requests** to understand true intent
3. **Verify context** by checking multiple sources within the session
4. **Flag discrepancies** when file metadata doesn't match content

**For Chat Search Usage**:
- Search tools are highly reliable for **technical content** and **specific information**
- Search tools are **unreliable for contextual understanding** when file metadata is wrong
- Always **verify session purpose** through actual content, not file headers

### Recommendation
**Trust the content, not the metadata.** Always verify file headers and summaries against actual session content before making any conclusions about session purpose or context.

## JSONL to Markdown Converter

**Location**: `/home/opsvi/master_root/apps/chat-search/jsonl_to_markdown.py`

**Purpose**: Convert JSONL chat log files into readable markdown format for documentation, sharing, and human-readable analysis.

### Basic Usage
```bash
# Convert single file
python apps/chat-search/jsonl_to_markdown.py session_123.jsonl

# Convert with custom output name
python apps/chat-search/jsonl_to_markdown.py session_123.jsonl -o session_summary.md

# Convert all JSONL files in directory
python apps/chat-search/jsonl_to_markdown.py -d chat_logs/ -o markdown_output/

# Convert with options
python apps/chat-search/jsonl_to_markdown.py session_123.jsonl --no-metadata --no-tools --max-length 1000

# Convert only user messages
python apps/chat-search/jsonl_to_markdown.py session_123.jsonl --filter user
```

### Output Features

**Structured Markdown Format**:
- **Session header** with metadata (session ID, working directory, git branch)
- **Message numbering** for easy reference
- **Role-based formatting** (User Message, Assistant Response, Tool Use/Result)
- **Timestamp formatting** in human-readable format
- **Tool call formatting** with JSON syntax highlighting
- **Content truncation** for large responses

**Content Options**:
- `--no-metadata`: Exclude timestamps and session metadata
- `--no-tools`: Exclude tool calls and results
- `--max-length N`: Truncate content longer than N characters
- `--filter TYPE`: Only include specific content types (user/assistant/tools)

### When to Use

**Documentation**:
- **Session summaries**: Create readable documentation of important sessions
- **Sharing**: Convert sessions to markdown for easy sharing and review
- **Archives**: Create human-readable archives of completed work

**Analysis**:
- **Manual review**: Read through sessions in a more natural format
- **Pattern analysis**: Look for patterns across multiple sessions
- **Training**: Use converted sessions for training or examples

**Integration**:
- **Reports**: Include session content in reports or documentation
- **Presentations**: Use markdown format for presentations or demos
- **Collaboration**: Share session content with team members

### Example Output Structure
```markdown
# Chat Session: session_123.jsonl

**Generated**: 2025-09-04 06:21:19
**Total Messages**: 10
**Session ID**: `63744462-cc0f-4210-9e6b-e319ea97b1af`
**Working Directory**: `/home/opsvi/master_root`
**Git Branch**: `fix/safety-gate-import-os`

---

## 1. Session Summary
**Summary**: Coding Project: Resolving Complex Implementation Challenge

## 2. User Message
**Timestamp**: 2025-09-03 23:15:10 UTC
<session-start-hook>Session started: 2025-09-03 19:15:10</session-start-hook>

## 3. Assistant Response
**Timestamp**: 2025-09-03 23:15:43 UTC
**Tool Used**: `mcp__thinking__metacognitivethinking`
**Tool Input**:
```json
{
  "thought": "User is running handoff command...",
  "triggerContext": "session start with handoff command"
}
```
```

### Performance Benefits

**Readability**:
- **Human-friendly format**: Easy to read and navigate
- **Structured layout**: Clear separation of messages and metadata
- **Syntax highlighting**: Tool calls and JSON properly formatted

**Flexibility**:
- **Customizable output**: Control what content to include
- **Size management**: Truncate large responses for focused analysis
- **Batch processing**: Convert multiple files at once

**Integration**:
- **Documentation ready**: Perfect for including in reports or wikis
- **Version control friendly**: Markdown format works well with git
- **Platform agnostic**: Works with any markdown viewer or editor

### Best Practices

**For Documentation**:
- Use `--no-tools` for cleaner, more readable output
- Use `--max-length 1000` to keep files manageable
- Include metadata for context and traceability

**For Analysis**:
- Use `--filter user` to focus on user requests
- Use `--filter assistant` to focus on agent responses
- Use full output for comprehensive session review

**For Sharing**:
- Use `--no-metadata` for cleaner sharing
- Use `--max-length 500` for concise summaries
- Consider converting multiple related sessions for comparison
