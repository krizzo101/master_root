# Consult Agent Usage Examples

## Code Generation Examples

### React Component Creation
```python
# Session tracking in requesting agent
current_feature = {
    "project": "admin_dashboard",
    "feature": "data_table_component",
    "session_id": "admin_datatable_001",
    "request_count": 0
}

# First request: Initial component creation
current_feature["request_count"] += 1
mcp_consult_agent_consult({
    "prompt": "### TASK\nCreate a React component for a data table with sorting, filtering, pagination, and export functionality\n\n### LANGUAGE / RUNTIME\nTypeScript · React 18 · Jest\n\n### INPUTS\n• Data: Array of objects with dynamic columns\n• Features: sort, filter, paginate, export to CSV\n\n### CONSTRAINTS\n- Include TypeScript types and accessibility features\n- Follow React best practices and include unit tests\n- Support keyboard navigation and screen readers\n\n### OUTPUT_FORMAT\n```tsx\n// Component code with full implementation\n```",
    "session_id": current_feature["session_id"],
    "artifact_type": "code",
    "iterate": 2,
    "critic_enabled": True
})

# Second request: Refinement based on previous work
current_feature["request_count"] += 1
mcp_consult_agent_consult({
    "prompt": "### TASK\nRefine the data table component to add virtual scrolling for large datasets\n\n### CONTEXT\nBuilding on the previous data table implementation with sorting/filtering\n\n### NEW REQUIREMENTS\n- Virtual scrolling for 10K+ rows\n- Maintain existing sorting/filtering functionality\n- Optimize performance for large datasets\n\n### OUTPUT_FORMAT\n```tsx\n// Updated component with virtual scrolling\n```",
    "session_id": current_feature["session_id"],  # Same session for context continuity
    "artifact_type": "code",
    "iterate": 1,
    "critic_enabled": True
})
```

### GitHub Actions Workflow
```python
mcp_consult_agent_consult({
    "prompt": "### TASK\nCreate a GitHub Actions workflow that builds & tests a Node library\n\n### LANGUAGE / RUNTIME\nYAML · Node 20\n\n### INPUTS\n• Node versions: [18.x, 20.x]\n• OS matrix: ubuntu-latest, macos-latest\n\n### CONSTRAINTS\n- Cache node_modules using actions/cache@v4\n- Lint with ESLint; fail on warnings\n\n### OUTPUT_FORMAT\n```yaml\n# .github/workflows/ci.yml\nname: CI\n...\n```",
    "session_id": "github_actions_001",
    "artifact_type": "workflow"
})
```

## Architecture Planning Examples

### Microservices Architecture
```python
# Session tracking for architecture planning
architecture_session = {
    "project": "ecommerce_platform",
    "phase": "system_design",
    "session_id": "ecommerce_architecture_001",
    "request_count": 0
}

# First request: High-level architecture
architecture_session["request_count"] += 1
mcp_consult_agent_consult({
    "prompt": "### ROLE\nSenior Cloud Architect\n\n### OBJECTIVE\nDesign a microservices architecture for an e-commerce platform with user management, product catalog, order processing, and payment integration\n\n### CONTEXT\n• Scale: 1M+ users, 10K+ concurrent sessions\n• SLA: 99.9% uptime, <200ms p95 latency\n• Budget: $50K/month infrastructure\n\n### DELIVERABLES\n1. Service boundary diagram (Mermaid)\n2. Data flow architecture\n3. Deployment strategy\n4. Scalability planning\n\n### FORMAT\nMarkdown + ```mermaid``` diagrams\n\n### RULES\n- Include security considerations\n- Consider data consistency patterns\n- Address monitoring and observability",
    "session_id": architecture_session["session_id"],
    "artifact_type": "plan",
    "iterate": 2,
    "critic_enabled": True
})

# Second request: Detailed service design (same session for context)
architecture_session["request_count"] += 1
mcp_consult_agent_consult({
    "prompt": "### ROLE\nSenior Cloud Architect\n\n### OBJECTIVE\nDesign detailed service specifications for the e-commerce microservices architecture\n\n### CONTEXT\nBuilding on the previous high-level architecture design\n\n### DELIVERABLES\n1. API specifications for each service\n2. Database schema design\n3. Service communication patterns\n4. Security implementation details\n\n### FORMAT\nMarkdown + OpenAPI specs\n\n### RULES\n- Maintain consistency with previous architecture decisions\n- Include error handling and resilience patterns",
    "session_id": architecture_session["session_id"],  # Same session for architectural consistency
    "artifact_type": "plan",
    "iterate": 2,
    "critic_enabled": True
})
```

## Documentation Examples

### Component Library Documentation
```python
# Session tracking for documentation
docs_session = {
    "project": "react_component_library",
    "doc_type": "component_documentation",
    "session_id": "react_library_docs_001",
    "request_count": 0
}

# First request: Component documentation structure
docs_session["request_count"] += 1
mcp_consult_agent_consult({
    "prompt": "### TARGET_AUDIENCE\nIntermediate to advanced React developers\n\n### DOC_TYPE\nComponent Library Documentation (.md)\n\n### PRODUCT_CONTEXT\nReact component library with TypeScript, 15+ components\n\n### MUST_INCLUDE\n- Usage examples with code snippets\n- Props documentation with TypeScript types\n- Best practices and patterns\n- Accessibility guidelines and examples\n- Installation and setup instructions\n\n### TONE\nProfessional, comprehensive, developer-friendly",
    "session_id": docs_session["session_id"],
    "artifact_type": "doc",
    "iterate": 1,
    "critic_enabled": True
})

