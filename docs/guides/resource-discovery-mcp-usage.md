# Resource Discovery MCP Tool Usage Guidelines

## Overview
The Resource Discovery MCP tool helps find existing functionality in the codebase while conserving tokens through intelligent result limiting and guidance.

## 🎯 Tool Improvements (Latest Version)

### Smart Result Limiting
- **Automatic guidance**: When too many results found, provides specific refinement suggestions
- **Token conservation**: Strict limits on returned data (5 packages, 5 modules per package)
- **Intelligent truncation**: Shows counts of additional items rather than listing everything

## 🚨 Common Problems & Solutions

### 1. Token Limit Prevention
- **Old Problem**: `list_packages()` returned 120,000+ tokens
- **New Solution**: Returns max 10 packages in summary mode by default
- **Guidance**: Tool now suggests using `search_resources()` or `check_package_exists()` instead

### 2. Information Overload Prevention
- **Old Problem**: Search returned every tangentially related module
- **New Solution**: Tool returns guidance when >8 packages match
- **Auto-suggestion**: Provides 5 specific refinement suggestions
- **Example**: Search "database" → suggests "database PostgreSQL", "database Redis", etc.

### 3. Duplicate Results
- **Problem**: Same utilities appear multiple times across packages
- **Cause**: No deduplication in results
- **Solution**: Focus on primary packages, ignore duplicates

## 📋 Best Practices (With New Limits)

### 1. Start Specific, Then Broaden
```python
# ❌ BAD: Too broad (tool will suggest refinements)
result = search_resources("database")
# Returns: guidance with suggestions like "database PostgreSQL", "database Redis"

# ✅ GOOD: Specific functionality
search_resources("neo4j client")  # Returns max 5 packages, 5 modules each
search_resources("JWT provider")  # Focused results within token limits
```

### 2. Use Package Existence Check First
```python
# Instead of searching broadly, check specific packages
check_package_exists("opsvi-auth")  # Quick, focused result
check_package_exists("opsvi-neo4j")  # Tells you if it exists
```

### 3. Understanding New Response Format
```python
# When search is too broad:
result = search_resources("database")
if result["search_guidance"]["status"] == "too_many_results":
    print(result["search_guidance"]["suggestion"])
    # "Found 25 packages matching 'database'. Please be more specific."
    print(result["search_guidance"]["refinement_suggestions"])
    # ["database PostgreSQL", "database MongoDB", "database Redis", ...]

# When search is good:
result = search_resources("JWT authentication")
if result["search_guidance"]["status"] == "success":
    print(result["search_guidance"]["recommendation"])
    # "Strongly recommend using 'opsvi-auth' - high relevance match."
```

### 4. Use Conservative Search Depth
```python
# Default is now 2 (reduced from 3)
search_resources(
    functionality="redis cache",
    search_depth=1,  # Even shallower for token conservation
    include_tests=False  # Skip test files
)
```

### 4. Use Multiple Narrow Searches
```python
# Instead of one broad search, use multiple specific ones
results1 = search_resources("ArangoDB provider", search_depth=2)
results2 = search_resources("PostgreSQL interface", search_depth=2)
results3 = search_resources("Redis client", search_depth=2)
```

## 🎯 Targeted Search Strategies

### Strategy 1: Technology-Specific Searches
```python
# Search for specific technologies/tools
"neo4j graph"     # Neo4j specific
"arango database" # ArangoDB specific
"redis cache"     # Redis specific
"JWT token"       # JWT authentication
"MCP server"      # MCP implementations
```

### Strategy 2: Pattern-Specific Searches
```python
# Search for design patterns
"provider interface"  # Provider pattern implementations
"base client"        # Base client classes
"middleware auth"    # Authentication middleware
"exception handler"  # Error handling patterns
```

### Strategy 3: Component-Specific Searches
```python
# Search for specific component types
"config settings"    # Configuration classes
"manager class"      # Manager components
"coordinator"        # Coordination components
"orchestrator"       # Orchestration systems
```

## 🔍 Query Optimization Techniques

### 1. Use Exact Package Names
```python
# When you know the package prefix
check_package_exists("opsvi-data")
check_package_exists("opsvi-auth")
check_package_exists("opsvi-mcp")
```

### 2. Combine Terms for Precision
```python
# Combine technology + pattern
search_resources("neo4j client provider", search_depth=2)
search_resources("JWT authentication middleware", search_depth=2)
```

### 3. Use Exclusion Logic
```python
# Focus on implementation, not tests
search_resources(
    functionality="database migration",
    search_depth=2,
    include_tests=False  # Exclude test files
)
```

## 📊 Interpreting Results

