# Hook Performance Analysis

## Current Response Times

### Test Results (with gpt-5-mini and gpt-5-nano)

| Hook | Model | Average | Median | Min | Max |
|------|-------|---------|--------|-----|-----|
| **prompt_opt.py** | gpt-5-mini | 2.08s | 2.08s | 2.02s | 2.13s |
| **answer_review.py** | gpt-5-nano | 1.44s | 1.42s | 1.41s | 1.50s |

### Breakdown of Response Time

1. **Initialization Overhead**: ~1.2s
   - Importing opsvi-llm modules: ~1.1s
   - Creating provider instance: ~0.1s
   - Pydantic schema definition: <0.001s

2. **API Call Time**:
   - gpt-5-mini: ~0.9-1.0s
   - gpt-5-nano: ~0.2-0.3s

3. **Total Response Time**:
   - prompt_opt.py: ~2.0-2.1s (1.2s init + 0.9s API)
   - answer_review.py: ~1.4-1.5s (1.2s init + 0.3s API)

## Performance Optimizations

### 1. Reduce Initialization Overhead (CRITICAL)

The biggest bottleneck is the 1.2s initialization time. Options:

#### Option A: Lazy Import (Recommended)
Move imports inside functions to defer loading:

```python
def get_provider():
    """Lazy load provider to reduce startup time."""
    global _provider
    if '_provider' not in globals():
        from opsvi_llm.providers.openai_provider import OpenAIProvider, OpenAIConfig
        config = OpenAIConfig(...)
        _provider = OpenAIProvider(config)
    return _provider
```

#### Option B: Direct OpenAI SDK (Fastest)
For absolute minimum latency, use OpenAI SDK directly with proper parameters:

```python
from openai import OpenAI
client = OpenAI()  # Much faster import

# Use correct parameters based on model
if model.startswith(("gpt-5", "o3", "o4")):
    params["max_completion_tokens"] = max_tokens
else:
    params["max_tokens"] = max_tokens
```

### 2. Model Selection Strategy

| Use Case | Recommended Model | Response Time |
|----------|------------------|---------------|
| Fast validation | gpt-5-nano | ~1.4s total |
| Prompt optimization | gpt-5-nano or gpt-5-mini | 1.4-2.1s |
| Complex review | gpt-5-mini | ~2.1s |
| Reasoning tasks | o4-mini | ~2.5-3s |

### 3. Token Optimization

Reduce max_tokens for faster responses:

```bash
# Environment variables for tuning
export PROMPT_OPT_MAX_TOK=2000  # Default: 4000
export REVIEW_MAX_TOK=1500      # Default: 4000
```

### 4. Parallel Processing

For multiple hooks, run in parallel:

```python
import asyncio

async def run_hooks_parallel():
    tasks = [
        run_prompt_opt(),
        run_answer_review()
    ]
    results = await asyncio.gather(*tasks)
    return results
```

## Recommended Configuration for Speed

### Fast Configuration (Target: <1.5s)
```bash
# Use fastest models
export PROMPT_OPT_MODEL=gpt-5-nano
export REVIEW_MODEL=gpt-5-nano
export REVIEW_MODEL_ESCALATE=gpt-5-mini

# Reduce token limits
export PROMPT_OPT_MAX_TOK=1500
export REVIEW_MAX_TOK=1000

# Tighter timeout
export OPENAI_TIMEOUT_SEC=10.0
```

### Balanced Configuration (Target: <2s)
```bash
# Current defaults
export PROMPT_OPT_MODEL=gpt-5-mini
export REVIEW_MODEL=gpt-5-nano
export REVIEW_MODEL_ESCALATE=gpt-5-mini

# Moderate token limits
export PROMPT_OPT_MAX_TOK=2500
export REVIEW_MAX_TOK=2000

export OPENAI_TIMEOUT_SEC=15.0
```

## Implementation Priority

1. **Immediate**: Switch prompt_opt.py to gpt-5-nano (saves ~0.7s)
2. **Short-term**: Implement lazy loading (saves ~1.2s on subsequent calls)
3. **Medium-term**: Consider caching provider between hook calls
4. **Long-term**: Move to async architecture for parallel execution

## Expected Performance After Optimizations

| Configuration | prompt_opt.py | answer_review.py |
|--------------|---------------|------------------|
| Current | 2.1s | 1.4s |
| Fast Config | 1.4s | 1.4s |
| With Lazy Load | 0.9s | 0.3s |
| Direct SDK | 0.8s | 0.2s |

## Conclusion

The current implementation is functional but has significant initialization overhead. The fastest path to improvement is:

1. Switch to gpt-5-nano for prompt_opt.py
2. Implement lazy loading of the provider
3. Reduce max_tokens to minimum needed

These changes could reduce response times by 50-75% without changing the architecture.
