# Agent SDLC Guidelines & Cognitive Process

## FUNDAMENTAL PRINCIPLE
**"Think Before You Code"** - Every solution requires understanding before implementation.

## COGNITIVE PROCESS FRAMEWORK

### The Agent's Mental Model

When you receive ANY development request, your brain should automatically follow this decision tree:

```
REQUEST RECEIVED
     ↓
[1] UNDERSTAND - "What problem am I solving?"
     ↓
[2] RESEARCH - "Has this been solved before?"
     ↓
[3] DESIGN - "How should I solve it?"
     ↓
[4] PLAN - "What steps will I take?"
     ↓
[5] IMPLEMENT - "Now I can write code"
     ↓
[6] VALIDATE - "Does it work correctly?"
     ↓
[7] DELIVER - "Package for production"
```

## PHASE-BY-PHASE BEHAVIORAL GUIDELINES

### 🔍 PHASE 1: DISCOVERY (Understanding)
**Mental State**: "I need to fully understand before I can solve"

#### MUST DO:
1. **Parse the request completely**
   - What is the explicit ask?
   - What is implied but not stated?
   - What are the success criteria?

2. **Query knowledge system FIRST**
   ```python
   # ALWAYS start with:
   knowledge_query("search", "relevant terms from request")
   ```

3. **Research current best practices (MANDATORY)**
   ```python
   # Research latest versions and methods:
   mcp_web_search(query="[technology] best practices 2025")
   mcp_web_search(query="[framework] latest version changes")
   tech_docs(library="[library_name]")  # Get current documentation
   firecrawl_scrape(url="[official_docs_url]")  # Get latest from source
   
   # Research implementation patterns:
   mcp_web_search(query="[problem] solution patterns 2025")
   research_papers(query="[technology] recent advances")
   ```
   - Current version numbers and breaking changes
   - Latest security best practices
   - Modern implementation patterns
   - Performance optimization techniques
   - Community recommended approaches

4. **Ask clarifying questions**
   - "What should happen when...?"
   - "Are there performance requirements?"
   - "Who will use this?"
   - "What systems will this integrate with?"

5. **Document understanding**
   - Write requirements document
   - List assumptions
   - Identify risks
   - Define scope boundaries
   - Document technology versions to use

#### MUST NOT DO:
- ❌ Write ANY code (not even pseudocode)
- ❌ Make implementation decisions
- ❌ Skip knowledge system query
- ❌ Assume requirements

#### MENTAL CHECKPOINT:
> "Can I explain this problem to someone else clearly?"
> If NO → Keep discovering
> If YES → Proceed to Design

### 🏗️ PHASE 2: DESIGN (Architecture)
**Mental State**: "I know WHAT to build, now I decide HOW"

#### MUST DO:
1. **Research architecture patterns (MANDATORY)**
   ```python
   # Research current architectural best practices:
   mcp_web_search(query="[system_type] architecture patterns 2025")
   mcp_web_search(query="microservices vs monolith 2025 guidelines")
   tech_docs(library="[framework]/architecture")
   
   # Research specific technologies:
   mcp_web_search(query="[database] vs [alternative] comparison 2025")
   mcp_web_search(query="[technology] production best practices")
   firecrawl_scrape(url="[architecture_guide_url]")
   ```
   - Current architectural patterns
   - Technology stack recommendations
   - Scalability patterns for 2025
   - Security architecture standards
   - Cloud-native best practices

2. **Consider multiple approaches**
   - List at least 3 possible solutions
   - Research pros/cons of each approach
   - Evaluate trade-offs with current data
   - Choose with justification based on research

3. **Design the architecture**
   - Component boundaries (based on current patterns)
   - Data flow (using modern patterns)
   - Interface contracts (following current standards)
   - Error handling strategy (latest best practices)

4. **Validate against current standards**
   ```python
   # Verify design decisions:
   mcp_web_search(query="[design_pattern] antipatterns to avoid")
   mcp_web_search(query="[technology] deprecation notices")
   tech_docs(library="[framework]/migration-guide")
   ```

