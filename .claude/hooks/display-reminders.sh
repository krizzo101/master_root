#!/bin/bash
# Display hook reminders to agent based on context

# Check if approaching context limit (would need Claude Code to expose this)
if [ "$CLAUDE_CONTEXT_PERCENTAGE" -gt 90 ] 2>/dev/null; then
    echo "⚠️ **CONTEXT AT $CLAUDE_CONTEXT_PERCENTAGE% - WRAP UP SOON**"
fi

echo "# AGENT REMINDERS ACTIVE

🎯 **BE BRIEF** - 1-3 sentences default
🧠 **THINK HARD** - Use full capabilities
🌐 **SEARCH FIRST** - Web/tech_docs for current info
✅ **NO LIES** - Test before claiming
🚫 **NO SHORTCUTS** - Fix real problems
⚡ **STRATEGIC EXECUTION** - Batch operations
👨‍🏫 **EXPERT ADVISOR** - Challenge bad approaches
💾 **COMMIT REGULARLY** - Save progress frequently

**Think deeply. Respond concisely. Use current sources.**"
