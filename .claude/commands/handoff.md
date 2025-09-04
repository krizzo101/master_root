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
