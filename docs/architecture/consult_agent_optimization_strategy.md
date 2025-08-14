# Consult Agent Optimization Strategy: Right Tool for the Job

**Date:** 2025-01-27
**Status:** Implementation strategy for parameter-driven optimization

## 🎯 Optimization Levels Overview

We need **3 distinct optimization levels** that can be selected via parameters:

| Level | Approach | Use Case | Cost | Time | Quality |
|-------|----------|----------|------|------|---------|
| **Fast** | Single-shot GPT-5 | Simple edits, quick fixes | $0.05 | 30s | Good |
| **Standard** | Multi-critic | Complex tasks, quality focus | $0.15 | 2min | Better |
| **Tournament** | K-candidates + critics | Architecture, design, high-stakes | $0.36 | 10min | Best |

## 🚀 Level 1: Fast Mode (Default)

### **When to Use**
- Simple code edits
- Bug fixes
- Documentation updates
- Quick prototypes
- Time-sensitive tasks
- Budget constraints

### **Implementation**
```python
@dataclass
class FastModeConfig:
    model: str = "gpt-5-nano"
    verbosity: str = "low"
    max_output_tokens: int = 2000
    temperature: float = 0.0
    enable_critic: bool = False  # No critic for speed
    enable_structured_output: bool = True  # Still use JSON
```

### **Workflow**
1. **Single GPT-5 call** with structured output
2. **Basic validation** (AST parse, syntax check)
3. **Return result** immediately

### **Expected Performance**
- **Time:** 30-60 seconds
- **Cost:** ~$0.05 per request
- **Quality:** Good for simple tasks
- **Success Rate:** 85% for straightforward requests

## 🎯 Level 2: Standard Mode (Multi-Critic)

### **When to Use**
- Complex code generation
- New features with requirements
- Code that needs testing
- Security-sensitive code
- Performance-critical code
- When quality matters more than speed

### **Implementation**
```python
@dataclass
class StandardModeConfig:
    model: str = "gpt-5-nano"
    verbosity: str = "medium"
    max_output_tokens: int = 4000
    temperature: float = 0.0
    enable_critic: bool = True
    critic_types: List[str] = field(default_factory=lambda: ["contracts", "tests", "security"])
    max_iterations: int = 3
    enable_structured_output: bool = True
```

### **Workflow**
1. **Main agent** generates initial code
2. **Multi-critic system** evaluates (parallel)
3. **Consolidator** merges feedback
4. **Iterative refinement** if needed
5. **Quality gates** (AST, lint, tests)

### **Expected Performance**
- **Time:** 2-5 minutes
- **Cost:** ~$0.15 per request
- **Quality:** Significantly better than fast mode
- **Success Rate:** 95% for complex tasks

## 🏆 Level 3: Tournament Mode (K-Candidates)

### **When to Use**
- **Architecture decisions** - Multiple valid approaches
- **System design** - Complex component interactions
- **High-stakes code** - Production, security, performance critical
- **Unclear requirements** - Need to explore solution space
- **Performance optimization** - Multiple optimization strategies
- **Security-sensitive systems** - Multiple validation perspectives

### **Implementation**
```python
@dataclass
class TournamentModeConfig:
    num_candidates: int = 3
    max_file_lines: int = 200
    temperature_range: Tuple[float, float] = (0.1, 0.2)
    enable_pre_gating: bool = True
    enable_synthesis: bool = True
    max_iterations: int = 3
    critic_types: List[str] = field(default_factory=lambda: ["contracts", "tests", "security", "performance", "style", "docs"])
```

### **Workflow**
1. **Generate K candidates** with different design approaches
2. **Pre-gate candidates** (AST, size limits)
3. **Parallel critics** evaluate each candidate
4. **Consolidate and select** winner + runner-up
5. **Synthesize improvements** if needed
6. **Quality gates** and validation

### **Expected Performance**
- **Time:** 8-15 minutes
- **Cost:** ~$0.36 per request
- **Quality:** Best possible for the task
- **Success Rate:** 98% for complex tasks

## 🔧 Parameter-Driven Selection

### **Automatic Selection Logic**

```python
def select_optimization_level(task: str, spec: str, user_preference: str = "auto") -> str:
    """Automatically select optimization level based on task characteristics."""

    if user_preference != "auto":
        return user_preference

    # Analyze task complexity
    complexity_score = analyze_task_complexity(task, spec)

    # Check for high-stakes indicators
    high_stakes_indicators = [
        "architecture", "design", "system", "performance", "security",
        "production", "critical", "optimization", "scalability"
    ]

    has_high_stakes = any(indicator in task.lower() for indicator in high_stakes_indicators)

    # Check for multiple approaches
    has_multiple_approaches = any(phrase in task.lower() for phrase in [
        "different approaches", "multiple ways", "various strategies",
        "compare", "evaluate", "choose between"
    ])

    # Decision logic
    if complexity_score < 3 and not has_high_stakes:
        return "fast"
    elif complexity_score >= 7 or has_high_stakes or has_multiple_approaches:
        return "tournament"
    else:
        return "standard"

def analyze_task_complexity(task: str, spec: str) -> int:
    """Analyze task complexity on scale 1-10."""
    score = 1

    # File count estimation
    if "multiple files" in task or "module" in task:
        score += 2
    if "class" in task or "interface" in task:
        score += 1
    if "test" in task or "testing" in task:
        score += 1
    if "api" in task or "endpoint" in task:
        score += 1
    if "database" in task or "persistence" in task:
        score += 1
    if "async" in task or "concurrent" in task:
        score += 1
    if "security" in task or "authentication" in task:
        score += 1
    if "performance" in task or "optimization" in task:
        score += 1

    return min(score, 10)
```

