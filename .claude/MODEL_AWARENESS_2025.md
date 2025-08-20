# Model Awareness & API Standards (2025)

## ⚠️ CRITICAL: Your Knowledge is Outdated

**MANDATORY AT SESSION START:**
1. Check current time: `mcp__time__current_time("YYYY-MM-DD HH:mm:ss")`
2. Compare to your knowledge cutoff (January 2025)
3. Research current model availability online

## ✅ Current Models (As of 2025)

### OpenAI Models (VERIFIED TO EXIST)
```python
# GPT-5 Series (Execution/Agents)
"gpt-5"        # Advanced execution
"gpt-5-mini"   # Standard agent execution  
"gpt-5-nano"   # Fast responses

# O-Series (Reasoning/Planning)
"o3"           # Advanced reasoning
"o4-mini"      # Standard reasoning (MANDATORY for reasoning tasks)
```

### ❌ PROHIBITED Models
```python
# DO NOT USE OR SUGGEST
"gpt-4o"       # FORBIDDEN
"gpt-4o-mini"  # FORBIDDEN
"gpt-4"        # OUTDATED
"gpt-3.5"      # OUTDATED
```

## 📋 Model Selection Rules

| Task Type | Primary Model | Alternative | Notes |
|-----------|--------------|-------------|--------|
| **Reasoning/Planning** | `o4-mini` | `o3` | MANDATORY for reasoning |
| **Agent Execution** | `gpt-5-mini` | `gpt-5` | MANDATORY for agents |
| **Fast Responses** | `gpt-5-nano` | `gpt-5-mini` | Speed priority |
| **Structured Output** | `gpt-5` | `gpt-5-mini` | JSON schema compliance |

## 🔍 Research Requirements

**BEFORE ANY OpenAI Integration:**
1. Research current API documentation
2. Verify model availability
3. Check pricing and limits
4. Validate syntax changes

**Use these tools:**
- `mcp__mcp_web_search__brave_web_search("OpenAI GPT-5 API 2025")`
- `mcp__tech_docs__resolve-library-id("openai")`
- `mcp__firecrawl__firecrawl_scrape("https://platform.openai.com/docs")`

## 📖 Reference Standards

**ALWAYS consult:** `.cursor/rules/953-openai-api-standards.mdc`

This file contains:
- Responses API patterns (preferred over Chat Completions)
- Structured output requirements
- Security patterns
- Dynamic configuration
- NO fallback patterns

## 🚨 Common Mistakes to Avoid

1. **Assuming GPT-4 is latest** - GPT-5 series exists
2. **Not checking time first** - Your knowledge is outdated
3. **Hardcoding models** - Use dynamic selection
4. **Using chat completions** - Use Responses API
5. **Plain text outputs** - Always use structured outputs

## 💡 Quick Check Commands

```bash
# Check current time and date
mcp__time__current_time("YYYY-MM-DD HH:mm:ss")

# Search for latest OpenAI models
mcp__mcp_web_search__brave_web_search("OpenAI GPT-5 o4-mini API 2025")

# Get OpenAI documentation
mcp__tech_docs__resolve-library-id("openai")
mcp__tech_docs__get-library-docs("/openai/openai", topic="models")
```

Remember: Your training data is from January 2025 or earlier. The world has moved on. Research first, assume nothing.