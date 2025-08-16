# Agent Invocation Standards

## Primary Agent Strategy: Claude Code First

### Executive Summary
**Claude Code is the primary agent for 95% of all agent tasks in the AI Factory.**

After extensive evaluation of specialized agents vs Claude Code, we've determined that Claude Code's versatility, context handling, and comprehensive capabilities make it the optimal choice for most development tasks.

## Core Principle: Default to Claude Code

### The Claude Code Agent Advantage
```python
# Instead of specialized agents:
await opsvi_agents.research_agent.execute(task)
await opsvi_agents.coding_agent.execute(task)
await opsvi_agents.review_agent.execute(task)

# Use Claude Code for everything:
await claude_code.execute(
    task="Research, design, implement, test, and deploy the solution",
    mode="comprehensive"
)
```

### Why Claude Code?
1. **Comprehensive Capabilities**: Can handle research, coding, testing, deployment in one session
2. **Context Persistence**: Maintains full context throughout the entire task
3. **Tool Integration**: Has access to all MCP tools and project intelligence
4. **Proven Reliability**: Battle-tested on complex multi-step tasks
5. **Reduced Complexity**: One agent interface instead of orchestrating multiple agents

## When to Use Claude Code (95% of cases)

### Default Use Cases
- **Feature Development**: Complete feature implementation from requirements to deployment
- **Bug Fixing**: Debug, fix, test, and verify in one session
- **Code Review**: Analyze code quality, suggest improvements, implement fixes
- **Documentation**: Generate and maintain comprehensive documentation
- **Testing**: Write tests, run them, fix issues, achieve coverage goals
- **Refactoring**: Analyze, plan, and execute code improvements
- **Research**: Technology research, best practices, implementation strategies
- **Integration**: API integration, service connections, data pipelines
- **Deployment**: Build, package, deploy applications
- **Maintenance**: Updates, dependency management, security patches

### Claude Code Invocation Pattern
```python
from opsvi_mcp.tools import claude_code_invoker

async def build_feature(requirements: str):
    """Standard pattern for invoking Claude Code"""
    
    # Single Claude Code invocation handles everything
    result = await claude_code_invoker.execute(
        task=f"""
        Complete implementation of the following feature:
        
        Requirements:
        {requirements}
        
        Tasks to complete:
        1. Research current best practices for this type of feature
        2. Review existing codebase for reusable components
        3. Design the solution architecture
        4. Implement the feature with proper error handling
        5. Write comprehensive tests
        6. Update documentation
        7. Run tests and ensure quality standards
        8. Prepare for deployment
        """,
        context={
            "project_root": "/home/opsvi/master_root",
            "target_app": "apps/my-app",
            "standards": "Follow monorepo standards",
            "sdlc_phase": "development"
        },
        tools_enabled=[
            "file_operations",
            "web_search",
            "git_operations",
            "test_execution",
            "project_intelligence"
        ]
    )
    
    return result
```

## When to Use Specialized Agents (5% of cases)

### Specialized Agent Use Cases

#### 1. High-Performance Batch Operations
**When**: Processing 1000+ files or operations
**Agent**: `batch_processor_agent`
**Reason**: Optimized for parallel processing and memory management
```python
# Use specialized agent for massive batch operations
await batch_processor_agent.process_files(
    files=large_file_list,  # 1000+ files
    operation="transform"
)
```

#### 2. Real-time Monitoring
**When**: Continuous monitoring with sub-second response requirements
**Agent**: `monitor_agent`
**Reason**: Event-driven architecture optimized for real-time
```python
# Use specialized agent for real-time monitoring
await monitor_agent.watch(
    targets=["system_metrics", "api_health"],
    interval_ms=100
)
```

#### 3. Domain-Specific Expertise
**When**: Highly specialized domains requiring specific models or tools
**Agent**: Domain-specific agents (e.g., `legal_agent`, `medical_agent`)
**Reason**: Pre-trained on domain data, specialized vocabulary
```python
# Use specialized agent for domain expertise
await legal_agent.review_contract(
    document=contract_text,
    jurisdiction="California"
)
```

#### 4. Deterministic Operations
**When**: Operations requiring 100% deterministic, reproducible results
**Agent**: `deterministic_processor`
**Reason**: Rule-based, no LLM variability
```python
# Use specialized agent for deterministic processing
await deterministic_processor.validate_schema(
    data=input_data,
    schema=validation_rules
)
```

