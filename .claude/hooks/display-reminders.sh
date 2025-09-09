#!/bin/bash
# Display hook reminders to agent based on context

# Check if approaching context limit (would need Claude Code to expose this)
if [ "$CLAUDE_CONTEXT_PERCENTAGE" -gt 90 ] 2>/dev/null; then
    echo "⚠️ **CONTEXT AT $CLAUDE_CONTEXT_PERCENTAGE% - WRAP UP SOON**"
fi

echo "# AGENT REMINDERS ACTIVE

🎯 **BE BRIEF** - 1-3 sentences default
🧠 **USE THINKING TOOL** - mcp__thinking__metacognitivethinking for complex problems
🌐 **WEB SEARCH FIRST** - Use mcp__web_search for latest technical info
✅ **NO LIES** - Test before claiming
🚫 **NO SHORTCUTS** - Fix real problems
⚡ **STRATEGIC EXECUTION** - Batch operations
👨‍🏫 **EXPERT ADVISOR** - Challenge bad approaches
💾 **COMMIT REGULARLY** - Save progress frequently
🔧 **USE MCP TOOLS** - firecrawl, knowledge, time, tech_docs
🖥️ **SHELL VIA MCP** - Use mcp__shell_exec for globs, not Bash

**Think deeply with thinking tool. Search current info. Use MCP shell for globs.**"
