#!/bin/bash
# Optimized Headless Claude Agent Configurations
# Maximum performance and customization parameters

# ============================================
# PERFORMANCE OPTIMIZATIONS
# ============================================

# Minimal MCP config for maximum speed
export CLAUDE_MINIMAL_MCP='{"mcpServers": {}}'
export CLAUDE_MINIMAL_MCP_PATH="$HOME/.claude_minimal.json"
echo "$CLAUDE_MINIMAL_MCP" > "$CLAUDE_MINIMAL_MCP_PATH"

# ============================================
# SPECIALIZED AGENT FUNCTIONS
# ============================================

# 1. SPEED DEMON - Maximum speed, minimum overhead
claude_speed() {
    local TASK="$1"
    local SESSION_ID="${2:-$(uuidgen)}"

    claude -p \
        --model sonnet \
        --strict-mcp-config --mcp-config "$CLAUDE_MINIMAL_MCP_PATH" \
        --dangerously-skip-permissions \
        --no-conversation-history \
        --max-tokens 4000 \
        --temperature 0.1 \
        --output-format json \
        --session-id "$SESSION_ID" \
        --append-system-prompt "Be extremely concise. Output only essential information. Skip explanations." \
        -- "$TASK"
}

# 2. CODE GENERATOR - Optimized for code generation
claude_code() {
    local TASK="$1"
    local SESSION_ID="${2:-$(uuidgen)}"
    local LANGUAGE="${3:-python}"

    claude -p \
        --model opus \
        --strict-mcp-config --mcp-config "$CLAUDE_MINIMAL_MCP_PATH" \
        --permission-mode acceptEdits \
        --max-tokens 8000 \
        --temperature 0.3 \
        --output-format json \
        --session-id "$SESSION_ID" \
        --allowed-tools "Write,Read,Edit,MultiEdit" \
        --append-system-prompt "You are an expert $LANGUAGE developer.
Generate production-ready code with:
- Comprehensive error handling
- Type hints/annotations
- Docstrings
- Performance optimizations
- Security best practices
- No placeholder code
- No comments unless complex logic
Output executable code only." \
        -- "$TASK"
}

# 3. CODE REVIEWER - Focused on finding issues
claude_review() {
    local CODE_PATH="$1"
    local SESSION_ID="${2:-$(uuidgen)}"

    claude -p \
        --model opus \
        --strict-mcp-config --mcp-config "$CLAUDE_MINIMAL_MCP_PATH" \
        --permission-mode bypassPermissions \
        --max-tokens 6000 \
        --temperature 0.2 \
        --output-format json \
        --session-id "$SESSION_ID" \
        --allowed-tools "Read,Grep,Glob" \
        --add-dir "$(dirname "$CODE_PATH")" \
        --append-system-prompt "You are a senior code reviewer. Focus on:
- Security vulnerabilities (OWASP Top 10)
- Performance bottlenecks (O(n²) or worse)
- Memory leaks and resource management
- Race conditions and concurrency issues
- Error handling gaps
- Code smells and anti-patterns
- Missing edge cases
Be direct. List issues with severity (CRITICAL/HIGH/MEDIUM/LOW).
Provide specific line numbers and fixes.
Skip style issues unless they impact maintainability." \
        -- "Review the code in $CODE_PATH"
}

# 4. TEST GENERATOR - Comprehensive test creation
claude_test() {
    local CODE_PATH="$1"
    local SESSION_ID="${2:-$(uuidgen)}"
    local FRAMEWORK="${3:-pytest}"

    claude -p \
        --model sonnet \
        --strict-mcp-config --mcp-config "$CLAUDE_MINIMAL_MCP_PATH" \
        --permission-mode acceptEdits \
        --max-tokens 8000 \
        --temperature 0.4 \
        --output-format json \
        --session-id "$SESSION_ID" \
        --allowed-tools "Write,Read,Edit" \
        --add-dir "$(dirname "$CODE_PATH")" \
        --append-system-prompt "You are a QA automation expert using $FRAMEWORK.
Generate comprehensive tests including:
- Unit tests for all functions/methods
- Edge cases and boundary conditions
- Error scenarios and exception handling
- Performance tests where applicable
- Integration tests for external dependencies
- Fixtures and mocks as needed
- Parametrized tests for multiple scenarios
- Coverage should aim for >90%
Use descriptive test names. No placeholder assertions." \
        -- "Write comprehensive tests for $CODE_PATH"
}