#### 5. Resource-Constrained Environments
**When**: Running on edge devices or limited compute
**Agent**: `lightweight_agent`
**Reason**: Optimized for minimal resource usage
```python
# Use specialized agent for edge deployment
await lightweight_agent.process_local(
    task=simple_task,
    max_memory_mb=512
)
```

## Decision Framework

### Quick Decision Tree
```
┌─────────────────────────┐
│   Start: Agent Task     │
└───────────┬─────────────┘
            │
            ▼
┌──────────────────────────┐
│ Is it one of the 5       │
│ specialized cases?       │
└─────────┬───────┬────────┘
          │ No    │ Yes
          ▼       ▼
┌──────────────┐ ┌──────────────────┐
│ Use Claude   │ │ Use Specialized  │
│ Code Agent   │ │ Agent            │
└──────────────┘ └──────────────────┘
```

### Decision Criteria Checklist
**Use Claude Code unless ALL of these are true:**
- [ ] Task requires specialized domain knowledge not in Claude Code
- [ ] Performance requirements exceed Claude Code capabilities
- [ ] Deterministic/reproducible results are mandatory
- [ ] Resource constraints prevent Claude Code usage
- [ ] Real-time processing with <1s response time needed

## Implementation Guidelines

### Standard Claude Code Wrapper
```python
# libs/opsvi-agents/opsvi_agents/claude_code_wrapper.py

from typing import Dict, Any, Optional
from opsvi_mcp.tools import mcp_invoker

class ClaudeCodeWrapper:
    """Standard wrapper for Claude Code invocations"""
    
    def __init__(self):
        self.default_context = {
            "project_root": "/home/opsvi/master_root",
            "standards": "Follow SDLC and monorepo standards",
            "knowledge_system": "Use knowledge system for patterns"
        }
    
    async def execute_task(
        self,
        task: str,
        app_name: Optional[str] = None,
        additional_context: Optional[Dict[str, Any]] = None,
        require_tests: bool = True,
        require_docs: bool = True,
        commit_changes: bool = True
    ) -> Dict[str, Any]:
        """
        Execute a task using Claude Code with standard patterns.
        
        Args:
            task: Task description
            app_name: Target app in apps/ directory
            additional_context: Extra context to merge
            require_tests: Enforce test writing
            require_docs: Enforce documentation
            commit_changes: Auto-commit on completion
        """
        context = self.default_context.copy()
        
        if app_name:
            context["target_app"] = f"apps/{app_name}"
        
        if additional_context:
            context.update(additional_context)
        
        # Build comprehensive task
        enhanced_task = f"""
        {task}
        
        Requirements:
        - Follow SDLC phases (Discovery → Design → Implementation → Testing)
        - Use project intelligence to find reusable components
        - Research current best practices before implementing
        {"- Write comprehensive tests" if require_tests else ""}
        {"- Update documentation" if require_docs else ""}
        {"- Commit changes with descriptive message" if commit_changes else ""}
        """
        
        result = await mcp_invoker.call(
            tool="claude_code",
            task=enhanced_task,
            context=context
        )
        
        return result

# Singleton instance
CLAUDE_CODE = ClaudeCodeWrapper()
```

### Integration with SDLC Enforcement
```python
# libs/opsvi-mcp/opsvi_mcp/tools/sdlc_claude_integration.py

class SDLCClaudeCodeEnforcer:
    """Ensures Claude Code follows SDLC phases"""
    
    async def execute_with_sdlc(
        self,
        task: str,
        skip_phases: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Execute task with SDLC phase enforcement"""
        
        phases = [
            ("discovery", "Research and gather requirements"),
            ("design", "Create solution design"),
            ("planning", "Plan implementation steps"),
            ("development", "Implement the solution"),
            ("testing", "Write and run tests"),
            ("deployment", "Prepare for deployment"),
            ("production", "Verify production readiness")
        ]
        
        skip_phases = skip_phases or []
        results = {}
        
        for phase_name, phase_desc in phases:
            if phase_name in skip_phases:
                continue
            
            phase_task = f"""
            SDLC Phase: {phase_name.upper()}
            {phase_desc} for the following task:
            {task}
            """
            
            results[phase_name] = await CLAUDE_CODE.execute_task(
                task=phase_task,
                commit_changes=(phase_name == "development")
            )
        
        return results
```

