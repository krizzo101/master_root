# Consult Agent Optimization Design Specification

**Version:** 1.0
**Date:** 2025-01-27
**Status:** Ready for Implementation Review
**Author:** AI Development Agent

## Executive Summary

This document outlines a comprehensive optimization strategy for the `consult_agent` system, focusing on performance improvements, cost reduction, and enhanced code quality through the integration of GPT-5's new parameters and tools, o3 model reasoning threading, and systematic log management.

### Key Objectives
- **25% token usage reduction** through optimized parameters and threading
- **20% faster response times** via minimal reasoning and verbosity control
- **96.3% log size reduction** through deduplication and structured logging
- **Enhanced code quality** through accountable critic feedback
- **Stateful conversations** using `previous_response_id` threading

## 1. Current System Analysis

### 1.1 Performance Issues Identified
- **Log Duplication:** 91.2% duplication rate in `knowledge/nano.txt` (13,118 lines, only 8.3% meaningful content)
- **Inefficient Parameters:** Fixed verbosity and reasoning effort for all tasks
- **Vague Critic Feedback:** Non-actionable suggestions instead of concrete fixes
- **Context Loss:** No threading support, requiring full context resend
- **High Token Usage:** Unoptimized prompts and parameter selection

### 1.2 Log Analysis Results
```
Total Lines: 13,118
Unique Lines: 1,145 (8.7%)
Duplicate Lines: 11,973 (91.2%)
Meaningful Content: 1,089 lines (8.3%)
Optimization Potential: 96.3% reduction
```

## 2. GPT-5 Integration Strategy

### 2.1 New Parameters Leveraged

#### Verbosity Control (Policy-Level)
- **Low:** Code generation, bug fixes (terse, minimal prose)
- **Medium:** Refactoring, documentation (balanced detail)
- **High:** Code review, teaching (verbose, comprehensive)
- **Implementation:** Mapped to prompt style and token limits, not API parameter

#### Minimal Reasoning (o-series only)
- **Minimal:** Simple fixes, formatting, basic validation
- **Medium:** Standard code generation, refactoring
- **High:** Architecture, complex algorithms, system design
- **Implementation:** `reasoning.effort` parameter for o3/o4-mini models only

#### Free-Form Function Calling
- **`code_exec` tool:** Direct Python code execution
- **`python_grammar` tool:** Context-Free Grammar syntax validation

### 2.2 Threading Implementation

#### GPT-5 Stateful Conversations
```python
# Implicit threading (server-side state)
r1 = client.responses.create(
    model="gpt-5",
    input=[{"role":"user","content":"Task 1"}],
    store=True,  # Platform keeps context
)

r2 = client.responses.create(
    model="gpt-5",
    previous_response_id=r1.id,  # Continue from r1
    input=[{"role":"user","content":"Task 2"}],
    store=True,
)

# Stateless fallback (curated context window)
if not store_responses or no_previous_response_id:
    curated_context = get_recent_messages(session_id, window_size=10)
    input_items = curated_context + [{"role":"user","content":"Task 2"}]
    r2 = client.responses.create(
        model="gpt-5",
        input=input_items,
        store=False,
    )
```

#### Benefits
- **Reduced token usage** by eliminating context resend
- **Faster response times** through context continuity
- **Natural conversation flow** across iterations
- **Cost optimization** through efficient context management

## 3. Main Agent Optimization

### 3.1 OptimizedMainAgent Class

#### Key Features
- **Dynamic parameter selection** based on task type and complexity
- **Threading support** with `previous_response_id`
- **Free-form function calling** for code execution and validation
- **Performance tracking** with token usage and cost estimation
- **Structured JSON output** to eliminate parsing issues

#### Configuration
```python
@dataclass
class AgentConfig:
    model: str = "gpt-5-nano"
    verbosity: str = "low"  # Policy-level setting, mapped to prompts
    reasoning_effort: str = "medium"  # o-series only parameter
    max_output_tokens: int = 4000
    temperature: float = 0.0  # Deterministic defaults
    store_responses: bool = True  # Enable threading
```