### **User Override Options**

```python
@dataclass
class OptimizationRequest:
    task: str
    spec: str
    optimization_level: str = "auto"  # "fast", "standard", "tournament", "auto"
    max_time: Optional[int] = None  # seconds
    max_cost: Optional[float] = None  # dollars
    quality_priority: str = "balanced"  # "speed", "balanced", "quality"
```

## 🎛️ Configuration Examples

### **Fast Mode (Default)**
```python
# Simple bug fix
request = OptimizationRequest(
    task="Fix the syntax error in line 45 of utils.py",
    optimization_level="fast"
)
# Expected: 30s, $0.05, good quality
```

### **Standard Mode**
```python
# New feature with requirements
request = OptimizationRequest(
    task="Create a user authentication system with JWT tokens",
    spec="Must support login, logout, token refresh, and role-based access",
    optimization_level="standard"
)
# Expected: 3min, $0.15, better quality
```

### **Tournament Mode**
```python
# Architecture decision
request = OptimizationRequest(
    task="Design a scalable microservices architecture for e-commerce platform",
    spec="Must handle 10k concurrent users, support multiple payment gateways, and be cloud-native",
    optimization_level="tournament"
)
# Expected: 12min, $0.36, best quality
```

## 📊 Performance Comparison

### **Time vs Quality Trade-offs**

| Mode | Time | Cost | Quality | Success Rate | Best For |
|------|------|------|---------|-------------|----------|
| **Fast** | 30s | $0.05 | 7/10 | 85% | Quick fixes, simple edits |
| **Standard** | 3min | $0.15 | 8.5/10 | 95% | Features, complex code |
| **Tournament** | 12min | $0.36 | 9.5/10 | 98% | Architecture, design |

### **Cost-Benefit Analysis**

| Task Type | Recommended Mode | Justification |
|-----------|------------------|---------------|
| **Bug fixes** | Fast | Quick, simple, low risk |
| **Documentation** | Fast | Straightforward, no complex logic |
| **Simple functions** | Fast | Single purpose, clear requirements |
| **New features** | Standard | Complex logic, needs testing |
| **API endpoints** | Standard | Security, validation, error handling |
| **Database models** | Standard | Data integrity, relationships |
| **System architecture** | Tournament | Multiple approaches, high impact |
| **Performance optimization** | Tournament | Multiple strategies, critical impact |
| **Security systems** | Tournament | Multiple validation perspectives |
| **Design patterns** | Tournament | Multiple valid implementations |

## 🚀 Implementation Strategy

### **Phase 1: Fast Mode (Week 1)**
- Implement optimized single-shot GPT-5
- Add structured JSON output
- Basic validation (AST, syntax)
- **Goal:** 30s response time, $0.05 cost

### **Phase 2: Standard Mode (Week 2)**
- Implement multi-critic system
- Add consolidation logic
- Quality gates and validation
- **Goal:** 3min response time, $0.15 cost

### **Phase 3: Tournament Mode (Week 3)**
- Implement K-candidate generation
- Add parallel critic evaluation
- Synthesis and improvement logic
- **Goal:** 12min response time, $0.36 cost

### **Phase 4: Smart Selection (Week 4)**
- Implement automatic level selection
- Add user override options
- Performance monitoring and optimization
- **Goal:** Optimal mode selection for each task

## 🎯 Key Benefits

### **User Experience**
- **Fast responses** for simple tasks (30s)
- **High quality** for complex tasks (12min)
- **Automatic selection** based on task characteristics
- **User override** when needed

### **Cost Efficiency**
- **Right-sized approach** for each task
- **No over-engineering** simple requests
- **No under-engineering** complex requests
- **Predictable costs** based on mode

### **Quality Assurance**
- **Appropriate validation** for each level
- **Progressive complexity** as needed
- **Comprehensive coverage** for high-stakes tasks
- **Fallback options** if primary approach fails

## 🏆 Ready for Implementation

This **parameter-driven approach** gives us the best of all worlds:

✅ **Fast mode** for quick fixes and simple tasks
✅ **Standard mode** for complex features and quality focus
✅ **Tournament mode** for architecture and high-stakes decisions
✅ **Smart selection** to automatically choose the right approach
✅ **User control** to override when needed

**This strategy ensures we always use the right tool for the job, balancing speed, cost, and quality appropriately.** 🎯