# 5. REFACTORING SPECIALIST - Clean, optimized refactoring
claude_refactor() {
    local CODE_PATH="$1"
    local SESSION_ID="${2:-$(uuidgen)}"
    local FOCUS="${3:-performance}"  # performance, readability, maintainability

    claude -p \
        --model opus \
        --strict-mcp-config --mcp-config "$CLAUDE_MINIMAL_MCP_PATH" \
        --permission-mode acceptEdits \
        --max-tokens 8000 \
        --temperature 0.2 \
        --output-format json \
        --session-id "$SESSION_ID" \
        --allowed-tools "Read,Edit,MultiEdit,Write" \
        --add-dir "$(dirname "$CODE_PATH")" \
        --append-system-prompt "You are a refactoring expert. Focus: $FOCUS.
Refactoring priorities:
- Preserve ALL existing functionality
- Improve $FOCUS significantly
- Apply SOLID principles
- Reduce cyclomatic complexity
- Extract reusable components
- Improve naming clarity
- Add type hints if missing
- Optimize algorithms and data structures
- Ensure backward compatibility
Make surgical changes. Test preservation is critical." \
        -- "Refactor $CODE_PATH with focus on $FOCUS"
}

# 6. DOCUMENTATION WRITER - Comprehensive docs
claude_document() {
    local CODE_PATH="$1"
    local SESSION_ID="${2:-$(uuidgen)}"
    local DOC_TYPE="${3:-api}"  # api, user, developer, architecture

    claude -p \
        --model sonnet \
        --strict-mcp-config --mcp-config "$CLAUDE_MINIMAL_MCP_PATH" \
        --permission-mode bypassPermissions \
        --max-tokens 8000 \
        --temperature 0.5 \
        --output-format json \
        --session-id "$SESSION_ID" \
        --allowed-tools "Read,Write,Grep" \
        --add-dir "$(dirname "$CODE_PATH")" \
        --append-system-prompt "You are a technical documentation expert. Create $DOC_TYPE documentation.
Include:
- Clear overview and purpose
- Installation/setup instructions
- API reference with all parameters
- Code examples for common use cases
- Error handling and troubleshooting
- Performance considerations
- Security notes
- Migration guides if applicable
Use markdown. Include mermaid diagrams where helpful.
Write for experienced developers. Be concise but complete." \
        -- "Document $CODE_PATH as $DOC_TYPE documentation"
}

# 7. ARCHITECT - System design and planning
claude_architect() {
    local REQUIREMENTS="$1"
    local SESSION_ID="${2:-$(uuidgen)}"

    claude -p \
        --model opus \
        --strict-mcp-config --mcp-config "$CLAUDE_MINIMAL_MCP_PATH" \
        --permission-mode bypassPermissions \
        --max-tokens 10000 \
        --temperature 0.6 \
        --output-format json \
        --session-id "$SESSION_ID" \
        --append-system-prompt "You are a senior solutions architect.
Design production-ready systems considering:
- Scalability (handle 10x growth)
- Reliability (99.9% uptime)
- Security (defense in depth)
- Performance (sub-second response)
- Maintainability (clear boundaries)
- Cost optimization
- Technology selection rationale
- Data flow and storage strategy
- API design and integration points
- Deployment and DevOps considerations
- Monitoring and observability
- Disaster recovery plans
Output: Complete technical specification with diagrams." \
        -- "Design architecture for: $REQUIREMENTS"
}

# 8. DEBUGGER - Find and fix issues
claude_debug() {
    local ERROR_MSG="$1"
    local CODE_PATH="$2"
    local SESSION_ID="${3:-$(uuidgen)}"

    claude -p \
        --model opus \
        --strict-mcp-config --mcp-config "$CLAUDE_MINIMAL_MCP_PATH" \
        --permission-mode acceptEdits \
        --max-tokens 6000 \
        --temperature 0.1 \
        --output-format json \
        --session-id "$SESSION_ID" \
        --allowed-tools "Read,Edit,Bash,Grep" \
        --add-dir "$(dirname "$CODE_PATH")" \
        --append-system-prompt "You are a debugging expert.
Debugging approach:
1. Analyze the error message and stack trace
2. Identify root cause (not symptoms)
3. Check for similar issues in codebase
4. Implement minimal fix
5. Add defensive code to prevent recurrence
6. Verify fix doesn't break other functionality
Be surgical. Fix the issue without unnecessary changes.
Add error handling to prevent future occurrences." \
        -- "Debug this error: $ERROR_MSG in $CODE_PATH"
}

# 9. PERFORMANCE OPTIMIZER
claude_optimize() {
    local CODE_PATH="$1"
    local SESSION_ID="${2:-$(uuidgen)}"
    local TARGET="${3:-latency}"  # latency, throughput, memory

    claude -p \
        --model opus \
        --strict-mcp-config --mcp-config "$CLAUDE_MINIMAL_MCP_PATH" \
        --permission-mode acceptEdits \
        --max-tokens 8000 \
        --temperature 0.3 \
        --output-format json \
        --session-id "$SESSION_ID" \
        --allowed-tools "Read,Edit,MultiEdit,Bash" \
        --add-dir "$(dirname "$CODE_PATH")" \
        --append-system-prompt "You are a performance optimization expert. Target: $TARGET.
Optimization priorities:
- Profile before optimizing
- Focus on bottlenecks (80/20 rule)
- Algorithm complexity improvements
- Data structure optimization
- Caching strategies
- Lazy loading and pagination
- Database query optimization
- Parallel processing where applicable
- Memory pooling and reuse
- I/O batching
Measure improvements. Include benchmarks.
Maintain code readability." \
        -- "Optimize $CODE_PATH for $TARGET"
}