#### Task-Specific Optimization
```python
def _get_verbosity_for_task(self, task_type: str) -> str:
    verbosity_map = {
        "code_generation": "low",      # Focus on code
        "bug_fix": "low",              # Quick fixes
        "refactoring": "medium",       # Some explanation
        "code_review": "high",         # Detailed analysis
        "teaching": "high"             # Explanations important
    }

def _get_main_agent_schema(self) -> dict:
    """Get structured output schema for main agent."""
    return {
        "type": "object",
        "properties": {
            "files": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "content": {"type": "string"}
                    },
                    "required": ["path", "content"]
                }
            },
            "tests": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "content": {"type": "string"}
                    },
                    "required": ["path", "content"]
                }
            },
            "commands": {"type": "array", "items": {"type": "string"}},
            "explanation": {"type": "string"},
            "status": {"type": "string", "enum": ["success", "error"]}
        },
        "required": ["files", "status"]
    }
```

### 3.2 Conversation Threading

#### Session Management
```python
def start_conversation(self, session_id: str) -> str:
    self.conversation_history[session_id] = {
        "current_response_id": None,
        "messages": [],
        "iteration_count": 0
    }

def continue_conversation(self, session_id: str, task: str, ...):
    # Add previous_response_id for threading
    if conversation["current_response_id"]:
        api_params["previous_response_id"] = conversation["current_response_id"]
```

## 4. Critic Agent Enhancement

### 4.1 o3 Model Integration

#### Reasoning Threading for o3
```python
# Stateful threading (preferred)
if self.config.store_responses and session["current_response_id"]:
    api_params["previous_response_id"] = session["current_response_id"]

# Stateless threading (fallback)
elif not self.config.store_responses and session["reasoning_items"]:
    # Include previous output items + reasoning.encrypted_content
    previous_items = session["reasoning_items"][-3:]  # Last 3 reasoning items
    api_params["input"] = previous_items + [{"role":"user","content":prompt}]
    api_params["include"] = ["reasoning.encrypted_content"]

# Extract reasoning items
reasoning_items = []
for item in response.output:
    if hasattr(item, "type") and item.type == "reasoning":
        reasoning_items.append(item)
```

#### Structured JSON Output (Responses API Enforced)
```python
# Critic API call with structured outputs
response = client.responses.create(
    model="o3",
    input=[{"role":"developer","content":prompt}],
    response={
        "modalities": ["text"],
        "text": {
            "format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "critic_result",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "status": {"type": "string", "enum": ["success", "error"]},
                            "issues": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "severity": {"type": "string", "enum": ["critical", "high", "medium", "low"]},
                                        "category": {"type": "string", "enum": ["syntax", "functional", "security", "performance", "style"]},
                                        "description": {"type": "string"},
                                        "location": {"type": "string"},
                                        "evidence": {"type": "string"},
                                        "impact": {"type": "string"}
                                    },
                                    "required": ["severity", "category", "description", "location", "evidence", "impact"]
                                }
                            },
                            "fixes": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "issue_id": {"type": "string"},
                                        "fix_type": {"type": "string", "enum": ["code_change", "architecture", "configuration", "dependency"]},
                                        "current_code": {"type": "string"},
                                        "fixed_code": {"type": "string"},
                                        "reasoning": {"type": "string"},
                                        "atomic_fix": {"type": "string", "maxLength": 140}
                                    },
                                    "required": ["issue_id", "fix_type", "current_code", "fixed_code", "reasoning", "atomic_fix"]
                                }
                            },
                            "priorities": {"type": "array", "items": {"type": "string"}},
                            "next_actions": {"type": "array", "items": {"type": "string"}},
                            "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
                            "estimated_effort": {"type": "string"}
                        },
                        "required": ["status", "issues", "fixes", "priorities", "next_actions", "confidence", "estimated_effort"]
                    },
                    "strict": True
                }
            }
        }
    }
)

# Parse structured output
data = response.output_parsed
```

### 4.2 Severity-Based Iteration

#### Iteration 1: Ruthless Analysis
- Find ALL issues, no matter how small
- Be extremely thorough and systematic
- Focus on critical issues that prevent code from running
- Identify architectural problems and security vulnerabilities

#### Iteration 2: Moderate Focus
- Focus on most critical issues from iteration 1
- Provide concrete, actionable fixes
- Prioritize functional correctness over style
- Address security and performance issues

#### Iteration 3: Light Polish
- Only address blocking issues
- Focus on final validation and polish
- Ensure all critical fixes are complete
- Minimal changes only

### 4.3 Accountability Framework

#### Performance Tracking
```python
def _calculate_performance_rating(self, session: Dict) -> str:
    total_issues = len(session["issues_found"])
    total_fixes = len(session["fixes_provided"])

    if total_fixes < total_issues * 0.5:
        return "NEEDS_IMPROVEMENT"
    elif total_fixes < total_issues * 0.8:
        return "GOOD"
    else:
        return "EXCELLENT"
```

