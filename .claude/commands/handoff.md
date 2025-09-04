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
