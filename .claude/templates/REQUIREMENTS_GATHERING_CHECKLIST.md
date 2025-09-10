# Requirements Gathering Checklist

**USE THIS WHEN:** User requests a new project/feature before creating workflows.

## Pre-Project Checklist - What I Must Capture:

### ✅ **Core Request Understanding**
- [ ] **What** exactly does the user want built/modified?
- [ ] **Why** do they need this? (business/technical driver)
- [ ] **When** do they need it? (timeline/urgency)
- [ ] **Who** will use it? (end users/stakeholders)

### ✅ **Functional Requirements**
- [ ] **Primary use cases** - What will users do with this?
- [ ] **Key features** - What capabilities must it have?
- [ ] **Input/Output** - What data goes in, what comes out?
- [ ] **Integration points** - What systems does it connect to?
- [ ] **Business logic** - What rules/workflows must it follow?

### ✅ **Non-Functional Requirements**
- [ ] **Performance** - How fast? How many concurrent users?
- [ ] **Scalability** - Expected growth over time?
- [ ] **Reliability** - Uptime expectations? Error tolerance?
- [ ] **Security** - Authentication? Data protection needs?
- [ ] **Usability** - UI/UX expectations and preferences?

### ✅ **Technical Constraints**
- [ ] **Must use** - Required technologies/frameworks/tools
- [ ] **Must avoid** - Technologies to avoid (and why)
- [ ] **Must integrate with** - Existing systems (with details)
- [ ] **Infrastructure** - Where will this run? (cloud, on-prem, etc.)
- [ ] **Data storage** - What data needs to be stored/accessed?

### ✅ **Success Criteria & Acceptance**
- [ ] **Definition of done** - How will we know it's complete?
- [ ] **Test scenarios** - How will the user verify it works?
- [ ] **Success metrics** - What measurements indicate success?
- [ ] **Acceptance process** - How will user review/approve?

### ✅ **Design Decisions & Options**
- [ ] **Alternatives considered** - What options did we discuss?
- [ ] **Trade-offs made** - What did we prioritize and why?
- [ ] **Architecture decisions** - High-level technical approach
- [ ] **UI/UX preferences** - Interface style, layout, interaction patterns

### ✅ **Context & Background**
- [ ] **Current state** - What exists now that we're building on?
- [ ] **Problem being solved** - What pain point does this address?
- [ ] **User workflow** - How does this fit into their daily work?
- [ ] **Related systems** - What other tools do they use?

### ✅ **Implementation Planning**
- [ ] **Priority order** - What should be built first?
- [ ] **Phasing strategy** - MVP vs full implementation
- [ ] **Dependencies** - What needs to be done before starting?
- [ ] **Risk factors** - What could go wrong or block progress?

---

## Questions I Should Ask If Not Clear:

### About the Problem:
- "Walk me through the current process - what's frustrating about it?"
- "What happens if we don't build this?"
- "Who else is affected by this problem?"

### About the Solution:
- "What would the ideal experience look like?"
- "Are there existing tools that do something similar?"
- "What would make you consider this a success?"

### About Constraints:
- "Are there any technical limitations I should know about?"
- "What's the timeline looking like?"
- "What's more important - speed to market or feature completeness?"

### About Integration:
- "What systems does this need to connect to?"
- "Who needs to access this and how?"
- "Are there any data sources I need to consider?"

---

## Before Creating Workflows - I Must:

1. **Fill out PROJECT_REQUIREMENTS_CAPTURE_TEMPLATE.md**
2. **Get user confirmation** on the captured requirements
3. **Store in `.claude/knowledge/docs/PROJECT_NAME_requirements.md`**
4. **Reference the requirements document** in all workflow task prompts
5. **Include conversation context** for agents to reference

## Red Flags - Don't Proceed If:
- User says "just figure it out" without providing specifics
- Requirements are vague or contradictory
- No clear success criteria defined
- Critical technical constraints unknown
- Integration requirements unclear

**Remember:** Better to over-capture requirements than have orchestrator agents work from incomplete information!