# Second request: API reference documentation (same session for consistency)
docs_session["request_count"] += 1
mcp_consult_agent_consult({
    "prompt": "### TARGET_AUDIENCE\nIntermediate to advanced React developers\n\n### DOC_TYPE\nAPI Reference Documentation (.md)\n\n### PRODUCT_CONTEXT\nBuilding on the previous component library documentation structure\n\n### MUST_INCLUDE\n- Complete API reference for all 15+ components\n- TypeScript interface definitions\n- Code examples for each component\n- Migration guides and breaking changes\n\n### TONE\nTechnical, comprehensive, reference-style",
    "session_id": docs_session["session_id"],  # Same session for documentation consistency
    "artifact_type": "doc",
    "iterate": 1,
    "critic_enabled": True
})
```

## Knowledge File Integration Examples

### Research-Based Implementation
```python
# Session tracking for knowledge-based planning
knowledge_session = {
    "project": "react_component_library",
    "phase": "research_implementation",
    "session_id": "react_library_research_001",
    "request_count": 0
}

# First, create knowledge file in .cursor/knowledge/
# File: .cursor/knowledge/knowledge_update_react_library_20250715.md

# Then use with consult agent (first request)
knowledge_session["request_count"] += 1
mcp_consult_agent_consult({
    "prompt": "Based on the attached knowledge file, create a comprehensive implementation plan for the React component library.",
    "session_id": knowledge_session["session_id"],
    "artifact_type": "plan",
    "file_paths": ["/home/opsvi/current_project/.cursor/knowledge/knowledge_update_react_library_20250715.md"],
    "iterate": 2,
    "critic_enabled": True
})

# Second request: Refine implementation based on research (same session)
knowledge_session["request_count"] += 1
mcp_consult_agent_consult({
    "prompt": "Based on the previous research and implementation plan, create detailed component specifications for the first 5 components in the library.",
    "session_id": knowledge_session["session_id"],  # Same session to maintain research context
    "artifact_type": "plan",
    "iterate": 1,
    "critic_enabled": True
})
```

## Interactive Response Handling Examples

### Multi-Turn Interaction
```python
# First call - Analysis and Questions
response1 = mcp_consult_agent_consult({
    "prompt": "Help me create a React auth component",
    "session_id": "auth_component_001"
})
# Returns: "QUESTIONS: 1. What auth method? 2. Existing utilities?..."

# Second call - Provide additional info
response2 = mcp_consult_agent_consult({
    "prompt": "We're using JWT, have existing utilities in /utils/auth.ts, need login/logout",
    "session_id": "auth_component_001"  # Same session ID
})
# Returns: "FINAL: Here's your React auth component..."
```

### Response Type Detection
```python
def extract_response_type(response_text):
    """Extract response type from consult agent response"""
    lines = response_text.strip().split('\n')
    first_line = lines[0].strip()

    if first_line.startswith("**FINAL:**"):
        return "FINAL"
    elif first_line.startswith("**QUESTIONS:**"):
        return "QUESTIONS"
    elif first_line.startswith("**CONCERNS:**"):
        return "CONCERNS"
    elif first_line.startswith("**CLARIFICATION:**"):
        return "CLARIFICATION"
    else:
        return "FINAL"  # Default to final response
```

## Session Management Examples

### Session Tracking Implementation
```python
# Maintain session state in your agent
sessions = {
    "current_project": "ecommerce_platform",
    "active_sessions": {
        "auth_system": "ecommerce_auth_001",
        "payment_flow": "ecommerce_payment_001",
        "api_docs": "ecommerce_docs_001"
    }
}

# Example session tracking in requesting agent
current_feature = {
    "project": "admin_dashboard",
    "feature": "data_table_component",
    "session_id": "admin_datatable_001",
    "request_count": 0
}

# Update session tracking
current_feature["request_count"] += 1
current_feature["last_request"] = time.time()

# Use consistent session ID for related requests
mcp_consult_agent_consult({
    "prompt": "...",
    "session_id": current_feature["session_id"]
})
```

### Session ID Naming Conventions
```python
# Project-Based Naming
"ecommerce_auth_001"
"ecommerce_payment_001"
"ecommerce_catalog_002"  # Version 2 of catalog feature

# Task-Based Naming
"code_review_auth_service_001"
"architecture_payment_flow_001"
"docs_api_reference_001"

# Time-Based Naming
"20250715_auth_implementation_001"
"20250715_auth_testing_002"
```

## Parameter Optimization Examples

### Auto-Selection Trust (Recommended)
```python
# The agent will analyze and select optimal parameters
mcp_consult_agent_consult({
    "prompt": "Create a React authentication component with JWT support",
    "session_id": "auth_component_001"
    # No parameters specified - intelligent analysis will determine optimal values
})
```

### Manual Override (Use Sparingly)
```python
# Only override if you have specific requirements
mcp_consult_agent_consult({
    "prompt": "Quick code review of this simple function",
    "session_id": "quick_review_001",
    "iterate": 1,  # Override: Simple task, only need 1 iteration
    "critic_enabled": False  # Override: Quick review, no critic needed
    # Model not specified - will be auto-selected
})
```

### Complex Reasoning Override
```python
mcp_consult_agent_consult({
    "prompt": "### ROLE\nSenior Technical Architect\n\n### OBJECTIVE\nAnalyze this complex architectural decision with multiple trade-offs...\n\n### CONTEXT\n[Your specific context]\n\n### DELIVERABLES\n[What you need]\n\n### FORMAT\n[Output format]\n\n### RULES\n[Constraints]",
    "session_id": "complex_analysis_001",
    "model": "o3"  # Force o3 for advanced reasoning
})
```
