# SDLC PHASE CHECKLIST - MANDATORY ACTIONS

## 🚨 CRITICAL: Before ANY SDLC Project

```bash
# RUN THIS FIRST - NO EXCEPTIONS
bash .claude/commands/sdlc-preflight-enhanced.sh <project-path>
```

If preflight fails, STOP. Fix issues before proceeding.

---

## ✅ Phase Checklists

### 1️⃣ DISCOVERY Phase

**FIRST ACTION:**
```python
# MANDATORY - Load phase profile
Read(".claude/agents/sdlc-discovery.md")
```

**REQUIRED TOOLS:**
```python
# 1. Check knowledge system (MANDATORY)
mcp__knowledge__knowledge_query(
    query_type="search",
    query_text="<your topic>"
)

# 2. Check existing code (MANDATORY)
mcp__resource_discovery__search_resources(
    functionality="<what you need>"
)

# 3. Research current practices (MANDATORY)
mcp__mcp_web_search__brave_web_search(
    query="<topic> best practices 2025"
)
```

**DELIVERABLE:** Create `docs/1-requirements.md`

**GATE:** Create `.sdlc/discovery-complete.json`

---

### 2️⃣ DESIGN Phase

**FIRST ACTION:**
```python
# MANDATORY - Load phase profile
Read(".claude/agents/sdlc-design.md")
```

**REQUIRED:** Architecture diagram, API specs, technology justification

**DELIVERABLE:** Create `docs/2-design.md`

**GATE:** Create `.sdlc/design-complete.json`

---

### 3️⃣ PLANNING Phase

**FIRST ACTION:**
```python
# MANDATORY - Load phase profile
Read(".claude/agents/sdlc-planning.md")
```

**REQUIRED:** Break into <2 hour tasks, create TodoWrite list

**DELIVERABLE:** Create `docs/3-planning.md`

**GATE:** Create `.sdlc/planning-complete.json`

---

### 4️⃣ DEVELOPMENT Phase

**FIRST ACTION:**
```python
# MANDATORY - Load phase profile
Read(".claude/agents/sdlc-development.md")
```

**FORBIDDEN TOOLS:**
- ❌ NO consult_suite for code generation
- ❌ NO claude_run for entire implementation
- ❌ NO bulk code generation

**REQUIRED APPROACH:**
1. Write test first (TDD)
2. Implement incrementally
3. Commit after EACH working piece
4. Run tests continuously

**GATE:** Create `.sdlc/development-complete.json`

---

### 5️⃣ TESTING Phase

**FIRST ACTION:**
```python
# MANDATORY - Load phase profile
Read(".claude/agents/sdlc-testing.md")
```

**REQUIRED:**
- Run ALL tests (not just write them)
- Show test output
- Verify >80% coverage

**GATE:** Create `.sdlc/testing-complete.json`

---

### 6️⃣ DEPLOYMENT Phase

**FIRST ACTION:**
```python
# MANDATORY - Load phase profile
Read(".claude/agents/sdlc-deployment.md")
```

**GATE:** Create `.sdlc/deployment-complete.json`

---

### 7️⃣ PRODUCTION Phase

**FIRST ACTION:**
```python
# MANDATORY - Load phase profile
Read(".claude/agents/sdlc-production.md")
```

**GATE:** Create `.sdlc/production-complete.json`

---

### 8️⃣ POSTMORTEM Phase

**FIRST ACTION:**
```python
# MANDATORY - Load phase profile (when it exists)
Read(".claude/agents/sdlc-postmortem.md")
```

**REQUIRED:**
- Analyze actual vs planned
- Identify violations
- Document lessons learned

**DELIVERABLE:** Create `docs/6-postmortem.md`

**GATE:** Create `.sdlc/postmortem-complete.json`

---

## 🛑 ENFORCEMENT RULES

1. **NO PHASE SKIPPING** - Must complete in order
2. **NO PROFILE SKIPPING** - Must load at phase start
3. **NO TOOL SKIPPING** - Must use required tools
4. **NO SHORTCUT TOOLS** - consult_suite banned in development
5. **NO BULK COMPLETION** - One task at a time
6. **NO UNTESTED CODE** - Must run tests, not just write them

## 🎯 Simple Verification

After each phase, ask yourself:
- Did I load the agent profile?
- Did I use the required tools?
- Did I create the deliverables?
- Did I create the gate file?
- Would this pass a postmortem review?

If any answer is "no" - STOP and fix it.
