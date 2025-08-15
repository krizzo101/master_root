# SDLC Quick Reference Card

## 🎯 THE GOLDEN RULE
**"No Code Without Requirements, No Design Without Understanding"**

## 📋 PHASE CHECKLIST

### □ DISCOVERY
- [ ] Query knowledge system FIRST
- [ ] Research current best practices
- [ ] Check latest technology versions
- [ ] Document requirements
- [ ] Identify risks
- [ ] Define success criteria
- **MUST**: Use web_search, tech_docs, firecrawl
- **CAN**: Write .md, .txt, .json files
- **CANNOT**: Write code files

### □ DESIGN  
- [ ] Research architecture patterns
- [ ] Compare technology options
- [ ] Architecture diagram
- [ ] Interface specifications
- [ ] Data models
- [ ] Consider alternatives
- **MUST**: Verify patterns still current
- **CAN**: Create design docs
- **CANNOT**: Write implementation code

### □ PLANNING
- [ ] Break into tasks (<2hr each)
- [ ] Test strategy
- [ ] Rollback plan
- [ ] Success metrics
- **CAN**: Create test specs
- **CANNOT**: Start coding

### □ DEVELOPMENT
- [ ] Test first (TDD)
- [ ] Incremental commits
- [ ] Document as you go
- [ ] Self-review
- **CAN**: Write ALL file types
- **MUST**: Follow design

### □ TESTING
- [ ] Unit tests (>80% coverage)
- [ ] Integration tests
- [ ] Edge cases
- [ ] Performance tests
- **MUST**: All tests pass
- **CANNOT**: Skip test levels

### □ DEPLOYMENT
- [ ] Deployment package
- [ ] Monitoring setup
- [ ] Runbook created
- [ ] Rollback tested
- **MUST**: Have rollback plan
- **CANNOT**: Deploy without monitoring

### □ PRODUCTION
- [ ] Monitor metrics
- [ ] Document lessons
- [ ] Update knowledge system
- [ ] Plan maintenance

## 🚨 STOP SIGNALS

STOP if you're about to:
- Write code without requirements ⛔
- Skip knowledge system query ⛔
- Design while coding ⛔
- Commit broken code ⛔
- Deploy without tests ⛔

## 💡 DECISION FLOWCHART

```
Got request to build something?
         ↓
    Simple (<3 files)?
    ↙          ↘
   NO          YES
   ↓            ↓
Create      Informal
Project     Process
   ↓            ↓
Strict      Still need:
SDLC        - Requirements
Process     - Design sketch
            - Tests
```

## 🔍 RESEARCH TOOLS (MANDATORY USE)

```python
# Web Search - Latest practices
mcp_web_search(query="technology best practices 2025")
mcp_web_search(query="framework vs alternative 2025")

# Technical Documentation - Current versions
tech_docs(library="/org/project")  # Get latest docs
tech_docs(library="/fastapi/fastapi")  # Example

# Web Scraping - Official sources
firecrawl_scrape(url="https://docs.python.org/3/whatsnew/")
firecrawl_scrape(url="https://github.com/org/repo/releases")

# Research Papers - Academic insights
research_papers(query="distributed systems patterns")

# ALWAYS CHECK:
- Current stable version
- Breaking changes
- Deprecated features
- Security advisories
- Performance benchmarks
```

## 🔧 SDLC TOOL COMMANDS

```python
# Create project
sdlc_tool("create_project", 
    project_name="Name",
    description="Description")

# Check before file operation  
sdlc_tool("check_path",
    file_path="/path/to/file",
    operation="write")

# Validate phase
sdlc_tool("validate_phase",
    project_id="xxx")

# Move to next phase
sdlc_tool("proceed_phase",
    project_id="xxx")

# Record knowledge query
sdlc_tool("record_knowledge",
    project_id="xxx",
    query="search terms")
```

## 📝 TEMPLATES

### Requirements Template
```markdown
## Functional Requirements
- What it must do
- User stories
- Acceptance criteria

## Non-Functional Requirements  
- Performance needs
- Security requirements
- Scalability needs

## Success Criteria
- Measurable outcomes
```

### Commit Message Template
```
[phase]: Brief description

- What was done
- Why it was done
- Any important notes

Phase: [discovery|design|planning|development|testing|deployment]
```

## 🎓 PROFESSIONAL MANTRAS

1. **"Understand → Design → Build → Verify"**
2. **"Knowledge first, code second"**
3. **"Test-driven, not debug-driven"**
4. **"Working software over clever code"**
5. **"Process prevents problems"**

## ⚡ EMERGENCY OVERRIDES

ONLY override process for:
1. Production system down
2. Active security breach
3. Data loss imminent

Even then:
- Document what was skipped
- Create debt ticket
- Fix properly ASAP

## 📊 SELF-SCORING

Rate yourself after each task (0-10):
- [ ] Queried knowledge first?
- [ ] Documented requirements?
- [ ] Designed before coding?
- [ ] Wrote tests first?
- [ ] Handled errors properly?
- [ ] Documented code?
- [ ] Planned rollback?
- [ ] Updated knowledge system?

**Target: Average >8/10**

---

**Remember:** This is not bureaucracy, it's professionalism.