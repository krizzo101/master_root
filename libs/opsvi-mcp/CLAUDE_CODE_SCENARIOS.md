# Claude Code Real-World Scenarios & Server Selection

## Purpose
This document provides detailed real-world scenarios showing exactly when and why to use each Claude Code server version, with complete rationale and example implementations.

---

## 📚 Scenario Categories

### 1. Development Scenarios
- [S1.1: Bug Fixing](#s11-bug-fixing)
- [S1.2: Feature Development](#s12-feature-development)
- [S1.3: Code Refactoring](#s13-code-refactoring)
- [S1.4: Test Generation](#s14-test-generation)

### 2. Analysis Scenarios
- [S2.1: Security Audit](#s21-security-audit)
- [S2.2: Performance Analysis](#s22-performance-analysis)
- [S2.3: Code Quality Review](#s23-code-quality-review)
- [S2.4: Technical Debt Assessment](#s24-technical-debt-assessment)

### 3. Operations Scenarios
- [S3.1: Documentation Generation](#s31-documentation-generation)
- [S3.2: Migration Tasks](#s32-migration-tasks)
- [S3.3: Deployment Preparation](#s33-deployment-preparation)
- [S3.4: Monitoring Setup](#s34-monitoring-setup)

---

## Development Scenarios

### S1.1: Bug Fixing

#### Scenario A: "There's a null pointer exception in the user service"
**User Prompt:** "Debug and fix the NullPointerException occurring in UserService.java line 145"

**Server Selection: V1 (Synchronous)**

**Rationale:**
- Single, specific issue to investigate
- Requires interactive debugging
- Need to understand context before fixing
- Sequential steps: analyze → understand → fix → verify

**Implementation:**
```python
result = await mcp__claude-code-wrapper__claude_run(
    task="""
    Debug NullPointerException in UserService.java line 145:
    1. Analyze the stack trace and surrounding code
    2. Identify the null reference
    3. Implement null safety checks
    4. Verify the fix doesn't break existing functionality
    """,
    outputFormat="json",
    permissionMode="default"
)
```

#### Scenario B: "Fix all TypeScript errors in the project"
**User Prompt:** "Find and fix all TypeScript compilation errors across the entire project"

**Server Selection: V2 (Parallel)**

**Rationale:**
- Multiple independent errors to fix
- Each file can be fixed separately
- Parallel processing saves significant time
- No dependencies between fixes

**Implementation:**
```python
# First, identify all files with errors
errors = await mcp__claude-code-wrapper__claude_run(
    task="Identify all TypeScript files with compilation errors",
    outputFormat="json"
)

# Then fix in parallel
await mcp__claude-code-v2__spawn_parallel_agents(
    tasks=[f"Fix TypeScript errors in {file}" for file in errors['files']],
    agent_profile="typescript_fixer",
    timeout=300
)
```

---

### S1.2: Feature Development

#### Scenario A: "Add a simple export button to the dashboard"
**User Prompt:** "Add an export to CSV button on the admin dashboard"

**Server Selection: V1 (Async)**

**Rationale:**
- Single, well-defined feature
- Straightforward implementation
- No complex quality requirements
- Can complete in one pass

**Implementation:**
```python
job_id = await mcp__claude-code-wrapper__claude_run_async(
    task="""
    Add CSV export button to admin dashboard:
    1. Create export button component
    2. Implement CSV generation logic
    3. Add click handler to trigger download
    4. Style to match existing UI
    """,
    permissionMode="default"
)
```

#### Scenario B: "Build a complete user authentication system"
**User Prompt:** "Create a production-ready authentication system with JWT, 2FA, rate limiting, and password recovery"

**Server Selection: V3 (FULL_CYCLE mode)**

**Rationale:**
- Complex, multi-component system
- Production requirements stated explicitly
- Needs comprehensive testing
- Security-critical functionality
- Requires documentation

**Implementation:**
```python
result = await mcp__claude-code-v3__claude_run_v3(
    task="""
    Create production-ready authentication system:
    - JWT token management with refresh tokens
    - Two-factor authentication with TOTP
    - Rate limiting on login attempts
    - Secure password recovery flow
    - Session management
    - Audit logging
    Include comprehensive tests and API documentation
    """,
    mode="FULL_CYCLE",
    quality_level="high"
)
```

---

### S1.3: Code Refactoring

#### Scenario A: "Clean up this messy function"
**User Prompt:** "Refactor the calculateOrderTotal function to be more readable"

**Server Selection: V1 (Synchronous)**

**Rationale:**
- Single function scope
- Immediate feedback desired
- Requires understanding existing logic
- Quick turnaround needed

**Implementation:**
```python
result = await mcp__claude-code-wrapper__claude_run(
    task="""
    Refactor calculateOrderTotal function:
    1. Analyze current implementation
    2. Identify code smells
    3. Apply clean code principles
    4. Maintain backward compatibility
    5. Add clarifying comments
    """,
    outputFormat="json"
)
```

#### Scenario B: "Modernize our entire API layer"
**User Prompt:** "Refactor all API endpoints from callbacks to async/await pattern"

**Server Selection: V2 (Parallel) + V3 (Review)**

**Rationale:**
- Many files to refactor
- Each endpoint independent
- Want quality assurance after refactoring
- Two-phase approach optimal

**Implementation:**
```python
# Phase 1: Parallel refactoring with V2
await mcp__claude-code-v2__spawn_parallel_agents(
    tasks=[f"Convert {endpoint} from callbacks to async/await" 
           for endpoint in api_endpoints],
    agent_profile="modernizer",
    output_dir="/tmp/refactored"
)

# Phase 2: Quality review with V3
await mcp__claude-code-v3__claude_run_v3(
    task="Review and validate all refactored API endpoints for correctness",
    mode="REVIEW"
)
```

---

### S1.4: Test Generation

#### Scenario A: "Write a test for this new function"
**User Prompt:** "Create unit tests for the calculateDiscount function"

**Server Selection: V1 (Synchronous)**

**Rationale:**
- Single function to test
- Quick, focused task
- Direct and simple

**Implementation:**
```python
result = await mcp__claude-code-wrapper__claude_run(
    task="""
    Create comprehensive unit tests for calculateDiscount:
    - Test normal cases
    - Test edge cases
    - Test error conditions
    - Include test documentation
    """,
    outputFormat="json"
)
```

#### Scenario B: "Generate test suites for all services"
**User Prompt:** "Create comprehensive test suites for all microservices with >80% coverage"

**Server Selection: V3 (TESTING mode)**

**Rationale:**
- Comprehensive testing requirement
- Coverage target specified
- Multiple service testing
- Quality critical

**Implementation:**
```python
result = await mcp__claude-code-v3__claude_run_v3(
    task="""
    Generate comprehensive test suites for all microservices:
    - Unit tests for all public methods
    - Integration tests for service interactions
    - E2E tests for critical paths
    - Achieve minimum 80% code coverage
    - Include test data factories
    - Add performance benchmarks
    """,
    mode="TESTING",
    quality_level="high"
)
```

---

## Analysis Scenarios

### S2.1: Security Audit

#### Scenario A: "Check this file for security issues"
**User Prompt:** "Review auth.js for security vulnerabilities"

**Server Selection: V1 (Synchronous)**

**Rationale:**
- Single file analysis
- Detailed investigation needed
- Immediate results wanted

**Implementation:**
```python
result = await mcp__claude-code-wrapper__claude_run(
    task="""
    Security audit of auth.js:
    1. Check for injection vulnerabilities
    2. Review authentication logic
    3. Verify proper input validation
    4. Check for sensitive data exposure
    5. Provide remediation recommendations
    """,
    permissionMode="readonly"
)
```

#### Scenario B: "Full security audit of the entire application"
**User Prompt:** "Perform comprehensive security analysis across all code, dependencies, and configurations"

**Server Selection: V2 (Parallel analysis) → V3 (Comprehensive report)**

**Rationale:**
- Large scope requiring parallel analysis
- Multiple aspects to check simultaneously
- Need aggregated findings and prioritization

**Implementation:**
```python
# Phase 1: Parallel security scans
security_tasks = [
    "Scan for SQL injection vulnerabilities",
    "Check for XSS vulnerabilities",
    "Audit authentication and authorization",
    "Review cryptographic implementations",
    "Check dependency vulnerabilities",
    "Analyze configuration security",
    "Review API security",
    "Check for sensitive data exposure"
]

await mcp__claude-code-v2__spawn_parallel_agents(
    tasks=security_tasks,
    agent_profile="security_auditor",
    output_dir="/tmp/security_audit"
)

# Phase 2: Aggregate and prioritize findings
await mcp__claude-code-v3__claude_run_v3(
    task="Aggregate security findings and create prioritized remediation plan",
    mode="ANALYSIS"
)
```

---

### S2.2: Performance Analysis

#### Scenario: "Find performance bottlenecks in our API"
**User Prompt:** "Analyze all API endpoints for performance issues and optimization opportunities"

**Server Selection: V2 (Parallel)**

**Rationale:**
- Multiple endpoints to analyze
- Each can be profiled independently
- Want comprehensive results quickly

**Implementation:**
```python
endpoints = get_all_endpoints()

await mcp__claude-code-v2__spawn_parallel_agents(
    tasks=[
        f"Profile {endpoint} for performance: analyze query efficiency, caching opportunities, and response time"
        for endpoint in endpoints
    ],
    agent_profile="performance_analyzer",
    timeout=600
)

# Collect and aggregate results
results = await mcp__claude-code-v2__collect_results(
    output_dir="/tmp/performance_analysis"
)
```

---

### S2.3: Code Quality Review

#### Scenario A: "Review my pull request"
**User Prompt:** "Review the changes in PR #234 for code quality and best practices"

**Server Selection: V1 (Synchronous)**

**Rationale:**
- Focused review of specific changes
- Interactive feedback expected
- Single cohesive review needed

**Implementation:**
```python
result = await mcp__claude-code-wrapper__claude_run(
    task="""
    Review PR #234:
    1. Check code style and formatting
    2. Verify best practices adherence
    3. Review logic and algorithms
    4. Check test coverage
    5. Provide actionable feedback
    """,
    outputFormat="json"
)
```

#### Scenario B: "Comprehensive code quality assessment for acquisition"
**User Prompt:** "Perform due diligence code quality assessment for potential acquisition"

**Server Selection: V3 (REVIEW mode)**

**Rationale:**
- Critical business decision
- Needs comprehensive analysis
- Requires detailed documentation
- Quality and accuracy paramount

**Implementation:**
```python
result = await mcp__claude-code-v3__claude_run_v3(
    task="""
    Comprehensive code quality assessment:
    - Architecture evaluation
    - Code quality metrics
    - Technical debt assessment
    - Security vulnerability scan
    - Scalability analysis
    - Maintenance complexity
    - Team velocity indicators
    - Technology stack evaluation
    Generate executive summary and detailed technical report
    """,
    mode="REVIEW",
    quality_level="maximum"
)
```

---

## Operations Scenarios

### S3.1: Documentation Generation

#### Scenario A: "Document this function"
**User Prompt:** "Add JSDoc comments to the processPayment function"

**Server Selection: V1 (Synchronous)**

**Rationale:**
- Single function documentation
- Quick task
- Straightforward requirement

**Implementation:**
```python
result = await mcp__claude-code-wrapper__claude_run(
    task="Add comprehensive JSDoc comments to processPayment function",
    outputFormat="json"
)
```

#### Scenario B: "Generate complete API documentation"
**User Prompt:** "Create comprehensive API documentation for all endpoints with examples"

**Server Selection: V3 (DOCUMENTATION mode)**

**Rationale:**
- Comprehensive documentation needed
- Requires consistency across all endpoints
- Examples and schemas required
- Quality important for external users

**Implementation:**
```python
result = await mcp__claude-code-v3__claude_run_v3(
    task="""
    Generate complete API documentation:
    - OpenAPI/Swagger specification
    - Endpoint descriptions and parameters
    - Request/response examples
    - Error code documentation
    - Authentication guide
    - Rate limiting information
    - Postman collection
    """,
    mode="DOCUMENTATION"
)
```

---

### S3.2: Migration Tasks

#### Scenario: "Migrate from MongoDB to PostgreSQL"
**User Prompt:** "Migrate our entire application from MongoDB to PostgreSQL"

**Server Selection: V3 (FULL_CYCLE) with V2 support**

**Rationale:**
- Complex, multi-phase migration
- Requires careful planning
- Need data migration scripts
- Must maintain data integrity
- Parallel migration possible for independent collections

**Implementation:**
```python
# Phase 1: Planning and schema design
plan = await mcp__claude-code-v3__claude_run_v3(
    task="""
    Design PostgreSQL migration plan:
    1. Analyze MongoDB schema
    2. Design PostgreSQL schema
    3. Create migration strategy
    4. Identify risks and mitigation
    """,
    mode="ANALYSIS"
)

# Phase 2: Parallel migration scripts
await mcp__claude-code-v2__spawn_parallel_agents(
    tasks=[
        f"Create migration script for {collection} collection to PostgreSQL"
        for collection in mongodb_collections
    ],
    agent_profile="migration_specialist"
)

# Phase 3: Implementation and validation
await mcp__claude-code-v3__claude_run_v3(
    task="""
    Implement and validate migration:
    1. Update application code for PostgreSQL
    2. Create rollback procedures
    3. Implement data validation
    4. Generate migration documentation
    """,
    mode="FULL_CYCLE"
)
```

---

### S3.3: Deployment Preparation

#### Scenario: "Prepare application for production deployment"
**User Prompt:** "Get our application ready for production deployment on AWS"

**Server Selection: V3 (FULL_CYCLE)**

**Rationale:**
- Production deployment is critical
- Multiple aspects to consider
- Requires comprehensive approach
- Quality and security paramount

**Implementation:**
```python
result = await mcp__claude-code-v3__claude_run_v3(
    task="""
    Prepare for AWS production deployment:
    - Environment configuration management
    - Secrets management setup (AWS Secrets Manager)
    - Infrastructure as Code (Terraform/CloudFormation)
    - CI/CD pipeline configuration
    - Monitoring and alerting setup
    - Auto-scaling configuration
    - Backup and disaster recovery
    - Security group and IAM setup
    - Health checks and readiness probes
    - Deployment documentation
    """,
    mode="FULL_CYCLE",
    quality_level="high"
)
```

---

## 🎯 Decision Matrix Summary

| Scenario Type | Single/Simple | Multiple/Independent | Complex/Quality-Critical |
|--------------|---------------|---------------------|------------------------|
| **Bug Fixing** | V1 Sync | V2 Parallel | V3 DEBUG |
| **Feature Dev** | V1 Async | V2 Parallel | V3 FULL_CYCLE |
| **Refactoring** | V1 Sync | V2 Parallel | V3 QUALITY |
| **Testing** | V1 Sync | V2 Parallel | V3 TESTING |
| **Security** | V1 Sync | V2 Parallel | V3 REVIEW |
| **Performance** | V1 Sync | V2 Parallel | V3 ANALYSIS |
| **Documentation** | V1 Sync | V2 Parallel | V3 DOCUMENTATION |
| **Migration** | V1 Async | V2 + V1 | V3 FULL_CYCLE |
| **Deployment** | V1 Async | V2 Parallel | V3 FULL_CYCLE |

---

## 🔄 Combined Server Patterns

### Pattern 1: V1 → V2 (Discover then Process)
```python
# Discover issues with V1
issues = await mcp__claude-code-wrapper__claude_run("Find all issues")

# Fix in parallel with V2
await mcp__claude-code-v2__spawn_parallel_agents(
    tasks=[f"Fix {issue}" for issue in issues]
)
```

### Pattern 2: V2 → V3 (Parallel then Validate)
```python
# Generate in parallel with V2
await mcp__claude-code-v2__spawn_parallel_agents(tasks=generation_tasks)

# Validate and integrate with V3
await mcp__claude-code-v3__claude_run_v3(
    task="Validate and integrate all generated components",
    mode="QUALITY"
)
```

### Pattern 3: V3 → V2 → V1 (Plan, Execute, Refine)
```python
# Plan with V3
plan = await mcp__claude-code-v3__claude_run_v3(task="Design system", mode="ANALYSIS")

# Execute in parallel with V2
await mcp__claude-code-v2__spawn_parallel_agents(tasks=plan['implementation_tasks'])

# Refine specific issues with V1
await mcp__claude-code-wrapper__claude_run("Refine edge cases")
```

---

## 📝 Server Selection Checklist

Before selecting a server, ask:

1. **Is this a single task or multiple tasks?**
   - Single → Consider V1
   - Multiple → Consider V2 or V3

2. **Are the tasks independent?**
   - Yes → V2 is optimal
   - No → V1 or V3

3. **Is quality/production-readiness critical?**
   - Yes → V3 is required
   - No → V1 or V2 sufficient

4. **Do I need immediate results?**
   - Yes → V1 synchronous
   - No → Any server works

5. **Is this debugging/investigation?**
   - Yes → V1 is best
   - No → Consider task type

6. **Will this benefit from multiple agents?**
   - Yes → V3 multi-agent
   - No → V1 or V2

This comprehensive scenario guide ensures optimal server selection for any situation.