# Ultimate Research-Driven Autonomous Coder

## The Complete Bootstrap Instruction

This single instruction to Claude Code creates a fully autonomous, research-driven coding system:

```python
ULTIMATE_AUTONOMOUS_INSTRUCTION = """
Build a complete RESEARCH-DRIVEN autonomous coding system that:

## CORE REQUIREMENT: Always Research First
Before implementing ANYTHING, research current (2024-2025) information about:
- Package versions (check npm, PyPI, crates.io, etc.)
- Best practices and patterns
- Security vulnerabilities and fixes
- Performance optimizations
- Alternative technologies
- Breaking changes and migrations

## System Architecture

### 1. Research Engine (research_engine.py)
Create a research system that:
- Uses web search to find current documentation
- Checks package registries for latest versions
- Reads GitHub repos for recent updates
- Analyzes Stack Overflow for current solutions
- Searches for security advisories
- Compiles findings into actionable intelligence

Methods needed:
- research_technology(name) -> TechReport
- get_latest_versions(packages) -> VersionMap
- find_best_practices(domain, year=2025) -> Practices
- check_security_advisories(tech_stack) -> Advisories
- compare_alternatives(requirement) -> Comparison

### 2. Intelligent Planner (planner.py)
Based on research, create plans that:
- Use only current, verified package versions
- Follow 2024-2025 best practices
- Avoid deprecated approaches
- Include fallback strategies
- Account for breaking changes

Methods:
- create_plan(goal, research_findings) -> Plan
- validate_tech_stack(choices) -> Validation
- adjust_for_compatibility(plan) -> UpdatedPlan

### 3. Autonomous Executor (executor.py)
Implementation engine that:
- Generates code using researched information
- Validates against current standards
- Tests with modern frameworks
- Handles errors with current solutions
- Continuously researches when stuck

Methods:
- execute_with_research(task) -> Result
- validate_implementation(code) -> TestResults
- fix_with_current_knowledge(error) -> Solution

### 4. Knowledge Base (knowledge_base.py)
Persistent learning system that:
- Caches research findings with expiry dates
- Tracks technology version history
- Stores successful patterns
- Maintains error solutions
- Updates as technologies evolve

Structure:
```python
{
    "technologies": {
        "react": {
            "current_version": "18.3.1",
            "checked_date": "2025-01-15",
            "breaking_changes": [...],
            "best_practices": [...],
            "common_issues": [...]
        }
    },
    "patterns": {
        "auth_implementation": {
            "current_approach": "...",
            "deprecated": [...],
            "security_notes": [...]
        }
    }
}
```

### 5. State Manager (state_manager.py)
Track everything including:
- Research performed and findings
- Technology decisions and rationale
- Implementation progress
- Test results with versions used
- Errors and solutions applied

### 6. Validator (validator.py)
Validation using current standards:
- Security scanning with 2025 rules
- Performance testing with current benchmarks
- Accessibility checking (WCAG 3.0)
- SEO validation for current algorithms
- Cross-browser testing for current versions

### 7. Main Orchestrator (autonomous_coder.py)
The main entry point that:
```python
class AutonomousCoder:
    async def build(self, goal: str) -> CompletedProject:
        # Phase 1: Research everything
        research = await self.research_engine.comprehensive_research(goal)
        
        # Phase 2: Make informed decisions
        tech_stack = await self.planner.decide_stack(research)
        
        # Phase 3: Verify versions exist
        verified = await self.research_engine.verify_availability(tech_stack)
        
        # Phase 4: Create researched plan
        plan = await self.planner.create_plan(goal, verified)
        
        # Phase 5: Execute with continuous research
        while not self.is_complete():
            task = self.state.get_next_task()
            
            # Research specific implementation details
            impl_research = await self.research_engine.research_implementation(task)
            
            # Execute with current knowledge
            result = await self.executor.execute_with_research(task, impl_research)
            
            # Validate with current standards
            validation = await self.validator.validate_current(result)
            
            if not validation.passed:
                # Research solutions to problems
                solutions = await self.research_engine.find_solutions(validation.errors)
                await self.executor.apply_fixes(solutions)
            
            self.state.update(result)
        
        return self.finalize_project()
