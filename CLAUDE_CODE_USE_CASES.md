# Claude Code MCP Servers - Ideal Use Cases Guide

## Overview
Each Claude Code server version is optimized for specific scenarios. This guide helps you choose the right server based on your task requirements.

---

## V1 Server (claude-code-wrapper) - Traditional Job Management

### 🎯 Ideal Use Cases

#### 1. **Interactive Development Sessions**
- **Scenario**: Step-by-step code development with immediate feedback
- **Example**: Building a REST API endpoint by endpoint
- **Why V1**: Synchronous execution provides instant results for iterative development

#### 2. **Debugging & Troubleshooting**
- **Scenario**: Identifying and fixing bugs in existing code
- **Example**: Tracking down a memory leak or performance issue
- **Why V1**: Job tracking and status monitoring help understand execution flow

#### 3. **Code Generation with Dependencies**
- **Scenario**: Creating code that depends on previous results
- **Example**: Building a data pipeline where each step depends on the previous
- **Why V1**: Parent-child job relationships maintain execution context

#### 4. **Learning & Exploration**
- **Scenario**: Exploring new libraries or frameworks
- **Example**: Testing different approaches to solve a problem
- **Why V1**: Immediate feedback and ability to kill/restart jobs

#### 5. **CI/CD Pipeline Integration**
- **Scenario**: Automated code generation in build pipelines
- **Example**: Generating API clients from OpenAPI specs
- **Why V1**: Synchronous execution fits pipeline steps, recursion tracking prevents runaway jobs

### 📋 V1 Best Practices
```python
# Synchronous for immediate needs
result = await claude_run(
    task="Fix the authentication bug in login.py",
    outputFormat="json",
    permissionMode="default"
)

# Async for longer tasks with monitoring
job_id = await claude_run_async(
    task="Refactor the entire authentication module",
    parentJobId=parent_id  # Maintain context
)
# Monitor progress
status = await claude_status(job_id)
```

---

## V2 Server (claude-code-v2) - Parallel Fire-and-Forget

### 🎯 Ideal Use Cases

#### 1. **Large-Scale Code Analysis**
- **Scenario**: Analyzing multiple repositories or large codebases
- **Example**: Security audit across 50 microservices
- **Why V2**: Parallel agents can analyze different services simultaneously

#### 2. **Batch Code Generation**
- **Scenario**: Creating multiple independent components
- **Example**: Generating CRUD operations for 20 database tables
- **Why V2**: Each table's code can be generated in parallel

#### 3. **Multi-Perspective Code Review**
- **Scenario**: Getting different types of analysis on the same code
- **Example**: Security, performance, and style reviews
- **Why V2**: Different agents can focus on different aspects concurrently

#### 4. **Test Suite Generation**
- **Scenario**: Creating comprehensive test coverage
- **Example**: Unit tests, integration tests, and e2e tests for a module
- **Why V2**: Different test types can be generated independently

#### 5. **Documentation Generation**
- **Scenario**: Creating multiple documentation formats
- **Example**: API docs, user guides, and developer docs
- **Why V2**: Each documentation type can be processed in parallel

#### 6. **Comparative Analysis**
- **Scenario**: Evaluating different implementation approaches
- **Example**: Comparing REST vs GraphQL implementations
- **Why V2**: Multiple agents can implement different approaches simultaneously

### 📋 V2 Best Practices
```python
# Parallel analysis tasks
jobs = await spawn_parallel_agents(
    tasks=[
        "Analyze security vulnerabilities in auth module",
        "Check performance bottlenecks in database queries",
        "Review code style and best practices",
        "Generate test coverage report"
    ],
    agent_profile="comprehensive",
    max_concurrent=4
)

# Collect and aggregate results
results = await collect_results({
    "job_ids": jobs,
    "wait_for_completion": True
})
summary = await aggregate_results(
    aggregation_type="consensus"  # Find common findings
)
```

---

## V3 Server (claude-code-v3) - Intelligent Multi-Agent

### 🎯 Ideal Use Cases

#### 1. **Production-Ready Feature Development**
- **Scenario**: Building complete, tested, documented features
- **Example**: Implementing a payment processing system
- **Why V3**: FULL_CYCLE mode ensures code, tests, docs, and security review

#### 2. **Complex Refactoring Projects**
- **Scenario**: Major architectural changes with quality assurance
- **Example**: Migrating monolith to microservices
- **Why V3**: QUALITY mode includes automatic review and validation

#### 3. **Rapid Prototyping**
- **Scenario**: Quick proof-of-concepts that might become production code
- **Example**: MVP for a new product feature
- **Why V3**: Auto-detects when to switch from RAPID to QUALITY mode

#### 4. **Automated Code Modernization**
- **Scenario**: Upgrading legacy code to modern standards
- **Example**: Python 2 to Python 3 migration
- **Why V3**: Intelligent mode selection based on code complexity

#### 5. **Critical System Components**
- **Scenario**: Building security-critical or high-reliability code
- **Example**: Authentication system, payment processing, data encryption
- **Why V3**: Automatic security agent review and comprehensive testing

#### 6. **AI-Driven Development**
- **Scenario**: Let AI determine the best approach
- **Example**: "Make this API 10x faster"
- **Why V3**: Analyzes task and selects appropriate agents and strategies

#### 7. **Educational Code Generation**
- **Scenario**: Creating well-documented example code
- **Example**: Tutorial code for a programming course
- **Why V3**: DOCUMENTATION mode focuses on clarity and explanation