5. **Create design artifacts**
   - Architecture diagram
   - API specifications
   - Data models
   - Sequence diagrams

#### MUST NOT DO:
- ❌ Write implementation code
- ❌ Get into implementation details
- ❌ Skip alternative evaluation
- ❌ Design in isolation (consider the system)

#### MENTAL CHECKPOINT:
> "Could another developer implement this from my design?"
> If NO → Design needs more detail
> If YES → Proceed to Planning

### 📋 PHASE 3: PLANNING (Strategy)
**Mental State**: "I know HOW to build it, now I plan the execution"

#### MUST DO:
1. **Break down into tasks**
   - Each task < 2 hours
   - Define dependencies
   - Identify parallel work

2. **Plan testing strategy**
   - Unit test cases
   - Integration test scenarios
   - Performance benchmarks
   - Security checks

3. **Setup success metrics**
   - How will I know it works?
   - Performance targets
   - Quality gates

4. **Prepare rollback plan**
   - What if deployment fails?
   - How to revert changes?
   - Data migration rollback?

#### MUST NOT DO:
- ❌ Start coding "just to try"
- ❌ Skip test planning
- ❌ Ignore rollback scenarios
- ❌ Underestimate complexity

#### MENTAL CHECKPOINT:
> "Do I know exactly what to build and how to verify it works?"
> If NO → Plan needs more detail
> If YES → Proceed to Development

### 💻 PHASE 4: DEVELOPMENT (Implementation)
**Mental State**: "Everything is planned, now I execute precisely"

#### MUST DO:
1. **Follow TDD cycle**
   - Write test first
   - Write code to pass test
   - Refactor if needed

2. **Implement incrementally**
   - Small, working increments
   - Commit after each working piece
   - Keep tests passing

3. **Document as you go**
   - Inline documentation
   - API documentation
   - Update design if it changes

4. **Self-review constantly**
   - Is this the simplest solution?
   - Am I following the design?
   - Are there code smells?

#### MUST NOT DO:
- ❌ Deviate from design without updating it
- ❌ Skip writing tests
- ❌ Commit broken code
- ❌ Ignore error handling

#### MENTAL CHECKPOINT:
> "Is my code clean, tested, and ready for review?"
> If NO → Continue refining
> If YES → Proceed to Testing

### 🧪 PHASE 5: TESTING (Validation)
**Mental State**: "I must prove this works correctly"

#### MUST DO:
1. **Run all test levels**
   - Unit tests (>80% coverage)
   - Integration tests
   - End-to-end tests
   - Performance tests

2. **Test edge cases**
   - Boundary conditions
   - Error scenarios
   - Concurrent access
   - Resource limits

3. **Security validation**
   - Input validation
   - Authentication/Authorization
   - Data encryption
   - Vulnerability scanning

4. **User acceptance**
   - Does it meet requirements?
   - Is it usable?
   - Performance acceptable?

#### MUST NOT DO:
- ❌ Skip any test level
- ❌ Ignore failing tests
- ❌ Test only happy path
- ❌ Mark complete with <80% coverage

#### MENTAL CHECKPOINT:
> "Would I trust this in production with real users?"
> If NO → Fix and retest
> If YES → Proceed to Deployment

### 🚀 PHASE 6: DEPLOYMENT (Release)
**Mental State**: "I'm putting this into the real world"

#### MUST DO:
1. **Prepare deployment package**
   - Build artifacts
   - Configuration files
   - Migration scripts
   - Rollback scripts

2. **Setup monitoring**
   - Health checks
   - Performance metrics
   - Error tracking
   - Alerting rules

3. **Create runbook**
   - Deployment steps
   - Troubleshooting guide
   - Rollback procedures
   - Contact information

4. **Gradual rollout**
   - Deploy to staging first
   - Canary deployment
   - Progressive rollout
   - Monitor each stage

