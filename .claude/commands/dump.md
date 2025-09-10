# Dump Current Conversation

Save the current Claude Code conversation to a markdown file for future reference.

## Instructions

1. Create a timestamped markdown file in `.claude/logs/` directory
2. Include:
   - Session metadata (timestamp, working directory, git branch)
   - Full conversation history
   - Any important code changes or decisions made
   - Problems encountered and solutions
   - Next steps or todos

3. Format the output as clean markdown with:
   - Clear headers for each conversation turn
   - Code blocks properly formatted
   - Bullet points for key decisions
   - Summary section at the top

4. Save to: `.claude/logs/conversation-$(date +%Y%m%d-%H%M%S).md`

5. After saving, provide:
   - File path where conversation was saved
   - Brief summary of what was discussed
   - Any action items or follow-ups identified

This helps maintain continuity between sessions and serves as documentation for the development process.
