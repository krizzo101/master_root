# Claude Code Command: `/requirements`

## Command Purpose
Invoke before asking Claude to design/build something. Ensures structured requirements gathering and documentation.

## Command Design

### Usage:
```
/requirements [project-name]
```

### What This Command Should Do:

1. **Display Requirements Checklist**
   - Show the requirements gathering checklist
   - Remind Claude what information needs to be captured
   - Set expectation for structured conversation

2. **Prepare Templates**
   - Create project-specific requirements document
   - Set up conversation capture structure
   - Initialize decision tracking

3. **Set Session Mode**
   - Put Claude into "requirements gathering mode"
   - Enable structured questioning prompts
   - Focus on capturing vs. implementing

### Expected Output:
```
🔍 REQUIREMENTS GATHERING MODE ACTIVATED

I'll help you define requirements for: [project-name]

Before we create any workflows or implementations, I need to gather comprehensive requirements. I'll ask structured questions to ensure orchestrator agents have complete context.

Required Information to Capture:
✅ Core request understanding (what, why, when, who)
✅ Functional requirements (features, use cases, logic)
✅ Non-functional requirements (performance, scalability)
✅ Technical constraints (must use, must avoid, integrations)
✅ Success criteria (definition of done, test scenarios)
✅ Design decisions (alternatives, trade-offs, preferences)
✅ Implementation planning (priority, phases, dependencies)

📋 I'll create a PROJECT_REQUIREMENTS_CAPTURE document as we discuss.
📝 Our conversation will be referenced for orchestrator agents.

Please describe what you'd like to build/modify:
```

### Implementation Notes:

**This command should:**
- Remind Claude to ask clarifying questions
- Structure the conversation around the checklist
- Create requirements document automatically
- Reference conversation context for agents

**Integration with workflow creation:**
- After requirements gathering complete, offer to create orchestrator workflow
- Include requirements document and conversation references in all task prompts
- Ensure agents have full context of decisions made

### Configuration Location:
Should be added to Claude Code's command system, possibly via:
- Custom command in `.claude/commands/`
- Hook in Claude Code configuration
- Integration with existing slash command system

### Alternative Approaches if Command System Not Available:
- Create an alias: `alias requirements="cat /home/opsvi/master_root/.claude/templates/REQUIREMENTS_GATHERING_CHECKLIST.md"`
- Manual trigger: User types `/requirements` and Claude recognizes it
- Document trigger: User creates `.claude/requirements-mode.flag` file before conversation

The key is creating a systematic approach where I consistently capture the right information before creating orchestrator workflows.