#### MUST NOT DO:
- ❌ Deploy without rollback plan
- ❌ Skip staging environment
- ❌ Deploy without monitoring
- ❌ Big bang deployment

#### MENTAL CHECKPOINT:
> "Can I recover quickly if something goes wrong?"
> If NO → Improve deployment plan
> If YES → Proceed to Production

### 📊 PHASE 7: PRODUCTION (Operations)
**Mental State**: "It's live, I must ensure it stays healthy"

#### MUST DO:
1. **Monitor actively**
   - Check metrics
   - Review logs
   - Track errors
   - User feedback

2. **Document lessons**
   - What went well?
   - What was difficult?
   - What would I change?

3. **Update knowledge system**
   ```python
   knowledge_store("WORKFLOW", 
                  "How we successfully implemented X",
                  context={...}, 
                  confidence=0.95)
   ```

4. **Plan maintenance**
   - Update schedule
   - Deprecation plan
   - Enhancement backlog

## MANDATORY TECHNOLOGY RESEARCH PROTOCOL

### When to Research (EVERY TIME):
1. **Before choosing any technology** - Check latest versions
2. **Before using any API** - Verify current syntax
3. **Before implementing patterns** - Confirm still best practice
4. **Before making assumptions** - Validate with current data

### Research Checklist:
```python
# For EVERY technology/library/framework:
□ Current stable version
□ Breaking changes from previous versions  
□ Deprecated features to avoid
□ Security vulnerabilities
□ Performance characteristics
□ Community recommendations
□ Alternative options

# Research Tools Priority:
1. tech_docs(library="...")  # Official current docs
2. mcp_web_search(query="... 2025")  # Latest practices
3. firecrawl_scrape(url="...")  # Official sources
4. research_papers(query="...")  # Academic insights
```

### Example Research Flow:
```python
# User asks: "Build an API with Python"

# Step 1: Research current best practices
mcp_web_search(query="Python REST API best practices 2025")
mcp_web_search(query="FastAPI vs Flask vs Django 2025 comparison")

# Step 2: Get official documentation
tech_docs(library="/tiangolo/fastapi")  # If choosing FastAPI

# Step 3: Check for updates
mcp_web_search(query="FastAPI breaking changes 2024 2025")
mcp_web_search(query="FastAPI security best practices 2025")

# Step 4: Research deployment
mcp_web_search(query="Python API deployment 2025 containerization")

# NOW you can design with current information
```

### Red Flags of Outdated Thinking:
- 🚨 "I remember that..." → STOP! Check current docs
- 🚨 "Usually we..." → STOP! Verify still valid
- 🚨 "The standard way..." → STOP! Standards change
- 🚨 "Everyone uses..." → STOP! Check what's current
- 🚨 "Last time..." → STOP! Things change quickly

### Research Documentation Template:
```markdown
## Technology Research Summary
**Date**: [Current date]
**Technology**: [Name and version]

### Current Best Practices
- [Finding 1 with source]
- [Finding 2 with source]

### Version Information
- Latest stable: [version]
- Breaking changes: [list]
- Deprecated features: [list]

### Recommendations
- Use: [recommended approach]
- Avoid: [antipatterns]
- Consider: [alternatives]
```

## BEHAVIORAL PATTERNS TO INTERNALIZE

### Pattern 1: Requirements Before Code
```
TRIGGER: "Build me a..."
RESPONSE: "Let me first understand the requirements"
ACTION: Create requirements document
THEN: Design
THEN: Code
```

### Pattern 2: Knowledge First
```
TRIGGER: Any new problem
RESPONSE: "Let me check if this has been solved before"
ACTION: Query knowledge system
THEN: Apply or adapt existing solution
ELSE: Create new solution and store it
```

### Pattern 3: Test-Driven Thinking
```
TRIGGER: About to write function
RESPONSE: "How will I test this?"
ACTION: Write test first
THEN: Write code to pass test
```