# 10. SECURITY AUDITOR
claude_security() {
    local CODE_PATH="$1"
    local SESSION_ID="${2:-$(uuidgen)}"

    claude -p \
        --model opus \
        --strict-mcp-config --mcp-config "$CLAUDE_MINIMAL_MCP_PATH" \
        --permission-mode bypassPermissions \
        --max-tokens 8000 \
        --temperature 0.1 \
        --output-format json \
        --session-id "$SESSION_ID" \
        --allowed-tools "Read,Grep,Glob" \
        --add-dir "$(dirname "$CODE_PATH")" \
        --append-system-prompt "You are a security auditor (CISSP/CEH level).
Security audit checklist:
- Input validation and sanitization
- SQL/NoSQL injection vulnerabilities
- XSS and CSRF protections
- Authentication and authorization flaws
- Sensitive data exposure
- Security misconfiguration
- Insecure dependencies (CVEs)
- Insufficient logging and monitoring
- API security issues
- Cryptographic weaknesses
- SSRF, XXE, and deserialization issues
Rate findings: CRITICAL/HIGH/MEDIUM/LOW.
Provide POC exploit code where applicable.
Include remediation steps with code." \
        -- "Security audit of $CODE_PATH"
}

# ============================================
# BATCH PROCESSING FUNCTIONS
# ============================================

# Run multiple agents in parallel
claude_parallel() {
    local MAX_PARALLEL="${MAX_PARALLEL:-10}"
    local TASKS=("$@")

    for task in "${TASKS[@]}"; do
        claude_speed "$task" &

        # Limit parallel jobs
        while [ $(jobs -r | wc -l) -ge $MAX_PARALLEL ]; do
            sleep 0.1
        done
    done
    wait
}

# Chain agents with context passing
claude_chain() {
    local SESSION_BASE="$(uuidgen | cut -d'-' -f1)"
    local RESULT=""

    for i in "$@"; do
        SESSION="${SESSION_BASE}-step-$i"
        RESULT=$(claude_speed "$i Context: $RESULT" "$SESSION")
    done

    echo "$RESULT"
}

# ============================================
# PERFORMANCE MONITORING
# ============================================

# Time and monitor agent execution
claude_monitor() {
    local AGENT_FUNC="$1"
    shift
    local ARGS="$@"

    local START=$(date +%s)
    local SESSION_ID=$(uuidgen)

    echo "Starting $AGENT_FUNC with session: $SESSION_ID" >&2

    # Run agent and capture result
    local RESULT=$($AGENT_FUNC "$ARGS" "$SESSION_ID")

    local END=$(date +%s)
    local DURATION=$((END - START))

    echo "Completed in ${DURATION}s" >&2
    echo "Session: $SESSION_ID" >&2
    echo "$RESULT"
}

# ============================================
# ALIASES FOR COMMON PATTERNS
# ============================================

alias claude-fast='claude_speed'
alias claude-code-gen='claude_code'
alias claude-review-pr='claude_review'
alias claude-write-tests='claude_test'
alias claude-refactor-perf='claude_refactor'
alias claude-write-docs='claude_document'
alias claude-design='claude_architect'
alias claude-fix='claude_debug'
alias claude-perf='claude_optimize'
alias claude-audit='claude_security'

# ============================================
# USAGE EXAMPLES
# ============================================

show_examples() {
    cat << 'EOF'
USAGE EXAMPLES:

# Quick task (3-5s)
claude_speed "Convert this JSON to YAML"

# Generate production code
claude_code "Implement OAuth2 flow with refresh tokens" session-123 python

# Review code for issues
claude_review ./src/auth.py

# Generate comprehensive tests
claude_test ./src/models.py session-456 pytest

# Refactor for performance
claude_refactor ./src/database.py session-789 performance

# Create documentation
claude_document ./src/api.py session-abc api

# Design system architecture
claude_architect "Multi-tenant SaaS platform with billing"

# Debug an error
claude_debug "TypeError: undefined is not a function" ./src/app.js

# Optimize performance
claude_optimize ./src/processor.py session-xyz latency

# Security audit
claude_security ./src/

# Parallel execution
claude_parallel "Task 1" "Task 2" "Task 3"

# Chained execution
claude_chain "Design API" "Implement API" "Write tests"

# Monitored execution
claude_monitor claude_code "Complex implementation"

EOF
}

# Export all functions
export -f claude_speed claude_code claude_review claude_test
export -f claude_refactor claude_document claude_architect
export -f claude_debug claude_optimize claude_security
export -f claude_parallel claude_chain claude_monitor