## Migration Strategy

### Phase 1: Documentation (Current)
- ✅ Document Claude Code as primary agent
- ✅ Define specialized agent use cases
- ✅ Create decision framework

### Phase 2: Wrapper Implementation
- [ ] Create `claude_code_wrapper.py`
- [ ] Integrate with MCP tools
- [ ] Add SDLC enforcement

### Phase 3: Agent Consolidation
- [ ] Deprecate redundant specialized agents
- [ ] Migrate existing agent calls to Claude Code
- [ ] Archive unused agent code

### Phase 4: Optimization
- [ ] Monitor Claude Code performance
- [ ] Identify new specialized agent needs
- [ ] Optimize invocation patterns

## Best Practices

### DO ✅
- **Use Claude Code by default** for all standard development tasks
- **Provide comprehensive context** in a single invocation
- **Let Claude Code handle the entire workflow** from research to deployment
- **Trust Claude Code's judgment** on tool selection and approach
- **Monitor results** and store successful patterns in knowledge system

### DON'T ❌
- **Don't split tasks** unnecessarily across multiple agents
- **Don't create specialized agents** without clear performance needs
- **Don't orchestrate** multiple agents when Claude Code can handle it
- **Don't assume** specialized agents are better for specific domains
- **Don't bypass** Claude Code without documenting the reason

## Performance Metrics

### Claude Code Performance Benchmarks
- **Feature Implementation**: 5-30 minutes (research to deployment)
- **Bug Fix**: 2-10 minutes (identification to verification)
- **Documentation**: 1-5 minutes per component
- **Test Writing**: 3-15 minutes for comprehensive suite
- **Code Review**: 2-8 minutes for thorough analysis

### Success Metrics
- **Task Completion Rate**: >95% without human intervention
- **Code Quality**: Passes all linting, type checking, tests
- **Context Retention**: Maintains context across entire session
- **Tool Utilization**: Automatically selects appropriate tools
- **Knowledge Integration**: Uses and updates knowledge system

## Examples

### Example 1: Complete Feature Implementation
```python
# Single Claude Code invocation replaces entire agent orchestra
result = await CLAUDE_CODE.execute_task(
    task="""
    Implement a user authentication system with:
    - JWT-based authentication
    - Role-based access control
    - Password reset functionality
    - Session management
    - Rate limiting
    """,
    app_name="auth-service",
    require_tests=True,
    require_docs=True,
    commit_changes=True
)
```

### Example 2: Complex Integration
```python
# Claude Code handles multi-service integration
result = await CLAUDE_CODE.execute_task(
    task="""
    Integrate Stripe payment processing:
    1. Research Stripe API best practices
    2. Review our existing payment architecture
    3. Design integration approach
    4. Implement webhook handlers
    5. Add payment processing logic
    6. Create comprehensive test suite
    7. Document API endpoints
    8. Set up monitoring
    """,
    app_name="payment-service"
)
```

### Example 3: When to Use Specialized Agent
```python
# ONLY use specialized agent for true edge cases
if len(files_to_process) > 10000:
    # Specialized batch processor for massive operations
    result = await batch_processor.process(
        files=files_to_process,
        parallel_workers=32
    )
else:
    # Claude Code for normal batch operations
    result = await CLAUDE_CODE.execute_task(
        task=f"Process {len(files_to_process)} files",
        additional_context={"files": files_to_process}
    )
```

## Conclusion

**Claude Code is the Swiss Army knife of AI agents** - versatile, reliable, and capable of handling almost any task. By standardizing on Claude Code as our primary agent, we:

1. **Reduce complexity** in our agent architecture
2. **Improve consistency** across all AI-assisted development
3. **Accelerate development** with single-agent workflows
4. **Maintain quality** through comprehensive task handling
5. **Simplify maintenance** with fewer agent interfaces

Specialized agents remain available for true edge cases, but Claude Code should be the first and usually only choice for agent tasks in the AI Factory.

---

*Last Updated: 2025-01-15*
*Status: Active Standard*
*Review Cycle: Quarterly*