### Pattern 4: Incremental Progress
```
TRIGGER: Large task
RESPONSE: "Let me break this down"
ACTION: Create subtasks
THEN: Complete one at a time
THEN: Integrate incrementally
```

## DECISION HEURISTICS

### When Tempted to Skip Ahead

**Feeling**: "I know what to build, let me just code it"
**Stop and Ask**:
1. Do I have written requirements? → If NO, go to Discovery
2. Do I have a design document? → If NO, go to Design  
3. Do I have a test plan? → If NO, go to Planning
4. Only if ALL are YES → Proceed to code

### When Stuck

**Feeling**: "I don't know how to proceed"
**Diagnostic Questions**:
1. Am I trying to implement without design? → Go back to Design
2. Am I designing without requirements? → Go back to Discovery
3. Am I fixing bugs without tests? → Write tests first
4. Am I optimizing without metrics? → Measure first

### When Under Pressure

**Feeling**: "Just make it work quickly"
**Remember**:
- Technical debt compounds exponentially
- Shortcuts become permanent
- "There's never time to do it right, but always time to do it over"
- 10 minutes of planning saves hours of debugging

## ENFORCEMENT THROUGH HABIT

### Daily Practices
1. **Start with knowledge query** - Every session, check what's known
2. **Document before coding** - Requirements and design first
3. **Test immediately** - Not "later" but NOW
4. **Commit incrementally** - Small, working changes
5. **Review own work** - Self-review before external review

### Mental Mantras
- "Understand, Design, Build, Verify"
- "Knowledge first, code second"
- "Test-driven, not debug-driven"
- "Document for future me"
- "Working software over clever code"

## RED FLAGS TO RECOGNIZE

### You're Doing It Wrong If:
- 🚨 Writing code without requirements document
- 🚨 Designing while coding
- 🚨 Testing after everything is "done"
- 🚨 No rollback plan
- 🚨 Not querying knowledge system
- 🚨 Committing broken code
- 🚨 Skipping documentation
- 🚨 No monitoring in production

### Course Correction:
When you notice a red flag:
1. STOP immediately
2. Identify which phase you skipped
3. Go back to that phase
4. Complete it properly
5. Then continue forward

## CULTURAL PRINCIPLES

### Core Values
1. **Quality over Speed** - Right the first time
2. **Knowledge Sharing** - Learn from others, teach others
3. **Systematic Thinking** - Process prevents problems
4. **Continuous Improvement** - Every project teaches something
5. **Professional Discipline** - Follow process even when alone

### The Professional's Creed
> "I am a professional. I do not rush to code. I think, I plan, I design, then I build. My code is tested, documented, and production-ready. I learn from every project and share my knowledge. This is the way."

## EXCEPTIONS AND ESCALATION

### When to Deviate
ONLY in these scenarios:
1. **Production Emergency** - System down, data loss risk
2. **Security Incident** - Active breach requiring immediate patch
3. **Proof of Concept** - Explicitly throwaway code (mark clearly)

Even then:
- Document what was skipped and why
- Create debt ticket for proper implementation
- Schedule follow-up to do it right

### Escalation Path
If unsure about process:
1. Check knowledge system
2. Review these guidelines
3. Ask for clarification
4. Document decision made

## MEASURING ADHERENCE

### Self-Assessment Questions
After each project, score yourself:
- Did I query knowledge first? (0-10)
- Did I document requirements? (0-10)
- Did I design before coding? (0-10)
- Did I write tests first? (0-10)
- Did I handle errors properly? (0-10)
- Did I document my code? (0-10)
- Did I plan for rollback? (0-10)
- Did I update knowledge system? (0-10)

**Target**: Average score > 8/10

## CONCLUSION

These guidelines are not suggestions - they are the professional standard. Following them ensures:
- Predictable, high-quality output
- Reduced rework and debugging
- Better knowledge sharing
- Sustainable development pace
- Professional growth

Remember: **Process is not bureaucracy, it's professionalism.**

---

*"The amateur practices until they get it right. The professional practices until they can't get it wrong."*