### Understanding Relevance Scores
- **Score > 100**: Very relevant, primary packages for this functionality
- **Score 50-100**: Relevant, contains useful utilities
- **Score 20-50**: Some relevance, might have helper functions
- **Score < 20**: Minimal relevance, probably just imports

### Focus on Key Fields
```python
# Most useful fields in results:
packages_found[0]['name']           # Package name
packages_found[0]['path']           # Location
packages_found[0]['relevant_modules']  # Specific modules
packages_found[0]['relevance_score']   # How relevant

# Often ignore:
potential_utilities  # Often duplicates
similar_patterns    # Usually empty or redundant
```

## 🚀 Practical Workflows

### Workflow 1: Finding Existing Functionality
```python
# Step 1: Check if dedicated package exists
check_package_exists("opsvi-redis")

# Step 2: If not, search for the functionality
search_resources("redis interface", search_depth=2)

# Step 3: Look at top 3 packages by relevance_score
# Focus on packages with score > 50
```

### Workflow 2: Avoiding Duplication
```python
# Before implementing new feature:
# Step 1: Search for similar functionality
find_similar_functionality(
    code_snippet="def authenticate_user(username, password)",
    language="python"
)

# Step 2: Check relevance scores
# If similarity_score > 0.7, likely duplicate
```

### Workflow 3: Understanding Dependencies
```python
# Step 1: Check package exists
check_package_exists("opsvi-agents")

# Step 2: Get its dependencies
get_package_dependencies("opsvi-agents")

# Step 3: Check each dependency exists
for dep in dependencies:
    check_package_exists(dep)
```

## ⚡ Quick Reference

### Do's
- ✅ Start with `check_package_exists()` for known packages
- ✅ Use specific, technical search terms
- ✅ Set `search_depth=1` or `2` for initial searches
- ✅ Always set `include_tests=False` unless you need tests
- ✅ Focus on packages with relevance_score > 50
- ✅ Use multiple narrow searches over one broad search

### Don'ts
- ❌ Never use `list_packages()` without filters (exceeds token limit)
- ❌ Avoid generic terms like "data", "service", "manager"
- ❌ Don't use search_depth > 3 unless necessary
- ❌ Don't parse all returned utilities (often duplicates)
- ❌ Avoid searching for common patterns (returns everything)

## 💡 Pro Tips

1. **Package Naming Convention**: All packages start with `opsvi-`
   - Quick check: `check_package_exists(f"opsvi-{feature}")`

2. **Core Packages to Know**:
   - `opsvi-auth`: Authentication
   - `opsvi-data`: Database providers
   - `opsvi-mcp`: MCP servers
   - `opsvi-agents`: AI agents
   - `opsvi-core`: Core utilities

3. **Search Incrementally**:
   ```python
   # Start shallow, go deeper only if needed
   result = search_resources("feature", search_depth=1)
   if not sufficient:
       result = search_resources("feature", search_depth=2)
   ```

4. **Cache Results**: 
   - Save search results to avoid repeated queries
   - Reuse package existence checks

## 🎯 Example Queries That Work Well

```python
# Specific technology searches
search_resources("neo4j graph database", search_depth=2)
search_resources("JWT authentication provider", search_depth=2)
search_resources("ArangoDB migration", search_depth=2)

# Pattern searches
search_resources("base provider class", search_depth=1)
search_resources("authentication middleware", search_depth=2)

# Component searches
search_resources("job manager", search_depth=2)
search_resources("task orchestrator", search_depth=2)

# Quick checks
check_package_exists("opsvi-auth")
get_package_dependencies("opsvi-mcp")
```

## 📝 Summary of Improvements

### New Token-Conserving Limits
- **Packages returned**: Max 5 by default (was unlimited)
- **Modules per package**: Max 5 shown (was unlimited)
- **Search depth**: Default 2 (was 3)
- **List packages**: Returns 10 summaries (was all with full details)

### Intelligent Guidance System
- **Too many results (>8)**: Provides refinement suggestions
- **Good results (≤8)**: Gives usage recommendations
- **No results**: Suggests creating new package

### Recommended Workflow
1. **First**: Try `check_package_exists("package-name")` if you know what you need
2. **Second**: Use specific `search_resources("specific technology feature")`
3. **Last resort**: Use `list_packages()` only for overview

### Key Changes from Original
| Feature | Old Behavior | New Behavior |
|---------|-------------|--------------|
| Broad search | Returns everything | Returns guidance + suggestions |
| Token usage | Could exceed 120k | Max ~5k tokens |
| Module lists | All modules shown | Max 5 + count of rest |
| Guidance | None | Context-aware suggestions |

Following these guidelines ensures efficient resource discovery without token overflow.