```

## Implementation Requirements

### Research Integration Points
Every component must research before acting:

1. **Before choosing technologies**: Research what's current and recommended
2. **Before writing code**: Research current syntax and patterns
3. **Before installing packages**: Verify versions and compatibility
4. **Before testing**: Research current testing approaches
5. **Before deploying**: Research current deployment methods

### MCP Tool Usage
Use these MCP tools for research:
- Web search for documentation and articles
- GitHub search for code examples
- Package registry queries for versions
- Stack Overflow for solutions
- Security databases for vulnerabilities

### Example Research Queries
```python
# Before using React
research_queries = [
    "React latest version 2025",
    "React 18 vs 19 breaking changes",
    "React Server Components best practices 2025",
    "React performance optimization 2025",
    "React security vulnerabilities CVE 2025"
]

# Before choosing a database
research_queries = [
    "PostgreSQL vs MySQL 2025 comparison",
    "Database scaling best practices 2025",
    "SQL injection prevention 2025",
    "Database connection pooling Node.js 2025"
]
```

### Continuous Learning
The system must:
- Update its knowledge daily
- Expire cached research after 7 days
- Re-research when encountering errors
- Learn from each build
- Share knowledge between sessions

## Testing the System

Create test scenarios that require current knowledge:

1. **Test 1**: Build an app using React 19 features (requires researching latest React)
2. **Test 2**: Implement OAuth 2.1 (requires researching current OAuth standards)
3. **Test 3**: Deploy to Vercel Edge Functions (requires current deployment knowledge)
4. **Test 4**: Use Bun instead of Node.js (requires researching Bun compatibility)

## Success Criteria

The system is complete when it can:
1. ✅ Research current technologies before using them
2. ✅ Choose correct, current package versions
3. ✅ Implement using 2024-2025 best practices
4. ✅ Avoid deprecated or outdated approaches
5. ✅ Fix errors using current solutions
6. ✅ Generate documentation with current information
7. ✅ Deploy using current methods
8. ✅ Handle any software request with up-to-date implementation

## Final Notes

CRITICAL: This system must NEVER rely on training data for technology information.
ALWAYS research current information before making any technology decision or writing any code.

The research phase is NOT optional - it's the foundation of every action.

Build this system, test it thoroughly, and ensure it can build modern applications
using only current, researched information - not outdated training data.
"""

# The execution is simple - give Claude this instruction
async def bootstrap():
    from mcp_tools import claude_run
    
    result = await claude_run(
        task=ULTIMATE_AUTONOMOUS_INSTRUCTION,
        permissionMode="bypassPermissions"
    )
    
    return result
```

## Key Differences from Basic Autonomous Systems

### Traditional Autonomous Coder:
```
Goal → Plan → Build → Test → Deploy
```

### Research-Driven Autonomous Coder:
```
Goal → RESEARCH → Informed Plan → RESEARCH → Build with Current Info → RESEARCH → Test with Modern Tools → RESEARCH → Deploy with Current Methods
```

## Why This Matters

1. **Package Versions**: Claude's training data has outdated versions
2. **Best Practices**: Standards change rapidly (weekly in web dev)
3. **Security**: New vulnerabilities discovered daily
4. **Performance**: Optimization techniques evolve constantly
5. **Compatibility**: Breaking changes between versions
6. **New Features**: Technologies add features after training cutoff

## Example: Building a React App

### Without Research (Using Training Data):
```javascript
// Might use React 17 patterns
import React from 'react';
class Component extends React.Component { // Outdated
    componentDidMount() { // Deprecated patterns
        // ...
    }
}
```

### With Research (Current Knowledge):
```javascript
// Uses React 19 with Server Components
import { use } from 'react'; // Latest React 19 feature
export default async function Component() {
    const data = use(fetchData()); // Current pattern
    return <div>{data}</div>;
}
```

## The Bootstrap Command

Just run:
```bash
claude --dangerously-skip-permissions -p "$(cat ULTIMATE_AUTONOMOUS.md)"
```

Or via MCP:
```python
await claude_run(task=ULTIMATE_AUTONOMOUS_INSTRUCTION, permissionMode="bypassPermissions")
```

Claude Code will:
1. Build the complete research-driven system
2. Test it with real examples requiring current knowledge
3. Document everything with up-to-date information
4. Create a production-ready autonomous coder that always uses current tech

## Success Metrics

The system should be able to:
- Correctly identify that React is at v18.3.x (not v16 or v17 from training)
- Know about Next.js 14/15 App Router (not just Pages Router)
- Use Vite instead of Create React App (CRA is deprecated)
- Implement current TypeScript 5.x features
- Use modern CSS (Container Queries, :has(), etc.)
- Deploy to modern platforms (Vercel Edge, Cloudflare Workers)
- Implement current security headers and CSP policies
- Use current testing approaches (Playwright, Vitest)

This ensures the autonomous coder builds modern, production-ready applications using current technologies, not outdated training knowledge.