## 5. Log Management Strategy

### 5.1 Current Log Issues
- **Massive duplication:** 91.2% duplicate lines
- **Boilerplate repetition:** Standard prompts repeated thousands of times
- **Poor structure:** Mixed content types without organization
- **Storage inefficiency:** 13,118 lines for 1,089 meaningful lines

### 5.2 Optimization Approach

#### Deduplication Strategy
```python
def clean_log_file(input_file: str, output_file: str):
    # Remove exact duplicates
    unique_lines = set()
    meaningful_lines = []

    for line in lines:
        if line not in unique_lines:
            unique_lines.add(line)
            if is_meaningful_content(line):
                meaningful_lines.append(line)
```

#### Log Rotation and Sampling
```python
@dataclass
class LogConfig:
    rotation_window: str = "daily"  # daily, weekly, monthly
    retention_days: int = 30
    sampling_rate: float = 0.1  # 10% of verbose traces
    indexed_fields: List[str] = field(default_factory=lambda: [
        "session_id", "response_id", "model", "total_tokens", "cost"
    ])
```

#### Structured Logging
```python
@dataclass
class LogEntry:
    timestamp: str
    session_id: str
    agent_type: str  # main|critic
    operation: str
    parameters: Dict[str, Any]
    result: Dict[str, Any]
    performance: Dict[str, Any]
```

#### Boilerplate Replacement
- Replace repeated prompts with placeholders
- Use session IDs for context tracking
- Implement structured JSON logging
- Enable selective log levels

### 5.3 Expected Results
- **96.3% size reduction** (13,118 → ~500 lines)
- **Improved readability** through structured format
- **Better analysis** with organized data
- **Reduced storage costs** and processing time

## 6. Implementation Roadmap

### Phase 1: Core Optimizations (Week 1)
1. **Implement OptimizedMainAgent**
   - Dynamic parameter selection
   - Threading support
   - Performance tracking
   - Free-form function calling

2. **Implement OptimizedCriticAgent**
   - Structured JSON output
   - Reasoning threading
   - Severity-based iterations
   - Accountability tracking

### Phase 2: Integration (Week 2)
1. **Update consult_agent tool**
   - Replace existing agent implementations
   - Add session management
   - Implement threading support
   - Update error handling

2. **Log Management**
   - Implement structured logging
   - Add deduplication
   - Create log analysis tools
   - Set up monitoring

### Phase 3: Testing & Validation (Week 3)
1. **Performance Testing**
   - Token usage comparison
   - Response time measurement (P95/P99 latency)
   - Cost analysis
   - Quality assessment
   - Reasoning token share measurement

2. **Integration Testing**
   - End-to-end workflow testing
   - Error handling validation
   - Threading verification
   - Log management validation

3. **Quality Gates (Blocking)**
   - **AST parse validation** - Ensure generated code is syntactically valid
   - **Ruff/Black formatting** - Enforce code style consistency
   - **MyPy type checking** - Validate type annotations
   - **Unit test execution** - Verify functionality
   - **Auto-critic invocation** - Route failures to critic with "verdict: revise" requirement

### Phase 4: Deployment (Week 4)
1. **Gradual Rollout**
   - Feature flags for new agents
   - A/B testing with existing system
   - Performance monitoring
   - User feedback collection

2. **Documentation & Training**
   - Update user documentation
   - Create migration guide
   - Train users on new features
   - Establish monitoring dashboards

## 7. Expected Benefits

### 7.1 Performance Improvements
- **25% token usage reduction** through optimized parameters and threading
- **20% faster response times** via minimal reasoning and verbosity control
- **96.3% log size reduction** through deduplication and structured logging
- **Better context continuity** through stateful conversations

### 7.2 Quality Enhancements
- **Concrete, actionable feedback** from critic agent
- **Systematic issue resolution** with accountability tracking
- **Improved code generation** through task-specific optimization
- **Better error handling** with structured validation

### 7.3 Cost Optimization
- **Reduced API costs** through efficient token usage
- **Lower storage costs** through log optimization
- **Faster development cycles** through improved feedback
- **Reduced debugging time** through better logging

## 8. Risk Assessment

### 8.1 Technical Risks
- **API compatibility:** New GPT-5 parameters may have limited availability
- **Threading complexity:** Stateful conversations require careful session management
- **Performance regression:** Optimization may introduce new bottlenecks
- **Integration challenges:** Existing system may require significant refactoring