### 📋 V3 Best Practices
```python
# Let V3 intelligently decide
result = await claude_run_v3(
    task="Create a production-ready user authentication system with JWT, rate limiting, and 2FA",
    auto_detect=True  # V3 will choose FULL_CYCLE mode
)

# Force specific quality level for critical code
result = await claude_run_v3(
    task="Implement encryption for sensitive user data",
    mode="QUALITY",
    quality_level="maximum"  # Highest security standards
)

# Rapid prototyping
result = await claude_run_v3(
    task="Quick POC for real-time notifications",
    mode="RAPID"  # Skip extensive validation
)
```

---

## Decision Matrix

| Requirement | V1 | V2 | V3 |
|------------|----|----|-----|
| **Immediate feedback needed** | ✅ Best | ⚠️ Okay | ⚠️ Okay |
| **Multiple independent tasks** | ⚠️ Sequential | ✅ Best | ✅ Good |
| **Quality assurance required** | ❌ Manual | ⚠️ Manual | ✅ Automatic |
| **Production-ready code** | ⚠️ Possible | ⚠️ Possible | ✅ Best |
| **Debugging/Investigation** | ✅ Best | ❌ Not ideal | ⚠️ Okay |
| **Batch processing** | ⚠️ Slow | ✅ Best | ✅ Good |
| **Context preservation** | ✅ Parent-child | ❌ Independent | ✅ Intelligent |
| **Resource efficiency** | ✅ Controlled | ⚠️ Can spike | ✅ Optimized |
| **Task complexity handling** | ⚠️ Manual | ⚠️ Manual | ✅ Automatic |

---

## Choosing the Right Server

### Use V1 When:
- You need immediate, synchronous results
- Tasks have dependencies on each other
- You want to monitor job progress in real-time
- Debugging or investigating issues
- Working in an interactive development session
- You need precise control over execution flow

### Use V2 When:
- You have many independent tasks to process
- Parallel execution would significantly reduce time
- Tasks don't need to communicate with each other
- You're doing batch analysis or generation
- Results can be collected and processed later
- You want maximum throughput

### Use V3 When:
- Code quality is critical
- You need production-ready output
- Task complexity varies and needs intelligent handling
- You want automatic quality assurance
- Multiple agents (critic, tester, documenter) add value
- You're unsure about the best approach (use auto-detect)

---

## Combined Usage Patterns

### Pattern 1: V3 → V2 (Planning → Execution)
```python
# V3 for intelligent planning
plan = await claude_run_v3(
    task="Design microservices architecture",
    mode="ANALYSIS"
)

# V2 for parallel implementation
services = await spawn_parallel_agents(
    tasks=plan["services_to_implement"],
    agent_profile="microservice"
)
```

### Pattern 2: V2 → V1 (Analysis → Fix)
```python
# V2 for parallel analysis
issues = await spawn_parallel_agents(
    tasks=["Security scan", "Performance audit", "Code review"]
)

# V1 for sequential fixes
for issue in issues["critical"]:
    await claude_run(task=f"Fix: {issue}", permissionMode="default")
```

### Pattern 3: V1 → V3 (Prototype → Production)
```python
# V1 for rapid iteration
prototype = await claude_run(
    task="Create quick POC for feature X"
)

# V3 for production-ready version
production = await claude_run_v3(
    task=f"Convert POC to production: {prototype['code']}",
    mode="FULL_CYCLE"
)
```

---

## Performance Considerations

### V1 Performance Profile
- **Latency**: 5-30 seconds per task
- **Throughput**: Limited by recursion depth (max 3 levels)
- **Memory**: Moderate, maintains job history
- **Best for**: 1-10 sequential tasks

### V2 Performance Profile
- **Latency**: Near-instant job submission
- **Throughput**: High, limited by system resources
- **Memory**: Can be high with many parallel agents
- **Best for**: 10-100+ parallel tasks

### V3 Performance Profile
- **Latency**: Variable (10s for RAPID, 2-5min for FULL_CYCLE)
- **Throughput**: Moderate, optimized per mode
- **Memory**: Managed through checkpointing
- **Best for**: Complex tasks requiring quality

---

## Real-World Scenarios

### Scenario 1: Startup MVP Development
**Best Choice: V3 with RAPID mode initially, then QUALITY mode**
- Start with rapid prototyping to validate ideas
- Switch to quality mode for customer-facing features
- Use FULL_CYCLE for payment and auth systems

### Scenario 2: Enterprise Code Audit
**Best Choice: V2 for analysis, V1 for fixes**
- V2 parallel agents scan all repositories
- Aggregate findings to identify patterns
- V1 for systematic remediation with tracking

### Scenario 3: Open Source Library Development
**Best Choice: V3 with DOCUMENTATION mode**
- Ensures code is well-documented
- Automatic test generation
- Quality review for public API

### Scenario 4: Hackathon Project
**Best Choice: V1 for speed and iteration**
- Quick feedback loops
- Easy to pivot and restart
- No overhead from quality checks

### Scenario 5: Microservices Migration
**Best Choice: Combined V3→V2→V1**
- V3 ANALYSIS mode for architecture design
- V2 parallel generation of service stubs
- V1 for sequential integration and testing

---

## Conclusion

- **V1** excels at interactive, sequential tasks with immediate feedback
- **V2** dominates parallel, independent batch processing scenarios  
- **V3** provides intelligent, quality-assured production-ready solutions

Choose based on your specific needs: speed (V1), scale (V2), or sophistication (V3).