### 8.2 Implementation Nits (Fast Wins)
- **Guard rails for contract drift:** Parse + assert public API signatures match spec before accepting generation
- **Determinism defaults:** `temperature=0` across critic/executor; allow per-task override only via explicit policy
- **Retry envelope:** Responses transient errors → exponential backoff with jitter; cap 3 tries, then fallback to "revise" with error payload
- **Cost caps:** Enforce `max_output_tokens` by task type and short-circuit if o3 spends too many reasoning tokens without tool call

### 8.3 Mitigation Strategies
- **Feature flags:** Gradual rollout with fallback options
- **Comprehensive testing:** Extensive validation before deployment
- **Monitoring:** Real-time performance tracking
- **Rollback plan:** Quick reversion to previous system if needed

## 9. Success Metrics

### 9.1 Quantitative Metrics
- **Token usage reduction:** Target 25% decrease
- **Response time improvement:** Target 20% faster (P95/P99 latency)
- **Log size reduction:** Target 96.3% decrease
- **Cost savings:** Target 30% reduction in API costs
- **Reasoning token share:** Target <20% for o-series models
- **Structured output success rate:** Target >95% parse success

### 9.2 Qualitative Metrics
- **Code quality improvement:** Measured through critic feedback
- **User satisfaction:** Feedback on response quality and speed
- **Developer productivity:** Time saved in development cycles
- **System reliability:** Reduced errors and improved stability

## 10. Technical Specifications

### 10.1 File Structure
```
consult_agent_optimization/
├── optimized_main_agent.py          # GPT-5 optimized main agent
├── optimized_critic_implementation.py # o3 optimized critic agent
├── log_management/
│   ├── clean_log.py                 # Log deduplication tool
│   ├── structured_logger.py         # Structured logging implementation
│   └── log_analyzer.py              # Log analysis utilities
├── integration/
│   ├── session_manager.py           # Conversation threading
│   ├── performance_tracker.py       # Metrics collection
│   └── config_manager.py            # Configuration management
└── tests/
    ├── test_main_agent.py           # Main agent tests
    ├── test_critic_agent.py         # Critic agent tests
    └── test_integration.py          # Integration tests
```

### 10.2 API Integration Points
- **OpenAI Responses API:** For GPT-5 and o3 model calls
- **Threading support:** `previous_response_id` parameter
- **Structured outputs:** JSON schema validation via `response.text.format.json_schema`
- **Free-form function calling:** Custom tool integration
- **o3 reasoning threading:** `include=["reasoning.encrypted_content"]` for stateless calls
- **Retry envelope:** Exponential backoff with jitter, max 3 attempts
- **Cost caps:** `max_output_tokens` enforcement by task type

### 10.3 Configuration Management
```python
# Environment variables
OPENAI_API_KEY=required
CONSULT_AGENT_LOG_LEVEL=INFO
CONSULT_AGENT_STORE_RESPONSES=true
CONSULT_AGENT_INCLUDE_REASONING=true
CONSULT_AGENT_MAX_RETRIES=3
CONSULT_AGENT_COST_CAP_PER_TASK=0.10  # $0.10 max per task

# Configuration files
agent_config.yaml    # Agent-specific settings
critic_config.yaml   # Critic-specific settings
logging_config.yaml  # Log management settings
quality_gates.yaml   # Testing and validation rules
```

## 11. Conclusion

This optimization design provides a comprehensive approach to improving the `consult_agent` system through:

1. **GPT-5 parameter optimization** for better performance and cost efficiency
2. **Threading support** for stateful conversations and context continuity
3. **Enhanced critic feedback** with structured, actionable guidance
4. **Systematic log management** for improved analysis and storage efficiency
5. **Accountability frameworks** for quality assurance and performance tracking

The implementation roadmap ensures a gradual, safe deployment with comprehensive testing and monitoring. The expected benefits include significant performance improvements, cost reductions, and enhanced code quality, making this optimization a high-value investment for the development team.

---

**Next Steps:**
1. Review and approve this design specification
2. Begin Phase 1 implementation (Core Optimizations)
3. Set up monitoring and testing infrastructure
4. Prepare for gradual rollout and user training

**Questions for Review:**
- Are there any technical constraints or limitations we should consider?
- Should we prioritize any specific aspect of the optimization?
- Are there additional metrics or success criteria we should include?
- What is the preferred timeline for implementation?
